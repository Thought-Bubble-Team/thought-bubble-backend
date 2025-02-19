from fastapi import APIRouter, HTTPException
from app.db.connection import supabase_admin
from app.schemas.schemas import EntryRequest, SentimentResponse
from app.services.sentiment_analysis import analyze_sentiment, analyze_emotion, summarize_analysis, adjust_sentiment
from app.services.preprocessing import preprocess
from app.utils.encryption import decrypt_text
import logging

# Use the global logger initialized in logging.py
logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/admin/sentiment-analysis/", response_model=list[SentimentResponse])
def get_all_sentiment_analysis():
    """
    Admin: Get all sentiment analysis results.
    """
    try:
        logger.info("Fetching all sentiment analysis results")
        results = supabase_admin.table("sentiment_analysis").select("*").execute()
        if not results.data:
            logger.warning("No sentiment analysis results found")
            raise HTTPException(status_code=404, detail="No sentiment analysis results found")
        return results.data
    except Exception as e:
        logger.exception("Error fetching all sentiment analysis results")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/analyze-sentiment/", response_model=SentimentResponse)
def analyze_sentiment_endpoint(entry: EntryRequest):
    """
    API endpoint to analyze sentiment and emotion of a given journal entry
    and save the result to the database.
    """
    try:
        entry_id = entry.entry_id
        if not entry_id:
            logger.warning("Missing entry_id in request")
            raise HTTPException(status_code=400, detail="entry_id is missing")

        logger.info(f"Analyzing sentiment for entry ID: {entry_id}")

        # Fetch the journal entry from the database
        journal_entry = supabase_admin.table("journal_entry").select("*").eq("entry_id", entry_id).execute()
        if not journal_entry.data or len(journal_entry.data) == 0:
            logger.warning(f"Journal entry with ID {entry_id} not found")
            raise HTTPException(status_code=404, detail="Journal entry not found")
        
        # decrypt the journal entry content before analyzing sentiment
        encrypted_content = journal_entry.data[0]["content"]
        decrypted_content = decrypt_text(encrypted_content)
    
        # Step 1: Preprocess text
        preprocessed_text = preprocess(decrypted_content)

        # Step 2: Perform sentiment and emotion analysis
        sentiment_result = analyze_sentiment(preprocessed_text)
        emotion_result = analyze_emotion(preprocessed_text)

        # Step 3: Adjust sentiment based on emotions and add nuanced labels
        sentiment_result = adjust_sentiment(sentiment_result, emotion_result)

        # Step 4: Generate summary
        summary = summarize_analysis(sentiment_result, emotion_result)

        # Step 5: Save to database
        response = supabase_admin.table("sentiment_analysis").insert({
            "entry_id": entry_id,
            "sentiment": sentiment_result["sentiment"],
            "confidence_score": sentiment_result["confidence_score"],
            "emotions": emotion_result,
        }).execute()

        # Validate the response by checking if `data` is present
        if not response.data or len(response.data) == 0:
            logger.error(f"Supabase returned an unexpected response: {response}")
            raise HTTPException(status_code=500, detail="Failed to save sentiment analysis result")

        # Step 6: Return response
        logger.info(f"Successfully analyzed sentiment for entry ID: {entry_id}")
        return {
            "entry_id": entry_id,
            "sentiment": sentiment_result["sentiment"],
            "confidence_score": sentiment_result["confidence_score"],
            "sentiment_summary": summary["sentiment_summary"],
            "emotion_summary": summary["emotion_summary"],
        }
    except Exception as e:
        logger.exception("Unhandled error in analyze_sentiment_endpoint")
        raise HTTPException(status_code=500, detail="Internal Server Error")
