#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

"""
接口权限控制器，基于权限标识和角色进行接口访问控制
"""

from typing import List, Set, Optional, Callable
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.api.v1.system.user.model import UserModel
from app.api.v1.system.permission.rbac_model import Permission, RolePermission, UserRole


class ApiPermission:
    """接口权限控制器"""
    
    # 权限类型常量
    PERMISSION_TYPE_MENU = 1      # 菜单权限
    PERMISSION_TYPE_BUTTON = 2    # 按钮权限
    PERMISSION_TYPE_DATA = 3      # 数据权限
    PERMISSION_TYPE_API = 4       # API权限
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._permission_cache = {}  # 权限缓存
    
    async def check_api_permission(
        self, 
        current_user: UserModel, 
        permission_code: str
    ) -> bool:
        """
        检查用户是否有指定的API权限
        
        Args:
            current_user: 当前用户
            permission_code: 权限编码
            
        Returns:
            是否有权限
        """
        # 超级管理员拥有所有权限
        if current_user.user_type == 10:
            return True
        
        # 获取用户的所有权限
        user_permissions = await self._get_user_permissions(current_user.id)
        
        return permission_code in user_permissions
    
    async def check_multiple_permissions(
        self, 
        current_user: UserModel, 
        permission_codes: List[str],
        require_all: bool = True
    ) -> bool:
        """
        检查用户是否有多个权限
        
        Args:
            current_user: 当前用户
            permission_codes: 权限编码列表
            require_all: 是否需要全部权限（True）还是任一权限（False）
            
        Returns:
            是否有权限
        """
        # 超级管理员拥有所有权限
        if current_user.user_type == 10:
            return True
        
        # 获取用户的所有权限
        user_permissions = await self._get_user_permissions(current_user.id)
        
        if require_all:
            # 需要全部权限
            return all(code in user_permissions for code in permission_codes)
        else:
            # 需要任一权限
            return any(code in user_permissions for code in permission_codes)
    
    async def _get_user_permissions(self, user_id: int) -> Set[str]:
        """
        获取用户的所有权限编码
        
        Args:
            user_id: 用户ID
            
        Returns:
            权限编码集合
        """
        cache_key = f"user_permissions_{user_id}"
        if cache_key in self._permission_cache:
            return self._permission_cache[cache_key]
        
        permissions = set()
        
        try:
            # 1. 获取用户的所有角色ID
            role_stmt = select(UserRole.role_id).where(
                UserRole.user_id == user_id,
                UserRole.enabled_flag == 1
            )
            role_result = await self.db.execute(role_stmt)
            role_ids = [row[0] for row in role_result.fetchall()]
            
            if role_ids:
                # 2. 获取角色的所有权限ID
                permission_stmt = select(RolePermission.permission_id).where(
                    RolePermission.role_id.in_(role_ids),
                    RolePermission.enabled_flag == 1
                ).distinct()
                permission_result = await self.db.execute(permission_stmt)
                permission_ids = [row[0] for row in permission_result.fetchall()]
                
                if permission_ids:
                    # 3. 获取权限编码
                    code_stmt = select(Permission.permission_code).where(
                        Permission.id.in_(permission_ids),
                        Permission.enabled_flag == 1,
                        Permission.status == 1
                    )
                    code_result = await self.db.execute(code_stmt)
                    permissions = {row[0] for row in code_result.fetchall()}
            
        except Exception as e:
            print(f"获取用户权限失败: {e}")
        
        # 缓存结果（可以考虑添加过期时间）
        self._permission_cache[cache_key] = permissions
        return permissions
    
    def clear_user_permission_cache(self, user_id: int):
        """清除用户权限缓存"""
        cache_key = f"user_permissions_{user_id}"
        if cache_key in self._permission_cache:
            del self._permission_cache[cache_key]
    
    def clear_all_permission_cache(self):
        """清除所有权限缓存"""
        self._permission_cache.clear()


# 全局权限控制器实例
_api_permission_instance = None


async def get_api_permission(db: AsyncSession = Depends(get_db)) -> ApiPermission:
    """获取API权限控制器实例"""
    global _api_permission_instance
    if _api_permission_instance is None:
        _api_permission_instance = ApiPermission(db)
    return _api_permission_instance


# 便捷函数
async def check_permission(
    current_user: UserModel,
    permission_code: str,
    db: AsyncSession
) -> bool:
    """
    便捷函数：检查权限
    
    Args:
        current_user: 当前用户
        permission_code: 权限编码
        db: 数据库会话
        
    Returns:
        是否有权限
    """
    api_permission = ApiPermission(db)
    return await api_permission.check_api_permission(current_user, permission_code)


# 权限管理工具类
class PermissionManager:
    """权限管理工具类"""
    
    @staticmethod
    async def create_api_permission(
        db: AsyncSession,
        permission_code: str,
        permission_name: str,
        resource_type: str = None,
        resource_id: int = None,
        description: str = None,
        created_by: int = None
    ) -> bool:
        """
        创建API权限
        
        Args:
            db: 数据库会话
            permission_code: 权限编码
            permission_name: 权限名称
            resource_type: 资源类型
            resource_id: 资源ID
            description: 描述
            created_by: 创建人
            
        Returns:
            是否创建成功
        """
        try:
            permission_data = {
                'permission_code': permission_code,
                'permission_name': permission_name,
                'permission_type': ApiPermission.PERMISSION_TYPE_API,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'description': description,
                'status': 1,
                'created_by': created_by
            }
            
            await Permission.create_or_update(permission_data)
            return True
            
        except Exception as e:
            print(f"创建API权限失败: {e}")
            return False
    
    @staticmethod
    async def batch_create_api_permissions(
        db: AsyncSession,
        permissions: List[dict],
        created_by: int = None
    ) -> int:
        """
        批量创建API权限
        
        Args:
            db: 数据库会话
            permissions: 权限列表
            created_by: 创建人
            
        Returns:
            成功创建的数量
        """
        success_count = 0
        
        for perm in permissions:
            perm['permission_type'] = ApiPermission.PERMISSION_TYPE_API
            perm['status'] = 1
            perm['created_by'] = created_by
            
            try:
                await Permission.create_or_update(perm)
                success_count += 1
            except Exception as e:
                print(f"创建权限失败 {perm.get('permission_code')}: {e}")
        
        return success_count