from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from app.dependencies import CurrentUser, bearer_scheme
from app.services import supabase_auth

router = APIRouter(prefix="/auth", tags=["Authentication"])


class Credentials(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=1, max_length=128)


def validate_credentials(payload: Credentials | None) -> tuple[str, str]:
    if payload is None or not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail={"error": "Email and password are required"})
    return str(payload.email), payload.password


@router.post("/signup", status_code=status.HTTP_201_CREATED, summary="Create an account")
def signup(payload: Credentials | None = None):
    email, password = validate_credentials(payload)
    try:
        result = supabase_auth.signup(email, password)
        return {"user": result["user"]}
    except supabase_auth.AuthProviderError as exc:
        if "not configured" in str(exc).lower():
            raise HTTPException(status_code=503, detail={"error": str(exc)}) from exc
        raise HTTPException(status_code=400, detail={"error": "Sign-up failed. Check credentials and Supabase settings."}) from exc


@router.post("/login", status_code=status.HTTP_200_OK, summary="Log in and receive JWT tokens")
def login(payload: Credentials | None = None):
    email, password = validate_credentials(payload)
    try:
        return supabase_auth.login(email, password)
    except supabase_auth.AuthProviderError as exc:
        if "not configured" in str(exc).lower():
            raise HTTPException(status_code=503, detail={"error": str(exc)}) from exc
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid login credentials"},
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Log out and revoke the session")
def logout(
    current_user: CurrentUser,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    # CurrentUser verifies this token before the route body executes.
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail={"error": "Access token required"})
    try:
        supabase_auth.logout(credentials.credentials)
    except supabase_auth.AuthProviderError as exc:
        raise HTTPException(status_code=401, detail={"error": "Invalid or expired token"}) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
