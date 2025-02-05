from fastapi import FastAPI, HTTPException
from decouple import config
from supabase import create_client, Client
from app.middlewares.exception_handler import ExceptionHandlerMiddleware
from app.middlewares.logging import setup_logging
from app.schemas.schemas import EntryRequest, SentimentResponse
from app.services.sentiment_analysis import analyze_sentiment, analyze_emotion, summarize_analysis, adjust_sentiment
from app.services.preprocessing import preprocess

url = config('SUPABASE_URL')
key = config('SUPABASE_KEY')
admin_key = config('SUPABASE_SERVICE_KEY')

# Setup logging
setup_logging()

app = FastAPI()
# Add exception handler middleware
app.add_middleware(ExceptionHandlerMiddleware)

# Initialize Supabase clients
supabase_anon: Client = create_client(url, key)
supabase_admin: Client = create_client(url, admin_key)

@app.post("/admin/analyze-sentiment/", response_model=SentimentResponse)
def analyze_sentiment_endpoint(entry: EntryRequest):
    """
    API endpoint to analyze sentiment and emotion of a given journal entry
    and save the result to the database.
    """
    entry_id = entry.entry_id
    if not entry_id:
        raise HTTPException(status_code=400, detail="entry_id is missing")

    # Fetch the journal entry from the database
    journal_entry = supabase_admin.table("journal_entries").select("*").eq("entry_id", entry_id).execute()
    if not journal_entry.data or len(journal_entry.data) == 0:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    # Get the content from the journal entry
    content = journal_entry.data[0]["content"]

    # Step 1: Preprocess text
    preprocessed_text = preprocess(content)

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
        "emotions": emotion_result
    }).execute()

    if hasattr(response, 'error') and response.error:
        raise HTTPException(status_code=500, detail="Failed to save sentiment analysis result")

    # Step 6: Return response
    return {
        "entry_id": entry_id,
        "content": content,
        "preprocessed_content": preprocessed_text,
        "sentiment": sentiment_result["sentiment"],
        "confidence_score": sentiment_result["confidence_score"],
        "sentiment_summary": summary["sentiment_summary"],
        "emotion_summary": summary["emotion_summary"]
    }