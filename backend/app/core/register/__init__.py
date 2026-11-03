# -*- coding: utf-8 -*-
"""应用注册：CORS / 路由 / 中间件相关初始化入口。"""
from app.core.register.cors import init_cors
from app.core.register.routers import init_router
from app.core.register.mount import init_mount
from app.core.register.limiter import init_limiter
from app.core.register.minio import init_minio
from app.core.register.scheduler import (
    init_scheduler,
    shutdown_scheduler,
    load_perf_pending_jobs,
)
from app.core.exceptions import init_exception
from app.core.middlewares import init_middleware

__all__ = [
    "init_cors",
    "init_router",
    "init_mount",
    "init_limiter",
    "init_minio",
    "init_scheduler",
    "shutdown_scheduler",
    "load_perf_pending_jobs",
    "init_exception",
    "init_middleware",
]
