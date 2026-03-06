# -*- coding: utf-8 -*-
"""
AI模型调用服务
"""

import httpx
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AIModelService:
    """AI模型调用服务"""
    
    @staticmethod
    async def call_openai_compatible_api(
        model_config: Any,
        messages: List[Dict[str, str]],
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """调用OpenAI兼容格式的API
        
        Args:
            model_config: 模型配置对象或字典
            messages: 消息列表
            max_tokens: 最大token数
        
        Returns:
            API响应字典
        """
        # 处理model_config，支持对象和字典两种格式
        if hasattr(model_config, 'api_key'):
            # 对象格式
            api_key = model_config.api_key
            base_url = model_config.base_url
            model_name = model_config.model_name
            temperature = model_config.temperature if hasattr(model_config, 'temperature') else 0.7
            top_p = model_config.top_p if hasattr(model_config, 'top_p') else 0.9
            config_max_tokens = model_config.max_tokens if hasattr(model_config, 'max_tokens') else 4096
        else:
            # 字典格式
            api_key = model_config['api_key']
            base_url = model_config['base_url']
            model_name = model_config['model_name']
            temperature = model_config.get('temperature', 0.7)
            top_p = model_config.get('top_p', 0.9)
            config_max_tokens = model_config.get('max_tokens', 4096)
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        actual_max_tokens = max_tokens if max_tokens is not None else config_max_tokens

        data = {
            'model': model_name,
            'messages': messages,
            'max_tokens': actual_max_tokens,
            'temperature': temperature,
            'top_p': top_p,
            'stream': False
        }
        
        # 确保base_url不以/结尾
        base_url = base_url.rstrip('/')
        if not base_url.endswith('/chat/completions'):
            import re
            version_match = re.search(r'/v(\d+)/?$', base_url)
            if version_match:
                url = f"{base_url}/chat/completions"
            else:
                url = f"{base_url}/v1/chat/completions"
        else:
            url = base_url

        logger.info(f"=== API调用详情 ===")
        logger.info(f"原始base_url: {base_url}")
        logger.info(f"最终请求URL: {url}")
        logger.info(f"模型名称: {model_name}")
        logger.info(f"max_tokens: {actual_max_tokens}")

        try:
            timeout_config = httpx.Timeout(
                connect=60.0,
                read=900.0,
                write=60.0,
                pool=60.0
            )
            async with httpx.AsyncClient(timeout=timeout_config, http2=False) as client:
                response = await client.post(url, headers=headers, json=data)
                
                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"API调用返回错误: Status={response.status_code}, Body={error_detail}")

                response.raise_for_status()
                result = response.json()
                logger.info(f"API调用成功")
                return result
        except httpx.HTTPStatusError as e:
            error_msg = f"API返回错误 {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.TimeoutException as e:
            logger.error(f"API请求超时: {repr(e)}")
            raise Exception(f"API请求超时，请稍后再试或检查网络连接")
        except Exception as e:
            logger.error(f"API调用失败: {repr(e)}")
            raise Exception(f"API调用失败: {str(e) or repr(e)}")
