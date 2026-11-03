#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort
"""
日志记录中间件
"""

import json
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from loguru import logger as _logger
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.system.log.service import OperationLogService
from app.core import g
from app.core.database import get_db
from app.utils.common import get_str_uuid
from app.utils.context import AppTraceId


class LogMiddleware(BaseHTTPMiddleware):
    """日志记录中间件"""
    
    def __init__(self, app, skip_paths: list = None):
        super().__init__(app)
        # 不需要记录日志的路径
        self.skip_paths = skip_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static",
            "/favicon.ico",
            "/health",
            "/api/v1/system/log"  # 避免日志接口自身产生日志
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        start_time = time.time()
        
        # 更新用户活动（对所有认证请求）
        await self._update_user_activity(request)
        
        # 检查是否需要跳过日志记录
        if self._should_skip_logging(request):
            return await call_next(request)
        
        # 记录请求数据
        request_data = await self._get_request_data(request)
        
        # 执行请求
        response = await call_next(request)
        
        # 计算执行时间
        execution_time = int((time.time() - start_time) * 1000)
        
        # 异步记录日志
        try:
            await self._log_operation(
                request=request,
                response=response,
                request_data=request_data,
                execution_time=execution_time
            )
        except Exception as e:
            # 日志记录失败不应该影响正常请求
            print(f"日志记录失败: {str(e)}")
        
        return response
    
    async def _update_user_activity(self, request: Request):
        """更新用户活动时间"""
        try:
            authorization = request.headers.get("Authorization")
            if authorization and authorization.startswith("Bearer "):
                from app.api.v1.system.auth.service import AuthService
                from app.api.v1.monitor.online.service import OnlineUserService
                
                token = authorization.replace("Bearer ", "")
                payload = AuthService.verify_token(token)
                user_id = payload.get("sub")
                session_id = payload.get("session_id")
                
                if user_id and session_id:
                    # 更新用户活动时间
                    await OnlineUserService.update_user_activity(int(user_id), session_id)
        except Exception as e:
            pass  # 静默失败，不影响正常请求
    
    def _should_skip_logging(self, request: Request) -> bool:
        """判断是否应该跳过日志记录"""
        path = request.url.path
        
        # 跳过指定路径
        for skip_path in self.skip_paths:
            if path.startswith(skip_path):
                return True
        
        # 只记录特定方法的请求
        if request.method not in ["POST", "PUT", "DELETE", "PATCH"]:
            return True
        
        return False
    
    async def _get_request_data(self, request: Request) -> dict:
        """获取请求数据"""
        try:
            # 获取查询参数
            query_params = dict(request.query_params)
            
            # 获取请求体（如果有）
            body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body_bytes = await request.body()
                    if body_bytes:
                        # 尝试解析JSON
                        try:
                            body = json.loads(body_bytes.decode())
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            body = body_bytes.decode('utf-8', errors='ignore')[:1000]  # 限制长度
                except Exception:
                    body = "无法读取请求体"
            
            return {
                "query_params": query_params,
                "body": body
            }
        except Exception:
            return {"error": "无法解析请求数据"}
    
    async def _log_operation(
        self,
        request: Request,
        response: Response,
        request_data: dict,
        execution_time: int
    ):
        """记录操作日志"""
        # 获取数据库会话
        async for db in get_db():
            try:
                # 从请求中获取用户信息（如果有认证）
                user_id = None
                username = None
                
                # 尝试从请求头获取用户信息
                authorization = request.headers.get("Authorization")
                if authorization and authorization.startswith("Bearer "):
                    try:
                        from app.api.v1.system.auth.service import AuthService
                        token = authorization.replace("Bearer ", "")
                        payload = AuthService.verify_token(token)
                        user_id = payload.get("sub")
                        username = payload.get("username")
                    except Exception:
                        pass  # 认证失败不影响日志记录
                
                # 确定操作类型和模块
                operation = self._get_operation_name(request)
                module = self._get_module_name(request)
                description = self._get_operation_description(request, operation)
                
                # 记录日志
                await OperationLogService.create_operation_log(
                    request=request,
                    operation=operation,
                    module=module,
                    description=description,
                    user_id=user_id,
                    username=username,
                    request_data=request_data,
                    response_data=None,  # 不记录响应数据以节省空间
                    status=1 if 200 <= response.status_code < 400 else 0,
                    error_msg=None if 200 <= response.status_code < 400 else f"HTTP {response.status_code}",
                    execution_time=execution_time,
                    db=db
                )
            except Exception as e:
                print(f"记录操作日志失败: {str(e)}")
            finally:
                await db.close()
            break
    
    def _get_operation_name(self, request: Request) -> str:
        """获取操作名称"""
        method = request.method
        path = request.url.path
        
        # 根据HTTP方法确定操作类型
        operation_map = {
            "POST": "创建",
            "PUT": "更新",
            "PATCH": "修改",
            "DELETE": "删除"
        }
        
        return operation_map.get(method, method)
    
    def _get_module_name(self, request: Request) -> str:
        """获取模块名称"""
        path = request.url.path
        
        # 从路径中提取模块名
        if "/api/v1/system/" in path:
            parts = path.split("/")
            if len(parts) >= 5:
                return parts[4]  # 获取模块名
        
        return "系统"
    
    def _get_operation_description(self, request: Request, operation: str) -> str:
        """获取操作描述"""
        path = request.url.path
        module = self._get_module_name(request)
        
        return f"{operation}{module}数据"


def init_middleware(app: FastAPI):
    """注册日志中间件与请求追踪中间件。"""
    app.add_middleware(LogMiddleware)

    @app.middleware("http")
    async def intercept(request: Request, call_next):
        g.trace_id = get_str_uuid()
        AppTraceId.set(g.trace_id)
        start_time = time.time()
        remote_addr = request.headers.get("X-Real-IP", request.client.host if request.client else "")
        _logger.info(f"访问记录:IP:{remote_addr}-method:{request.method}-url:{request.url}")
        response = await call_next(request)
        response.headers["X-request-id"] = g.trace_id
        _logger.info(f"请求耗时： {time.time() - start_time}")
        return response
