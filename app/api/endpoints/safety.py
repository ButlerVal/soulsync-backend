from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List

from app.db.session import get_db_session
from app.models.user import User
from app.schemas.report import ReportCreate, ReportRead
from app.services.safety_service import safety_service
from app.services.user_service import user_service # Need this to check if user exists
from app.api.deps import get_current_active_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/users/{user_id}/block", status_code=status.HTTP_204_NO_CONTENT)
async def block_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Blocks a user."""
    if current_user.user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot block yourself."
        )

    # Check if the user to be blocked exists
    user_to_block = await user_service.get_user_by_id(db, user_id=user_id)
    if not user_to_block:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User to block not found."
        )

    await safety_service.block_user(
        db, blocker_id=current_user.user_id, blocked_id=user_id
    )
    return None # Return 204 No Content

@router.delete("/users/{user_id}/unblock", status_code=status.HTTP_204_NO_CONTENT)
async def unblock_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Unblocks a user."""
    success = await safety_service.unblock_user(
        db, blocker_id=current_user.user_id, blocked_id=user_id
    )
    if not success:
         # This isn't strictly an error, but good to know
         logger.info(f"User {current_user.user_id} tried to unblock {user_id}, but no block was found.")
    return None # Return 204 No Content

@router.get("/blocked-list", response_model=List[uuid.UUID])
async def get_my_blocked_list(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Retrieves a list of user IDs that the current user has blocked."""
    return await safety_service.get_blocked_users(db, user_id=current_user.user_id)

@router.post("/reports", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_in: ReportCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Submits a report against another user."""
    if current_user.user_id == report_in.reported_user_id:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot report yourself."
        )

    # Check if the reported user exists
    reported_user = await user_service.get_user_by_id(db, user_id=report_in.reported_user_id)
    if not reported_user:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User to report not found."
        )

    new_report = await safety_service.create_report(
        db, reporter_id=current_user.user_id, report_in=report_in
    )
    return new_report