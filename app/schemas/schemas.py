from pydantic import BaseModel
from typing import Dict

class EntryRequest(BaseModel):
    entry_id: int

class SentimentResponse(BaseModel):
    entry_id: int
    content: str
    preprocessed_content: str
    sentiment: str  # Includes nuanced labels like "Slightly Positive", "Strongly Negative"
    confidence_score: float
    sentiment_summary: str
    emotion_summary: Dict[str, str]  # Handles both percentage-based and human-friendly summaries

class JournalEntry(BaseModel):
    content: str
