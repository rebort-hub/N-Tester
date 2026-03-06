# -*- coding: utf-8 -*-
"""
AI 模块 API
"""
from fastapi import APIRouter
from .llm_config import router as llm_config_router
from .conversation import router as conversation_router

router = APIRouter()

# 注册子路由
router.include_router(llm_config_router, prefix="/llm-config", tags=["AI - LLM配置"])
router.include_router(conversation_router, tags=["AI - 对话管理"])

__all__ = ['router']