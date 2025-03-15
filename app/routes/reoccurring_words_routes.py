import nltk

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")

from fastapi import APIRouter, HTTPException, Query
from app.db.connection import supabase_admin
from app.utils.encryption import decrypt_text
from collections import Counter
from datetime import datetime, timedelta
import logging
import re
from typing import Dict, Optional
from pydantic import BaseModel

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

router = APIRouter()
logger = logging.getLogger(__name__)

# Standard NLTK stop words
stop_words = set(stopwords.words('english'))

# Custom stop words for informal language
custom_stop_words = {"even", "im", "like", "gonna", "wanna", "gotta"}  

# Combine standard and custom stop words
stop_words = stop_words.union(custom_stop_words)

def extract_words(text: str) -> list[str]:
    """
    Extract words from the input text, convert to lowercase, remove punctuation,
    split into words, and remove stop words using NLTK.
    """
    text = text.lower()  # Lowercase the text
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    words = word_tokenize(text)  # Tokenize the text
    words = [word for word in words if word not in stop_words]  # Remove stop words
    return words

class ReoccurringWordsResponse(BaseModel):
    message: str
    word_counts: Dict[str, int]
    reoccurring_id: Optional[int] = None
    user_id: str
    month: Optional[str] = None
    year: Optional[str] = None
    weekly: Optional[str] = None
    created_at: Optional[datetime] = None

@router.get("/reoccurring-words/",
            summary="Get Reoccurring Words",
            description="Fetches and counts reoccurring words from a user's journal entries for a week or a month.",
            response_model=ReoccurringWordsResponse,
            tags=["Reoccurring Words"])
def get_reoccurring_words(
    user_id: str = Query(..., description="The ID of the user (UUID)"),
    period: str = Query("weekly", enum=["weekly", "monthly"], description="Time period to analyze: weekly or monthly"),
    month: int = Query(None, description="Month number (1-12), required if period is monthly"),
    year: int = Query(None, description="Year, required if period is monthly")
):
    """
    Fetches and counts reoccurring words from a user's journal entries for a week or a month.
    """
    try:
        logger.info(f"Fetching reoccurring words for user {user_id} - Period: {period}")

        today = datetime.now()
        start_date = None
        end_date = None
        month_str = None
        weekly_str = None

        if period == "weekly":
            start_date = today - timedelta(days=today.weekday())  # Start of the week (Monday)
            end_date = start_date + timedelta(days=6)  # End of the week (Sunday)
            weekly_str = f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"
        elif period == "monthly":
            if month is None or year is None:
                raise HTTPException(status_code=400, detail="Month and year are required for monthly period")
            start_date = datetime(year, month, 1)
            end_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            month_str = start_date.strftime("%b")  # "Jan", "Feb", etc.
        else:
            raise HTTPException(status_code=400, detail="Invalid period. Must be 'weekly' or 'monthly'")

        # Fetch journal entries within the date range
        response = (
            supabase_admin.table("journal_entry")
            .select("content")
            .eq("user_id", user_id)
            .gte("created_at", start_date.strftime("%Y-%m-%d"))
            .lte("created_at", end_date.strftime("%Y-%m-%d"))
            .execute()
        )

        if not response.data:
            logger.warning(f"No journal entries found for user {user_id} in the specified period")
            return {"message": "No journal entries found", "word_counts": {}}

        journal_entries = response.data
        all_words = []

        # Aggregate words from all entries
        for entry in journal_entries:
            decrypted_content = decrypt_text(entry["content"])
            words = extract_words(decrypted_content)
            all_words.extend(words)

        # Count word occurrences
        word_counts = Counter(all_words)
        word_counts_dict = dict(word_counts.most_common(20))  # Convert to dict before saving

        # Check if a record already exists for the user and period
        existing_record = (
            supabase_admin.table("reoccurring_words")
            .select("*")
            .eq("user_id", user_id)
            .eq("month", month_str)
            .eq("weekly", weekly_str)
            .execute()
        )
        
        existing_data = existing_record.data[0] if existing_record.data else None

        if existing_record.data:
            # Update the existing record
            logger.info(f"Updating existing reoccurring words for user {user_id}")
            update_response = (
                supabase_admin.table("reoccurring_words")
                .update({"word_counts": word_counts_dict})
                .eq("user_id", user_id)
                .eq("month", month_str)
                .eq("weekly", weekly_str)
                .execute()
            )
        else:
            # Create a new record
            logger.info(f"Creating new reoccurring words for user {user_id}")
            insert_data = {
                "user_id": user_id,
                "word_counts": word_counts_dict,
                "month": month_str,
                "year": str(year) if year else None,
                "weekly": weekly_str
            }
            response = supabase_admin.table("reoccurring_words").insert(insert_data).execute()

        # Properly return data for display in Swagger UI
        reoccurring_data = {
            "message": "Reoccurring words fetched and saved successfully",
            "word_counts": word_counts_dict,  # Display current word counts
            "user_id": user_id,
            "month": month_str,
            "year": str(year) if year else None,
            "weekly": weekly_str,
        }
        if existing_data:
             reoccurring_data["reoccurring_id"] = existing_data.get("reoccurring_id")
             reoccurring_data["created_at"] = existing_data.get("created_at")
        return reoccurring_data

    except Exception as e:
        logger.error(f"Error fetching reoccurring words: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
