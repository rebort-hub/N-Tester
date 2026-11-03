#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort
"""
基础CRUD类提供通用的数据访问操作
"""
from __future__ import annotations

from typing import Any, Generic, TypeVar, Type, Optional, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, text, bindparam
from app.utils.context import AppTraceId

if TYPE_CHECKING:
    from app.core.database import Base

ModelType = TypeVar("ModelType", bound="Base")


class BaseCRUD(Generic[ModelType]):
    """基础CRUD类"""
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        初始化CRUD
        
        Args:
            model: 数据模型类
            db: 数据库会话
        """
        self.model = model
        self.db = db
    
    async def get_by_id_crud(self, id: int) -> Optional[ModelType]:
        """
        根据ID获取单条记录
        
        Args:
            id: 记录ID
            
        Returns:
            模型实例或None
        """
        stmt = select(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_list_crud(
        self,
        conditions: list = None,
        order_by: list = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[ModelType], int]:
        """
        获取列表（带分页）
        
        Args:
            conditions: 查询条件列表
            order_by: 排序条件列表
            skip: 跳过记录数
            limit: 限制记录数
            
        Returns:
            (模型实例列表, 总数)
        """
        # 构建查询
        stmt = select(self.model)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # 应用排序
        if order_by:
            for order in order_by:
                stmt = stmt.order_by(order)
        
        # 查询总数
        count_stmt = select(func.count(self.model.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()
        
        # 应用分页
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        
        return list(items), total
    
    async def create_crud(self, data: dict[str, Any]) -> ModelType:
        """
        创建记录
        
        Args:
            data: 数据字典
            
        Returns:
            新创建的模型实例
        """
        # 获取注入TraceId
        if hasattr(self.model, 'trace_id') and AppTraceId.get():
            data = {**data, 'trace_id': AppTraceId.get()}
        obj = self.model(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj
    
    async def update_crud(self, id: int, data: dict[str, Any]) -> ModelType:
        """
        更新记录
        
        Args:
            id: 记录ID
            data: 更新数据字典
            
        Returns:
            更新后的模型实例
        """
        stmt = update(self.model).where(self.model.id == id).values(**data)
        await self.db.execute(stmt)
        await self.db.commit()
        return await self.get_by_id_crud(id)
    
    async def delete_crud(self, ids: list[int]) -> None:
        """
        删除记录（硬删除）
        
        Args:
            ids: 记录ID列表
        """
        stmt = delete(self.model).where(self.model.id.in_(ids))
        await self.db.execute(stmt)
        await self.db.commit()
    
    async def soft_delete_crud(self, ids: list[int]) -> None:
        """
        软删除记录
        
        Args:
            ids: 记录ID列表
        """
        if hasattr(self.model, 'enabled_flag'):
            stmt = update(self.model).where(self.model.id.in_(ids)).values(enabled_flag=0)
            await self.db.execute(stmt)
            await self.db.commit()
        else:
            # 如果没有enabled_flag字段，执行硬删除
            await self.delete_crud(ids)

    async def get_list_with_operator(
        self,
        conditions: list = None,
        order_by: list = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list, int]:
        """获取列表并关联操作人登录名，将 COUNT + 数据 + 用户名合并为单次 SQL 执行。

        使用窗口函数 COUNT(*) OVER() 获取总数，LEFT JOIN sys_user 获取操作人 username，
        将原 3 次串行查询合并为 1 次，降低网络往返延迟。

        Args:
            conditions: 查询条件列表
            order_by:   排序条件列表
            skip:       跳过记录数（分页偏移）
            limit:      返回记录数上限
        Returns:
            tuple[list[Row], int]: (行结果列表, 总数)
                每个 Row 包含模型实例及 operator_name（操作人登录名）字段
        """
        from app.api.v1.system.user.model import UserModel

        count_col = func.count().over().label('total')
        operator_col = UserModel.username.label('operator_name')

        stmt = (
            select(self.model, count_col, operator_col)
            .outerjoin(
                UserModel,
                UserModel.id == func.coalesce(self.model.updated_by, self.model.created_by),
            )
        )
        if conditions:
            stmt = stmt.where(and_(*conditions))
        if order_by:
            for o in order_by:
                stmt = stmt.order_by(o)
        stmt = stmt.offset(skip).limit(limit)

        rows = (await self.db.execute(stmt)).all()
        total = rows[0].total if rows else 0
        return rows, total

    async def get_options_crud(
        self,
        name_field: str = "name",
        conditions: list = None,
        order_by: list = None,
    ) -> list[dict[str, Any]]:
        """
        查询下拉选项，仅 SELECT id 和指定名称列，返回 [{id, name}] 列表。
        适用于所有需要"ID + 显示名"下拉的场景，避免各 Service 重复写轻量查询。

        Args:
            name_field: 作为 name 的列名，默认 "name"（如文件用 "file_name"、用户用 "username"）
            conditions: WHERE 条件列表，默认不过滤
            order_by:   排序列表，默认不排序
        Returns:
            [{"id": ..., "name": ...}, ...]
        """
        name_col = getattr(self.model, name_field)
        stmt = select(self.model.id, name_col)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        if order_by:
            for o in order_by:
                stmt = stmt.order_by(o)
        result = await self.db.execute(stmt)
        return [{"id": row[0], "name": row[1]} for row in result.all()]
