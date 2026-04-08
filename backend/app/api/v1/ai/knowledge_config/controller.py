# -*- coding: utf-8 -*-
"""
知识库全局向量配置 API
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user_id
from app.db.sqlalchemy import get_db
from app.common.response import success_response
from .schema import (
    EmbeddingConnectionTestSchema,
    KnowledgeGlobalConfigSchema,
    VectorConnectionTestSchema,
)
from .service import KnowledgeConfigService

router = APIRouter()


@router.get("/global", summary="获取知识库全局配置")
async def get_global_config(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    data = await KnowledgeConfigService.get_config(db, current_user_id)
    return success_response(data=data, message="查询成功")


@router.put("/global", summary="保存知识库全局配置")
async def save_global_config(
    data: KnowledgeGlobalConfigSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await KnowledgeConfigService.save_config(db, current_user_id, data)


@router.post("/test-embedding", summary="测试嵌入模型连接")
async def test_embedding_connection(data: EmbeddingConnectionTestSchema):
    return await KnowledgeConfigService.test_embedding_connection(data.model_dump())


@router.post("/test-vector-db", summary="测试向量数据库连接")
async def test_vector_db_connection(data: VectorConnectionTestSchema):
    return await KnowledgeConfigService.test_vector_connection(data.model_dump())
