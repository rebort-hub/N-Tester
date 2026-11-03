#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.api.v1.system.menu.service import MenuService
from app.api.v1.system.menu.schema import (
    MenuCreateSchema,
    MenuUpdateSchema,
    MenuOutSchema
)
from app.common.response import success_response

router = APIRouter()


@router.get("", summary="获取菜单列表（根路径）")
async def get_menus(
    db: AsyncSession = Depends(get_db)
):
    """
    获取菜单列表（用于前端菜单管理页面）
    返回树形结构
    """
    # MenuService已经返回success_response格式，直接返回
    return await MenuService.get_menu_tree_service(db)


@router.get("/list/all", summary="获取菜单列表")
async def get_menu_list(
    db: AsyncSession = Depends(get_db)
):
    """获取菜单列表（扁平列表）"""
    return await MenuService.get_menu_list_service(db)


@router.get("/tree", summary="获取菜单树（前端使用）")
async def get_menu_tree_frontend(
    db: AsyncSession = Depends(get_db)
):
    """获取菜单树形结构（前端角色管理使用）"""
    return await MenuService.get_menu_tree_service(db)


@router.get("/tree/all", summary="获取菜单树（完整路径）")
async def get_menu_tree(
    db: AsyncSession = Depends(get_db)
):
    """获取菜单树形结构"""
    return await MenuService.get_menu_tree_service(db)


@router.get("/routes/user", summary="获取用户菜单路由")
async def get_user_routes(
    menu_ids: Optional[List[int]] = Query(None, description="菜单ID列表"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户菜单路由（前端使用）
    如果不传menu_ids，则返回所有菜单
    """
    return await MenuService.get_menu_routes_service(menu_ids, db)


@router.get("/{menu_id}", summary="获取菜单详情")
async def get_menu_detail(
    menu_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取菜单详情"""
    result = await MenuService.get_menu_detail_service(menu_id, db)
    return success_response(data=result.model_dump())


@router.post("", summary="创建菜单")
async def create_menu(
    data: MenuCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建菜单"""
    result = await MenuService.create_menu_service(data, current_user_id, db)
    return success_response(data=result.model_dump(), message="创建成功")


@router.put("/{menu_id}", summary="更新菜单")
async def update_menu(
    menu_id: int,
    data: MenuUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新菜单"""
    result = await MenuService.update_menu_service(menu_id, data, current_user_id, db)
    return success_response(data=result.model_dump(), message="更新成功")


@router.delete("/{menu_id}", summary="删除单个菜单")
async def delete_single_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除单个菜单"""
    await MenuService.delete_menu_service([menu_id], db)
    return success_response(message="删除成功")


@router.delete("", summary="批量删除菜单")
async def delete_menus(
    ids: List[int] = Query(..., description="菜单ID列表"),
    db: AsyncSession = Depends(get_db)
):
    """批量删除菜单"""
    await MenuService.delete_menu_service(ids, db)
    return success_response(message="删除成功")
