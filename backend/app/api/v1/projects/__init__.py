"""
项目管理模块
"""

from fastapi import APIRouter
from .controller import router as project_router
from .project_platform_controller import router as project_platform_router

router = APIRouter()
router.include_router(project_platform_router)
router.include_router(project_router)

__all__ = ["router"]
