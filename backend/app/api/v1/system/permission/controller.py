#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.api.v1.system.permission.service import PermissionService
from app.api.v1.system.permission.schema import (
    PermissionCreateSchema,
    PermissionUpdateSchema,
    PermissionQuerySchema
)
from app.common.response import success_response

router = APIRouter()


@router.get("/{permission_id}", summary="获取权限详情")
async def get_permission_detail(
    permission_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取权限详情"""
    result = await PermissionService.get_permission_detail_service(permission_id, db)
    return success_response(data=result.model_dump())


@router.get("/list/all", summary="获取权限列表")
async def get_permission_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    permission_name: str = Query("", description="权限名称"),
    permission_code: str = Query("", description="权限编码"),
    permission_type: str = Query("", description="权限类型"),
    status: str = Query("", description="状态"),
    db: AsyncSession = Depends(get_db)
):
    """获取权限列表"""
    # 处理参数，将空字符串转换为None
    permission_type_int = None
    if permission_type and permission_type.strip():
        try:
            permission_type_int = int(permission_type)
        except ValueError:
            permission_type_int = None
    
    status_int = None
    if status and status.strip():
        try:
            status_int = int(status)
        except ValueError:
            status_int = None
    
    query = PermissionQuerySchema(
        page=page,
        page_size=page_size,
        permission_name=permission_name if permission_name.strip() else None,
        permission_code=permission_code if permission_code.strip() else None,
        permission_type=permission_type_int,
        status=status_int
    )
    return await PermissionService.get_permission_list_service(query, db)


@router.get("/all/enabled", summary="获取所有启用的权限")
async def get_all_permissions(
    db: AsyncSession = Depends(get_db)
):
    """获取所有启用的权限（用于分配）"""
    return await PermissionService.get_all_permissions_service(db)


@router.post("", summary="创建权限")
async def create_permission(
    data: PermissionCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建权限"""
    result = await PermissionService.create_permission_service(data, current_user_id, db)
    return success_response(data=result.model_dump(), message="创建成功")


@router.put("/{permission_id}", summary="更新权限")
async def update_permission(
    permission_id: int,
    data: PermissionUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新权限"""
    result = await PermissionService.update_permission_service(permission_id, data, current_user_id, db)
    return success_response(data=result.model_dump(), message="更新成功")


@router.delete("", summary="删除权限")
async def delete_permission(
    ids: List[int] = Query(..., description="权限ID列表"),
    db: AsyncSession = Depends(get_db)
):
    """删除权限"""
    await PermissionService.delete_permission_service(ids, db)
    return success_response(message="删除成功")
