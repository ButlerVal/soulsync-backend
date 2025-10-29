import torch
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
    BatchEncoding
)
import numpy as np
import os
# Removed: BASE_DIR, Dataset imports, Trainer, TrainingArguments, pickle
from typing import cast
import logging

logger = logging.getLogger(__name__)

# --- 1. Define Model ID and Core Emotions ---
# --- REPLACE THIS with your Hugging Face Model ID ---
HF_MODEL_ID = "Valisces/soulsync-emotion-model" # E.g., "ButlerVal/soulsync-emotion-model"
# --- /REPLACE ---

CORE_EMOTIONS = {
    0: "joy", 1: "sadness", 2: "anxiety", 3: "calm",
    4: "anger", 5: "excitement", 6: "empathy", 7: "confidence"
}
NUM_LABELS = len(CORE_EMOTIONS)

# --- (GO_EMOTIONS_MAP is no longer needed for loading/prediction) ---
# --- (EmotionDataset class is no longer needed) ---

# --- Simplified Classifier Class ---
class EmotionClassifier:
    def __init__(self):
        self.model_load_path = HF_MODEL_ID # Load directly from Hub ID
        self.tokenizer: DistilBertTokenizer | None = None
        self.model: DistilBertForSequenceClassification | None = None
        self.device: torch.device | None = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Removed _initialize_model_and_tokenizer
    # Removed _prepare_data
    # Removed train_model

    def load_model(self):
        """Loads the model directly from Hugging Face Hub."""
        logger.info(f"Loading model and tokenizer from Hugging Face Hub: {self.model_load_path}...")
        try:
            # from_pretrained handles download, caching, and map_location
            self.tokenizer = cast(
                DistilBertTokenizer,
                DistilBertTokenizer.from_pretrained(self.model_load_path)
            )
            self.model = cast(
                DistilBertForSequenceClassification,
                DistilBertForSequenceClassification.from_pretrained(self.model_load_path)
            )

            assert self.model is not None, "Model loading failed"
            assert self.device is not None, "Device not initialized"
            self.model = self.model.to(self.device) # Move to appropriate device
            self.model.eval()
            logger.info(f"Model loaded successfully onto device: {self.device}")

        except Exception as e:
            logger.error(f"Error loading model from {self.model_load_path}: {e}", exc_info=True)
            self.model = None
            self.tokenizer = None
            # Raise a more specific error or handle inability to load
            raise RuntimeError(f"Failed to load model from Hugging Face Hub: {e}")

    def predict(self, texts: list[str]) -> np.ndarray | None:
        """Analyzes text using the loaded model."""
        if not self.model or not self.tokenizer or not self.device:
            logger.error("Model, tokenizer, or device not loaded/initialized. Cannot predict.")
            return None

        self.model.eval()
        encodings: BatchEncoding = self.tokenizer(
            texts, truncation=True, padding=True, max_length=128, return_tensors="pt"
        )

        encodings = encodings.to(self.device)
        input_ids = encodings['input_ids']
        attention_mask = encodings['attention_mask']

        with torch.no_grad():
            outputs = self.model(input_ids, attention_mask=attention_mask)
            probs = torch.nn.functional.softmax(outputs.logits, dim=1)
            avg_probs = torch.mean(probs, dim=0)

        return avg_probs.cpu().numpy()
