#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.common.response import success_response, error_response
from app.utils.common import body_to_json
from .service import PrecisionTestService

router = APIRouter()


# ------------------------------------------------------------------ #
# Repository endpoints                                                #
# ------------------------------------------------------------------ #

@router.post("/repository/list")
async def list_repositories(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """查询仓库列表"""
    try:
        body = await body_to_json(request)
        data = await PrecisionTestService.list_repositories(db, body, current_user_id)
        return success_response(data)
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/repository/save")
async def save_repository(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增或更新仓库"""
    try:
        body = await body_to_json(request)
        data = await PrecisionTestService.save_repository(db, body, current_user_id)
        return success_response(data)
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/repository/delete")
async def delete_repository(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除仓库"""
    try:
        body = await body_to_json(request)
        data = await PrecisionTestService.delete_repository(db, body, current_user_id)
        return success_response(data)
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


# ------------------------------------------------------------------ #
# Coverage report endpoints                                           #
# ------------------------------------------------------------------ #

@router.post("/coverage/report/list")
async def list_reports(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """查询覆盖率报告列表"""
    try:
        body = await body_to_json(request)
        data = await PrecisionTestService.list_reports(db, body, current_user_id)
        return success_response(data)
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/coverage/report/get")
async def get_report(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """查询单条覆盖率报告"""
    try:
        body = await body_to_json(request)
        data = await PrecisionTestService.get_report(db, body, current_user_id)
        return success_response(data)
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/coverage/report/delete")
async def delete_report(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除覆盖率报告"""
    try:
        body = await body_to_json(request)
        data = await PrecisionTestService.delete_report(db, body, current_user_id)
        return success_response(data)
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


# ------------------------------------------------------------------ #
# Coverage detail endpoint                                            #
# ------------------------------------------------------------------ #

@router.post("/coverage/detail")
async def get_coverage_detail(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """查询覆盖率详情"""
    try:
        body = await body_to_json(request)
        data = await PrecisionTestService.get_coverage_detail(db, body, current_user_id)
        return success_response(data)
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


# ------------------------------------------------------------------ #
# Upload XML endpoint (multipart)                                     #
# ------------------------------------------------------------------ #

@router.post("/coverage/upload_xml")
async def upload_xml(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
    file: UploadFile = File(...),
    report_id: int = Form(...),
):
    """上传 JaCoCo XML 文件"""
    try:
        file_bytes = await file.read()
        data = await PrecisionTestService.upload_jacoco_xml(db, file_bytes, report_id, current_user_id)
        return success_response(data)
    except HTTPException:
        raise
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


# ------------------------------------------------------------------ #
# JaCoCo Dump endpoint — call jar to pull from running agent          #
# ------------------------------------------------------------------ #

@router.post("/coverage/jacoco_dump")
async def jacoco_dump(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """通过 JaCoCo CLI 从运行中的 agent 拉取覆盖率数据并解析入库"""
    try:
        body = await body_to_json(request)
        data = await PrecisionTestService.jacoco_dump(db, body, current_user_id)
        return success_response(data)
    except HTTPException:
        raise
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


# ------------------------------------------------------------------ #
# Trigger coverage endpoint                                           #
# ------------------------------------------------------------------ #

@router.post("/trigger_coverage")
async def trigger_coverage(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """触发覆盖率分析"""
    try:
        body = await body_to_json(request)
        data = await PrecisionTestService.trigger_coverage(db, body, current_user_id)
        return success_response(data)
    except HTTPException:
        raise
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")
