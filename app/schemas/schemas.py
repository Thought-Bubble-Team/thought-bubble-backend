from pydantic import BaseModel, Field
from typing import Dict, Optional


# Schema for returning a journal entry
class JournalEntryResponse(BaseModel):
    entry_id: int
    user_id: str = Field(..., example="user123")
    content: str = Field(..., example="This is a sample journal entry.")
    title: str = Field(..., example="Sample Journal Entry") 
    created_at: Optional[str] = Field(..., example="2021-08-01T12:00:00")
    updated_at: Optional[str] = Field(..., example="2021-08-01T12:00:00")


# Represents a request to fetch a journal entry based on its ID
class EntryRequest(BaseModel):
    entry_id: int  # Unique identifier for a journal entry


# Represents the response after sentiment analysis of a journal entry
class SentimentResponse(BaseModel):
    entry_id: int
    sentiment: str  # Overall sentiment classification (e.g., positive, neutral, negative)
    confidence_score: float
    analysis_feedback: Optional[str] = None
    strongest_emotion: str


# Password Reset Schema
class PasswordResetRequest(BaseModel):
    user_id: str = Field(..., description="Supabase user ID")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password")
