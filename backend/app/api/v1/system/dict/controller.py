#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.api.v1.system.dict.service import DictTypeService, DictDataService
from app.api.v1.system.dict.schema import (
    DictTypeCreateSchema,
    DictTypeUpdateSchema,
    DictTypeQuerySchema,
    DictDataCreateSchema,
    DictDataUpdateSchema,
    DictDataQuerySchema
)
from app.common.response import success_response

router = APIRouter()


# ==================== 通用接口 ====================

@router.get("", summary="获取所有字典类型（简化版）")
async def get_all_dict_types(
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有字典类型（用于前端缓存）
    返回简化的字典类型列表
    """
    query = DictTypeQuerySchema(page=1, page_size=100)
    result = await DictTypeService.get_dict_type_list_service(query, db)
    return result


# ==================== 字典类型接口 ====================

@router.get("/type/{dict_type_id}", summary="获取字典类型详情")
async def get_dict_type_detail(
    dict_type_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取字典类型详情"""
    result = await DictTypeService.get_dict_type_detail_service(dict_type_id, db)
    return success_response(data=result.model_dump())


@router.get("/type/list/all", summary="获取字典类型列表")
async def get_dict_type_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    dict_name: str = Query(None, description="字典名称"),
    dict_type: str = Query(None, description="字典类型"),
    status: int = Query(None, ge=0, le=1, description="状态"),
    begin_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    db: AsyncSession = Depends(get_db)
):
    """获取字典类型列表"""
    query = DictTypeQuerySchema(
        page=page,
        page_size=page_size,
        dict_name=dict_name,
        dict_type=dict_type,
        status=status,
        begin_time=begin_time,
        end_time=end_time
    )
    return await DictTypeService.get_dict_type_list_service(query, db)


@router.post("/type", summary="创建字典类型")
async def create_dict_type(
    data: DictTypeCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建字典类型"""
    result = await DictTypeService.create_dict_type_service(data, current_user_id, db)
    return success_response(data=result.model_dump(), message="创建成功")


@router.put("/type/{dict_type_id}", summary="更新字典类型")
async def update_dict_type(
    dict_type_id: int,
    data: DictTypeUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新字典类型"""
    result = await DictTypeService.update_dict_type_service(dict_type_id, data, current_user_id, db)
    return success_response(data=result.model_dump(), message="更新成功")


@router.delete("/type", summary="删除字典类型（批量）")
async def delete_dict_type(
    ids: List[int] = Query(..., description="字典类型ID列表"),
    db: AsyncSession = Depends(get_db)
):
    """删除字典类型（批量）"""
    await DictTypeService.delete_dict_type_service(ids, db)
    return success_response(message="删除成功")


@router.delete("/type/{dict_type_id}", summary="删除字典类型（单个）")
async def delete_dict_type_by_id(
    dict_type_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除字典类型（单个）"""
    await DictTypeService.delete_dict_type_service([dict_type_id], db)
    return success_response(message="删除成功")


# ==================== 字典数据接口 ====================

@router.get("/data/{dict_data_id}", summary="获取字典数据详情")
async def get_dict_data_detail(
    dict_data_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取字典数据详情"""
    result = await DictDataService.get_dict_data_detail_service(dict_data_id, db)
    return success_response(data=result.model_dump())


@router.get("/data/list/all", summary="获取字典数据列表")
async def get_dict_data_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=1000, description="每页数量"),
    dict_label: str = Query(None, description="字典标签"),
    dict_type: str = Query(None, description="字典类型"),
    status: int = Query(None, ge=0, le=1, description="状态"),
    db: AsyncSession = Depends(get_db)
):
    """获取字典数据列表"""
    query = DictDataQuerySchema(
        page=page,
        page_size=page_size,
        dict_label=dict_label,
        dict_type=dict_type,
        status=status
    )
    return await DictDataService.get_dict_data_list_service(query, db)


@router.get("/data/type/{dict_type}", summary="根据字典类型获取数据")
async def get_dict_data_by_type(
    dict_type: str,
    db: AsyncSession = Depends(get_db)
):
    """根据字典类型获取数据（前端使用）"""
    return await DictDataService.get_dict_data_by_type_service(dict_type, db)


@router.post("/data", summary="创建字典数据")
async def create_dict_data(
    data: DictDataCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建字典数据"""
    result = await DictDataService.create_dict_data_service(data, current_user_id, db)
    return success_response(data=result.model_dump(), message="创建成功")


@router.put("/data/{dict_data_id}", summary="更新字典数据")
async def update_dict_data(
    dict_data_id: int,
    data: DictDataUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新字典数据"""
    result = await DictDataService.update_dict_data_service(dict_data_id, data, current_user_id, db)
    return success_response(data=result.model_dump(), message="更新成功")


@router.delete("/data", summary="删除字典数据（批量）")
async def delete_dict_data(
    ids: List[int] = Query(..., description="字典数据ID列表"),
    db: AsyncSession = Depends(get_db)
):
    """删除字典数据（批量）"""
    await DictDataService.delete_dict_data_service(ids, db)
    return success_response(message="删除成功")


@router.delete("/data/{dict_data_id}", summary="删除字典数据（单个）")
async def delete_dict_data_by_id(
    dict_data_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除字典数据（单个）"""
    await DictDataService.delete_dict_data_service([dict_data_id], db)
    return success_response(message="删除成功")
