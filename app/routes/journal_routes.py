from fastapi import APIRouter, HTTPException, Query, Path, Depends
from app.db.connection import supabase_admin, supabase_anon
from app.schemas.schemas import JournalEntryResponse
from app.utils.encryption import encrypt_text, decrypt_text
import logging
from typing import List
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# Define a Pydantic model for updating a journal entry
class UpdateJournalEntry(BaseModel):
    content: str
    title: str

@router.get("/journal-entry/{user_id}/", response_model=List[JournalEntryResponse])
def get_user_journal_entries(user_id: str) -> List[JournalEntryResponse]:
    """
    Fetch journal entries for a specific user.
    """
    try:
        logger.info(f"Fetching journal entries for user: {user_id}")

        # Use supabase_admin to bypass RLS if necessary
        entries = supabase_admin.table("journal_entry").select("*").eq("user_id", user_id).execute()

        # Log raw response for debugging
        logger.debug(f"Supabase response: {entries}")

        if not entries.data:
            logger.warning(f"No journal entries found for user {user_id}")
            raise HTTPException(status_code=404, detail="No journal entries found for this user")

        # Decrypt entries before returning
        journal_entries = []
        for entry in entries.data:
            try:
                decrypted_content = decrypt_text(entry["content"])
                journal_entry = JournalEntryResponse(
                    entry_id=entry["entry_id"],
                    user_id=entry["user_id"],
                    content=decrypted_content,
                    title=entry["title"],
                )
                journal_entries.append(journal_entry)
            except Exception as decryption_error:
                logger.error(f"Decryption failed for entry ID {entry['entry_id']}: {decryption_error}")
                raise HTTPException(status_code=500, detail="Failed to decrypt journal entry content")

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
        )
    except Exception as e:
        logger.error(f"Error creating journal entry: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.put("/journal-entry/{entry_id}", response_model=JournalEntryResponse)
def update_journal_entry(
    entry_id: int,
    user_id: str = Query(..., description="The ID of the user"),
    content: str = Query(..., description="The journal entry content"),
    title: str = Query(..., description="The journal entry title"),
):
    # Update an existing journal entry using query parameters.
    try:
        logger.info(f"Updating journal entry with ID: {entry_id}")

        # Encrypt the updated content
        encrypted_content = encrypt_text(content)

        # Prepare the data to update
        update_data = {"content": encrypted_content, "title": title, "user_id":user_id}

        # Send the update request to Supabase
        response = (
            supabase_admin.table("journal_entry")
            .update(update_data)
            .eq("entry_id", entry_id)
            .execute()  # type: ignore
        )

        # Check if the update was successful
        if not response.data:
            logger.error(f"Supabase returned an unexpected response: {response}")
            raise HTTPException(status_code=500, detail="Failed to update journal entry")

        updated_entry = response.data[0]
        # Decrypt the content before returning the response
        decrypted_content = decrypt_text(updated_entry["content"])
        return JournalEntryResponse(
            entry_id=updated_entry["entry_id"],
            user_id=updated_entry["user_id"],
            content=decrypted_content,
            title=updated_entry["title"],
        )

    except Exception as e:
        logger.error(f"Error updating journal entry: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.delete("/journal-entry/{entry_id}", status_code=204)
def delete_journal_entry(entry_id: int):
    # Delete a journal entry.
    try:
        logger.info(f"Deleting journal entry with ID: {entry_id}")

        # Send the delete request to Supabase
        response = (
            supabase_admin.table("journal_entry")
            .delete()
            .eq("entry_id", entry_id)
            .execute()  # type: ignore
        )

        # Check if the deletion was successful
        if not response.data:
            logger.error(f"Supabase returned an unexpected response: {response}")
            raise HTTPException(status_code=500, detail="Failed to delete journal entry")

    except Exception as e:
        logger.error(f"Error deleting journal entry: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

