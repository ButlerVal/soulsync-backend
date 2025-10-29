from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate # Import schemas
from app.services.user_service import user_service # Import the service
from app.api.deps import get_current_active_user # Import auth dependency

router = APIRouter()

@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current logged-in user's profile.
    """
    # The dependency already fetches the user object.
    # Pydantic will convert it to UserRead for the response.
    return current_user

@router.put("/me", response_model=UserRead)
async def update_user_me(
    user_update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Update current logged-in user's profile.
    """
    updated_user = await user_service.update_user(
        db=db, user=current_user, user_in=user_update_data
    )
    return updated_user

# --- TODO: Add endpoint for deleting user account ---
# DELETE /me

# --- TODO: Add endpoint for uploading profile photo ---
# POST /me/photo