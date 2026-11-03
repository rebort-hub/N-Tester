#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
import asyncio
import io
from datetime import timedelta
from typing import Optional

import urllib3
from loguru import logger
from minio import Minio
from minio.error import S3Error

from app.utils.common import fmt_cloudflare_html_resp


class MinioClient:
    """
    #======================================================================================
    MinIO 客户端封装（单例）
    - 将同步 minio-py SDK 包装为异步接口，与 FastAPI 异步上下文兼容。
    - 所有 IO 操作通过 asyncio.run_in_executor 在线程池中执行。
    - 通过 get_client() 获取 Minio 实例，全进程共享一个连接池。
    - MinIO 公网访问经 Cloudflare 代理转发，中间代理可能在空闲一段时间后静默
      断开连接（不发 FIN/RST），复用到失效连接会导致读超时；因此显式配置有
      界超时（而非 SDK 默认的宽松超时），并在 get_object_bytes 失败时重建连
      接池重试一次，覆盖"真实网络故障"与"连接池复用到失效连接"两种情况。
    #======================================================================================
    """
    _client: Optional[Minio] = None

    # 控制机 → MinIO(Cloudflare代理) 的连接/读超时（秒），避免代理端静默断开
    # 连接时长时间挂起等待读超时才报错
    _CONNECT_TIMEOUT = 10
    _READ_TIMEOUT = 20

    # ------------------------------------------------------------------ #
    #                       初始化客户端
    # ------------------------------------------------------------------ #
    @classmethod
    def get_client(cls) -> Minio:
        """获取 Minio 客户端单例（懒加载，读 config.py 中的 MINIO_* 配置）。"""
        if cls._client is None:
            from app.config.setting import config
            http_client = urllib3.PoolManager(
                timeout=urllib3.Timeout(connect=cls._CONNECT_TIMEOUT, read=cls._READ_TIMEOUT),
                retries=urllib3.Retry(total=1, backoff_factor=0.2),
            )
            cls._client = Minio(endpoint=config.MINIO_ENDPOINT, access_key=config.MINIO_ACCESS_KEY,
                                secret_key=config.MINIO_SECRET_KEY, secure=config.MINIO_SECURE,
                                http_client=http_client,)
            logger.info(f"MinIO 客户端初始化完成，endpoint={config.MINIO_ENDPOINT}")
        return cls._client

    @classmethod
    async def ensure_bucket(cls, bucket: str) -> None:
        """确保 bucket 存在，不存在则自动创建。服务启动时调用一次即可。"""
        def _ensure():
            client = cls.get_client()
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
                logger.info(f"MinIO bucket 已创建：{bucket}")
            else:
                logger.debug(f"MinIO bucket 已存在：{bucket}")
        # minio-py 是同步阻塞库，run_in_executor 将其投递到线程池执行，
        # await 期间事件循环不被阻塞，可继续处理其他请求。
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _ensure)

    # ------------------------------------------------------------------ #
    #  上传文件（小文件通过后端代理）
    # ------------------------------------------------------------------ #
    @classmethod
    async def put_object(cls, bucket: str, object_key: str, data: bytes,
        content_type: str = "application/octet-stream",) -> None:
        """
        将文件类型的 bytes 数据上传到 MinIO。
        Args:
            bucket:       目标 bucket 名称
            object_key:   对象路径，如 performance/jmx/2026/04/uuid.jmx
            data:         文件二进制内容
            content_type: MIME 类型
        """
        def _put():
            client = cls.get_client()
            stream = io.BytesIO(data)
            client.put_object(bucket_name=bucket, object_name=object_key, data=stream, length=len(data),
                              content_type=content_type,)

        # 同步阻塞的 minio-py 调用投递到线程池，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _put)

    # ------------------------------------------------------------------ #
    #  上传、下载文件预签名 URL（大文件前端直传）
    # ------------------------------------------------------------------ #

    @classmethod
    def presign_put(cls, bucket: str, object_key: str, expires_minutes: int = 30,) -> str:
        """
        生成预签名 PUT URL，供前端直接上传大文件。
        Args:
            bucket:          目标 bucket
            object_key:      对象路径
            expires_minutes: URL 有效期（分钟），默认 30 分钟
        Returns:
            预签名 PUT URL 字符串
        """
        return cls.get_client().presigned_put_object(
            bucket_name=bucket, object_name=object_key, expires=timedelta(minutes=expires_minutes),)

    @classmethod
    def presign_get(cls, bucket: str, object_key: str, expires_minutes: int = 5, file_name: Optional[str] = None,) -> str:
        """
        生成预签名 GET URL，供前端直接下载文件。
        Args:
            bucket:          目标 bucket
            object_key:      对象路径
            expires_minutes: URL 有效期（分钟），默认 5 分钟
            file_name:       指定下载时的文件名（Content-Disposition）
        Returns:
            预签名 GET URL 字符串
        """
        extra_headers = {}
        if file_name:
            extra_headers["response-content-disposition"] = f'attachment; filename="{file_name}"'
        return cls.get_client().presigned_get_object(
            bucket_name=bucket, object_name=object_key, expires=timedelta(minutes=expires_minutes),
            response_headers=extra_headers if extra_headers else None,
        )

    # ------------------------------------------------------------------ #
    #  校验 & 元信息（confirm 阶段使用）
    # ------------------------------------------------------------------ #
    @classmethod
    async def stat_object(cls, bucket: str, object_key: str) -> dict:
        """
        获取 MinIO 对象元信息（用于 confirm 阶段验证文件真实存在）。
        Returns:
            {"size": int, "content_type": str, "etag": str}
        Raises:
            S3Error: 对象不存在时抛出，由调用方捕获转为 HTTP 400
        """
        def _stat():
            return cls.get_client().stat_object(bucket, object_key)

        # 同步阻塞的 minio-py 调用投递到线程池，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        stat = await loop.run_in_executor(None, _stat)
        return {
            "size":         stat.size,
            "content_type": stat.content_type,
            "etag":         stat.etag,
        }

    # ------------------------------------------------------------------ #
    #  Minio中删除文件
    # ------------------------------------------------------------------ #

    @classmethod
    async def remove_object(cls, bucket: str, object_key: str) -> None:
        """
        删除 MinIO 对象。对象不存在时静默忽略（幂等）。
        Args:
            bucket:     目标 bucket
            object_key: 对象路径
        """
        def _remove():
            try:
                cls.get_client().remove_object(bucket, object_key)
            except S3Error as e:
                if e.code == "NoSuchKey":
                    logger.warning(f"MinIO 对象不存在，跳过删除：{bucket}/{object_key}")
                else:
                    raise

        # 同步阻塞的 minio-py 调用投递到线程池，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _remove)

    # ------------------------------------------------------------------ #
    #  流式读取（代理下载备用，通常用预签名 URL 替代）
    # ------------------------------------------------------------------ #

    @classmethod
    async def get_object_bytes(cls, bucket: str, object_key: str) -> bytes:
        """
        读取 MinIO 对象全部内容并返回 bytes。
        注意：仅适用于小文件（≤50MB），大文件请使用 presign_get 预签名 URL。

        经 Cloudflare 代理的连接可能被代理端静默断开而连接池未感知，复用到
        这种失效连接会在读取阶段挂起直至超时；因此这里对超时类异常做一次
        "重建连接池后重试"，避免偶发的连接失效导致整次下载失败。
        若异常信息中已包含 "Response code:"，说明边缘代理/服务端已经明确
        响应（如 Cloudflare WAF 403），并非连接层故障，重试没有意义，直接
        抛出，逻辑与 app.core.register.minio.init_minio 保持一致。
        """
        def _get():
            response = cls.get_client().get_object(bucket, object_key)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()

        # 同步阻塞的 minio-py 调用投递到线程池，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, _get)
        except Exception as e:
            if 'Response code:' in str(e):
                raise
            logger.warning(f"MinIO 下载首次失败，重建连接池后重试一次：{bucket}/{object_key}，原因：{fmt_cloudflare_html_resp(e)}")
            cls._client = None  # 丢弃可能已失效的连接池单例，下次 get_client() 重新建池
            return await loop.run_in_executor(None, _get)