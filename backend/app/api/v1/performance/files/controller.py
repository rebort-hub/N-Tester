#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
import json
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import success_response
from app.core.dependencies import get_current_user_id
from app.corelibs.logger import logger
from app.db.sqlalchemy import get_db
from .schema import (
    PerfFileConfirmReqSchema,
    PerfFileConfirmReuploadReqSchema,
    PerfFilePresignReqSchema,
    PerfFilePresignReuploadReqSchema,
    PerfFileSetRefsSchema, DistributeReqSchema, SplitDistributeReqSchema, ClearDistributeReqSchema,
)
from .service import PerfFileService, DistributeService

router = APIRouter(prefix="/performance/files", tags=["性能测试 - 文件管理"])
"""
=========================================================================
性能测试 - 文件管理 Controller

API 路由入口：
--------------------文件上传下载相关----------------------------
  POST   /upload              小文件（≤50MB）后端代理上传
  POST   /presignUpload       大文件申请预签名 PUT URL（第一阶段）
  POST   /confirm             大文件确认上传完成（第二阶段）
  GET    /options             文件下拉选项（轻量，仅 id+name）
  GET    /list                文件列表（分页 + 多维过滤）
  GET    /{file_id}/downloadUrl  获取预签名下载 URL
  PUT    /reupload/{file_id}       更新文件元数据
  PUT    /update/{file_id}       修改文件（名称、引用文件等）
  DELETE /delete/{file_id}       删除文件（MinIO + 软删 DB）
--------------------文件分发、清除相关（SSE 实时进度）-----------
  POST   /distribute/share/stream  共享分发（完整文件分发）
  POST   /distribute/split/stream  分割分发（等比分片分发）
  POST   /distribute/clear/stream  清除分发（删除压力机上的文件）
=========================================================================
"""

# ================================================================== #
#  方案 B：小文件后端代理上传（≤100MB）
# ================================================================== #

@router.post("/upload", summary="小文件上传", description="≤100MB，后端代理到 MinIO")
async def upload_file(
    file:     UploadFile    = File(...,  description="上传的文件（白名单：jmx/csv/txt/json/yaml/zip/gz等）"),
    remark:   Optional[str] = Form(None, description="备注"),
    db:       AsyncSession  = Depends(get_db),
    user_id:  int           = Depends(get_current_user_id),
):
    """
    小文件直接上传接口（前端使用 multipart/form-data上传）。
    文件大小超过 100MB 时接口返回 400，引导前端改用 /presign-upload。
    """
    result = await PerfFileService(db).common_upload(file, remark, user_id)
    return success_response(data=result, message="上传成功")


# ================================================================== #
#  方案 C：大文件预签名两阶段直传
# ================================================================== #

@router.post("/presignUpload", summary="大文件申请预签名", description=" PUT URL（第一阶段）")
async def presign_upload(
    data:    PerfFilePresignReqSchema,
    db:      AsyncSession = Depends(get_db),
    user_id: int          = Depends(get_current_user_id),
):
    """
    大文件上传第一步：后端签发预签名 PUT URL，前端用 XMLHttpRequest 直接 PUT 到 MinIO。
    返回：file_id（预占位记录ID）、upload_url（有效期30分钟）、object_key。
    """
    result = await PerfFileService(db).presign_upload(data, user_id)
    return success_response(data=result)


@router.post("/confirm", summary="大文件确认上传完成", description="（第二阶段）")
async def confirm_upload(
    data:    PerfFileConfirmReqSchema,
    db:      AsyncSession = Depends(get_db),
    user_id: int          = Depends(get_current_user_id),
):
    """
    大文件上传第二步：前端确认文件已成功 PUT 到 MinIO。
    后端通过 MinIO stat_object 验证对象真实存在后，将 upload_status 置为 1（完成）。
    """
    result = await PerfFileService(db).confirm_upload(data, user_id)
    return success_response(data=result, message="上传确认成功")


