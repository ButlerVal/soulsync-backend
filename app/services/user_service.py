from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash
from typing import Any, Dict
import uuid
import logging

logger = logging.getLogger(__name__)

class UserService:
    """
    Service class for user-related database operations.
    """

    async def get_user_by_email(self, db: AsyncSession, email: str) -> User | None:
        """
        Fetches a user from the database by their email.
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_user_by_id(self, db: AsyncSession, user_id: uuid.UUID) -> User | None:
        """
        Fetches a user from the database by their user_id.
        """
        result = await db.execute(select(User).where(User.user_id == user_id))
        return result.scalars().first()

    async def create_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        """
        Creates a new user in the database.
        """
        # Create the new User model instance
        new_user = User(
            email=user_in.email,
            password_hash=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            date_of_birth=user_in.date_of_birth
        )

        # Add to the session and commit
        db.add(new_user)
        await db.commit()

        # Refresh the instance to get data from the DB (like created_at)
        await db.refresh(new_user)

        return new_user
    
    async def update_user(self, db: AsyncSession, user: User, user_in: UserUpdate) -> User:
        """Updates a user's profile information in the database."""
        logger.info(f"Updating profile for user {user.user_id}")

        # Get update data, excluding unset fields to avoid overwriting with None
        update_data: Dict[str, Any] = user_in.model_dump(exclude_unset=True)

        # Update the user object with new data
        for field, value in update_data.items():
            setattr(user, field, value)

        # Mark the object as modified and commit
        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"Profile updated for user {user.user_id}")
        return user
    

    async def update_user_password(self, db: AsyncSession, user: User, new_password: str) -> User:
        """Updates a user's password."""
        logger.info(f"Updating password for user {user.user_id}")

        user.password_hash = get_password_hash(new_password)

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"Password updated for user {user.user_id}")
        return user

# Create a single, importable instance of the service
user_service = UserService()