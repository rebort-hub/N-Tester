#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
import asyncio
import json
import os
import re
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta, datetime
from typing import AsyncGenerator, Dict, List, Optional, Any, Tuple


from app.utils.common import format_file_size, get_content_type, build_object_key, get_current_time_str
from app.corelibs.logger import logger
from fastapi import HTTPException, UploadFile, status
from minio.error import S3Error
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseCRUD
from app.core.minio_client import MinioClient
from app.utils.oper_shell import ShellOperationUtils, _is_ssh_conn_error
from app.utils.oper_jmx import extract_jmx_thread_config, calc_jmx_estimated_duration
from app.utils.crypto import decrypt_field
from .crud import PerfFileCRUD
from .model import PerfFileModel
from .schema import (
    PerfFilePresignReqSchema,
    PerfFileConfirmReqSchema,
    PerfFileSetRefsSchema,
    PerfFileRespSchema,
    PerfFileRefItemSchema, DistributeNodeResultSchema, PerfFilePresignReuploadReqSchema,
)
from ..config.crud import PerfMachineCRUD, PerfParamCRUD
from ..config.model import PerfConfigMachineModel


def _build_credential(machine: PerfConfigMachineModel) -> Optional[dict]:
    """从机器对象构造 SSH 凭证 dict，无凭证时返回 None（走全局 .env 兜底）。"""
    if not machine or not (machine.ssh_user or machine.ssh_password):
        return None
    return {
        "ssh_user":     machine.ssh_user or None,
        "ssh_password": decrypt_field(machine.ssh_password) if machine.ssh_password else None,
    }

"""
==============================================================================
性能测试 - 文件管理 Service
业务逻辑层，负责：
  - 方案 B：小文件（≤50MB）后端代理上传到 MinIO
  - 方案 C：大文件预签名两阶段直传（签发 URL → confirm）
  - 文件列表分页查询（含操作人）
  - 下载 URL 签发
  - 文件删除（MinIO + 软删 DB）
  - JMX 引用数据文件的读写（ref_file_ids JSON 字段）
==============================================================================
"""

import urllib.request as _urllib_request
import shutil as _shutil
import subprocess as _subprocess


