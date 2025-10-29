import uuid
import datetime
from sqlalchemy import func, ForeignKey, String, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from app.db.base import Base
from app.models.user import User # Import User for relationships
from typing import TYPE_CHECKING, List # Import List
if TYPE_CHECKING:
    from app.models.message import Message # Import only for type checker

class Conversation(Base):
    """Model for the 'conversations' table."""

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user1_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    user2_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # Relationships to users
    user1: Mapped["User"] = relationship(foreign_keys=[user1_id])
    user2: Mapped["User"] = relationship(foreign_keys=[user2_id])

    # Relationship to messages
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")

    last_message_at: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, index=True)
    # last_message_preview: Mapped[str | None] = mapped_column(String(100), nullable=True) # Maybe add later
    # unread_count_user1: Mapped[int] = mapped_column(Integer, default=0) # Maybe add later
    # unread_count_user2: Mapped[int] = mapped_column(Integer, default=0) # Maybe add later
    # is_archived_user1: Mapped[bool] = mapped_column(Boolean, default=False) # Maybe add later
    # is_archived_user2: Mapped[bool] = mapped_column(Boolean, default=False) # Maybe add later

    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )