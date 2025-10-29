import numpy as np
from app.ml.emotion_classifier import EmotionClassifier, CORE_EMOTIONS
from app.schemas.emotional_profile import EmotionalProfileBase
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

# Configure logging
logger = logging.getLogger(__name__)

class EmotionAnalysisService:
    """
    Service to load the emotion model and perform predictions.
    """
    def __init__(self):
        self.classifier = None # Will be loaded at startup

    def load_model(self):
        """Loads the trained emotion classifier model."""
        logger.info("Attempting to load emotion model...")
        try:
            self.classifier = EmotionClassifier()
            self.classifier.load_model()
            logger.info("Emotion model loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading emotion model: {e}", exc_info=True)
            self.classifier = None # Ensure classifier is None if loading fails

    def analyze_texts(self, texts: list[str]) -> EmotionalProfileBase | None:
        """
        Analyzes a list of texts and returns the emotion scores.
        """
        if not self.classifier:
            logger.error("Emotion model not loaded. Cannot perform analysis.")
            return None
        if not texts:
            logger.warning("Received empty list of texts for analysis.")
            return EmotionalProfileBase() # Return default scores

        try:
            logger.info(f"Analyzing {len(texts)} text samples...")
            # Get the average probability vector from the classifier
            avg_probs: np.ndarray = self.classifier.predict(texts) # type: ignore

            # Map probabilities to the EmotionalProfileBase schema
            scores_dict = {
                CORE_EMOTIONS[i]: float(avg_probs[i])
                for i in range(len(CORE_EMOTIONS))
            }
            logger.info("Analysis complete.")
            return EmotionalProfileBase(**scores_dict)

        except Exception as e:
            logger.error(f"Error during emotion analysis: {e}", exc_info=True)
            return None

# Create a single instance
emotion_service = EmotionAnalysisService()

# --- Lifespan Event Handler ---
# This special function runs code *before* the app starts serving requests
# and *after* it stops. We use it to load the ML model only once.

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run before the application starts
    print("INFO:     Application startup: Loading ML model...")
    emotion_service.load_model()
    yield
    # Code to run when the application is shutting down
    print("INFO:     Application shutdown.")