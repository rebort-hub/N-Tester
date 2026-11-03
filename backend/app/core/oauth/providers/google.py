#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

import logging
from typing import Dict, Optional

import requests

from app.core.oauth.base_oauth_service import BaseOAuthService
from app.config.setting import config

logger = logging.getLogger(__name__)


class GoogleOAuthService(BaseOAuthService):
    """Google OAuth 服务类"""

    PROVIDER_NAME = 'google'
    AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    @classmethod
    def get_client_config(cls) -> Dict[str, str]:
        """获取 Google 客户端配置"""
        return {
            'client_id': config.GOOGLE_CLIENT_ID,
            'client_secret': config.GOOGLE_CLIENT_SECRET,
            'redirect_uri': config.GOOGLE_REDIRECT_URI,
        }

    @classmethod
    def get_extra_authorize_params(cls) -> Dict[str, str]:
        """Google 需要 scope 和 access_type 参数"""
        return {
            'scope': 'openid email profile',
            'access_type': 'offline',
            'response_type': 'code',
        }

    @classmethod
    def get_user_info(cls, access_token: str) -> Optional[Dict]:
        """
        使用访问令牌获取 Google 用户信息
        
        Args:
            access_token: 访问令牌
        
        Returns:
            Optional[Dict]: 用户信息字典，失败返回 None
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
            }
            response = requests.get(
                cls.USER_INFO_URL,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            user_info = response.json()

            if 'id' not in user_info:
                logger.error(f"Google 用户信息格式错误: {user_info}")
                return None

            return user_info

        except requests.RequestException as e:
            logger.error(f"请求 Google 用户信息失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取 Google 用户信息异常: {str(e)}")
            return None

    @classmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """
        标准化 Google 用户信息
        
        Args:
            raw_user_info: Google 原始用户信息
        
        Returns:
            Dict: 标准化后的用户信息
        """
        return {
            'provider_id': raw_user_info.get('id'),
            'username': raw_user_info.get('email', '').split('@')[0],  # 使用邮箱前缀作为用户名
            'name': raw_user_info.get('name') or raw_user_info.get('email'),
            'email': raw_user_info.get('email'),
            'avatar': raw_user_info.get('picture'),
            'bio': None,
        }
