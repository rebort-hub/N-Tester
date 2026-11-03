#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.v1.system.auth.service import AuthService, CaptchaService
from app.api.v1.system.auth.schema import (
    LoginSchema,
    LoginResponseSchema,
    RefreshTokenSchema,
    UserInfoSchema,
    ChangePasswordSchema,
    RegisterSchema
)
from app.common.response import success_response

router = APIRouter()


def get_client_ip(request: Request) -> str:
    """获取客户端真实IP"""
    # 优先从X-Forwarded-For获取（代理/负载均衡场景）
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # 从X-Real-IP获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 直接从client获取
    if request.client:
        return request.client.host
    
    return "unknown"


@router.get("/captcha/get", summary="获取登录验证码")
async def get_captcha():
    """
    获取图片验证码。

    - CAPTCHA_ENABLE=true：返回 enable/key/img_base，答案存 Redis
    - CAPTCHA_ENABLE=false：返回 enable=false，前端隐藏验证码
    """
    data = await CaptchaService.get_captcha_service()
    return success_response(data=data, message="获取验证码成功")


@router.post("/login", summary="用户登录", response_model=dict)
async def login(
    data: LoginSchema,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    
    返回访问令牌和刷新令牌
    """
    client_ip = get_client_ip(request)
    result = await AuthService.login_service(data, client_ip, request, db)
    return success_response(data=result.model_dump(), message="登录成功")


@router.post("/logout", summary="用户登出")
async def logout(
    authorization: str = Header(..., description="Bearer token"),
    db: AsyncSession = Depends(get_db)
):
    """
    用户登出
    
    将令牌加入黑名单（可选实现）
    """
    # 提取token
    token = authorization.replace("Bearer ", "")
    await AuthService.logout_service(token, db)
    return success_response(message="登出成功")


@router.post("/refresh", summary="刷新令牌", response_model=dict)
async def refresh_token(
    data: RefreshTokenSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    刷新访问令牌
    
    使用刷新令牌获取新的访问令牌
    """
    result = await AuthService.refresh_token_service(data, db)
    return success_response(data=result.model_dump(), message="刷新成功")


@router.get("/userinfo", summary="获取当前用户信息", response_model=dict)
async def get_user_info(
    authorization: str = Header(..., description="Bearer token"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前登录用户的信息
    
    包括用户基本信息、角色和权限
    """
    # 提取token
    token = authorization.replace("Bearer ", "")
    result = await AuthService.get_current_user_service(token, db)
    return success_response(data=result.model_dump(), message="查询成功")


@router.get("/menus", summary="获取当前用户菜单", response_model=dict)
async def get_user_menus(
    authorization: str = Header(..., description="Bearer token"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前登录用户的菜单列表
    
    根据用户角色返回有权限的菜单
    """
    # 提取token
    token = authorization.replace("Bearer ", "")
    result = await AuthService.get_user_menus_service(token, db)
    return success_response(data=result, message="查询成功")


@router.put("/password", summary="修改密码")
async def change_password(
    data: ChangePasswordSchema,
    authorization: str = Header(..., description="Bearer token"),
    db: AsyncSession = Depends(get_db)
):
    """
    修改当前用户密码
    
    需要提供旧密码进行验证
    """
    # 提取token并获取用户ID
    token = authorization.replace("Bearer ", "")
    payload = AuthService.verify_token(token)
    user_id = int(payload.get("sub"))
    
    await AuthService.change_password_service(user_id, data, db)
    return success_response(message="密码修改成功")


@router.post("/register", summary="用户注册", response_model=dict)
async def register(
    data: RegisterSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册
    
    创建新用户账号
    """
    result = await AuthService.register_service(data, db)
    return success_response(data=result.model_dump(), message="注册成功")
