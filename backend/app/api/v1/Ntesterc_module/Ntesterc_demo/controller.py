#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort
"""
示例 展示数据权限和接口权限的使用
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.common.response import success_response, page_response
from app.api.v1.system.auth.dependencies import (
    get_current_user, 
    require_api_permission,
    require_any_api_permission
)
from app.api.v1.system.user.model import UserModel
from app.core.data_permission import DataPermission, apply_data_permission

router = APIRouter()


@router.get("/users", summary="获取用户列表（带数据权限）")
async def get_users_with_data_permission(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    username: Optional[str] = Query(None, description="用户名筛选"),
    current_user: UserModel = Depends(require_api_permission("business:user:list")),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户列表 - 演示数据权限的使用
    
    权限要求：
    - API权限：business:user:list
    - 数据权限：根据用户角色的数据权限范围过滤
    """
    # 构建基础查询
    stmt = select(UserModel).where(UserModel.status == 1)
    
    # 添加筛选条件
    if username:
        stmt = stmt.where(UserModel.username.like(f"%{username}%"))
    
    # 应用数据权限过滤
    stmt = await apply_data_permission(stmt, UserModel, db, current_user)
    
    # 计算总数
    from sqlalchemy import func
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    # 分页查询
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    # 转换为字典格式
    user_list = []
    for user in users:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "email": user.email,
            "dept_id": user.dept_id,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "created_by": user.created_by
        }
        user_list.append(user_dict)
    
    return page_response(
        items=user_list,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/users/{user_id}", summary="获取用户详情")
async def get_user_detail(
    user_id: int,
    current_user: UserModel = Depends(require_api_permission("business:user:detail")),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户详情 - 演示单个资源的数据权限检查
    
    权限要求：
    - API权限：business:user:detail
    - 数据权限：只能查看有权限范围内的用户
    """
    # 构建查询
    stmt = select(UserModel).where(
        UserModel.id == user_id,
        UserModel.status == 1
    )
    
    # 应用数据权限过滤
    stmt = await apply_data_permission(stmt, UserModel, db, current_user)
    
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="用户不存在或无权限访问")
    
    user_dict = {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "email": user.email,
        "phone": user.phone,
        "dept_id": user.dept_id,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "created_by": user.created_by,
        "updated_by": user.updated_by
    }
    
    return success_response(data=user_dict)


@router.post("/users/{user_id}/reset-password", summary="重置用户密码")
async def reset_user_password(
    user_id: int,
    current_user: UserModel = Depends(require_any_api_permission(
        "business:user:reset-password",  # 用户重置密码权限
        "business:admin:reset-password"  # 管理员重置密码权限
    )),
    db: AsyncSession = Depends(get_db)
):
    """
    重置用户密码 - 演示多权限选择
    
    权限要求：
    - API权限：business:user:reset-password 或 business:admin:reset-password
    - 数据权限：只能重置有权限范围内的用户密码
    """
    # 构建查询
    stmt = select(UserModel).where(
        UserModel.id == user_id,
        UserModel.status == 1
    )
    
    # 应用数据权限过滤
    stmt = await apply_data_permission(stmt, UserModel, db, current_user)
    
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="用户不存在或无权限操作")
    
    # 这里应该调用实际的密码重置逻辑
    # user.password = hash_password("123456")
    # await db.commit()
    
    return success_response(message="密码重置成功")


@router.get("/stats", summary="获取统计信息")
async def get_stats(
    current_user: UserModel = Depends(require_api_permission("business:stats:view")),
    db: AsyncSession = Depends(get_db)
):
    """
    获取统计信息 - 演示数据权限对统计的影响
    
    权限要求：
    - API权限：business:stats:view
    - 数据权限：统计结果基于用户的数据权限范围
    """
    # 构建用户查询
    user_stmt = select(UserModel).where(UserModel.status == 1)
    
    # 应用数据权限过滤
    user_stmt = await apply_data_permission(user_stmt, UserModel, db, current_user)
    
    # 统计用户数量
    from sqlalchemy import func
    count_stmt = select(func.count()).select_from(user_stmt.subquery())
    total_result = await db.execute(count_stmt)
    total_users = total_result.scalar()
    
    # 按部门统计（如果有部门权限）
    dept_stats = []
    if hasattr(UserModel, 'dept_id'):
        dept_stmt = select(
            UserModel.dept_id,
            func.count(UserModel.id).label('user_count')
        ).select_from(user_stmt.subquery()).group_by(UserModel.dept_id)
        
        dept_result = await db.execute(dept_stmt)
        dept_stats = [
            {"dept_id": row[0], "user_count": row[1]} 
            for row in dept_result.fetchall()
        ]
    
    stats = {
        "total_users": total_users,
        "dept_stats": dept_stats,
        "permission_scope": "根据用户数据权限范围统计"
    }
    
    return success_response(data=stats)


@router.get("/my-data", summary="获取我的数据")
async def get_my_data(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的数据 - 无需额外权限，只能看自己的数据
    
    权限要求：
    - 仅需要登录认证
    - 自动限制为当前用户的数据
    """
    # 直接查询当前用户创建的数据
    stmt = select(UserModel).where(
        UserModel.created_by == current_user.id,
        UserModel.status == 1
    )
    
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    user_list = []
    for user in users:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        user_list.append(user_dict)
    
    return success_response(data={
        "my_created_users": user_list,
        "total": len(user_list)
    })


# 演示如何在CRUD类中集成数据权限
class UserCRUDWithPermission:
    """带权限的用户CRUD类示例"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.model = UserModel
    
    async def get_list_with_permission(
        self, 
        current_user: UserModel,
        page: int = 1,
        page_size: int = 10,
        **filters
    ):
        """带权限的分页查询"""
        # 构建基础查询
        stmt = select(self.model).where(self.model.status == 1)
        
        # 应用过滤条件
        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        
        # 应用数据权限
        permission = DataPermission(self.model, self.db, current_user)
        stmt = await permission.apply_data_permission(stmt)
        
        # 计算总数
        from sqlalchemy import func
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()
        
        # 分页查询
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }