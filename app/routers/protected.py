from typing import Any
from fastapi import APIRouter
from app.dependencies import CurrentUser

router = APIRouter(prefix="/protected", tags=["Protected"])


@router.get("/profile", summary="Read the authenticated user's profile")
def profile(current_user: CurrentUser) -> dict[str, Any]:
    return {
        "id": current_user.get("id"),
        "email": current_user.get("email"),
        "created_at": current_user.get("created_at"),
        "last_sign_in_at": current_user.get("last_sign_in_at"),
    }


@router.get("/dashboard", summary="Example second protected route")
def dashboard(current_user: CurrentUser) -> dict[str, Any]:
    return {"message": "You are authenticated.", "user_id": current_user.get("id")}