# ================================================================== #
#  文件列表
# ================================================================== #

@router.get("/options", summary="获取文件下拉选项（轻量，仅 id+name）")
async def get_file_options(
    file_type: Optional[str] = Query(None, description="文件类型过滤：jmx/csv/txt 等"),
    db:        AsyncSession  = Depends(get_db),
    user_id:   int           = Depends(get_current_user_id),
):
    """仅返回 id 和 name，专供表单下拉选择器使用，无分页。"""
    result = await PerfFileService(db).get_options(file_type)
    return success_response(data=result)


@router.get("/list", summary="获取文件列表")
async def list_files(
    name:        Optional[str] = Query(None, description="文件名称，模糊匹配"),
    file_type:   Optional[str] = Query(None, description="文件类型：jmx/csv/txt/json 等"),
    ref_status:  Optional[int] = Query(None, description="引用状态：0-未引用 1-已引用 2-已关联 3-使用中"),
    page:        int           = Query(1,    ge=1,        description="页码"),
    page_size:   int           = Query(20,   ge=1, le=100, description="每页数量"),
    db:          AsyncSession  = Depends(get_db),
    user_id:     int           = Depends(get_current_user_id),
):
    """
    分页查询文件列表，仅返回 upload_status=1（上传完成）的记录。
    JMX 类型文件自动附带 ref_files（引用的数据文件简要信息）。
    """
    result = await PerfFileService(db).get_list(page, page_size, file_type, ref_status, name)
    return success_response(data=result)


# ================================================================== #
#  下载 URL
# ================================================================== #

@router.get("/{file_id}/downloadUrl", summary="获取文件下载预签名 URL")
async def get_download_url(
    file_id: int,
    db:      AsyncSession = Depends(get_db),
    user_id: int          = Depends(get_current_user_id),
):
    """
    返回有效期 5 分钟的预签名 GET URL。
    前端通过 window.open(url) 或 <a download> 触发下载，文件流量直接走 MinIO。
    """
    result = await PerfFileService(db).get_download_url(file_id)
    return success_response(data=result)


# ================================================================== #
#  替换上传（覆盖原文件）
# ================================================================== #

@router.put("/reupload/{file_id}", summary="替换文件", description="（覆盖原 MinIO 对象，保留 DB 记录 ID）")
async def update_file(
    file_id: int,
    file:    UploadFile    = File(...,  description="新文件，替换原有内容"),
    remark:  Optional[str] = Form(None, description="备注"),
    db:      AsyncSession  = Depends(get_db),
    user_id: int           = Depends(get_current_user_id),
):
    """
    小文件替换接口（≤限制值）：删除 MinIO 旧对象，上传新文件，原地更新 DB 记录。
    DB 记录 ID 不变，已有的 JMX 引用关系保持不断。
    大文件替换请使用 /presign-reupload/{file_id} + /confirm-reupload/{file_id} 两阶段接口。
    """
    await PerfFileService(db).update_upload(file_id, file, remark, user_id)
    return success_response(data=[], message="更新成功")


# ================================================================== #
#  大文件替换：预签名两阶段直传（保留 DB 记录 ID 及关联关系）
# ================================================================== #

@router.post("/presignReupload", summary="大文件替换申请预签名 PUT URL（第一阶段）")
async def presign_reupload(
    data:    PerfFilePresignReuploadReqSchema,
    db:      AsyncSession = Depends(get_db),
    user_id: int          = Depends(get_current_user_id),
):
    """
    大文件替换第一步：校验文件扩展名一致后签发预签名 PUT URL，前端直传 MinIO。
    file_id、file_name、file_size 均在请求体中传入。
    """
    result = await PerfFileService(db).presign_reupload(data, user_id)
    return success_response(data=result)


