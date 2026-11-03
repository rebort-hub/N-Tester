#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.api.v1.system.role.service import RoleService
from app.api.v1.system.role.schema import (
    RoleCreateSchema,
    RoleUpdateSchema,
    RoleOutSchema,
    RoleQuerySchema
)
from app.common.response import success_response

router = APIRouter()


@router.get("/{role_id}", summary="获取角色详情")
async def get_role_detail(
    role_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取角色详情"""
    result = await RoleService.get_role_detail_service(role_id, db)
    return success_response(data=result.model_dump())


@router.get("", summary="获取角色列表")
async def get_role_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    role_name: str = Query(None, description="角色名称"),
    role_key: str = Query(None, description="角色权限字符串"),
    status: int = Query(None, ge=0, le=1, description="角色状态"),
    begin_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    db: AsyncSession = Depends(get_db)
):
    """获取角色列表"""
    query = RoleQuerySchema(
        page=page,
        page_size=page_size,
        role_name=role_name,
        role_key=role_key,
        status=status,
        begin_time=begin_time,
        end_time=end_time
    )
    return await RoleService.get_role_list_service(query, db)


@router.post("", summary="创建角色")
async def create_role(
    data: RoleCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建角色"""
    result = await RoleService.create_role_service(data, current_user_id, db)
    return success_response(data=result.model_dump(), message="创建成功")


@router.put("/{role_id}", summary="更新角色")
async def update_role(
    role_id: int,
    data: RoleUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新角色"""
    result = await RoleService.update_role_service(role_id, data, current_user_id, db)
    return success_response(data=result.model_dump(), message="更新成功")


@router.delete("/{role_id}", summary="删除单个角色")
async def delete_single_role(
    role_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除单个角色"""
    await RoleService.delete_role_service([role_id], db)
    return success_response(message="删除成功")


@router.delete("", summary="批量删除角色")
async def delete_role(
    ids: List[int] = Query(..., description="角色ID列表"),
    db: AsyncSession = Depends(get_db)
):
    """批量删除角色"""
    await RoleService.delete_role_service(ids, db)
    return success_response(message="删除成功")
