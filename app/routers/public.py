from fastapi import APIRouter

router = APIRouter(tags=["Public"])


@router.get("/public/info", summary="Public information")
def public_info():
    return {"message": "Welcome stranger! This info is public."}
