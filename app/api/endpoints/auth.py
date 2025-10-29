from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.token import (
    TokenPair, RefreshTokenRequest, 
    ForgotPasswordRequest, ResetPasswordRequest
)
from app.core.security import (
    verify_password, create_access_token, create_refresh_token,
    decode_token, create_password_reset_token, decode_password_reset_token
)
from app.services.email_service import email_service # Import mock email service

import logging # Import logging
import uuid # Import uuid

logger = logging.getLogger(__name__) # Add logger

from app.db.session import get_db_session
from app.services.user_service import user_service
from app.schemas.user import UserCreate, UserRead

router = APIRouter()

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Register a new user.
    """
    # Check if user already exists
    existing_user = await user_service.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    # Create new user
    new_user = await user_service.create_user(db, user_in=user_in)
    return new_user

@router.post("/login", response_model=TokenPair)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session)
):
    """
    User login to get access and refresh tokens.
    FastAPI's OAuth2PasswordRequestForm expects 'username' and 'password' fields.
    We will use the 'username' field to hold the user's email.
    """
    # Find user by email (which is in form_data.username)
    user = await user_service.get_user_by_email(db, email=form_data.username)
    
    # --- FIXED LOGIC ---
    
    # Step 1: Check if user exists *at all*
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Step 2: Check password
    # (Pylance now knows 'user' is not None here, so user.password_hash is safe)
    if not verify_password(form_data.password, user.password_hash):
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Step 3: Check if user is active
    # (Pylance also knows 'user' is not None here, so user.is_active is safe)
    if not user.is_active:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user.",
        )
    
    # --- END OF FIX ---

    # Create tokens
    token_data = {"sub": str(user.user_id)}
    access_token_str = create_access_token(data=token_data)
    refresh_token_str = create_refresh_token(data=token_data)
    
    return {
        "access_token": {"access_token": access_token_str},
        "refresh_token": {"refresh_token": refresh_token_str}
    }

@router.post("/refresh-token", response_model=TokenPair)
async def refresh_access_token(
    token_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Renews an access token using a valid refresh token.
    """
    token_data = decode_token(token_request.refresh_token) # Use the standard token decoder

    if not token_data or not token_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_service.get_user_by_id(db, user_id=uuid.UUID(token_data.user_id))

    if not user or not user.is_active:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Issue a new pair of tokens
    new_token_data = {"sub": str(user.user_id)}
    access_token_str = create_access_token(data=new_token_data)
    refresh_token_str = create_refresh_token(data=new_token_data)

    return {
        "access_token": {"access_token": access_token_str},
        "refresh_token": {"refresh_token": refresh_token_str}
    }


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Initiates the password reset process.
    Always returns 202 Accepted, even if user doesn't exist, to prevent email enumeration.
    """
    user = await user_service.get_user_by_email(db, email=request.email)

    if user:
        try:
            # User exists, create token and "send" email
            reset_token = create_password_reset_token(email=user.email)
            await email_service.send_password_reset_email(
                email_to=user.email, reset_token=reset_token
            )
        except Exception as e:
            # Log email sending failure
            logger.error(f"Failed to send password reset email for {request.email}: {e}", exc_info=True)
            # Still return 202 to the client

    # Do not let the client know if the user existed or not
    return {"msg": "If an account with this email exists, a password reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Resets the user's password using a valid token.
    """
    # 1. Validate the token
    email = decode_password_reset_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token."
        )

    # 2. Find the user
    user = await user_service.get_user_by_email(db, email=email)
    if not user or not user.is_active:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or is inactive."
        )

    # 3. Validate the new password (using schema validator)
    # Pydantic v2 validates on creation, but we can re-check rules
    try:
         # This is a bit redundant if UserCreate has the validator, but good practice
         UserCreate(email="test@test.com", password=request.new_password) 
    except ValueError as e:
         raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid password: {e}"
        )

    # 4. Update the password
    await user_service.update_user_password(db, user=user, new_password=request.new_password)

    return None # Return 204 No Content