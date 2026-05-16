from fastapi import APIRouter

from app.modules.articles.router import router as articles_router
from app.modules.audit_logs.router import router as audit_logs_router
from app.modules.auth.router import router as auth_router
from app.modules.clients.router import router as clients_router
from app.modules.health.router import router as health_router
from app.modules.leads.router import router as leads_router
from app.modules.media.router import router as media_router
from app.modules.office_config.router import router as office_config_router
from app.modules.users.router import router as users_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(leads_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(audit_logs_router)
api_router.include_router(office_config_router)
api_router.include_router(media_router)
api_router.include_router(articles_router)
api_router.include_router(clients_router)
