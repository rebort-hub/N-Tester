# -*- coding: utf-8 -*-
"""
AI 模块 API
"""
from fastapi import APIRouter
from .llm_config import router as llm_config_router
from .conversation import router as conversation_router
from .knowledge_config import router as knowledge_config_router

router = APIRouter()

# 注册子路由
router.include_router(llm_config_router, prefix="/llm-config", tags=["AI - LLM配置"])
router.include_router(conversation_router, tags=["AI - 对话管理"])
router.include_router(knowledge_config_router, prefix="/knowledge-config", tags=["AI - 知识库全局配置"])

__all__ = ['router']