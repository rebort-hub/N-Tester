#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort
"""
LLM 服务封装 - 使用 LangChain，支持所有 OpenAI 兼容的 API
"""
from __future__ import annotations

import logging
import time
from typing import List, Dict, Any, Optional, Union, AsyncGenerator, Tuple
from enum import Enum

from app.api.v1.Ntesterc_module.Ntesterc_ai.llm_config.model import LLMConfigModel
from sqlalchemy import select
from app.core.database import async_session


try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    # Nuitka/缺失依赖时导入失败：必须给符号占位，避免类注解 NameError 导致整个后端起不来
    LANGCHAIN_AVAILABLE = False
    ChatOpenAI = None  # type: ignore[misc, assignment]
    HumanMessage = AIMessage = SystemMessage = BaseMessage = Any  # type: ignore[misc, assignment]

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM 提供商枚举"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    CUSTOM = "custom"


class LLMMessage:
    """LLM 消息类"""
    def __init__(self, role: str, content: Any, name: Optional[str] = None):
        self.role = role  # system, user, assistant
        self.content = content
        self.name = name
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "role": self.role,
            "content": self.content
        }
        if self.name:
            result["name"] = self.name
        return result


def extract_usage_from_message(msg: Any) -> Dict[str, int]:
    """
    从 LangChain AIMessage / chunk 中提取 usage。
    兼容 usage_metadata、response_metadata.token_usage、OpenAI cached_tokens、Anthropic cache_read。
    """
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    cached_tokens = 0

    um = getattr(msg, "usage_metadata", None) or {}
    if isinstance(um, dict) and um:
        prompt_tokens = int(um.get("input_tokens") or um.get("prompt_tokens") or 0)
        completion_tokens = int(um.get("output_tokens") or um.get("completion_tokens") or 0)
        total_tokens = int(um.get("total_tokens") or 0)
        details = um.get("input_token_details") or um.get("input_tokens_details") or {}
        if isinstance(details, dict):
            cached_tokens = int(
                details.get("cache_read")
                or details.get("cached_tokens")
                or details.get("cache_read_input_tokens")
                or 0
            )
        output_details = um.get("output_token_details") or {}
        if isinstance(output_details, dict) and not cached_tokens:
            # 少数提供商把缓存信息放在别处，忽略
            pass

    meta = getattr(msg, "response_metadata", None) or {}
    if isinstance(meta, dict):
        tu = meta.get("token_usage") or meta.get("usage") or {}
        if isinstance(tu, dict) and tu:
            if not prompt_tokens:
                prompt_tokens = int(tu.get("prompt_tokens") or tu.get("input_tokens") or 0)
            if not completion_tokens:
                completion_tokens = int(tu.get("completion_tokens") or tu.get("output_tokens") or 0)
            if not total_tokens:
                total_tokens = int(tu.get("total_tokens") or 0)
            if not cached_tokens:
                ptd = tu.get("prompt_tokens_details") or tu.get("input_tokens_details") or {}
                if isinstance(ptd, dict):
                    cached_tokens = int(ptd.get("cached_tokens") or ptd.get("cache_read") or 0)
                cached_tokens = int(
                    tu.get("cache_read_input_tokens")
                    or tu.get("cached_tokens")
                    or cached_tokens
                    or 0
                )

    if total_tokens <= 0:
        total_tokens = prompt_tokens + completion_tokens

    return {
        "prompt_tokens": max(prompt_tokens, 0),
        "completion_tokens": max(completion_tokens, 0),
        "total_tokens": max(total_tokens, 0),
        "cached_tokens": max(cached_tokens, 0),
    }


class LLMResponse:
    """LLM 响应类"""
    def __init__(self, content: str, usage: Optional[Dict] = None, model: Optional[str] = None):
        self.content = content
        self.usage = usage or {}
        self.model = model
    
    @property
    def input_tokens(self) -> int:
        return int(self.usage.get("prompt_tokens", 0) or 0)
    
    @property
    def output_tokens(self) -> int:
        return int(self.usage.get("completion_tokens", 0) or 0)
    
    @property
    def total_tokens(self) -> int:
        total = int(self.usage.get("total_tokens", 0) or 0)
        if total <= 0:
            return self.input_tokens + self.output_tokens
        return total

    @property
    def cached_tokens(self) -> int:
        return int(self.usage.get("cached_tokens", 0) or 0)


