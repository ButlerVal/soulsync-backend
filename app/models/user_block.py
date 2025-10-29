import uuid
import datetime
from sqlalchemy import func, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from app.db.base import Base

class UserBlock(Base):
    """
    Model for the 'user_blocks' table.
    Stores a record of one user blocking another.
    """

    block_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # The user who initiated the block
    blocker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    # The user who was blocked
    blocked_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    # Add a unique constraint to prevent duplicate blocks
    __table_args__ = (
        UniqueConstraint('blocker_id', 'blocked_id', name='_blocker_blocked_uc'),
    )