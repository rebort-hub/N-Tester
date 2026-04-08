# -*- coding: utf-8 -*-
"""
知识库全局向量配置模型
"""

from sqlalchemy import Boolean, Column, Integer, String, Text, BigInteger, ForeignKey, Index
from app.models.base import Base


class KnowledgeVectorGlobalConfigModel(Base):
    """知识库全局配置（按用户隔离）"""

    __tablename__ = "knowledge_vector_global_config"
    __table_args__ = (
        Index("uq_kvgc_user", "user_id", unique=True),
        {"comment": "知识库全局向量配置", "mysql_charset": "utf8mb4"},
    )

    user_id = Column(
        BigInteger,
        ForeignKey("sys_user.id", use_alter=True, name="fk_kvgc_user"),
        nullable=False,
        comment="用户ID",
    )

    # Embedding model config
    embedding_provider = Column(String(50), default="openai", comment="嵌入提供商")
    embedding_base_url = Column(String(500), nullable=True, comment="嵌入服务Base URL")
    embedding_api_key = Column(String(2000), nullable=True, comment="嵌入API Key")
    embedding_model = Column(String(200), default="text-embedding-3-small", comment="嵌入模型")

    # Vector DB config
    vector_enabled = Column(Boolean, default=False, comment="是否启用向量检索")
    vector_provider = Column(String(50), default="qdrant", comment="向量库类型")
    vector_url = Column(String(500), nullable=True, comment="向量库地址")
    vector_api_key = Column(String(2000), nullable=True, comment="向量库API Key")
    vector_collection = Column(String(200), default="knowledge_default", comment="默认集合")
    vector_dimension = Column(Integer, default=1536, comment="向量维度")
    retrieval_top_k = Column(Integer, default=5, comment="检索TopK")

    # Chunk config
    chunk_size = Column(Integer, default=1000, comment="默认切块大小")
    chunk_overlap = Column(Integer, default=200, comment="默认切块重叠")
    distance_metric = Column(String(20), default="Cosine", comment="向量距离度量")

    remark = Column(Text, nullable=True, comment="备注")
