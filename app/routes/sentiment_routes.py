from fastapi import APIRouter, HTTPException
from app.db.connection import supabase_admin
from app.schemas.schemas import EntryRequest, SentimentResponse
from app.services import sentiment_analysis, preprocessing
from app.utils.encryption import decrypt_text
import logging

# Use the global logger initialized in logging.py
logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/admin/sentiment-analysis/", response_model=list[SentimentResponse])
def get_all_sentiment_analysis() -> list[SentimentResponse]:
    # Admin: Get all sentiment analysis results.
    logger.info("Fetching all sentiment analysis results")
    results = supabase_admin.table("sentiment_analysis").select("*").execute()

    if not results.data:
        logger.warning("No sentiment analysis results found")
        raise HTTPException(status_code=404, detail="No sentiment analysis results found")

    return [SentimentResponse(**item) for item in results.data]


@router.post("/analyze-sentiment/", response_model=SentimentResponse)
def analyze_sentiment_endpoint(entry: EntryRequest) -> SentimentResponse:
    # API endpoint to analyze sentiment and emotion of a given journal entry.
    entry_id = entry.entry_id
    if not entry_id:
        logger.warning("Missing entry_id in request")
        raise HTTPException(status_code=400, detail="entry_id is missing")

    logger.info(f"Analyzing sentiment for entry ID: {entry_id}")

    journal_entry = (
        supabase_admin.table("journal_entry").select("*").eq("entry_id", entry_id).execute()
    )  # type: ignore

    if not journal_entry.data or not journal_entry.data[0]:
        logger.warning(f"Journal entry with ID {entry_id} not found")
        raise HTTPException(status_code=404, detail="Journal entry not found")

    encrypted_content = journal_entry.data[0]["content"]
    decrypted_content = decrypt_text(encrypted_content)
    preprocessed_text = preprocessing.preprocess(decrypted_content)

    sentiment_result = sentiment_analysis.analyze_sentiment(preprocessed_text)
    emotion_result = sentiment_analysis.analyze_emotion(preprocessed_text)
    sentiment_result = sentiment_analysis.adjust_sentiment(sentiment_result, emotion_result)
    summary = sentiment_analysis.summarize_analysis(sentiment_result, emotion_result)

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
        .execute()  # type: ignore
    )

    if not response.data:
        logger.error(f"Supabase returned an unexpected response: {response}")
        raise HTTPException(status_code=500, detail="Failed to save sentiment analysis result")

    logger.info(f"Successfully analyzed sentiment for entry ID: {entry_id}")

    return SentimentResponse(
        entry_id=entry_id,
        sentiment=sentiment_result["sentiment"],
        confidence_score=float(sentiment_result["confidence_score"]),
        sentiment_summary=summary["sentiment_summary"],
        emotion_summary=summary["emotion_summary"],
        strongest_emotion=summary["strongest_emotion"],
    )
