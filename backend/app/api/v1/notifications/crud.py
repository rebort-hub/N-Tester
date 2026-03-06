"""
统一通知系统数据库操作
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, desc, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.base_crud import BaseCRUD
from .model import NotificationConfigModel, NotificationHistoryModel, TaskNotificationSettingModel
from .schema import (
    NotificationConfigCreate, NotificationConfigUpdate,
    NotificationHistoryCreate,
    TaskNotificationSettingCreate, TaskNotificationSettingUpdate
)


class NotificationConfigCRUD(BaseCRUD[NotificationConfigModel]):
    """通知配置CRUD操作"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(NotificationConfigModel, db)
    
    async def get_by_type(self, config_type: str, is_active: bool = True) -> List[NotificationConfigModel]:
        """根据类型获取通知配置"""
        conditions = [
            self.model.config_type == config_type,
            self.model.enabled_flag == True
        ]
        if is_active is not None:
            conditions.append(self.model.is_active == is_active)
        
        stmt = select(self.model).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_list_crud(
        self,
        conditions: list = None,
        order_by: list = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[NotificationConfigModel], int]:
        """获取列表（带分页）"""
        # 添加默认条件：只查询未删除的记录
        base_conditions = [self.model.enabled_flag == True]
        if conditions:
            base_conditions.extend(conditions)
        
        return await super().get_list_crud(
            conditions=base_conditions,
            order_by=order_by,
            skip=skip,
            limit=limit
        )
    
    async def get_default_config(self, config_type: str = None) -> Optional[NotificationConfigModel]:
        """获取默认通知配置"""
        conditions = [
            self.model.is_default == True,
            self.model.is_active == True,
            self.model.enabled_flag == True
        ]
        if config_type:
            conditions.append(self.model.config_type == config_type)
        
        stmt = select(self.model).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def set_default(self, config_id: int, config_type: str) -> bool:
        """设置默认配置"""
        # 先取消同类型的其他默认配置
        stmt1 = (
            update(self.model)
            .where(and_(
                self.model.config_type == config_type,
                self.model.id != config_id,
                self.model.enabled_flag == True
            ))
            .values(is_default=False)
        )
        await self.db.execute(stmt1)
        
        # 设置当前配置为默认
        stmt2 = (
            update(self.model)
            .where(and_(
                self.model.id == config_id,
                self.model.enabled_flag == True
            ))
            .values(is_default=True)
        )
        result = await self.db.execute(stmt2)
        
        await self.db.commit()
        return result.rowcount > 0
    
    async def get_active_configs(self) -> List[NotificationConfigModel]:
        """获取所有激活的通知配置"""
        stmt = select(self.model).where(and_(
            self.model.is_active == True,
            self.model.enabled_flag == True
        ))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class NotificationHistoryCRUD(BaseCRUD[NotificationHistoryModel]):
    """通知历史CRUD操作"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(NotificationHistoryModel, db)
    
    async def get_by_config(self, config_id: int, skip: int = 0, limit: int = 100) -> List[NotificationHistoryModel]:
        """根据配置ID获取通知历史"""
        stmt = (
            select(self.model)
            .where(and_(
                self.model.config_id == config_id,
                self.model.enabled_flag == True
            ))
            .order_by(desc(self.model.creation_date))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[NotificationHistoryModel]:
        """根据状态获取通知历史"""
        stmt = (
            select(self.model)
            .where(and_(
                self.model.status == status,
                self.model.enabled_flag == True
            ))
            .order_by(desc(self.model.creation_date))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_recent_histories(self, days: int = 7, skip: int = 0, limit: int = 100) -> List[NotificationHistoryModel]:
        """获取最近的通知历史"""
        from datetime import datetime, timedelta
        start_time = datetime.now() - timedelta(days=days)
        
        stmt = (
            select(self.model)
            .where(and_(
                self.model.creation_date >= start_time,
                self.model.enabled_flag == True
            ))
            .order_by(desc(self.model.creation_date))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def update_status(self, history_id: int, status: str, error_message: str = None, response_data: Dict[str, Any] = None) -> bool:
        """更新通知状态"""
        update_data = {"status": status}
        if error_message:
            update_data["error_message"] = error_message
        if response_data:
            update_data["response_data"] = response_data
        
        stmt = (
            update(self.model)
            .where(and_(
                self.model.id == history_id,
                self.model.enabled_flag == True
            ))
            .values(**update_data)
        )
        result = await self.db.execute(stmt)
        
        await self.db.commit()
        return result.rowcount > 0


class TaskNotificationSettingCRUD(BaseCRUD[TaskNotificationSettingModel]):
    """任务通知设置CRUD操作"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(TaskNotificationSettingModel, db)
    
    async def get_list_crud(
        self,
        conditions: list = None,
        order_by: list = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[TaskNotificationSettingModel], int]:
        """获取列表（带分页）"""
        # 添加默认条件：只查询未删除的记录
        base_conditions = [self.model.enabled_flag == True]
        if conditions:
            base_conditions.extend(conditions)
        
        return await super().get_list_crud(
            conditions=base_conditions,
            order_by=order_by or [self.model.creation_date.desc()],
            skip=skip,
            limit=limit
        )
    
    async def get_by_task(self, task_id: int, task_type: str) -> List[TaskNotificationSettingModel]:
        """根据任务获取通知设置"""
        stmt = select(self.model).where(and_(
            self.model.task_id == task_id,
            self.model.task_type == task_type,
            self.model.enabled_flag == True
        ))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_enabled_settings(self, task_id: int, task_type: str) -> List[TaskNotificationSettingModel]:
        """获取启用的任务通知设置"""
        stmt = select(self.model).where(and_(
            self.model.task_id == task_id,
            self.model.task_type == task_type,
            self.model.is_enabled == True,
            self.model.enabled_flag == True
        ))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_config(self, config_id: int) -> List[TaskNotificationSettingModel]:
        """根据通知配置获取任务设置"""
        stmt = select(self.model).where(and_(
            self.model.notification_config_id == config_id,
            self.model.enabled_flag == True
        ))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def delete_by_task(self, task_id: int, task_type: str) -> bool:
        """删除任务的所有通知设置"""
        stmt = (
            update(self.model)
            .where(and_(
                self.model.task_id == task_id,
                self.model.task_type == task_type,
                self.model.enabled_flag == True
            ))
            .values(enabled_flag=False)
        )
        result = await self.db.execute(stmt)
        
        await self.db.commit()
        return result.rowcount > 0