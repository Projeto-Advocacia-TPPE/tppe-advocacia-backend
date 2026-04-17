from fastapi import APIRouter

from app.views.health_view import router as health_router
from app.views.lead_view import router as lead_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(lead_router)

