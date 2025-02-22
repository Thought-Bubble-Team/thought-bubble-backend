from pydantic import BaseModel, Field
from typing import Dict, Optional


# Schema for returning a journal entry
class JournalEntryResponse(BaseModel):
    entry_id: int
    user_id: str = Field(..., example="user123")
    content: str = Field(..., example="This is a sample journal entry.")
    title: str = Field(..., example="Sample Journal Entry")


# Represents a request to fetch a journal entry based on its ID
class EntryRequest(BaseModel):
    entry_id: int  # Unique identifier for a journal entry


# Represents the response after sentiment analysis of a journal entry
class SentimentResponse(BaseModel):
    entry_id: int
    content: Optional[str] = None
    preprocessed_content: Optional[str] = None
    sentiment: str  # Overall sentiment classification (e.g., positive, neutral, negative)
    confidence_score: float
    sentiment_summary: str
    emotion_summary: Dict[str, str]  # Breakdown of detected emotions with their intensity
