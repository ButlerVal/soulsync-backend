import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, delete
import logging

from app.models.user_block import UserBlock
from app.models.report import Report
from app.schemas.report import ReportCreate # Import schema for creating reports

logger = logging.getLogger(__name__)

class SafetyService:
    """Service for handling user blocking and reporting."""

    async def block_user(self, db: AsyncSession, blocker_id: uuid.UUID, blocked_id: uuid.UUID) -> UserBlock | None:
        """Creates a block record from blocker_id to blocked_id."""
        if blocker_id == blocked_id:
            logger.warning(f"User {blocker_id} attempted to block themselves.")
            return None # Users cannot block themselves

        # Check if block already exists
        existing_block = await db.execute(
            select(UserBlock).where(
                UserBlock.blocker_id == blocker_id,
                UserBlock.blocked_id == blocked_id
            )
        )
        if existing_block.scalars().first():
            logger.info(f"User {blocker_id} already blocked {blocked_id}.")
            return existing_block.scalars().first() # Return existing block

        logger.info(f"User {blocker_id} blocking user {blocked_id}.")
        new_block = UserBlock(blocker_id=blocker_id, blocked_id=blocked_id)
        db.add(new_block)
        await db.commit()
        await db.refresh(new_block)

        # --- TODO: ---
        # - Remove any pending matches between these users.
        # - Terminate any active conversation/WebSocket connection.
        # --- /TODO ---

        return new_block

    async def unblock_user(self, db: AsyncSession, blocker_id: uuid.UUID, blocked_id: uuid.UUID) -> bool:
        """Removes a block record."""
        logger.info(f"User {blocker_id} attempting to unblock user {blocked_id}.")
        stmt = delete(UserBlock).where(
            UserBlock.blocker_id == blocker_id,
            UserBlock.blocked_id == blocked_id
        )
        result = await db.execute(stmt)
        await db.commit()

        if result.rowcount > 0:
            logger.info(f"User {blocker_id} successfully unblocked {blocked_id}.")
            return True
        else:
            logger.warning(f"No block found from {blocker_id} to {blocked_id} to remove.")
            return False

    async def get_blocked_users(self, db: AsyncSession, user_id: uuid.UUID) -> list[uuid.UUID]:
        """Gets a list of user IDs blocked by the specified user."""
        result = await db.execute(
            select(UserBlock.blocked_id).where(UserBlock.blocker_id == user_id)
        )
        return list(result.scalars().all())

    async def check_if_blocked(self, db: AsyncSession, user1_id: uuid.UUID, user2_id: uuid.UUID) -> bool:
        """Checks if either user has blocked the other."""
        result = await db.execute(
            select(UserBlock).where(
                or_(
                    (UserBlock.blocker_id == user1_id) & (UserBlock.blocked_id == user2_id),
                    (UserBlock.blocker_id == user2_id) & (UserBlock.blocked_id == user1_id)
                )
            )
        )
        return result.scalars().first() is not None

    async def create_report(self, db: AsyncSession, reporter_id: uuid.UUID, report_in: ReportCreate) -> Report:
        """Creates a new report record."""
        logger.info(f"User {reporter_id} reporting user {report_in.reported_user_id} for {report_in.report_type.value}.")
        new_report = Report(
            reporter_id=reporter_id,
            **report_in.model_dump() # Unpack schema data into model fields
        )
        db.add(new_report)
        await db.commit()
        await db.refresh(new_report)

        # --- TODO: ---
        # - Trigger notification/alert to moderation team.
        # --- /TODO ---

        return new_report

# Create a single instance
safety_service = SafetyService()