from transformers import pipeline
from typing import Dict

# Load sentiment model
try:
    sentiment_model = pipeline(
        "sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment"
    )
except Exception as e:
    raise Exception(f"Failed to load sentiment analysis model: {e}")

# Constants
LABEL_MAPPING = {"LABEL_0": "Negative", "LABEL_1": "Neutral", "LABEL_2": "Positive"}

# Functions
def analyze_sentiment(texts: list[str]) -> list[Dict[str, float | str]]:
    """Analyze sentiment in batch mode for efficiency."""
    if not isinstance(texts, list):
        raise ValueError("Input must be a list of strings.")

    texts = [text.strip() for text in texts if text.strip()]

    if not texts:
        return [{"sentiment": "Neutral", "confidence_score": 0.0}]

    results = sentiment_model(texts)

    return [
        {
            "sentiment": LABEL_MAPPING.get(res["label"], "Unknown"),
            "confidence_score": round(res["score"], 2)
        }
        for res in results
    ]