@router.post("/confirmReupload", summary="大文件替换确认完成（第二阶段）")
async def confirm_reupload(
    data:    PerfFileConfirmReuploadReqSchema,
    db:      AsyncSession = Depends(get_db),
    user_id: int          = Depends(get_current_user_id),
):
    """
    大文件替换第二步：stat 验证 MinIO 对象存在，删旧对象，原地更新 DB 记录（ID 不变）。
    file_id、object_key、file_name 均在请求体中传入。
    """
    result = await PerfFileService(db).confirm_reupload(data, user_id)
    return success_response(data=result, message="替换确认成功")


# ================================================================== #
#  删除
# ================================================================== #

@router.delete("/delete/{file_id}", summary="删除文件")
async def delete_file(
    file_id: int,
    db:      AsyncSession = Depends(get_db),
    user_id: int          = Depends(get_current_user_id),
):
    """删除文件：先从 MinIO 删除对象，再软删 DB 记录（enabled_flag=0）。"""
    await PerfFileService(db).delete(file_id)
    return success_response(data=[], message="删除成功")


# ================================================================== #
#  JMX 引用数据文件管理
# ================================================================== #

@router.put("/update/{file_id}", summary="更新 JMX 文件名称及引用的数据文件列表")
async def edit_set_refs(
    file_id: int,
    data:    PerfFileSetRefsSchema,
    db:      AsyncSession = Depends(get_db),
    user_id: int          = Depends(get_current_user_id),
):
    """
    覆盖式更新 JMX 文件名称（可选）和引用的数据文件列表（ref_file_ids 字段）。
    传入 ref_file_ids=[] 表示清空所有引用。
    自动同步被引用数据文件的 ref_status 字段。
    """
    await PerfFileService(db).edit_set_refs(file_id, data, user_id)
    return success_response(data=[], message="更新成功")


# ================================================================== #
#           共享分发 SSE 流式接口
# ================================================================== #
@router.post("/distribute/share/stream", summary="共享分发（SSE 实时进度）")
async def share_distribute_stream(
    req: DistributeReqSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    共享分发 SSE 流式接口。响应体为 text/event-stream，客户端通过 fetch ReadableStream 消费。
    每完成一台压力机分发立即推送 node_done 事件，无需等待全部结束。
    事件类型：start | master | node_pending | method | node_done | done | error
    """
    service = DistributeService(db)

    async def event_gen():
        try:
            async for chunk in service.share_distribute_stream(
                file_id=req.file_id, worker_count=req.worker_count, machine_type=req.machine_type, user_id=user_id
            ):
                yield chunk
        except Exception as e:
            logger.error(f"共享分发 SSE 事件流异常: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ================================================================== #
#           清除分发 SSE 流式接口
# ================================================================== #
@router.post("/distribute/clear/stream", summary="清除分发（SSE 实时进度）")
async def clear_distribute_stream(
    req: ClearDistributeReqSchema,
    db: AsyncSession = Depends(get_db),
):
    """
    清除分发 SSE 流式接口。事件协议同共享/分割分发，dist_status=0（清除后重置为未分发）。
    事件类型：start | master | method | node_pending | node_done | done | error
    """
    service = DistributeService(db)

    async def event_gen():
        try:
            async for chunk in service.clear_distribute_stream(file_id=req.file_id, worker_count=req.worker_count):
                yield chunk
        except Exception as e:
            logger.error(f"清除分发 SSE 事件流异常: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

# ================================================================== #
#           分割分发 SSE 流式接口
# ================================================================== #
@router.post("/distribute/split/stream", summary="分割分发（SSE 实时进度）")
async def split_distribute_stream(
    req: SplitDistributeReqSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    分割分发 SSE 流式接口。事件协议同共享分发，dist_status=2。
    """
    service = DistributeService(db)

    async def event_gen():
        try:
            async for chunk in service.split_distribute_stream(
                file_id=req.file_id, worker_count=req.worker_count, machine_type=req.machine_type, user_id=user_id
            ):
                yield chunk
        except Exception as e:
            logger.error(f"分割分发 SSE 事件流异常: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )