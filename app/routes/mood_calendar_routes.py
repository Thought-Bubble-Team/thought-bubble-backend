from fastapi import APIRouter, HTTPException, Query
from app.db.connection import supabase_admin
from app.utils.encryption import decrypt_text
from datetime import datetime, timedelta
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/mood-calendar/")
def get_mood_calendar(user_id: str, month: int, year: int):
    # Fetches mood data for a given user in the specified month and year.
    try:
        logger.info(f"Fetching mood calendar for user {user_id} - {month}/{year}")

        # Calculate the start and end date of the month
        start_date = datetime(year, month, 1)
        end_date = start_date.replace(day=28) + timedelta(days=4)
        end_date = end_date - timedelta(days=end_date.day - 1)

        # Fetch journal entries within the date range
        response = (
            supabase_admin.table("journal_entry")
            .select("entry_id, created_at, content")
            .eq("user_id", user_id)
            .gte("created_at", start_date.strftime("%Y-%m-%d"))
            .lte("created_at", end_date.strftime("%Y-%m-%d"))
            .execute()
        )

        if not response.data:
            logger.warning(f"No journal entries found for user {user_id} in {month}/{year}")
            return {"message": "No journal entries found", "calendar": []}

        journal_entries = response.data
        mood_data = []

        for entry in journal_entries:
            date_string = entry["created_at"].split("T")[0]
            decrypted_content = decrypt_text(entry["content"])

            # Fetch sentiment analysis for this entry
            sentiment_response = (
                supabase_admin.table("sentiment_analysis")
                .select("sentiment, strongest_emotion")
                .eq("entry_id", entry["entry_id"])
                .execute()
            )

            sentiment_data = sentiment_response.data[0] if sentiment_response.data else {}

            mood_data.append({
                "date": date_string,
                "emotions": sentiment_data.get("strongest_emotion", "neutral"),
                "sentiment": sentiment_data.get("sentiment", "unknown"),
            })

        # Structure data in calendar format
        return {
            "message": "Mood calendar data fetched successfully",
            "calendar": mood_data
        }

    except Exception as e:
        logger.error(f"Error fetching mood calendar: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")