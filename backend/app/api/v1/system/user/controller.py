#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort
"""
用户API控制器
"""

from typing import List
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.api.v1.system.user.service import UserService
from app.api.v1.system.user.schema import (
    UserCreateSchema,
    UserUpdateSchema,
    UserOutSchema,
    UserQuerySchema,
    UserPasswordSchema,
    UserResetPasswordSchema,
    UserProfileUpdateSchema,
    UserAvatarUpdateSchema
)
from app.common.response import success_response

router = APIRouter()


@router.put("/profile", summary="更新个人信息")
async def update_profile(
    data: UserProfileUpdateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """更新个人信息（用户自己）"""
    result = await UserService.update_profile_service(user_id, data, db)
    return success_response(data=result.model_dump(), message="更新成功")


@router.put("/avatar", summary="更新头像")
async def update_avatar(
    data: UserAvatarUpdateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """更新头像（用户自己）"""
    result = await UserService.update_avatar_service(user_id, data, db)
    return success_response(data=result.model_dump(), message="头像更新成功")


@router.put("/password", summary="修改密码")
async def change_password(
    data: UserPasswordSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """修改密码（用户自己）"""
    await UserService.change_password_service(user_id, data, db)
    return success_response(message="密码修改成功")


@router.get("", summary="获取用户列表")
async def get_user_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    username: str = Query(None, description="用户名"),
    nickname: str = Query(None, description="用户昵称"),
    phone: str = Query(None, description="手机号"),
    email: str = Query(None, description="邮箱"),
    status: int = Query(None, ge=0, le=1, description="用户状态"),
    user_type: int = Query(None, ge=0, le=10, description="用户类型"),
    dept_id: int = Query(None, description="部门ID"),
    begin_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    db: AsyncSession = Depends(get_db)
):
    """获取用户列表"""
    query = UserQuerySchema(
        page=page,
        page_size=page_size,
        username=username,
        nickname=nickname,
        phone=phone,
        email=email,
        status=status,
        user_type=user_type,
        dept_id=dept_id,
        begin_time=begin_time,
        end_time=end_time
    )
    return await UserService.get_user_list_service(query, db)


@router.post("", summary="创建用户")
async def create_user(
    data: UserCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建用户"""
    result = await UserService.create_user_service(data, current_user_id, db)
    return success_response(data=result.model_dump(), message="创建成功")


@router.delete("", summary="删除用户")
async def delete_user(
    ids: List[int] = Query(..., description="用户ID列表"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除用户"""
    await UserService.delete_user_service(ids, db)
    return success_response(message="删除成功")


@router.get("/{user_id}", summary="获取用户详情")
async def get_user_detail(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取用户详情"""
    result = await UserService.get_user_detail_service(user_id, db)
    return success_response(data=result.model_dump())


@router.put("/{user_id}", summary="更新用户")
async def update_user(
    user_id: int,
    data: UserUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新用户"""
    result = await UserService.update_user_service(user_id, data, current_user_id, db)
    return success_response(data=result.model_dump(), message="更新成功")


@router.put("/{user_id}/password", summary="修改指定用户密码（管理员）")
async def change_user_password(
    user_id: int,
    data: UserPasswordSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """修改指定用户密码（管理员操作）"""
    await UserService.change_password_service(user_id, data, db)
    return success_response(message="密码修改成功")


@router.put("/{user_id}/reset-password", summary="重置密码")
async def reset_password(
    user_id: int,
    data: UserResetPasswordSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """重置密码（管理员操作）"""
    await UserService.reset_password_service(user_id, data, db)
    return success_response(message="密码重置成功")


@router.put("/{user_id}/status", summary="更新用户状态")
async def update_status(
    user_id: int,
    status: int = Body(..., embed=True, ge=0, le=1, description="状态"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新用户状态"""
    await UserService.update_status_service(user_id, status, db)
    return success_response(message="状态更新成功")
