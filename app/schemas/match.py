import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.match import MatchStatusEnum # Import the enum
from app.schemas.user import UserRead # Import UserRead to show user details

class MatchBase(BaseModel):
    compatibility_score: float = Field(..., ge=0, le=100) # Ensure score is 0-100
    match_explanation: str | None = None
    suggested_starters: list[str] | None = None # Assuming starters are a list of strings

class MatchRead(MatchBase):
    match_id: uuid.UUID
    user1: UserRead # Show user details (excluding sensitive info)
    user2: UserRead
    status: MatchStatusEnum
    created_at: datetime
    expires_at: datetime | None

    class Config:
        from_attributes = True

class MatchResult(BaseModel):
    """Schema specifically for returning a list of matches for a user."""
    match_id: uuid.UUID
    other_user: UserRead # The user they matched *with*
    compatibility_score: float = Field(..., ge=0, le=100)
    match_explanation: str | None = None
    suggested_starters: list[str] | None = None
    status: MatchStatusEnum
    created_at: datetime