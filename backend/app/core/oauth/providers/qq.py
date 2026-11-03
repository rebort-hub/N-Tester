#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

import json
import logging
import re
from typing import Dict, Optional

import requests

from app.core.oauth.base_oauth_service import BaseOAuthService
from app.config.setting import config

logger = logging.getLogger(__name__)


class QQOAuthService(BaseOAuthService):
    """QQ 互联 OAuth 服务类"""

    PROVIDER_NAME = 'qq'
    AUTHORIZE_URL = "https://graph.qq.com/oauth2.0/authorize"
    TOKEN_URL = "https://graph.qq.com/oauth2.0/token"
    USER_INFO_URL = "https://graph.qq.com/user/get_user_info"
    OPENID_URL = "https://graph.qq.com/oauth2.0/me"

    @classmethod
    def get_client_config(cls) -> Dict[str, str]:
        """获取 QQ 客户端配置"""
        return {
            'client_id': config.QQ_APP_ID,
            'client_secret': config.QQ_APP_KEY,
            'redirect_uri': config.QQ_REDIRECT_URI,
        }

    @classmethod
    def get_extra_authorize_params(cls) -> Dict[str, str]:
        """QQ 需要 response_type 参数"""
        return {
            'response_type': 'code',
        }

    @classmethod
    def get_access_token(cls, code: str) -> Optional[str]:
        """
        使用授权码获取访问令牌
        
        QQ 返回的是 URL 参数格式，需要特殊处理
        
        Args:
            code: 授权码
        
        Returns:
            Optional[str]: 访问令牌，失败返回 None
        """
        try:
            client_config = cls.get_client_config()

            params = {
                'grant_type': 'authorization_code',
                'client_id': client_config['client_id'],
                'client_secret': client_config['client_secret'],
                'code': code,
                'redirect_uri': client_config['redirect_uri'],
            }

            response = requests.get(
                cls.TOKEN_URL,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            # QQ 返回的是 URL 参数格式: access_token=xxx&expires_in=xxx
            response_text = response.text

            # 解析 access_token
            match = re.search(r'access_token=([^&]+)', response_text)
            if match:
                access_token = match.group(1)
                logger.info(f"QQ access_token 获取成功")
                return access_token
            else:
                logger.error(f"QQ access_token 解析失败: {response_text}")
                return None

        except requests.RequestException as e:
            logger.error(f"请求 QQ access_token 失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取 QQ access_token 异常: {str(e)}")
            return None

    @classmethod
    def get_user_info(cls, access_token: str) -> Optional[Dict]:
        """
        使用访问令牌获取 QQ 用户信息
        
        QQ 需要先获取 openid，再获取用户信息
        
        Args:
            access_token: 访问令牌
        
        Returns:
            Optional[Dict]: 用户信息字典，失败返回 None
        """
        try:
            # 1. 获取 openid
            openid_response = requests.get(
                cls.OPENID_URL,
                params={'access_token': access_token},
                timeout=10
            )
            openid_response.raise_for_status()

            # QQ 返回的是 JSONP 格式: callback( {"client_id":"xxx","openid":"xxx"} );
            openid_text = openid_response.text

            # 解析 openid
            match = re.search(r'callback\(\s*(\{.*?\})\s*\)', openid_text)
            if not match:
                logger.error(f"QQ openid 解析失败: {openid_text}")
                return None

            openid_data = json.loads(match.group(1))
            openid = openid_data.get('openid')

            if not openid:
                logger.error(f"QQ openid 不存在: {openid_data}")
                return None

            logger.info(f"QQ openid 获取成功: {openid}")

            # 2. 获取用户信息
            client_config = cls.get_client_config()
            user_response = requests.get(
                cls.USER_INFO_URL,
                params={
                    'access_token': access_token,
                    'oauth_consumer_key': client_config['client_id'],
                    'openid': openid
                },
                timeout=10
            )
            user_response.raise_for_status()

            user_info = user_response.json()

            # 检查返回状态
            if user_info.get('ret') != 0:
                logger.error(f"QQ 用户信息获取失败: {user_info.get('msg')}")
                return None

            # 将 openid 添加到用户信息中
            user_info['openid'] = openid

            return user_info

        except requests.RequestException as e:
            logger.error(f"请求 QQ 用户信息失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取 QQ 用户信息异常: {str(e)}")
            return None

    @classmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """
        标准化 QQ 用户信息
        
        Args:
            raw_user_info: QQ 原始用户信息
        
        Returns:
            Dict: 标准化后的用户信息
        """
        return {
            'provider_id': raw_user_info.get('openid'),
            'username': raw_user_info.get('nickname', '').replace(' ', '_'),  # QQ 昵称可能有空格
            'name': raw_user_info.get('nickname'),
            'email': None,  # QQ 不提供邮箱
            'avatar': raw_user_info.get('figureurl_qq_2') or raw_user_info.get('figureurl_qq_1'),
            'bio': None,
        }

    @classmethod
    def get_user_id_field(cls) -> str:
        """QQ 使用 qq_openid 字段"""
        return 'qq_openid'
