# Supabase Auth adapter: keep provider-specific calls in this module.
from typing import Any
import httpx
from app.config import get_settings


class AuthProviderError(Exception):
    """Safe, provider-neutral authentication error."""


def get_supabase_client():
    settings = get_settings()
    if not settings.supabase_configured:
        raise AuthProviderError(
            "Supabase is not configured. Copy .env.example to .env and add your project URL and key."
        )
    try:
        from supabase import create_client
        return create_client(settings.supabase_url, settings.supabase_key)
    except Exception as exc:
        raise AuthProviderError("Could not initialize Supabase Auth.") from exc


def _user_dict(user: Any) -> dict[str, Any] | None:
    if user is None:
        return None
    if hasattr(user, "model_dump"):
        return user.model_dump(mode="json")
    if hasattr(user, "dict"):
        return user.dict()
    if isinstance(user, dict):
        return user
    return {
        "id": str(getattr(user, "id", "")),
        "email": getattr(user, "email", None),
        "created_at": getattr(user, "created_at", None),
        "last_sign_in_at": getattr(user, "last_sign_in_at", None),
        "user_metadata": getattr(user, "user_metadata", {}) or {},
    }


def signup(email: str, password: str) -> dict[str, Any]:
    try:
        response = get_supabase_client().auth.sign_up({"email": email, "password": password})
        user = _user_dict(getattr(response, "user", None))
        if user is None:
            raise AuthProviderError("Supabase did not return a user. Check email confirmation and project settings.")
        return {"user": user}
    except AuthProviderError:
        raise
    except Exception as exc:
        raise AuthProviderError("Supabase sign-up failed. Check the supplied details and project settings.") from exc


def login(email: str, password: str) -> dict[str, Any]:
    try:
        response = get_supabase_client().auth.sign_in_with_password({"email": email, "password": password})
        session = getattr(response, "session", None)
        user = _user_dict(getattr(response, "user", None))
        access_token = getattr(session, "access_token", None) if session else None
        refresh_token = getattr(session, "refresh_token", None) if session else None
        if not user or not access_token:
            raise AuthProviderError("Supabase did not return a valid login session.")
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    except AuthProviderError:
        raise
    except Exception as exc:
        raise AuthProviderError("Invalid login credentials") from exc


def verify_access_token(access_token: str) -> dict[str, Any]:
    try:
        response = get_supabase_client().auth.get_user(access_token)
        user = _user_dict(getattr(response, "user", None))
        if not user or not user.get("id"):
            raise AuthProviderError("Invalid or expired token")
        return user
    except AuthProviderError:
        raise
    except Exception as exc:
        raise AuthProviderError("Invalid or expired token") from exc


def logout(access_token: str) -> None:
    settings = get_settings()
    if not settings.supabase_configured:
        raise AuthProviderError("Supabase is not configured.")
    try:
        response = httpx.post(
            f"{settings.supabase_url.rstrip('/')}/auth/v1/logout",
            headers={
                "apikey": settings.supabase_key,
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=10.0,
        )
        if response.status_code not in (200, 204):
            raise AuthProviderError("Supabase logout failed; the token may be invalid or expired.")
    except AuthProviderError:
        raise
    except httpx.HTTPError as exc:
        raise AuthProviderError("Supabase logout service could not be reached.") from exc
