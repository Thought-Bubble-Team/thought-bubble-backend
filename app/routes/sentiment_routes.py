from fastapi import APIRouter, HTTPException, Query
from app.db.connection import supabase_admin
from app.schemas.schemas import SentimentResponse
from app.services import sentiment_analysis, preprocessing, emotions_analysis
from app.utils.encryption import decrypt_text
import logging, requests

# Use the global logger initialized in logging.py
logger = logging.getLogger(__name__)
router = APIRouter()
HUGGING_FACE_API = "https://Reimers-ThoughtBubble-Sentiment.hf.space/analyze-sentiment/"

@router.post("/analyze-sentiment/", response_model=SentimentResponse)
def analyze_sentiment_endpoint(entry_id: int = Query(..., description="The ID of the journal entry to analyze")):
    """API endpoint to analyze sentiment and emotion of a given journal entry."""

    if not entry_id:
        logger.warning("Missing entry_id in request")
        raise HTTPException(status_code=400, detail="entry_id is missing")

    response = requests.post(HUGGING_FACE_API, json={"entry_id": entry_id})
    
    logger.info(f"Received sentiment analysis request for entry ID: {entry_id}")

    try:
        # Fetch the journal entry from the database using the provided entry ID
        journal_entry = (
            supabase_admin.table("journal_entry")
            .select("*")
            .eq("entry_id", entry_id)
            .execute()
        )

        # If the entry does not exist, log a warning and return a 404 error
        if not journal_entry.data:
            logger.warning(f"Journal entry {entry_id} not found")
            raise HTTPException(status_code=404, detail="Journal entry not found")

        # Decrypt the stored content of the journal entry
        decrypted_content = decrypt_text(journal_entry.data[0]["content"])

        # Preprocess the text (e.g., lowercasing, stopword removal, lemmatization)
        preprocessed_text = preprocessing.preprocess(decrypted_content)

        logger.debug(f"Preprocessed Text: {preprocessed_text}")  # Log the processed text for debugging

        # Perform sentiment analysis on the preprocessed text (ensure it's in list format)
        sentiment_result = sentiment_analysis.analyze_sentiment([preprocessed_text])[0]

        # Perform emotion analysis on the same text
        emotion_result = emotions_analysis.analyze_emotion(preprocessed_text)

        # Adjust sentiment classification based on emotion analysis results
        sentiment_result = emotions_analysis.adjust_sentiment(sentiment_result, emotion_result)

        # Summarize the overall sentiment and emotions for easier interpretation
        summary = emotions_analysis.summarize_analysis(sentiment_result, emotion_result)

        logger.info(f"Sentiment analysis completed for Entry ID: {entry_id} - Sentiment: {sentiment_result['sentiment']}")

        # Save analysis result to Supabase
        response = (
            supabase_admin.table("sentiment_analysis")
            .insert(
                {
                    "entry_id": entry_id,
                    "sentiment": sentiment_result["sentiment"],
                    "confidence_score": sentiment_result["confidence_score"],
                    "emotions": emotion_result, 
                    "strongest_emotion": summary["strongest_emotion"],
                }
            )
            .execute()
        )

        # Log the insert response to detect issues
        logger.debug(f"Supabase Insert Response: {response}")

        # Ensure it was successfully inserted
        if not response.data:
            logger.error(f"Supabase Insert Failed: {response}")
            raise HTTPException(status_code=500, detail="Database insert failed")

        # Return the analysis results in a structured response
        return SentimentResponse(
            entry_id=entry_id,
            sentiment=sentiment_result["sentiment"],
            confidence_score=float(sentiment_result["confidence_score"]),
            sentiment_summary=summary["sentiment_summary"],
            emotion_summary=summary["emotion_summary"],
            strongest_emotion=summary["strongest_emotion"],
        )

    except Exception as e:
        # Log any unexpected errors and return a 500 Internal Server Error response
        logger.error(f"Error processing sentiment analysis for Entry ID {entry_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze sentiment")
    
@router.get("/sentiment-analysis/{entry_id}", response_model=SentimentResponse)
def get_sentiment_analysis_by_entry_id(entry_id: int):
    try:
        logger.info(f"Fetching sentiment analysis for entry ID: {entry_id}")
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

        # Retrieve sentiment classification and emotions from the database
        sentiment_result = {
            "sentiment": sentiment_data.get("sentiment", "unknown"),
            "confidence_score": float(sentiment_data.get("confidence_score", 0.0)),
        }
        emotion_result = sentiment_data.get("emotions", {})

        # Always generate sentiment and emotion summaries dynamically
        summary = emotions_analysis.summarize_analysis(sentiment_result, emotion_result)

        return SentimentResponse(
            entry_id=sentiment_data.get("entry_id"),
            sentiment=sentiment_result["sentiment"],
            confidence_score=sentiment_result["confidence_score"],
            sentiment_summary=summary["sentiment_summary"],  
            emotion_summary=summary["emotion_summary"],  
            strongest_emotion=summary["strongest_emotion"], 
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
