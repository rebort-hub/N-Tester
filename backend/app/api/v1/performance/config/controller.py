#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.sqlalchemy import get_db
from app.common.response import success_response
from app.core.dependencies import get_current_user_id
from .schema import (
    PerfMachineCreateSchema, PerfMachineUpdateSchema,
    PerfParamCreateSchema, PerfParamUpdateSchema,
)
from .service import PerfConfigMachineService, PerfConfigParamService
from .crud import PerfParamCRUD

router = APIRouter(prefix="/performance/config", tags=["性能测试 - 配置管理"])

"""
性能测试 - 配置管理 Controller
提供压力机配置、性能参数配置的 RESTful API 路由入口。
"""
# ==================== 压力机配置 ====================

@router.post("/machines/add", summary="新增压力机配置")
async def create_machine(data: PerfMachineCreateSchema, db: AsyncSession = Depends(get_db),
                         user_id: int = Depends(get_current_user_id),):
    """创建压力机配置接口。
    Args:
        data:    压力机创建参数（请求体）
        db:      数据库会话（依赖注入）
        user_id: 当前登录用户 ID（依赖注入）
    Returns:
        统一响应体，data 为新建压力机的 ID
    """
    result = await PerfConfigMachineService.create(db, data, user_id)
    return success_response(data=result, message="新建成功")


@router.get("/machines/list", summary="获取压力机配置列表")
async def list_machines(
    name: Optional[str] = Query(None, description="压力机名称"),
    status: Optional[int] = Query(None, description="状态筛选：1启用 0禁用"),
    page:      int           = Query(1,    ge=1,         description="页码"),
    page_size: int           = Query(20,   ge=1, le=50, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """分页查询压力机配置列表，支持按状态和名称筛选。
    Args:
        page:      页码，默认 1
        page_size: 每页数量，默认 20，最大 200
        status:    状态筛选，1-启用 0-禁用，不传则返回全部
        name:      名称关键字，模糊匹配，不传则不过滤
        db:        数据库会话（依赖注入）
        user_id:   当前登录用户 ID（依赖注入）
    Returns:
        统一响应体，data 包含 items、total、page、page_size
    """
    result = await PerfConfigMachineService.get_list(db, page, page_size, status, name)
    return success_response(data=result)


@router.put("/machines/update/{machine_id}", summary="更新压力机配置")
async def update_machine(
    machine_id: int,
    data: PerfMachineUpdateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """更新压力机配置信息（仅传入需要修改的字段）。
    Args:
        machine_id: 压力机 ID（路径参数）
        data:       待更新字段（请求体）
        db:         数据库会话（依赖注入）
        user_id:    当前登录用户 ID（依赖注入）
    Returns:
        统一响应体，message 为更新成功提示
    """
    await PerfConfigMachineService.update(db, machine_id, data, user_id)
    return success_response(data=[], message="更新成功")


@router.delete("/machines/delete/{machine_id}", summary="删除压力机配置")
async def delete_machine(
    machine_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """软删除压力机（逻辑删除，数据仍保留在库中）。
    Args:
        machine_id: 压力机 ID（路径参数）
        db:         数据库会话（依赖注入）
        user_id:    当前登录用户 ID（依赖注入）
    Returns:
        统一响应体，message 为删除成功提示
    """
    await PerfConfigMachineService.delete(db, machine_id)
    return success_response(data=[], message="删除成功")


# =========================== 参数配置 =============================
@router.post("/params/add", summary="新增参数配置")
async def create_param(
    data: PerfParamCreateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """新增一条性能参数配置记录。
    Args:
        data:    参数创建参数（请求体）
        db:      数据库会话（依赖注入）
        user_id: 当前登录用户 ID（依赖注入）
    Returns:
        统一响应体，data 为新建参数的 ID
    """
    result = await PerfConfigParamService.create(db, data, user_id)
    return success_response(data=result, message="新建成功")


@router.get("/params/list", summary="获取参数配置列表")
async def list_params(
    name: Optional[str] = Query(None, description="参数名称/参数名"),
    status: Optional[int] = Query(None, description="状态筛选：1启用 0禁用"),
    page:      int           = Query(1,    ge=1,         description="页码"),
    page_size: int           = Query(20,   ge=1, le=200, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """分页查询性能参数列表，支持按状态和名称筛选。
    Args:
        page:      页码，默认 1
        page_size: 每页数量，默认 20，最大 200
        status:    状态筛选，1-启用 0-禁用，不传则返回全部
        name:      名称关键字，模糊匹配，不传则不过滤
        db:        数据库会话（依赖注入）
        user_id:   当前登录用户 ID（依赖注入）
    Returns:
        统一响应体，data 包含 items、total、page、page_size
    """
    result = await PerfConfigParamService.get_list(db, page, page_size, status, name)
    return success_response(data=result)


@router.put("/params/update/{param_id}", summary="更新参数配置")
async def update_param(
    param_id: int,
    data: PerfParamUpdateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """更新性能参数配置信息（仅传入需要修改的字段）。
    Args:
        param_id: 参数 ID（路径参数）
        data:     待更新字段（请求体）
        db:       数据库会话（依赖注入）
        user_id:  当前登录用户 ID（依赖注入）
    Returns:
        统一响应体，message 为更新成功提示
    """
    await PerfConfigParamService.update(db, param_id, data, user_id)
    return success_response(data=[], message="更新成功")


@router.delete("/params/delete/{param_id}", summary="删除参数配置")
async def delete_param(
    param_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """软删除性能参数（逻辑删除，数据仍保留在库中）。
    Args:
        param_id: 参数 ID（路径参数）
        db:       数据库会话（依赖注入）
        user_id:  当前登录用户 ID（依赖注入）
    Returns:
        统一响应体，message 为删除成功提示
    """
    await PerfConfigParamService.delete(db, param_id)
    return success_response(data=[], message="删除成功")