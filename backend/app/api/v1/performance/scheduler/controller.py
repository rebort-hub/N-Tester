#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import success_response
from app.core.dependencies import get_current_user_id
from app.db.sqlalchemy import get_db
from .schema import (
    PerfSchedulerCancelReqSchema,
    PerfSchedulerCreateReqSchema,
    PerfSchedulerUpdateReqSchema,
)
from .service import PerfSchedulerService

router = APIRouter(prefix="/performance/schedulers", tags=["性能测试 - 定时任务"])
"""
=========================================================================
性能测试 - 定时任务 Controller

API 路由：
  GET    /list      分页查询定时任务列表
  POST   /add       新建定时任务
  PUT    /update    修改定时任务（仅 待触发/已取消 状态允许）
  DELETE /delete    删除定时任务（仅 待触发/已取消 状态允许）
  PUT    /cancel    取消定时任务（仅 进行中 状态允许）
=========================================================================
"""


@router.get("/list", summary="定时任务列表")
async def list_schedulers(
    name:        Optional[str] = Query(None, description="任务名称，模糊匹配"),
    task_status: Optional[int] = Query(None, description="任务状态：0-待触发 1-进行中 2-已结束 3-已取消"),
    is_active:   Optional[int] = Query(None, description="启用状态：1-启用 0-禁用"),
    page:        int           = Query(1,    ge=1,         description="页码"),
    page_size:   int           = Query(20,   ge=1, le=100, description="每页数量"),
    db:          AsyncSession  = Depends(get_db),
    user_id:     int           = Depends(get_current_user_id),
):
    """
    分页查询定时任务列表。
    支持按 name/task_status/is_active 组合过滤，联查场景编号、脚本名称和操作人名称。
    """
    result = await PerfSchedulerService(db).get_list(page, page_size, name, task_status, is_active)
    return success_response(data=result)

@router.post("/add", summary="新建定时任务")
async def add_scheduler(
    data:    PerfSchedulerCreateReqSchema,
    db:      AsyncSession = Depends(get_db),
    user_id: int          = Depends(get_current_user_id),
):
    result = await PerfSchedulerService(db).create(data, user_id)
    return success_response(data=result, message="创建成功")


@router.put("/update", summary="修改定时任务（仅待触发/已取消状态允许）")
async def update_scheduler(
    data:    PerfSchedulerUpdateReqSchema,
    db:      AsyncSession = Depends(get_db),
    user_id: int          = Depends(get_current_user_id),
):
    """id 放请求体；后端校验 task_status in (0, 3) 才允许修改。"""
    await PerfSchedulerService(db).update(data, user_id)
    return success_response(data=[], message="修改成功")


@router.delete("/delete", summary="删除定时任务（仅待触发/已取消状态允许）")
async def delete_scheduler(
    id:      int          = Query(..., gt=0, description="任务主键ID"),
    db:      AsyncSession = Depends(get_db),
    user_id: int          = Depends(get_current_user_id),
):
    """id 放查询参数；后端校验 task_status in (0, 3) 才允许删除。"""
    await PerfSchedulerService(db).delete(id)
    return success_response(data=[], message="删除成功")


@router.put("/cancel", summary="取消定时任务（仅进行中状态允许）")
async def cancel_scheduler(
    data:    PerfSchedulerCancelReqSchema,
    db:      AsyncSession = Depends(get_db),
    user_id: int          = Depends(get_current_user_id),
):
    """id 放请求体；后端校验 task_status == 1 才允许取消，将状态置为 已取消(3)。"""
    await PerfSchedulerService(db).cancel(data.id, user_id)
    return success_response(data=[], message="已取消")