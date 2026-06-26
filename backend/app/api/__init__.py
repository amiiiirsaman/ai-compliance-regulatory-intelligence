"""API routes module."""
from fastapi import APIRouter

from .auth import router as auth_router
from .documents import router as documents_router
from .reviews import router as reviews_router
from .reports import router as reports_router
from .websocket import router as websocket_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(documents_router, prefix="/documents", tags=["Documents"])
router.include_router(reviews_router, prefix="/reviews", tags=["Reviews"])
router.include_router(reports_router, prefix="/reports", tags=["Reports"])
router.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])
