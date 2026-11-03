#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.v1.common.health.service import HealthService
from app.common.response import success_response

router = APIRouter()


@router.get("", summary="健康检查")
async def health_check():
    """基础健康检查"""
    result = await HealthService.basic_health_check_service()
    return success_response(data=result, message="系统正常")


@router.get("/database", summary="数据库健康检查")
async def database_health_check(
    db: AsyncSession = Depends(get_db)
):
    """数据库健康检查"""
    result = await HealthService.database_health_check_service(db)
    return success_response(data=result, message="数据库连接正常")


@router.get("/system", summary="系统信息")
async def system_info():
    """获取系统信息"""
    result = await HealthService.get_system_info_service()
    return success_response(data=result, message="查询成功")
