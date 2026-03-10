# -*- coding: utf-8 -*-
"""
AI智能化模块业务逻辑层
"""

import json
import httpx
import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional, AsyncIterator
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from .crud import (
    RequirementDocumentCRUD,
    RequirementAnalysisCRUD,
    BusinessRequirementCRUD,
    GeneratedTestCaseCRUD,
    TestCaseGenerationTaskCRUD,
    AIModelConfigCRUD,
    PromptConfigCRUD,
    GenerationConfigCRUD,
    AICaseCRUD,
    AIExecutionRecordCRUD
)
from .model import (
    RequirementDocumentModel,
    RequirementAnalysisModel,
    BusinessRequirementModel,
    TestCaseGenerationTaskModel,
    AIModelConfigModel,
    PromptConfigModel,
    GenerationConfigModel
)
from .schema import (
    RequirementDocumentCreateSchema,
    RequirementDocumentUpdateSchema,
    TestCaseGenerationTaskCreateSchema,
    TestCaseGenerationTaskUpdateSchema,
    AIModelConfigCreateSchema,
    AIModelConfigUpdateSchema,
    PromptConfigCreateSchema,
    PromptConfigUpdateSchema
)

logger = logging.getLogger(__name__)


class RequirementDocumentService:
    """需求文档服务"""
    
    @staticmethod
    async def create_document(
        db: AsyncSession,
        document_data: RequirementDocumentCreateSchema,
        file_path: str,
        file_size: int,
        uploaded_by: int,
        extracted_text: str = None
    ) -> RequirementDocumentModel:
        """创建需求文档"""
        document_crud = RequirementDocumentCRUD(db)
        document_dict = document_data.dict()
        document_dict.update({
            'file_path': file_path,
            'file_size': file_size,
            'uploaded_by': uploaded_by,
            'extracted_text': extracted_text
        })
        return await document_crud.create_crud(data=document_dict)
    
    @staticmethod
    async def get_project_documents(db: AsyncSession, project_id: int) -> List[RequirementDocumentModel]:
        """获取项目下的所有需求文档"""
        document_crud = RequirementDocumentCRUD(db)
        return await document_crud.get_by_project(project_id)
    
    @staticmethod
    async def get_document_with_analysis(db: AsyncSession, document_id: int) -> Optional[RequirementDocumentModel]:
        """获取包含分析结果的需求文档"""
        document_crud = RequirementDocumentCRUD(db)
        return await document_crud.get_with_analysis(document_id)
    
    @staticmethod
    async def update_document(
        db: AsyncSession,
        document_id: int,
        update_data: RequirementDocumentUpdateSchema
    ) -> Optional[RequirementDocumentModel]:
        """更新需求文档"""
        document_crud = RequirementDocumentCRUD(db)
        return await document_crud.update_crud(document_id, update_data.dict(exclude_unset=True))
    
    @staticmethod
    async def delete_document(db: AsyncSession, document_id: int) -> bool:
        """删除需求文档"""
        document_crud = RequirementDocumentCRUD(db)
        try:
            # 先检查文档是否存在
            document = await document_crud.get_by_id_crud(document_id)
            if not document:
                return False
            
            # 执行软删除
            await document_crud.soft_delete_crud([document_id])
            return True
        except Exception as e:
            logger.error(f"删除需求文档失败: {e}")
            return False

    @staticmethod
    async def get_all_documents(db: AsyncSession) -> List[RequirementDocumentModel]:
        """获取所有需求文档"""
        document_crud = RequirementDocumentCRUD(db)
        conditions = [RequirementDocumentModel.enabled_flag == 1]
        items, _ = await document_crud.get_list_crud(
            conditions=conditions,
            order_by=[RequirementDocumentModel.creation_date.desc()]
        )
        return items
    
    @staticmethod
    async def analyze_document(
        db: AsyncSession,
        document_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """分析需求文档
        
        Args:
            db: 数据库会话
            document_id: 文档ID
            user_id: 用户ID
        
        Returns:
            分析结果字典
        """
        from app.services.ai.requirement_analysis_service import RequirementAnalysisService
        from .model import RequirementAnalysisModel, BusinessRequirementModel
        
        # 1. 获取文档
        document_crud = RequirementDocumentCRUD(db)
        document = await document_crud.get_by_id_crud(document_id)
        if not document:
            raise ValueError("文档不存在")
        
        if not document.extracted_text:
            raise ValueError("文档未提取文本，无法分析")
        
        # 2. 获取Writer模型配置
        model_config_crud = AIModelConfigCRUD(db)
        model_config = await model_config_crud.get_active_by_role('writer')
        if not model_config:
            raise ValueError("未找到Writer模型配置，请先在AI模型配置中添加writer角色的配置")
        
        # 3. 更新文档状态
        document.status = 'analyzing'
        await db.commit()
        
        start_time = datetime.now()
        
        try:
            # 4. 执行分析
            analysis_service = RequirementAnalysisService({
                'api_key': model_config.api_key,
                'base_url': model_config.base_url,
                'model_name': model_config.model_name,
                'temperature': model_config.temperature or 0.3,
                'max_tokens': model_config.max_tokens or 8000
            })
            
            # 获取项目名称
            project_name = ""
            if document.project_id:
                try:
                    # 直接通过SQL查询获取项目名称，避免导入模型
                    from sqlalchemy import text
                    stmt = text("SELECT name FROM projects WHERE id = :project_id")
                    result = await db.execute(stmt, {"project_id": document.project_id})
                    row = result.fetchone()
                    if row:
                        project_name = row[0]
                except Exception as e:
                    logger.warning(f"获取项目名称失败: {e}")
                    project_name = ""
            
            result = await analysis_service.analyze_document(
                document_text=document.extracted_text,
                project_name=project_name
            )
            
            # 5. 保存分析结果
            analysis_crud = RequirementAnalysisCRUD(db)
            analysis_data = {
                'document_id': document_id,
                'analysis_report': result['summary'],
                'requirements_count': len(result['requirements']),
                'analysis_time': (datetime.now() - start_time).total_seconds(),
                'created_by': user_id
            }
            analysis = await analysis_crud.create_crud(analysis_data)
            await db.flush()
            
            # 6. 保存业务需求
            requirement_crud = BusinessRequirementCRUD(db)
            for req_data in result['requirements']:
                requirement_data = {
                    'analysis_id': analysis.id,
                    'requirement_id': req_data['requirement_id'],
                    'requirement_name': req_data['requirement_name'],
                    'requirement_type': req_data['requirement_type'],
                    'module': req_data['module'],
                    'requirement_level': req_data['requirement_level'],
                    'description': req_data['description'],
                    'acceptance_criteria': req_data['acceptance_criteria'],
                    'parent_requirement_id': req_data.get('parent_requirement_id'),
                    'created_by': user_id
                }
                await requirement_crud.create_crud(requirement_data)
            
            # 7. 更新文档状态
            document.status = 'analyzed'
            await db.commit()
            
            logger.info(f"需求文档分析完成: document_id={document_id}, requirements_count={analysis.requirements_count}")
            
            return {
                'analysis_id': analysis.id,
                'requirements_count': analysis.requirements_count,
                'analysis_time': analysis.analysis_time,
                'modules': result['modules']
            }
            
        except Exception as e:
            logger.error(f"需求文档分析失败: {str(e)}", exc_info=True)
            document.status = 'failed'
            await db.commit()
            raise e


class AIModelConfigService:
    """AI模型配置服务"""
    
    @staticmethod
    async def create_config(
        db: AsyncSession,
        config_data: AIModelConfigCreateSchema,
        created_by: int
    ) -> AIModelConfigModel:
        """创建AI模型配置"""
        config_crud = AIModelConfigCRUD(db)
        config_dict = config_data.dict()
        config_dict['created_by'] = created_by
        
        # 如果提供了llm_config_id，自动同步LLM配置的参数
        if config_dict.get('llm_config_id'):
            from sqlalchemy import select
            from app.models.ai.llm_config import LLMConfigModel
            
            llm_stmt = select(LLMConfigModel).where(
                LLMConfigModel.id == config_dict['llm_config_id']
            )
            llm_result = await db.execute(llm_stmt)
            llm_config = llm_result.scalar_one_or_none()
            
            if llm_config:
                logger.info(f"自动同步LLM配置（ID: {llm_config.id}）的参数到AI模型配置")
                
                # 同步关键参数（如果前端没有提供，则使用LLM配置的值）
                # 确保API Key以明文形式保存
                if not config_dict.get('api_key'):
                    config_dict['api_key'] = llm_config.api_key
                    logger.info(f"同步API Key: {llm_config.api_key[:10]}...")
                
                if not config_dict.get('base_url'):
                    config_dict['base_url'] = llm_config.base_url
                    logger.info(f"同步Base URL: {llm_config.base_url}")
                
                if not config_dict.get('model_name'):
                    config_dict['model_name'] = llm_config.model_name
                    logger.info(f"同步模型名称: {llm_config.model_name}")
                
                if not config_dict.get('max_tokens'):
                    config_dict['max_tokens'] = llm_config.max_tokens
                
                if not config_dict.get('temperature'):
                    config_dict['temperature'] = llm_config.temperature
                
                # top_p使用默认值（LLM配置没有这个字段）
                if not config_dict.get('top_p'):
                    config_dict['top_p'] = 0.9
            else:
                logger.warning(f"LLM配置不存在: ID={config_dict['llm_config_id']}")
                raise Exception(f"LLM配置不存在: ID={config_dict['llm_config_id']}")
        else:
            # 如果没有提供llm_config_id，验证必填字段
            if not config_dict.get('api_key'):
                raise Exception("未提供llm_config_id时，api_key为必填项")
            if not config_dict.get('base_url'):
                raise Exception("未提供llm_config_id时，base_url为必填项")
            if not config_dict.get('model_name'):
                raise Exception("未提供llm_config_id时，model_name为必填项")
            
            # 设置默认值
            if not config_dict.get('max_tokens'):
                config_dict['max_tokens'] = 4096
            if not config_dict.get('temperature'):
                config_dict['temperature'] = 0.7
            if not config_dict.get('top_p'):
                config_dict['top_p'] = 0.9
        
        # 确保API Key以明文形式保存到数据库
        logger.info(f"准备保存AI模型配置，API Key: {config_dict.get('api_key', 'None')[:10]}...")
        
        return await config_crud.create_crud(data=config_dict)
    
    @staticmethod
    async def get_active_config_by_role(db: AsyncSession, role: str) -> Optional[AIModelConfigModel]:
        """获取指定角色的活跃配置"""
        config_crud = AIModelConfigCRUD(db)
        return await config_crud.get_active_by_role(role)
    
    @staticmethod
    async def get_configs_by_type_and_role(
        db: AsyncSession,
        model_type: str,
        role: str
    ) -> List[AIModelConfigModel]:
        """获取指定模型类型和角色的配置"""
        config_crud = AIModelConfigCRUD(db)
        return await config_crud.get_by_model_type_and_role(model_type, role)
    
    @staticmethod
    async def get_all_active_configs(db: AsyncSession) -> List[AIModelConfigModel]:
        """获取所有活跃的配置"""
        config_crud = AIModelConfigCRUD(db)
        return await config_crud.get_active_configs()
    
    @staticmethod
    async def update_config(
        db: AsyncSession,
        config_id: int,
        update_data: AIModelConfigUpdateSchema
    ) -> Optional[AIModelConfigModel]:
        """更新AI模型配置"""
        config_crud = AIModelConfigCRUD(db)
        update_dict = update_data.dict(exclude_unset=True)
        
        # 检查API Key是否是脱敏值（包含****），如果是则从数据库保留原值
        if 'api_key' in update_dict and update_dict['api_key'] and '****' in update_dict['api_key']:
            logger.warning(f"检测到脱敏的API Key: {update_dict['api_key']}, 将保留数据库中的原值")
            # 获取当前配置
            current_config = await config_crud.get_by_id_crud(config_id)
            if current_config and current_config.api_key:
                # 检查数据库中的API Key是否也是脱敏值
                if '****' in current_config.api_key:
                    logger.error(f"数据库中的API Key也是脱敏值: {current_config.api_key}, 无法恢复明文")
                    # 删除这个字段，避免更新脱敏值
                    del update_dict['api_key']
                    logger.warning("跳过API Key更新，请重新输入完整的API Key")
                else:
                    update_dict['api_key'] = current_config.api_key
                    logger.info(f"保留原API Key: {current_config.api_key[:10]}...")
            else:
                # 如果数据库中也没有，则删除这个字段，避免更新
                del update_dict['api_key']
                logger.warning("数据库中也没有API Key，跳过更新")
        
        # 如果更新了llm_config_id，自动同步LLM配置的参数
        if 'llm_config_id' in update_dict and update_dict['llm_config_id']:
            from sqlalchemy import select
            from app.models.ai.llm_config import LLMConfigModel
            
            llm_stmt = select(LLMConfigModel).where(
                LLMConfigModel.id == update_dict['llm_config_id']
            )
            llm_result = await db.execute(llm_stmt)
            llm_config = llm_result.scalar_one_or_none()
            
            if llm_config:
                logger.info(f"自动同步LLM配置（ID: {llm_config.id}）的参数到AI模型配置")
                
                # 同步关键参数（更新时总是同步，确保一致性）
                # 确保API Key以明文形式保存
                update_dict['api_key'] = llm_config.api_key
                update_dict['base_url'] = llm_config.base_url
                update_dict['model_name'] = llm_config.model_name
                update_dict['max_tokens'] = llm_config.max_tokens
                update_dict['temperature'] = llm_config.temperature
                # top_p保持原值或使用默认值（LLM配置没有这个字段）
                if 'top_p' not in update_dict:
                    update_dict['top_p'] = 0.9
                
                logger.info(f"同步完成: API Key={llm_config.api_key[:10]}..., Base URL={llm_config.base_url}")
            else:
                logger.warning(f"LLM配置不存在: ID={update_dict['llm_config_id']}")
        
        return await config_crud.update_crud(config_id, update_dict)
    
    @staticmethod
    async def delete_config(db: AsyncSession, config_id: int) -> bool:
        """删除AI模型配置（硬删除）"""
        config_crud = AIModelConfigCRUD(db)
        try:
            # 先检查配置是否存在
            config = await config_crud.get_by_id_crud(config_id)
            if not config:
                return False
            
            # 检查是否有生成任务在使用此配置
            try:
                from sqlalchemy import select, or_
                from .model import TestCaseGenerationTaskModel
                
                check_stmt = select(TestCaseGenerationTaskModel).where(
                    or_(
                        TestCaseGenerationTaskModel.writer_model_config_id == config_id,
                        TestCaseGenerationTaskModel.reviewer_model_config_id == config_id
                    ),
                    TestCaseGenerationTaskModel.enabled_flag == 1
                )
                check_result = await db.execute(check_stmt)
                related_tasks = check_result.scalars().all()
                
                if related_tasks:
                    task_titles = [t.title for t in related_tasks[:3]]  # 只显示前3个
                    more_text = f" 等{len(related_tasks)}个任务" if len(related_tasks) > 3 else ""
                    raise Exception(f"无法删除，以下生成任务正在使用此配置: {', '.join(task_titles)}{more_text}")
            except Exception as check_error:
                if "无法删除" in str(check_error):
                    # 重新抛出业务异常
                    raise check_error
                else:
                    # 其他异常记录日志但不阻止删除
                    logger.warning(f"检查生成任务关联时出错: {check_error}")
            
            # 执行硬删除
            from sqlalchemy import delete
            from .model import AIModelConfigModel
            
            stmt = delete(AIModelConfigModel).where(AIModelConfigModel.id == config_id)
            await db.execute(stmt)
            await db.commit()
            
            logger.info(f"硬删除AI模型配置成功: ID={config_id}, Name={config.name}")
            return True
        except Exception as e:
            logger.error(f"删除AI模型配置失败: {e}")
            raise Exception(str(e))


class PromptConfigService:
    """提示词配置服务"""
    
    @staticmethod
    async def create_config(
        db: AsyncSession,
        config_data: PromptConfigCreateSchema,
        created_by: int
    ) -> PromptConfigModel:
        """创建提示词配置"""
        config_crud = PromptConfigCRUD(db)
        config_dict = config_data.dict()
        config_dict['created_by'] = created_by
        return await config_crud.create_crud(data=config_dict)
    
    @staticmethod
    async def get_active_config_by_type(db: AsyncSession, prompt_type: str) -> Optional[PromptConfigModel]:
        """获取指定类型的活跃提示词配置"""
        config_crud = PromptConfigCRUD(db)
        return await config_crud.get_active_by_type(prompt_type)
    
    @staticmethod
    async def get_configs_by_type(db: AsyncSession, prompt_type: str) -> List[PromptConfigModel]:
        """获取指定类型的所有提示词配置"""
        config_crud = PromptConfigCRUD(db)
        conditions = [
            PromptConfigModel.prompt_type == prompt_type,
            PromptConfigModel.enabled_flag == 1
        ]
        items, _ = await config_crud.get_list_crud(conditions=conditions)
        return items
    
    @staticmethod
    async def update_config(
        db: AsyncSession,
        config_id: int,
        update_data: PromptConfigUpdateSchema
    ) -> Optional[PromptConfigModel]:
        """更新提示词配置"""
        config_crud = PromptConfigCRUD(db)
        return await config_crud.update_crud(config_id, update_data.dict(exclude_unset=True))
    
    @staticmethod
    async def delete_config(db: AsyncSession, config_id: int) -> bool:
        """删除提示词配置"""
        config_crud = PromptConfigCRUD(db)
        try:
            await config_crud.soft_delete_crud([config_id])
            return True
        except Exception:
            return False


class TestCaseGenerationTaskService:
    """测试用例生成任务服务"""
    
    @staticmethod
    async def create_task(
        db: AsyncSession,
        task_data: TestCaseGenerationTaskCreateSchema,
        created_by: int
    ) -> TestCaseGenerationTaskModel:
        """创建测试用例生成任务"""
        task_crud = TestCaseGenerationTaskCRUD(db)
        task_dict = task_data.dict()
        task_dict.update({
            'task_id': str(uuid.uuid4()),
            'created_by': created_by
        })
        return await task_crud.create_crud(data=task_dict)
    
    @staticmethod
    async def get_task_by_id(db: AsyncSession, task_id: str) -> Optional[TestCaseGenerationTaskModel]:
        """根据任务ID获取任务"""
        task_crud = TestCaseGenerationTaskCRUD(db)
        return await task_crud.get_by_task_id(task_id)
    
    @staticmethod
    async def get_project_tasks(db: AsyncSession, project_id: int) -> List[TestCaseGenerationTaskModel]:
        """获取项目下的所有生成任务"""
        task_crud = TestCaseGenerationTaskCRUD(db)
        return await task_crud.get_by_project(project_id)
    
    @staticmethod
    async def get_tasks_by_status(db: AsyncSession, status: str) -> List[TestCaseGenerationTaskModel]:
        """根据状态获取任务"""
        task_crud = TestCaseGenerationTaskCRUD(db)
        return await task_crud.get_by_status(status)
    
    @staticmethod
    async def update_task(
        db: AsyncSession,
        task_id: str,
        update_data: TestCaseGenerationTaskUpdateSchema
    ) -> Optional[TestCaseGenerationTaskModel]:
        """更新任务"""
        task_crud = TestCaseGenerationTaskCRUD(db)
        task = await task_crud.get_by_task_id(task_id)
        if not task:
            return None
        return await task_crud.update_crud(task.id, update_data.dict(exclude_unset=True))
    
    @staticmethod
    async def update_stream_buffer(db: AsyncSession, task_id: str, chunk: str) -> bool:
        """更新流式输出缓冲区"""
        try:
            task_crud = TestCaseGenerationTaskCRUD(db)
            task = await task_crud.get_by_task_id(task_id)
            if not task:
                return False
            
            # 更新缓冲区
            current_buffer = task.stream_buffer or ""
            new_buffer = current_buffer + chunk
            new_position = len(new_buffer)
            
            update_data = TestCaseGenerationTaskUpdateSchema(
                stream_buffer=new_buffer,
                stream_position=new_position,
                last_stream_update=datetime.now()
            )
            
            await task_crud.update_crud(task.id, update_data.dict(exclude_unset=True))
            return True
        except Exception as e:
            logger.error(f"更新流式缓冲区失败: {e}")
            return False


class AIModelService:
    """AI模型调用服务"""
    
    @staticmethod
    async def call_openai_compatible_api(
        config: AIModelConfigModel,
        messages: List[Dict[str, str]],
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """调用OpenAI兼容格式的API"""
        headers = {
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json'
        }

        actual_max_tokens = max_tokens if max_tokens is not None else config.max_tokens

        data = {
            'model': config.model_name,
            'messages': messages,
            'max_tokens': actual_max_tokens,
            'temperature': config.temperature,
            'top_p': config.top_p,
            'stream': False
        }
        
        # 确保base_url不以/结尾
        base_url = config.base_url.rstrip('/')
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
        logger.info(f"原始base_url: {config.base_url}")
        logger.info(f"最终请求URL: {url}")
        logger.info(f"模型名称: {config.model_name}")

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
                
                # 检查响应体中的错误状态（某些API提供商会在HTTP 200中返回错误）
                if isinstance(result, dict):
                    # 检查是否有错误状态码
                    if 'status' in result and result['status'] != '200' and result['status'] != 200:
                        error_msg = result.get('msg', result.get('message', '未知错误'))
                        logger.error(f"API返回业务错误: status={result['status']}, msg={error_msg}")
                        raise Exception(f"API返回错误: {error_msg}")
                    
                    # 检查是否缺少必需的choices字段
                    if 'choices' not in result:
                        logger.error(f"API响应格式异常，缺少choices字段: {result}")
                        # 如果有错误信息，抛出更友好的错误
                        if 'msg' in result or 'message' in result:
                            error_msg = result.get('msg', result.get('message', ''))
                            raise Exception(f"API返回错误: {error_msg}")
                        raise Exception(f"API响应格式异常，缺少choices字段")
                
                logger.info(f"API调用成功")
                return result
        except httpx.HTTPStatusError as e:
            provider_name = config.model_type
            error_msg = f"{provider_name} API返回错误 {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.TimeoutException as e:
            provider_name = config.model_type
            logger.error(f"{provider_name} API请求超时: {repr(e)}")
            raise Exception(f"{provider_name} API请求超时，请稍后再试或检查网络连接")
        except Exception as e:
            provider_name = config.model_type
            logger.error(f"{provider_name} API调用失败: {repr(e)}")
            raise Exception(f"{provider_name} API调用失败: {str(e) or repr(e)}")
    
    @staticmethod
    async def call_openai_compatible_api_stream(
        config: AIModelConfigModel,
        messages: List[Dict[str, str]],
        callback=None,
        max_tokens: int = None
    ) -> AsyncIterator[str]:
        """流式调用OpenAI兼容格式的API，支持自动续写"""
        headers = {
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json'
        }

        actual_max_tokens = max_tokens if max_tokens is not None else config.max_tokens

        # 确保base_url不以/结尾
        base_url = config.base_url.rstrip('/')
        if not base_url.endswith('/chat/completions'):
            import re
            version_match = re.search(r'/v(\d+)/?$', base_url)
            if version_match:
                url = f"{base_url}/chat/completions"
            else:
                url = f"{base_url}/v1/chat/completions"
        else:
            url = base_url

        # 续写控制
        current_messages = list(messages)
        continuation_count = 0
        MAX_CONTINUATIONS = 5
        
        while continuation_count <= MAX_CONTINUATIONS:
            data = {
                'model': config.model_name,
                'messages': current_messages,
                'max_tokens': actual_max_tokens,
                'temperature': config.temperature,
                'top_p': config.top_p,
                'stream': True
            }

            logger.info(f"发起流式请求 (第{continuation_count+1}次), messages数量: {len(current_messages)}")

            chunk_content_buffer = ""
            finish_reason = None
            
            try:
                timeout_config = httpx.Timeout(
                    connect=60.0,
                    read=900.0,
                    write=60.0,
                    pool=60.0
                )
                async with httpx.AsyncClient(timeout=timeout_config, http2=False) as client:
                    async with client.stream('POST', url, headers=headers, json=data) as response:
                        if response.status_code != 200:
                            error_detail = await response.aread()
                            error_msg = error_detail.decode('utf-8')
                            logger.error(f"流式API调用返回错误: Status={response.status_code}, Body={error_msg}")
                            response.raise_for_status()
                        
                        logger.info(f"流式API响应状态码: {response.status_code}, Content-Type: {response.headers.get('content-type')}")
                        
                        line_count = 0
                        async for line in response.aiter_lines():
                            line_count += 1
                            if line_count <= 5:  # 记录前5行用于调试
                                logger.info(f"流式响应第{line_count}行: {line[:300]}")
                            
                            if not line.strip():
                                continue

                            # 添加调试日志
                            logger.debug(f"收到流式响应行: {line[:200]}")  # 只记录前200字符

                            if line.startswith('data: '):
                                data_str = line[6:]
                                if data_str.strip() == '[DONE]':
                                    logger.info("收到[DONE]标记，流式响应结束")
                                    break

                                try:
                                    chunk_data = json.loads(data_str)
                                    logger.debug(f"解析chunk数据: {chunk_data}")
                                    
                                    # 检查是否有错误状态（某些API在流式响应中也会返回错误）
                                    if isinstance(chunk_data, dict):
                                        if 'status' in chunk_data and chunk_data['status'] != '200' and chunk_data['status'] != 200:
                                            error_msg = chunk_data.get('msg', chunk_data.get('message', '未知错误'))
                                            logger.error(f"流式API返回业务错误: status={chunk_data['status']}, msg={error_msg}")
                                            raise Exception(f"API返回错误: {error_msg}")
                                    
                                    if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                        choice = chunk_data['choices'][0]
                                        delta = choice.get('delta', {})
                                        finish_reason = choice.get('finish_reason', None)
                                        content = delta.get('content', '')

                                        if content:
                                            chunk_content_buffer += content
                                            if callback:
                                                await callback(content)
                                            yield content
                                    else:
                                        logger.warning(f"chunk数据中没有choices或choices为空: {chunk_data}")

                                except json.JSONDecodeError as e:
                                    logger.warning(f"JSON解析失败: {data_str[:100]}, 错误: {e}")
                                    continue
                            else:
                                logger.debug(f"跳过非data行: {line[:100]}")
                        
                        logger.info(f"流式响应读取完成: 总行数={line_count}, chunk_content_buffer长度={len(chunk_content_buffer)}, finish_reason={finish_reason}")
            
                # 检查 finish_reason
                if finish_reason == 'length':
                    logger.warning(f"检测到生成被截断 (finish_reason='length')，准备自动续写。当前已续写 {continuation_count} 次。")
                    continuation_count += 1
                    
                    # 将本次生成的内容作为 assistant 回复加入历史
                    if current_messages[-1]['role'] == 'assistant':
                        current_messages[-1]['content'] += chunk_content_buffer
                    else:
                        current_messages.append({"role": "assistant", "content": chunk_content_buffer})
                    
                    # 添加续写指令
                    if current_messages[-1]['role'] != 'user':
                        current_messages.append({"role": "user", "content": "请继续输出剩余的内容，不要重复已输出的部分，紧接着上文继续。"})
                    
                    continue
                else:
                    logger.info(f"流式生成正常结束 (finish_reason={finish_reason})")
                    break

            except Exception as e:
                logger.error(f"流式请求异常: {e}")
                raise e
    
    @staticmethod
    async def generate_test_cases(
        db: AsyncSession,
        task: TestCaseGenerationTaskModel
    ) -> str:
        """生成测试用例"""
        writer_prompt = task.writer_prompt_config.content
        
        # 构建用户提示
        user_message = (
            f"请深入分析以下需求文档，并设计高覆盖率的测试用例。\n\n"
            f"【生成指令】\n"
            f"1. **数量原则**：请根据需求内容的实际复杂度，自动决定生成用例的数量。务必覆盖所有功能点、异常场景和边界条件，不设数量上限，应写尽写。\n"
            f"2. **深度遍历策略**：\n"
            f"   - 请按文档结构逐章节分析，不要遗漏末尾的功能点。\n"
            f"   - 对每个功能点，必须设计：1个正常场景 + 2-3个异常/边界场景。\n"
            f"3. **拒绝合并**：严禁将多个验证点合并在一条用例中。例如'验证输入框'应拆分为'输入为空'、'输入超长'、'输入特殊字符'等独立用例。\n"
            f"4. **场景扩展库**：\n"
            f"   - 数据完整性（必填项、默认值、数据类型）\n"
            f"   - 业务逻辑约束（状态流转、权限控制、重复操作）\n"
            f"   - 外部接口异常（超时、断网、返回错误）\n"
            f"   - UI交互体验（提示文案、跳转逻辑、防误触）\n"
            f"5. **⚠️ 输出顺序要求（必须严格执行）**：\n"
            f"   - **必须按用例编号从小到大的顺序输出**（如：001, 002, 003...或LOGIN_001, LOGIN_002, LOGIN_003...）\n"
            f"   - **绝对不能跳号、重复或乱序输出**\n"
            f"   - **编号必须连续，中间不能有遗漏**\n"
            f"   - **所有用例必须一次性完整输出，不能中断**\n"
            f"6. **⚠️ 特殊字符处理（关键）**：\n"
            f"   - **如果在表格内容（如操作步骤、预期结果）中出现管道符 '|'，请使用HTML实体 '&#124;' 代替**。\n"
            r"   - **绝对不要使用反斜杠转义（如 '\|'），这会导致输出混乱**。\n"
            r"   - 示例：应输入 'a&#124;b' 而不是 'a|b' 或 'a\|b'。\n\n"
            f"【需求文档内容】\n{task.requirement_text}"
        )
        
        messages = [
            {"role": "system", "content": writer_prompt},
            {"role": "user", "content": user_message}
        ]

        # 调用API生成测试用例
        response = await AIModelService.call_openai_compatible_api(
            task.writer_model_config,
            messages
        )

        return response['choices'][0]['message']['content']
    
    @staticmethod
    async def generate_test_cases_stream(
        db: AsyncSession,
        task: TestCaseGenerationTaskModel,
        callback=None
    ) -> str:
        """伪流式生成测试用例（使用非流式API + 模拟流式输出）
        
        由于某些API提供商不支持标准的SSE流式格式，我们使用伪流式方案：
        1. 调用非流式API获取完整内容
        2. 将内容分块，模拟流式输出给前端
        """
        import asyncio
        
        writer_prompt = task.writer_prompt_config.content

        # 构建用户提示
        user_message = (
            f"请深入分析以下需求文档，并设计高覆盖率的测试用例。\n\n"
            f"【生成指令】\n"
            f"1. **数量原则**：请根据需求内容的实际复杂度，自动决定生成用例的数量。务必覆盖所有功能点、异常场景和边界条件，不设数量上限，应写尽写。\n"
            f"2. **深度遍历策略**：\n"
            f"   - 请按文档结构逐章节分析，不要遗漏末尾的功能点。\n"
            f"   - 对每个功能点，必须设计：1个正常场景 + 2-3个异常/边界场景。\n"
            f"3. **拒绝合并**：严禁将多个验证点合并在一条用例中。例如'验证输入框'应拆分为'输入为空'、'输入超长'、'输入特殊字符'等独立用例。\n"
            f"4. **场景扩展库**：\n"
            f"   - 数据完整性（必填项、默认值、数据类型）\n"
            f"   - 业务逻辑约束（状态流转、权限控制、重复操作）\n"
            f"   - 外部接口异常（超时、断网、返回错误）\n"
            f"   - UI交互体验（提示文案、跳转逻辑、防误触）\n"
            f"5. **⚠️ 输出顺序要求（必须严格执行）**：\n"
            f"   - **必须按用例编号从小到大的顺序输出**（如：001, 002, 003...或LOGIN_001, LOGIN_002, LOGIN_003...）\n"
            f"   - **绝对不能跳号、重复或乱序输出**\n"
            f"   - **编号必须连续，中间不能有遗漏**\n"
            f"   - **所有用例必须一次性完整输出，不能中断**\n"
            f"6. **⚠️ 特殊字符处理（关键）**：\n"
            f"   - **如果在表格内容（如操作步骤、预期结果）中出现管道符 '|'，请使用HTML实体 '&#124;' 代替**。\n"
            r"   - **绝对不要使用反斜杠转义（如 '\|'），这会导致输出混乱**。\n"
            r"   - 示例：应输入 'a&#124;b' 而不是 'a|b' 或 'a\|b'。\n\n"
            f"【需求文档内容】\n{task.requirement_text}"
        )

        messages = [
            {"role": "system", "content": writer_prompt},
            {"role": "user", "content": user_message}
        ]
        
        logger.info(f"使用伪流式模式：调用非流式API获取完整内容")
        
        try:
            # 调用非流式API获取完整内容
            response = await AIModelService.call_openai_compatible_api(
                task.writer_model_config,
                messages
            )
            
            full_content = response['choices'][0]['message']['content']
            logger.info(f"非流式API返回完整内容，长度: {len(full_content)}")
            
            # 检查生成内容是否为空
            if len(full_content) == 0:
                logger.error(f"API返回空内容")
                raise Exception("API返回空内容，请检查提示词或需求文档")
            
            # 模拟流式输出：将内容分块发送给callback
            if callback:
                # 分块大小：每次发送100个字符（可调整以平衡性能和体验）
                chunk_size = 100
                total_chunks = (len(full_content) + chunk_size - 1) // chunk_size
                
                logger.info(f"开始模拟流式输出: 总长度={len(full_content)}, 分块大小={chunk_size}, 总块数={total_chunks}")
                
                for i in range(0, len(full_content), chunk_size):
                    chunk = full_content[i:i+chunk_size]
                    await callback(chunk)
                    
                    # 添加小延迟，模拟真实流式效果（避免数据库压力过大）
                    if i + chunk_size < len(full_content):  # 最后一块不延迟
                        await asyncio.sleep(0.1)  # 100ms延迟
                
                logger.info(f"模拟流式输出完成")
            
            return full_content
            
        except Exception as e:
            logger.error(f"伪流式生成失败: {e}")
            raise



class TestCaseTemplateService:
    """测试用例模板服务"""
    
    @staticmethod
    async def get_list(db: AsyncSession, template_type: Optional[str] = None):
        """获取模板列表"""
        from .crud import TestCaseTemplateCRUD
        crud = TestCaseTemplateCRUD(db)
        
        if template_type:
            return await crud.get_by_type(template_type)
        else:
            conditions = [crud.model.enabled_flag == 1]
            items, _ = await crud.get_list_crud(
                conditions=conditions,
                order_by=[crud.model.creation_date.desc()]
            )
            return items
    
    @staticmethod
    async def get_by_id(db: AsyncSession, template_id: int):
        """获取模板详情"""
        from .crud import TestCaseTemplateCRUD
        crud = TestCaseTemplateCRUD(db)
        return await crud.get_by_id_crud(template_id)
    
    @staticmethod
    async def get_default_template(db: AsyncSession, template_type: str = 'ui'):
        """获取默认模板"""
        from .crud import TestCaseTemplateCRUD
        crud = TestCaseTemplateCRUD(db)
        return await crud.get_default_template(template_type)
    
    @staticmethod
    async def create(db: AsyncSession, data, created_by: int):
        """创建模板"""
        from .crud import TestCaseTemplateCRUD
        crud = TestCaseTemplateCRUD(db)
        
        template_dict = data.dict()
        template_dict['created_by'] = created_by
        
        return await crud.create_crud(template_dict)
    
    @staticmethod
    async def update(db: AsyncSession, template_id: int, data, updated_by: int):
        """更新模板"""
        from .crud import TestCaseTemplateCRUD
        crud = TestCaseTemplateCRUD(db)
        
        # 检查模板是否存在
        template = await crud.get_by_id_crud(template_id)
        if not template:
            return None
        
        # 构建更新数据
        update_dict = data.dict(exclude_unset=True)
        update_dict['updated_by'] = updated_by
        update_dict['updation_date'] = datetime.now()
        
        return await crud.update_crud(template_id, update_dict)
    
    @staticmethod
    async def delete(db: AsyncSession, template_id: int):
        """删除模板（软删除）"""
        from .crud import TestCaseTemplateCRUD
        crud = TestCaseTemplateCRUD(db)
        
        # 检查模板是否存在
        template = await crud.get_by_id_crud(template_id)
        if not template:
            return False
        
        # 软删除
        await crud.update_crud(template_id, {'enabled_flag': 0})
        return True


class TestCaseParserService:
    """测试用例解析服务"""
    
    @staticmethod
    def parse_markdown_table(content: str) -> List[Dict[str, str]]:
        """解析Markdown表格"""
        # 移除代码块标记
        content = content.strip()
        if content.startswith('```markdown'):
            content = content.replace('```markdown\n', '', 1)
            content = content.rsplit('\n```', 1)[0]
        elif content.startswith('```'):
            content = content.replace('```\n', '', 1)
            content = content.rsplit('\n```', 1)[0]
        
        lines = content.split('\n')
        headers = []
        data_rows = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('|') and '---' not in line:
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                if not headers:
                    headers = cells
                else:
                    if cells and any(cells):
                        data_rows.append(dict(zip(headers, cells)))
        
        return data_rows
    
    @staticmethod
    def parse_steps(steps_text: str) -> List[str]:
        """解析操作步骤"""
        # 处理<br>标签
        steps_text = steps_text.replace('<br>', '\n').replace('<br/>', '\n')
        
        # 按行分割
        lines = steps_text.split('\n')
        steps = []
        
        for line in lines:
            line = line.strip()
            if line:
                # 移除序号（如 1. 2. 等）
                import re
                line = re.sub(r'^\d+\.\s*', '', line)
                if line:
                    steps.append(line)
        
        return steps
    
    @staticmethod
    def map_fields(row: Dict[str, str], field_mapping: dict) -> Dict[str, Any]:
        """根据模板映射字段"""
        result = {}
        
        for column in field_mapping.get('columns', []):
            source = column['source']
            target = column['target']
            value = row.get(source, '')
            
            # 类型转换
            if column['type'] == 'enum':
                value = column.get('values', {}).get(value, column.get('default', ''))
            elif column['type'] == 'text':
                value = value.replace('<br>', '\n').replace('<br/>', '\n')
            
            result[target] = value
        
        return result
    
    @staticmethod
    async def save_to_testcases(
        db: AsyncSession,
        task_id: str,
        ui_project_id: int,
        template_id: Optional[int],
        created_by: int
    ) -> int:
        """保存到测试用例"""
        from datetime import datetime
        
        # 1. 获取生成任务
        task = await TestCaseGenerationTaskService.get_task_by_id(db, task_id)
        if not task or not task.final_test_cases:
            raise Exception("任务不存在或没有生成用例")
        
        # 2. 获取模板
        if template_id:
            template = await TestCaseTemplateService.get_by_id(db, template_id)
        else:
            template = await TestCaseTemplateService.get_default_template(db)
        
        if not template:
            raise Exception("模板不存在")
        
        # 3. 解析用例
        rows = TestCaseParserService.parse_markdown_table(task.final_test_cases)
        
        if not rows:
            raise Exception("没有解析到有效的测试用例")
        
        # 4. 批量保存
        # 导入UI测试用例模型
        from sqlalchemy import text
        
        saved_count = 0
        for row in rows:
            mapped_data = TestCaseParserService.map_fields(row, template.field_mapping)
            
            # 创建测试用例
            insert_sql = text("""
                INSERT INTO ui_test_cases (
                    ui_project_id, name, description, priority, 
                    preconditions, expected_result, created_by, 
                    creation_date, enabled_flag
                ) VALUES (
                    :ui_project_id, :name, :description, :priority,
                    :preconditions, :expected_result, :created_by,
                    NOW(), 1
                )
            """)
            
            result = await db.execute(insert_sql, {
                'ui_project_id': ui_project_id,
                'name': mapped_data.get('name', '未命名用例'),
                'description': row.get('用例ID', ''),
                'priority': mapped_data.get('priority', 'medium'),
                'preconditions': mapped_data.get('preconditions', ''),
                'expected_result': mapped_data.get('expected_result', ''),
                'created_by': created_by
            })
            
            test_case_id = result.lastrowid
            
            # 解析并创建测试步骤
            if mapped_data.get('steps'):
                steps = TestCaseParserService.parse_steps(mapped_data['steps'])
                
                for idx, step in enumerate(steps, 1):
                    step_sql = text("""
                        INSERT INTO ui_test_steps (
                            test_case_id, step_number, action_type, 
                            description, created_by, creation_date
                        ) VALUES (
                            :test_case_id, :step_number, :action_type,
                            :description, :created_by, NOW()
                        )
                    """)
                    
                    await db.execute(step_sql, {
                        'test_case_id': test_case_id,
                        'step_number': idx,
                        'action_type': 'manual',
                        'description': step,
                        'created_by': created_by
                    })
            
            saved_count += 1
        
        await db.commit()
        
        # 注意：不再更新is_saved_to_records，允许重复保存到不同项目/模块
        
        return saved_count

    
    @staticmethod
    async def save_to_main_project_testcases(
        db: AsyncSession,
        task_id: str,
        project_id: int,
        template_id: Optional[int],
        created_by: int,
        module_id: Optional[int] = None
    ) -> int:
        """保存到主项目测试用例"""
        from datetime import datetime
        from loguru import logger
        
        logger.info(f"[保存用例] 开始保存: task_id={task_id}, project_id={project_id}, module_id={module_id}")
        
        # 1. 获取生成任务
        task = await TestCaseGenerationTaskService.get_task_by_id(db, task_id)
        if not task or not task.final_test_cases:
            raise Exception("任务不存在或没有生成用例")
        
        logger.info(f"[保存用例] 获取到任务，用例内容长度: {len(task.final_test_cases)}")
        
        # 2. 获取模板
        if template_id:
            template = await TestCaseTemplateService.get_by_id(db, template_id)
        else:
            template = await TestCaseTemplateService.get_default_template(db, 'main')
        
        if not template:
            raise Exception("模板不存在")
        
        logger.info(f"[保存用例] 使用模板: {template.name}")
        
        # 3. 解析用例
        rows = TestCaseParserService.parse_markdown_table(task.final_test_cases)
        
        if not rows:
            raise Exception("没有解析到有效的测试用例")
        
        logger.info(f"[保存用例] 解析到 {len(rows)} 个用例")
        
        # 4. 批量保存到主项目测试用例表
        from sqlalchemy import text
        
        saved_count = 0
        for row in rows:
            mapped_data = TestCaseParserService.map_fields(row, template.field_mapping)
            
            logger.info(f"[保存用例] 映射后的字段: {list(mapped_data.keys())}")
            logger.info(f"[保存用例] 标题: {mapped_data.get('title')}")
            
            # 创建测试用例
            insert_sql = text("""
                INSERT INTO test_cases (
                    project_id, module_id, title, description, priority, 
                    preconditions, expected_result, test_type,
                    status, author_id, created_by, 
                    creation_date, enabled_flag
                ) VALUES (
                    :project_id, :module_id, :title, :description, :priority,
                    :preconditions, :expected_result, :test_type,
                    'draft', :author_id, :created_by,
                    NOW(), 1
                )
            """)
            
            result = await db.execute(insert_sql, {
                'project_id': project_id,
                'module_id': module_id,
                'title': mapped_data.get('title', '未命名用例'),
                'description': mapped_data.get('description', row.get('用例ID', '')),
                'priority': mapped_data.get('priority', 'medium'),
                'preconditions': mapped_data.get('preconditions', ''),
                'expected_result': mapped_data.get('expected_result', ''),
                'test_type': mapped_data.get('test_type', 'functional'),
                'author_id': created_by,
                'created_by': created_by
            })
            
            test_case_id = result.lastrowid
            logger.info(f"[保存用例] 创建用例成功，ID: {test_case_id}")
            
            # 解析并创建测试步骤
            # 支持两种字段名：test_steps（主项目模板）和 steps（UI项目模板）
            steps_data = mapped_data.get('test_steps') or mapped_data.get('steps')
            logger.info(f"[保存用例] 测试步骤数据: {steps_data[:200] if steps_data else 'None'}")
            
            if steps_data:
                steps = TestCaseParserService.parse_steps(steps_data)
                logger.info(f"[保存用例] 解析到 {len(steps)} 个步骤")
                
                for idx, step in enumerate(steps, 1):
                    step_sql = text("""
                        INSERT INTO test_case_steps (
                            test_case_id, step_number, action, expected,
                            created_by, creation_date, enabled_flag
                        ) VALUES (
                            :test_case_id, :step_number, :action, :expected,
                            :created_by, NOW(), 1
                        )
                    """)
                    
                    await db.execute(step_sql, {
                        'test_case_id': test_case_id,
                        'step_number': idx,
                        'action': step,
                        'expected': '',  # 默认为空字符串
                        'created_by': created_by
                    })
                    logger.info(f"[保存用例] 保存步骤{idx}: {step[:50]}")
            else:
                logger.warning(f"[保存用例] 没有找到测试步骤数据！mapped_data keys: {list(mapped_data.keys())}")
            
            saved_count += 1
        
        await db.commit()
        logger.info(f"[保存用例] 提交事务成功，共保存 {saved_count} 个用例")
        
        # 注意：不再更新is_saved_to_records，允许重复保存到不同项目/模块
        
        return saved_count


    @staticmethod
    async def save_to_api_testcases(
        db: AsyncSession,
        task_id: str,
        api_project_id: int,
        template_id: Optional[int],
        created_by: int
    ) -> int:
        """保存到API测试用例"""
        from datetime import datetime
        
        # 1. 获取生成任务
        task = await TestCaseGenerationTaskService.get_task_by_id(db, task_id)
        if not task or not task.final_test_cases:
            raise Exception("任务不存在或没有生成用例")
        
        # 2. 获取模板
        if template_id:
            template = await TestCaseTemplateService.get_by_id(db, template_id)
        else:
            template = await TestCaseTemplateService.get_default_template(db, 'api')
        
        if not template:
            raise Exception("API模板不存在")
        
        # 3. 解析用例
        rows = TestCaseParserService.parse_markdown_table(task.final_test_cases)
        
        if not rows:
            raise Exception("没有解析到有效的测试用例")
        
        # 4. 获取或创建默认集合
        from sqlalchemy import text
        
        # 查找或创建"AI生成用例"集合
        collection_query = text("""
            SELECT id FROM api_collections
            WHERE api_project_id = :api_project_id 
              AND name = 'AI生成用例'
              AND enabled_flag = 1
            LIMIT 1
        """)
        result = await db.execute(collection_query, {'api_project_id': api_project_id})
        collection = result.fetchone()
        
        if collection:
            collection_id = collection[0]
        else:
            # 创建新集合
            create_collection_sql = text("""
                INSERT INTO api_collections (
                    api_project_id, name, description, 
                    created_by, creation_date, enabled_flag
                ) VALUES (
                    :api_project_id, 'AI生成用例', 'AI智能生成的测试用例',
                    :created_by, NOW(), 1
                )
            """)
            result = await db.execute(create_collection_sql, {
                'api_project_id': api_project_id,
                'created_by': created_by
            })
            collection_id = result.lastrowid
        
        # 5. 批量保存API请求
        saved_count = 0
        for row in rows:
            mapped_data = TestCaseParserService.map_fields(row, template.field_mapping)
            
            # 创建API请求
            insert_sql = text("""
                INSERT INTO api_requests (
                    collection_id, name, description, 
                    method, url, request_type,
                    headers, params, body,
                    assertions, created_by, 
                    creation_date, enabled_flag
                ) VALUES (
                    :collection_id, :name, :description,
                    :method, :url, 'single',
                    :headers, :params, :body,
                    :assertions, :created_by,
                    NOW(), 1
                )
            """)
            
            # 解析请求方法和URL
            method = mapped_data.get('method', 'GET').upper()
            url = mapped_data.get('url', '')
            
            # 解析headers（如果有）
            headers_json = json.dumps({})
            if mapped_data.get('headers'):
                try:
                    headers_json = json.dumps(json.loads(mapped_data['headers']))
                except:
                    headers_json = json.dumps({})
            
            # 解析params（如果有）
            params_json = json.dumps({})
            if mapped_data.get('params'):
                try:
                    params_json = json.dumps(json.loads(mapped_data['params']))
                except:
                    params_json = json.dumps({})
            
            # 解析body（如果有）
            body_json = json.dumps({})
            if mapped_data.get('body'):
                try:
                    body_json = json.dumps(json.loads(mapped_data['body']))
                except:
                    body_json = json.dumps({})
            
            # 解析assertions（如果有）
            assertions_json = json.dumps([])
            if mapped_data.get('assertions'):
                try:
                    assertions_json = json.dumps(json.loads(mapped_data['assertions']))
                except:
                    # 简单的断言格式：状态码200
                    assertions_json = json.dumps([{
                        'type': 'status_code',
                        'operator': 'equals',
                        'expected': '200'
                    }])
            
            await db.execute(insert_sql, {
                'collection_id': collection_id,
                'name': mapped_data.get('name', '未命名API用例'),
                'description': mapped_data.get('description', row.get('用例ID', '')),
                'method': method,
                'url': url,
                'headers': headers_json,
                'params': params_json,
                'body': body_json,
                'assertions': assertions_json,
                'created_by': created_by
            })
            
            saved_count += 1
        
        await db.commit()
        
        # 6. 更新任务状态
        from .schema import TestCaseGenerationTaskUpdateSchema
        await TestCaseGenerationTaskService.update_task(
            db,
            task_id,
            TestCaseGenerationTaskUpdateSchema(
                is_saved_to_records=True,
                saved_at=datetime.now()
            )
        )
        await db.commit()
        
        return saved_count



class AICaseService:
    """AI智能浏览器用例服务"""
    
    @staticmethod
    async def execute_ai_case(
        db: AsyncSession,
        case_id: int,
        user_id: int,
        headless: bool = False
    ) -> Dict[str, Any]:
        """执行AI用例
        
        Args:
            db: 数据库会话
            case_id: 用例ID
            user_id: 执行用户ID
            headless: 是否无头模式
        
        Returns:
            执行结果字典
        """
        from app.services.ai.browser_use_service import BrowserUseService
        from .model import AICaseModel, AIExecutionRecordModel
        
        execution_id = None
        execution_crud = AIExecutionRecordCRUD(db)
        
        try:
            # 1. 获取用例信息
            case_crud = AICaseCRUD(db)
            case = await case_crud.get_by_id_crud(case_id)
            if not case:
                # 即使用例不存在，也创建一个失败记录
                execution_data = {
                    'ai_case_id': case_id,
                    'case_name': f'用例ID:{case_id}',
                    'task_description': '用例不存在',
                    'execution_mode': 'text',
                    'status': 'failed',
                    'executed_by': user_id,
                    'created_by': user_id,
                    'start_time': datetime.now(),
                    'end_time': datetime.now(),
                    'duration': 0,
                    'error_message': '用例不存在',
                    'logs': f'[错误] 用例ID {case_id} 不存在\n'
                }
                execution = await execution_crud.create_crud(execution_data)
                await db.commit()
                logger.error(f"用例不存在: case_id={case_id}")
                raise ValueError("用例不存在")
            
            # 2. 获取AI模型配置（browser_use_text角色）
            model_config_crud = AIModelConfigCRUD(db)
            model_config = await model_config_crud.get_active_by_role('browser_use_text')
            if not model_config:
                # 创建失败记录
                execution_data = {
                    'ui_project_id': case.ui_project_id,
                    'ai_case_id': case.id,
                    'case_name': case.name,
                    'task_description': case.task_description,
                    'execution_mode': 'text',
                    'status': 'failed',
                    'executed_by': user_id,
                    'created_by': user_id,
                    'start_time': datetime.now(),
                    'end_time': datetime.now(),
                    'duration': 0,
                    'error_message': '未找到Browser-use模型配置',
                    'logs': '[错误] 未找到Browser-use模型配置，请先在AI模型配置中添加browser_use_text角色的配置\n'
                }
                execution = await execution_crud.create_crud(execution_data)
                await db.commit()
                logger.error("未找到Browser-use模型配置")
                raise ValueError("未找到Browser-use模型配置，请先在AI模型配置中添加browser_use_text角色的配置")
            
            # 3. 创建执行记录
            execution_data = {
                'ui_project_id': case.ui_project_id,
                'ai_case_id': case.id,
                'case_name': case.name,
                'task_description': case.task_description,
                'execution_mode': 'text',
                'status': 'running',
                'executed_by': user_id,
                'created_by': user_id,
                'start_time': datetime.now(),
                'logs': '开始执行AI用例...\n'
            }
            execution = await execution_crud.create_crud(execution_data)
            await db.commit()  # 立即提交，确保前端能查询到
            await db.refresh(execution)  # 刷新对象
            execution_id = execution.id
            
            logger.info(f"✅ 创建执行记录成功: execution_id={execution_id}, case_id={case_id}, case_name={case.name}")
            
            # 4. 执行Browser-use任务
            browser_service = BrowserUseService({
                'api_key': model_config.api_key,
                'base_url': model_config.base_url,
                'model_name': model_config.model_name,
                'temperature': model_config.temperature or 0.7,
                'max_tokens': model_config.max_tokens or 4096
            })
            
            # 进度回调函数
            async def progress_callback(step_info: Dict[str, Any]):
                """更新执行进度"""
                try:
                    # 重新获取执行记录
                    exec_record = await execution_crud.get_by_id_crud(execution_id)
                    if exec_record:
                        # 追加日志
                        current_logs = exec_record.logs or "开始执行AI用例...\n"
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        new_log = f"[{timestamp}] 步骤{step_info.get('step_number', '?')}: {step_info.get('action', '执行中')}"
                        exec_record.logs = current_logs + new_log + "\n"
                        
                        # 更新步骤列表
                        steps = exec_record.steps_completed or []
                        steps.append(step_info.get('action', '执行中'))
                        exec_record.steps_completed = steps
                        
                        await db.commit()
                        await db.refresh(exec_record)
                        
                        logger.debug(f"更新执行进度: step={len(steps)}, action={step_info.get('action')}")
                except Exception as e:
                    logger.error(f"更新执行进度失败: {e}", exc_info=True)
            
            # 执行任务
            result = await browser_service.execute_task(
                task=case.task_description,
                headless=headless,
                callback=progress_callback
            )
            
            # 5. 更新执行记录
            execution = await execution_crud.get_by_id_crud(execution_id)
            execution.status = result['status']
            execution.end_time = datetime.now()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
            execution.steps_completed = result['steps']
            
            # 保留之前的进度日志，追加最终结果
            current_logs = execution.logs or "开始执行AI用例...\n"
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # 追加最终日志
            if result['logs']:
                final_logs = "\n".join(result['logs'])
                execution.logs = current_logs + f"\n[{timestamp}] 执行完成\n{final_logs}\n"
            else:
                execution.logs = current_logs + f"\n[{timestamp}] 执行完成\n"
            
            execution.gif_path = result.get('gif_path')
            
            if result['error']:
                execution.error_message = result['error']
            
            await db.commit()
            
            logger.info(f"✅ AI用例执行完成: case_id={case_id}, execution_id={execution_id}, status={result['status']}")
            
            return {
                'execution_id': execution.id,
                'status': execution.status,
                'duration': execution.duration,
                'steps_count': len(result['steps'])
            }
            
        except Exception as e:
            logger.error(f"❌ 执行AI用例失败: case_id={case_id}, error={str(e)}", exc_info=True)
            
            # 更新执行记录为失败状态（如果已创建）
            if execution_id:
                try:
                    execution = await execution_crud.get_by_id_crud(execution_id)
                    if execution:
                        execution.status = 'failed'
                        execution.end_time = datetime.now()
                        execution.duration = (execution.end_time - execution.start_time).total_seconds()
                        execution.error_message = str(e)
                        
                        # 保留之前的进度日志，追加失败信息
                        current_logs = execution.logs or "开始执行AI用例...\n"
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        
                        # 添加详细的错误信息
                        import traceback
                        error_traceback = traceback.format_exc()
                        
                        execution.logs = (
                            current_logs + 
                            f"\n[{timestamp}] ========== 执行失败 ==========\n" +
                            f"错误类型: {type(e).__name__}\n" +
                            f"错误信息: {str(e)}\n" +
                            f"\n详细堆栈:\n{error_traceback}\n" +
                            f"========================================\n"
                        )
                        
                        await db.commit()
                        await db.refresh(execution)
                        
                        logger.info(f"✅ 执行记录已更新为失败状态: execution_id={execution_id}")
                except Exception as update_error:
                    logger.error(f"❌ 更新失败状态时出错: {update_error}", exc_info=True)
            
            # 不要抛出异常，让后台任务正常结束
            return {
                'execution_id': execution_id,
                'status': 'failed',
                'error': str(e)
            }
