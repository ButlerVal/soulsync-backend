import uuid
from pydantic import BaseModel
from datetime import datetime

class EmotionalProfileBase(BaseModel):
    """Base schema for emotional profile scores."""
    joy: float = 0.0
    sadness: float = 0.0
    anxiety: float = 0.0
    calm: float = 0.0
    anger: float = 0.0
    excitement: float = 0.0
    empathy: float = 0.0
    confidence: float = 0.0

class EmotionalProfileRead(EmotionalProfileBase):
    """Schema for reading an emotional profile."""
    profile_id: uuid.UUID
    user_id: uuid.UUID
    profile_strength: int
    updated_at: datetime | None

    class Config:
        from_attributes = True

class TextAnalysisRequest(BaseModel):
    """Schema for the text input from the user."""
    # Using 'text_samples' as a list of strings
    text_samples: list[str]