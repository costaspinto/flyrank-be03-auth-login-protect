from typing import Annotated, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.services import supabase_auth

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="BearerAuth")


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Access token required"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return supabase_auth.verify_access_token(credentials.credentials.strip())
    except supabase_auth.AuthProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired token"},
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
