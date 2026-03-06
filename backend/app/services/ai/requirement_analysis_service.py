# -*- coding: utf-8 -*-
"""
需求分析服务
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RequirementAnalysisService:
    """需求分析服务"""
    
    def __init__(self, model_config: Dict[str, Any]):
        """初始化服务
        
        Args:
            model_config: AI模型配置
                - api_key: API密钥
                - base_url: API基础URL
                - model_name: 模型名称
                - temperature: 温度参数
                - max_tokens: 最大token数
        """
        self.model_config = model_config
    
    async def analyze_document(
        self, 
        document_text: str,
        project_name: str = ""
    ) -> Dict[str, Any]:
        """分析需求文档
        
        Args:
            document_text: 文档文本内容
            project_name: 项目名称
        
        Returns:
            分析结果字典:
            {
                'summary': '需求文档总体概述',
                'modules': ['模块1', '模块2', ...],
                'requirements': [
                    {
                        'requirement_id': 'REQ-001',
                        'requirement_name': '需求名称',
                        'requirement_type': '功能需求',
                        'module': '所属模块',
                        'requirement_level': '高',
                        'description': '详细描述',
                        'acceptance_criteria': '验收标准',
                        'parent_requirement_id': None
                    }
                ]
            }
        """
        from app.services.ai.ai_model_service import AIModelService
        
        logger.info(f"开始分析需求文档，项目: {project_name}, 文档长度: {len(document_text)}")
        
        # 构建系统提示词
        system_prompt = self._get_system_prompt()
        
        # 构建用户提示词
        user_prompt = self._get_user_prompt(document_text, project_name)
        
        # 调用AI模型
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # 使用AIModelService调用API
            response = await AIModelService.call_openai_compatible_api(
                self.model_config,
                messages,
                max_tokens=8000  # 需求分析需要较长的输出
            )
            
            content = response['choices'][0]['message']['content']
            logger.info(f"AI模型返回内容长度: {len(content)}")
            
            # 解析结果
            result = self._parse_response(content)
            
            logger.info(f"需求分析完成，提取到 {len(result['requirements'])} 个需求")
            
            return result
            
        except Exception as e:
            logger.error(f"需求分析失败: {str(e)}", exc_info=True)
            raise Exception(f"需求分析失败: {str(e)}")
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的需求分析专家。你的任务是分析需求文档，提取业务需求信息。

请按照以下JSON格式返回分析结果：

```json
{
  "summary": "需求文档总体概述（100-200字）",
  "modules": ["模块1", "模块2", "模块3"],
  "requirements": [
    {
      "requirement_id": "REQ-001",
      "requirement_name": "需求名称",
      "requirement_type": "功能需求",
      "module": "所属模块",
      "requirement_level": "高",
      "description": "详细描述需求的内容、目的和预期效果",
      "acceptance_criteria": "明确的验收标准，可测试可验证",
      "parent_requirement_id": null
    }
  ]
}
```

要求：
1. requirement_id必须唯一，格式为REQ-001, REQ-002...（三位数字）
2. requirement_type只能是：功能需求、非功能需求、业务需求
3. requirement_level只能是：高、中、低
4. module必须从文档中提取，如果没有明确模块，根据功能归类
5. description要详细描述需求的内容、目的和预期效果
6. acceptance_criteria必须明确、可测试、可验证
7. 如果有父子关系的需求，设置parent_requirement_id为父需求的ID
8. 必须返回纯JSON格式，不要包含markdown代码块标记

分析原则：
- 全面：提取文档中所有明确的需求
- 准确：准确理解需求的含义和范围
- 结构化：按模块和层级组织需求
- 可测试：验收标准必须明确可测试
"""
    
    def _get_user_prompt(self, document_text: str, project_name: str) -> str:
        """获取用户提示词"""
        # 限制文档长度，避免超过token限制
        max_length = 15000
        if len(document_text) > max_length:
            document_text = document_text[:max_length] + "\n\n...(文档过长，已截断)"
        
        prompt = f"""请分析以下需求文档：

项目名称：{project_name or '未指定'}

文档内容：
{document_text}

请仔细阅读文档，提取所有业务需求，并按照指定的JSON格式返回。

注意：
1. 确保提取所有明确的需求点
2. 为每个需求分配唯一的编号
3. 合理划分模块
4. 验收标准要具体可测试
5. 返回纯JSON格式，不要包含markdown代码块标记
"""
        return prompt
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """解析AI返回的内容
        
        Args:
            content: AI返回的文本内容
        
        Returns:
            解析后的结果字典
        """
        try:
            # 尝试直接解析JSON
            result = json.loads(content)
            return self._validate_and_format_result(result)
        except json.JSONDecodeError:
            # 如果不是纯JSON，尝试提取JSON部分
            logger.warning("AI返回内容不是纯JSON，尝试提取...")
            
            # 尝试提取```json ... ```之间的内容
            import re
            json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                try:
                    result = json.loads(json_str)
                    return self._validate_and_format_result(result)
                except json.JSONDecodeError:
                    pass
            
            # 尝试提取``` ... ```之间的内容
            json_match = re.search(r'```\s*\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                try:
                    result = json.loads(json_str)
                    return self._validate_and_format_result(result)
                except json.JSONDecodeError:
                    pass
            
            # 尝试提取{ ... }之间的内容
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    result = json.loads(json_str)
                    return self._validate_and_format_result(result)
                except json.JSONDecodeError:
                    pass
            
            # 如果都失败了，返回默认结构
            logger.error(f"无法解析AI返回内容: {content[:500]}")
            return {
                'summary': '需求分析失败，无法解析AI返回内容',
                'modules': [],
                'requirements': []
            }
    
    def _validate_and_format_result(self, result: Dict) -> Dict:
        """验证和格式化结果
        
        Args:
            result: 原始结果字典
        
        Returns:
            验证和格式化后的结果字典
        """
        # 确保必需字段存在
        if 'requirements' not in result:
            result['requirements'] = []
        
        if 'summary' not in result:
            result['summary'] = "需求分析完成"
        
        if 'modules' not in result:
            result['modules'] = []
        
        # 验证和修正每个需求
        for idx, req in enumerate(result['requirements']):
            # 确保requirement_id存在且唯一
            if 'requirement_id' not in req or not req['requirement_id']:
                req['requirement_id'] = f"REQ-{str(idx + 1).zfill(3)}"
            
            # 确保requirement_name存在
            if 'requirement_name' not in req or not req['requirement_name']:
                req['requirement_name'] = f"需求{idx + 1}"
            
            # 确保requirement_type有效
            if 'requirement_type' not in req or req['requirement_type'] not in ['功能需求', '非功能需求', '业务需求']:
                req['requirement_type'] = '功能需求'
            
            # 确保module存在
            if 'module' not in req or not req['module']:
                req['module'] = '未分类'
            
            # 确保requirement_level有效
            if 'requirement_level' not in req or req['requirement_level'] not in ['高', '中', '低']:
                req['requirement_level'] = '中'
            
            # 确保description存在
            if 'description' not in req or not req['description']:
                req['description'] = req['requirement_name']
            
            # 确保acceptance_criteria存在
            if 'acceptance_criteria' not in req or not req['acceptance_criteria']:
                req['acceptance_criteria'] = '待补充验收标准'
            
            # parent_requirement_id可以为None
            if 'parent_requirement_id' not in req:
                req['parent_requirement_id'] = None
        
        # 提取所有模块（如果modules为空）
        if not result['modules'] and result['requirements']:
            modules = set()
            for req in result['requirements']:
                if req.get('module'):
                    modules.add(req['module'])
            result['modules'] = list(modules)
        
        return result