class LLMService:
    """LLM 服务类"""
    
    def __init__(
        self,
        provider: LLMProvider,
        config: Dict[str, Any],
        llm_config_id: Optional[int] = None,
    ):
        self.provider = provider
        self.config = config
        self.llm_config_id = llm_config_id
        self.client = None
        self.last_usage: Dict[str, int] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cached_tokens": 0,
        }
        self.last_latency_ms: Optional[int] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化客户端"""
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain not installed. Install: pip install langchain langchain-openai")
        
        try:
            # 清理 API 密钥
            api_key = self.config.get("api_key", "") or ""
            
            # 对于本地模型（如 Ollama），API Key 可以为空
            if api_key and api_key.startswith("Bearer "):
                api_key = api_key[7:].strip()
                logger.info("Removed 'Bearer ' prefix from API key")
            
            # 如果没有 API Key，使用占位符（某些本地模型需要）
            if not api_key:
                api_key = "not-needed"
                logger.info("No API key provided, using placeholder for local model")
            
            # 清理 base_url
            base_url = self.config.get("base_url", "")
            if base_url:
                # 移除完整端点路径（用户可能直接粘贴了完整的 completions URL）
                endpoints_to_remove = ['/chat/completions', '/completions']
                for endpoint in endpoints_to_remove:
                    if base_url.endswith(endpoint):
                        base_url = base_url[:-len(endpoint)]
                        logger.info(f"Removed endpoint '{endpoint}' from base_url")
                        break

                base_url = base_url.rstrip('/')

          
                import re as _re
                has_version = bool(_re.search(r'/v\d+(/|$)', base_url) or base_url.endswith('/compatible-mode/v1'))
                if not has_version:
                    base_url = base_url + '/v1'
                    logger.info(f"Added /v1 to base_url: {base_url}")
                else:
                    logger.info(f"base_url already contains version path, kept as-is: {base_url}")
            
            client_kwargs: Dict[str, Any] = {
                "model": self.config.get("model", "gpt-3.5-turbo"),
                "temperature": self.config.get("temperature", 0.7),
                "api_key": api_key,
                "base_url": base_url,
                "max_tokens": self.config.get("max_tokens"),
                # 缩短超时与重试，模型不可用时尽快失败，避免前端一直等待
                "timeout": 30.0,
                "max_retries": 1,
            }
            # 新版 langchain-openai：流式末包带回 usage
            try:
                self.client = ChatOpenAI(**client_kwargs, stream_usage=True)
            except TypeError:
                # 兼容旧版参数名
                client_kwargs.pop("timeout", None)
                client_kwargs.pop("max_retries", None)
                try:
                    self.client = ChatOpenAI(**client_kwargs, request_timeout=30.0, max_retries=1)
                except TypeError:
                    self.client = ChatOpenAI(**{k: v for k, v in client_kwargs.items() if k not in ("timeout", "max_retries")})
            
            logger.info(f"LangChain ChatOpenAI initialized: model={self.config.get('model')}, base_url={base_url}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            raise

    def _to_langchain_messages(
        self, messages: List[Union[LLMMessage, Dict[str, Any]]]
    ) -> List[BaseMessage]:
        langchain_messages = []
        for msg in messages:
            if isinstance(msg, LLMMessage):
                content = msg.content
                role = msg.role
            elif isinstance(msg, dict):
                content = msg.get("content", "")
                role = msg.get("role", "user")
            else:
                continue

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
        return langchain_messages
    
    async def chat_completion(
        self,
        messages: List[Union[LLMMessage, Dict[str, Any]]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """聊天完成接口 - 使用 LangChain"""
        try:
            langchain_messages = self._to_langchain_messages(messages)
            logger.info(f"Chat completion: {len(langchain_messages)} messages, stream={stream}")
            
            if stream:
                return self._stream_completion(langchain_messages)
            else:
                started = time.perf_counter()
                response = await self.client.ainvoke(langchain_messages)
                self.last_latency_ms = int((time.perf_counter() - started) * 1000)
                usage = extract_usage_from_message(response)
                self.last_usage = usage
                content = response.content
                if not isinstance(content, str):
                    content = str(content or "")
                return LLMResponse(
                    content=content,
                    usage=usage,
                    model=model or self.config.get("model"),
                )
                
        except Exception as e:
            logger.error(f"Chat completion failed: {e}", exc_info=True)
            raise
    
    async def _stream_completion(self, messages: List[BaseMessage]) -> AsyncGenerator[str, None]:
        """流式聊天完成；结束后 self.last_usage 为真实 usage（若供应商支持）"""
        try:
            logger.info("Starting stream completion...")
            chunk_count = 0
            started = time.perf_counter()
            usage: Dict[str, int] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cached_tokens": 0,
            }
            async for chunk in self.client.astream(messages):
                chunk_usage = extract_usage_from_message(chunk)
                if any(chunk_usage.values()):
                    usage = chunk_usage
                if hasattr(chunk, "content") and chunk.content:
                    chunk_count += 1
                    content = chunk.content
                    if not isinstance(content, str):
                        content = str(content)
                    yield content
            self.last_usage = usage
            self.last_latency_ms = int((time.perf_counter() - started) * 1000)
            logger.info(
                f"Stream completion finished: {chunk_count} chunks, "
                f"usage={usage}, latency_ms={self.last_latency_ms}"
            )
        except Exception as e:
            logger.error(f"Stream completion failed: {e}", exc_info=True)
            raise

    async def stream_completion_with_usage(
        self,
        messages: List[Union[LLMMessage, Dict[str, Any]]],
    ) -> Tuple[AsyncGenerator[str, None], "LLMService"]:
        """流式调用便捷入口：返回生成器；结束后读 self.last_usage。"""
        return self._stream_completion(self._to_langchain_messages(messages)), self


# ==================== 辅助函数 ====================

async def get_llm_service(llm_config_id: Optional[int] = None) -> LLMService:
    """
    获取 LLM 服务实例
    
    Args:
        llm_config_id: LLM 配置 ID，如果为 None 则使用默认配置
        
    Returns:
        LLM 服务实例
    """
    async with async_session() as db:
        config = None
        if llm_config_id:
            # 根据 ID 获取配置
            logger.info(f"获取指定 LLM 配置: config_id={llm_config_id}")
            stmt = select(LLMConfigModel).where(
                LLMConfigModel.id == llm_config_id,
                LLMConfigModel.enabled_flag == 1
            )
            result = await db.execute(stmt)
            config = result.scalar_one_or_none()
            if not config:
                raise ValueError(
                    f"指定的 LLM 配置不存在或已删除（ID={llm_config_id}），"
                    "请在聊天页顶部重新选择模型"
                )
            if not config.is_active:
                raise ValueError(
                    f"指定的 LLM 配置未启用（{config.config_name or config.name}），"
                    "请先在「LLM 配置管理」中启用，或更换其他模型"
                )
        else:
            # 获取默认配置
            logger.info("获取默认 LLM 配置")
            stmt = select(LLMConfigModel).where(
                LLMConfigModel.is_default == True,
                LLMConfigModel.is_active == True,
                LLMConfigModel.enabled_flag == 1
            )
            result = await db.execute(stmt)
            config = result.scalar_one_or_none()
            
            # 无默认时回退到任意已启用配置
            if not config:
                logger.warning("未找到默认配置，尝试使用第一个已启用配置...")
                fallback_stmt = (
                    select(LLMConfigModel)
                    .where(
                        LLMConfigModel.is_active == True,
                        LLMConfigModel.enabled_flag == 1,
                    )
                    .order_by(LLMConfigModel.id.desc())
                    .limit(1)
                )
                fallback_result = await db.execute(fallback_stmt)
                config = fallback_result.scalar_one_or_none()
        
        if not config:
            raise ValueError(
                "未找到可用的 LLM 配置，请先在「AI 管理 → LLM 配置管理」中创建并启用模型，"
                "然后在聊天页顶部选择模型后再发送"
            )
        
        logger.info(f"使用 LLM 配置: ID={config.id}, name={config.config_name}, provider={config.provider}")
        
        # 创建服务实例
        provider = LLMProvider(config.provider)
        service_config = {
            "model": config.model_name,
            "api_key": config.api_key,
            "base_url": config.base_url,
            "temperature": config.temperature or 0.7,
            "max_tokens": config.max_tokens,
            "system_prompt": config.system_prompt or "",
            "supports_vision": bool(config.supports_vision),
            "context_limit": int(config.context_limit or 0),
        }
        
        return LLMService(provider, service_config, llm_config_id=config.id)


async def get_llm_service_by_id(llm_config_id: int) -> LLMService:
    """根据配置 ID 获取 LLM 服务实例"""
    return await get_llm_service(llm_config_id)
