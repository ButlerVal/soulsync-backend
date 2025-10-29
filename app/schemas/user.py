import uuid
from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, field_validator # Import field_validator
import re # Import re for regex
# --- Base User Schemas ---

class UserBase(BaseModel):
    """Base schema with common user fields."""
    email: EmailStr
    full_name: str | None = None
    date_of_birth: date | None = None

class UserCreate(UserBase):
    """Schema for creating a new user (registration)."""
    password: str = Field(..., min_length=8) # [cite: 11]

    # --- FIX: ADD PASSWORD VALIDATION ---
    @field_validator('password')
    def validate_password_complexity_and_length(cls, v):
        # Check length (Bcrypt limit is 72 bytes, UTF-8 can be > 1 byte/char)
        if len(v.encode('utf-8')) > 72:
             raise ValueError('Password exceeds maximum length (72 bytes)')
        # [cite_start]PDF requirements check [cite: 11]
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v): # Example special chars
             raise ValueError('Password must contain at least one special character')
        return v

class UserRead(UserBase):
    """Schema for reading user data (API response)."""
    user_id: uuid.UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_active: datetime | None

    class Config:
        from_attributes = True # Replaces orm_mode = True

class UserInDB(UserRead):
    """Schema for user data stored in the DB (includes hash)."""
    password_hash: str

# Add this class to app/schemas/user.py

class UserUpdate(BaseModel):
    """Schema for updating user profile information."""
    full_name: str | None = Field(None, max_length=255)
    date_of_birth: date | None = None
    bio: str | None = Field(None, max_length=500) # Max length from PDF [cite: 143]
    # profile_photo_url: str | None = Field(None, max_length=512) # Add later when handling uploads
    use_case: str | None = Field(None, max_length=50) # Allow changing intent

    # Add validation if needed, e.g., for use_case enum    