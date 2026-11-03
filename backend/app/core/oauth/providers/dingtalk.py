#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

import logging
from typing import Dict, Optional

import requests

from app.core.oauth.base_oauth_service import BaseOAuthService
from app.config.setting import config

logger = logging.getLogger(__name__)


class DingTalkOAuthService(BaseOAuthService):
    """钉钉 OAuth 服务类
    
    钉钉 OAuth 文档：
    https://open.dingtalk.com/document/orgapp/tutorial-obtaining-user-personal-information
    """

    PROVIDER_NAME = 'dingtalk'

    # 钉钉扫码登录授权地址
    AUTHORIZE_URL = "https://login.dingtalk.com/oauth2/auth"

    # 钉钉获取 access_token 地址
    TOKEN_URL = "https://api.dingtalk.com/v1.0/oauth2/userAccessToken"

    # 钉钉获取用户信息地址
    USER_INFO_URL = "https://api.dingtalk.com/v1.0/contact/users/me"

    @classmethod
    def get_client_config(cls) -> Dict[str, str]:
        """获取钉钉客户端配置"""
        return {
            'client_id': config.DINGTALK_APP_ID,
            'client_secret': config.DINGTALK_APP_SECRET,
            'redirect_uri': config.DINGTALK_REDIRECT_URI,
        }

    @classmethod
    def get_extra_authorize_params(cls) -> Dict[str, str]:
        """钉钉需要的额外授权参数"""
        return {
            'response_type': 'code',
            'scope': 'openid',  # 获取用户基本信息
            'prompt': 'consent',  # 每次都显示授权页面
        }

    @classmethod
    def get_access_token(cls, code: str) -> Optional[str]:
        """
        使用授权码获取访问令牌
        
        钉钉的 token 获取方式与标准 OAuth2 不同：
        - 使用 POST 请求
        - 参数在 JSON body 中
        - 返回格式也不同
        
        Args:
            code: 授权码
        
        Returns:
            Optional[str]: 访问令牌，失败返回 None
        """
        try:
            client_config = cls.get_client_config()

            # 钉钉使用 JSON body 传递参数
            data = {
                'clientId': client_config['client_id'],
                'clientSecret': client_config['client_secret'],
                'code': code,
                'grantType': 'authorization_code',
            }

            headers = {
                'Content-Type': 'application/json',
            }

            response = requests.post(
                cls.TOKEN_URL,
                json=data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            result = response.json()

            # 钉钉返回格式: {"accessToken": "xxx", "refreshToken": "xxx", "expireIn": 7200}
            if 'accessToken' in result:
                logger.info(f"钉钉 access_token 获取成功")
                return result['accessToken']
            else:
                logger.error(f"钉钉 token 响应格式错误: {result}")
                return None

        except requests.RequestException as e:
            logger.error(f"请求钉钉 access_token 失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取钉钉 access_token 异常: {str(e)}")
            return None

    @classmethod
    def get_user_info(cls, access_token: str) -> Optional[Dict]:
        """
        使用访问令牌获取钉钉用户信息
        
        Args:
            access_token: 访问令牌
        
        Returns:
            Optional[Dict]: 用户信息字典，失败返回 None
        """
        try:
            headers = {
                'x-acs-dingtalk-access-token': access_token,
                'Content-Type': 'application/json',
            }

            response = requests.get(
                cls.USER_INFO_URL,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            user_info = response.json()

            # 钉钉返回格式检查
            if 'unionId' not in user_info:
                logger.error(f"钉钉用户信息格式错误: {user_info}")
                return None

            return user_info

        except requests.RequestException as e:
            logger.error(f"请求钉钉用户信息失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取钉钉用户信息异常: {str(e)}")
            return None

    @classmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """
        标准化钉钉用户信息
        
        钉钉用户信息格式：
        {
            "unionId": "xxx",
            "openId": "xxx",
            "nick": "张三",
            "avatarUrl": "https://...",
            "mobile": "13800138000",
            "email": "xxx@example.com"
        }
        
        Args:
            raw_user_info: 钉钉原始用户信息
        
        Returns:
            Dict: 标准化后的用户信息
        """
        # 使用 unionId 作为唯一标识
        provider_id = raw_user_info.get('unionId', '')

        # 钉钉的昵称字段
        nick = raw_user_info.get('nick', '')

        # 生成用户名（使用 nick 或 unionId 的一部分）
        username = nick if nick else f"dingtalk_{provider_id[:8]}"

        return {
            'provider_id': provider_id,
            'username': username,
            'name': nick or username,
            'email': raw_user_info.get('email'),
            'avatar': raw_user_info.get('avatarUrl'),
            'bio': f"钉钉用户 - {nick}" if nick else "钉钉用户",
        }

    @classmethod
    def get_user_id_field(cls) -> str:
        """
        获取用户 ID 字段名
        
        Returns:
            str: 字段名 'dingtalk_unionid'
        """
        return 'dingtalk_unionid'
