"""
统一通知系统业务逻辑服务
"""

import json
import time
import hmac
import hashlib
import base64
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
import httpx
from app.corelibs.logger import logger
from .crud import NotificationConfigCRUD, NotificationHistoryCRUD, TaskNotificationSettingCRUD
from .schema import (
    NotificationConfigCreate, NotificationConfigUpdate, NotificationConfigResponse,
    NotificationHistoryResponse, TaskNotificationSettingCreate, TaskNotificationSettingUpdate,
    TaskNotificationSettingResponse, SendNotificationRequest, SendNotificationResponse
)


class NotificationService:
    """统一通知服务"""
    
    def __init__(self):
        self.timeout = 30  # 请求超时时间
    
    async def create_config(self, db: AsyncSession, *, config_data: NotificationConfigCreate, current_user_id: int) -> NotificationConfigResponse:
        """创建通知配置"""
        # 验证配置数据
        self._validate_config_data(config_data.config_type, config_data.notification_config)
        
        # 创建配置
        crud = NotificationConfigCRUD(db)
        data = config_data.dict()
        data['created_by'] = current_user_id
        config = await crud.create_crud(data=data)
        
        logger.info(f"用户 {current_user_id} 创建通知配置: {config.name}")
        return NotificationConfigResponse.from_orm(config)
    
    async def get_config(self, db: AsyncSession, *, config_id: int) -> Optional[NotificationConfigResponse]:
        """获取通知配置"""
        crud = NotificationConfigCRUD(db)
        config = await crud.get_by_id_crud(id=config_id)
        if not config:
            return None
        return NotificationConfigResponse.from_orm(config)
    
    async def get_configs(self, db: AsyncSession, *, skip: int = 0, limit: int = 100, config_type: str = None, is_active: bool = None) -> dict:
        """获取通知配置列表"""
        crud = NotificationConfigCRUD(db)
        
        if config_type:
            configs = await crud.get_by_type(config_type=config_type, is_active=is_active)
            total = len(configs)
            # 手动分页
            configs = configs[skip:skip + limit]
        else:
            configs, total = await crud.get_list_crud(skip=skip, limit=limit)
            if is_active is not None:
                configs = [c for c in configs if c.is_active == is_active]
                total = len(configs)
        
        items = [NotificationConfigResponse.from_orm(config).dict() for config in configs]
        
        return {
            "items": items,
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "page_size": limit
        }
    
    async def update_config(self, db: AsyncSession, *, config_id: int, config_data: NotificationConfigUpdate, current_user_id: int) -> Optional[NotificationConfigResponse]:
        """更新通知配置"""
        crud = NotificationConfigCRUD(db)
        config = await crud.get_by_id_crud(id=config_id)
        if not config:
            return None
        
        # 验证配置数据
        if config_data.config_type and config_data.notification_config:
            self._validate_config_data(config_data.config_type, config_data.notification_config)
        
        # 更新配置
        update_data = config_data.dict(exclude_unset=True)
        update_data['updated_by'] = current_user_id
        updated_config = await crud.update_crud(
            id=config_id,
            data=update_data
        )
        
        logger.info(f"用户 {current_user_id} 更新通知配置: {updated_config.name}")
        return NotificationConfigResponse.from_orm(updated_config)
    
    async def delete_config(self, db: AsyncSession, *, config_id: int, current_user_id: int) -> bool:
        """删除通知配置"""
        return await self.delete_configs(db=db, config_ids=[config_id], current_user_id=current_user_id)
    
    async def delete_configs(self, db: AsyncSession, *, config_ids: list[int], current_user_id: int) -> bool:
        """批量删除通知配置"""
        crud = NotificationConfigCRUD(db)
        
        # 检查配置是否存在
        for config_id in config_ids:
            config = await crud.get_by_id_crud(id=config_id)
            if not config:
                raise HTTPException(status_code=404, detail=f"通知配置 {config_id} 不存在")
            
            # 检查是否有任务在使用此配置
            task_crud = TaskNotificationSettingCRUD(db)
            task_settings = await task_crud.get_by_config(config_id=config_id)
            if task_settings:
                raise HTTPException(status_code=400, detail=f"通知配置 {config.name} 正在被任务使用，无法删除")
        
        # 硬删除配置
        await crud.delete_crud(config_ids)
        logger.info(f"用户 {current_user_id} 删除通知配置: {config_ids}")
        return True
    
    async def set_default_config(self, db: AsyncSession, *, config_id: int, current_user_id: int) -> bool:
        """设置默认通知配置"""
        crud = NotificationConfigCRUD(db)
        config = await crud.get_by_id_crud(id=config_id)
        if not config:
            return False
        
        result = await crud.set_default(config_id=config_id, config_type=config.config_type)
        if result:
            logger.info(f"用户 {current_user_id} 设置默认通知配置: {config.name}")
        return result
    
    async def send_notification(self, db: AsyncSession, *, request: SendNotificationRequest, current_user_id: int = None) -> SendNotificationResponse:
        """发送通知"""
        # 获取通知配置
        config_crud = NotificationConfigCRUD(db)
        config = await config_crud.get_by_id_crud(id=request.config_id)
        if not config or not config.is_active:
            return SendNotificationResponse(
                success=False,
                message="通知配置不存在或未启用"
            )
        
        # 创建历史记录
        history_data = {
            "config_id": request.config_id,
            "title": request.title,
            "content": request.content,
            "recipient": request.recipient,
            "status": "pending",
            "sent_at": int(time.time())
        }
        
        history_crud = NotificationHistoryCRUD(db)
        history_data['created_by'] = current_user_id
        history = await history_crud.create_crud(data=history_data)
        
        try:
            # 根据配置类型发送通知
            if config.config_type == "webhook_feishu":
                success, message, response_data = await self._send_feishu_notification(config, request)
            elif config.config_type == "webhook_wechat":
                success, message, response_data = await self._send_wechat_notification(config, request)
            elif config.config_type == "webhook_dingtalk":
                success, message, response_data = await self._send_dingtalk_notification(config, request)
            elif config.config_type == "telegram":
                success, message, response_data = await self._send_telegram_notification(config, request)
            elif config.config_type == "email":
                success, message, response_data = await self._send_email_notification(config, request)
            else:
                success, message, response_data = False, f"不支持的通知类型: {config.config_type}", None
            
            # 更新历史记录状态
            status = "success" if success else "failed"
            error_message = None if success else message
            
            await history_crud.update_status(
                history_id=history.id,
                status=status,
                error_message=error_message,
                response_data=response_data
            )
            
            if success:
                logger.info(f"通知发送成功: {request.title}")
            else:
                logger.error(f"通知发送失败: {request.title}, 错误: {message}")
            
            return SendNotificationResponse(
                success=success,
                message=message,
                history_id=history.id
            )
            
        except Exception as e:
            # 更新历史记录为失败状态
            await history_crud.update_status(
                history_id=history.id,
                status="failed",
                error_message=str(e)
            )
            
            logger.error(f"通知发送异常: {request.title}, 错误: {str(e)}")
            return SendNotificationResponse(
                success=False,
                message=f"发送失败: {str(e)}",
                history_id=history.id
            )
    
    async def get_notification_histories(self, db: AsyncSession, *, config_id: int = None, status: str = None, days: int = 7, skip: int = 0, limit: int = 100) -> dict:
        """获取通知历史"""
        crud = NotificationHistoryCRUD(db)
        
        if config_id:
            histories = await crud.get_by_config(config_id=config_id, skip=skip, limit=limit)
        elif status:
            histories = await crud.get_by_status(status=status, skip=skip, limit=limit)
        else:
            histories = await crud.get_recent_histories(days=days, skip=skip, limit=limit)
        
        items = [NotificationHistoryResponse.from_orm(history).dict() for history in histories]
        
        return {
            "items": items,
            "total": len(items),
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "page_size": limit
        }
    
    async def delete_notification_history(self, db: AsyncSession, *, history_id: int, current_user_id: int) -> bool:
        """删除通知历史记录"""
        return await self.delete_notification_histories(db=db, history_ids=[history_id], current_user_id=current_user_id)
    
    async def delete_notification_histories(self, db: AsyncSession, *, history_ids: list[int], current_user_id: int) -> bool:
        """批量删除通知历史记录"""
        crud = NotificationHistoryCRUD(db)
        
        # 检查历史记录是否存在
        for history_id in history_ids:
            history = await crud.get_by_id_crud(id=history_id)
            if not history:
                raise HTTPException(status_code=404, detail=f"通知历史记录 {history_id} 不存在")
        
        # 硬删除历史记录
        await crud.delete_crud(history_ids)
        logger.info(f"用户 {current_user_id} 删除通知历史记录: {history_ids}")
        return True
    
    async def test_notification(self, db: AsyncSession, *, config_id: int, current_user_id: int) -> SendNotificationResponse:
        """测试通知配置"""
        test_request = SendNotificationRequest(
            config_id=config_id,
            title="N-Tester测试通知",
            content="这是一条N-Tester测试通知消息，用于验证通知配置是否正常工作。",
            recipient="测试"
        )
        
        return await self.send_notification(db=db, request=test_request, current_user_id=current_user_id)
    
    def _validate_config_data(self, config_type: str, notification_config: Dict[str, Any]):
        """验证配置数据"""
        if not notification_config:
            raise HTTPException(status_code=400, detail="通知配置不能为空")
        
        # 根据不同类型验证不同的必需字段
        if config_type in ["webhook_feishu", "webhook_wechat", "webhook_dingtalk"]:
            required_fields = ["webhook_url"]
        elif config_type == "telegram":
            required_fields = ["bot_token", "chat_id"]
        elif config_type == "email":
            required_fields = ["smtp_server", "smtp_port", "username", "password", "from_email", "to_emails"]
        else:
            raise HTTPException(status_code=400, detail=f"不支持的通知类型: {config_type}")
        
        for field in required_fields:
            if field not in notification_config:
                raise HTTPException(status_code=400, detail=f"缺少必需字段: {field}")
        
        # 验证URL格式（对于webhook类型）
        if config_type in ["webhook_feishu", "webhook_wechat", "webhook_dingtalk"]:
            webhook_url = notification_config.get("webhook_url", "")
            if not webhook_url.startswith(("http://", "https://")):
                raise HTTPException(status_code=400, detail="Webhook URL格式不正确")
        
        # 验证邮箱格式（对于email类型）
        if config_type == "email":
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            from_email = notification_config.get("from_email", "")
            if not re.match(email_pattern, from_email):
                raise HTTPException(status_code=400, detail="发件人邮箱格式不正确")
            
            to_emails = notification_config.get("to_emails", [])
            if isinstance(to_emails, str):
                to_emails = [to_emails]
            for email in to_emails:
                if not re.match(email_pattern, email):
                    raise HTTPException(status_code=400, detail=f"收件人邮箱格式不正确: {email}")
    
    async def _send_feishu_notification(self, config, request: SendNotificationRequest) -> tuple[bool, str, Dict[str, Any]]:
        """发送飞书通知"""
        webhook_url = config.notification_config.get("webhook_url")
        secret = config.notification_config.get("secret")
        
        # 构建消息体
        message = {
            "msg_type": "text",
            "content": {
                "text": f"{request.title}\n\n{request.content}"
            }
        }
        
        # 如果有签名密钥，添加签名
        if secret:
            timestamp = str(int(time.time()))
            sign = self._generate_feishu_sign(timestamp, secret)
            message["timestamp"] = timestamp
            message["sign"] = sign
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(webhook_url, json=message)
                response_data = response.json()
                
                if response.status_code == 200 and response_data.get("code") == 0:
                    return True, "发送成功", response_data
                else:
                    return False, f"发送失败: {response_data.get('msg', '未知错误')}", response_data
                    
        except Exception as e:
            return False, f"网络请求失败: {str(e)}", None
    
    async def _send_wechat_notification(self, config, request: SendNotificationRequest) -> tuple[bool, str, Dict[str, Any]]:
        """发送企业微信通知"""
        webhook_url = config.notification_config.get("webhook_url")
        
        # 构建消息体
        message = {
            "msgtype": "text",
            "text": {
                "content": f"{request.title}\n\n{request.content}"
            }
        }
        
        # 添加@成员
        mentioned_list = config.notification_config.get("mentioned_list", [])
        mentioned_mobile_list = config.notification_config.get("mentioned_mobile_list", [])
        
        if mentioned_list or mentioned_mobile_list:
            message["text"]["mentioned_list"] = mentioned_list
            message["text"]["mentioned_mobile_list"] = mentioned_mobile_list
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(webhook_url, json=message)
                response_data = response.json()
                
                if response.status_code == 200 and response_data.get("errcode") == 0:
                    return True, "发送成功", response_data
                else:
                    return False, f"发送失败: {response_data.get('errmsg', '未知错误')}", response_data
                    
        except Exception as e:
            return False, f"网络请求失败: {str(e)}", None
    
    async def _send_dingtalk_notification(self, config, request: SendNotificationRequest) -> tuple[bool, str, Dict[str, Any]]:
        """发送钉钉通知"""
        webhook_url = config.notification_config.get("webhook_url")
        secret = config.notification_config.get("secret")
        
        # 如果有签名密钥，添加签名参数
        if secret:
            timestamp = str(round(time.time() * 1000))
            sign = self._generate_dingtalk_sign(timestamp, secret)
            webhook_url += f"&timestamp={timestamp}&sign={sign}"
        
        # 构建消息体
        message = {
            "msgtype": "text",
            "text": {
                "content": f"{request.title}\n\n{request.content}"
            }
        }
        
        # 添加@成员
        at_mobiles = config.notification_config.get("at_mobiles", [])
        at_user_ids = config.notification_config.get("at_user_ids", [])
        is_at_all = config.notification_config.get("is_at_all", False)
        
        if at_mobiles or at_user_ids or is_at_all:
            message["at"] = {
                "atMobiles": at_mobiles,
                "atUserIds": at_user_ids,
                "isAtAll": is_at_all
            }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(webhook_url, json=message)
                response_data = response.json()
                
                if response.status_code == 200 and response_data.get("errcode") == 0:
                    return True, "发送成功", response_data
                else:
                    return False, f"发送失败: {response_data.get('errmsg', '未知错误')}", response_data
                    
        except Exception as e:
            return False, f"网络请求失败: {str(e)}", None
    
    def _generate_feishu_sign(self, timestamp: str, secret: str) -> str:
        """生成飞书签名"""
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return sign
    
    def _generate_dingtalk_sign(self, timestamp: str, secret: str) -> str:
        """生成钉钉签名"""
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return sign
    
    async def _send_telegram_notification(self, config, request: SendNotificationRequest) -> tuple[bool, str, Dict[str, Any]]:
        """发送Telegram通知"""
        bot_token = config.notification_config.get("bot_token")
        chat_id = config.notification_config.get("chat_id")
        parse_mode = config.notification_config.get("parse_mode", "HTML")
        disable_web_page_preview = config.notification_config.get("disable_web_page_preview", False)
        
        if not bot_token or not chat_id:
            return False, "缺少必需的Telegram配置参数", None
        
        # 构建消息内容
        text = f"<b>{request.title}</b>\n\n{request.content}"
        if parse_mode == "Markdown":
            text = f"*{request.title}*\n\n{request.content}"
        elif parse_mode == "MarkdownV2":
            # MarkdownV2需要转义特殊字符
            title = request.title.replace(".", "\.").replace("-", "\-").replace("(", "\(").replace(")", "\)")
            content = request.content.replace(".", "\.").replace("-", "\-").replace("(", "\(").replace(")", "\)")
            text = f"*{title}*\n\n{content}"
        
        # Telegram Bot API URL
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        # 构建请求数据
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=data)
                response_data = response.json()
                
                if response.status_code == 200 and response_data.get("ok"):
                    return True, "发送成功", response_data
                else:
                    error_msg = response_data.get("description", "未知错误")
                    return False, f"发送失败: {error_msg}", response_data
                    
        except Exception as e:
            return False, f"网络请求失败: {str(e)}", None
    
    async def _send_email_notification(self, config, request: SendNotificationRequest) -> tuple[bool, str, Dict[str, Any]]:
        """发送邮件通知"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.header import Header
        
        smtp_server = config.notification_config.get("smtp_server")
        smtp_port = config.notification_config.get("smtp_port", 587)
        username = config.notification_config.get("username")
        password = config.notification_config.get("password")
        from_email = config.notification_config.get("from_email")
        to_emails = config.notification_config.get("to_emails", [])
        use_tls = config.notification_config.get("use_tls", True)
        use_ssl = config.notification_config.get("use_ssl", False)
        
        if not all([smtp_server, username, password, from_email, to_emails]):
            return False, "缺少必需的邮件配置参数", None
        
        try:
            # 创建邮件消息
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails) if isinstance(to_emails, list) else to_emails
            msg['Subject'] = Header(request.title, 'utf-8')
            
            # 添加邮件正文
            body = MIMEText(request.content, 'plain', 'utf-8')
            msg.attach(body)
            
            # 连接SMTP服务器
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port)
                if use_tls:
                    server.starttls()
            
            # 登录并发送邮件
            server.login(username, password)
            text = msg.as_string()
            server.sendmail(from_email, to_emails, text)
            server.quit()
            
            response_data = {
                "from": from_email,
                "to": to_emails,
                "subject": request.title,
                "sent_at": int(time.time())
            }
            
            return True, "发送成功", response_data
            
        except Exception as e:
            return False, f"邮件发送失败: {str(e)}", None


# 任务通知设置服务
class TaskNotificationService:
    """任务通知设置服务"""
    
    async def create_task_setting(self, db: AsyncSession, *, setting_data: TaskNotificationSettingCreate, current_user_id: int):
        """创建任务通知设置"""
        # 检查通知配置是否存在
        config_crud = NotificationConfigCRUD(db)
        config = await config_crud.get_by_id_crud(id=setting_data.notification_config_id)
        if not config or not config.is_active:
            raise HTTPException(status_code=400, detail="通知配置不存在或未启用")
        
        # 检查是否已存在相同的设置
        crud = TaskNotificationSettingCRUD(db)
        existing = await crud.get_by_task(
            task_id=setting_data.task_id,
            task_type=setting_data.task_type
        )
        
        for setting in existing:
            if setting.notification_config_id == setting_data.notification_config_id:
                raise HTTPException(status_code=400, detail="该任务已配置此通知")
        
        # 创建设置
        data = setting_data.dict()
        data['created_by'] = current_user_id
        setting = await crud.create_crud(data=data)
        
        logger.info(f"用户 {current_user_id} 创建任务通知设置: 任务{setting_data.task_id}")
        return setting
    
    async def get_task_settings(self, db: AsyncSession, *, task_id: int = None, task_type: str = None, notification_config_id: int = None, skip: int = 0, limit: int = 100):
        """获取任务通知设置"""
        crud = TaskNotificationSettingCRUD(db)
        
        if task_id is not None and task_type is not None:
            # 获取特定任务的设置
            settings = await crud.get_by_task(task_id=task_id, task_type=task_type)
            items = [TaskNotificationSettingResponse.from_orm(setting).dict() for setting in settings]
            return {
                "items": items,
                "total": len(items),
                "page": 1,
                "page_size": len(items)
            }
        else:
            # 获取所有设置（支持分页和筛选）
            conditions = []
            if task_id is not None:
                conditions.append(crud.model.task_id == task_id)
            if task_type is not None:
                conditions.append(crud.model.task_type == task_type)
            if notification_config_id is not None:
                conditions.append(crud.model.notification_config_id == notification_config_id)
            
            settings, total = await crud.get_list_crud(
                conditions=conditions,
                skip=skip,
                limit=limit
            )
            
            items = [TaskNotificationSettingResponse.from_orm(setting).dict() for setting in settings]
            
            return {
                "items": items,
                "total": total,
                "page": (skip // limit) + 1 if limit > 0 else 1,
                "page_size": limit
            }
    
    async def update_task_setting(self, db: AsyncSession, *, setting_id: int, setting_data: TaskNotificationSettingUpdate, current_user_id: int):
        """更新任务通知设置"""
        crud = TaskNotificationSettingCRUD(db)
        setting = await crud.get_by_id_crud(id=setting_id)
        if not setting:
            return None
        
        # 如果更新通知配置ID，检查配置是否存在
        if setting_data.notification_config_id:
            config_crud = NotificationConfigCRUD(db)
            config = await config_crud.get_by_id_crud(id=setting_data.notification_config_id)
            if not config or not config.is_active:
                raise HTTPException(status_code=400, detail="通知配置不存在或未启用")
        
        update_data = setting_data.dict(exclude_unset=True)
        update_data['updated_by'] = current_user_id
        updated_setting = await crud.update_crud(
            id=setting_id,
            data=update_data
        )
        
        logger.info(f"用户 {current_user_id} 更新任务通知设置: {setting_id}")
        return updated_setting
    
    async def delete_task_setting(self, db: AsyncSession, *, setting_id: int, current_user_id: int) -> bool:
        """删除任务通知设置（硬删除）"""
        return await self.delete_task_settings(db=db, setting_ids=[setting_id], current_user_id=current_user_id)
    
    async def delete_task_settings(self, db: AsyncSession, *, setting_ids: list[int], current_user_id: int) -> bool:
        """批量删除任务通知设置（硬删除）"""
        crud = TaskNotificationSettingCRUD(db)
        
        # 检查设置是否存在
        for setting_id in setting_ids:
            setting = await crud.get_by_id_crud(id=setting_id)
            if not setting:
                raise HTTPException(status_code=404, detail=f"任务通知设置 {setting_id} 不存在")
        
        # 硬删除设置
        await crud.delete_crud(setting_ids)
        logger.info(f"用户 {current_user_id} 删除任务通知设置: {setting_ids}")
        return True


# 创建服务实例
notification_service = NotificationService()
task_notification_service = TaskNotificationService()