def _download_url_to_file(url: str, local_path: str) -> None:
    """通过预签名 URL 将 MinIO 文件下载到本地。
    优先使用系统 curl（TLS 指纹与浏览器接近，能绕过 Cloudflare Bot Fight Mode）；
    curl 不可用时降级为 wget；最后兜底 urllib（部分环境下仍可能被拦截）。
    """
    if _shutil.which('curl'):
        result = _subprocess.run(
            [
                'curl', '-fsSL', '--max-time', '3600',
                '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                '-o', local_path, url,
            ],
            capture_output=True, timeout=3660,
        )
        if result.returncode != 0:
            raise RuntimeError(f"curl 下载失败（exit={result.returncode}）: {result.stderr.decode(errors='replace').strip()}")
        return

    if _shutil.which('wget'):
        result = _subprocess.run(
            [
                'wget', '-qO', local_path,
                '--timeout=3600',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                url,
            ],
            capture_output=True, timeout=3660,
        )
        if result.returncode != 0:
            raise RuntimeError(f"wget 下载失败（exit={result.returncode}）: {result.stderr.decode(errors='replace').strip()}")
        return

    req = _urllib_request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': '*/*',
    })
    with _urllib_request.urlopen(req, timeout=3600) as resp:
        with open(local_path, 'wb') as f:
            while chunk := resp.read(1 << 20):
                f.write(chunk)


def _parse_mbps(value: str, default: int = 500) -> int:
    """从参数值中提取 Mbps 数字，兼容 '500'、'500Mbps'、'500 mbps'、'1000MB/s' 等格式，单位一律按 Mbps 计算。"""
    m = re.match(r'^\s*(\d+)', str(value))
    return int(m.group(1)) if m else default


def _get_file_type(filename: str) -> str:
    """根据文件扩展名推断 file_type 字段值（小写扩展名，与字典表 perf_file_type 的 dict_label.lower() 保持一致）。"""
    ext = os.path.splitext(filename)[-1].lstrip(".").lower()
    norm = {"yml": "yaml"}  # .yml 归一化为 yaml，与字典标签 YAML 对应
    return norm.get(ext, ext)


async def _get_allowed_extensions(db: AsyncSession) -> set:
    """
    从 Redis 缓存获取允许上传的扩展名集合，缓存未命中时查字典表 perf_file_type。
    dict_value 格式为不含点的扩展名（如 jmx、csv）。
    TTL 300 秒，字典变更后下次请求自动刷新。
    Redis 不可用时自动降级为直接查库。
    """
    from app.db import get_redis_pool
    from app.api.v1.system.dict.crud import DictDataCRUD
    from app.api.v1.system.dict.service import DICT_CACHE_KEY_PREFIX
    from config import config

    cache_key = f"{DICT_CACHE_KEY_PREFIX}perf_file_type"
    cache_ttl = 300

    try:
        redis_pool = get_redis_pool()
        if not redis_pool.redis:
            redis_pool.init_by_config(config=config)
        redis = redis_pool.redis

        cached = await redis.get(cache_key)
        if cached:
            return set(cached)  # MyAsyncRedis.get 已自动 JSON 反序列化 → list

        items = await DictDataCRUD(db).get_by_type_crud("perf_file_type")
        values = [item.dict_label.lower() for item in items if item.status == 1]
        await redis.set(cache_key, values, ex=cache_ttl)
        return set(values)
    except Exception:
        # Redis 不可用时降级为直接查库，不影响上传流程
        items = await DictDataCRUD(db).get_by_type_crud("perf_file_type")
        return set(item.dict_label.lower() for item in items if item.status == 1)


async def _validate_extension(filename: str, db: AsyncSession) -> None:
    """校验文件扩展名是否在字典表 perf_file_type 配置的白名单内，不合法时抛出 HTTP 400。
    白名单来自 dict_label.lower()，dict_value 为数字仅作标识，不参与校验。
    """
    ext = os.path.splitext(filename)[-1].lstrip(".").lower()
    norm = {"yml": "yaml"}  # .yml 归一化为 yaml，与字典标签 YAML 对应
    ext = norm.get(ext, ext)
    allowed = await _get_allowed_extensions(db)
    if ext not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型：.{ext}，允许的类型：{', '.join(f'.{e}' for e in sorted(allowed))}",
        )


class PerfFileService:
    """性能测试文件管理 Service。"""
    def __init__(self, db: AsyncSession):
        self.db = db
        self.param_crud   = PerfParamCRUD(self.db)
        self.file_crud    = PerfFileCRUD(self.db)
    # ------------------------------------------------------------------ #
    #  方案 B：小文件后端代理上传（≤50MB）
    # ------------------------------------------------------------------ #

    async def common_upload(self, file: UploadFile, remark: Optional[str], user_id: int,) -> Dict:
        """
        小文件代理上传流程：
        1. 校验扩展名（字典表白名单）
        2. 读取文件内容，校验大小（≤100MB）
        3. 推断 file_type、content_type、生成 object_key
        4. 上传到 MinIO（put_object）
        5. 写 DB 元数据，upload_status=1（直接完成）

        Args:
            file:    上传的文件对象（multipart/form-data）
            remark:  备注，可选
            user_id: 当前操作人 ID
        Returns:
            Dict: {'id': 新建文件记录的 ID}
        """
        from config import config

        await _validate_extension(file.filename, self.db)

        content = await file.read()
        file_size = len(content)
        upload_max_bytes = await self.param_crud.get_param_value("PROXY_UPLOAD_MAX_BYTES")
        max_bytes = int(re.findall(r'\d+', upload_max_bytes)[0])
        if file_size > max_bytes * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"文件大小 {file_size / 1024 / 1024:.1f} MB 超过代理上传限制（{upload_max_bytes}），"
                    "请使用预签名直传接口 /presign-upload"
                ),
            )

        file_type    = _get_file_type(file.filename)
        content_type = get_content_type(file.filename)
        object_key   = build_object_key(file.filename, file_type)
        bucket       = config.MINIO_BUCKET
        # 上传文件到Minio文件服务器
        await MinioClient.put_object(bucket, object_key, content, content_type)
        # 数据库插入上传文件相关数据
        obj_create = await self.file_crud.create_crud({
            "file_name":             file.filename,
            "file_type":             file_type,
            "file_size":             file_size,
            "content_type":          content_type,
            "bucket":                bucket,
            "object_key":            object_key,
            "upload_status":         1,
            "remark":                remark,
            "created_by":            user_id,
            # JMX 小文件：content 已在内存，上传完成后即时解析线程组配置缓存
            "parsed_thread_config":  extract_jmx_thread_config(content) if file_type == 'jmx' else None,
        })
        return {'id': obj_create.id}

    # ------------------------------------------------------------------ #
    #  方案 C：大文件预签名两阶段直传
    # ------------------------------------------------------------------ #

    async def presign_upload(self, data: PerfFilePresignReqSchema, user_id: int,) -> Dict:
        """
        大文件预签名上传第一阶段：签发预签名 PUT URL。
        写 upload_status=0 的预占位记录，前端拿到 URL 后直接 PUT 到 MinIO，无需经过后端。

        Args:
            data:    预签名请求体（file_name、file_size、remark）
            user_id: 当前操作人 ID
        Returns:
            Dict: {file_id, upload_url, object_key}
              - file_id:    预占位 DB 记录 ID，confirm 时原样回传
              - upload_url: 有效期 30 分钟的预签名 PUT URL
              - object_key: MinIO 对象路径，confirm 时用于防篡改校验
        """
        from config import config
        # 校验文件拓展名
        await _validate_extension(data.file_name, self.db)

        file_type  = _get_file_type(data.file_name)
        object_key = build_object_key(data.file_name, file_type)
        bucket     = config.MINIO_BUCKET
        # 新增上传数据（upload_status=0）
        obj = await self.file_crud.create_crud({
            "file_name":     data.file_name,
            "file_type":     file_type,
            "file_size":     data.file_size,
            "content_type":  get_content_type(data.file_name),
            "bucket":        bucket,
            "object_key":    object_key,
            "upload_status": 0,
            "remark":        data.remark,
            "created_by":    user_id,
        })
        # 返回预签名URL
        upload_url = MinioClient.presign_put(bucket, object_key, expires_minutes=30)
        return {"file_id": obj.id, "upload_url": upload_url, "object_key": object_key}

    async def confirm_upload(self, data: PerfFileConfirmReqSchema, user_id: int,) -> Dict:
        """
        大文件预签名上传第二阶段：前端上传完成后确认。
        通过 MinIO stat_object 验证对象真实存在后，将 upload_status 置为 1。

        Args:
            data:    确认请求体（file_id、object_key）
            user_id: 当前操作人 ID
        Returns:
            Dict: 更新后的文件记录完整字段（PerfFileRespSchema）
        Raises:
            HTTPException 404: file_id 对应记录不存在
            HTTPException 400: 已确认过 / object_key 不匹配 / MinIO 中对象不存在
        """
        obj = await self.file_crud.get_by_id_crud(data.file_id)

        # 幂等校验：防止重复确认或伪造 object_key
        if not obj or not obj.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件记录不存在")
        if obj.upload_status != 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该文件已确认上传，请勿重复提交")
        if obj.object_key != data.object_key:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="object_key 与预签名记录不匹配")

        try:
            # stat_object 验证 MinIO 中对象真实存在，同时获取服务端实际文件大小
            stat = await MinioClient.stat_object(obj.bucket, obj.object_key)
        except S3Error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MinIO 中未找到该对象，请确认文件已上传完成")

        # 更新确认上传结果：文件大小、upload_status
        update_data: dict = {
            "file_size":     stat["size"],
            "upload_status": 1,
            "updated_by":    user_id,
        }
        # JMX 大文件：从 MinIO 下载后解析线程组配置缓存（confirm 时文件已确实存在）
        if obj.file_type == 'jmx':
            try:
                from config import config as app_config
                jmx_bytes = await MinioClient.get_object_bytes(app_config.MINIO_BUCKET, obj.object_key)
                update_data['parsed_thread_config'] = extract_jmx_thread_config(jmx_bytes)
            except Exception:
                logger.warning(f'confirm_upload JMX 线程组配置解析失败 file_id={obj.id}，不影响确认结果')
        updated = await self.file_crud.update_crud(obj.id, update_data)
        return {'id': updated.id}

    # ------------------------------------------------------------------ #
    #  大文件替换：预签名两阶段直传（原地更新 DB 记录，保留 ref_file_ids 关联）
    # ------------------------------------------------------------------ #

    async def presign_reupload(self, data: PerfFilePresignReuploadReqSchema, user_id: int) -> Dict:
        """
        大文件替换预签名第一阶段：校验旧文件存在且扩展名与新文件一致，签发预签名 PUT URL。
        不创建新 DB 记录，不修改旧记录，仅返回 upload_url 和 object_key 供前端直传 MinIO。

        Args:
            data:    PerfFilePresignReuploadReqSchema（file_id、file_name、file_size、remark?）
            user_id: 当前操作人 ID
        Returns:
            Dict: {upload_url, object_key}
        """
        from config import config

        obj = await self.file_crud.get_by_id_crud(data.file_id)
        if not obj or not obj.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

        # 校验新旧文件扩展名一致（.yml 归一化为 yaml）
        norm = {"yml": "yaml"}
        old_ext_raw = os.path.splitext(obj.file_name)[-1].lstrip(".").lower()
        old_ext = norm.get(old_ext_raw, old_ext_raw)
        new_ext = _get_file_type(data.file_name)
        if old_ext != new_ext:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件类型不匹配，请上传 .{old_ext} 格式的文件",
            )

        object_key = build_object_key(data.file_name, new_ext)
        upload_url = MinioClient.presign_put(config.MINIO_BUCKET, object_key, expires_minutes=30)
        return {"upload_url": upload_url, "object_key": object_key}

    async def confirm_reupload(self, data: "PerfFileConfirmReuploadReqSchema", user_id: int) -> Dict:
        """
        大文件替换确认第二阶段：stat 验证新文件在 MinIO 中真实存在，
        删除旧 MinIO 对象，原地更新 DB 记录（ID 不变，保留 ref_file_ids 等关联关系）。

        Args:
            data:    PerfFileConfirmReuploadReqSchema（file_id、object_key、file_name）
            user_id: 当前操作人 ID
        Returns:
            Dict: {'id': file_id}
        """
        obj = await self.file_crud.get_by_id_crud(data.file_id)
        if not obj or not obj.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

        try:
            stat = await MinioClient.stat_object(obj.bucket, data.object_key)
        except S3Error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MinIO 中未找到该对象，请确认文件已上传完成",
            )

        # 删除旧 MinIO 对象（幂等，对象不存在时静默忽略）
        if obj.upload_status == 1:
            await MinioClient.remove_object(obj.bucket, obj.object_key)

        file_type = _get_file_type(data.file_name)
        update_data: dict = {
            "file_name":    data.file_name,
            "file_type":    file_type,
            "file_size":    stat["size"],
            "content_type": get_content_type(data.file_name),
            "object_key":   data.object_key,
            "upload_status": 1,
            "updated_by":   user_id,
        }
        # JMX 大文件替换后重新解析线程组配置缓存；非 JMX 清除旧缓存
        if file_type == "jmx":
            try:
                jmx_bytes = await MinioClient.get_object_bytes(obj.bucket, data.object_key)
                update_data["parsed_thread_config"] = extract_jmx_thread_config(jmx_bytes)
            except Exception:
                logger.warning(f"confirm_reupload JMX 线程组配置解析失败 file_id={data.file_id}，不影响确认结果")
        else:
            update_data["parsed_thread_config"] = None

        updated = await self.file_crud.update_crud(data.file_id, update_data)
        return {"id": updated.id}

    # ------------------------------------------------------------------ #
    #  列表查询
    # ------------------------------------------------------------------ #

    async def get_list(self, page: int, page_size: int,
        file_type: Optional[str] = None, ref_status: Optional[int] = None, name: Optional[str] = None,) -> Dict:
        """
        分页查询文件列表。
        使用 BaseCRUD.get_list_with_operator() 一次 SQL 获取列表、总数、操作人。
        JMX 文件自动附带 ref_files（引用数据文件的简要信息）。

        Args:
            page:        页码，从 1 开始
            page_size:   每页条数
            file_type:   文件类型过滤（jmx/csv/txt 等），None 表示不过滤
            ref_status:  引用状态过滤（0-未引用 1-已引用 2-已关联 3-使用中），None 表示不过滤
            name:        文件名关键字模糊匹配，None 表示不过滤
        Returns:
            Dict: {items, total, page, page_size}
        """
        conditions = [
            PerfFileModel.enabled_flag == 1,   # 数据状态正常
            PerfFileModel.upload_status == 1,  # 只展示上传完成的文件
        ]
        if file_type:
            conditions.append(PerfFileModel.file_type == file_type)
        if ref_status is not None:
            conditions.append(PerfFileModel.ref_status == ref_status)
        if name:
            conditions.append(PerfFileModel.file_name.like(f"%{name}%"))

        # 复合查询：主列表（含操作人）+ JMX 引用数据文件，共 2 次 SQL
        rows, total, ref_map = await self.file_crud.get_files_with_refs(
            conditions=conditions, order_by=[PerfFileModel.id.desc()],
            skip=(page - 1) * page_size, limit=page_size,)

        # 组装响应，JMX 文件附带引用数据文件详情
        items = []
        for row in rows:
            obj = row[0]
            item = PerfFileRespSchema.model_validate(obj).model_dump()
            item["operator_name"] = row.operator_name if hasattr(row, "operator_name") else None
            if obj.file_type == "jmx" and obj.ref_file_ids:
                item["ref_files"] = [
                    PerfFileRefItemSchema.model_validate(ref_map[fid]).model_dump()
                    for fid in obj.ref_file_ids
                    if fid in ref_map
                ]
            items.append(item)

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    # ------------------------------------------------------------------ #
    #  下拉选项（轻量）
    # ------------------------------------------------------------------ #

    async def get_options(self, file_type: Optional[str] = None) -> List[Dict]:
        """查询文件下拉选项，返回 id、name 及 parsed_thread_config，供场景创建表单自动识别线程组类型并预填参数。"""
        conditions = [PerfFileModel.enabled_flag == 1, PerfFileModel.upload_status == 1]
        if file_type:
            conditions.append(PerfFileModel.file_type == file_type)
        stmt = (
            select(PerfFileModel.id, PerfFileModel.file_name, PerfFileModel.parsed_thread_config)
            .where(and_(*conditions))
            .order_by(PerfFileModel.id.desc())
        )
        result = await self.db.execute(stmt)

        def _parse_tg(raw: Optional[str]) -> list:
            """将 TEXT 列中的 JSON 字符串解析为线程组数组（提取 thread_groups 层）。"""
            if not raw:
                return []
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    return data.get('thread_groups') or []
                if isinstance(data, list):
                    return data
            except Exception:
                pass
            return []

        options = []
        for row in result.all():
            tg_list = _parse_tg(row.parsed_thread_config)
            secs, has_unknown = calc_jmx_estimated_duration(tg_list)
            options.append({
                "id": row.id,
                "name": row.file_name,
                "parsed_thread_config": tg_list,
                "estimated_seconds": secs,
                "has_unknown_times": has_unknown,
            })
        return options

    # ------------------------------------------------------------------ #
    #  下载 URL
    # ------------------------------------------------------------------ #

    async def get_download_url(self, file_id: int) -> Dict:
        """
        签发文件下载预签名 URL（有效期 5 分钟）。

        Args:
            file_id: 文件记录 ID
        Returns:
            Dict: {download_url, file_name, expires_in}
        Raises:
            HTTPException 404: 文件不存在
            HTTPException 400: 文件尚未上传完成
        """
        obj = await self.file_crud.get_by_id_crud(file_id)
        # 判断文件数据是否存在
        if not obj or not obj.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
        if obj.upload_status != 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件尚未上传完成，无法下载")
        # 生成下载URL
        download_url = MinioClient.presign_get(
            bucket=obj.bucket, object_key=obj.object_key, expires_minutes=5, file_name=obj.file_name,)
        return {"download_url": download_url, "file_name": obj.file_name, "expires_in": 300}

    # ------------------------------------------------------------------ #
    #  替换上传（覆盖原文件，保留 DB 记录 ID）
    # ------------------------------------------------------------------ #

    async def update_upload(self, file_id: int, file: UploadFile, remark: Optional[str], user_id: int,) -> Dict:
        """
        文件替换流程：
        1. 校验原记录存在
        2. 校验新文件扩展名（字典表白名单）
        3. 读取新文件内容，校验大小（≤100MB）
        4. 删除 MinIO 旧对象（仅 upload_status=1 时执行）
        5. 上传新文件到 MinIO（生成新 object_key）
        6. 原地更新 DB 记录（保留原 id，JMX 引用关系不断）

        Args:
            file_id: 待替换的文件记录 ID
            file:    新文件对象（multipart/form-data）
            remark:  备注，传 None 时保持原值不变
            user_id: 当前操作人 ID
        Returns:
            None
        Raises:
            HTTPException 404: 文件不存在
            HTTPException 400: 扩展名不合法 / 文件超过 100MB
        """
        from config import config

        obj = await self.file_crud.get_by_id_crud(file_id)
        if not obj or not obj.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
        # 验证文件类型
        await _validate_extension(file.filename, self.db)
        # 判断文件大小<=100M
        content = await file.read()
        file_size = len(content)
        upload_max_bytes = await self.param_crud.get_param_value("PROXY_UPLOAD_MAX_BYTES")
        max_bytes = int(re.findall(r'\d+', upload_max_bytes)[0])
        if file_size > max_bytes * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"文件大小 {file_size / 1024 / 1024:.1f} MB 超过代理上传限制（{upload_max_bytes}），"
                    "请使用预签名直传接口 /presign-upload"
                ),
            )

        file_type    = _get_file_type(file.filename)
        content_type = get_content_type(file.filename)
        object_key   = build_object_key(file.filename, file_type)
        bucket       = config.MINIO_BUCKET

        # 删除 MinIO 旧对象
        if obj.upload_status == 1:
            await MinioClient.remove_object(obj.bucket, obj.object_key)

        # 上传新文件
        await MinioClient.put_object(bucket, object_key, content, content_type)

        # 原地更新 DB 记录
        update_data = {
            "file_name":     file.filename,
            "file_type":     file_type,
            "file_size":     file_size,
            "content_type":  content_type,
            "bucket":        bucket,
            "object_key":    object_key,
            "upload_status": 1,
            "creation_date": datetime.now(),   # 刷新上传时间，供前端与分发时间比较判断是否需要重新分发
            "updated_by":    user_id,
            # 替换后重新解析（非 JMX 写 None 清除旧缓存）
            "parsed_thread_config": extract_jmx_thread_config(content) if file_type == 'jmx' else None,
        }
        if remark is not None:
            update_data["remark"] = remark

        updated = await self.file_crud.update_crud(file_id, update_data)

    # ------------------------------------------------------------------ #
    #  删除
    # ------------------------------------------------------------------ #

    async def delete(self, file_id: int) -> None:
        """
        删除文件：先从 MinIO 删除对象，再软删 DB 记录（enabled_flag=0）。

        Args:
            file_id: 文件记录 ID
        Raises:
            HTTPException 404: 文件不存在
        """
        obj = await self.file_crud.get_by_id_crud(file_id)
        if not obj or not obj.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
        # Minio删除文件对象
        if obj.upload_status == 1:
            await MinioClient.remove_object(obj.bucket, obj.object_key)
        # 数据库再软删除数据
        await self.file_crud.soft_delete_crud([file_id])

    # ------------------------------------------------------------------ #
    #  JMX 引用数据文件（JSON 字段读写）
    # ------------------------------------------------------------------ #

    async def edit_set_refs(self, jmx_file_id: int, data: PerfFileSetRefsSchema, user_id: int,) -> Dict:
        """
        覆盖式设置 JMX 文件引用的数据文件列表。
        传入 ref_file_ids=[] 表示清空所有引用。

        流程：
        1. 校验 JMX 文件存在且类型为 jmx
        2. 校验所有 data_file_id 对应的文件存在且 upload_status=1
        3. 更新 ref_file_ids 字段（整体覆盖）
        4. 同步更新被引用文件的 ref_status：新增引用→1，移除引用且无其他引用→0

        Args:
            jmx_file_id:  JMX 文件记录 ID
            data:         请求体，包含新的 ref_file_ids 列表
            user_id:      当前操作人 ID
        Returns:
            None
        Raises:
            HTTPException 404: JMX 文件不存在
            HTTPException 400: 文件类型非 jmx / 数据文件不存在或未上传完成
        """
        # 校验 JMX 文件
        jmx_obj = await self.file_crud.get_by_id_crud(jmx_file_id)
        if not jmx_obj or not jmx_obj.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"JMX 文件不存在：id={jmx_file_id}")
        if jmx_obj.file_type != "jmx":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只有 jmx 类型文件才能设置数据文件引用")

        new_ids = list(dict.fromkeys(data.ref_file_ids))  # 去重并保持顺序

        # 校验数据文件存在
        if new_ids:
            data_files, _ = await self.file_crud.get_list_crud(conditions=[
                PerfFileModel.enabled_flag == 1,
                PerfFileModel.upload_status == 1,
                PerfFileModel.id.in_(new_ids),
            ])
            found_ids = {f.id for f in data_files}
            missing = set(new_ids) - found_ids
            if missing:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"数据文件不存在或未上传完成：ids={sorted(missing)}")

        # 原引用列表（用于还原 ref_status）
        old_ids: List[int] = jmx_obj.ref_file_ids or []

        # 更新 JMX 文件的 ref_file_ids，若携带 file_name 则一并更新；clear_dist=True 时清除分发记录
        update_data: dict = {"ref_file_ids": new_ids, "updated_by": user_id}
        if data.file_name is not None:
            update_data["file_name"] = data.file_name
        if data.clear_dist:
            update_data.update({"dist_status": 0, "dist_worker_ids": [], "dist_time": None, "remark": None})
        await self.file_crud.update_crud(jmx_file_id, update_data)

        # 同步被引用文件的 ref_status
        # 新增引用的文件 → ref_status=1
        added_ids = set(new_ids) - set(old_ids)
        for fid in added_ids:
            await self.file_crud.update_crud(fid, {"ref_status": 1, "updated_by": user_id})

        # 移除引用的文件：检查是否还被其他 JMX 引用，若无则 ref_status→0
        removed_ids = set(old_ids) - set(new_ids)
        if removed_ids:
            # 查询其他 JMX 是否还引用了这些文件（JSON_CONTAINS 需 MySQL 5.7+）
            for fid in removed_ids:
                still_ref = await PerfFileService._is_still_referenced(self.db, fid, exclude_jmx_id=jmx_file_id)
                if not still_ref:
                    await self.file_crud.update_crud(fid, {"ref_status": 0, "updated_by": user_id})

    # ------------------------------------------------------------------ #
    #  内部辅助
    # ------------------------------------------------------------------ #

    async def _is_still_referenced(self, data_file_id: int, exclude_jmx_id: int) -> bool:
        """
        检查数据文件是否还被其他 JMX 文件引用（用于决定是否将 ref_status 还原为 0）。
        使用 MySQL JSON_CONTAINS 函数查询 ref_file_ids 字段（需 MySQL 5.7+）。

        Args:
            data_file_id:   待检查的数据文件 ID
            exclude_jmx_id: 排除的 JMX 文件 ID（即当前正在操作的 JMX，避免自引用干扰）
        Returns:
            bool: True 表示还有其他 JMX 引用该文件，False 表示已无引用
        """
        from sqlalchemy import func, text
        stmt = (
            select(PerfFileModel.id)
            .where(
                and_(
                    PerfFileModel.enabled_flag == 1,
                    PerfFileModel.file_type == "jmx",
                    PerfFileModel.id != exclude_jmx_id,
                    func.json_contains(
                        PerfFileModel.ref_file_ids,
                        text(f"'{data_file_id}'"),
                    ),
                )
            )
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None


"""
=====================================================================================
文件分发业务Services：文件分发、清除分发等。
负责从 MinIO 获取文件，并通过 SSH/SFTP 将文件分发至压力机。所有 SSH 认证均使用系统配置的默认凭据（私钥或密码）。
=====================================================================================
"""
class DistributeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.machine_crud = PerfMachineCRUD(self.db)
        self.param_crud = PerfParamCRUD(self.db)
        self.file_curd = PerfFileCRUD(self.db)
        # 远程压力机上的数据文件目录
        self.worker_data_dir = ["PERF_WORKER_DATA_DIR", "data/jmeter/"]

    @staticmethod
    def _calculate_max_workers(node_count: int, transfer_size_bytes: int) -> int:
        """
        按节点数和文件大小规划最大并发SSH连接数：
        - 若节点数 ≤ 20 且单节点传输文件 ≤ 200MB，则全并发（并发数 = 节点数）。
        - 否则限制并发数在 10 ~ 20 之间（取节点数的一半，并限制边界）。
        这样既能保证小规模/小文件任务快速完成，又能避免大文件传输时
        控制机资源（文件描述符、SSH 连接数）过载。
        Args:
            node_count: 分发目标节点数
            transfer_size_bytes: 单节点实际传输的文件大小（字节）
            - 共享分发：完整文件大小
            - 分割分发：分片文件大小 ≈ 完整文件大小 / 节点数量
        returns:
            int: 最大并发SSH连接数
        """
        transfer_size_mb = transfer_size_bytes / (1024 * 1024)
        if node_count <= 20 and transfer_size_mb <= 200:
            return node_count
        return min(20, max(10, node_count // 2))

    # ---------- 共享分发：MinIO 连通性探测 ----------
    @staticmethod
    def _probe_minio_reachable(ssh, minio_url: str, timeout: int = 10) -> tuple[bool, str]:
        """
        探测压力机是否能直接访问 MinIO（HTTP HEAD 请求，timeout 秒超时）。
        直接使用预签名 URL 探测，同时验证：网络可达 + 工具可用 + URL 签名有效。
        curl 和 wget 任意一个成功即返回 (True, '')；失败返回 (False, 具体原因)。

        :param ssh: 已建立的 paramiko.SSHClient
        :param minio_url: MinIO 预签名下载 URL（同分发使用的 URL）
        :param timeout: 探测超时秒数，默认 10
        :return: (可直连, 失败原因)
        """
        from app.common.commands import MINIO_URL_PROBE
        cmd = MINIO_URL_PROBE.format(url=minio_url, timeout=timeout)
        _, out, _ = ShellOperationUtils.execute_remote_command(ssh, cmd)
        lines = [l for l in (out or '').splitlines() if l.startswith('R:')]
        if not lines:
            logger.warning(f"MinIO 探测命令无输出 url={minio_url[:80]!r}")
            return False, "探测命令无输出"
        last = lines[-1]
        parts = last.split(':', 3)
        tool    = parts[1] if len(parts) > 1 else '?'
        code    = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
        detail  = parts[3].strip() if len(parts) > 3 else ''
        if code != 0:
            logger.warning(f"MinIO 探测失败 tool={tool} exit={code} reason={detail!r} url={minio_url[:80]!r}")
        return code == 0, detail

    # ---------- 共享分发单节点 - 方案A（压力机直拉 MinIO）----------
    @staticmethod
    def _share_distribute_direct(machine: PerfConfigMachineModel, minio_url: str, remote_dir: str,
                                  file_name: str, jump_host: str = None, jump_port: int = 22,
                                  master_ssh=None, credential: dict = None) -> DistributeNodeResultSchema:
        """
        【共享分发 - 方案A】压力机直接从 MinIO 下载完整文件。
        工具降级顺序：curl → wget（含 busybox）→ python3 urllib。
        全程文件内容不经过控制机，控制机仅发送一条 SSH 命令。
        """
        ssh = None
        try:
            try:
                ssh = ShellOperationUtils.get_ssh_client(
                    machine.ip, machine.name,
                    target_port=machine.ssh_port or 22, jump_host=jump_host, jump_port=jump_port,
                    reuse_master_ssh=master_ssh, credential=credential)
            except Exception as e:
                logger.exception(f"节点 {machine.ip} SSH 连接异常")
                return DistributeNodeResultSchema(machine_id=machine.id, machine_name=machine.name,
                    ip=machine.ip, success=False, message=str(e), failure_stage='connect')
            try:
                remote_dir = remote_dir.rstrip('/')
                remote_file = f"{remote_dir}/{file_name}"
                from app.common.commands import DOWNLOAD_FROM_URL
                cmd = DOWNLOAD_FROM_URL.format(
                    remote_dir=remote_dir,
                    remote_file=remote_file,
                    minio_url=minio_url,
                )
                exit_code, _, stderr = ShellOperationUtils.execute_remote_command(ssh, cmd)
                if exit_code == 0:
                    return DistributeNodeResultSchema(machine_id=machine.id, machine_name=machine.name,
                        ip=machine.ip, success=True, message="共享分发成功（直连MinIO）")
                err = stderr.strip()
                if _is_ssh_conn_error(exit_code, err):
                    return DistributeNodeResultSchema(machine_id=machine.id, machine_name=machine.name,
                        ip=machine.ip, success=False, message=f"SSH连接失败: {err}", failure_stage='connect')
                return DistributeNodeResultSchema(machine_id=machine.id, machine_name=machine.name,
                    ip=machine.ip, success=False, message=f"下载失败: {err}", failure_stage='transfer')
            except ConnectionError as e:
                logger.error(f"节点 {machine.ip} SSH中继连接失败: {e}")
                return DistributeNodeResultSchema(machine_id=machine.id, machine_name=machine.name,
                    ip=machine.ip, success=False, message=str(e), failure_stage='connect')
            except Exception as e:
                logger.exception(f"节点 {machine.ip} 直连MinIO分发异常")
                return DistributeNodeResultSchema(machine_id=machine.id, machine_name=machine.name,
                    ip=machine.ip, success=False, message=str(e), failure_stage='transfer')
        finally:
            if ssh:
                ssh.close()

    # ---------- 共享分发单节点 - 方案C（Master 拉取 MinIO 后 SCP 到 Slave）----------
    @staticmethod
    def _share_via_master_relay_single(
        machine: PerfConfigMachineModel,
        master_ssh,
        tmp_master_path: str,
        remote_dir: str,
        file_name: str,
        file_size: int,
        progress_callback=None,
    ) -> "DistributeNodeResultSchema":
        """
        【共享分发 - 方案C】Master 已从 MinIO 下载好文件到自身 /tmp，
        由 Master 执行 SCP 将文件推送到 Slave。
        通过在 Master 上轮询 Slave 端文件大小追踪传输进度。
        平台机全程不传输文件数据，只发出 SSH 命令。
        """
        from config import config as _cfg
        import base64 as _b64

        user = (credential or {}).get("ssh_user") or _cfg.SSH_DEFAULT_USER
        worker_ip = machine.ip
        worker_port = machine.ssh_port or 22
        remote_file = f"{remote_dir.rstrip('/')}/{file_name}"

        try:
            # 确保 Slave 目标目录存在（通过 Master relay ssh 命令）
            mkdir_cmd = f"mkdir -p '{remote_dir.rstrip('/')}'"
            encoded = _b64.b64encode(mkdir_cmd.encode()).decode("ascii")
            from app.common.commands import MKDIR_VIA_RELAY
            relay_mkdir = MKDIR_VIA_RELAY.format(
                worker_port=worker_port,
                ssh_user=user,
                worker_ip=worker_ip,
                encoded=encoded,
            )
            _, m_out, m_err = master_ssh.exec_command(relay_mkdir)
            mkdir_code = m_out.channel.recv_exit_status()
            if mkdir_code == 255:
                err = m_err.read().decode().strip()
                return DistributeNodeResultSchema(
                    machine_id=machine.id, machine_name=machine.name, ip=machine.ip,
                    success=False, message=f"SSH 连接失败（mkdir）: {err}", failure_stage="connect",
                )

            # Master SCP → Slave
            from app.common.commands import SCP_PUSH_TO_WORKER
            scp_cmd = SCP_PUSH_TO_WORKER.format(
                worker_port=worker_port,
                tmp_master_path=tmp_master_path,
                ssh_user=user,
                worker_ip=worker_ip,
                remote_file=remote_file,
            )
            _, scp_stdout, scp_stderr = master_ssh.exec_command(scp_cmd)

            # 每2秒轮询 Slave 端文件大小追踪 SCP 进度
            _last_pct = [-1]
            while not scp_stdout.channel.exit_status_ready():
                import time as _time
                _time.sleep(4)  # stat 只读 inode，开销极小；4s 兼顾实时性与 SSH channel 复用压力
                try:
                    poll_cmd = f"stat -c '%s' '{remote_file}' 2>/dev/null || echo 0"
                    p_encoded = _b64.b64encode(poll_cmd.encode()).decode("ascii")
                    from app.common.commands import POLL_FILESIZE_VIA_RELAY
                    relay_poll = POLL_FILESIZE_VIA_RELAY.format(
                        worker_port=worker_port,
                        ssh_user=user,
                        worker_ip=worker_ip,
                        p_encoded=p_encoded,
                    )
                    _, p_out, _ = master_ssh.exec_command(relay_poll)
                    p_out.channel.recv_exit_status()
                    current = int(p_out.read().decode().strip() or "0")
                    if file_size > 0:
                        pct = min(99, current * 100 // file_size)
                        if pct != _last_pct[0]:
                            _last_pct[0] = pct
                            if progress_callback:
                                progress_callback(pct)
                except Exception:
                    pass

            exit_code = scp_stdout.channel.recv_exit_status()
            err = scp_stderr.read().decode().strip()

            if exit_code == 0:
                if progress_callback:
                    progress_callback(100)
                return DistributeNodeResultSchema(
                    machine_id=machine.id, machine_name=machine.name, ip=machine.ip,
                    success=True, message="共享分发成功（Master 中转）",
                )
            if _is_ssh_conn_error(exit_code, err):
                return DistributeNodeResultSchema(
                    machine_id=machine.id, machine_name=machine.name, ip=machine.ip,
                    success=False, message=f"SSH 连接失败: {err}", failure_stage="connect",
                )
            return DistributeNodeResultSchema(
                machine_id=machine.id, machine_name=machine.name, ip=machine.ip,
                success=False, message=f"SCP 失败 (exit={exit_code}): {err}", failure_stage="transfer",
            )
        except Exception as e:
            logger.exception(f"节点 {machine.ip} 方案C分发异常")
            return DistributeNodeResultSchema(
                machine_id=machine.id, machine_name=machine.name, ip=machine.ip,
                success=False, message=str(e),
            )

    # ---------- 分割分发 ----------
    @staticmethod
    def _split_file_locally(source_path: str, parts: int) -> List[str]:
        """
        【分割分发步骤 1】将控制机本地文件按字节数等分为 parts 份。
        :param source_path: 待分割的本地文件完整路径
        :param parts: 分割份数（等于目标压力机数量）
        :return: 分片文件路径列表，长度等于 parts
        """
        file_size = os.path.getsize(source_path)
        # 分片文件大小
        chunk_size = file_size // parts
        # 剩余文件大小
        remainder = file_size % parts
        base_name = os.path.basename(source_path)
        dir_name = os.path.dirname(source_path)
        part_paths = []
        with open(source_path, "rb") as f:
            for i in range(parts):
                part_name = f"{base_name}.part{i}"
                part_path = os.path.join(dir_name, part_name)
                with open(part_path, "wb") as pf:
                    read_size = chunk_size + (remainder if i == parts - 1 else 0)
                    pf.write(f.read(read_size))
                part_paths.append(part_path)
        return part_paths

    @staticmethod
    def _split_distribute_single(machine: PerfConfigMachineModel, part_file_path: str, local_dir: str,
                                  original_name: str, jump_host: str = None, jump_port: int = 22,
                                  master_ssh=None, progress_callback=None,
                                  credential: dict = None, on_connected=None) -> DistributeNodeResultSchema:
        """
        【分割分发步骤 2】将单个分片文件通过 SFTP 上传至指定压力机，以原始文件名落盘。
        on_connected：SSH 连接成功后、SFTP 传输前调用，供上层独立推送连接成功事件。
        """
        ssh = None
        try:
            try:
                ssh = ShellOperationUtils.get_ssh_client(
                    machine.ip, machine.name,
                    target_port=machine.ssh_port or 22, jump_host=jump_host, jump_port=jump_port,
                    reuse_master_ssh=master_ssh, credential=credential)
            except Exception as e:
                logger.exception(f"节点 {machine.ip} SSH 连接异常")
                return DistributeNodeResultSchema(machine_id=machine.id, machine_name=machine.name,
                    ip=machine.ip, success=False, message=str(e), failure_stage='connect')
            # SSH 连接成功，通知上层（独立于 SFTP 进度）
            if on_connected:
                try:
                    on_connected()
                except Exception:
                    pass
            try:
                target_file = local_dir.rstrip('/') + '/' + original_name
                ShellOperationUtils.execute_remote_command(ssh, f"mkdir -p '{local_dir}'")
                ShellOperationUtils.upload_file_via_sftp(
                    ssh, part_file_path, target_file,
                    progress_label=f"{machine.name} {original_name}",
                    progress_callback=progress_callback,
                )
                return DistributeNodeResultSchema(machine_id=machine.id, machine_name=machine.name,
                    ip=machine.ip, success=True, message="分割分发成功")
            except ConnectionError as e:
                logger.error(f"节点 {machine.ip} SSH中继连接失败: {e}")
                return DistributeNodeResultSchema(machine_id=machine.id, machine_name=machine.name,
                    ip=machine.ip, success=False, message=str(e), failure_stage='connect')
            except Exception as e:
                logger.exception(f"节点 {machine.ip} 分割分发异常")
                return DistributeNodeResultSchema(machine_id=machine.id, machine_name=machine.name,
                    ip=machine.ip, success=False, message=str(e), failure_stage='transfer')
        finally:
            if ssh:
                ssh.close()

    @staticmethod
    def _clear_distribute_single(machine: PerfConfigMachineModel, local_dir: str, target_file: str,
                                  jump_host: str = None, jump_port: int = 22,
                                  master_ssh=None, progress_callback=None,
                                  credential: dict = None) \
            -> DistributeNodeResultSchema:
        """
        【清除分发】删除单台压力机上配置目录下的目标文件。
        进度阶段：SSH连接中(0) → 已连接(50) → 执行rm命令(90) → 完成由node_done表示
        """
        def _report(pct: int):
            if progress_callback:
                try:
                    progress_callback(pct)
                except Exception:
                    pass

        ssh = None
        try:
            try:
                ssh = ShellOperationUtils.get_ssh_client(
                    machine.ip, machine.name,
                    target_port=machine.ssh_port or 22, jump_host=jump_host, jump_port=jump_port,
                    reuse_master_ssh=master_ssh, credential=credential)
            except Exception as e:
                logger.exception(f"节点 {machine.ip} SSH 连接异常")
                return DistributeNodeResultSchema(machine_id=machine.id, machine_name=machine.name,
                    ip=machine.ip, success=False, message=str(e), failure_stage='connect')
            _report(50)  # SSH 连接成功（连接前不上报，避免轮询到 0% 时过早显示"已连接"）
            try:
                remote_dir = local_dir.rstrip('/')
                cmd = f"rm -f '{remote_dir}/{target_file}'"
                _report(90)
                exit_code, stdout, stderr = ShellOperationUtils.execute_remote_command(ssh, cmd)
                if exit_code == 0:
                    return DistributeNodeResultSchema(machine_id=machine.id, machine_name=machine.name,
                        ip=machine.ip, success=True, message="清除成功")
                err = stderr.strip()
                if _is_ssh_conn_error(exit_code, err):
                    return DistributeNodeResultSchema(machine_id=machine.id, machine_name=machine.name,
                        ip=machine.ip, success=False, message=f"SSH连接失败: {err}", failure_stage='connect')
                return DistributeNodeResultSchema(machine_id=machine.id, machine_name=machine.name,
                    ip=machine.ip, success=False, message=f"清除失败: {err}", failure_stage='transfer')
            except Exception as e:
                logger.exception(f"节点 {machine.ip} 清除异常")
                return DistributeNodeResultSchema(machine_id=machine.id, machine_name=machine.name,
                    ip=machine.ip, success=False, message=str(e), failure_stage='transfer')
        finally:
            if ssh:
                ssh.close()

    # ==================== 通用并发执行器 ====================
    @staticmethod
    def _run_concurrent_tasks(machines: List[PerfConfigMachineModel], task_func: callable, max_workers: int, **kwargs
    ) -> List[DistributeNodeResultSchema]:
        """
        通用并发任务执行器，使用线程池并行处理多台机器。

        :param machines: 压力机对象列表
        :param task_func: 单节点任务函数
        :param max_workers: 最大并发线程数
        :param kwargs: 传递给 task_func 的额外关键字参数
        :return: 所有节点的执行结果列表
        """
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_machine = {
                executor.submit(task_func, machine, **kwargs): machine
                for machine in machines
            }
            for future in as_completed(future_to_machine):
                machine = future_to_machine[future]
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error(f"节点 {machine.ip} 任务执行异常: {e}")
                    results.append(DistributeNodeResultSchema(machine_id=machine.id, machine_name=machine.name,
                            ip=machine.ip, success=False, message=str(e)))
        return results

    @staticmethod
    def _build_failure_remark(failed_results: List["DistributeNodeResultSchema"]) -> Optional[str]:
        """将失败节点信息格式化为备注字符串，每条占一行；无失败时返回 None（清空备注）。"""
        if not failed_results:
            return None
        return "\n".join(
            f"【{r.machine_id}】{r.machine_name}：{r.message}" for r in failed_results
        )

    # ==================== 共享分发 SSE 生成器 ====================
    async def share_distribute_stream(
        self, file_id: int, worker_count: int, user_id: int, machine_type: int = 2
    ) -> AsyncGenerator[str, None]:
        """
        【共享分发 SSE 生成器】逐步 yield SSE 格式事件字符串，供 StreamingResponse 消费。

        执行顺序：
          1. 校验文件 → yield start
          2. 获取可用压力机列表
          3. 读取系统参数 + 查询 Master 跳板机
          4. 若有 Master，测试 SSH 连接 → yield master 事件（失败则终止）；保留连接供后续复用
          5. yield node_pending：预推所有节点，前端提前渲染等待行
          6. 探测第1台机器能否直连 MinIO → yield method（方案A/B）；复用 Master 连接
          7. 方案A：并发 SSH 指令让压力机直拉 MinIO
             方案B：Master 先从 MinIO 拉取文件，再并发 SCP 到各 Slave
          8. 每台机器完成后立即 yield node_done（asyncio.wait FIRST_COMPLETED）
          9. 更新数据库 dist_status=1 → yield done
        """
        def evt(data: dict) -> str:
            return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        master_ssh_shared = None  # 整个分发流程共享的 Master SSH 连接
        try:
            # ── 1. 校验文件 ──
            yield evt({"type": "start", "message": "正在校验文件..."})
            file_record = await self.file_curd.get_by_id_crud(file_id)
            if not file_record or not file_record.enabled_flag:
                logger.warning(f"共享分发 file_id={file_id}: 文件不存在或已禁用")
                yield evt({"type": "error", "message": f"文件 ID {file_id} 不存在"})
                return
            if file_record.upload_status != 1:
                err_msg = "文件尚未上传完成，无法分发"
                logger.warning(f"共享分发 file_id={file_id}: {err_msg}")
                await self.file_curd.update_crud(file_id, {"remark": err_msg})
                yield evt({"type": "error", "message": err_msg})
                return

            # ── 2. 获取可用压力机 ──
            machines = await self.machine_crud.get_available_machines(limit=worker_count, machine_type=machine_type)
            if len(machines) < worker_count:
                err_msg = f"可用压力机不足，需要 {worker_count} 台，实际只有 {len(machines)} 台"
                logger.warning(f"共享分发 file_id={file_id}: {err_msg}")
                await self.file_curd.update_crud(file_id, {"remark": err_msg})
                yield evt({"type": "error", "message": err_msg})
                return

            # ── 3. 系统参数 + Master 跳板机（仅分布式模式需要） ──
            local_dir    = await self.param_crud.get_param_value(self.worker_data_dir[0], self.worker_data_dir[1])
            sys_max      = int(await self.param_crud.get_param_value("SHARE_DIST_MAX_WORKERS", "10"))
            ctrl_bw_mbps = _parse_mbps(await self.param_crud.get_param_value("CTRL_BANDWIDTH_MBPS", "500"))
            master       = await self.machine_crud.get_master_machine() if machine_type == 2 else None
            jump_host    = master.ip if master else None
            jump_port    = (master.ssh_port or 22) if master else 22

            # ── 4. 测试 Master SSH 连接，保留连接供后续复用 ──
            if master:
                from config import config as _cfg
                _kp = _cfg.PLATFORM_SSH_KEY_PATH
                auth_method = "key" if _kp and os.path.exists(_kp) else "password"
                yield evt({"type": "master", "status": "connecting",
                           "name": master.name, "ip": master.ip, "message": "正在连接 Master...",
                           "auth_method": auth_method})
                master_credential = _build_credential(master)
                try:
                    master_ssh_shared = await asyncio.to_thread(
                        ShellOperationUtils.get_ssh_client,
                        master.ip, master.name, 2, 1.0, None, 22, master.ssh_port or 22,
                        credential=master_credential,
                    )
                    yield evt({"type": "master", "status": "success",
                               "name": master.name, "ip": master.ip, "message": "Master 连接成功",
                               "auth_method": auth_method})
                except Exception as e:
                    err_msg = f"Master 连接失败: {e}"
                    logger.error(f"共享分发 file_id={file_id}: {err_msg}")
                    await self.file_curd.update_crud(file_id, {"remark": err_msg})
                    yield evt({"type": "master", "status": "failed",
                               "name": master.name, "ip": master.ip, "message": err_msg,
                               "auth_method": auth_method})
                    return

            # ── 5. 预推所有节点等待行，让前端提前渲染 ──
            for m in machines:
                yield evt({"type": "node_pending", "machine_id": m.id, "name": m.name, "ip": m.ip})

            # ── 6. 获取文件信息 + MinIO 预签名 URL ──
            bucket, object_key = file_record.bucket, file_record.object_key
            file_size = file_record.file_size or 0
            minio_url = MinioClient.presign_get(bucket, object_key, 60)

            # ── 7. 探测 MinIO 连通性，决定方案A/B；复用 master_ssh_shared，不额外握手 ──
            use_direct = False
            use_master_relay = False
            tunnel_type = "unknown"
            probe_detail = ""  # 探测失败原因，用于备注和日志
            worker_credential = _build_credential(machines[0]) if machines else None
            try:
                probe_ssh = await asyncio.wait_for(
                    asyncio.to_thread(
                        ShellOperationUtils.get_ssh_client,
                        machines[0].ip, machines[0].name, 2, 1.0,
                        jump_host, jump_port, machines[0].ssh_port or 22,
                        reuse_master_ssh=master_ssh_shared,
                        credential=worker_credential,
                    ),
                    timeout=8.0,
                )
                try:
                    from app.utils.oper_shell import _RelayClient as _RC
                    tunnel_type = "ssh_relay" if isinstance(probe_ssh, _RC) else "direct_tcpip"
                    use_direct, probe_detail = await asyncio.wait_for(
                        asyncio.to_thread(self._probe_minio_reachable, probe_ssh, minio_url),
                        timeout=25.0,
                    )
                except asyncio.TimeoutError:
                    probe_detail = "连通性探测超时（>25s）"
                    logger.warning("MinIO 连通性探测超时，回退方案B（Master中转）")
                finally:
                    probe_ssh.close()
            except (Exception, asyncio.TimeoutError) as e:
                probe_detail = str(e)
                logger.warning(f"MinIO 连通性探测失败，回退方案B（Master中转）: {e}")

            # 若 Slave 无法直连 MinIO，进一步探测 Master 是否能访问 MinIO（方案B）
            if not use_direct and master_ssh_shared:
                try:
                    use_master_relay, _ = await asyncio.wait_for(
                        asyncio.to_thread(self._probe_minio_reachable, master_ssh_shared, minio_url),
                        timeout=15.0,
                    )
                except (Exception, asyncio.TimeoutError) as e:
                    logger.warning(f"Master MinIO 连通性探测失败: {e}")

            if use_direct:
                method_label = "方案A：直拉 MinIO" if machine_type == 3 else "方案A：Slave 直拉 MinIO"
            elif use_master_relay:
                method_label = "方案B：Master 中转 MinIO"
            elif machine_type == 3:
                method_label = "方案C：平台机中转 SFTP"
            else:
                method_label = "无法分发：Slave 和 Master 均无法访问 MinIO"
            yield evt({"type": "method", "use_direct": use_direct, "use_master_relay": use_master_relay,
                       "tunnel_type": tunnel_type, "message": method_label})

            # ── 8. 并发分发：每台机器完成立即 yield node_done ──
            results: List[DistributeNodeResultSchema] = []
            # 各节点上传进度（线程写/asyncio读，GIL保证简单int赋值的原子性）
            machine_progress: dict = {m.id: 0 for m in machines}
            # 各节点当前操作阶段
            machine_stage: dict = {m.id: "transferring" for m in machines}

            def make_progress_cb(machine_id: int, stage: str = "transferring"):
                def cb(pct: int):
                    machine_progress[machine_id] = pct
                    machine_stage[machine_id] = stage
                return cb

            async def _run_and_stream(fn, use_progress: bool = False,
                                      _stage: str = "transferring", max_workers: int = 0, **kwargs):
                """内部异步生成器：为每台机器创建 to_thread 任务，FIRST_COMPLETED 实时推送。
                :param _stage: 进度回调使用的阶段标签，统一在此提取避免 dict comprehension 中 pop 变异
                :param max_workers: 最大并发数（Semaphore），0 表示不限制
                """
                sem = asyncio.Semaphore(max_workers) if max_workers > 0 else None

                async def _guarded(m):
                    extra = {"progress_callback": make_progress_cb(m.id, _stage)} if use_progress else {}
                    if sem:
                        async with sem:
                            return await asyncio.to_thread(fn, m, **extra, **kwargs)
                    return await asyncio.to_thread(fn, m, **extra, **kwargs)

                task_map = {asyncio.ensure_future(_guarded(m)): m for m in machines}
                pending = set(task_map.keys())
                while pending:
                    done_set, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED, timeout=10.0)
                    if not done_set:
                        if use_progress:
                            for t in pending:
                                m = task_map[t]
                                yield evt({"type": "node_progress", "machine_id": m.id, "name": m.name,
                                           "ip": m.ip, "progress": machine_progress.get(m.id, 0),
                                           "stage": machine_stage.get(m.id, "transferring")})
                        else:
                            yield evt({"type": "progress",
                                       "message": f"文件传输中，请耐心等待... (剩余 {len(pending)} 台)"})
                        continue
                    for fut in done_set:
                        m = task_map[fut]
                        try:
                            r: DistributeNodeResultSchema = fut.result()
                        except Exception as ex:
                            logger.error(f"节点 {m.ip} 执行异常: {ex}")
                            r = DistributeNodeResultSchema(
                                machine_id=m.id, machine_name=m.name, ip=m.ip, success=False, message=str(ex))
                        results.append(r)
                        yield evt({"type": "node_done", "machine_id": r.machine_id,
                                   "name": r.machine_name, "ip": r.ip,
                                   "success": r.success, "message": r.message,
                                   "failure_stage": r.failure_stage})

            if use_direct:
                max_w = min(sys_max, len(machines))
                logger.info(f"共享分发[方案A] 文件={file_record.file_name} 并发={max_w}")
                async for chunk in _run_and_stream(
                    self._share_distribute_direct, use_progress=False, max_workers=max_w,
                    minio_url=minio_url, remote_dir=local_dir,
                    file_name=file_record.file_name, jump_host=jump_host, jump_port=jump_port,
                    master_ssh=master_ssh_shared, credential=worker_credential,
                ):
                    yield chunk

            elif use_master_relay:
                # 方案B：Master 先从 MinIO 拉文件，再并发 SCP 到各 Slave
                import uuid as _uuid, operator as _op
                tmp_master_path = f"/tmp/.ntdist_{_uuid.uuid4().hex}_{os.path.basename(object_key)}"
                master_dl_pct = [0]

                def _dl_cb(pct: int):
                    master_dl_pct[0] = pct

                logger.info(f"共享分发[方案B] 文件={file_record.file_name} Slaves={len(machines)}")
                # 子阶段1：Master 拉取 MinIO 文件
                yield evt({"type": "progress", "stage": "master_pull", "progress": 0,
                           "message": f"Master 正在从 MinIO 拉取文件（{format_file_size(file_size)}）..."})
                _dl_task = asyncio.ensure_future(asyncio.to_thread(
                    ShellOperationUtils.master_download_from_minio,
                    master_ssh_shared, minio_url, tmp_master_path, file_size, _dl_cb,
                ))
                while not _dl_task.done():
                    _done, _ = await asyncio.wait([_dl_task], timeout=3.0)
                    if not _done:
                        yield evt({"type": "progress", "stage": "master_pull",
                                   "progress": master_dl_pct[0],
                                   "message": f"Master 正在拉取 MinIO 文件 {master_dl_pct[0]}%..."})
                dl_exit = await _dl_task
                if dl_exit != 0:
                    err_msg = f"Master 从 MinIO 拉取文件失败（exit={dl_exit}）"
                    logger.error(f"共享分发[方案B] file_id={file_id}: {err_msg}")
                    await self.file_curd.update_crud(file_id, {"remark": err_msg})
                    yield evt({"type": "error", "message": err_msg})
                    return
                yield evt({"type": "progress", "stage": "master_pull", "progress": 100,
                           "message": "Master 拉取完成，开始向 Slave 分发..."})

                # 子阶段2：Master 并发 SCP 到各 Slave
                try:
                    max_w = min(sys_max, len(machines))
                    logger.info(f"共享分发[方案B] Master SCP 并发={max_w}")
                    async for chunk in _run_and_stream(
                        self._share_via_master_relay_single, use_progress=True,
                        _stage="master_pushing", max_workers=max_w,
                        master_ssh=master_ssh_shared,
                        tmp_master_path=tmp_master_path,
                        remote_dir=local_dir, file_name=file_record.file_name,
                        file_size=file_size,
                    ):
                        yield chunk
                finally:
                    # 清理 Master 临时文件（忽略错误）
                    try:
                        master_ssh_shared.exec_command(f"rm -f '{tmp_master_path}'")
                    except Exception:
                        pass

            elif machine_type == 3:
                # 方案C：单机模式 — 平台机从 MinIO 下载后 SFTP 中转，绕过 CloudFlare 对预签名 URL 的拦截
                logger.info(f"共享分发[方案C-单机中转] 文件={file_record.file_name}")
                with tempfile.TemporaryDirectory() as tmpdir:
                    local_file = os.path.join(tmpdir, os.path.basename(object_key))

                    # ① 阶段1：连接 MinIO
                    yield evt({"type": "progress", "stage": "minio_connect",
                               "message": f"正在连接 MinIO，准备下载文件（{format_file_size(file_size)}）..."})
                    _dl_task = asyncio.ensure_future(asyncio.to_thread(
                        _download_url_to_file, minio_url, local_file
                    ))

                    # ② 阶段2：MinIO 下载进度（每 3 秒轮询本地文件大小计算百分比）
                    while not _dl_task.done():
                        _done, _ = await asyncio.wait([_dl_task], timeout=3.0)
                        if not _done:
                            downloaded = os.path.getsize(local_file) if os.path.exists(local_file) else 0
                            pct = min(int(downloaded / file_size * 100), 99) if file_size > 0 else 0
                            yield evt({"type": "progress", "stage": "minio_download",
                                       "progress": pct,
                                       "message": f"正在从 MinIO 下载文件 {pct}%（{format_file_size(downloaded)} / {format_file_size(file_size)}）"})
                    await _dl_task
                    yield evt({"type": "progress", "stage": "minio_download", "progress": 100,
                               "message": "MinIO 文件下载完成，开始向单机压力机分发..."})

                    machine = machines[0]
                    node_progress   = [0]
                    _node_connected = [False]   # SSH 连通标志（线程写，asyncio读）
                    _ssh_evt_sent   = [False]   # 已推送 SSH 连通事件

                    def _node_progress_cb(pct: int):
                        node_progress[0] = pct

                    def _on_ssh_connected():
                        _node_connected[0] = True

                    _sftp_task = asyncio.ensure_future(asyncio.to_thread(
                        self._split_distribute_single,
                        machine, local_file, local_dir, file_record.file_name,
                        None, 22, None, _node_progress_cb, worker_credential, _on_ssh_connected,
                    ))
                    while not _sftp_task.done():
                        _done, _ = await asyncio.wait([_sftp_task], timeout=3.0)
                        if not _done:
                            # SSH 刚连通：独立推送连接成功事件（进度仍为 0）
                            if _node_connected[0] and not _ssh_evt_sent[0]:
                                _ssh_evt_sent[0] = True
                                yield evt({"type": "node_progress", "machine_id": machine.id,
                                           "name": machine.name, "ip": machine.ip,
                                           "progress": 0, "stage": "sftp_start"})
                            else:
                                yield evt({"type": "node_progress", "machine_id": machine.id,
                                           "name": machine.name, "ip": machine.ip,
                                           "progress": node_progress[0], "stage": "master_pushing"})
                    r: DistributeNodeResultSchema = await _sftp_task
                    if r.success:
                        r = DistributeNodeResultSchema(
                            machine_id=r.machine_id, machine_name=r.machine_name, ip=r.ip,
                            success=True, message="共享分发成功（平台机中转）",
                        )
                    results.append(r)
                    yield evt({"type": "node_done", "machine_id": r.machine_id,
                               "name": r.machine_name, "ip": r.ip, "success": r.success,
                               "message": r.message, "failure_stage": r.failure_stage})

            else:
                reason_hint = f"（{probe_detail}）" if probe_detail else ""
                if "403" in probe_detail:
                    reason_hint += "，MinIO 凭证缺少 s3:GetObject 权限，请在 MinIO 控制台补充授权"
                err_msg = f"共享分发失败：Slave 和 Master 均无法访问 MinIO{reason_hint}，请检查网络连通性或 MinIO 地址配置"
                yield evt({"type": "error", "message": err_msg})
                await self.file_curd.update_crud(file_id, {"remark": err_msg})
                return

            # ── 9. 更新数据库 + 推送汇总事件 ──
            success_count  = sum(1 for r in results if r.success)
            failed_results = [r for r in results if not r.success]
            update_data: dict = {"remark": self._build_failure_remark(failed_results)}
            if success_count > 0:
                update_data.update({
                    "dist_status": 1,
                    "dist_worker_ids": [r.machine_id for r in results if r.success],
                    "dist_time": get_current_time_str(),
                })
            await self.file_curd.update_crud(file_id, update_data)
            yield evt({"type": "done", "success_count": success_count,
                       "failed_count": len(machines) - success_count, "dist_status": 1})

        except Exception as e:
            logger.exception("共享分发 SSE 生成器异常")
            try:
                await self.file_curd.update_crud(file_id, {"remark": f"分发异常: {e}"})
            except Exception:
                pass
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            if master_ssh_shared:
                try:
                    master_ssh_shared.close()
                except Exception:
                    pass

    # ==================== 分割分发 SSE 生成器 ====================
    async def split_distribute_stream(
        self, file_id: int, worker_count: int, user_id: int, machine_type: int = 2
    ) -> AsyncGenerator[str, None]:
        """
        【分割分发 SSE 生成器】逐步 yield SSE 格式事件字符串，供 StreamingResponse 消费。

        执行顺序：
          1. 校验文件 → yield start
          2. 获取可用压力机列表
          3. 查询 Master 跳板机 + 系统参数
          4. 若有 Master，测试 SSH 连接 → yield master 事件（失败则终止）；保留连接供后续复用
          5. yield node_pending：预推所有节点等待行
          6. 从 MinIO 下载完整文件到控制机临时目录
          7. 本地等分切割文件为 N 份（N = 压力机数量）
          8. 每台机器上传对应分片，完成立即 yield node_done
          9. 更新数据库 dist_status=2 → yield done
        """
        def evt(data: dict) -> str:
            return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        master_ssh_shared = None
        try:
            # ── 1. 校验文件 ──
            yield evt({"type": "start", "message": "正在校验文件..."})
            file_record = await self.file_curd.get_by_id_crud(file_id)
            if not file_record or not file_record.enabled_flag:
                logger.warning(f"分割分发 file_id={file_id}: 文件不存在或已禁用")
                yield evt({"type": "error", "message": f"文件 ID {file_id} 不存在"})
                return
            if file_record.upload_status != 1:
                err_msg = "文件尚未上传完成，无法分发"
                logger.warning(f"分割分发 file_id={file_id}: {err_msg}")
                await self.file_curd.update_crud(file_id, {"remark": err_msg})
                yield evt({"type": "error", "message": err_msg})
                return

            # ── 2. 获取可用压力机 ──
            machines = await self.machine_crud.get_available_machines(limit=worker_count, machine_type=machine_type)
            if len(machines) < worker_count:
                err_msg = f"可用压力机不足，需要 {worker_count} 台，实际只有 {len(machines)} 台"
                logger.warning(f"分割分发 file_id={file_id}: {err_msg}")
                await self.file_curd.update_crud(file_id, {"remark": err_msg})
                yield evt({"type": "error", "message": err_msg})
                return

            # ── 3. 系统参数 + Master 跳板机（仅分布式模式需要） ──
            local_dir = await self.param_crud.get_param_value(self.worker_data_dir[0], self.worker_data_dir[1])
            master    = await self.machine_crud.get_master_machine() if machine_type == 2 else None
            jump_host = master.ip if master else None
            jump_port = (master.ssh_port or 22) if master else 22
            bucket, object_key = file_record.bucket, file_record.object_key
            file_size = file_record.file_size or 0
            minio_url = MinioClient.presign_get(bucket, object_key, 60)

            # ── 4. 测试 Master SSH 连接，保留连接供后续复用 ──
            if master:
                from config import config as _cfg
                _kp = _cfg.PLATFORM_SSH_KEY_PATH
                auth_method = "key" if _kp and os.path.exists(_kp) else "password"
                yield evt({"type": "master", "status": "connecting",
                           "name": master.name, "ip": master.ip, "message": "正在连接 Master...",
                           "auth_method": auth_method})
                master_credential = _build_credential(master)
                try:
                    master_ssh_shared = await asyncio.to_thread(
                        ShellOperationUtils.get_ssh_client,
                        master.ip, master.name, 2, 1.0, None, 22, master.ssh_port or 22,
                        credential=master_credential,
                    )
                    yield evt({"type": "master", "status": "success",
                               "name": master.name, "ip": master.ip, "message": "Master 连接成功",
                               "auth_method": auth_method})
                except Exception as e:
                    err_msg = f"Master 连接失败: {e}"
                    logger.error(f"分割分发 file_id={file_id}: {err_msg}")
                    await self.file_curd.update_crud(file_id, {"remark": err_msg})
                    yield evt({"type": "master", "status": "failed",
                               "name": master.name, "ip": master.ip, "message": err_msg,
                               "auth_method": auth_method})
                    return

            # ── 5. 预推所有节点等待行，附带各节点分配的文件大小 ──
            chunk_size = file_size // len(machines)
            remainder  = file_size % len(machines)
            for i, m in enumerate(machines):
                node_bytes = chunk_size + (remainder if i == len(machines) - 1 else 0)
                yield evt({"type": "node_pending", "machine_id": m.id, "name": m.name, "ip": m.ip,
                           "chunk_size": format_file_size(node_bytes)})

            # ── 5.5 探测隧道类型；复用 master_ssh_shared，不额外握手 ──
            tunnel_type = "unknown"
            worker_credential = _build_credential(machines[0]) if machines else None
            if jump_host and machines:
                try:
                    probe_w = await asyncio.wait_for(
                        asyncio.to_thread(
                            ShellOperationUtils.get_ssh_client,
                            machines[0].ip, machines[0].name, 1, 1.0,
                            jump_host, jump_port, machines[0].ssh_port or 22,
                            reuse_master_ssh=master_ssh_shared,
                            credential=worker_credential,
                        ),
                        timeout=8.0,
                    )
                    from app.utils.oper_shell import _RelayClient as _RC
                    tunnel_type = "ssh_relay" if isinstance(probe_w, _RC) else "direct_tcpip"
                    probe_w.close()
                except (Exception, asyncio.TimeoutError) as e:
                    logger.warning(f"分割分发：隧道探测失败: {e}")
            yield evt({"type": "method", "use_direct": False, "tunnel_type": tunnel_type,
                       "message": "分割分发（平台机中转 SFTP）"})

            # ── 6. 下载完整文件 + 等分切割 ──
            max_chunk_sz = chunk_size + remainder
            max_w        = self._calculate_max_workers(len(machines), max_chunk_sz)

            results: List[DistributeNodeResultSchema] = []
            with tempfile.TemporaryDirectory() as tmpdir:
                local_file = os.path.join(tmpdir, os.path.basename(object_key))
                yield evt({"type": "progress", "message": f"正在从 MinIO 下载文件到控制机（{format_file_size(file_size)}）..."})
                _dl_task = asyncio.ensure_future(asyncio.to_thread(
                    _download_url_to_file, minio_url, local_file
                ))
                while not _dl_task.done():
                    _done, _ = await asyncio.wait([_dl_task], timeout=15.0)
                    if not _done:
                        yield evt({"type": "progress", "message": "正在从 MinIO 下载文件，请耐心等待..."})
                await _dl_task
                logger.info(f"分割分发：文件已下载至临时目录: {local_file}")
                yield evt({"type": "progress", "message": "文件下载完成，开始切分并分发..."})

                # ── 7. 等分切割 ──
                part_files = self._split_file_locally(local_file, len(machines))
                logger.info(f"分割分发：文件已分割为 {len(part_files)} 份")

                # ── 8. 并发上传分片，完成立即推送 ──
                original_name = file_record.file_name
                machine_part_pairs = list(zip(machines, part_files))
                # 各节点进度字典（线程写/asyncio读，GIL保证原子性）
                split_progress: dict = {m.id: 0 for m in machines}
                split_stage: dict = {m.id: "master_pushing" for m in machines}

                def make_split_progress_cb(machine_id: int):
                    def cb(pct: int):
                        split_progress[machine_id] = pct
                        split_stage[machine_id] = "master_pushing"
                    return cb

                task_map = {
                    asyncio.ensure_future(
                        asyncio.to_thread(
                            self._split_distribute_single,
                            m, part_path, local_dir, original_name, jump_host, jump_port,
                            master_ssh_shared, make_split_progress_cb(m.id),
                            worker_credential,
                        )
                    ): m
                    for m, part_path in machine_part_pairs
                }
                pending = set(task_map.keys())
                while pending:
                    done_set, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED, timeout=10.0)
                    if not done_set:
                        for t in pending:
                            m = task_map[t]
                            yield evt({"type": "node_progress", "machine_id": m.id, "name": m.name,
                                       "ip": m.ip, "progress": split_progress.get(m.id, 0),
                                       "stage": split_stage.get(m.id, "master_pushing")})
                        continue
                    for fut in done_set:
                        m = task_map[fut]
                        try:
                            r: DistributeNodeResultSchema = fut.result()
                        except Exception as ex:
                            logger.error(f"节点 {m.ip} 分割分发异常: {ex}")
                            r = DistributeNodeResultSchema(
                                machine_id=m.id, machine_name=m.name, ip=m.ip, success=False, message=str(ex))
                        results.append(r)
                        yield evt({"type": "node_done", "machine_id": r.machine_id,
                                   "name": r.machine_name, "ip": r.ip,
                                   "success": r.success, "message": r.message,
                                   "failure_stage": r.failure_stage})

            # ── 9. 更新数据库 + 推送汇总事件 ──
            success_count  = sum(1 for r in results if r.success)
            failed_results = [r for r in results if not r.success]
            update_data: dict = {"remark": self._build_failure_remark(failed_results)}
            if success_count > 0:
                update_data.update({
                    "dist_status": 2,
                    "dist_worker_ids": [r.machine_id for r in results if r.success],
                    "dist_time": get_current_time_str(),
                })
            await self.file_curd.update_crud(file_id, update_data)
            yield evt({"type": "done", "success_count": success_count,
                       "failed_count": len(machines) - success_count, "dist_status": 2})

        except Exception as e:
            logger.exception("分割分发 SSE 生成器异常")
            try:
                await self.file_curd.update_crud(file_id, {"remark": f"分发异常: {e}"})
            except Exception:
                pass
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            if master_ssh_shared:
                try:
                    master_ssh_shared.close()
                except Exception:
                    pass

    # ==================== 清除分发 SSE 生成器 ====================
    async def clear_distribute_stream(self, file_id: int, worker_count: int = 0) -> AsyncGenerator[str, None]:
        """
        【清除分发 SSE 生成器】实时推送各压力机清除进度。

        执行顺序：
          1. 校验文件 → yield start
          2. 从 dist_worker_ids 获取压力机列表（worker_count>0 则只取前 N 台）
          3. 测试 Master SSH，保留连接供后续复用 → yield master 事件
          4. 探测隧道类型 → yield method 事件；复用 Master 连接
          5. yield node_pending
          6. 并发 rm -f → yield node_done
          7. 更新数据库 → yield done
        """
        def evt(data: dict) -> str:
            return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        master_ssh_shared = None
        try:
            yield evt({"type": "start", "message": "正在校验文件..."})
            file_record = await self.file_curd.get_by_id_crud(file_id)
            if not file_record or not file_record.enabled_flag:
                yield evt({"type": "error", "message": f"文件 ID {file_id} 不存在"})
                return

            worker_ids = file_record.dist_worker_ids or []
            if not worker_ids:
                yield evt({"type": "error", "message": "该文件尚未分发到任何压力机，无需清除"})
                return

            machines = await self.machine_crud.get_machines_by_ids(worker_ids)
            if not machines:
                yield evt({"type": "error", "message": "记录的压力机均不可用，无法执行清除"})
                return

            if worker_count > 0:
                machines = machines[:worker_count]

            local_dir = await self.param_crud.get_param_value(self.worker_data_dir[0], self.worker_data_dir[1])
            # 单机压力机（machine_type=3）直连，不需要 Master 跳板
            all_standalone = all(getattr(m, 'machine_type', 2) == 3 for m in machines)
            master    = await self.machine_crud.get_master_machine() if not all_standalone else None
            jump_host = master.ip if master else None
            jump_port = (master.ssh_port or 22) if master else 22

            from config import config as _cfg
            _kp = _cfg.PLATFORM_SSH_KEY_PATH
            auth_method = "key" if _kp and os.path.exists(_kp) else "password"
            master_credential = _build_credential(master) if master else None

            if master:
                yield evt({"type": "master", "status": "connecting",
                           "name": master.name, "ip": master.ip,
                           "message": "正在连接 Master...", "auth_method": auth_method})
                try:
                    master_ssh_shared = await asyncio.to_thread(
                        ShellOperationUtils.get_ssh_client,
                        master.ip, master.name, 2, 1.0, None, 22, master.ssh_port or 22,
                        credential=master_credential,
                    )
                    yield evt({"type": "master", "status": "success",
                               "name": master.name, "ip": master.ip,
                               "message": "Master 连接成功", "auth_method": auth_method})
                except Exception as e:
                    yield evt({"type": "master", "status": "failed",
                               "name": master.name, "ip": master.ip,
                               "message": f"Master 连接失败: {e}", "auth_method": auth_method})
                    return

            # ── 先推 node_pending，让前端立即看到等待行 ──
            for m in machines:
                yield evt({"type": "node_pending", "machine_id": m.id, "name": m.name, "ip": m.ip})

            # ── 隧道类型探测；复用 master_ssh_shared，不额外握手 ──
            tunnel_type = "unknown"
            worker_credential = _build_credential(machines[0]) if machines else None
            if jump_host and machines:
                try:
                    probe_w = await asyncio.wait_for(
                        asyncio.to_thread(
                            ShellOperationUtils.get_ssh_client,
                            machines[0].ip, machines[0].name, 1, 1.0,
                            jump_host, jump_port, machines[0].ssh_port or 22,
                            reuse_master_ssh=master_ssh_shared,
                            credential=worker_credential,
                        ),
                        timeout=8.0,
                    )
                    from app.utils.oper_shell import _RelayClient as _RC
                    tunnel_type = "ssh_relay" if isinstance(probe_w, _RC) else "direct_tcpip"
                    probe_w.close()
                except (Exception, asyncio.TimeoutError) as e:
                    logger.warning(f"清除分发：隧道探测失败: {e}")

            method_label = "SSH Relay 隧道" if tunnel_type == "ssh_relay" else "直连" if tunnel_type == "direct_tcpip" else "直连"
            yield evt({"type": "method", "use_direct": False, "tunnel_type": tunnel_type,
                       "message": f"清除分发（{method_label}）"})

            target_file = file_record.file_name
            results: List[DistributeNodeResultSchema] = []
            # 各节点清除进度百分比（线程写，asyncio读）
            clear_progress: dict = {m.id: 0 for m in machines}

            def make_clear_progress_cb(machine_id: int):
                def cb(pct: int):
                    clear_progress[machine_id] = pct
                return cb

            task_map = {
                asyncio.ensure_future(
                    asyncio.to_thread(
                        self._clear_distribute_single, m,
                        local_dir=local_dir, target_file=target_file,
                        jump_host=jump_host, jump_port=jump_port,
                        master_ssh=master_ssh_shared,
                        progress_callback=make_clear_progress_cb(m.id),
                        credential=worker_credential,
                    )
                ): m
                for m in machines
            }
            pending_set = set(task_map.keys())
            while pending_set:
                done_set, pending_set = await asyncio.wait(pending_set, return_when=asyncio.FIRST_COMPLETED, timeout=3.0)
                if not done_set:
                    # 超时未完成，推送各节点当前进度
                    for t in pending_set:
                        m = task_map[t]
                        yield evt({"type": "node_progress", "machine_id": m.id,
                                   "name": m.name, "ip": m.ip,
                                   "progress": clear_progress.get(m.id, 0)})
                    continue
                for fut in done_set:
                    m = task_map[fut]
                    try:
                        r: DistributeNodeResultSchema = fut.result()
                    except Exception as ex:
                        logger.error(f"节点 {m.ip} 清除异常: {ex}")
                        r = DistributeNodeResultSchema(
                            machine_id=m.id, machine_name=m.name, ip=m.ip, success=False, message=str(ex),
                            failure_stage='connect')
                    results.append(r)
                    yield evt({"type": "node_done", "machine_id": r.machine_id,
                               "name": r.machine_name, "ip": r.ip,
                               "success": r.success, "message": r.message,
                               "failure_stage": r.failure_stage})

            success_count  = sum(1 for r in results if r.success)
            failed_results = [r for r in results if not r.success]
            failed_ids     = [r.machine_id for r in failed_results]

            update_data: dict = {"remark": self._build_failure_remark(failed_results)}
            if not failed_ids:
                update_data.update({"dist_status": 0, "dist_worker_ids": [], "dist_time": None})
            else:
                update_data["dist_worker_ids"] = failed_ids

            if success_count > 0 or failed_ids:
                await self.file_curd.update_crud(file_id, update_data)

            yield evt({"type": "done", "success_count": success_count,
                       "failed_count": len(machines) - success_count, "dist_status": 0})

        except Exception as e:
            logger.exception("清除分发 SSE 生成器异常")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            if master_ssh_shared:
                try:
                    master_ssh_shared.close()
                except Exception:
                    pass