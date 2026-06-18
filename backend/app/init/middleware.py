# -*- coding: utf-8 -*-
# @author: rebort
import time

from fastapi import FastAPI, Request
from loguru import logger

from app.corelibs import g
from app.utils.common import get_str_uuid
from app.utils.context import AppTraceId
from app.middleware.log_middleware import LogMiddleware


def init_middleware(app: FastAPI):
    """初始化中间件"""
    
    # 注册日志记录中间件
    app.add_middleware(LogMiddleware)

    @app.middleware("http")
    async def intercept(request: Request, call_next):
        """HTTP请求拦截中间件"""
        g.trace_id = get_str_uuid()
        AppTraceId.set(g.trace_id)
        start_time = time.time()
        remote_addr = request.headers.get("X-Real-IP", request.client.host)
        logger.info(f"访问记录:IP:{remote_addr}-method:{request.method}-url:{request.url}")
        
        # 处理请求
        response = await call_next(request)
        response.headers["X-request-id"] = g.trace_id
        logger.info(f"请求耗时： {time.time() - start_time}")
        return response
