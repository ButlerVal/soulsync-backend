from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
from app.schemas.user import UserRead
from app.db.session import get_db_session
from app.models.user import User
from app.models.emotional_profile import EmotionalProfile
from app.models.match import Match, MatchStatusEnum, UserActionEnum  # Import Match model
from app.schemas.match import MatchResult # Import the response schema
from app.services.match_service import match_service
from app.api.deps import get_current_active_user
from sqlalchemy.future import select # Needed for profile query

router = APIRouter()

# --- Helper to get user profile ---
async def get_user_profile(db: AsyncSession, user_id: uuid.UUID) -> EmotionalProfile | None:
    result = await db.execute(
        select(EmotionalProfile).where(EmotionalProfile.user_id == user_id)
    )
    return result.scalars().first()

@router.get("/daily", response_model=List[MatchResult])
async def get_daily_matches(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieves daily matches for the current user.
    If no matches exist, it attempts to generate them.
    """
    # 1. Try to get existing pending matches
    existing_matches = await match_service.get_daily_matches_for_user(db, user_id=current_user.user_id)

    # 2. If none found, generate new ones (if profile exists)
    if not existing_matches:
        user_profile = await get_user_profile(db, user_id=current_user.user_id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Cannot generate matches."
            )

        # Generate potential match data (list of dicts)
        potential_matches_data = await match_service.find_potential_matches(db, current_user, user_profile)

        # Save the generated matches to the DB
        await match_service.save_matches(db, potential_matches_data)

        # Fetch the newly saved matches
        existing_matches = await match_service.get_daily_matches_for_user(db, user_id=current_user.user_id)

    # 3. Format the response
    formatted_matches: List[MatchResult] = []
    for match in existing_matches:
        # Determine which user is the "other user"
        other_user_model = match.user2 if match.user1_id == current_user.user_id else match.user1
        if other_user_model: # Ensure relationship loaded correctly
            other_user_read = UserRead.model_validate(other_user_model) # Use model_validate (replaces from_orm)
            formatted_matches.append(
                MatchResult(
                    match_id=match.match_id,
                    other_user=other_user_read, # Pass the schema instance
                    compatibility_score=match.compatibility_score,
                    match_explanation=match.match_explanation,
                    suggested_starters=match.suggested_starters.get("starters", []) if match.suggested_starters else [],
                    status=match.status,
                    created_at=match.created_at
                )
            )
            # --- END FIX ---

    return formatted_matches

# Add these inside matches.py, below get_daily_matches

@router.post("/{match_id}/connect", response_model=MatchResult) # Reuse MatchResult for now
async def connect_match(
    match_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Allows the current user to express interest (connect) on a match."""
    match = await match_service.get_match_by_id(db, match_id=match_id)

    # Validation
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    if current_user.user_id not in [match.user1_id, match.user2_id]:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this match")
    if match.status != MatchStatusEnum.pending:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Match is already {match.status.value}")

    updated_match = await match_service.update_match_action(
        db, match=match, user_id=current_user.user_id, action=UserActionEnum.connected
    )

    # Re-format response similar to get_daily_matches
    other_user_model = updated_match.user2 if updated_match.user1_id == current_user.user_id else updated_match.user1
    if not other_user_model: # Should always load, but safety check
        raise HTTPException(status_code=500, detail="Could not load matched user data.")

    other_user_read = UserRead.model_validate(other_user_model)
    return MatchResult(
         match_id=updated_match.match_id,
         other_user=other_user_read,
         compatibility_score=updated_match.compatibility_score,
         match_explanation=updated_match.match_explanation,
         suggested_starters=updated_match.suggested_starters.get("starters", []) if updated_match.suggested_starters else [],
         status=updated_match.status,
         created_at=updated_match.created_at
    )


@router.post("/{match_id}/pass", status_code=status.HTTP_204_NO_CONTENT) # No content on success
async def pass_match(
    match_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Allows the current user to decline (pass) on a match."""
    match = await match_service.get_match_by_id(db, match_id=match_id)

    # Validation (similar to connect)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    if current_user.user_id not in [match.user1_id, match.user2_id]:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this match")
    if match.status != MatchStatusEnum.pending:
         # Allow passing even if already connected/passed? Maybe not. Keep strict for now.
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Match is already {match.status.value}")

    await match_service.update_match_action(
        db, match=match, user_id=current_user.user_id, action=UserActionEnum.passed
    )

    # No response body needed for a successful pass
    return None

