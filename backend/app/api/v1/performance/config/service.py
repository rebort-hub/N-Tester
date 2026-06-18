#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_
from fastapi import HTTPException, status

from app.core.base_crud import BaseCRUD
from app.api.v1.performance.config.crud import _prepare_ssh_password
from .model import PerfConfigMachineModel, PerfConfigParamModel
from .schema import (
    PerfMachineCreateSchema, PerfMachineUpdateSchema, PerfMachineRespSchema,
    PerfParamCreateSchema, PerfParamUpdateSchema, PerfParamRespSchema,
)

"""
性能测试 - 配置管理 Service
提供压力机配置、性能参数配置的增删改查业务逻辑。
"""
# ==================== 压力机配置 ====================

class PerfConfigMachineService:
    """压力机配置 Service，负责压力机资源的业务逻辑处理。"""

    @staticmethod
    async def create(db: AsyncSession, data: PerfMachineCreateSchema, user_id: int) -> Dict:
        """创建压力机配置。
        Args:
            db:      数据库异步会话
            data:    压力机创建参数
            user_id: 当前操作人 ID
        Returns:
            Dict: 新建压力机的ID字段
        """
        crud = BaseCRUD(PerfConfigMachineModel, db)
        # 名称去重：同名且未删除的记录不允许重复新建
        existing, _ = await crud.get_list_crud(conditions=[
            PerfConfigMachineModel.enabled_flag == 1,
            PerfConfigMachineModel.name == data.name,
        ])
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='压力机名称已存在')
        create_data = data.model_dump()
        create_data['ssh_password'] = _prepare_ssh_password(create_data.get('ssh_password'))
        obj_create = await crud.create_crud({**create_data, 'created_by': user_id})
        return {'id': obj_create.id}

    @staticmethod
    async def get_list(db: AsyncSession, page: int, page_size: int, status_filter: Optional[int] = None,
                       name: Optional[str] = None,) -> Dict:
        """分页查询压力机列表。
        Args:
            db:        数据库异步会话
            page:      页码，从 1 开始
            page_size: 每页条数
            status_filter: 状态筛选，1-启用 0-禁用，None 表示不筛选
            name:      名称关键字，模糊匹配，None 表示不筛选
        Returns:
            Dict: 包含 items（列表）、total（总数）、page、page_size 的分页结果
        """
        crud = BaseCRUD(PerfConfigMachineModel, db)
        conditions = [PerfConfigMachineModel.enabled_flag == 1]
        # 新增查询条件：状态
        if status_filter is not None:
            conditions.append(PerfConfigMachineModel.status == status_filter)
        # 新增查询条件：名称
        if name:
            conditions.append(PerfConfigMachineModel.name.like(f'%{name}%'))
        # 通过BaseCRUD的get_list_with_operator方法，提高查询效率
        rows, total = await crud.get_list_with_operator(
            conditions=conditions, order_by=[PerfConfigMachineModel.id.desc()],
            skip=(page - 1) * page_size, limit=page_size,
        )

        resp_items = []
        for row in rows:
            item_dict = PerfMachineRespSchema.model_validate(row[0]).model_dump()
            item_dict['operator_name'] = row.operator_name
            resp_items.append(item_dict)

        return {
            'items': resp_items,
            'total': total, 'page': page, 'page_size': page_size,
        }

    @staticmethod
    async def get_detail(db: AsyncSession, machine_id: int) -> Dict:
        """查询单条压力机配置详情。
        Args:
            db:         数据库异步会话
            machine_id: 压力机配置数据 ID
        Returns:
            Dict: 压力机详情字段
        Raises:
            HTTPException 404: 压力机不存在或已被删除
        """
        obj_query = await BaseCRUD(PerfConfigMachineModel, db).get_by_id_crud(machine_id)
        if not obj_query or not obj_query.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='压力机配置数据不存在！')
        return PerfMachineRespSchema.model_validate(obj_query).model_dump()

    @staticmethod
    async def update(db: AsyncSession, machine_id: int, data: PerfMachineUpdateSchema, user_id: int) -> None:
        """更新压力机配置信息。
        Args:
            db:         数据库异步会话
            machine_id: 压力机配置数据 ID
            data:       待更新字段（仅传入有变化的字段）
            user_id:    当前操作人 ID
        Returns:
            None
        Raises:
            HTTPException 404: 压力机不存在或已被删除
        """
        crud = BaseCRUD(PerfConfigMachineModel, db)
        obj_query = await crud.get_by_id_crud(machine_id)
        if not obj_query or not obj_query.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='压力机配置数据不存在')
        # 名称去重：修改时若传入了 name，检查是否与其他记录重名
        if data.name:
            existing, _ = await crud.get_list_crud(conditions=[
                PerfConfigMachineModel.enabled_flag == 1,
                PerfConfigMachineModel.name == data.name,
                PerfConfigMachineModel.id != machine_id,
            ])
            if existing:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='压力机名称已存在')
        update_data = data.model_dump(exclude_unset=True)
        # ssh_password 单独处理：None=不更新保留原值，''=清空，其他=RSA解密+Fernet加密或token原样
        if 'ssh_password' in update_data:
            update_data['ssh_password'] = _prepare_ssh_password(
                update_data['ssh_password'], obj_query.ssh_password
            )
        await crud.update_crud(machine_id, {**update_data, 'updated_by': user_id})

    @staticmethod
    async def delete(db: AsyncSession, machine_id: int) -> None:
        """软删除压力机配置（将 enabled_flag 置为 0）。
        Args:
            db:         数据库异步会话
            machine_id: 压力机配置数据 ID
        Raises:
            HTTPException 404: 压力机不存在或已被删除
        """
        obj_query = await BaseCRUD(PerfConfigMachineModel, db).get_by_id_crud(machine_id)
        if not obj_query or not obj_query.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='压力机配置数据不存在')
        await BaseCRUD(PerfConfigMachineModel, db).soft_delete_crud([machine_id])


