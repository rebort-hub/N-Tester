# -*- coding: utf-8 -*-
"""
知识库全局向量配置服务
"""

from typing import Any, Dict
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.response import success_response, error_response
from .model import KnowledgeVectorGlobalConfigModel
from .schema import KnowledgeGlobalConfigSchema


def _default_config() -> Dict[str, Any]:
    return {
        "embedding_provider": "openai",
        "embedding_base_url": "",
        "embedding_api_key": "",
        "embedding_model": "text-embedding-3-small",
        "vector_enabled": False,
        "vector_provider": "qdrant",
        "vector_url": "",
        "vector_api_key": "",
        "vector_collection": "knowledge_default",
        "vector_dimension": 1536,
        "retrieval_top_k": 5,
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "distance_metric": "Cosine",
        "remark": "",
    }


class KnowledgeConfigService:
    @staticmethod
    async def get_config(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        row = (
            await db.execute(
                select(KnowledgeVectorGlobalConfigModel).where(
                    KnowledgeVectorGlobalConfigModel.user_id == user_id,
                    KnowledgeVectorGlobalConfigModel.enabled_flag == 1,
                )
            )
        ).scalar_one_or_none()
        if not row:
            return _default_config()

        return {
            "id": row.id,
            "embedding_provider": row.embedding_provider,
            "embedding_base_url": row.embedding_base_url or "",
            "embedding_api_key": row.embedding_api_key or "",
            "embedding_model": row.embedding_model,
            "vector_enabled": bool(row.vector_enabled),
            "vector_provider": row.vector_provider,
            "vector_url": row.vector_url or "",
            "vector_api_key": row.vector_api_key or "",
            "vector_collection": row.vector_collection,
            "vector_dimension": row.vector_dimension,
            "retrieval_top_k": row.retrieval_top_k,
            "chunk_size": row.chunk_size,
            "chunk_overlap": row.chunk_overlap,
            "distance_metric": row.distance_metric,
            "remark": row.remark or "",
        }

    @staticmethod
    async def save_config(db: AsyncSession, user_id: int, data: KnowledgeGlobalConfigSchema):
        row = (
            await db.execute(
                select(KnowledgeVectorGlobalConfigModel).where(
                    KnowledgeVectorGlobalConfigModel.user_id == user_id,
                    KnowledgeVectorGlobalConfigModel.enabled_flag == 1,
                )
            )
        ).scalar_one_or_none()
        payload = data.model_dump()

        if row is None:
            row = KnowledgeVectorGlobalConfigModel(
                user_id=user_id,
                created_by=user_id,
                updated_by=user_id,
                **payload,
            )
            db.add(row)
        else:
            for k, v in payload.items():
                setattr(row, k, v)
            row.updated_by = user_id
        await db.commit()
        return success_response(message="保存成功")

    @staticmethod
    async def test_embedding_connection(payload: Dict[str, Any]):
        api_key = payload.get("embedding_api_key")
        if not api_key:
            prov = (payload.get("embedding_provider") or "openai").strip()
            mdl = (payload.get("embedding_model") or "text-embedding-3-small").strip()
            return error_response(message=f"{prov} / {mdl}：embedding_api_key 不能为空")

        base_url = (payload.get("embedding_base_url") or "https://api.openai.com/v1").rstrip("/")
        model = payload.get("embedding_model") or "text-embedding-3-small"
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    f"{base_url}/embeddings",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"model": model, "input": "ping"},
                )
            if resp.status_code < 400:
                prov = (payload.get("embedding_provider") or "openai").strip()
                mdl = (payload.get("embedding_model") or "text-embedding-3-small").strip()
                return success_response(
                    message=f"{prov} / {mdl} 嵌入连接成功",
                    data={"status_code": resp.status_code},
                )
            prov_e = (payload.get("embedding_provider") or "openai").strip()
            return error_response(
                message=f"{prov_e} / {model} 嵌入连接失败: HTTP {resp.status_code}",
                data={"body": resp.text[:300]},
            )
        except Exception as e:
            prov = (payload.get("embedding_provider") or "openai").strip()
            mdl = (payload.get("embedding_model") or "text-embedding-3-small").strip()
            return error_response(message=f"{prov} / {mdl} 嵌入连接失败: {e}")

    @staticmethod
    async def test_vector_connection(payload: Dict[str, Any]):
        provider = (payload.get("vector_provider") or "qdrant").lower()
        url = (payload.get("vector_url") or "").rstrip("/")
        if not url:
            return error_response(message=f"{provider}：vector_url 不能为空")
        headers = {}
        if payload.get("vector_api_key"):
            headers["api-key"] = payload.get("vector_api_key")
            headers["Authorization"] = f"Bearer {payload.get('vector_api_key')}"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                if provider == "qdrant":
                    resp = await client.get(f"{url}/collections", headers=headers)
                elif provider == "chroma":
                    resp = await client.get(f"{url}/api/v1/collections", headers=headers)
                else:
                    resp = await client.get(url, headers=headers)
            if resp.status_code < 400:
                return success_response(
                    message=f"{provider} 向量库连接成功",
                    data={"status_code": resp.status_code},
                )
            return error_response(
                message=f"{provider} 向量库连接失败: HTTP {resp.status_code}",
                data={"body": resp.text[:300]},
            )
        except Exception as e:
            prov = (payload.get("vector_provider") or "qdrant").strip()
            return error_response(message=f"{prov} 向量库连接失败: {e}")
