"""
统一通知系统数据模型
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, JSON, BigInteger, Index
from sqlalchemy.orm import relationship
from app.models.base import Base


class NotificationConfigModel(Base):
    """统一通知配置模型"""
    
    __tablename__ = "unified_notification_configs"
    __table_args__ = (
        Index("idx_config_type", "config_type"),
        Index("idx_is_default", "is_default"),
        Index("idx_is_active", "is_active"),
        {'comment': '统一通知配置表', 'mysql_charset': 'utf8mb4'}
    )
    
    name = Column(String(100), nullable=False, comment="配置名称")
    config_type = Column(String(30), default="webhook_feishu", comment="配置类型: webhook_feishu/webhook_wechat/webhook_dingtalk/telegram/email")
    notification_config = Column(JSON, comment="通知配置信息(JSON格式，根据不同类型存储不同字段)")
    is_default = Column(Boolean, default=False, comment="是否默认配置")
    is_active = Column(Boolean, default=True, comment="是否启用")


class NotificationHistoryModel(Base):
    """通知历史记录模型"""
    
    __tablename__ = "notification_histories"
    __table_args__ = (
        Index("idx_config_id", "config_id"),
        Index("idx_status", "status"),
        Index("idx_sent_at", "sent_at"),
        {'comment': '通知历史记录表', 'mysql_charset': 'utf8mb4'}
    )
    
    config_id = Column(BigInteger, nullable=False, comment="通知配置ID")
    title = Column(String(200), nullable=False, comment="通知标题")
    content = Column(Text, comment="通知内容")
    recipient = Column(String(500), comment="接收者")
    status = Column(String(20), default="pending", comment="发送状态: pending/success/failed")
    error_message = Column(Text, comment="错误信息")
    sent_at = Column(Integer, comment="发送时间戳")
    response_data = Column(JSON, comment="响应数据")


class TaskNotificationSettingModel(Base):
    """任务通知设置模型"""
    
    __tablename__ = "task_notification_settings"
    __table_args__ = (
        Index("idx_task", "task_id", "task_type"),
        Index("idx_config", "notification_config_id"),
        {'comment': '任务通知配置表', 'mysql_charset': 'utf8mb4'}
    )
    
    task_id = Column(BigInteger, nullable=False, comment="任务ID")
    task_type = Column(String(10), nullable=False, comment="任务类型: API/UI")
    notification_config_id = Column(BigInteger, nullable=False, comment="通知配置ID")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    notify_on_success = Column(Boolean, default=False, comment="成功时通知")
    notify_on_failure = Column(Boolean, default=True, comment="失败时通知")