#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

import logging
from typing import Dict, Optional

import requests

from app.core.oauth.base_oauth_service import BaseOAuthService
from app.config.setting import config

logger = logging.getLogger(__name__)


class GiteeOAuthService(BaseOAuthService):
    """Gitee OAuth 服务类"""

    PROVIDER_NAME = 'gitee'
    AUTHORIZE_URL = "https://gitee.com/oauth/authorize"
    TOKEN_URL = "https://gitee.com/oauth/token"
    USER_INFO_URL = "https://gitee.com/api/v5/user"

    @classmethod
    def get_client_config(cls) -> Dict[str, str]:
        """获取 Gitee 客户端配置"""
        return {
            'client_id': config.GITEE_CLIENT_ID,
            'client_secret': config.GITEE_CLIENT_SECRET,
            'redirect_uri': config.GITEE_REDIRECT_URI,
        }

    @classmethod
    def get_user_info(cls, access_token: str) -> Optional[Dict]:
        """
        使用访问令牌获取 Gitee 用户信息
        
        Args:
            access_token: 访问令牌
        
        Returns:
            Optional[Dict]: 用户信息字典，失败返回 None
        """
        try:
            params = {'access_token': access_token}
            response = requests.get(
                cls.USER_INFO_URL,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            user_info = response.json()

            if 'id' not in user_info:
                logger.error(f"Gitee 用户信息格式错误: {user_info}")
                return None

            return user_info

        except requests.RequestException as e:
            logger.error(f"请求 Gitee 用户信息失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取 Gitee 用户信息异常: {str(e)}")
            return None

    @classmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """
        标准化 Gitee 用户信息
        
        Args:
            raw_user_info: Gitee 原始用户信息
        
        Returns:
            Dict: 标准化后的用户信息
        """
        return {
            'provider_id': str(raw_user_info.get('id')),
            'username': raw_user_info.get('login'),
            'name': raw_user_info.get('name', raw_user_info.get('login')),
            'email': raw_user_info.get('email'),
            'avatar': raw_user_info.get('avatar_url'),
            'bio': raw_user_info.get('bio'),
        }
