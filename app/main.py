from fastapi import FastAPI, HTTPException
from decouple import config
from supabase import create_client, Client
from app.middlewares.exception_handler import ExceptionHandlerMiddleware
from app.middlewares.logging import setup_logging
from app.schemas.schemas import EntryRequest, SentimentResponse, JournalEntry
from app.services.sentiment_analysis import analyze_sentiment

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

@app.get("/admin/journal-entries")
def get_admin_journal_entries():
    journal_entries = supabase_admin.table('journal_entries').select("*").execute()
    return journal_entries

@app.get("/journal-entries")
def get_journal_entries():
    journal_entries = supabase_anon.table('journal_entries').select("*").execute()
    return journal_entries

@app.post("/admin/analyze-sentiment/", response_model=SentimentResponse)
def analyze_sentiment_endpoint(entry: EntryRequest):
    """
    API endpoint to analyze sentiment of a given journal entry
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

    # Perform sentiment analysis
    result = analyze_sentiment(content)

    # Save the result into the database
    response = supabase_admin.table("sentiment_analysis").insert({
        "entry_id": entry_id,
        "sentiment": result["sentiment"],
        "confidence_score": result["confidence_score"]
    }).execute()

    # Check for errors in response
    if hasattr(response, 'error') and response.error:
        logger.error(f"Failed to save sentiment analysis result: {response.error.message}")
        raise HTTPException(status_code=500, detail="Failed to save sentiment analysis result")
    
    # Return the successful result in JSON format
    return SentimentResponse(
        entry_id=entry_id,
        content=content,
        sentiment=result["sentiment"],
        confidence_score=result["confidence_score"]
    )

# New endpoints
@app.post("/journal-entries")
def create_journal_entry(entry: JournalEntry):
    """
    Create a new journal entry.
    """
    response = supabase_anon.table("journal_entries").insert({"content": entry.content}).execute()
    if hasattr(response, 'error') and response.error:
        raise HTTPException(status_code=500, detail="Failed to create journal entry")
    return {"message": "Journal entry created successfully", "entry_id": response.data[0]["entry_id"]}

@app.get("/journal-entries/{entry_id}")
def get_journal_entry(entry_id: int):
    """
    Get a specific journal entry by ID.
    """
    journal_entry = supabase_anon.table("journal_entries").select("*").eq("entry_id", entry_id).execute()
    if not journal_entry.data or len(journal_entry.data) == 0:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return journal_entry.data[0]

@app.put("/journal-entries/{entry_id}")
def update_journal_entry(entry_id: int, entry: JournalEntry):
    """
    Update a specific journal entry by ID.
    """
    response = supabase_anon.table("journal_entries").update({"content": entry.content}).eq("entry_id", entry_id).execute()
    if hasattr(response, 'error') and response.error:
        raise HTTPException(status_code=500, detail="Failed to update journal entry")
    return {"message": "Journal entry updated successfully"}

@app.delete("/journal-entries/{entry_id}")
def delete_journal_entry(entry_id: int):
    """
    Delete a specific journal entry by ID.
    """
    response = supabase_anon.table("journal_entries").delete().eq("entry_id", entry_id).execute()
    if hasattr(response, 'error') and response.error:
        raise HTTPException(status_code=500, detail="Failed to delete journal entry")
    return {"message": "Journal entry deleted successfully"}

@app.get("/journal-entries/{entry_id}/sentiment")
def get_sentiment_analysis(entry_id: int):
    """
    Get sentiment analysis for a specific journal entry by ID.
    """
    sentiment_analysis = supabase_anon.table("sentiment_analysis").select("*").eq("entry_id", entry_id).execute()
    if not sentiment_analysis.data or len(sentiment_analysis.data) == 0:
        raise HTTPException(status_code=404, detail="Sentiment analysis not found")
    return sentiment_analysis.data[0]

@app.get("/sentiment-analysis")
def get_all_sentiment_analysis():
    """
    Get all sentiment analysis results.
    """
    sentiment_analysis = supabase_anon.table("sentiment_analysis").select("*").execute()
    return sentiment_analysis.data

@app.get("/sentiment-analysis/summary")
def get_sentiment_summary():
    """
    Get a summary of sentiment analysis results.
    """
    sentiment_analysis = supabase_anon.table("sentiment_analysis").select("*").execute()
    summary = {
        "positive": 0,
        "negative": 0,
        "neutral": 0
    }
    for entry in sentiment_analysis.data:
        sentiment = entry["sentiment"].lower()
        if sentiment in summary:
            summary[sentiment] += 1
    return summary