"""
MCP 执行记录模型
"""
from sqlalchemy import Column, BigInteger, String, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base


class MCPExecutionRecordModel(Base):
    """MCP 执行记录"""
    __tablename__ = "sys_mcp_execution_record"
    __table_args__ = {"comment": "MCP 执行记录表"}

    conversation_id = Column(BigInteger, ForeignKey("sys_conversation.id"), nullable=False, index=True, comment="对话ID")
    user_id = Column(BigInteger, nullable=False, index=True, comment="用户ID")
    project_id = Column(BigInteger, nullable=True, index=True, comment="项目ID")
    knowledge_base_id = Column(BigInteger, nullable=True, comment="知识库ID")
    mcp_config_id = Column(BigInteger, nullable=True, index=True, comment="MCP配置ID")
    phase = Column(String(30), nullable=False, default="auto_plan", comment="阶段 auto_plan/tool_call/forced_call")
    tool_name = Column(String(255), nullable=True, comment="工具名")
    tool_arguments = Column(JSON, nullable=True, comment="工具参数")
    status = Column(String(20), nullable=False, default="success", comment="状态 success/failed/skipped")
    duration_ms = Column(Integer, nullable=True, comment="耗时毫秒")
    output_summary = Column(Text, nullable=True, comment="输出摘要")
    error_message = Column(Text, nullable=True, comment="错误信息")

    conversation = relationship("ConversationModel")

