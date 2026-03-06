# -*- coding: utf-8 -*-
"""
Figma需求提取服务
"""

from typing import Dict, Any, List, Optional
import json
import base64
import httpx
import logging
from datetime import datetime

from .figma_service import FigmaService

logger = logging.getLogger(__name__)


class FigmaRequirementService:
    """Figma需求提取服务"""
    
    def __init__(
        self, 
        figma_token: Optional[str],
        ai_model_config: Dict[str, Any]
    ):
        """初始化服务
        
        Args:
            figma_token: Figma Access Token（公开文件可选）
            ai_model_config: AI模型配置
                - api_key: API密钥
                - base_url: API基础URL
                - model_name: 模型名称（需要支持Vision）
                - temperature: 温度参数
                - max_tokens: 最大token数
        """
        self.figma_service = FigmaService(figma_token)
        self.ai_config = ai_model_config
    
    async def extract_requirements_from_figma(
        self,
        file_key: str,
        project_name: str = ""
    ) -> Dict[str, Any]:
        """从Figma文件提取需求
        
        Args:
            file_key: Figma文件ID
            project_name: 项目名称
        
        Returns:
            需求分析结果
        """
        logger.info(f"开始从Figma文件提取需求: file_key={file_key}, project={project_name}")
        
        try:
            # 1. 获取Figma文件数据
            logger.info("步骤1: 获取Figma文件数据...")
            file_data = await self.figma_service.get_file(file_key)
            file_name = file_data.get("name", "未命名文件")
            logger.info(f"文件名称: {file_name}")
            
            # 2. 提取页面和Frame
            logger.info("步骤2: 提取页面和Frame...")
            pages = await self.figma_service.extract_pages_and_frames(file_data)
            logger.info(f"提取到 {len(pages)} 个页面")
            
            # 3. 提取文本内容
            logger.info("步骤3: 提取文本内容...")
            document = file_data.get("document", {})
            all_texts = await self.figma_service.extract_text_content(document)
            logger.info(f"提取到 {len(all_texts)} 条文本")
            
            # 4. 提取组件信息
            logger.info("步骤4: 提取组件信息...")
            components = await self.figma_service.extract_components(document)
            logger.info(f"提取到 {len(components)} 个组件")
            
            # 5. 获取关键Frame的截图URL
            logger.info("步骤5: 获取Frame截图URL...")
            frame_ids = []
            frame_info_map = {}
            
            for page in pages:
                for frame in page.get("frames", [])[:5]:  # 每页最多5个Frame
                    frame_ids.append(frame["id"])
                    frame_info_map[frame["id"]] = {
                        "page_name": page["name"],
                        "frame_name": frame["name"]
                    }
            
            if not frame_ids:
                logger.warning("未找到任何Frame，无法生成截图")
                return self._create_text_only_requirements(
                    all_texts, components, project_name, file_name
                )
            
            logger.info(f"准备获取 {len(frame_ids)} 个Frame的截图")
            image_urls = await self.figma_service.get_file_images(file_key, frame_ids)
            logger.info(f"成功获取 {len(image_urls)} 个截图URL")

            
            # 6. 使用AI模型分析截图
            logger.info("步骤6: 使用AI模型分析截图...")
            requirements = []
            
            for idx, (frame_id, image_url) in enumerate(image_urls.items(), 1):
                frame_info = frame_info_map.get(frame_id, {})
                logger.info(f"分析Frame {idx}/{len(image_urls)}: {frame_info.get('frame_name', frame_id)}")
                
                try:
                    frame_requirements = await self._analyze_frame_with_ai(
                        image_url,
                        project_name,
                        frame_info.get("page_name", ""),
                        frame_info.get("frame_name", "")
                    )
                    requirements.extend(frame_requirements)
                    logger.info(f"从Frame提取到 {len(frame_requirements)} 个需求")
                except Exception as e:
                    logger.error(f"分析Frame失败: {str(e)}")
                    continue
            
            # 7. 结合文本和组件信息，生成完整需求
            logger.info("步骤7: 合并和优化需求...")
            final_requirements = await self._merge_and_optimize_requirements(
                requirements,
                all_texts,
                components,
                project_name
            )
            
            logger.info(f"最终生成 {len(final_requirements)} 个需求")
            
            return {
                "summary": f"从Figma设计稿《{file_name}》提取了{len(final_requirements)}个需求，涵盖{len(pages)}个页面",
                "modules": self._extract_modules(final_requirements),
                "requirements": final_requirements
            }
            
        except Exception as e:
            logger.error(f"Figma需求提取失败: {str(e)}", exc_info=True)
            raise e
    
    async def _analyze_frame_with_ai(
        self,
        image_url: str,
        project_name: str,
        page_name: str,
        frame_name: str
    ) -> List[Dict[str, Any]]:
        """使用AI模型分析Frame截图
        
        Args:
            image_url: 图片URL
            project_name: 项目名称
            page_name: 页面名称
            frame_name: Frame名称
        
        Returns:
            需求列表
        """
        try:
            # 下载图片并转为base64
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                image_data = response.content
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # 构建提示词
            prompt = self._build_vision_prompt(project_name, page_name, frame_name)
            
            # 调用AI模型（OpenAI兼容格式）
            result = await self._call_vision_api(prompt, image_base64)
            
            # 解析结果
            requirements = self._parse_ai_response(result)
            
            return requirements
            
        except Exception as e:
            logger.error(f"AI分析Frame失败: {str(e)}")
            return []
    
    def _build_vision_prompt(
        self, 
        project_name: str, 
        page_name: str, 
        frame_name: str
    ) -> str:
        """构建Vision分析提示词"""
        return f"""请分析这个UI设计稿，提取功能需求。

项目信息：
- 项目名称：{project_name}
- 页面名称：{page_name}
- Frame名称：{frame_name}

请识别以下内容：
1. **页面功能**：这是什么页面？主要功能是什么？
2. **交互元素**：有哪些按钮、输入框、下拉框、开关等？
3. **数据展示**：有哪些表格、列表、卡片、图表等？
4. **业务流程**：是否有步骤、状态流转、导航等？
5. **表单验证**：输入框是否有必填、格式要求等？

请按以下JSON格式返回（只返回JSON，不要其他文字）：
[
  {{
    "requirement_id": "REQ-001",
    "requirement_name": "需求名称（简短明确）",
    "requirement_type": "功能需求",
    "module": "所属模块（如：用户管理、订单管理）",
    "requirement_level": "高",
    "description": "详细描述这个需求的功能和行为",
    "acceptance_criteria": "明确的验收标准，可测试的条件"
  }}
]

要求：
- requirement_type只能是：功能需求、非功能需求、业务需求
- requirement_level只能是：高、中、低
- acceptance_criteria必须明确可测试，使用编号列表
- 每个可见的交互元素都应该有对应的需求
"""
    
    async def _call_vision_api(
        self, 
        prompt: str, 
        image_base64: str
    ) -> str:
        """调用Vision API
        
        Args:
            prompt: 提示词
            image_base64: base64编码的图片
        
        Returns:
            AI响应内容
        """
        headers = {
            'Authorization': f'Bearer {self.ai_config["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        # 构建请求数据（OpenAI Vision格式）
        data = {
            'model': self.ai_config['model_name'],
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': prompt
                        },
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:image/png;base64,{image_base64}'
                            }
                        }
                    ]
                }
            ],
            'max_tokens': self.ai_config.get('max_tokens', 4096),
            'temperature': self.ai_config.get('temperature', 0.3)
        }
        
        # 确保base_url格式正确
        base_url = self.ai_config['base_url'].rstrip('/')
        if not base_url.endswith('/chat/completions'):
            import re
            version_match = re.search(r'/v(\d+)/?$', base_url)
            if version_match:
                url = f"{base_url}/chat/completions"
            else:
                url = f"{base_url}/v1/chat/completions"
        else:
            url = base_url
        
        logger.info(f"调用Vision API: {url}")
        
        try:
            timeout_config = httpx.Timeout(
                connect=60.0,
                read=300.0,  # Vision分析可能需要更长时间
                write=60.0,
                pool=60.0
            )
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                
                # 提取内容
                content = result['choices'][0]['message']['content']
                return content
                
        except httpx.HTTPStatusError as e:
            error_msg = f"Vision API返回错误 {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Vision API调用失败: {str(e)}")
            raise Exception(f"Vision API调用失败: {str(e)}")
    
    def _parse_ai_response(self, response_text: str) -> List[Dict[str, Any]]:
        """解析AI响应
        
        Args:
            response_text: AI返回的文本
        
        Returns:
            需求列表
        """
        try:
            # 尝试直接解析JSON
            requirements = json.loads(response_text)
            if isinstance(requirements, list):
                return requirements
            elif isinstance(requirements, dict) and 'requirements' in requirements:
                return requirements['requirements']
            else:
                return []
        except json.JSONDecodeError:
            # 如果不是纯JSON，尝试提取JSON部分
            import re
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                try:
                    requirements = json.loads(json_match.group(0))
                    return requirements if isinstance(requirements, list) else []
                except:
                    pass
            
            logger.warning("无法解析AI响应为JSON格式")
            return []
    
    async def _merge_and_optimize_requirements(
        self,
        vision_requirements: List[Dict],
        texts: List[str],
        components: List[Dict],
        project_name: str
    ) -> List[Dict[str, Any]]:
        """合并和优化需求
        
        Args:
            vision_requirements: Vision分析的需求
            texts: 提取的文本
            components: 提取的组件
            project_name: 项目名称
        
        Returns:
            优化后的需求列表
        """
        # 去重：基于需求名称
        seen_names = set()
        unique_requirements = []
        
        for req in vision_requirements:
            name = req.get('requirement_name', '')
            if name and name not in seen_names:
                seen_names.add(name)
                unique_requirements.append(req)
        
        # 重新编号
        for idx, req in enumerate(unique_requirements, 1):
            req['requirement_id'] = f"REQ-{idx:03d}"
        
        logger.info(f"去重后剩余 {len(unique_requirements)} 个需求")
        
        return unique_requirements
    
    def _create_text_only_requirements(
        self,
        texts: List[str],
        components: List[Dict],
        project_name: str,
        file_name: str
    ) -> Dict[str, Any]:
        """仅基于文本和组件创建需求（当没有截图时）
        
        Args:
            texts: 文本列表
            components: 组件列表
            project_name: 项目名称
            file_name: 文件名称
        
        Returns:
            需求分析结果
        """
        logger.info("使用文本和组件信息生成基础需求")
        
        requirements = []
        
        # 基于组件生成需求
        for idx, component in enumerate(components[:20], 1):  # 最多20个
            req = {
                "requirement_id": f"REQ-{idx:03d}",
                "requirement_name": component.get('name', f'组件{idx}'),
                "requirement_type": "功能需求",
                "module": "UI组件",
                "requirement_level": "中",
                "description": component.get('description') or f"实现{component.get('name')}组件的功能",
                "acceptance_criteria": f"1. {component.get('name')}组件正常显示\n2. 组件交互功能正常"
            }
            requirements.append(req)
        
        return {
            "summary": f"从Figma设计稿《{file_name}》提取了{len(requirements)}个基础需求（基于组件信息）",
            "modules": ["UI组件"],
            "requirements": requirements
        }
    
    def _extract_modules(self, requirements: List[Dict]) -> List[str]:
        """提取所有模块名称
        
        Args:
            requirements: 需求列表
        
        Returns:
            模块名称列表
        """
        modules = set()
        for req in requirements:
            if req.get("module"):
                modules.add(req["module"])
        return list(modules)
