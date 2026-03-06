# AI助手模块 - 数据模型层

from sqlalchemy import Column, BigInteger, String, Text, DateTime, Boolean, Index
from sqlalchemy.sql import func
from app.core.base_model import BaseModel


class AIAssistantConfig(BaseModel):
    """AI助手配置表"""
    __tablename__ = 'ai_assistant_configs'
    
    name = Column(String(100), nullable=False, comment='助手名称')
    dify_api_key = Column(String(200), nullable=False, comment='Dify API Key')
    dify_base_url = Column(String(500), nullable=False, comment='Dify Base URL')
    assistant_type = Column(String(20), default='chatbot', comment='助手类型: chatbot/workflow/agent')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_by = Column(BigInteger, nullable=False, comment='创建者ID')
    
    __table_args__ = (
        Index('idx_created_by', 'created_by'),
        Index('idx_active', 'is_active'),
    )


class AIConversation(BaseModel):
    """AI对话记录表"""
    __tablename__ = 'ai_conversations'
    
    user_id = Column(BigInteger, nullable=False, comment='用户ID')
    assistant_config_id = Column(BigInteger, nullable=False, comment='助手配置ID')
    conversation_id = Column(String(100), comment='Dify会话ID')
    title = Column(String(200), comment='对话标题')
    
    __table_args__ = (
        Index('idx_user', 'user_id'),
        Index('idx_assistant_config', 'assistant_config_id'),
        Index('idx_conversation_id', 'conversation_id'),
    )


class AIMessage(BaseModel):
    """AI消息记录表"""
    __tablename__ = 'ai_messages'
    
    conversation_id = Column(BigInteger, nullable=False, comment='对话ID')
    role = Column(String(20), nullable=False, comment='角色: user/assistant')
    content = Column(Text, nullable=False, comment='消息内容')
    
    __table_args__ = (
        Index('idx_conversation', 'conversation_id'),
        Index('idx_role', 'role'),
    )