import uuid
import datetime
from typing import Optional # Import Optional for nullable fields

from sqlalchemy import String, Date, Boolean, func, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.sqltypes import TIMESTAMP

# Import the new 2.0-style tools
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class User(Base):
    """
    Model for the 'users' table.
    Refactored for SQLAlchemy 2.0+ with Mapped and type hints
    to provide full support for Pylance and other type checkers.
    """

    # We replace `Column(...)` with `Mapped[type] = mapped_column(...)`

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Nullable fields use Optional[type]
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date_of_birth: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)

    profile_photo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    use_case: Mapped[str] = mapped_column(String(50), default="friends") 

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # We need to type Mapped[datetime.datetime] for timestamps
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP(timezone=True), onupdate=func.now(), nullable=True
    )
    last_active: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )