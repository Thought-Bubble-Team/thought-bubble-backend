from fastapi import APIRouter, HTTPException, Query
from app.db.connection import supabase_admin
from app.utils.encryption import decrypt_text
from datetime import datetime
import logging
import calendar
from collections import defaultdict

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/mood-bar/")
def get_monthly_emotion_summary(
    user_id: str = Query(..., description="User UUID"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., description="Year")
):
    """
    Get top 5 emotions for a user in a specific month.
    If a monthly summary already exists, returns the stored data.
    Otherwise, computes the summary, stores it, and returns it.
    Uses calendar.monthrange for accurate month-end determination.
    """
    try:
        # Calculate the start date for the given month and year.
        start_date = datetime(year, month, 1)
        # Use calendar.monthrange to determine the last day of the month.
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day)
        
        logger.info(f"Fetching mood bar data for {user_id} - {month}/{year}")

        # Define month abbreviation and year string for lookup.
        month_abbr = start_date.strftime("%b")
        year_str = str(year)

        # Check if a monthly summary already exists for this user and period.
        existing_summary = supabase_admin.table("monthly_summary") \
            .select("mood_bar") \
            .eq("user_id", user_id) \
            .eq("month", month_abbr) \
            .eq("year", year_str) \
            .execute()

        if existing_summary.data:
            logger.info(f"Monthly summary already exists for {user_id} - {month_abbr} {year_str}")
            stored_emotions = existing_summary.data[0].get("mood_bar", [])
            return {
                "message": "Monthly emotion percentages retrieved successfully",
                "emotions": stored_emotions
            }

        # Fetch journal entries for the specified period.
        journal_entries = supabase_admin.table("journal_entry") \
            .select("entry_id") \
            .eq("user_id", user_id) \
            .gte("created_at", start_date.strftime("%Y-%m-%d")) \
            .lte("created_at", end_date.strftime("%Y-%m-%d")) \
            .execute()

        if not journal_entries.data:
            return {"message": "No journal entries found for this period", "emotions": []}

        # Bulk fetch sentiment analysis data for these journal entries.
        entry_ids = [str(e['entry_id']) for e in journal_entries.data]
        sentiment_data = supabase_admin.table("sentiment_analysis") \
            .select("emotions") \
            .in_("entry_id", entry_ids) \
            .execute()

        # Aggregate emotion scores from the sentiment analysis results.
        emotion_totals = defaultdict(float)
        for analysis in sentiment_data.data:
            for emotion, score in analysis.get('emotions', {}).items():
                emotion_totals[emotion] += float(score)

        # Calculate percentages for each emotion.
        total_score = sum(emotion_totals.values())
        percentages = []
        if total_score > 0:
            top_emotions = sorted(emotion_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            total_percent = 0
            for i, (emotion, score) in enumerate(top_emotions):
                percent = round((score / total_score) * 100, 2)
                # Adjust the last emotion's percentage to ensure total sums to 100%
                if i == len(top_emotions) - 1:
                    percent = 100 - total_percent
                else:
                    total_percent += percent
                percentages.append({"emotion": emotion, "percentage": percent})

        # Store the computed monthly summary (only once).
        supabase_admin.table("monthly_summary").upsert({
            "user_id": user_id,
            "month": month_abbr,
            "year": year_str,
            "mood_bar": percentages or [],
            "mood_flow": None
        }).execute()

        return {
            "message": "Monthly emotion percentages retrieved successfully",
            "emotions": percentages
        }

    except Exception as e:
        logger.error(f"Error in mood bar: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")