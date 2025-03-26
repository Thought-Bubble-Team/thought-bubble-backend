from fastapi import APIRouter, HTTPException, Body
import requests
from decouple import config
from app.schemas.schemas import PasswordResetRequest

router = APIRouter()
SUPABASE_URL = config("SUPABASE_URL")
SUPABASE_SERVICE_KEY = config("SUPABASE_SERVICE_KEY")

@router.post("/reset-password/")
def reset_password(payload: PasswordResetRequest):
    """
    Resets a user's password using their Supabase user ID.
    """
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    try:
        response = requests.put(
            f"{SUPABASE_URL}/auth/v1/admin/users/{payload.user_id}",
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",  # Admin key used here
                "Content-Type": "application/json"
            },
            json={"password": payload.new_password}
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("msg", "Failed to reset password")
            )

        return {"message": "Password has been successfully updated."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))