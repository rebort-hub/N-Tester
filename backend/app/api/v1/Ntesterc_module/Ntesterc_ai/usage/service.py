#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

"""
LLM 用量日志写入服务
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.core.database import async_session
from app.api.v1.Ntesterc_module.Ntesterc_ai.usage.model import LLMUsageLogModel

_table_ensured = False

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS llm_usage_logs (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    creation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT NULL,
    updation_date DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by BIGINT NULL,
    enabled_flag TINYINT(1) NOT NULL DEFAULT 1,
    trace_id VARCHAR(255) NULL,
    user_id BIGINT NULL,
    llm_config_id BIGINT NULL,
    provider VARCHAR(50) NULL,
    model_name VARCHAR(100) NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'chat',
    conversation_id BIGINT NULL,
    message_id BIGINT NULL,
    prompt_tokens INT NOT NULL DEFAULT 0,
    completion_tokens INT NOT NULL DEFAULT 0,
    total_tokens INT NOT NULL DEFAULT 0,
    cached_tokens INT NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'success',
    error_message TEXT NULL,
    latency_ms INT NULL,
    INDEX ix_llm_usage_logs_user_id (user_id),
    INDEX ix_llm_usage_logs_llm_config_id (llm_config_id),
    INDEX ix_llm_usage_logs_model_name (model_name),
    INDEX ix_llm_usage_logs_source (source),
    INDEX ix_llm_usage_logs_conversation_id (conversation_id),
    INDEX ix_llm_usage_logs_creation_date (creation_date)
) COMMENT='LLM 用量日志表'
"""


class UsageLogService:
    """写入 llm_usage_logs"""

    @classmethod
    async def ensure_table(cls, db: Optional[AsyncSession] = None) -> None:
        global _table_ensured
        if _table_ensured:
            return
        try:
            if db is not None:
                await db.execute(text(_CREATE_TABLE_SQL))
                await db.commit()
            else:
                async with async_session() as session:
                    await session.execute(text(_CREATE_TABLE_SQL))
                    await session.commit()
            _table_ensured = True
        except Exception as e:
            logger.warning(f"[UsageLog] ensure_table 失败（忽略）: {e}")

    @classmethod
    async def record(
        cls,
        *,
        db: Optional[AsyncSession] = None,
        user_id: Optional[int] = None,
        llm_config_id: Optional[int] = None,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        source: str = "chat",
        conversation_id: Optional[int] = None,
        message_id: Optional[int] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        cached_tokens: int = 0,
        status: str = "success",
        error_message: Optional[str] = None,
        latency_ms: Optional[int] = None,
        usage: Optional[Dict[str, Any]] = None,
    ) -> None:
        try:
            await cls.ensure_table(db=None)
            if usage:
                prompt_tokens = int(usage.get("prompt_tokens") or prompt_tokens or 0)
                completion_tokens = int(usage.get("completion_tokens") or completion_tokens or 0)
                total_tokens = int(usage.get("total_tokens") or total_tokens or 0)
                cached_tokens = int(usage.get("cached_tokens") or cached_tokens or 0)
                if total_tokens <= 0:
                    total_tokens = prompt_tokens + completion_tokens

            row = LLMUsageLogModel(
                user_id=user_id,
                llm_config_id=llm_config_id,
                provider=(provider or "")[:50] or None,
                model_name=(model_name or "")[:100] or None,
                source=(source or "chat")[:50],
                conversation_id=conversation_id,
                message_id=message_id,
                prompt_tokens=max(prompt_tokens, 0),
                completion_tokens=max(completion_tokens, 0),
                total_tokens=max(total_tokens, 0),
                cached_tokens=max(cached_tokens, 0),
                status=(status or "success")[:20],
                error_message=(error_message[:2000] if error_message else None),
                latency_ms=latency_ms,
                created_by=user_id,
                updated_by=user_id,
            )

            if db is not None:
                db.add(row)
                await db.flush()
                return

            async with async_session() as session:
                session.add(row)
                await session.commit()
        except Exception as e:
            logger.warning(f"[UsageLog] 写入用量日志失败（忽略）: {e}")
