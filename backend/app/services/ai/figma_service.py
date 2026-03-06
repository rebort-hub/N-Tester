# -*- coding: utf-8 -*-
"""
Figma API服务
"""

import httpx
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class FigmaService:
    """Figma API服务"""
    
    def __init__(self, access_token: Optional[str] = None, config_id: int = None, db_session = None, current_user_id: int = None):
        """初始化Figma服务
        
        Args:
            access_token: Figma Personal Access Token（可选，公开文件不需要）
            config_id: Figma配置ID（用于速率限制和缓存）
            db_session: 数据库会话（用于缓存和日志）
            current_user_id: 当前用户ID
        """
        self.access_token = access_token
        self.config_id = config_id
        self.db_session = db_session
        self.current_user_id = current_user_id
        self.base_url = "https://api.figma.com/v1"
        self.headers = {}
        if access_token:
            self.headers["X-Figma-Token"] = access_token
    
    async def get_file(self, file_key: str, use_cache: bool = True) -> Dict[str, Any]:
        """获取Figma文件数据（支持缓存和速率限制）
        
        Args:
            file_key: Figma文件ID
            use_cache: 是否使用缓存
        
        Returns:
            文件数据字典
        """
        import time
        
        # 1. 尝试从缓存获取
        if use_cache and self.db_session:
            from app.services.ai.figma_cache_service import FigmaCacheService
            
            cached_data = await FigmaCacheService.get_cached_file(
                self.db_session, file_key, force_refresh=False
            )
            if cached_data:
                logger.info(f"✅ 使用缓存数据: {file_key}")
                return cached_data
        
        # 2. 检查速率限制
        if self.db_session and self.config_id:
            from app.services.ai.figma_rate_limiter import FigmaRateLimiter
            
            rate_status = await FigmaRateLimiter.check_rate_limit(
                self.db_session, self.config_id
            )
            
            if not rate_status['can_call']:
                wait_seconds = rate_status['wait_seconds']
                raise Exception(
                    f"⚠️ API调用频率超限\n\n"
                    f"剩余配额：\n"
                    f"- 每分钟: {rate_status['remaining_minute']}/{rate_status['total_minute']}\n"
                    f"- 每小时: {rate_status['remaining_hour']}/{rate_status['total_hour']}\n"
                    f"- 今日: {rate_status['remaining_day']}/{rate_status['total_day']}\n\n"
                    f"请等待 {wait_seconds} 秒后重试\n\n"
                    f"💡 建议：使用'离线查看'功能查看缓存数据"
                )
        
        # 3. 调用API
        url = f"{self.base_url}/files/{file_key}"
        start_time = time.time()
        status_code = None
        
        try:
            timeout_config = httpx.Timeout(
                connect=30.0,
                read=60.0,
                write=30.0,
                pool=30.0
            )
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.get(url, headers=self.headers)
                status_code = response.status_code
                response.raise_for_status()
                
                response_time = int((time.time() - start_time) * 1000)
                
                # 4. 记录API调用
                if self.db_session and self.config_id:
                    from app.services.ai.figma_rate_limiter import FigmaRateLimiter
                    
                    await FigmaRateLimiter.log_api_call(
                        self.db_session,
                        self.config_id,
                        f"/files/{file_key}",
                        status_code,
                        response_time,
                        self.current_user_id
                    )
                
                file_data = response.json()
                
                # 5. 保存到缓存
                if self.db_session and self.config_id:
                    from app.services.ai.figma_cache_service import FigmaCacheService
                    
                    await FigmaCacheService.save_file_cache(
                        self.db_session,
                        self.config_id,
                        file_key,
                        file_data,
                        file_version=file_data.get('version'),
                        current_user_id=self.current_user_id
                    )
                
                logger.info(f"✅ API调用成功: {file_key}, 耗时: {response_time}ms")
                
                return file_data
                
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            response_time = int((time.time() - start_time) * 1000)
            
            # 记录失败的调用
            if self.db_session and self.config_id:
                from app.services.ai.figma_rate_limiter import FigmaRateLimiter
                
                await FigmaRateLimiter.log_api_call(
                    self.db_session,
                    self.config_id,
                    f"/files/{file_key}",
                    status_code,
                    response_time,
                    self.current_user_id
                )
            
            # 处理不同的错误
            if status_code == 403 and not self.access_token:
                logger.error(f"Figma API返回403: 该文件需要Access Token访问")
                raise Exception(
                    "该Figma文件需要Access Token才能访问。\n\n"
                    "原型链接（/proto/）虽然可以在浏览器中查看，但API访问需要Token。\n\n"
                    "获取Token步骤：\n"
                    "1. 访问 https://www.figma.com/settings\n"
                    "2. 找到 'Personal access tokens'\n"
                    "3. 点击 'Generate new token'\n"
                    "4. 复制生成的Token\n"
                    "5. 在配置中填写Token后重试\n\n"
                    "注：免费Figma账号即可生成Token，无需付费"
                )
            elif status_code == 429:
                logger.error(f"Figma API返回429: 速率限制")
                raise Exception(
                    "Figma API调用频率超限，请稍后再试。\n\n"
                    "原因：短时间内调用次数过多\n"
                    "解决：等待1-2分钟后重试\n\n"
                    "💡 建议：\n"
                    "1. 使用'离线查看'功能查看缓存数据\n"
                    "2. 使用'快速提取'模式（只调用1次API）\n"
                    "3. 避免频繁提取同一文件"
                )
            elif status_code == 404:
                logger.error(f"Figma API返回404: 文件不存在或文件ID错误")
                raise Exception(f"Figma文件不存在，请检查文件ID是否正确")
            else:
                logger.error(f"Figma API返回错误: {e.response.status_code} - {e.response.text}")
                raise Exception(f"获取Figma文件失败: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Figma API调用失败: {str(e)}")
            raise Exception(f"Figma API调用失败: {str(e)}")

    
    async def get_file_nodes(
        self, 
        file_key: str, 
        node_ids: List[str]
    ) -> Dict[str, Any]:
        """获取指定节点的详细信息
        
        Args:
            file_key: 文件ID
            node_ids: 节点ID列表
        
        Returns:
            节点数据字典
        """
        url = f"{self.base_url}/files/{file_key}/nodes"
        params = {"ids": ",".join(node_ids)}
        
        try:
            timeout_config = httpx.Timeout(connect=30.0, read=60.0, write=30.0, pool=30.0)
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"获取节点信息失败: {str(e)}")
            raise Exception(f"获取节点信息失败: {str(e)}")
    
    async def get_file_images(
        self, 
        file_key: str, 
        node_ids: List[str],
        scale: float = 2.0,
        format: str = "png"
    ) -> Dict[str, str]:
        """获取节点的渲染图片URL
        
        Args:
            file_key: 文件ID
            node_ids: 节点ID列表
            scale: 缩放比例（1-4）
            format: 图片格式（png/jpg/svg/pdf）
        
        Returns:
            {node_id: image_url} 字典
        """
        url = f"{self.base_url}/images/{file_key}"
        params = {
            "ids": ",".join(node_ids),
            "scale": scale,
            "format": format
        }
        
        try:
            timeout_config = httpx.Timeout(connect=30.0, read=60.0, write=30.0, pool=30.0)
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("images", {})
        except Exception as e:
            logger.error(f"获取图片URL失败: {str(e)}")
            raise Exception(f"获取图片URL失败: {str(e)}")
    
    async def extract_pages_and_frames(
        self, 
        file_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """提取文件中的所有页面和Frame
        
        Args:
            file_data: Figma文件数据
        
        Returns:
            页面和Frame列表
        """
        pages = []
        document = file_data.get("document", {})
        
        for page in document.get("children", []):
            if page.get("type") == "CANVAS":
                page_info = {
                    "id": page.get("id"),
                    "name": page.get("name"),
                    "type": "PAGE",
                    "frames": []
                }
                
                # 提取Frame
                for child in page.get("children", []):
                    if child.get("type") == "FRAME":
                        bounding_box = child.get("absoluteBoundingBox", {})
                        frame_info = {
                            "id": child.get("id"),
                            "name": child.get("name"),
                            "type": "FRAME",
                            "width": bounding_box.get("width"),
                            "height": bounding_box.get("height")
                        }
                        page_info["frames"].append(frame_info)
                
                pages.append(page_info)
        
        logger.info(f"提取到 {len(pages)} 个页面")
        return pages
    
    async def extract_text_content(
        self, 
        node: Dict[str, Any]
    ) -> List[str]:
        """递归提取节点中的所有文本内容
        
        Args:
            node: 节点数据
        
        Returns:
            文本列表
        """
        texts = []
        
        if node.get("type") == "TEXT":
            text = node.get("characters", "")
            if text.strip():
                texts.append(text.strip())
        
        # 递归处理子节点
        for child in node.get("children", []):
            texts.extend(await self.extract_text_content(child))
        
        return texts
    
    async def extract_components(
        self, 
        node: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """提取所有组件信息
        
        Args:
            node: 节点数据
        
        Returns:
            组件列表
        """
        components = []
        
        node_type = node.get("type")
        if node_type in ["COMPONENT", "INSTANCE"]:
            component_info = {
                "id": node.get("id"),
                "name": node.get("name"),
                "type": node_type,
                "description": node.get("description", "")
            }
            components.append(component_info)
        
        # 递归处理子节点
        for child in node.get("children", []):
            components.extend(await self.extract_components(child))
        
        return components
    
    @staticmethod
    def extract_file_key_from_url(figma_url: str) -> Optional[str]:
        """从Figma URL中提取文件ID
        
        Args:
            figma_url: Figma文件URL
                      支持格式：
                      - https://www.figma.com/file/ABC123/MyDesign
                      - https://www.figma.com/proto/ABC123/MyDesign?node-id=...
                      - https://www.figma.com/design/ABC123/MyDesign
        
        Returns:
            文件ID，如果提取失败返回None
        """
        import re
        # 匹配 /file/, /proto/, /design/ 后面的文件ID
        match = re.search(r'/(file|proto|design)/([a-zA-Z0-9]+)', figma_url)
        if match:
            return match.group(2)
        return None
