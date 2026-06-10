from fastapi import APIRouter
from forenchain.config import get_settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", status_code=200)
async def health_check():
    """Public health check — used by load balancers and uptime monitors."""
    settings = get_settings()
    return {"status": "ok", "version": settings.app_version}
