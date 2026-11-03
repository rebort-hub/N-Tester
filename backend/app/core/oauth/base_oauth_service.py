#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple

import requests
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.api.v1.system.user.model import UserModel
from app.config.setting import config

logger = logging.getLogger(__name__)


class BaseOAuthService(ABC):
    """OAuth 服务基类"""

    # 子类需要定义这些属性
    PROVIDER_NAME: str = None  # 提供商名称，如 'gitee', 'github'
    AUTHORIZE_URL: str = None  # 授权 URL
    TOKEN_URL: str = None  # 获取 token 的 URL
    USER_INFO_URL: str = None  # 获取用户信息的 URL

    @classmethod
    @abstractmethod
    def get_client_config(cls) -> Dict[str, str]:
        """
        获取客户端配置
        
        Returns:
            Dict: 包含 client_id, client_secret, redirect_uri
        """
        pass

    @classmethod
    def get_authorize_url(cls, state: str = None) -> str:
        """
        获取 OAuth 授权 URL
        
        Args:
            state: 状态参数，用于防止 CSRF 攻击
        
        Returns:
            str: 授权 URL
        """
        from urllib.parse import urlencode
        
        client_config = cls.get_client_config()
        params = {
            'client_id': client_config['client_id'],
            'redirect_uri': client_config['redirect_uri'],
            'response_type': 'code',
        }
        if state:
            params['state'] = state

        # 子类可以覆盖此方法添加额外参数（如 scope）
        params.update(cls.get_extra_authorize_params())

        # 使用 urlencode 进行 URL 编码，确保特殊字符（如 #）被正确编码
        query_string = urlencode(params)
        return f"{cls.AUTHORIZE_URL}?{query_string}"

    @classmethod
    def get_extra_authorize_params(cls) -> Dict[str, str]:
        """
        获取额外的授权参数（子类可覆盖）
        
        Returns:
            Dict: 额外参数
        """
        return {}

    @classmethod
    def get_access_token(cls, code: str) -> Optional[str]:
        """
        使用授权码获取访问令牌
        
        Args:
            code: 授权码
        
        Returns:
            Optional[str]: 访问令牌，失败返回 None
        """
        try:
            client_config = cls.get_client_config()
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': client_config['client_id'],
                'client_secret': client_config['client_secret'],
                'redirect_uri': client_config['redirect_uri'],
            }

            response = requests.post(
                cls.TOKEN_URL,
                data=data,
                headers=cls.get_token_request_headers(),
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            access_token = result.get('access_token')

            if not access_token:
                logger.error(f"获取 {cls.PROVIDER_NAME} access_token 失败: {result}")
                return None

            return access_token

        except requests.RequestException as e:
            logger.error(f"请求 {cls.PROVIDER_NAME} access_token 失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取 {cls.PROVIDER_NAME} access_token 异常: {str(e)}")
            return None

    @classmethod
    def get_token_request_headers(cls) -> Dict[str, str]:
        """
        获取 token 请求的 headers（子类可覆盖）
        
        Returns:
            Dict: headers
        """
        return {}

    @classmethod
    @abstractmethod
    def get_user_info(cls, access_token: str) -> Optional[Dict]:
        """
        使用访问令牌获取用户信息（子类必须实现）
        
        Args:
            access_token: 访问令牌
        
        Returns:
            Optional[Dict]: 用户信息字典，失败返回 None
        """
        pass

    @classmethod
    @abstractmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """
        标准化用户信息（子类必须实现）
        
        将不同 OAuth 提供商的用户信息格式统一为标准格式
        
        Args:
            raw_user_info: 原始用户信息
        
        Returns:
            Dict: 标准化后的用户信息，包含:
                - provider_id: 提供商的用户 ID
                - username: 用户名
                - name: 显示名称
                - email: 邮箱
                - avatar: 头像 URL
                - bio: 个人简介
        """
        pass

    @classmethod
    def get_user_id_field(cls) -> str:
        """
        获取用户 ID 字段名（如 gitee_id, github_id）
        
        Returns:
            str: 字段名
        """
        return f"{cls.PROVIDER_NAME}_id"

    @classmethod
    async def handle_oauth_login(
            cls,
            code: str,
            ip_address: str,
            user_agent: str = None,
            login_type: str = None
    ) -> Tuple[UserModel, str, str, int]:
        """
        处理 OAuth 登录流程
        
        Args:
            code: 授权码
            ip_address: 用户 IP 地址
            user_agent: 用户代理字符串
            login_type: 登录方式 (gitee/github/qq/google/wechat/microsoft/dingtalk/feishu)
        
        Returns:
            Tuple: (user, access_token, refresh_token, expire_time)
        
        Raises:
            ValueError: 登录失败时抛出
        """
        # 1. 使用 code 换取 access_token
        access_token = cls.get_access_token(code)
        if not access_token:
            raise ValueError(f"获取 {cls.PROVIDER_NAME} 访问令牌失败")

        # 2. 使用 access_token 获取用户信息
        raw_user_info = cls.get_user_info(access_token)
        if not raw_user_info:
            raise ValueError(f"获取 {cls.PROVIDER_NAME} 用户信息失败")

        # 3. 标准化用户信息
        user_info = cls.normalize_user_info(raw_user_info)
        provider_id = user_info['provider_id']
        username = user_info['username']
        name = user_info['name']
        email = user_info.get('email')
        avatar = user_info.get('avatar')
        bio = user_info.get('bio')

        # 4. 查找或创建用户
        user_id_field = cls.get_user_id_field()
        
        async with async_session() as session:
            # 查找用户
            stmt = select(UserModel).where(
                getattr(UserModel, user_id_field) == provider_id,
                UserModel.enabled_flag == 1
            )
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            is_superadmin = 0
            if config.GRANT_ADMIN_TO_OAUTH_USER:
                is_superadmin = 10  # 超级管理员

            if user:
                # 用户已存在，更新信息
                logger.info(f"{cls.PROVIDER_NAME} 用户已存在: {username} (ID: {provider_id})")

                # 更新用户信息
                if email and not user.email:
                    user.email = email
                if bio and not user.bio:
                    user.bio = bio
                if avatar and not user.avatar:
                    user.avatar = avatar
                
                # 如果配置了授予管理员权限，且用户当前不是管理员，则升级为管理员
                if config.GRANT_ADMIN_TO_OAUTH_USER and user.user_type != 10:
                    user.user_type = 10
                    logger.info(f"将 {cls.PROVIDER_NAME} 用户 {username} 升级为管理员")

                await session.commit()
                await session.refresh(user)
                
                # 检查用户是否已有角色，如果没有则分配管理员角色
                print(f"[DEBUG] 检查已存在用户: GRANT_ADMIN_TO_OAUTH_USER={config.GRANT_ADMIN_TO_OAUTH_USER}")
                logger.info(f"检查已存在用户是否需要分配角色: GRANT_ADMIN_TO_OAUTH_USER={config.GRANT_ADMIN_TO_OAUTH_USER}")
                
                if config.GRANT_ADMIN_TO_OAUTH_USER:
                    print(f"[DEBUG] 开始检查已存在用户 {username} (id={user.id}) 的角色...")
                    logger.info(f"🔄 开始检查已存在的 OAuth 用户 {username} (id={user.id}) 的角色...")
                    
                    try:
                        from app.api.v1.system.role.model import RoleModel
                        from app.api.v1.system.permission.rbac_model import UserRole
                        
                        # 检查用户是否已有角色
                        print(f"[DEBUG] 查询用户角色...")
                        check_role_stmt = select(UserRole).where(
                            UserRole.user_id == user.id,
                            UserRole.enabled_flag == 1
                        ).limit(1)
                        check_result = await session.execute(check_role_stmt)
                        has_role = check_result.scalar_one_or_none()
                        
                        if not has_role:
                            print(f"[DEBUG] 用户 {username} 没有角色，开始分配管理员角色...")
                            logger.info(f"⚠️ 用户 {username} 没有角色，开始分配管理员角色...")
                            
                            # 查找管理员角色
                            print(f"[DEBUG] 查找管理员角色...")
                            admin_role_stmt = select(RoleModel).where(
                                (RoleModel.role_key == 'admin') | 
                                (RoleModel.role_name.in_(['管理员', '超级管理员', 'Administrator'])),
                                RoleModel.status == 1
                            ).limit(1)
                            admin_role_result = await session.execute(admin_role_stmt)
                            admin_role = admin_role_result.scalar_one_or_none()
                            
                            if admin_role:
                                print(f"[DEBUG] 找到管理员角色: {admin_role.role_name} (id={admin_role.id})")
                                logger.info(f"✅ 找到管理员角色: {admin_role.role_name} (id={admin_role.id})")
                                
                                # 创建用户-角色关联
                                print(f"[DEBUG] 创建用户-角色关联...")
                                user_role = UserRole(
                                    user_id=user.id,
                                    role_id=admin_role.id,
                                    created_by=user.id,
                                    enabled_flag=1
                                )
                                session.add(user_role)
                                
                                print(f"[DEBUG] 提交事务...")
                                await session.commit()
                                
                                print(f"[DEBUG] ✅ 角色分配成功！")
                                logger.info(f"✅ 成功为已存在的 OAuth 用户 {username} (id={user.id}) 分配管理员角色: {admin_role.role_name}")
                            else:
                                print(f"[DEBUG] ❌ 未找到管理员角色")
                                logger.warning(f"❌ 未找到管理员角色，无法为 OAuth 用户 {username} 分配角色")
                        else:
                            print(f"[DEBUG] OAuth 用户 {username} 已有角色 (role_id={has_role.role_id})，跳过")
                            logger.info(f"OAuth 用户 {username} 已有角色 (role_id={has_role.role_id})，跳过角色分配")
                    except Exception as e:
                        print(f"[DEBUG] ❌ 角色分配异常: {str(e)}")
                        logger.error(f"❌ 为已存在的 OAuth 用户分配角色失败: {str(e)}", exc_info=True)
                else:
                    print(f"[DEBUG] GRANT_ADMIN_TO_OAUTH_USER=False，跳过角色分配")
                    logger.info(f"GRANT_ADMIN_TO_OAUTH_USER=False，跳过角色分配")
            else:
                # 用户不存在，创建新用户
                logger.info(f"创建新的 {cls.PROVIDER_NAME} 用户: {username} (ID: {provider_id})")

                # 生成唯一的用户名
                unique_username = username
                counter = 1
                while True:
                    stmt = select(UserModel).where(UserModel.username == unique_username, UserModel.enabled_flag == 1)
                    result = await session.execute(stmt)
                    if not result.scalar_one_or_none():
                        break
                    unique_username = f"{username}_{counter}"
                    counter += 1

                # 创建用户
                user = UserModel(
                    username=unique_username,
                    nickname=name,
                    password='',  # OAuth 用户无密码
                    email=email or '',
                    bio=bio,
                    avatar=avatar or '',
                    oauth_provider=cls.PROVIDER_NAME,
                    user_type=is_superadmin,  # 0:普通用户 10:超级管理员
                    status=1,  # 启用
                    remark=f'{cls.PROVIDER_NAME} OAuth 用户',
                )
                setattr(user, user_id_field, provider_id)
                
                session.add(user)
                await session.commit()
                await session.refresh(user)
                
                logger.info(f"✅ {cls.PROVIDER_NAME} 用户创建成功: {unique_username} (id={user.id})")
                
                # 如果配置了授予管理员权限，自动分配管理员角色
                print(f"[DEBUG] 检查配置: GRANT_ADMIN_TO_OAUTH_USER={config.GRANT_ADMIN_TO_OAUTH_USER}")
                logger.info(f"检查是否需要分配管理员角色: GRANT_ADMIN_TO_OAUTH_USER={config.GRANT_ADMIN_TO_OAUTH_USER}")
                
                if config.GRANT_ADMIN_TO_OAUTH_USER:
                    print(f"[DEBUG] 开始为新用户 {unique_username} (id={user.id}) 分配管理员角色...")
                    logger.info(f"🔄 开始为新创建的 OAuth 用户 {unique_username} (id={user.id}) 分配管理员角色...")
                    
                    try:
                        from app.api.v1.system.role.model import RoleModel
                        from app.api.v1.system.permission.rbac_model import UserRole
                        
                        # 查找管理员角色（支持多种角色名称）
                        print(f"[DEBUG] 查找管理员角色...")
                        logger.info(f"🔍 查找管理员角色...")
                        
                        admin_role_stmt = select(RoleModel).where(
                            (RoleModel.role_key == 'admin') | 
                            (RoleModel.role_name.in_(['管理员', '超级管理员', 'Administrator'])),
                            RoleModel.status == 1
                        ).limit(1)
                        admin_role_result = await session.execute(admin_role_stmt)
                        admin_role = admin_role_result.scalar_one_or_none()
                        
                        if admin_role:
                            print(f"[DEBUG] 找到管理员角色: {admin_role.role_name} (id={admin_role.id}, role_key={admin_role.role_key})")
                            logger.info(f"✅ 找到管理员角色: {admin_role.role_name} (id={admin_role.id}, role_key={admin_role.role_key})")
                            
                            # 创建用户-角色关联
                            print(f"[DEBUG] 创建用户-角色关联: user_id={user.id}, role_id={admin_role.id}")
                            user_role = UserRole(
                                user_id=user.id,
                                role_id=admin_role.id,
                                created_by=user.id,
                                enabled_flag=1
                            )
                            session.add(user_role)
                            
                            print(f"[DEBUG] 提交事务...")
                            await session.commit()
                            
                            print(f"[DEBUG] ✅ 角色分配成功！")
                            logger.info(f"✅ 成功为 OAuth 用户 {unique_username} (id={user.id}) 分配管理员角色: {admin_role.role_name}")
                            
                            # 验证角色是否真的插入了
                            verify_stmt = select(UserRole).where(
                                UserRole.user_id == user.id,
                                UserRole.role_id == admin_role.id
                            )
                            verify_result = await session.execute(verify_stmt)
                            verify_role = verify_result.scalar_one_or_none()
                            
                            if verify_role:
                                print(f"[DEBUG] ✅ 验证成功：角色关联已存在于数据库中")
                                logger.info(f"✅ 验证成功：用户 {unique_username} 的角色关联已存在于数据库中")
                            else:
                                print(f"[DEBUG] ❌ 验证失败：角色关联未找到！")
                                logger.error(f"❌ 验证失败：用户 {unique_username} 的角色关联未找到！")
                        else:
                            print(f"[DEBUG] ❌ 未找到管理员角色")
                            logger.warning(f"❌ 未找到管理员角色（role_key='admin' 或 role_name in ['管理员', '超级管理员']），无法为 OAuth 用户 {unique_username} 分配角色")
                    except Exception as e:
                        print(f"[DEBUG] ❌ 角色分配异常: {str(e)}")
                        logger.error(f"❌ 为 OAuth 用户分配角色失败: {str(e)}", exc_info=True)
                        # 不影响登录流程，继续执行
                else:
                    print(f"[DEBUG] GRANT_ADMIN_TO_OAUTH_USER=False，跳过角色分配")
                    logger.info(f"GRANT_ADMIN_TO_OAUTH_USER=False，跳过角色分配")

            # 更新用户最后登录方式
            if login_type:
                user.last_login_type = login_type
                await session.commit()

            # 检查用户状态
            if user.status == 0:
                raise ValueError("账户已被禁用")

        # 5. 生成 JWT token
        from app.api.v1.system.auth.service import AuthService
        from app.utils.common import get_str_uuid
        
        # 生成会话ID
        session_id = get_str_uuid()
        
        # 创建访问令牌
        jwt_access_token = AuthService.create_access_token(
            data={"sub": str(user.id), "username": user.username, "session_id": session_id}
        )
        
        # 创建刷新令牌
        jwt_refresh_token = AuthService.create_refresh_token(
            data={"sub": str(user.id), "username": user.username, "session_id": session_id}
        )
        
        # Token 过期时间（秒）
        expire_time = config.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        # 6. 记录登录日志和在线用户
        from app.api.v1.system.log.service import LoginLogService
        from app.api.v1.monitor.online.service import OnlineUserService
        
        # 创建一个简单的 request 对象用于日志记录
        class SimpleRequest:
            def __init__(self, ip, user_agent):
                self.client = type('obj', (object,), {'host': ip})()
                self.headers = {'user-agent': user_agent or ''}
        
        simple_request = SimpleRequest(ip_address, user_agent)
        
        # 记录登录成功日志
        async with async_session() as log_session:
            await LoginLogService.create_login_log(
                request=simple_request,
                username=user.username,
                user_id=user.id,
                status=1,
                message=f"{cls.PROVIDER_NAME.capitalize()} OAuth 登录成功",
                db=log_session
            )
        
        # 清理该用户的旧会话
        try:
            await OnlineUserService.force_offline(user.id)
        except Exception as e:
            logger.warning(f"清理旧会话失败: {e}")
        
        # 添加在线用户记录
        try:
            await OnlineUserService.add_online_user(
                user_id=user.id,
                username=user.username,
                nickname=user.nickname,
                avatar=user.avatar,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent or ''
            )
        except Exception as e:
            logger.warning(f"添加在线用户失败: {e}")

        return user, jwt_access_token, jwt_refresh_token, expire_time
