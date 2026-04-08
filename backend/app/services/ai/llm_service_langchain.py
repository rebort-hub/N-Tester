"""
LLM 服务封装 - 使用 LangChain，支持所有 OpenAI 兼容的 API
"""
import logging
from typing import List, Dict, Any, Optional, Union, AsyncGenerator
from enum import Enum

from app.models.ai.llm_config import LLMConfigModel
from sqlalchemy import select
from app.db.sqlalchemy import async_session


try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

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


class LLMResponse:
    """LLM 响应类"""
    def __init__(self, content: str, usage: Optional[Dict] = None, model: Optional[str] = None):
        self.content = content
        self.usage = usage or {}
        self.model = model
    
    @property
    def input_tokens(self) -> int:
        return self.usage.get("prompt_tokens", 0)
    
    @property
    def output_tokens(self) -> int:
        return self.usage.get("completion_tokens", 0)
    
    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", 0)


class LLMService:
    """LLM 服务类"""
    
    def __init__(self, provider: LLMProvider, config: Dict[str, Any]):
        self.provider = provider
        self.config = config
        self.client = None
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
                # 移除端点路径
                endpoints_to_remove = ['/chat/completions', '/v1/chat/completions', '/completions']
                for endpoint in endpoints_to_remove:
                    if base_url.endswith(endpoint):
                        base_url = base_url[:-len(endpoint)]
                        logger.info(f"Removed endpoint '{endpoint}' from base_url")
                        break
                
                # 确保以 /v1 结尾
                if not base_url.endswith('/v1') and not base_url.endswith('/compatible-mode/v1'):
                    base_url = base_url.rstrip('/') + '/v1'
                    logger.info(f"Added /v1 to base_url: {base_url}")
            
            # 创建 ChatOpenAI 实例（兼容所有 OpenAI 格式的 API）
            self.client = ChatOpenAI(
                model=self.config.get("model", "gpt-3.5-turbo"),
                temperature=self.config.get("temperature", 0.7),
                api_key=api_key,
                base_url=base_url,
                max_tokens=self.config.get("max_tokens")
            )
            
            logger.info(f"LangChain ChatOpenAI initialized: model={self.config.get('model')}, base_url={base_url}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            raise
    
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
            # 转换消息格式为 LangChain 格式
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
            
            logger.info(f"Chat completion: {len(langchain_messages)} messages, stream={stream}")
            
            if stream:
                # 流式响应
                return self._stream_completion(langchain_messages)
            else:
                # 非流式响应
                response = await self.client.ainvoke(langchain_messages)
                return LLMResponse(
                    content=response.content,
                    usage={},
                    model=model or self.config.get("model")
                )
                
        except Exception as e:
            logger.error(f"Chat completion failed: {e}", exc_info=True)
            raise
    
    async def _stream_completion(self, messages: List[BaseMessage]) -> AsyncGenerator[str, None]:
        """流式聊天完成 - 使用 LangChain"""
        try:
            logger.info("Starting stream completion...")
            chunk_count = 0
            async for chunk in self.client.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    chunk_count += 1
                    yield chunk.content
            logger.info(f"Stream completion finished: {chunk_count} chunks")
        except Exception as e:
            logger.error(f"Stream completion failed: {e}", exc_info=True)
            raise


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
        if llm_config_id:
            # 根据 ID 获取配置
            logger.info(f"获取指定 LLM 配置: config_id={llm_config_id}")
            stmt = select(LLMConfigModel).where(
                LLMConfigModel.id == llm_config_id,
                LLMConfigModel.enabled_flag == 1
            )
            result = await db.execute(stmt)
            config = result.scalar_one_or_none()
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
            
            # 如果没有默认配置，记录所有配置的状态
            if not config:
                logger.warning("未找到默认配置，查询所有配置状态...")
                all_stmt = select(LLMConfigModel).where(LLMConfigModel.enabled_flag == 1)
                all_result = await db.execute(all_stmt)
                all_configs = all_result.scalars().all()
                for c in all_configs:
                    logger.info(f"配置 ID={c.id}, name={c.config_name}, is_default={c.is_default}, is_active={c.is_active}")
        
        if not config:
            raise ValueError("No LLM configuration found")
        
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
        
        return LLMService(provider, service_config)


async def get_llm_service_by_id(llm_config_id: int) -> LLMService:
    """根据配置 ID 获取 LLM 服务实例"""
    return await get_llm_service(llm_config_id)
