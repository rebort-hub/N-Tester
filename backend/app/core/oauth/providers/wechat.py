#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

import logging
from typing import Dict, Optional

import requests

from app.core.oauth.base_oauth_service import BaseOAuthService
from app.config.setting import config

logger = logging.getLogger(__name__)


class WeChatOAuthService(BaseOAuthService):
    """微信开放平台 OAuth 服务类"""

    PROVIDER_NAME = 'wechat'
    AUTHORIZE_URL = "https://open.weixin.qq.com/connect/qrconnect"
    TOKEN_URL = "https://api.weixin.qq.com/sns/oauth2/access_token"
    USER_INFO_URL = "https://api.weixin.qq.com/sns/userinfo"

    @classmethod
    def get_user_id_field(cls) -> str:
        """微信使用 unionid 作为唯一标识"""
        return 'wechat_unionid'

    @classmethod
    def get_client_config(cls) -> Dict[str, str]:
        """获取微信客户端配置"""
        return {
            'client_id': config.WECHAT_APP_ID,
            'client_secret': config.WECHAT_APP_SECRET,
            'redirect_uri': config.WECHAT_REDIRECT_URI,
        }

    @classmethod
    def get_extra_authorize_params(cls) -> Dict[str, str]:
        """微信需要 appid 和 scope 参数"""
        client_config = cls.get_client_config()
        return {
            'appid': client_config['client_id'],  # 微信使用 appid 而不是 client_id
            'scope': 'snsapi_login',  # 网页扫码登录
            'response_type': 'code',
        }

    @classmethod
    def get_authorize_url(cls, state: Optional[str] = None) -> str:
        """
        获取微信授权 URL
        微信的参数名称与标准 OAuth 2.0 不同
        """
        client_config = cls.get_client_config()
        extra_params = cls.get_extra_authorize_params()

        params = {
            'appid': client_config['client_id'],
            'redirect_uri': client_config['redirect_uri'],
            'response_type': 'code',
            'scope': extra_params['scope'],
        }

        if state:
            params['state'] = state

        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        # 微信需要添加 #wechat_redirect 锚点
        return f"{cls.AUTHORIZE_URL}?{query_string}#wechat_redirect"

    @classmethod
    def get_access_token(cls, code: str) -> Optional[Dict]:
        """
        使用授权码获取访问令牌
        微信的参数名称与标准 OAuth 2.0 不同
        
        Returns:
            Dict: 包含 access_token 和 openid
        """
        try:
            client_config = cls.get_client_config()
            params = {
                'appid': client_config['client_id'],  # 微信用 appid
                'secret': client_config['client_secret'],  # 微信用 secret
                'code': code,
                'grant_type': 'authorization_code',
            }

            response = requests.get(
                cls.TOKEN_URL,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            token_data = response.json()

            # 检查错误
            if 'errcode' in token_data:
                logger.error(f"微信获取 token 失败: {token_data}")
                return None

            if 'access_token' not in token_data or 'openid' not in token_data:
                logger.error(f"微信 token 响应格式错误: {token_data}")
                return None

            return token_data

        except requests.RequestException as e:
            logger.error(f"请求微信 token 失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取微信 token 异常: {str(e)}")
            return None

    @classmethod
    def get_user_info(cls, access_token: str, openid: str = None) -> Optional[Dict]:
        """
        使用访问令牌获取微信用户信息
        微信需要同时传递 access_token 和 openid
        
        Args:
            access_token: 访问令牌（实际上是包含 token 和 openid 的字典）
            openid: 用户的 openid
        
        Returns:
            Optional[Dict]: 用户信息字典，失败返回 None
        """
        try:
            # 如果 access_token 是字典（从 get_access_token 返回）
            if isinstance(access_token, dict):
                token_data = access_token
                access_token = token_data.get('access_token')
                openid = token_data.get('openid')
            
            params = {
                'access_token': access_token,
                'openid': openid,
                'lang': 'zh_CN',
            }

            response = requests.get(
                cls.USER_INFO_URL,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            user_info = response.json()

            # 检查错误
            if 'errcode' in user_info:
                logger.error(f"微信获取用户信息失败: {user_info}")
                return None

            if 'openid' not in user_info:
                logger.error(f"微信用户信息格式错误: {user_info}")
                return None

            return user_info

        except requests.RequestException as e:
            logger.error(f"请求微信用户信息失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取微信用户信息异常: {str(e)}")
            return None

    @classmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """
        标准化微信用户信息
        
        Args:
            raw_user_info: 微信原始用户信息
        
        Returns:
            Dict: 标准化后的用户信息
        """
        # 优先使用 unionid，如果没有则使用 openid
        provider_id = raw_user_info.get('unionid') or raw_user_info.get('openid')

        # 微信昵称可能包含 emoji 和特殊字符，需要处理
        nickname = raw_user_info.get('nickname', '')
        username = nickname.replace(' ', '_')[:30] if nickname else f"wechat_{provider_id[:8]}"

        return {
            'provider_id': provider_id,
            'username': username,
            'name': nickname or username,
            'email': None,  # 微信不提供邮箱
            'avatar': raw_user_info.get('headimgurl'),
            'bio': None,
        }
