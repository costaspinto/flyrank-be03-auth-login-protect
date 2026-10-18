from fastapi import FastAPI
from app.routers import auth, public, protected

app = FastAPI(
    title="FlyRank BE-03 Auth API",
    description="Supabase-backed signup, login, logout, JWT verification, and protected routes.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Authentication", "description": "Supabase account and session operations."},
        {"name": "Public", "description": "Endpoints that do not require a token."},
        {"name": "Protected", "description": "Endpoints requiring a valid Supabase access token."},
    ],
)

app.include_router(auth.router)
app.include_router(public.router)
app.include_router(protected.router)


@app.get("/", tags=["System"], summary="Service health")
def root():
    return {"service": "FlyRank BE-03 Auth API", "status": "ok", "docs": "/docs"}


@app.get("/health", tags=["System"], summary="Health check")
def health():
    return {"status": "healthy"}
