# -*- coding: utf-8 -*-
# @author: rebort
"""API 限流配置 - 使用 fastapi-limiter"""
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import redis.asyncio as aioredis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from config import config


def get_real_ip(request: Request) -> str:
    """
    获取真实 IP 地址
    优先从 X-Real-IP 或 X-Forwarded-For 获取
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "127.0.0.1"


async def rate_limit_callback(request: Request, response: Response, pexpire: int):
    """
    限流回调函数
    当触发限流时返回自定义响应
    """
    return JSONResponse(
        status_code=429,
        content={
            "code": 429,
            "msg": f"请求过于频繁，请稍后再试。请在 {pexpire/1000:.0f} 秒后重试",
            "success": False,
            "data": None
        }
    )


async def init_limiter(app: FastAPI):
    """
    初始化限流器
    
    Args:
        app: FastAPI 应用实例
    """
    try:
        # 从配置中获取 Redis URI
        redis_uri = str(config.REDIS_URI)
        
        # 创建 Redis 连接
        redis_connection = aioredis.from_url(
            redis_uri,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
        )
        
        # 初始化 FastAPILimiter
        await FastAPILimiter.init(
            redis=redis_connection,
            prefix="fastapi-limiter",
            identifier=get_real_ip,
            http_callback=rate_limit_callback
        )
        
        print("✓ API 限流器初始化成功")
        
    except Exception as e:
        print(f"✗ API 限流器初始化失败: {str(e)}")
        print("  限流功能将不可用，但不影响系统运行")


# 导出 RateLimiter 供路由使用
__all__ = ['init_limiter', 'RateLimiter']
