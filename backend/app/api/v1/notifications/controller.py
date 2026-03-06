"""
统一通知系统API控制器
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sqlalchemy import get_db
from app.core.dependencies import get_current_user_id
from app.common.response import success_response, error_response
from .service import notification_service, task_notification_service
from .schema import (
    NotificationConfigCreate, NotificationConfigUpdate, NotificationConfigResponse,
    NotificationHistoryResponse, TaskNotificationSettingCreate, TaskNotificationSettingUpdate,
    TaskNotificationSettingResponse, SendNotificationRequest, SendNotificationResponse,
    NotificationConfigBatchDeleteSchema, NotificationHistoryBatchDeleteSchema,
    TaskNotificationSettingBatchDeleteSchema
)

router = APIRouter(prefix="/notifications", tags=["统一通知系统"])


# 通知配置管理
@router.post("/configs", response_model=dict, summary="创建通知配置")
async def create_notification_config(
    config_data: NotificationConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建通知配置"""
    try:
        config = await notification_service.create_config(
            db=db,
            config_data=config_data,
            current_user_id=current_user_id
        )
        return success_response(data=config.dict(), message="通知配置创建成功")
    except Exception as e:
        return error_response(message=f"创建失败: {str(e)}")


@router.get("/configs", response_model=dict, summary="获取通知配置列表")
async def get_notification_configs(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    config_type: Optional[str] = Query(None, description="配置类型"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取通知配置列表"""
    try:
        configs = await notification_service.get_configs(
            db=db,
            skip=skip,
            limit=limit,
            config_type=config_type,
            is_active=is_active
        )
        return success_response(data=configs, message="获取成功")
    except Exception as e:
        return error_response(message=f"获取失败: {str(e)}")


@router.get("/configs/{config_id}", response_model=dict, summary="获取通知配置详情")
async def get_notification_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取通知配置详情"""
    try:
        config = await notification_service.get_config(db=db, config_id=config_id)
        if not config:
            return error_response(message="通知配置不存在")
        return success_response(data=config.dict(), message="获取成功")
    except Exception as e:
        return error_response(message=f"获取失败: {str(e)}")


@router.put("/configs/{config_id}", response_model=dict, summary="更新通知配置")
async def update_notification_config(
    config_id: int,
    config_data: NotificationConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新通知配置"""
    try:
        config = await notification_service.update_config(
            db=db,
            config_id=config_id,
            config_data=config_data,
            current_user_id=current_user_id
        )
        if not config:
            return error_response(message="通知配置不存在")
        return success_response(data=config.dict(), message="更新成功")
    except Exception as e:
        return error_response(message=f"更新失败: {str(e)}")


@router.delete("/configs/{config_id}", response_model=dict, summary="删除通知配置")
async def delete_notification_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除通知配置"""
    try:
        success = await notification_service.delete_config(
            db=db,
            config_id=config_id,
            current_user_id=current_user_id
        )
        if not success:
            return error_response(message="通知配置不存在")
        return success_response(message="删除成功")
    except Exception as e:
        return error_response(message=f"删除失败: {str(e)}")


@router.delete("/configs", response_model=dict, summary="批量删除通知配置")
async def batch_delete_notification_configs(
    data: NotificationConfigBatchDeleteSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """批量删除通知配置"""
    try:
        if not data.ids:
            return error_response(message="请选择要删除的配置")
        
        success = await notification_service.delete_configs(
            db=db,
            config_ids=data.ids,
            current_user_id=current_user_id
        )
        if not success:
            return error_response(message="删除失败")
        return success_response(message=f"成功删除 {len(data.ids)} 个配置")
    except Exception as e:
        return error_response(message=f"删除失败: {str(e)}")


@router.post("/configs/{config_id}/set-default", response_model=dict, summary="设置默认通知配置")
async def set_default_notification_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """设置默认通知配置"""
    try:
        success = await notification_service.set_default_config(
            db=db,
            config_id=config_id,
            current_user_id=current_user_id
        )
        if not success:
            return error_response(message="通知配置不存在")
        return success_response(message="设置成功")
    except Exception as e:
        return error_response(message=f"设置失败: {str(e)}")


@router.post("/configs/{config_id}/test", response_model=dict, summary="测试通知配置")
async def test_notification_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """测试通知配置"""
    try:
        result = await notification_service.test_notification(
            db=db,
            config_id=config_id,
            current_user_id=current_user_id
        )
        return success_response(data=result.dict(), message="测试完成")
    except Exception as e:
        return error_response(message=f"测试失败: {str(e)}")


# 发送通知
@router.post("/send", response_model=dict, summary="发送通知")
async def send_notification(
    request: SendNotificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """发送通知"""
    try:
        result = await notification_service.send_notification(
            db=db,
            request=request,
            current_user_id=current_user_id
        )
        return success_response(data=result.dict(), message="发送完成")
    except Exception as e:
        return error_response(message=f"发送失败: {str(e)}")


# 通知历史
@router.get("/histories", response_model=dict, summary="获取通知历史")
async def get_notification_histories(
    config_id: Optional[int] = Query(None, description="通知配置ID"),
    status: Optional[str] = Query(None, description="发送状态"),
    days: int = Query(7, ge=1, le=30, description="最近天数"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取通知历史"""
    try:
        histories = await notification_service.get_notification_histories(
            db=db,
            config_id=config_id,
            status=status,
            days=days,
            skip=skip,
            limit=limit
        )
        return success_response(data=histories, message="获取成功")
    except Exception as e:
        return error_response(message=f"获取失败: {str(e)}")


@router.delete("/histories/{history_id}", response_model=dict, summary="删除通知历史记录")
async def delete_notification_history(
    history_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除通知历史记录"""
    try:
        success = await notification_service.delete_notification_history(
            db=db,
            history_id=history_id,
            current_user_id=current_user_id
        )
        if not success:
            return error_response(message="通知历史记录不存在")
        return success_response(message="删除成功")
    except Exception as e:
        return error_response(message=f"删除失败: {str(e)}")


@router.delete("/histories", response_model=dict, summary="批量删除通知历史记录")
async def batch_delete_notification_histories(
    data: NotificationHistoryBatchDeleteSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """批量删除通知历史记录"""
    try:
        if not data.ids:
            return error_response(message="请选择要删除的历史记录")
        
        success = await notification_service.delete_notification_histories(
            db=db,
            history_ids=data.ids,
            current_user_id=current_user_id
        )
        if not success:
            return error_response(message="删除失败")
        return success_response(message=f"成功删除 {len(data.ids)} 条历史记录")
    except Exception as e:
        return error_response(message=f"删除失败: {str(e)}")


# 任务通知设置
@router.post("/task-settings", response_model=dict, summary="创建任务通知设置")
async def create_task_notification_setting(
    setting_data: TaskNotificationSettingCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建任务通知设置"""
    try:
        setting = await task_notification_service.create_task_setting(
            db=db,
            setting_data=setting_data,
            current_user_id=current_user_id
        )
        return success_response(data=TaskNotificationSettingResponse.from_orm(setting).dict(), message="创建成功")
    except Exception as e:
        return error_response(message=f"创建失败: {str(e)}")


@router.get("/task-settings", response_model=dict, summary="获取任务通知设置")
async def get_task_notification_settings(
    task_id: Optional[int] = Query(None, description="任务ID"),
    task_type: Optional[str] = Query(None, description="任务类型"),
    notification_config_id: Optional[int] = Query(None, description="通知配置ID"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取任务通知设置"""
    try:
        settings = await task_notification_service.get_task_settings(
            db=db,
            task_id=task_id,
            task_type=task_type,
            notification_config_id=notification_config_id,
            skip=skip,
            limit=limit
        )
        return success_response(data=settings, message="获取成功")
    except Exception as e:
        return error_response(message=f"获取失败: {str(e)}")


@router.put("/task-settings/{setting_id}", response_model=dict, summary="更新任务通知设置")
async def update_task_notification_setting(
    setting_id: int,
    setting_data: TaskNotificationSettingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新任务通知设置"""
    try:
        setting = await task_notification_service.update_task_setting(
            db=db,
            setting_id=setting_id,
            setting_data=setting_data,
            current_user_id=current_user_id
        )
        if not setting:
            return error_response(message="任务通知设置不存在")
        return success_response(data=TaskNotificationSettingResponse.from_orm(setting).dict(), message="更新成功")
    except Exception as e:
        return error_response(message=f"更新失败: {str(e)}")


@router.delete("/task-settings/{setting_id}", response_model=dict, summary="删除任务通知设置")
async def delete_task_notification_setting(
    setting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除任务通知设置"""
    try:
        success = await task_notification_service.delete_task_setting(
            db=db,
            setting_id=setting_id,
            current_user_id=current_user_id
        )
        if not success:
            return error_response(message="任务通知设置不存在")
        return success_response(message="删除成功")
    except Exception as e:
        return error_response(message=f"删除失败: {str(e)}")


@router.delete("/task-settings", response_model=dict, summary="批量删除任务通知设置")
async def batch_delete_task_notification_settings(
    data: TaskNotificationSettingBatchDeleteSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """批量删除任务通知设置"""
    try:
        if not data.ids:
            return error_response(message="请选择要删除的设置")
        
        success = await task_notification_service.delete_task_settings(
            db=db,
            setting_ids=data.ids,
            current_user_id=current_user_id
        )
        if not success:
            return error_response(message="删除失败")
        return success_response(message=f"成功删除 {len(data.ids)} 个设置")
    except Exception as e:
        return error_response(message=f"删除失败: {str(e)}")


# 获取支持的通知类型
@router.get("/types", response_model=dict, summary="获取支持的通知类型")
async def get_notification_types():
    """获取支持的通知类型"""
    types = [
        {
            "type": "webhook_feishu",
            "name": "飞书机器人",
            "description": "通过飞书Webhook机器人发送通知",
            "fields": [
                {"name": "webhook_url", "label": "Webhook URL", "type": "url", "required": True},
                {"name": "secret", "label": "签名密钥", "type": "password", "required": False},
                {"name": "keywords", "label": "关键词", "type": "array", "required": False}
            ]
        },
        {
            "type": "webhook_wechat",
            "name": "企业微信机器人",
            "description": "通过企业微信Webhook机器人发送通知",
            "fields": [
                {"name": "webhook_url", "label": "Webhook URL", "type": "url", "required": True},
                {"name": "mentioned_list", "label": "提醒成员", "type": "array", "required": False},
                {"name": "mentioned_mobile_list", "label": "提醒手机号", "type": "array", "required": False}
            ]
        },
        {
            "type": "webhook_dingtalk",
            "name": "钉钉机器人",
            "description": "通过钉钉Webhook机器人发送通知",
            "fields": [
                {"name": "webhook_url", "label": "Webhook URL", "type": "url", "required": True},
                {"name": "secret", "label": "签名密钥", "type": "password", "required": False},
                {"name": "at_mobiles", "label": "@手机号", "type": "array", "required": False},
                {"name": "at_user_ids", "label": "@用户ID", "type": "array", "required": False},
                {"name": "is_at_all", "label": "@所有人", "type": "boolean", "required": False}
            ]
        },
        {
            "type": "telegram",
            "name": "Telegram机器人",
            "description": "通过Telegram机器人发送通知",
            "fields": [
                {"name": "bot_token", "label": "Bot Token", "type": "password", "required": True},
                {"name": "chat_id", "label": "Chat ID", "type": "text", "required": True},
                {"name": "parse_mode", "label": "解析模式", "type": "select", "required": False, "options": ["HTML", "Markdown", "MarkdownV2"]},
                {"name": "disable_web_page_preview", "label": "禁用网页预览", "type": "boolean", "required": False}
            ]
        },
        {
            "type": "email",
            "name": "邮件推送",
            "description": "通过SMTP服务器发送邮件通知",
            "fields": [
                {"name": "smtp_server", "label": "SMTP服务器", "type": "text", "required": True},
                {"name": "smtp_port", "label": "SMTP端口", "type": "number", "required": True},
                {"name": "username", "label": "用户名", "type": "text", "required": True},
                {"name": "password", "label": "密码", "type": "password", "required": True},
                {"name": "from_email", "label": "发件人邮箱", "type": "email", "required": True},
                {"name": "to_emails", "label": "收件人邮箱", "type": "array", "required": True},
                {"name": "use_tls", "label": "使用TLS", "type": "boolean", "required": False},
                {"name": "use_ssl", "label": "使用SSL", "type": "boolean", "required": False}
            ]
        }
    ]
    
    return success_response(data=types, message="获取成功")