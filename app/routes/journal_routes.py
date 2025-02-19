from fastapi import APIRouter, HTTPException, Query
from app.db.connection import supabase_admin, supabase_anon
from app.schemas.schemas import JournalEntryResponse
from app.utils.encryption import encrypt_text, decrypt_text
import logging


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/admin/journal-entry/", response_model=list[JournalEntryResponse])
def get_all_journal_entries():
    """
    Admin: Fetch all journal entries.
    """
    try:
        logger.info("Fetching all journal entries")
        entries = supabase_admin.table("journal_entry").select("*").execute()
        if not entries.data:
            raise HTTPException(status_code=404, detail="No journal entries found")
        return entries.data
    except Exception as e:
        logger.error(f"Error fetching all journal entries: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/journal-entry/{user_id}/", response_model=list[JournalEntryResponse])
def get_user_journal_entries(user_id: str):
    """
    Fetch journal entries for a specific user.
    """
    try:
        logger.info(f"Fetching journal entries for user: {user_id}")
        entries = supabase_anon.table("journal_entry").select("*").eq("user_id", user_id).execute()
        if not entries.data:
            raise HTTPException(status_code=404, detail="No journal entries found for this user")
        # Decrypt entries before returning
        for entry in entries.data:
            entry["content"] = decrypt_text(entry["content"])  # Decrypt content
        return entries.data
    except Exception as e:
        logger.error(f"Error fetching user journal entries: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/admin/journal-entry/", response_model=JournalEntryResponse)
def create_journal_entry(
    user_id: str = Query(..., description="The ID of the user"),
    content: str = Query(..., description="The journal entry content"),
    title: str = Query(..., description="The journal entry title")
):
    """
    Create a new journal entry using query parameters.
    """
    try:
        logger.info(f"Creating a new journal entry for user_id: {user_id}")
        # encrypt the journal entry content before storing it in the database
        encrypted_content = encrypt_text(content)
        
        # Prepare the data to insert
        entry_data = {"user_id": user_id, "content": encrypted_content, "title": title}

        # Send the insert request to Supabase
        response = supabase_admin.table("journal_entry").insert(entry_data).execute()

        # Validate the response by checking if `data` is present and not empty
        if not response.data or len(response.data) == 0:
            logger.error(f"Supabase returned an unexpected response: {response}")
            raise HTTPException(status_code=500, detail="Failed to save journal entry")

        # Log and return the created entry
        logger.info(f"Journal entry created successfully: {response.data[0]}")
        return response.data[0]
    except AttributeError as e:
        # Handle attribute-related errors specifically
        logger.error(f"Supabase client issue: {e}")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while processing the request.",
        )
    except Exception as e:
        # Log any other unhandled exceptions
        logger.error(f"Error creating journal entry: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.delete("/journal-entry/{entry_id}/")
def delete_journal_entry(entry_id: int):
    """
    Delete a journal entry by ID.
    """
    try:
        logger.info(f"Deleting journal entry with ID: {entry_id}")
        response = supabase_admin.table("journal_entry").delete().eq("entry_id", entry_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Journal entry not found")
        return {"message": "Journal entry deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting journal entry: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")