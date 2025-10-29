import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert as pg_insert # For upsert
from datetime import datetime, timezone
import logging

from app.models.emotional_profile import EmotionalProfile
from app.schemas.emotional_profile import EmotionalProfileBase # Schema with scores

logger = logging.getLogger(__name__)

class ProfileService:
    """Service for handling EmotionalProfile database operations."""

    async def get_profile_by_user_id(self, db: AsyncSession, user_id: uuid.UUID) -> EmotionalProfile | None:
        """Retrieves an emotional profile by user ID."""
        result = await db.execute(
            select(EmotionalProfile).where(EmotionalProfile.user_id == user_id)
        )
        return result.scalars().first()

    async def update_or_create_profile(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        profile_data: EmotionalProfileBase, # The calculated scores
        text_samples: list[str] # The texts used for analysis
    ) -> EmotionalProfile:
        """
        Updates an existing emotional profile or creates a new one (Upsert).
        Stores the latest scores and the text samples used.
        """
        logger.info(f"Updating/Creating profile for user {user_id}")

        # Prepare values dictionary from the schema
        values_to_update = profile_data.model_dump()
        # Add other fields to update/insert
        values_to_update['user_id'] = user_id
        values_to_update['sample_texts'] = {"samples": text_samples} # Store texts as JSON
        values_to_update['profile_strength'] = len(text_samples)
        values_to_update['updated_at'] = datetime.now(timezone.utc)

        # Use PostgreSQL's ON CONFLICT DO UPDATE (Upsert)
        stmt = pg_insert(EmotionalProfile).values(
            **values_to_update
        ).on_conflict_do_update(
            index_elements=[EmotionalProfile.user_id], # Conflict target
            set_=values_to_update # Values to update on conflict
        ).returning(EmotionalProfile) # Return the inserted or updated row

        result = await db.execute(stmt)
        saved_profile = result.scalars().one()
        await db.commit() # Commit the transaction

        logger.info(f"Profile saved/updated for user {user_id}")
        return saved_profile

# Create a single instance
profile_service = ProfileService()