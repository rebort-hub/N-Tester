#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

import logging
from typing import Dict, Optional

import requests

from app.core.oauth.base_oauth_service import BaseOAuthService
from app.config.setting import config

logger = logging.getLogger(__name__)


class GitHubOAuthService(BaseOAuthService):
    """GitHub OAuth 服务类"""

    PROVIDER_NAME = 'github'
    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_INFO_URL = "https://api.github.com/user"

    @classmethod
    def get_client_config(cls) -> Dict[str, str]:
        """获取 GitHub 客户端配置"""
        return {
            'client_id': config.GITHUB_CLIENT_ID,
            'client_secret': config.GITHUB_CLIENT_SECRET,
            'redirect_uri': config.GITHUB_REDIRECT_URI,
        }

    @classmethod
    def get_extra_authorize_params(cls) -> Dict[str, str]:
        """GitHub 需要 scope 参数"""
        return {
            'scope': 'user:email',  # 请求用户邮箱权限
        }

    @classmethod
    def get_token_request_headers(cls) -> Dict[str, str]:
        """GitHub 需要 Accept header 来获取 JSON 响应"""
        return {
            'Accept': 'application/json',
        }

    @classmethod
    def get_user_info(cls, access_token: str) -> Optional[Dict]:
        """
        使用访问令牌获取 GitHub 用户信息
        
        Args:
            access_token: 访问令牌
        
        Returns:
            Optional[Dict]: 用户信息字典，失败返回 None
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }
            response = requests.get(
                cls.USER_INFO_URL,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            user_info = response.json()

            if 'id' not in user_info:
                logger.error(f"GitHub 用户信息格式错误: {user_info}")
                return None

            return user_info

        except requests.RequestException as e:
            logger.error(f"请求 GitHub 用户信息失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取 GitHub 用户信息异常: {str(e)}")
            return None

    @classmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """
        标准化 GitHub 用户信息
        
        Args:
            raw_user_info: GitHub 原始用户信息
        
        Returns:
            Dict: 标准化后的用户信息
        """
        return {
            'provider_id': str(raw_user_info.get('id')),
            'username': raw_user_info.get('login'),
            'name': raw_user_info.get('name') or raw_user_info.get('login'),
            'email': raw_user_info.get('email'),
            'avatar': raw_user_info.get('avatar_url'),
            'bio': raw_user_info.get('bio'),
        }
