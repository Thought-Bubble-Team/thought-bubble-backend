from fastapi import APIRouter, HTTPException, Query, Path, Depends
from app.db.connection import supabase_admin, supabase_anon
from app.schemas.schemas import JournalEntryResponse
from app.utils.encryption import encrypt_text, decrypt_text
import logging, requests
from typing import List, Union
from pydantic import BaseModel
from datetime import datetime
import concurrent.futures
from fastapi.responses import JSONResponse

# Use the global logger initialized in logging.py
logger = logging.getLogger(__name__)
router = APIRouter()
HUGGING_FACE_API = "https://reimers-thoughtbubble-sentiment.hf.space/analyze-sentiment/"

# Define a Pydantic model for updating a journal entry
class UpdateJournalEntry(BaseModel):
    content: str
    title: str

@router.get("/journal-entry/{user_id}/", response_model=List[JournalEntryResponse])
def get_user_journal_entries(
    user_id: str,
    limit: int = Query(50, description="Number of journal entries to return"),
    offset: int = Query(0, description="Number of journal entries to skip")
) -> List[JournalEntryResponse]:
    # Fetch journal entries for a specific user with pagination.
    # Log the request details including user_id, limit, and offset.
    logger.info(f"Fetching journal entries for user: {user_id} with limit={limit} and offset={offset}")
    
    try:
        # Query the database using Supabase with pagination:
        # - Filter journal entries by user_id.
        # - Order the entries by 'entry_id' in descending order (latest entries first).
        # - Apply pagination using the .range() method.
        entries = (
            supabase_admin.table("journal_entry")
            .select("*")
            .eq("user_id", user_id)
            .order("entry_id", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        # If no entries are found, log a warning and return an empty list.
        if not entries.data:
            logger.warning(f"No journal entries found for user {user_id}. Returning empty list.")
            return []

        # Define a helper function to process each journal entry:
        # - Decrypt the content using decrypt_text().
        # - Return a JournalEntryResponse object with the decrypted content and other details.
        def process_entry(entry: dict) -> JournalEntryResponse:
            try:
                decrypted_content = decrypt_text(entry["content"])
                return JournalEntryResponse(
                    entry_id=entry["entry_id"],
                    user_id=entry["user_id"],
                    content=decrypted_content,
                    title=entry["title"],
                    created_at=entry.get("created_at"),
                    updated_at=entry.get("updated_at"),
                )
            except Exception as decryption_error:
                # Log error if decryption fails for this entry.
                logger.error(f"Decryption failed for entry ID {entry.get('entry_id')}: {decryption_error}")
                # Propagate the error via HTTPException.
                raise HTTPException(status_code=500, detail="Failed to decrypt journal entry content")

        # Use ThreadPoolExecutor to decrypt entries concurrently,
        # which speeds up processing when handling multiple entries.
        with concurrent.futures.ThreadPoolExecutor() as executor:
            journal_entries = list(executor.map(process_entry, entries.data))

        # Return the list of processed journal entries.
        return journal_entries

    except HTTPException as http_exc:
        # Log and re-raise any HTTPExceptions encountered.
        logger.warning(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc

    except Exception as e:
        # Log unexpected errors and return a generic 500 error.
        logger.error(f"Error fetching user journal entries: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    
@router.post("/admin/journal-entry/", response_model=JournalEntryResponse)
def create_journal_entry(
    user_id: str = Query(..., description="The ID of the user"),
    content: str = Query(..., description="The journal entry content"),
    title: str = Query(..., description="The journal entry title"),
) -> JournalEntryResponse:
    # Create a new journal entry using query parameters.
    logger.info(f"Creating a new journal entry for user_id: {user_id}")
    try:
        encrypted_content = encrypt_text(content)
        entry_data = {"user_id": user_id, "content": encrypted_content, "title": title}
        response = supabase_admin.table("journal_entry").insert(entry_data).execute()  # type: ignore

        if not response.data:
            logger.error(f"Supabase returned an unexpected response: {response}")
            raise HTTPException(status_code=500, detail="Failed to create journal entry")

        new_entry = response.data[0]
        return JournalEntryResponse(
            entry_id=new_entry["entry_id"],
            user_id=new_entry["user_id"],
            content=content,  # Return the original content, not the encrypted one
            title=new_entry["title"],
            created_at=new_entry["created_at"],
            updated_at=new_entry["updated_at"],
        )
    except Exception as e:
        logger.error(f"Error creating journal entry: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.put("/journal-entry/{entry_id}", response_model=JournalEntryResponse)
def update_journal_entry(
    entry_id: int,
    user_id: str = Query(...),
    content: str = Query(...),
    title: str = Query(...),
):
    try:
        logger.info(f"Updating journal entry with ID: {entry_id}")

        encrypted_content = encrypt_text(content)
        update_data = {
            "content": encrypted_content,
            "title": title,
            "updated_at": datetime.utcnow().isoformat()
        }

        response = (
            supabase_admin.table("journal_entry")
            .update(update_data)
            .eq("entry_id", entry_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to update journal entry")

        updated_entry = response.data[0]
        decrypted_content = decrypt_text(updated_entry["content"])

        # Delete existing sentiment analysis
        supabase_admin.table("sentiment_analysis").delete().eq("entry_id", entry_id).execute()

        # Re-run analysis by calling API endpoint
        analysis_response = requests.post(
            f"{HUGGING_FACE_API}",
            json={"content": decrypted_content},
            headers={"Content-Type": "application/json"}
        )

        if analysis_response.status_code != 200:
            logger.error(f"Failed to analyze updated entry: {analysis_response.text}")
            raise HTTPException(
                status_code=500,
                detail="Failed to re-analyze sentiment after journal update"
            )

        analysis_result = analysis_response.json()

        # Save new analysis to Supabase
        supabase_admin.table("sentiment_analysis").insert({
            "entry_id": entry_id,
            "sentiment": analysis_result["sentiment"],
            "confidence_score": analysis_result["confidence_score"],
            "emotions": analysis_result["emotions"],
            "strongest_emotion": analysis_result["strongest_emotion"],
            "analysis_feedback": analysis_result["analysis_feedback"],
        }).execute()

        return JournalEntryResponse(
            entry_id=updated_entry["entry_id"],
            user_id=updated_entry["user_id"],
            content=decrypted_content,
            title=updated_entry["title"],
            created_at=updated_entry["created_at"],
            updated_at=updated_entry["updated_at"],
        )

    except Exception as e:
        logger.error(f"Error updating journal entry: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.delete("/journal-entry/{entry_id}", status_code=200)
def delete_journal_entry(entry_id: int):
    """Deletes a journal entry by ID, leveraging ON DELETE CASCADE."""
    try:
        logger.info(f"Deleting journal entry with ID: {entry_id}")

        # Send the delete request to Supabase
        response = (
            supabase_admin.table("journal_entry")
            .delete()
            .eq("entry_id", entry_id)
            .execute()
        )

        # Check if the deletion was successful
        if not response.data:
            logger.warning(f"Journal entry {entry_id} not found for deletion.")
            return JSONResponse(
                status_code=404,
                content={"message": "Journal entry not found or already deleted", "entry_id": entry_id},
            )

        logger.info(f"Successfully deleted journal entry with ID: {entry_id}")

        return JSONResponse(
            status_code=200,
            content={"message": "Journal entry deleted successfully", "entry_id": entry_id},
        )

    except Exception as e:
        logger.error(f"Error deleting journal entry {entry_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")