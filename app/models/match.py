import uuid
import datetime
from sqlalchemy import String, Float, func, Column, Text, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from app.db.base import Base
from app.models.user import User # Import User for relationships
import enum

# Define Enums for match status and user actions
class MatchStatusEnum(str, enum.Enum):
    pending = "pending"
    connected = "connected"
    passed = "passed"
    expired = "expired"

class UserActionEnum(str, enum.Enum):
    none = "none"
    connected = "connected"
    passed = "passed"

class Match(Base):
    """
    Model for the 'matches' table.
    Stores potential matches between users.
    """
    

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Foreign keys to the users table
    user1_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    user2_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # Relationships (optional but helpful)
    user1: Mapped["User"] = relationship(foreign_keys=[user1_id])
    user2: Mapped["User"] = relationship(foreign_keys=[user2_id])

    compatibility_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    match_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_starters: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[MatchStatusEnum] = mapped_column(
        SQLAlchemyEnum(MatchStatusEnum, name="match_status_enum", create_type=True),
        default=MatchStatusEnum.pending,
        nullable=False,
        index=True
    )
    user1_action: Mapped[UserActionEnum] = mapped_column(
        SQLAlchemyEnum(UserActionEnum, name="user_action_enum", create_type=True),
        default=UserActionEnum.none,
        nullable=False
    )
    user2_action: Mapped[UserActionEnum] = mapped_column(
        SQLAlchemyEnum(UserActionEnum, name="user_action_enum", create_type=True), # Reuse the same enum type
        default=UserActionEnum.none,
        nullable=False
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime.datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True # E.g., set to 14 days from created_at
    )
    connected_at: Mapped[datetime.datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )