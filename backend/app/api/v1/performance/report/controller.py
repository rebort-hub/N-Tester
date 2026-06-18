#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import success_response
from app.core.dependencies import get_current_user_id
from app.db.sqlalchemy import get_db
from .schema import PerfReportIdReqSchema
from .service import PerfReportService

router = APIRouter(prefix='/performance/reports', tags=['性能测试 - 压测报告'])
"""
=========================================================================
性能测试 - 压测报告 Controller

API 路由（均不使用整型 ID 路径参数）：
  GET    /list                          分页查询报告列表
  GET    /download?id=xx                获取 zip 预签名下载 URL
  GET    /preview/{report_code}/{path}  在线预览文件代理
  GET    /log?id=xx&log_type=console|collector  查看日志
  GET    /collectProcess?id=xx          报告收集进度 SSE 流
  POST   /stop                          强制停止收集（id 放请求体）
  POST   /resume                        恢复中断的收集（id 放请求体）
  POST   /delete                        删除报告（id 放请求体）
=========================================================================
"""


@router.get('/list', summary='压测报告列表')
async def list_reports(
    report_name:        Optional[str] = Query(None, description='报告文件名称，模糊匹配'),
    scenario_code:      Optional[str] = Query(None, description='场景编号，精确匹配'),
    creator:            Optional[str] = Query(None, description='报告人，模糊匹配'),
    generated_at_start: Optional[str] = Query(None, description='生成时间起（yyyy-MM-dd HH:mm:ss）'),
    generated_at_end:   Optional[str] = Query(None, description='生成时间止（yyyy-MM-dd HH:mm:ss）'),
    page:               int           = Query(1,  ge=1,          description='页码'),
    page_size:          int           = Query(20, ge=1, le=100,  description='每页数量'),
    db:       AsyncSession = Depends(get_db),
    user_id:  int          = Depends(get_current_user_id),
):
    """分页查询压测报告，支持按报告名称/场景编号/生成时间范围/报告人组合过滤。"""
    result = await PerfReportService(db).get_list(
        report_name=report_name,
        scenario_code=scenario_code,
        creator=creator,
        generated_at_start=generated_at_start,
        generated_at_end=generated_at_end,
        page=page,
        page_size=page_size,
    )
    return success_response(data=result)


@router.get('/download', summary='获取报告下载链接')
async def download_report(
    id:      int          = Query(..., gt=0, description='报告主键 ID'),
    types:   str | None   = Query(None, description='文件类型，逗号分隔：report,log,jtl；缺省=全部'),
    db:      AsyncSession = Depends(get_db),
    user_id: int          = Depends(get_current_user_id),
):
    """返回各文件的 Minio 预签名下载 URL（有效期 30 分钟）。

    - report → jmeter-reports.zip（HTML 报告）
    - log    → jmeter-logs.zip（JMeter 运行日志）
    - jtl    → results.zip（JTL 结果文件）
    """
    type_list = [t.strip() for t in types.split(',')] if types else None
    urls = await PerfReportService(db).get_download_url(id, type_list)
    return success_response(data=urls)


@router.get('/preview/{report_code}/{path:path}', summary='在线报告预览文件代理')
async def preview_report(
    request:     Request,
    report_code: str,
    path:        str,
    db:          AsyncSession = Depends(get_db),
):
    """
    直接流式返回报告预览文件，前端通过 window.open 在新 Tab 打开。

    - report_code 为业务标识（纯 ASCII），不是数据库整型 ID
    - path 为 zip 内 report/ 目录下的相对路径，如 index.html
    - index.html 会自动注入 <base> 标签，使相对路径资源走本接口代理
    """
    return await PerfReportService(db).stream_preview_file(
        report_code, path, str(request.base_url),
        if_none_match=request.headers.get('if-none-match'),
    )


@router.get('/log', summary='查看报告日志')
async def get_report_log(
    id:       int          = Query(..., gt=0,  description='报告主键 ID'),
    log_type: str          = Query('console',  description='日志类型：console-JMeter控制台日志，collector-收集流程日志'),
    filename: str | None   = Query(None,       description='指定日志文件名（log_type=console 时有效，缺省=合并所有文件）'),
    db:       AsyncSession = Depends(get_db),
    user_id:  int          = Depends(get_current_user_id),
):
    """
    获取日志文本内容。

    - log_type=console：返回 zip 内 logs/jmeter.log（压测过程控制台输出）
      - filename 指定时只返回该文件；未指定时合并全部文件
      - 响应 data.files 返回 zip 内文件名列表（供前端构建悬停菜单）
    - log_type=collector：返回 Minio 收集流程日志（每场景最新一次的收集过程日志）
    """
    data = await PerfReportService(db).get_log(id, log_type, filename)
    return success_response(data=data)


@router.get('/collectProcess', summary='报告收集进度 SSE')
async def collect_process_sse(
    id:      int          = Query(..., gt=0, description='报告主键 ID'),
    db:      AsyncSession = Depends(get_db),
    user_id: int          = Depends(get_current_user_id),
):
    """
    报告收集进度实时推流（SSE）。

    - 收集中（status=1）：每秒推送当前步骤、进度百分比、详情，收集结束后关闭流。
    - 已完成/失败：立即推送终态事件后关闭。
    - 事件格式：{ step, pct, step_name, detail, status: 'running'|'done'|'failed' }
    """
    return await PerfReportService(db).collect_process_sse(id)


@router.post('/stop', summary='强制停止报告收集')
async def stop_report(
    data:    PerfReportIdReqSchema,
    db:      AsyncSession = Depends(get_db),
    user_id: int          = Depends(get_current_user_id),
):
    """强制停止收集中（status=1）的报告，状态变更为中断（status=3），同步清理 Minio 残留文件。"""
    await PerfReportService(db).stop(data)
    return success_response(data=[], message='强制停止成功')


@router.post('/resume', summary='恢复中断的报告收集')
async def resume_report(
    data:    PerfReportIdReqSchema,
    db:      AsyncSession = Depends(get_db),
    user_id: int          = Depends(get_current_user_id),
):
    """
    恢复中断（status=3）的报告收集。

    - SSH 采集当前源文件 MD5，与 DB 原始签名对比
    - 任一文件 MD5 一致则恢复，全部不一致则拒绝（源文件已被覆盖）
    - 清理 Minio 残留后重新启动收集任务
    """
    await PerfReportService(db).resume(data)
    return success_response(data=[], message='已重新启动收集任务')


@router.post('/delete', summary='删除压测报告')
async def delete_report(
    data:    PerfReportIdReqSchema,
    db:      AsyncSession = Depends(get_db),
    user_id: int          = Depends(get_current_user_id),
):
    """删除 Minio zip、预览文件，软删 DB 记录。id 放请求体。"""
    await PerfReportService(db).delete(data)
    return success_response(data=[], message='删除成功')