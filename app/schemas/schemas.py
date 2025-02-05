from pydantic import BaseModel
from typing import Dict

# Represents a request to fetch a journal entry based on its ID
class EntryRequest(BaseModel):
    entry_id: int  # Unique identifier for a journal entry

# Represents the response after sentiment analysis of a journal entry
class SentimentResponse(BaseModel):
    entry_id: int 
    content: str  
    preprocessed_content: str  
    sentiment: str  # Overall sentiment classification (e.g., positive, neutral, negative)
    confidence_score: float 
    sentiment_summary: str  
    emotion_summary: Dict[str, str]  # Breakdown of detected emotions with their intensity

# Represents a new journal entry submission
class JournalEntry(BaseModel):
    content: str  # The actual text of the journal entry
