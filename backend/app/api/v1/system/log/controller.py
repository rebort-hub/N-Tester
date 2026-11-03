#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.v1.system.log.service import OperationLogService, LoginLogService
from app.api.v1.system.log.schema import (
    OperationLogQuerySchema,
    LoginLogQuerySchema,
    LogBatchDeleteSchema
)
from app.common.response import success_response

router = APIRouter()


# 操作日志相关接口
@router.get("/operation", summary="获取操作日志列表")
async def get_operation_log_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    username: str = Query(None, description="用户名"),
    operation: str = Query(None, description="操作类型"),
    method: str = Query(None, description="请求方法"),
    module: str = Query(None, description="操作模块"),
    status: int = Query(None, ge=0, le=1, description="操作状态"),
    ip: str = Query(None, description="操作IP"),
    begin_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    db: AsyncSession = Depends(get_db)
):
    """获取操作日志列表"""
    query = OperationLogQuerySchema(
        page=page,
        page_size=page_size,
        username=username,
        operation=operation,
        method=method,
        module=module,
        status=status,
        ip=ip,
        begin_time=begin_time,
        end_time=end_time
    )
    return await OperationLogService.get_operation_log_list(query, db)


@router.get("/operation/{log_id}", summary="获取操作日志详情")
async def get_operation_log_detail(
    log_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取操作日志详情"""
    result = await OperationLogService.get_operation_log_detail(log_id, db)
    return success_response(data=result.model_dump())


@router.delete("/operation", summary="批量删除操作日志")
async def delete_operation_logs(
    data: LogBatchDeleteSchema,
    db: AsyncSession = Depends(get_db)
):
    """批量删除操作日志"""
    await OperationLogService.delete_operation_logs(data, db)
    return success_response(message="删除成功")


@router.delete("/operation/clean", summary="清理旧的操作日志")
async def clean_old_operation_logs(
    days: int = Query(30, ge=1, description="保留天数"),
    db: AsyncSession = Depends(get_db)
):
    """清理旧的操作日志"""
    count = await OperationLogService.clean_old_operation_logs(days, db)
    return success_response(data={"deleted_count": count}, message=f"清理完成，删除了 {count} 条记录")


@router.get("/operation/statistics", summary="获取操作日志统计")
async def get_operation_log_statistics(
    db: AsyncSession = Depends(get_db)
):
    """获取操作日志统计"""
    result = await OperationLogService.get_operation_log_statistics(db)
    return success_response(data=result)


# 登录日志相关接口
@router.get("/login", summary="获取登录日志列表")
async def get_login_log_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    username: str = Query(None, description="用户名"),
    login_type: str = Query(None, description="登录类型"),
    status: int = Query(None, ge=0, le=1, description="登录状态"),
    ip: str = Query(None, description="登录IP"),
    begin_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    db: AsyncSession = Depends(get_db)
):
    """获取登录日志列表"""
    query = LoginLogQuerySchema(
        page=page,
        page_size=page_size,
        username=username,
        login_type=login_type,
        status=status,
        ip=ip,
        begin_time=begin_time,
        end_time=end_time
    )
    return await LoginLogService.get_login_log_list(query, db)


@router.get("/login/{log_id}", summary="获取登录日志详情")
async def get_login_log_detail(
    log_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取登录日志详情"""
    result = await LoginLogService.get_login_log_detail(log_id, db)
    return success_response(data=result.model_dump())


@router.delete("/login", summary="批量删除登录日志")
async def delete_login_logs(
    data: LogBatchDeleteSchema,
    db: AsyncSession = Depends(get_db)
):
    """批量删除登录日志"""
    await LoginLogService.delete_login_logs(data, db)
    return success_response(message="删除成功")


@router.delete("/login/clean", summary="清理旧的登录日志")
async def clean_old_login_logs(
    days: int = Query(90, ge=1, description="保留天数"),
    db: AsyncSession = Depends(get_db)
):
    """清理旧的登录日志"""
    count = await LoginLogService.clean_old_login_logs(days, db)
    return success_response(data={"deleted_count": count}, message=f"清理完成，删除了 {count} 条记录")


@router.get("/login/statistics", summary="获取登录日志统计")
async def get_login_log_statistics(
    db: AsyncSession = Depends(get_db)
):
    """获取登录日志统计"""
    result = await LoginLogService.get_login_log_statistics(db)
    return success_response(data=result)