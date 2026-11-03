#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.api.v1.system.dept.service import DeptService
from app.api.v1.system.dept.schema import (
    DeptCreateSchema,
    DeptUpdateSchema,
    DeptOutSchema
)
from app.common.response import success_response

router = APIRouter()


@router.get("", summary="获取部门树（根路径）")
async def get_depts(
    db: AsyncSession = Depends(get_db)
):
    """
    获取部门树（用于前端部门管理页面）
    返回树形结构
    """
    return await DeptService.get_dept_tree_service(db)


@router.get("/{dept_id}", summary="获取部门详情")
async def get_dept_detail(
    dept_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取部门详情"""
    result = await DeptService.get_dept_detail_service(dept_id, db)
    return success_response(data=result.model_dump())


@router.get("/list/all", summary="获取部门列表")
async def get_dept_list(
    db: AsyncSession = Depends(get_db)
):
    """获取部门列表（扁平列表）"""
    return await DeptService.get_dept_list_service(db)


@router.get("/tree/all", summary="获取部门树")
async def get_dept_tree(
    db: AsyncSession = Depends(get_db)
):
    """获取部门树形结构"""
    return await DeptService.get_dept_tree_service(db)


@router.post("", summary="创建部门")
async def create_dept(
    data: DeptCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建部门"""
    result = await DeptService.create_dept_service(data, current_user_id, db)
    return success_response(data=result.model_dump(), message="创建成功")


@router.put("/{dept_id}", summary="更新部门")
async def update_dept(
    dept_id: int,
    data: DeptUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新部门"""
    result = await DeptService.update_dept_service(dept_id, data, current_user_id, db)
    return success_response(data=result.model_dump(), message="更新成功")


@router.delete("", summary="删除部门（批量）")
async def delete_dept(
    ids: List[int] = Query(..., description="部门ID列表"),
    db: AsyncSession = Depends(get_db)
):
    """删除部门（批量）"""
    await DeptService.delete_dept_service(ids, db)
    return success_response(message="删除成功")


@router.delete("/{dept_id}", summary="删除部门（单个）")
async def delete_dept_by_id(
    dept_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除部门（单个）"""
    await DeptService.delete_dept_service([dept_id], db)
    return success_response(message="删除成功")
