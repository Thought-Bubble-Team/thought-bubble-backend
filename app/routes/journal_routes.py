from fastapi import APIRouter, HTTPException, Query
from app.db.connection import supabase_admin, supabase_anon
from app.schemas.schemas import JournalEntryResponse
from app.utils.encryption import encrypt_text, decrypt_text
import logging
from typing import List

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/admin/journal-entry/", response_model=List[JournalEntryResponse])
def get_all_journal_entries() -> List[JournalEntryResponse]:
    """Admin: Fetch all journal entries."""
    logger.info("Fetching all journal entries")
    try:
        entries = supabase_admin.table("journal_entry").select("*").execute()  # type: ignore
        if not entries.data:
            raise HTTPException(status_code=404, detail="No journal entries found")
        return [JournalEntryResponse(**entry) for entry in entries.data]
    except Exception as e:
        logger.error(f"Error fetching all journal entries: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/journal-entry/{user_id}/", response_model=List[JournalEntryResponse])
def get_user_journal_entries(user_id: str) -> List[JournalEntryResponse]:
    """Fetch journal entries for a specific user."""
    logger.info(f"Fetching journal entries for user: {user_id}")
    try:
        entries = supabase_anon.table("journal_entry").select("*").eq("user_id", user_id).execute()  # type: ignore
        if not entries.data:
            raise HTTPException(status_code=404, detail="No journal entries found for this user")

        journal_entries = []
        for entry in entries.data:
            decrypted_content = decrypt_text(entry["content"])
            journal_entry = JournalEntryResponse(
                entry_id=entry["entry_id"],
                user_id=entry["user_id"],
                content=decrypted_content,
                title=entry["title"],
            )
            journal_entries.append(journal_entry)

        return journal_entries
    except Exception as e:
        logger.error(f"Error fetching user journal entries: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/admin/journal-entry/", response_model=JournalEntryResponse)
def create_journal_entry(
    user_id: str = Query(..., description="The ID of the user"),
    content: str = Query(..., description="The journal entry content"),
    title: str = Query(..., description="The journal entry title"),
) -> JournalEntryResponse:
    """Create a new journal entry using query parameters."""
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
        )
    except Exception as e:
        logger.error(f"Error creating journal entry: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
