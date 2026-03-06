"""
统一通知系统Pydantic模式
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_serializer
from app.schemas.base import BaseSchema


# 通知配置相关模式
class NotificationConfigBase(BaseModel):
    """通知配置基础模式"""
    name: str = Field(..., description="配置名称")
    config_type: str = Field(default="webhook_feishu", description="配置类型")
    notification_config: Optional[Dict[str, Any]] = Field(None, description="通知配置信息")
    is_default: bool = Field(default=False, description="是否默认配置")
    is_active: bool = Field(default=True, description="是否启用")


class NotificationConfigCreate(NotificationConfigBase):
    """创建通知配置模式"""
    pass


class NotificationConfigUpdate(BaseModel):
    """更新通知配置模式"""
    name: Optional[str] = Field(None, description="配置名称")
    config_type: Optional[str] = Field(None, description="配置类型")
    notification_config: Optional[Dict[str, Any]] = Field(None, description="通知配置信息")
    is_default: Optional[bool] = Field(None, description="是否默认配置")
    is_active: Optional[bool] = Field(None, description="是否启用")


class NotificationConfigResponse(BaseSchema, NotificationConfigBase):
    """通知配置响应模式"""
    id: int = Field(..., description="配置ID")
    creation_date: Optional[datetime] = Field(None, description="创建时间")
    created_by: Optional[int] = Field(None, description="创建人ID")
    
    @field_serializer('creation_date')
    def serialize_creation_date(self, value: Optional[datetime]) -> Optional[str]:
        if value:
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return None


# 通知历史相关模式
class NotificationHistoryBase(BaseModel):
    """通知历史基础模式"""
    config_id: int = Field(..., description="通知配置ID")
    title: str = Field(..., description="通知标题")
    content: Optional[str] = Field(None, description="通知内容")
    recipient: Optional[str] = Field(None, description="接收者")
    status: str = Field(default="pending", description="发送状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    sent_at: Optional[int] = Field(None, description="发送时间戳")
    response_data: Optional[Dict[str, Any]] = Field(None, description="响应数据")


class NotificationHistoryCreate(NotificationHistoryBase):
    """创建通知历史模式"""
    pass


class NotificationHistoryResponse(BaseSchema, NotificationHistoryBase):
    """通知历史响应模式"""
    id: int = Field(..., description="历史记录ID")
    creation_date: Optional[datetime] = Field(None, description="创建时间")
    created_by: Optional[int] = Field(None, description="创建人ID")
    
    @field_serializer('creation_date')
    def serialize_creation_date(self, value: Optional[datetime]) -> Optional[str]:
        if value:
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return None


# 任务通知设置相关模式
class TaskNotificationSettingBase(BaseModel):
    """任务通知设置基础模式"""
    task_id: int = Field(..., description="任务ID")
    task_type: str = Field(..., description="任务类型")
    notification_config_id: int = Field(..., description="通知配置ID")
    is_enabled: bool = Field(default=True, description="是否启用")
    notify_on_success: bool = Field(default=False, description="成功时通知")
    notify_on_failure: bool = Field(default=True, description="失败时通知")


class TaskNotificationSettingCreate(TaskNotificationSettingBase):
    """创建任务通知设置模式"""
    pass


class TaskNotificationSettingUpdate(BaseModel):
    """更新任务通知设置模式"""
    notification_config_id: Optional[int] = Field(None, description="通知配置ID")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    notify_on_success: Optional[bool] = Field(None, description="成功时通知")
    notify_on_failure: Optional[bool] = Field(None, description="失败时通知")


class TaskNotificationSettingResponse(BaseSchema, TaskNotificationSettingBase):
    """任务通知设置响应模式"""
    id: int = Field(..., description="设置ID")
    creation_date: Optional[datetime] = Field(None, description="创建时间")
    created_by: Optional[int] = Field(None, description="创建人ID")
    
    @field_serializer('creation_date')
    def serialize_creation_date(self, value: Optional[datetime]) -> Optional[str]:
        if value:
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return None


# 发送通知相关模式
class SendNotificationRequest(BaseModel):
    """发送通知请求模式"""
    config_id: int = Field(..., description="通知配置ID")
    title: str = Field(..., description="通知标题")
    content: str = Field(..., description="通知内容")
    recipient: Optional[str] = Field(None, description="接收者")


class SendNotificationResponse(BaseModel):
    """发送通知响应模式"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    history_id: Optional[int] = Field(None, description="历史记录ID")


# 机器人配置模式
class WebhookBotConfig(BaseModel):
    """Webhook机器人配置模式"""
    webhook_url: str = Field(..., description="Webhook URL")
    secret: Optional[str] = Field(None, description="签名密钥")
    keywords: Optional[List[str]] = Field(None, description="关键词")
    at_mobiles: Optional[List[str]] = Field(None, description="@手机号列表")
    at_user_ids: Optional[List[str]] = Field(None, description="@用户ID列表")
    is_at_all: bool = Field(default=False, description="是否@所有人")


class FeishuBotConfig(WebhookBotConfig):
    """飞书机器人配置模式"""
    pass


class WechatBotConfig(WebhookBotConfig):
    """企业微信机器人配置模式"""
    mentioned_list: Optional[List[str]] = Field(None, description="提醒成员列表")
    mentioned_mobile_list: Optional[List[str]] = Field(None, description="提醒手机号列表")


class DingtalkBotConfig(WebhookBotConfig):
    """钉钉机器人配置模式"""
    pass


# 批量操作相关模式
class NotificationConfigBatchDeleteSchema(BaseSchema):
    """通知配置批量删除模式"""
    ids: List[int] = Field(..., description="配置ID列表")


class NotificationHistoryBatchDeleteSchema(BaseSchema):
    """通知历史批量删除模式"""
    ids: List[int] = Field(..., description="历史记录ID列表")


class TaskNotificationSettingBatchDeleteSchema(BaseSchema):
    """任务通知设置批量删除模式"""
    ids: List[int] = Field(..., description="设置ID列表")