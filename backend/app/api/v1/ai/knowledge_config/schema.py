# -*- coding: utf-8 -*-
"""
知识库全局配置 Schema
"""

from typing import Optional
from pydantic import BaseModel, Field


class KnowledgeGlobalConfigSchema(BaseModel):
    embedding_provider: str = Field(default="openai")
    embedding_base_url: Optional[str] = Field(default=None)
    embedding_api_key: Optional[str] = Field(default=None)
    embedding_model: str = Field(default="text-embedding-3-small")

    vector_enabled: bool = Field(default=False)
    vector_provider: str = Field(default="qdrant")
    vector_url: Optional[str] = Field(default=None)
    vector_api_key: Optional[str] = Field(default=None)
    vector_collection: str = Field(default="knowledge_default")
    vector_dimension: int = Field(default=1536, ge=1)
    retrieval_top_k: int = Field(default=5, ge=1, le=50)

    chunk_size: int = Field(default=1000, ge=100, le=8000)
    chunk_overlap: int = Field(default=200, ge=0, le=2000)
    distance_metric: str = Field(default="Cosine")
    remark: Optional[str] = Field(default=None)


class EmbeddingConnectionTestSchema(BaseModel):
    embedding_provider: str = Field(default="openai")
    embedding_base_url: Optional[str] = Field(default=None)
    embedding_api_key: str
    embedding_model: str = Field(default="text-embedding-3-small")


class VectorConnectionTestSchema(BaseModel):
    vector_provider: str = Field(default="qdrant")
    vector_url: str
    vector_api_key: Optional[str] = None