# ================================参数配置 =======================================

class PerfConfigParamService:
    """性能参数配置 Service，负责性能参数资源的业务逻辑处理。"""

    @staticmethod
    async def create(db: AsyncSession, data: PerfParamCreateSchema, user_id: int) -> Dict:
        """创建性能参数。
        Args:
            db:      数据库异步会话
            data:    参数创建参数
            user_id: 当前操作人 ID
        Returns:
            Dict: 新建参数配置的ID字段
        """
        crud = BaseCRUD(PerfConfigParamModel, db)
        # 参数名去重：同 param_key 且未删除的记录不允许重复新建
        existing, _ = await crud.get_list_crud(conditions=[
            PerfConfigParamModel.enabled_flag == 1,
            PerfConfigParamModel.param_key == data.param_key,
        ])
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='参数名已存在')
        obj_create = await crud.create_crud({**data.model_dump(), 'created_by': user_id})
        return {'id': obj_create.id}

    @staticmethod
    async def get_list(db: AsyncSession, page: int, page_size: int, status_filter: Optional[int] = None,
                       name: Optional[str] = None,) -> Dict:
        """分页查询性能参数列表。
        Args:
            db:        数据库异步会话
            page:      页码，从 1 开始
            page_size: 每页条数
            status_filter: 状态筛选，1-启用 0-禁用，None 表示不筛选
            name:      名称关键字，模糊匹配，None 表示不筛选
        Returns:
            Dict: 包含 items（列表）、total（总数）、page、page_size 的分页结果
        """
        crud = BaseCRUD(PerfConfigParamModel, db)
        conditions = [PerfConfigParamModel.enabled_flag == 1]
        # 查询条件：支持通过状态查询
        if status_filter is not None:
            conditions.append(PerfConfigParamModel.status == status_filter)
        # 查询条件：支持通过参数名称或参数名查询
        if name:
            conditions.append(or_(
                PerfConfigParamModel.name.like(f'%{name}%'),
                PerfConfigParamModel.param_key.like(f'%{name}%'),
            ))
        # 使用get_list_with_operator方法，多场景联合查询
        rows, total = await crud.get_list_with_operator(
            conditions=conditions, order_by=[PerfConfigParamModel.id.asc()],
            skip=(page - 1) * page_size, limit=page_size,
        )

        resp_items = []
        for row in rows:
            item_dict = PerfParamRespSchema.model_validate(row[0]).model_dump()
            item_dict['operator_name'] = row.operator_name or ('System' if row[0].is_system else None)
            resp_items.append(item_dict)

        return {
            'items': resp_items,
            'total': total, 'page': page, 'page_size': page_size,
        }

    @staticmethod
    async def get_detail(db: AsyncSession, param_id: int) -> Dict:
        """查询单条性能参数详情。
        Args:
            db:       数据库异步会话
            param_id: 参数 ID
        Returns:
            Dict: 参数详情字段
        Raises:
            HTTPException 404: 参数不存在或已被删除
        """
        obj_query = await BaseCRUD(PerfConfigParamModel, db).get_by_id_crud(param_id)
        if not obj_query or not obj_query.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='参数不存在')
        return PerfParamRespSchema.model_validate(obj_query).model_dump()

    @staticmethod
    async def update(db: AsyncSession, param_id: int, data: PerfParamUpdateSchema, user_id: int) -> None:
        """更新性能参数信息。
        Args:
            db:       数据库异步会话
            param_id: 参数 ID
            data:     待更新字段（仅传入有变化的字段）
            user_id:  当前操作人 ID
        Returns:
            None
        Raises:
            HTTPException 404: 参数不存在或已被删除
        """
        crud = BaseCRUD(PerfConfigParamModel, db)
        obj_query = await crud.get_by_id_crud(param_id)
        if not obj_query or not obj_query.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='参数配置数据不存在')
        update_data = data.model_dump(exclude_unset=True)
        # 系统参数不允许修改 status
        if obj_query.is_system:
            update_data.pop('status', None)
        await crud.update_crud(param_id, {**update_data, 'updated_by': user_id})

    @staticmethod
    async def delete(db: AsyncSession, param_id: int) -> None:
        """软删除性能参数（将 enabled_flag 置为 0）。
        Args:
            db:       数据库异步会话
            param_id: 参数 ID
        Raises:
            HTTPException 404: 参数不存在或已被删除
        """
        obj_query = await BaseCRUD(PerfConfigParamModel, db).get_by_id_crud(param_id)
        if not obj_query or not obj_query.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='参数配置数据不存在')
        if obj_query.is_system:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='系统参数不可删除')
        await BaseCRUD(PerfConfigParamModel, db).soft_delete_crud([param_id])