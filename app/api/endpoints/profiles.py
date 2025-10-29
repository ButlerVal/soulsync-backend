from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid # Keep uuid import

from app.db.session import get_db_session
from app.schemas.emotional_profile import TextAnalysisRequest, EmotionalProfileRead
from app.services.emotion_service import emotion_service

from app.services.profile_service import profile_service
from app.api.deps import get_current_active_user
from app.models.user import User # Import User model for dependency



router = APIRouter()

@router.post("/analyze", response_model=EmotionalProfileRead)
async def analyze_user_texts_and_save( # Renamed function
    request_body: TextAnalysisRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user)
    
):
    """
    Receives text samples for the current user, analyzes emotions,
    saves/updates the profile in the DB, and returns the profile.
    """
    if not request_body.text_samples:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No text samples provided for analysis."
        )

    # Perform analysis using the loaded model
    analysis_result = emotion_service.analyze_texts(request_body.text_samples)

    if analysis_result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze emotions. Model might not be loaded correctly.",
        )

    
    saved_profile = await profile_service.update_or_create_profile(
        db=db,
        user_id=current_user.user_id,
        profile_data=analysis_result,
        text_samples=request_body.text_samples
    )
    
    return saved_profile