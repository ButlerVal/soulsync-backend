import uuid
import datetime
from typing import Optional
from sqlalchemy import func, Column, Text, Float, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.user import User # Import User to set up the relationship

class EmotionalProfile(Base):
    """
    Model for the 'emotional_profiles' table.
    Stores the 8-dimensional emotion vector for a user.
    """
    
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Create the one-to-one relationship with the User
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), unique=True, nullable=False
    )
    user: Mapped["User"] = relationship(back_populates=None) # Simple relationship

    # [cite_start]The 8 core emotions from the PDF [cite: 55-63]
    joy: Mapped[float] = mapped_column(Float, default=0.0)
    sadness: Mapped[float] = mapped_column(Float, default=0.0)
    anxiety: Mapped[float] = mapped_column(Float, default=0.0)
    calm: Mapped[float] = mapped_column(Float, default=0.0)
    anger: Mapped[float] = mapped_column(Float, default=0.0)
    excitement: Mapped[float] = mapped_column(Float, default=0.0)
    empathy: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # [cite_start]Store the raw text samples used for the analysis [cite: 404]
    sample_texts: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # How many samples were used?
    profile_strength: Mapped[int] = mapped_column(Integer, default=0) 

    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP(timezone=True), onupdate=func.now(), nullable=True
    )