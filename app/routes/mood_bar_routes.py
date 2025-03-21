from fastapi import APIRouter, HTTPException, Query
from app.db.connection import supabase_admin
from datetime import datetime, timedelta
import logging
from collections import defaultdict

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/mood-bar/")
def get_monthly_emotion_summary(
    user_id: str = Query(..., description="User UUID"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., description="Year")
):
    # Get top 5 emotions for a user in a specific month.
    try:
        # Calculate the start and end dates for the specified month
        start_date = datetime(year, month, 1)
        # Calculate last day of month using a standard trick:
        end_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        
        logger.info(f"Fetching mood bar data for {user_id} - {month}/{year}")

        # First, check if a monthly summary record already exists for this user and period.
        month_abbr = start_date.strftime("%b")
        year_str = str(year)
        existing_summary = supabase_admin.table("monthly_summary") \
            .select("mood_bar") \
            .eq("user_id", user_id) \
            .eq("month", month_abbr) \
            .eq("year", year_str) \
            .execute()

        if existing_summary.data:
            # If record exists, return the stored mood_bar data.
            logger.info(f"Monthly summary already exists for {user_id} - {month_abbr} {year_str}")
            stored_emotions = existing_summary.data[0].get("mood_bar", [])
            return {
                "message": "Monthly emotion percentages retrieved successfully",
                "emotions": stored_emotions
            }

        # Get journal entries for the period if no summary exists
        journal_entries = supabase_admin.table("journal_entry") \
            .select("entry_id") \
            .eq("user_id", user_id) \
            .gte("created_at", start_date.strftime("%Y-%m-%d")) \
            .lte("created_at", end_date.strftime("%Y-%m-%d")) \
            .execute()

        if not journal_entries.data:
            return {"message": "No journal entries found for this period", "emotions": []}

        # Get sentiment analyses for the journal entries in bulk
        entry_ids = [str(e['entry_id']) for e in journal_entries.data]
        sentiment_data = supabase_admin.table("sentiment_analysis") \
            .select("emotions") \
            .in_("entry_id", entry_ids) \
            .execute()

        # Aggregate emotion scores from sentiment analyses
        emotion_totals = defaultdict(float)
        for analysis in sentiment_data.data:
            for emotion, score in analysis.get('emotions', {}).items():
                emotion_totals[emotion] += float(score)

        # Calculate percentages for each emotion
        total_score = sum(emotion_totals.values())
        percentages = []
        if total_score > 0:
            top_emotions = sorted(emotion_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            total_percent = 0
            for i, (emotion, score) in enumerate(top_emotions):
                percent = round((score / total_score) * 100, 2)
                # Adjust the last emotion's percentage to sum to 100%
                if i == len(top_emotions) - 1:
                    percent = 100 - total_percent
                else:
                    total_percent += percent
                percentages.append({"emotion": emotion, "percentage": percent})

        # Store the computed summary in monthly_summary table (only once)
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