# This file is a placeholder for future web app authentication.
# For a web app, you would implement JWT-based authentication here.
# The Telegram bot handles auth via telegram_id.

from fastapi import APIRouter, Depends, HTTPException, status
from src.app.startup import get_user_use_cases
from src.use_cases.user_use_cases import UserUseCases

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
async def web_login():
    """Endpoint for future web app login (e.g., with OTP)."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Web login not yet implemented.")

@router.get("/me")
async def read_users_me():
    """Endpoint to get current user info for a logged-in web user."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Web user profile not yet implemented.")