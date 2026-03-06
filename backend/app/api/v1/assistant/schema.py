# AI助手模块 - 数据传输对象层

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# AI助手配置相关Schema
class AssistantConfigBase(BaseModel):
    """AI助手配置基础Schema"""
    name: str = Field(..., description="助手名称", max_length=100)
    dify_api_key: str = Field(..., description="Dify API Key", max_length=200)
    dify_base_url: str = Field(..., description="Dify Base URL", max_length=500)
    assistant_type: str = Field("chatbot", description="助手类型: chatbot/workflow/agent")


class AssistantConfigCreate(AssistantConfigBase):
    """创建AI助手配置请求"""
    pass


class AssistantConfigUpdate(BaseModel):
    """更新AI助手配置请求"""
    name: Optional[str] = Field(None, description="助手名称", max_length=100)
    dify_api_key: Optional[str] = Field(None, description="Dify API Key", max_length=200)
    dify_base_url: Optional[str] = Field(None, description="Dify Base URL", max_length=500)
    assistant_type: Optional[str] = Field(None, description="助手类型")
    is_active: Optional[bool] = Field(None, description="是否启用")


class AssistantConfigResponse(AssistantConfigBase):
    """AI助手配置响应"""
    id: int = Field(..., description="配置ID")
    is_active: bool = Field(..., description="是否启用")
    created_by: int = Field(..., description="创建者ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# AI对话相关Schema
class ConversationBase(BaseModel):
    """AI对话基础Schema"""
    title: Optional[str] = Field(None, description="对话标题", max_length=200)


class ConversationCreate(ConversationBase):
    """创建AI对话请求"""
    assistant_config_id: int = Field(..., description="助手配置ID")


class ConversationUpdate(BaseModel):
    """更新AI对话请求"""
    title: Optional[str] = Field(None, description="对话标题", max_length=200)


class ConversationResponse(ConversationBase):
    """AI对话响应"""
    id: int = Field(..., description="对话ID")
    user_id: int = Field(..., description="用户ID")
    assistant_config_id: int = Field(..., description="助手配置ID")
    conversation_id: Optional[str] = Field(None, description="Dify会话ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 关联数据
    assistant_name: Optional[str] = Field(None, description="助手名称")
    message_count: int = Field(0, description="消息数量")
    last_message_time: Optional[datetime] = Field(None, description="最后消息时间")

    class Config:
        from_attributes = True


# AI消息相关Schema
class MessageBase(BaseModel):
    """AI消息基础Schema"""
    content: str = Field(..., description="消息内容")


class MessageCreate(MessageBase):
    """创建AI消息请求"""
    conversation_id: int = Field(..., description="对话ID")


class MessageResponse(MessageBase):
    """AI消息响应"""
    id: int = Field(..., description="消息ID")
    conversation_id: int = Field(..., description="对话ID")
    role: str = Field(..., description="角色: user/assistant")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


# Dify集成相关Schema
class DifyChatRequest(BaseModel):
    """Dify聊天请求"""
    query: str = Field(..., description="用户问题")
    conversation_id: Optional[str] = Field(None, description="会话ID")
    user: str = Field("user", description="用户标识")


class DifyChatResponse(BaseModel):
    """Dify聊天响应"""
    answer: str = Field(..., description="AI回答")
    conversation_id: str = Field(..., description="会话ID")
    message_id: str = Field(..., description="消息ID")


# 统计相关Schema
class AssistantStatistics(BaseModel):
    """AI助手统计"""
    total_configs: int = Field(0, description="总配置数")
    active_configs: int = Field(0, description="活跃配置数")
    total_conversations: int = Field(0, description="总对话数")
    total_messages: int = Field(0, description="总消息数")
    today_conversations: int = Field(0, description="今日对话数")
    today_messages: int = Field(0, description="今日消息数")


# 分页响应Schema
class PaginatedResponse(BaseModel):
    """分页响应"""
    items: List = Field([], description="数据列表")
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页")
    page_size: int = Field(20, description="每页大小")
    pages: int = Field(0, description="总页数")