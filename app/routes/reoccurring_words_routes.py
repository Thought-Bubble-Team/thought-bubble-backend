import nltk

nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('wordnet')
nltk.download('omw-1.4')

from fastapi import APIRouter, HTTPException, Query
from app.db.connection import supabase_admin
from app.utils.encryption import decrypt_text
from collections import Counter
from datetime import datetime, timedelta
import logging
import re
from typing import Dict

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

@router.get("/reoccurring-words/",
            summary="Get Reoccurring Words",
            description="Fetches and counts reoccurring words from a user's journal entries for a week or a month.",
            response_model=Dict,
            tags=["Reoccurring Words"])
def get_reoccurring_words(
    user_id: str = Query(..., description="The ID of the user (UUID)"),
    period: str = Query("weekly", enum=["weekly", "monthly"], description="Time period to analyze: weekly or monthly"),
    month: int = Query(None, description="Month number (1-12), required if period is monthly"),
    year: int = Query(None, description="Year, required if period is monthly")
):
    """
    Fetches and counts reoccurring words from a user's journal entries, either for a week or a month.
    """
    try:
        logger.info(f"Fetching reoccurring words for user {user_id} - Period: {period}")

        today = datetime.now()
        if period == "weekly":
            start_date = today - timedelta(days=today.weekday())  # Start of the week (Monday)
            end_date = start_date + timedelta(days=6)  # End of the week (Sunday)
        elif period == "monthly":
            if month is None or year is None:
                raise HTTPException(status_code=400, detail="Month and year are required for monthly period")
            start_date = datetime(year, month, 1)
            end_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
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

        # Return the most common words and their counts
        return {
            "message": "Reoccurring words fetched successfully",
            "word_counts": dict(word_counts.most_common(20))  # Limit to top 20 for brevity
        }

    except Exception as e:
        logger.error(f"Error fetching reoccurring words: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
