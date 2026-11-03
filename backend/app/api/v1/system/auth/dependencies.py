#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.v1.system.auth.service import AuthService
from app.api.v1.system.user.crud import UserCRUD
from app.core.api_permission import ApiPermission, check_permission


async def get_current_user(
    authorization: str = Header(..., description="Bearer token"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前登录用户
    
    Args:
        authorization: Authorization header
        db: 数据库会话
        
    Returns:
        当前用户对象
        
    Raises:
        HTTPException: 未授权或用户不存在
    """
    # 提取token
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证方式",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    
    # 验证token
    payload = AuthService.verify_token(token)
    user_id = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌无效"
        )
    
    # 获取用户
    crud = UserCRUD(db)
    user = await crud.get_by_id_crud(int(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 验证用户状态
    if user.status != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user


async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """
    获取当前活跃用户（状态为启用）
    
    Args:
        current_user: 当前用户
        
    Returns:
        当前用户对象
        
    Raises:
        HTTPException: 用户已被禁用
    """
    if current_user.status != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    return current_user


async def check_menu_permission(
    permission: str,
    current_user = Depends(get_current_user)
):
    """
    检查用户是否有指定的菜单权限
    
    Args:
        permission: 权限标识
        current_user: 当前用户
        
    Returns:
        当前用户对象
        
    Raises:
        HTTPException: 无权限
    """
    # 超级管理员拥有所有权限
    if current_user.user_type == 10:
        return current_user
    
    # 获取用户权限列表
    user_permissions = []
    if current_user.roles:
        for role in current_user.roles:
            if role.menus:
                for menu in role.menus:
                    if menu.perms:
                        user_permissions.append(menu.perms)
    
    # 检查权限
    if permission not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问"
        )
    
    return current_user


def require_permission(permission: str):
    """
    权限装饰器工厂
    
    Args:
        permission: 需要的权限标识
        
    Returns:
        依赖函数
    """
    async def permission_checker(
        current_user = Depends(get_current_user)
    ):
        return await check_menu_permission(permission, current_user)
    
    return permission_checker


def require_api_permission(permission_code: str):
    """
    API权限装饰器
    
    Args:
        permission_code: 权限编码
        
    Returns:
        依赖函数
    """
    async def permission_checker(
        current_user = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        # 检查API权限
        has_permission = await check_permission(current_user, permission_code, db)
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权限访问，需要权限: {permission_code}"
            )
        
        return current_user
    
    return permission_checker


def require_any_api_permission(*permission_codes: str):
    """
    需要任一API权限的装饰器
    
    Args:
        *permission_codes: 权限编码列表
        
    Returns:
        依赖函数
    """
    async def permission_checker(
        current_user = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        # 超级管理员拥有所有权限
        if current_user.user_type == 10:
            return current_user
        
        # 检查是否有任一权限
        api_permission = ApiPermission(db)
        has_permission = await api_permission.check_multiple_permissions(
            current_user, list(permission_codes), require_all=False
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权限访问，需要以下任一权限: {', '.join(permission_codes)}"
            )
        
        return current_user
    
    return permission_checker


def require_all_api_permissions(*permission_codes: str):
    """
    需要全部API权限的装饰器
    
    Args:
        *permission_codes: 权限编码列表
        
    Returns:
        依赖函数
    """
    async def permission_checker(
        current_user = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        # 超级管理员拥有所有权限
        if current_user.user_type == 10:
            return current_user
        
        # 检查是否有全部权限
        api_permission = ApiPermission(db)
        has_permission = await api_permission.check_multiple_permissions(
            current_user, list(permission_codes), require_all=True
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权限访问，需要以下全部权限: {', '.join(permission_codes)}"
            )
        
        return current_user
    
    return permission_checker
