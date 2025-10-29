import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.models.emotional_profile import EmotionalProfile
from app.models.match import Match, MatchStatusEnum, UserActionEnum
from datetime import datetime, timedelta, timezone
from typing import Tuple
import uuid
import logging

logger = logging.getLogger(__name__)

class MatchService:
    """
    Service class for calculating and managing user matches.
    """

    def _calculate_cosine_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """Calculates cosine similarity between two 8-dim emotion vectors."""
        if vector1 is None or vector2 is None or vector1.shape != (8,) or vector2.shape != (8,):
            logger.warning("Invalid vectors provided for cosine similarity calculation.")
            return 0.0

        dot_product = np.dot(vector1, vector2)
        norm1 = np.linalg.norm(vector1)
        norm2 = np.linalg.norm(vector2)

        if norm1 == 0 or norm2 == 0:
            return 0.0 # Avoid division by zero

        similarity = dot_product / (norm1 * norm2)
        # Clip similarity to [-1, 1] range due to potential float errors
        similarity = np.clip(similarity, -1.0, 1.0)

        # [cite_start]Normalize to 0-100% score as per PDF [cite: 90]
        score = (similarity + 1) / 2 * 100
        return score

    def _apply_use_case_weighting(self, base_score: float, profile1: EmotionalProfile, profile2: EmotionalProfile, use_case: str) -> tuple[float, str]:
        """Applies adjustments based on the use case (Friends, Dating, etc.)."""
        score = base_score
        explanation_parts = [f"Base score: {base_score:.1f}%"]

        # [cite_start]--- Friends Weighting [cite: 91-95] ---
        if use_case == "friends":
            # Calm alignment check
            if abs(profile1.calm - profile2.calm) <= 0.2: # High weight [cite: 92]
                score += 5
                explanation_parts.append("+Similar Calm levels")
            # Empathy alignment check
            if abs(profile1.empathy - profile2.empathy) <= 0.3: # High weight [cite: 92]
                score += 5
                explanation_parts.append("+Similar Empathy levels")
             # [cite_start]Similar Joy/Excitement boost [cite: 93]
            if abs((profile1.joy + profile1.excitement) - (profile2.joy + profile2.excitement)) <= 0.4:
                 score += 3
                 explanation_parts.append("+Similar Energy levels")
            # [cite_start]Penalize both high Anxiety [cite: 94]
            if profile1.anxiety > 0.7 and profile2.anxiety > 0.7:
                score -= 10
                explanation_parts.append("-Both High Anxiety")
            # [cite_start]Optimal: Complementary energy (simple check) [cite: 95]
            # (Could be more sophisticated later)
            if (profile1.calm > 0.6 and profile2.excitement > 0.6) or \
               (profile2.calm > 0.6 and profile1.excitement > 0.6):
                score += 4
                explanation_parts.append("+Complementary Energy (Calm/Excited)")


        # [cite_start]--- Dating Weighting [cite: 96-100] ---
        elif use_case == "dating":
            # [cite_start]Complementary Anxiety (one high, one low) [cite: 97]
            if (profile1.anxiety > 0.6 and profile2.anxiety < 0.4) or \
               (profile2.anxiety > 0.6 and profile1.anxiety < 0.4):
                 score += 8
                 explanation_parts.append("+Complementary Anxiety")
            # [cite_start]Similar Excitement boost [cite: 98]
            if abs(profile1.excitement - profile2.excitement) <= 0.3:
                score += 4
                explanation_parts.append("+Similar Excitement")
            # [cite_start]Both high Empathy boost [cite: 98]
            if profile1.empathy > 0.6 and profile2.empathy > 0.6:
                score += 6
                explanation_parts.append("+Both High Empathy")
            # [cite_start]Emotional stability boost (low Anger) [cite: 99]
            if profile1.anger < 0.3 and profile2.anger < 0.3:
                 score += 5
                 explanation_parts.append("+Low Anger (Stability)")
            # [cite_start]Penalize both high Anger or Anxiety [cite: 100]
            if profile1.anger > 0.6 and profile2.anger > 0.6:
                score -= 10
                explanation_parts.append("-Both High Anger")
            if profile1.anxiety > 0.7 and profile2.anxiety > 0.7:
                 score -= 8
                 explanation_parts.append("-Both High Anxiety")

        # [cite_start]--- Cofounder Weighting [cite: 101-105] ---
        elif use_case == "cofounder":
            # [cite_start]Complementary Confidence [cite: 102]
            if (profile1.confidence > 0.6 and profile2.confidence < 0.4) or \
               (profile2.confidence > 0.6 and profile1.confidence < 0.4):
                 score += 10
                 explanation_parts.append("+Complementary Confidence")
            # [cite_start]Similar Energy/Excitement boost [cite: 103]
            if abs((profile1.joy + profile1.excitement) - (profile2.joy + profile2.excitement)) <= 0.4:
                 score += 5
                 explanation_parts.append("+Similar Energy levels")
            # [cite_start]Require one low Anxiety [cite: 104]
            if profile1.anxiety < 0.4 or profile2.anxiety < 0.4:
                 score += 4 # Small boost if condition met
                 explanation_parts.append("+One partner has low Anxiety")
            else:
                 score -= 8 # Penalize if both high anxiety
                 explanation_parts.append("-Both have moderate/high Anxiety")
            # [cite_start]Penalize both low Confidence [cite: 105]
            if profile1.confidence < 0.3 and profile2.confidence < 0.3:
                 score -= 12
                 explanation_parts.append("-Both Low Confidence")

        # [cite_start]--- Support Weighting [cite: 106-110] ---
        # Assume profile1 is the potential Supporter, profile2 is the Seeker
        elif use_case == "support_seeker": # seeker requesting support
            if profile1.empathy > 0.7 and profile1.calm > 0.6 and profile1.anxiety < 0.4: # [cite: 107, 108]
                score += 15 # Big boost for good supporter traits
                explanation_parts.append("+Potential supporter has high Empathy & Calm, low Anxiety")
            else:
                score -= 20 # Penalize heavily if supporter traits aren't met
                explanation_parts.append("-Potential supporter lacks key Support traits")
             # [cite_start]Complementary pairing boost [cite: 110]
            if profile2.anxiety > 0.5: # If seeker has anxiety
                score += 5
                explanation_parts.append("+Good Supporter/Seeker dynamic potential")

        elif use_case == "support_provider": # provider offering support
             # Check seeker traits (allow high anxiety)
            if profile2.empathy < 0.7 and profile2.calm < 0.6: # If seeker needs support
                score += 5
                explanation_parts.append("+Potential seeker may benefit from support")
             # [cite_start]Complementary pairing boost [cite: 110]
            if profile1.empathy > 0.7 and profile1.calm > 0.6 and profile1.anxiety < 0.4: # [cite: 107, 108]
                score += 15
                explanation_parts.append("+You have strong Supporter traits")
            else:
                score -= 10 # Penalize provider if they lack traits
                explanation_parts.append("-Consider enhancing Support traits")


        # Clip final score to 0-100
        final_score = np.clip(score, 0, 100)
        explanation = ". ".join(explanation_parts)
        return final_score, explanation


    async def find_potential_matches(self, db: AsyncSession, user: User, user_profile: EmotionalProfile):
        """
        Finds potential matches for a given user based on their profile and use case.
        This is a simplified version - a real system would need filters, pagination,
        and exclusion of existing matches/blocks.
        """
        logger.info(f"Finding potential matches for user {user.user_id} ({user.use_case})...")

        # Fetch all *other* users and their profiles (INEFFICIENT - needs optimization later)
        result = await db.execute(
            select(User, EmotionalProfile)
            .join(EmotionalProfile, User.user_id == EmotionalProfile.user_id)
            .where(User.user_id != user.user_id)
            # TODO: Add filters for location, age, preferences, is_active etc.
        )
        potential_partners = result.all() # Returns list of tuples (User, EmotionalProfile)

        if not potential_partners:
            logger.info("No potential partners found for matching.")
            return []

        matches = []
        user_vector = np.array([
            user_profile.joy, user_profile.sadness, user_profile.anxiety, user_profile.calm,
            user_profile.anger, user_profile.excitement, user_profile.empathy, user_profile.confidence
        ])

        for partner, partner_profile in potential_partners:
             # --- Determine effective use case for matching ---
             # Simplification: If either user specified 'dating', match on dating rules.
             # If either specified 'cofounder', match on cofounder rules (unless dating).
             # If support is involved, use specific support rules.
             # Otherwise, default to friends.
             effective_use_case = "friends" # Default
             user1_uc = user.use_case
             user2_uc = partner.use_case

             if user1_uc == "dating" or user2_uc == "dating":
                  effective_use_case = "dating"
             elif user1_uc == "cofounder" or user2_uc == "cofounder":
                  effective_use_case = "cofounder"
             elif user1_uc == "support" and user2_uc != "support":
                  effective_use_case = "support_provider" # User 1 is offering support
             elif user2_uc == "support" and user1_uc != "support":
                  effective_use_case = "support_seeker" # User 1 needs support

             # Don't match two 'support' providers directly unless explicitly needed later
             elif user1_uc == "support" and user2_uc == "support":
                 continue # Skip for now


             partner_vector = np.array([
                 partner_profile.joy, partner_profile.sadness, partner_profile.anxiety, partner_profile.calm,
                 partner_profile.anger, partner_profile.excitement, partner_profile.empathy, partner_profile.confidence
             ])

             # [cite_start]Calculate base similarity [cite: 89]
             base_score = self._calculate_cosine_similarity(user_vector, partner_vector)

             # Apply weighting
             final_score, explanation = self._apply_use_case_weighting(
                base_score, user_profile, partner_profile, effective_use_case
            )

             # [cite_start]TODO: Add filtering by user preferences [cite: 115]
             # [cite_start]TODO: Exclude already connected/passed matches [cite: 116]

             if final_score >= 40: # Arbitrary threshold for now
                 match_data = {
                     "user1_id": user.user_id,
                     "user2_id": partner.user_id,
                     "compatibility_score": final_score,
                     "match_explanation": explanation,
                     # [cite_start]TODO: Generate suggested starters [cite: 123]
                     "suggested_starters": {"starters": ["Say hi!", "What's up?"]}, # Placeholder
                     "status": MatchStatusEnum.pending,
                     "expires_at": datetime.now(timezone.utc) + timedelta(days=14)
                 }
                 matches.append(match_data)

        # [cite_start]Sort by score (descending) [cite: 117]
        matches.sort(key=lambda x: x['compatibility_score'], reverse=True)

        logger.info(f"Generated {len(matches)} potential matches.")
        return matches # Return raw match data for now

    async def save_matches(self, db: AsyncSession, matches_data: list[dict]):
        """Saves generated matches to the database."""
        if not matches_data:
            return

        logger.info(f"Saving {len(matches_data)} matches to database...")
        new_matches = [Match(**data) for data in matches_data]
        db.add_all(new_matches)
        await db.commit()
        logger.info("Matches saved successfully.")

    async def get_daily_matches_for_user(self, db: AsyncSession, user_id: uuid.UUID, limit: int = 10):
        """Retrieves existing pending matches for a user."""
        logger.info(f"Fetching daily matches for user {user_id}...")
        # Query for matches where user is user1 OR user2 and status is pending
        result = await db.execute(
            select(Match)
            .where(
                (Match.user1_id == user_id) | (Match.user2_id == user_id)
            )
            .where(Match.status == MatchStatusEnum.pending)
            # TODO: Add filtering for expires_at > now()
            .order_by(Match.compatibility_score.desc())
            .limit(limit)
        )
        matches = result.scalars().all()
        logger.info(f"Found {len(matches)} pending matches.")
        return matches
    
    # Add these inside the MatchService class

    async def get_match_by_id(self, db: AsyncSession, match_id: uuid.UUID) -> Match | None:
        """Retrieves a specific match by its ID."""
        result = await db.execute(select(Match).where(Match.match_id == match_id))
        return result.scalars().first()

    async def update_match_action(
        self,
        db: AsyncSession,
        match: Match,
        user_id: uuid.UUID,
        action: UserActionEnum # Pass in the action ('connected' or 'passed')
    ) -> Match:
        """Updates a user's action on a match and checks for mutual connection."""
        is_user1 = (match.user1_id == user_id)
        current_time = datetime.now(timezone.utc) # Use timezone-aware datetime

        if is_user1:
            if match.user1_action != UserActionEnum.none:
                logger.warning(f"User {user_id} already acted on match {match.match_id}")
                return match # Prevent re-acting
            match.user1_action = action
            other_user_action = match.user2_action
        else: # User is user2
            if match.user2_action != UserActionEnum.none:
                logger.warning(f"User {user_id} already acted on match {match.match_id}")
                return match # Prevent re-acting
            match.user2_action = action
            other_user_action = match.user1_action

        # Check for outcomes
        if action == UserActionEnum.passed:
            match.status = MatchStatusEnum.passed
            logger.info(f"Match {match.match_id} passed by user {user_id}.")
        elif action == UserActionEnum.connected and other_user_action == UserActionEnum.connected:
            match.status = MatchStatusEnum.connected
            match.connected_at = current_time
            logger.info(f"Mutual connection formed for match {match.match_id}!")
            # --- TODO: Create a Conversation between the users ---
            # await message_service.get_or_create_conversation(db, match.user1_id, match.user2_id)
            # --- TODO: Send notifications (WebSocket/Push) to both users ---
        else:
            # Action is 'connected', but other user hasn't acted or passed yet
            logger.info(f"User {user_id} connected on match {match.match_id}, waiting for other user.")
            pass # Status remains 'pending' until both connect or one passes

        await db.commit()
        await db.refresh(match)
        return match

# Create a single instance
match_service = MatchService()