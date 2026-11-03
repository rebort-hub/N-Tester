#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

import logging
from typing import Dict, Optional

import requests

from app.core.oauth.base_oauth_service import BaseOAuthService
from app.config.setting import config

logger = logging.getLogger(__name__)


class FeishuOAuthService(BaseOAuthService):
    """飞书 OAuth 服务类
    
    飞书 OAuth 文档：
    https://open.feishu.cn/document/common-capabilities/sso/api/get-user-info
    """

    PROVIDER_NAME = 'feishu'

    # 飞书网页应用登录授权地址
    AUTHORIZE_URL = "https://open.feishu.cn/open-apis/authen/v1/authorize"

    # 飞书获取 access_token 地址
    TOKEN_URL = "https://open.feishu.cn/open-apis/authen/v1/oidc/access_token"

    # 飞书获取用户信息地址
    USER_INFO_URL = "https://open.feishu.cn/open-apis/authen/v1/user_info"

    @classmethod
    def get_client_config(cls) -> Dict[str, str]:
        """获取飞书客户端配置"""
        return {
            'client_id': config.FEISHU_APP_ID,
            'client_secret': config.FEISHU_APP_SECRET,
            'redirect_uri': config.FEISHU_REDIRECT_URI,
        }

    @classmethod
    def get_extra_authorize_params(cls) -> Dict[str, str]:
        """飞书需要的额外授权参数"""
        return {
            'response_type': 'code',
            'scope': 'contact:user.base:readonly',  # 获取用户基本信息
        }

    @classmethod
    def _get_app_access_token(cls) -> Optional[str]:
        """
        获取应用级别的 access_token（用于调用飞书 API）
        
        Returns:
            Optional[str]: 应用 access_token
        """
        try:
            client_config = cls.get_client_config()

            url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
            data = {
                'app_id': client_config['client_id'],
                'app_secret': client_config['client_secret'],
            }

            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()

            result = response.json()

            if result.get('code') == 0:
                return result.get('app_access_token')

            logger.error(f"获取飞书 app_access_token 失败: {result}")
            return None

        except Exception as e:
            logger.error(f"获取飞书 app_access_token 异常: {str(e)}")
            return None

    @classmethod
    def get_access_token(cls, code: str) -> Optional[str]:
        """
        使用授权码获取访问令牌
        
        飞书的 token 获取方式：
        - 使用 POST 请求
        - 参数在 JSON body 中
        - 需要先获取 app_access_token
        
        Args:
            code: 授权码
        
        Returns:
            Optional[str]: 访问令牌，失败返回 None
        """
        try:
            # 飞书使用 JSON body 传递参数
            data = {
                'grant_type': 'authorization_code',
                'code': code,
            }

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {cls._get_app_access_token()}',
            }

            response = requests.post(
                cls.TOKEN_URL,
                json=data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            result = response.json()

            # 飞书返回格式: {"code": 0, "msg": "success", "data": {"access_token": "xxx", ...}}
            if result.get('code') == 0 and 'data' in result:
                access_token = result['data'].get('access_token')
                if access_token:
                    logger.info(f"飞书 access_token 获取成功")
                    return access_token

            logger.error(f"飞书 token 响应格式错误: {result}")
            return None

        except requests.RequestException as e:
            logger.error(f"请求飞书 access_token 失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取飞书 access_token 异常: {str(e)}")
            return None

    @classmethod
    def get_user_info(cls, access_token: str) -> Optional[Dict]:
        """
        使用访问令牌获取飞书用户信息
        
        Args:
            access_token: 访问令牌
        
        Returns:
            Optional[Dict]: 用户信息字典，失败返回 None
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            }

            response = requests.get(
                cls.USER_INFO_URL,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            result = response.json()

            # 飞书返回格式检查
            if result.get('code') == 0 and 'data' in result:
                user_info = result['data']
                if 'union_id' not in user_info:
                    logger.error(f"飞书用户信息格式错误: {result}")
                    return None
                return user_info

            logger.error(f"飞书用户信息响应错误: {result}")
            return None

        except requests.RequestException as e:
            logger.error(f"请求飞书用户信息失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取飞书用户信息异常: {str(e)}")
            return None

    @classmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """
        标准化飞书用户信息
        
        飞书用户信息格式：
        {
            "union_id": "xxx",
            "user_id": "xxx",
            "open_id": "xxx",
            "name": "张三",
            "en_name": "Zhang San",
            "avatar_url": "https://...",
            "avatar_thumb": "https://...",
            "avatar_middle": "https://...",
            "avatar_big": "https://...",
            "email": "xxx@example.com",
            "mobile": "+86-13800138000"
        }
        
        Args:
            raw_user_info: 飞书原始用户信息
        
        Returns:
            Dict: 标准化后的用户信息
        """
        # 使用 union_id 作为唯一标识
        provider_id = raw_user_info.get('union_id', '')

        # 飞书的名称字段
        name = raw_user_info.get('name', '')
        en_name = raw_user_info.get('en_name', '')

        # 生成用户名（优先使用英文名，否则使用中文名或 union_id 的一部分）
        username = en_name or name or f"feishu_{provider_id[:8]}"
        # 替换空格为下划线
        username = username.replace(' ', '_')

        # 处理手机号（飞书返回格式：+86-13800138000）
        mobile = raw_user_info.get('mobile', '')
        if mobile and mobile.startswith('+86-'):
            mobile = mobile[4:]  # 去掉 +86-

        return {
            'provider_id': provider_id,
            'username': username,
            'name': name or username,
            'email': raw_user_info.get('email'),
            'avatar': raw_user_info.get('avatar_url') or raw_user_info.get('avatar_big'),
            'bio': f"飞书用户 - {name}" if name else "飞书用户",
        }

    @classmethod
    def get_user_id_field(cls) -> str:
        """
        获取用户 ID 字段名
        
        Returns:
            str: 字段名 'feishu_union_id'
        """
        return 'feishu_union_id'
