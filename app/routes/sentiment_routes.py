from fastapi import APIRouter, HTTPException, Query
from app.db.connection import supabase_admin
from app.schemas.schemas import SentimentResponse
from app.utils.encryption import decrypt_text
import logging, requests

# Use the global logger initialized in logging.py
logger = logging.getLogger(__name__)
router = APIRouter()
HUGGING_FACE_API = "https://reimers-thoughtbubble-sentiment.hf.space/analyze-sentiment/"

@router.post("/analyze-sentiment/", response_model=SentimentResponse)
def analyze_sentiment_endpoint(entry_id: int):
    """Sends journal entry to Hugging Face API for sentiment & emotion analysis."""

    if not entry_id:
        logger.warning("Missing entry_id in request")
        raise HTTPException(status_code=400, detail="entry_id is missing")

    logger.info(f"Requesting sentiment analysis for entry ID: {entry_id}")

    try:
        # Fetch journal entry from database
        journal_entry = (
            supabase_admin.table("journal_entry")
            .select("*")
            .eq("entry_id", entry_id)
            .execute()
        )

        if not journal_entry.data:
            logger.warning(f"Journal entry {entry_id} not found")
            raise HTTPException(status_code=404, detail="Journal entry not found")

        # Decrypt content
        decrypted_content = decrypt_text(journal_entry.data[0]["content"])

        # Ensure the content is valid
        if not decrypted_content.strip():
            logger.warning(f"Empty journal content for entry {entry_id}")
            raise HTTPException(status_code=400, detail="Journal content cannot be empty")

        # Send request to Hugging Face API
        payload = {"content": decrypted_content}
        logger.info(f"Sending request to Hugging Face API: {HUGGING_FACE_API} with payload {payload}")

        response = requests.post(HUGGING_FACE_API, json=payload, headers={"Content-Type": "application/json"})

        # Log the raw response
        logger.info(f"Hugging Face API Response Status: {response.status_code}")
        logger.info(f"Hugging Face API Response Text: {response.text}")  

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Hugging Face API Error: {response.text}")

        # Ensure response is JSON
        try:
            analysis_result = response.json()
        except requests.exceptions.JSONDecodeError:
            logger.error("Hugging Face API did not return valid JSON")
            raise HTTPException(status_code=500, detail="Invalid response from Hugging Face API")

        # Save results to database
        db_response = (
            supabase_admin.table("sentiment_analysis")
            .insert(
                {
                    "entry_id": entry_id,
                    "sentiment": analysis_result["sentiment"],
                    "confidence_score": analysis_result["confidence_score"],
                    "emotions": analysis_result["emotion_result"],
                    "strongest_emotion": analysis_result["strongest_emotion"],
                    "analysis_feedback": analysis_result["analysis_feedback"],
                }
            )
            .execute()
        )

        if not db_response.data:
            logger.error("Failed to store sentiment analysis results in database")
            raise HTTPException(status_code=500, detail="Database insert failed")

        return SentimentResponse(
            entry_id=entry_id,
            sentiment=analysis_result["sentiment"],
            confidence_score=float(analysis_result["confidence_score"]),
            emotions=analysis_result["emotion_result"],
            strongest_emotion=analysis_result["strongest_emotion"],
        )

    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze sentiment")
    
@router.get("/sentiment-analysis/{entry_id}", response_model=SentimentResponse)
def get_sentiment_analysis_by_entry_id(entry_id: int, user_id: str = Query(..., description="The ID of the user")):
    try:
        logger.info(f"Fetching sentiment analysis for entry ID: {entry_id} and user ID: {user_id}")

        # Fetch sentiment analysis from the database
        results = (
            supabase_admin.table("sentiment_analysis")
            .select("*")
            .eq("entry_id", entry_id)
            .execute()
        )

        if not results.data:
            logger.warning(f"No sentiment analysis found for entry ID: {entry_id}")
            raise HTTPException(status_code=404, detail="Sentiment analysis not found")

        sentiment_data = results.data[0]

        # Fetch the associated journal entry to verify user ownership
        journal_entry = (
            supabase_admin.table("journal_entry")
            .select("user_id")
            .eq("entry_id", entry_id)
            .execute()
        )

        if not journal_entry.data or journal_entry.data[0]["user_id"] != user_id:
            logger.warning(f"Unauthorized access attempt for sentiment analysis of entry ID {entry_id}")
            raise HTTPException(status_code=403, detail="Unauthorized access to sentiment data")

        return SentimentResponse(
            entry_id=sentiment_data.get("entry_id"),
            sentiment=sentiment_data.get("sentiment", "unknown"),
            confidence_score=float(sentiment_data.get("confidence_score", 0.0)),
            sentiment_summary=sentiment_data.get("sentiment_summary", "No summary available"),  
            emotion_summary=sentiment_data.get("emotion_summary", {}),  
            strongest_emotion=sentiment_data.get("strongest_emotion", "neutral"), 
        )

    except Exception as e:
        logger.error(f"Error fetching sentiment analysis for entry ID {entry_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.delete("/sentiment-analysis/{entry_id}", status_code=204)  # 204 No Content on success
def delete_sentiment_analysis_by_entry_id(entry_id: int):
    # Delete sentiment analysis for a specific entry ID.
    try:
        logger.info(f"Deleting sentiment analysis for entry ID: {entry_id}")
        response = (
            supabase_admin.table("sentiment_analysis")
            .delete()
            .eq("entry_id", entry_id)
            .execute()
        )

        if not response.data:
            logger.error(f"Supabase returned an unexpected response: {response}")
            raise HTTPException(status_code=500, detail="Failed to delete sentiment analysis")

        logger.info(f"Sentiment analysis deleted for entry ID: {entry_id}")

    except Exception as e:
        logger.error(f"Error deleting sentiment analysis for entry ID {entry_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
