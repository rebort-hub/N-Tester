#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

import logging
from typing import Dict, Optional

import requests

from app.core.oauth.base_oauth_service import BaseOAuthService
from app.config.setting import config

logger = logging.getLogger(__name__)


class MicrosoftOAuthService(BaseOAuthService):
    """微软 OAuth 服务类 (Microsoft Identity Platform)"""

    PROVIDER_NAME = 'microsoft'
    AUTHORIZE_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    USER_INFO_URL = "https://graph.microsoft.com/v1.0/me"

    @classmethod
    def get_client_config(cls) -> Dict[str, str]:
        """获取微软客户端配置"""
        return {
            'client_id': config.MICROSOFT_CLIENT_ID,
            'client_secret': config.MICROSOFT_CLIENT_SECRET,
            'redirect_uri': config.MICROSOFT_REDIRECT_URI,
        }

    @classmethod
    def get_extra_authorize_params(cls) -> Dict[str, str]:
        """微软需要 scope 和 response_mode 参数"""
        return {
            'scope': 'openid email profile User.Read',
            'response_type': 'code',
            'response_mode': 'query',
        }

    @classmethod
    def get_user_info(cls, access_token: str) -> Optional[Dict]:
        """
        使用 Microsoft Graph API 获取用户信息
        
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
                logger.error(f"Microsoft 用户信息格式错误: {user_info}")
                return None

            return user_info

        except requests.RequestException as e:
            logger.error(f"请求 Microsoft 用户信息失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取 Microsoft 用户信息异常: {str(e)}")
            return None

    @classmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """
        标准化微软用户信息
        
        Args:
            raw_user_info: Microsoft 原始用户信息
        
        Returns:
            Dict: 标准化后的用户信息
        """
        # 使用 userPrincipalName 的前缀作为用户名
        user_principal_name = raw_user_info.get('userPrincipalName', '')
        username = user_principal_name.split('@')[0] if '@' in user_principal_name else user_principal_name

        # 优先使用 mail，如果没有则使用 userPrincipalName
        email = raw_user_info.get('mail') or raw_user_info.get('userPrincipalName')

        return {
            'provider_id': raw_user_info.get('id'),
            'username': username or f"ms_{raw_user_info.get('id', '')[:8]}",
            'name': raw_user_info.get('displayName') or username,
            'email': email,
            'avatar': None,  # Microsoft Graph 需要额外 API 调用获取头像
            'bio': raw_user_info.get('jobTitle'),
        }
