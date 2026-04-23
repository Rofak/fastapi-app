from fastapi import APIRouter
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Heath"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "ok"}