import uuid
import datetime
from sqlalchemy import func, ForeignKey, Text, String, Boolean, Enum as SQLAlchemyEnum, TIMESTAMP # Import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import enum

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.conversation import Conversation


# Define Enum for message types
class MessageTypeEnum(str, enum.Enum):
    text = "text"
    image = "image"
    voice = "voice"
    gif = "gif"

class Message(Base):
    """Model for the 'messages' table."""
    # __tablename__ removed

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.conversation_id"), nullable=False, index=True
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # Relationship uses string for SQLAlchemy
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    message_type: Mapped[MessageTypeEnum] = mapped_column(
        SQLAlchemyEnum(MessageTypeEnum, name="message_type_enum", create_type=True),
        default=MessageTypeEnum.text,
        nullable=False
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    read_at: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), index=True
    )
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)