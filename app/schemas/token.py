from pydantic import BaseModel, EmailStr, Field # Add EmailStr and Field

class Token(BaseModel):
    """Schema for the JWT access token."""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Schema for the data encoded inside the JWT."""
    user_id: str | None = None

class RefreshToken(BaseModel):
    """Schema for the JWT refresh token."""
    refresh_token: str
    token_type: str = "bearer"

class TokenPair(BaseModel):
    """Schema for returning both access and refresh tokens."""
    access_token: Token
    refresh_token: RefreshToken

# Add these new classes to app/schemas/token.py

class RefreshTokenRequest(BaseModel):
    """Schema for requesting a new access token using a refresh token."""
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    """Schema for the forgot password request."""
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    """Schema for the reset password request."""
    token: str
    new_password: str = Field(..., min_length=8)    