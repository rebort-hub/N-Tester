# -*- coding: utf-8 -*-
"""
AI智能化模块控制器
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.db.sqlalchemy import get_db
from app.core.dependencies import get_current_user_id
from app.common.response import success_response, error_response

from .schema import (
    RequirementDocumentOutSchema,
    RequirementDocumentCreateSchema,
    RequirementDocumentUpdateSchema,
    AIModelConfigOutSchema,
    AIModelConfigCreateSchema,
    AIModelConfigUpdateSchema,
    PromptConfigOutSchema,
    PromptConfigCreateSchema,
    PromptConfigUpdateSchema,
    TestCaseGenerationTaskOutSchema,
    TestCaseGenerationTaskCreateSchema,
    TestCaseGenerationTaskUpdateSchema,
    AICaseOutSchema,
    AICaseCreateSchema,
    AICaseUpdateSchema,
    AIExecutionRecordOutSchema,
    AIExecutionRecordCreateSchema,
    AIExecutionRecordUpdateSchema,
    StreamChunkSchema,
    TaskStatusSchema,
    TestCaseTemplateCreateSchema,
    TestCaseTemplateUpdateSchema,
    TestCaseTemplateOutSchema,
    SaveToTestCaseSchema,
    FigmaConfigCreateSchema,
    FigmaConfigUpdateSchema,
    FigmaConfigOutSchema,
    AITestReportCreateSchema,
    AITestReportOutSchema
)
from .service import (
    RequirementDocumentService,
    AIModelConfigService,
    PromptConfigService,
    TestCaseGenerationTaskService,
    AIModelService,
    TestCaseTemplateService,
    TestCaseParserService
)
from .crud import (
    AIModelConfigCRUD,
    PromptConfigCRUD,
    TestCaseGenerationTaskCRUD
)

router = APIRouter()


# ==================== 需求文档管理 ====================

@router.get("/requirement-documents")
async def get_requirement_documents(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取需求文档列表"""
    try:
        from sqlalchemy import select
        from .model import RequirementAnalysisModel
        
        if project_id:
            documents = await RequirementDocumentService.get_project_documents(db, project_id)
        else:
            documents = await RequirementDocumentService.get_all_documents(db)
        
       
        result = []
        for doc in documents:
            # 检查是否有分析记录
            stmt = select(RequirementAnalysisModel).where(
                RequirementAnalysisModel.document_id == doc.id,
                RequirementAnalysisModel.enabled_flag == 1
            )
            analysis_result = await db.execute(stmt)
            analysis = analysis_result.scalar_one_or_none()
            has_analysis = analysis is not None
            
            doc_dict = {
                'id': doc.id,
                'project_id': doc.project_id,
                'title': doc.title,
                'file_path': doc.file_path,
                'document_type': doc.document_type,
                'status': doc.status,
                'file_size': doc.file_size,
                'extracted_text': doc.extracted_text,
                'uploaded_by': doc.uploaded_by,
                'creation_date': doc.creation_date.isoformat() if doc.creation_date else None,
                'updation_date': doc.updation_date.isoformat() if doc.updation_date else None,
                'has_analysis': has_analysis
            }
            result.append(doc_dict)
        
        return success_response(data=result)
    except Exception as e:
        return error_response(message=f"获取需求文档失败: {str(e)}")


@router.post("/requirement-documents")
async def create_requirement_document(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    title: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """上传需求文档"""
    try:
        # 检查文件类型
        allowed_types = ['pdf', 'docx', 'txt', 'md']
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in allowed_types:
            raise HTTPException(status_code=400, detail="不支持的文件类型")
        
        # 保存文件
        import os
        from datetime import datetime
        from app.utils.document_extractor import DocumentExtractor
        
        upload_dir = f"static/upload/requirement_docs/{datetime.now().strftime('%Y%m%d')}"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = f"{upload_dir}/{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 提取文本内容
        extracted_text = DocumentExtractor.extract_text(file_path, file_extension)
        
        # 创建文档记录
        document_data = RequirementDocumentCreateSchema(
            project_id=project_id,
            title=title,
            document_type=file_extension
        )
        
        document = await RequirementDocumentService.create_document(
            db, document_data, file_path, len(content), current_user_id, extracted_text
        )
        
        # 转换为字典返回
        doc_dict = {
            'id': document.id,
            'project_id': document.project_id,
            'title': document.title,
            'file_path': document.file_path,
            'document_type': document.document_type,
            'status': document.status,
            'file_size': document.file_size,
            'extracted_text': document.extracted_text,
            'uploaded_by': document.uploaded_by,
            'creation_date': document.creation_date.isoformat() if document.creation_date else None,
            'updation_date': document.updation_date.isoformat() if document.updation_date else None,
            'has_analysis': False
        }
        
        return success_response(data=doc_dict)
    except Exception as e:
        return error_response(message=f"上传需求文档失败: {str(e)}")


@router.get("/requirement-documents/{document_id}")
async def get_requirement_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取需求文档详情"""
    try:
        from sqlalchemy import select
        from .model import RequirementAnalysisModel
        
        document = await RequirementDocumentService.get_document_with_analysis(db, document_id)
        if not document:
            return error_response(message="需求文档不存在", code=404)
        
        # 检查是否有分析记录
        stmt = select(RequirementAnalysisModel).where(
            RequirementAnalysisModel.document_id == document_id,
            RequirementAnalysisModel.enabled_flag == 1
        )
        result = await db.execute(stmt)
        analysis = result.scalar_one_or_none()
        has_analysis = analysis is not None
        
        # 转换为字典，避免懒加载
        doc_dict = {
            'id': document.id,
            'project_id': document.project_id,
            'title': document.title,
            'file_path': document.file_path,
            'document_type': document.document_type,
            'status': document.status,
            'file_size': document.file_size,
            'extracted_text': document.extracted_text,
            'uploaded_by': document.uploaded_by,
            'creation_date': document.creation_date.isoformat() if document.creation_date else None,
            'updation_date': document.updation_date.isoformat() if document.updation_date else None,
            'has_analysis': has_analysis
        }
        
        return success_response(data=doc_dict)
    except Exception as e:
        return error_response(message=f"获取需求文档失败: {str(e)}")


@router.put("/requirement-documents/{document_id}")
async def update_requirement_document(
    document_id: int,
    document_update: RequirementDocumentUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新需求文档"""
    try:
        document = await RequirementDocumentService.update_document(db, document_id, document_update)
        if not document:
            raise HTTPException(status_code=404, detail="需求文档不存在")
        
        return success_response(data=document)
    except Exception as e:
        return error_response(message=f"更新需求文档失败: {str(e)}")


@router.delete("/requirement-documents/{document_id}")
async def delete_requirement_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除需求文档"""
    try:
        success = await RequirementDocumentService.delete_document(db, document_id)
        if not success:
            return error_response(message="需求文档不存在", code=404)
        
        return success_response(message="删除成功")
    except Exception as e:
        return error_response(message=f"删除需求文档失败: {str(e)}")


@router.post("/requirement-documents/{document_id}/analyze")
async def analyze_requirement_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """分析需求文档"""
    try:
        from app.db.sqlalchemy import async_session_factory
        
        # 后台执行分析
        async def run_analysis():
            """后台执行需求分析"""
            async with async_session_factory() as db_session:
                try:
                    await RequirementDocumentService.analyze_document(
                        db_session, document_id, current_user_id
                    )
                except Exception as e:
                    logger.error(f"后台执行需求分析失败: {str(e)}", exc_info=True)
        
        # 添加后台任务
        background_tasks.add_task(run_analysis)
        
        return success_response(message="需求分析已启动，请稍后查看结果")
    except Exception as e:
        logger.error(f"启动需求分析失败: {str(e)}")
        return error_response(message=f"启动失败: {str(e)}")


@router.get("/requirement-documents/{document_id}/analysis")
async def get_document_analysis(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取文档分析结果"""
    try:
        from sqlalchemy import select
        from .model import RequirementAnalysisModel, BusinessRequirementModel
        from .crud import RequirementAnalysisCRUD, BusinessRequirementCRUD
        
        # 获取分析记录
        analysis_crud = RequirementAnalysisCRUD(db)
        stmt = select(RequirementAnalysisModel).where(
            RequirementAnalysisModel.document_id == document_id,
            RequirementAnalysisModel.enabled_flag == 1
        ).order_by(RequirementAnalysisModel.creation_date.desc())
        result = await db.execute(stmt)
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            return error_response(message="未找到分析结果，请先执行分析", code=404)
        
        # 获取业务需求
        requirement_crud = BusinessRequirementCRUD(db)
        stmt = select(BusinessRequirementModel).where(
            BusinessRequirementModel.analysis_id == analysis.id,
            BusinessRequirementModel.enabled_flag == 1
        ).order_by(BusinessRequirementModel.requirement_id)
        result = await db.execute(stmt)
        requirements = result.scalars().all()
        
        # 统计模块
        modules = {}
        for req in requirements:
            if req.module not in modules:
                modules[req.module] = 0
            modules[req.module] += 1
        
        return success_response(data={
            'analysis': {
                'id': analysis.id,
                'analysis_report': analysis.analysis_report,
                'requirements_count': analysis.requirements_count,
                'analysis_time': analysis.analysis_time,
                'created_at': analysis.creation_date.isoformat() if analysis.creation_date else None
            },
            'requirements': [
                {
                    'id': req.id,
                    'requirement_id': req.requirement_id,
                    'requirement_name': req.requirement_name,
                    'requirement_type': req.requirement_type,
                    'module': req.module,
                    'requirement_level': req.requirement_level,
                    'description': req.description,
                    'acceptance_criteria': req.acceptance_criteria,
                    'parent_requirement_id': req.parent_requirement_id
                }
                for req in requirements
            ],
            'modules': modules
        })
    except Exception as e:
        logger.error(f"获取分析结果失败: {str(e)}", exc_info=True)
        return error_response(message=f"获取失败: {str(e)}")


# ==================== AI模型配置 ====================

@router.get("/ai-model-configs")
async def get_ai_model_configs(
    role: Optional[str] = None,
    model_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取AI模型配置列表"""
    try:
        if role and model_type:
            configs = await AIModelConfigService.get_configs_by_type_and_role(db, model_type, role)
        elif role:
            # 按角色筛选
            config_crud = AIModelConfigCRUD(db)
            from .model import AIModelConfigModel
            conditions = [
                AIModelConfigModel.role == role,
                AIModelConfigModel.enabled_flag == 1
            ]
            items, _ = await config_crud.get_list_crud(conditions=conditions)
            configs = items
        else:
            config_crud = AIModelConfigCRUD(db)
            from .model import AIModelConfigModel
            conditions = [AIModelConfigModel.enabled_flag == 1]
            items, _ = await config_crud.get_list_crud(conditions=conditions)
            configs = items
        
        # 转换为字典并脱敏API Key
        result = []
        for config in configs:
            config_dict = {
                'id': config.id,
                'config_name': config.name,  
                'name': config.name,
                'provider': config.model_type,  
                'model_type': config.model_type,
                'role': config.role,
                'api_key': config.api_key[:8] + "****" + config.api_key[-4:] if config.api_key else None,
                'base_url': config.base_url,
                'model_name': config.model_name,
                'max_tokens': config.max_tokens,
                'temperature': config.temperature,
                'top_p': config.top_p,
                'is_active': config.is_active,
                'llm_config_id': config.llm_config_id,
                'creation_date': config.creation_date.isoformat() if config.creation_date else None,
                'updation_date': config.updation_date.isoformat() if config.updation_date else None
            }
            result.append(config_dict)
        
        return success_response(data=result)
    except Exception as e:
        return error_response(message=f"获取AI模型配置失败: {str(e)}")


@router.post("/ai-model-configs")
async def create_ai_model_config(
    config_data: AIModelConfigCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建AI模型配置"""
    try:
        config = await AIModelConfigService.create_config(db, config_data, current_user_id)
        
        # 转换为字典并脱敏API Key
        config_dict = {
            'id': config.id,
            'config_name': config.name,
            'name': config.name,
            'provider': config.model_type,
            'model_type': config.model_type,
            'role': config.role,
            'api_key': config.api_key[:8] + "****" + config.api_key[-4:] if config.api_key else None,
            'base_url': config.base_url,
            'model_name': config.model_name,
            'max_tokens': config.max_tokens,
            'temperature': config.temperature,
            'top_p': config.top_p,
            'is_active': config.is_active,
            'llm_config_id': config.llm_config_id,
            'creation_date': config.creation_date.isoformat() if config.creation_date else None,
            'updation_date': config.updation_date.isoformat() if config.updation_date else None
        }
        
        return success_response(data=config_dict)
    except Exception as e:
        return error_response(message=f"创建AI模型配置失败: {str(e)}")


@router.get("/ai-model-configs/{config_id}")
async def get_ai_model_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取AI模型配置详情"""
    try:
        config_crud = AIModelConfigCRUD(db)
        config = await config_crud.get_by_id_crud(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="AI模型配置不存在")
        
        # 转换为字典并脱敏API Key
        config_dict = {
            'id': config.id,
            'config_name': config.name,
            'name': config.name,
            'provider': config.model_type,
            'model_type': config.model_type,
            'role': config.role,
            'api_key': config.api_key[:8] + "****" + config.api_key[-4:] if config.api_key else None,
            'base_url': config.base_url,
            'model_name': config.model_name,
            'max_tokens': config.max_tokens,
            'temperature': config.temperature,
            'top_p': config.top_p,
            'is_active': config.is_active,
            'llm_config_id': config.llm_config_id,
            'creation_date': config.creation_date.isoformat() if config.creation_date else None,
            'updation_date': config.updation_date.isoformat() if config.updation_date else None
        }
        
        return success_response(data=config_dict)
    except Exception as e:
        return error_response(message=f"获取AI模型配置失败: {str(e)}")


@router.put("/ai-model-configs/{config_id}")
async def update_ai_model_config(
    config_id: int,
    config_update: AIModelConfigUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新AI模型配置"""
    try:
        config = await AIModelConfigService.update_config(db, config_id, config_update)
        if not config:
            raise HTTPException(status_code=404, detail="AI模型配置不存在")
        
        # 转换为字典并脱敏API Key
        config_dict = {
            'id': config.id,
            'config_name': config.name,
            'name': config.name,
            'provider': config.model_type,
            'model_type': config.model_type,
            'role': config.role,
            'api_key': config.api_key[:8] + "****" + config.api_key[-4:] if config.api_key else None,
            'base_url': config.base_url,
            'model_name': config.model_name,
            'max_tokens': config.max_tokens,
            'temperature': config.temperature,
            'top_p': config.top_p,
            'is_active': config.is_active,
            'llm_config_id': config.llm_config_id,
            'creation_date': config.creation_date.isoformat() if config.creation_date else None,
            'updation_date': config.updation_date.isoformat() if config.updation_date else None
        }
        
        return success_response(data=config_dict)
    except Exception as e:
        return error_response(message=f"更新AI模型配置失败: {str(e)}")


@router.delete("/ai-model-configs/{config_id}")
async def delete_ai_model_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除AI模型配置（硬删除）"""
    try:
        await AIModelConfigService.delete_config(db, config_id)
        return success_response(message="删除成功")
    except Exception as e:
        error_msg = str(e)
        if "无法删除" in error_msg:
            return error_response(message=error_msg, code=400)
        elif "不存在" in error_msg:
            return error_response(message="AI模型配置不存在", code=404)
        else:
            return error_response(message=f"删除AI模型配置失败: {error_msg}")


# ==================== 提示词配置 ====================

@router.get("/prompt-configs")
async def get_prompt_configs(
    prompt_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取提示词配置列表"""
    try:
        if prompt_type:
            configs = await PromptConfigService.get_configs_by_type(db, prompt_type)
        else:
            config_crud = PromptConfigCRUD(db)
            from .model import PromptConfigModel
            conditions = [PromptConfigModel.enabled_flag == 1]
            items, _ = await config_crud.get_list_crud(conditions=conditions)
            configs = items
        
        return success_response(data=configs)
    except Exception as e:
        return error_response(message=f"获取提示词配置失败: {str(e)}")


@router.post("/prompt-configs")
async def create_prompt_config(
    config_data: PromptConfigCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建提示词配置"""
    try:
        config = await PromptConfigService.create_config(db, config_data, current_user_id)
        return success_response(data=config)
    except Exception as e:
        return error_response(message=f"创建提示词配置失败: {str(e)}")


@router.get("/prompt-configs/{config_id}")
async def get_prompt_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取提示词配置详情"""
    try:
        config_crud = PromptConfigCRUD(db)
        config = await config_crud.get_by_id_crud(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="提示词配置不存在")
        
        return success_response(data=config)
    except Exception as e:
        return error_response(message=f"获取提示词配置失败: {str(e)}")


@router.put("/prompt-configs/{config_id}")
async def update_prompt_config(
    config_id: int,
    config_update: PromptConfigUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新提示词配置"""
    try:
        config = await PromptConfigService.update_config(db, config_id, config_update)
        if not config:
            raise HTTPException(status_code=404, detail="提示词配置不存在")
        
        return success_response(data=config)
    except Exception as e:
        return error_response(message=f"更新提示词配置失败: {str(e)}")


@router.delete("/prompt-configs/{config_id}")
async def delete_prompt_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除提示词配置"""
    try:
        success = await PromptConfigService.delete_config(db, config_id)
        if not success:
            raise HTTPException(status_code=404, detail="提示词配置不存在")
        
        return success_response(message="删除成功")
    except Exception as e:
        return error_response(message=f"删除提示词配置失败: {str(e)}")


# ==================== 测试用例生成任务 ====================

@router.get("/generation-tasks")
async def get_generation_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    title: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取测试用例生成任务列表（支持分页和搜索）"""
    try:
        from .model import TestCaseGenerationTaskModel
        
        task_crud = TestCaseGenerationTaskCRUD(db)
        
        # 构建查询条件
        conditions = [TestCaseGenerationTaskModel.enabled_flag == 1]
        
        if project_id:
            conditions.append(TestCaseGenerationTaskModel.project_id == project_id)
        if status:
            conditions.append(TestCaseGenerationTaskModel.status == status)
        if title:
            conditions.append(TestCaseGenerationTaskModel.title.like(f"%{title}%"))
        
        # 计算skip
        skip = (page - 1) * page_size
        
        # 分页查询
        items, total = await task_crud.get_list_crud(
            conditions=conditions,
            skip=skip,
            limit=page_size,
            order_by=[TestCaseGenerationTaskModel.creation_date.desc()]
        )
        
        # 返回包含total的响应
        response = success_response(data=items)
        response['total'] = total
        return response
    except Exception as e:
        logger.error(f"获取生成任务失败: {str(e)}")
        return error_response(message=f"获取生成任务失败: {str(e)}")


@router.post("/generation-tasks")
async def create_generation_task(
    task_data: TestCaseGenerationTaskCreateSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建测试用例生成任务"""
    try:
        task = await TestCaseGenerationTaskService.create_task(db, task_data, current_user_id)
        await db.commit()
        
        # 启动后台任务（无论是流式还是批量模式）
        background_tasks.add_task(start_generation_task, task.task_id)
        
        logger.info(f"创建生成任务成功: {task.task_id}, 输出模式: {task.output_mode}")
        
        return success_response(data=task)
    except Exception as e:
        logger.error(f"创建生成任务失败: {str(e)}")
        return error_response(message=f"创建生成任务失败: {str(e)}")


@router.get("/generation-tasks/{task_id}")
async def get_generation_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取测试用例生成任务详情"""
    try:
        task = await TestCaseGenerationTaskService.get_task_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="生成任务不存在")
        
        return success_response(data=task)
    except Exception as e:
        return error_response(message=f"获取生成任务失败: {str(e)}")


@router.get("/generation-tasks/{task_id}/stream")
async def stream_generation_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """流式获取生成任务输出"""
    try:
        task = await TestCaseGenerationTaskService.get_task_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="生成任务不存在")
        
        async def generate():
            import asyncio
            last_position = 0
            while True:
                # 重新获取任务状态
                current_task = await TestCaseGenerationTaskService.get_task_by_id(db, task_id)
                if not current_task:
                    break
                
                # 检查是否有新内容
                if current_task.stream_buffer and len(current_task.stream_buffer) > last_position:
                    new_content = current_task.stream_buffer[last_position:]
                    last_position = len(current_task.stream_buffer)
                    
                    chunk_data = StreamChunkSchema(
                        task_id=task_id,
                        chunk=new_content,
                        position=last_position,
                        is_complete=current_task.status in ['completed', 'failed']
                    )
                    yield f"data: {chunk_data.json()}\n\n"
                
                # 如果任务完成，结束流式输出
                if current_task.status in ['completed', 'failed']:
                    break
                
                # 等待一段时间再检查
                await asyncio.sleep(1)
        
        return StreamingResponse(generate(), media_type="text/plain")
    except Exception as e:
        return error_response(message=f"流式获取失败: {str(e)}")


# ==================== AI智能浏览器用例 ====================

@router.get("/ai-cases")
async def get_ai_cases(
    ui_project_id: Optional[int] = None,
    source_project_id: Optional[int] = None,
    source_module_id: Optional[int] = None,
    status: Optional[str] = None,
    source_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取AI智能浏览器用例列表
    
    支持的查询参数：
    - ui_project_id: UI项目ID
    - source_project_id: 来源项目ID（测试管理项目）
    - source_module_id: 来源模块ID（测试管理模块）
    - status: 状态（draft/active/archived）
    - source_type: 来源类型（manual/import/testcase）
    - page: 页码
    - page_size: 每页数量
    """
    try:
        from .model import AICaseModel, AIExecutionRecordModel
        from sqlalchemy import select, and_, func, desc
        
        # 构建查询条件
        conditions = [AICaseModel.enabled_flag == 1]
        
        if ui_project_id:
            conditions.append(AICaseModel.ui_project_id == ui_project_id)
        
        if source_project_id:
            conditions.append(AICaseModel.source_project_id == source_project_id)
        
        if source_module_id:
            conditions.append(AICaseModel.source_module_id == source_module_id)
        
        if status:
            conditions.append(AICaseModel.status == status)
        
        if source_type:
            conditions.append(AICaseModel.source_type == source_type)
        
        # 查询总数
        count_stmt = select(func.count(AICaseModel.id)).where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # 查询数据（分页）
        offset = (page - 1) * page_size
        stmt = (
            select(AICaseModel)
            .where(and_(*conditions))
            .order_by(desc(AICaseModel.creation_date))
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        cases = result.scalars().all()
        
        # 获取每个用例的执行统计
        cases_data = []
        for case in cases:
            # 查询执行次数
            exec_count_stmt = select(func.count(AIExecutionRecordModel.id)).where(
                and_(
                    AIExecutionRecordModel.ai_case_id == case.id,
                    AIExecutionRecordModel.enabled_flag == 1
                )
            )
            exec_count_result = await db.execute(exec_count_stmt)
            execution_count = exec_count_result.scalar() or 0
            
            # 查询最后一次执行记录
            last_exec_stmt = (
                select(AIExecutionRecordModel)
                .where(
                    and_(
                        AIExecutionRecordModel.ai_case_id == case.id,
                        AIExecutionRecordModel.enabled_flag == 1
                    )
                )
                .order_by(desc(AIExecutionRecordModel.start_time))
                .limit(1)
            )
            last_exec_result = await db.execute(last_exec_stmt)
            last_execution = last_exec_result.scalar_one_or_none()
            
            case_dict = {
                'id': case.id,
                'case_id': f"AI{str(case.id).zfill(6)}",
                'ui_project_id': case.ui_project_id,
                'source_project_id': case.source_project_id,
                'source_module_id': case.source_module_id,
                'name': case.name,
                'title': case.name,  # 前端使用title字段
                'description': case.description,
                'task_description': case.task_description,
                'status': case.status or 'active',
                'source_type': case.source_type or 'manual',
                'priority': case.priority or 'P2',
                'precondition': case.precondition,
                'test_steps': case.test_steps or [],
                'expected_result': case.expected_result,
                'execution_mode': case.execution_mode or 'headless',
                'timeout': case.timeout or 300,
                'execution_count': execution_count,
                'last_execution_status': last_execution.status if last_execution else None,
                'last_execution_time': last_execution.start_time.isoformat() if last_execution and last_execution.start_time else None,
                'created_by': case.created_by,
                'creation_date': case.creation_date.isoformat() if case.creation_date else None,
                'updation_date': case.updation_date.isoformat() if case.updation_date else None,
            }
            cases_data.append(case_dict)
        
        return success_response(data={
            'items': cases_data,
            'total': total,
            'page': page,
            'page_size': page_size
        })
    except Exception as e:
        logger.error(f"获取AI用例失败: {str(e)}", exc_info=True)
        return error_response(message=f"获取AI用例失败: {str(e)}")


@router.post("/ai-cases")
async def create_ai_case(
    case_data: AICaseCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建AI智能浏览器用例"""
    try:
        from .crud import AICaseCRUD
        case_crud = AICaseCRUD(db)
        case_dict = case_data.dict()
        case_dict['created_by'] = current_user_id
        
        case = await case_crud.create_crud(data=case_dict)
        return success_response(data=case)
    except Exception as e:
        return error_response(message=f"创建AI用例失败: {str(e)}")


@router.get("/ai-cases/{case_id}")
async def get_ai_case(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取AI智能浏览器用例详情"""
    try:
        from .crud import AICaseCRUD
        case_crud = AICaseCRUD(db)
        case = await case_crud.get_by_id_crud(case_id)
        if not case:
            return error_response(message="AI用例不存在", code=404)
        
        return success_response(data=case)
    except Exception as e:
        return error_response(message=f"获取AI用例失败: {str(e)}")


@router.put("/ai-cases/{case_id}")
async def update_ai_case(
    case_id: int,
    case_data: AICaseUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新AI智能浏览器用例"""
    try:
        from .crud import AICaseCRUD
        case_crud = AICaseCRUD(db)
        
        # 检查用例是否存在
        case = await case_crud.get_by_id_crud(case_id)
        if not case:
            return error_response(message="AI用例不存在", code=404)
        
        # 更新用例
        update_dict = case_data.dict(exclude_unset=True)
        updated_case = await case_crud.update_crud(case_id, update_dict)
        
        return success_response(data=updated_case)
    except Exception as e:
        return error_response(message=f"更新AI用例失败: {str(e)}")


@router.delete("/ai-cases/{case_id}")
async def delete_ai_case(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除AI智能浏览器用例（硬删除）"""
    try:
        from .crud import AICaseCRUD
        case_crud = AICaseCRUD(db)
        
        # 检查用例是否存在
        case = await case_crud.get_by_id_crud(case_id)
        if not case:
            return error_response(message="AI用例不存在", code=404)
        
        # 硬删除
        await case_crud.delete_crud([case_id])
        
        return success_response(message="删除成功")
    except Exception as e:
        logger.error(f"删除AI用例失败: {str(e)}", exc_info=True)
        return error_response(message=f"删除AI用例失败: {str(e)}")


@router.post("/ai-cases/batch-delete")
async def batch_delete_ai_cases(
    delete_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """批量删除AI智能浏览器用例
    
    Args:
        delete_data: 删除数据，包含：
            - case_ids: 用例ID列表
    
    Returns:
        删除结果
    """
    try:
        case_ids = delete_data.get('case_ids', [])
        
        if not case_ids:
            return error_response(message="请选择要删除的用例")
        
        logger.info(f"开始批量删除AI用例: case_ids={case_ids}")
        
        from .crud import AICaseCRUD
        case_crud = AICaseCRUD(db)
        
        
        await case_crud.delete_crud(case_ids)
        
        logger.info(f"成功删除 {len(case_ids)} 个AI用例")
        
        return success_response(
            data={'deleted_count': len(case_ids)},
            message=f"成功删除 {len(case_ids)} 个用例"
        )
    except Exception as e:
        logger.error(f"批量删除AI用例失败: {str(e)}", exc_info=True)
        return error_response(message=f"批量删除AI用例失败: {str(e)}")


@router.post("/ai-cases/{case_id}/execute")
async def execute_ai_case(
    case_id: int,
    headless: bool = Query(False, description="是否无头模式"),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """执行AI智能浏览器用例
    
    Args:
        case_id: 用例ID
        headless: 是否无头模式（默认False，显示浏览器窗口）
    
    Returns:
        执行启动结果
    """
    try:
        from .service import AICaseService
        from app.db.sqlalchemy import async_session_factory
        
        # 后台执行任务
        async def run_execution():
            """后台执行AI用例"""
            async with async_session_factory() as db_session:
                try:
                    await AICaseService.execute_ai_case(
                        db_session, case_id, current_user_id, headless
                    )
                except Exception as e:
                    logger.error(f"后台执行AI用例失败: {str(e)}", exc_info=True)
        
        # 添加后台任务
        background_tasks.add_task(run_execution)
        
        return success_response(message="AI用例执行已启动，请稍后查看执行记录")
    except Exception as e:
        logger.error(f"启动AI用例执行失败: {str(e)}")
        return error_response(message=f"启动执行失败: {str(e)}")


@router.post("/ai-cases/batch-execute")
async def batch_execute_ai_cases(
    batch_data: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """批量执行AI用例
    
    Args:
        batch_data: 批量执行数据，包含：
            - task_name: 任务名称
            - execution_mode: 执行模式（headless/headed）
            - parallel_count: 并行数量
            - case_ids: 用例ID列表
    
    Returns:
        执行结果
    """
    try:
        task_name = batch_data.get('task_name', '批量执行任务')
        execution_mode = batch_data.get('execution_mode', 'headless')
        parallel_count = batch_data.get('parallel_count', 1)
        case_ids = batch_data.get('case_ids', [])
        
        if not case_ids:
            return error_response(message="请至少选择一个用例")
        
        headless = execution_mode == 'headless'
        
        logger.info(f"开始批量执行AI用例: task_name={task_name}, case_ids={case_ids}, headless={headless}")
        
        # 导入服务
        from .service import AICaseService
        from app.db.sqlalchemy import async_session_factory
        
        # 后台批量执行任务
        async def run_batch_execution():
            """后台批量执行AI用例"""
            async with async_session_factory() as db_session:
                try:
                    # 根据并行数量执行
                    if parallel_count == 1:
                        # 串行执行
                        for case_id in case_ids:
                            try:
                                await AICaseService.execute_ai_case(
                                    db_session, case_id, current_user_id, headless
                                )
                            except Exception as e:
                                logger.error(f"执行用例 {case_id} 失败: {str(e)}", exc_info=True)
                                continue
                    else:
                        # 并行执行（简单实现，未来可优化）
                        import asyncio
                        tasks = []
                        for case_id in case_ids:
                            task = AICaseService.execute_ai_case(
                                db_session, case_id, current_user_id, headless
                            )
                            tasks.append(task)
                        
                        # 等待所有任务完成
                        await asyncio.gather(*tasks, return_exceptions=True)
                    
                    logger.info(f"批量执行完成: {len(case_ids)} 个用例")
                except Exception as e:
                    logger.error(f"批量执行AI用例失败: {str(e)}", exc_info=True)
        
        # 添加后台任务
        background_tasks.add_task(run_batch_execution)
        
        return success_response(
            message=f"批量执行任务已创建，共 {len(case_ids)} 个用例",
            data={
                'task_name': task_name,
                'case_count': len(case_ids),
                'execution_mode': execution_mode
            }
        )
    except Exception as e:
        logger.error(f"启动批量执行失败: {str(e)}")
        return error_response(message=f"启动批量执行失败: {str(e)}")


@router.post("/ai-cases/import-from-modules")
async def import_ai_cases_from_modules(
    import_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """从测试用例模块批量导入AI用例
    
    Args:
        import_data: 导入数据，包含：
            - project_id: 项目ID
            - module_ids: 模块ID列表
    
    Returns:
        导入结果
    """
    try:
        project_id = import_data.get('project_id')
        module_ids = import_data.get('module_ids', [])
        
        if not project_id:
            return error_response(message="项目ID不能为空")
        
        if not module_ids:
            return error_response(message="请至少选择一个模块")
        
        logger.info(f"开始从模块导入AI用例: project_id={project_id}, module_ids={module_ids}")
        
        # 查询测试用例
        from sqlalchemy import select, and_, text as sql_text
        
        # 使用原生SQL查询测试用例表
        sql = sql_text("""
            SELECT 
                tc.id, 
                tc.title, 
                tc.description, 
                tc.project_id, 
                tc.module_id,
                tc.preconditions,
                tc.expected_result,
                tc.priority
            FROM test_cases tc
            WHERE tc.project_id = :project_id
            AND tc.module_id IN :module_ids
            AND tc.enabled_flag = 1
        """)
        
        result = await db.execute(
            sql,
            {
                'project_id': project_id,
                'module_ids': tuple(module_ids) if len(module_ids) > 1 else (module_ids[0],)
            }
        )
        testcases = result.fetchall()
        
        logger.info(f"查询到 {len(testcases)} 个测试用例")
        
        # 批量创建AI用例
        from .model import AICaseModel
        imported_count = 0
        skipped_count = 0
        
        for testcase in testcases:
            try:
                # 检查是否已导入（避免重复）
                check_stmt = select(AICaseModel).where(
                    and_(
                        AICaseModel.name == testcase.title,
                        AICaseModel.ui_project_id == project_id,
                        AICaseModel.enabled_flag == 1
                    )
                )
                check_result = await db.execute(check_stmt)
                existing = check_result.scalar_one_or_none()
                
                if existing:
                    logger.info(f"用例已存在，跳过: {testcase.title}")
                    skipped_count += 1
                    continue
                
                # 查询测试步骤
                steps_sql = sql_text("""
                    SELECT step_number, action, expected
                    FROM test_case_steps
                    WHERE test_case_id = :test_case_id
                    AND enabled_flag = 1
                    ORDER BY step_number
                """)
                steps_result = await db.execute(steps_sql, {'test_case_id': testcase.id})
                steps = steps_result.fetchall()
                
                # 格式化测试步骤为JSON数组
                test_steps = []
                if steps:
                    for step in steps:
                        test_steps.append({
                            'step_num': step.step_number,
                            'description': step.action,
                            'expected': step.expected or ''
                        })
                
                # 转换优先级格式（如果有）
                priority_map = {
                    'critical': 'P0',
                    'high': 'P1',
                    'medium': 'P2',
                    'low': 'P3'
                }
                priority = priority_map.get(testcase.priority, 'P2') if hasattr(testcase, 'priority') and testcase.priority else 'P2'
                
                # 创建AI用例
                ai_case = AICaseModel(
                    ui_project_id=project_id,
                    source_project_id=project_id,  
                    source_module_id=testcase.module_id,  
                    name=testcase.title,
                    description=testcase.description or f"从测试用例导入: {testcase.title}",
                    task_description=testcase.description or testcase.title,
                    precondition=testcase.preconditions if hasattr(testcase, 'preconditions') else '',  # 前置条件
                    test_steps=test_steps,  
                    expected_result=testcase.expected_result if hasattr(testcase, 'expected_result') else '',  # 预期结果
                    status='active', 
                    source_type='testcase',  
                    priority=priority, 
                    created_by=current_user_id,
                    enabled_flag=1
                )
                
                db.add(ai_case)
                imported_count += 1
                logger.info(f"成功导入用例: {testcase.title}, 包含 {len(test_steps)} 个测试步骤")
                
            except Exception as e:
                logger.error(f"导入用例失败: {testcase.title}, 错误: {str(e)}")
                continue
        
        await db.commit()
        
        logger.info(f"成功导入 {imported_count} 个AI用例，跳过 {skipped_count} 个已存在的用例")
        
        return success_response(
            data={
                'imported_count': imported_count,
                'skipped_count': skipped_count,
                'total_found': len(testcases)
            },
            message=f"成功导入 {imported_count} 个用例，跳过 {skipped_count} 个已存在的用例"
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"批量导入AI用例失败: {str(e)}", exc_info=True)
        return error_response(message=f"导入失败: {str(e)}")


@router.post("/ai-cases/import-from-excel")
async def import_ai_cases_from_excel(
    file: UploadFile = File(...),
    project_id: Optional[int] = Form(None),
    module_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """从Excel导入AI智能浏览器测试用例
    
    支持两种导入模式：
    1. 单模块模式：指定project_id和module_id，导入所有Sheet到同一个模块
    2. 多模块模式：指定project_id，每个Sheet名称对应一个模块名称
    
    Args:
        file: Excel文件
        project_id: 项目ID（必需）
        module_id: 模块ID（可选，如果指定则所有用例导入到该模块）
    
    Returns:
        导入结果
    """
    try:
        # 检查文件类型
        if not file.filename.endswith(('.xlsx', '.xls')):
            return error_response(message="只支持Excel文件（.xlsx, .xls）")
        
        # 项目ID是必需的
        if not project_id:
            return error_response(message="请选择项目")
        
        logger.info(f"开始导入Excel文件: {file.filename}, 项目ID: {project_id}, 模块ID: {module_id}")
        
        # 读取文件内容
        file_content = await file.read()
        
        # 使用Excel导入器解析
        from app.utils.excel_importer import ExcelImporter
        import pandas as pd
        from io import BytesIO
        
        # 读取Excel文件，获取所有Sheet
        excel_file = BytesIO(file_content)
        excel_data = pd.ExcelFile(excel_file)
        sheet_names = excel_data.sheet_names
        
        logger.info(f"Excel文件包含 {len(sheet_names)} 个Sheet: {sheet_names}")
        
        # 如果指定了模块ID，所有Sheet导入到同一个模块
        if module_id:
            logger.info(f"单模块模式：所有Sheet导入到模块 {module_id}")
            
            default_values = {
                'ui_project_id': project_id,
                'source_project_id': project_id,
                'source_module_id': module_id,
                'created_by': current_user_id,
                'enabled_flag': 1
            }
            
            import_result = ExcelImporter.import_ai_cases(file_content, default_values)
            
            if not import_result['success']:
                return error_response(
                    message=f"导入失败: {'; '.join(import_result['errors'])}",
                    data=import_result
                )
            
            # 批量创建AI用例
            imported_count, skipped_count, error_count = await _batch_create_cases(
                db, import_result['cases'], project_id, module_id
            )
            
        else:
            # 多模块模式：每个Sheet对应一个模块
            logger.info(f"多模块模式：每个Sheet对应一个模块")
            
            # 获取项目下的所有模块
            from sqlalchemy import select, text
            
            # 使用原生SQL查询避免模型重复定义问题
            query = text("""
                SELECT id, name 
                FROM module_info 
                WHERE project_id = :project_id AND enabled_flag = 1
            """)
            result = await db.execute(query, {"project_id": project_id})
            modules = result.fetchall()
            
            # 构建模块名称到ID的映射
            module_map = {row.name: row.id for row in modules}
            logger.info(f"项目 {project_id} 下的模块: {list(module_map.keys())}")
            
            imported_count = 0
            skipped_count = 0
            error_count = 0
            sheet_results = []
            
            # 遍历每个Sheet
            for sheet_name in sheet_names:
                try:
                    logger.info(f"处理Sheet: {sheet_name}")
                    
                    # 查找对应的模块
                    target_module_id = module_map.get(sheet_name)
                    
                    if not target_module_id:
                        logger.warning(f"Sheet '{sheet_name}' 没有对应的模块，跳过")
                        sheet_results.append({
                            'sheet': sheet_name,
                            'status': 'skipped',
                            'message': f"未找到名为 '{sheet_name}' 的模块"
                        })
                        continue
                    
                    # 读取该Sheet的数据
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    
                    if df.empty:
                        logger.info(f"Sheet '{sheet_name}' 为空，跳过")
                        continue
                    
                    # 将DataFrame转换为字节流
                    sheet_buffer = BytesIO()
                    with pd.ExcelWriter(sheet_buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    sheet_buffer.seek(0)
                    sheet_content = sheet_buffer.read()
                    
                    # 解析该Sheet的用例
                    default_values = {
                        'ui_project_id': project_id,
                        'source_project_id': project_id,
                        'source_module_id': target_module_id,
                        'created_by': current_user_id,
                        'enabled_flag': 1
                    }
                    
                    import_result = ExcelImporter.import_ai_cases(sheet_content, default_values)
                    
                    if not import_result['success']:
                        logger.error(f"Sheet '{sheet_name}' 解析失败: {import_result['errors']}")
                        sheet_results.append({
                            'sheet': sheet_name,
                            'status': 'error',
                            'message': '; '.join(import_result['errors'])
                        })
                        continue
                    
                    # 批量创建该Sheet的用例
                    sheet_imported, sheet_skipped, sheet_error = await _batch_create_cases(
                        db, import_result['cases'], project_id, target_module_id
                    )
                    
                    imported_count += sheet_imported
                    skipped_count += sheet_skipped
                    error_count += sheet_error
                    
                    sheet_results.append({
                        'sheet': sheet_name,
                        'module_id': target_module_id,
                        'status': 'success',
                        'imported': sheet_imported,
                        'skipped': sheet_skipped,
                        'errors': sheet_error
                    })
                    
                    logger.info(f"Sheet '{sheet_name}' 导入完成: 成功{sheet_imported}, 跳过{sheet_skipped}, 失败{sheet_error}")
                    
                except Exception as e:
                    logger.error(f"处理Sheet '{sheet_name}' 失败: {str(e)}", exc_info=True)
                    sheet_results.append({
                        'sheet': sheet_name,
                        'status': 'error',
                        'message': str(e)
                    })
                    continue
        
        await db.commit()
        
        logger.info(f"Excel导入完成: 成功{imported_count}个，跳过{skipped_count}个，失败{error_count}个")
        
        response_data = {
            'imported_count': imported_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'mode': 'single_module' if module_id else 'multi_module'
        }
        
        if not module_id:
            response_data['sheet_results'] = sheet_results
        
        return success_response(
            data=response_data,
            message=f"成功导入 {imported_count} 个用例，跳过 {skipped_count} 个已存在的用例"
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Excel导入失败: {str(e)}", exc_info=True)
        return error_response(message=f"导入失败: {str(e)}")


async def _batch_create_cases(
    db: AsyncSession,
    cases: list,
    project_id: int,
    module_id: int
) -> tuple:
    """批量创建AI用例
    
    Returns:
        (imported_count, skipped_count, error_count)
    """
    from .model import AICaseModel
    from sqlalchemy import select, and_
    
    imported_count = 0
    skipped_count = 0
    error_count = 0
    
    for case_data in cases:
        try:
            # 检查是否已存在（根据名称、项目ID和模块ID）
            check_conditions = [
                AICaseModel.name == case_data['name'],
                AICaseModel.ui_project_id == project_id,
                AICaseModel.source_module_id == module_id,
                AICaseModel.enabled_flag == 1
            ]
            
            check_stmt = select(AICaseModel).where(and_(*check_conditions))
            check_result = await db.execute(check_stmt)
            existing = check_result.scalar_one_or_none()
            
            if existing:
                logger.info(f"用例已存在，跳过: {case_data['name']} (项目:{project_id}, 模块:{module_id})")
                skipped_count += 1
                continue
            
            # 创建AI用例
            ai_case = AICaseModel(**case_data)
            db.add(ai_case)
            imported_count += 1
            
        except Exception as e:
            logger.error(f"创建用例失败: {case_data.get('name')}, 错误: {str(e)}")
            error_count += 1
            continue
    
    return imported_count, skipped_count, error_count


@router.get("/ai-cases/excel-template")
async def download_excel_template():
    """下载AI测试用例Excel模板
    
    Returns:
        Excel文件
    """
    try:
        from app.utils.excel_importer import ExcelImporter
        from fastapi.responses import FileResponse
        import tempfile
        from pathlib import Path
        
        logger.info("开始生成Excel模板...")
        
        # 创建临时目录
        temp_dir = Path(tempfile.gettempdir()) / "ai_templates"
        temp_dir.mkdir(exist_ok=True)
        template_path = temp_dir / "AI_TestCase_Template.xlsx"
        
        # 生成模板内容
        template_content = ExcelImporter.generate_template()
        
        # 写入文件
        with open(template_path, "wb") as f:
            f.write(template_content)
        
        logger.info(f"Excel模板生成成功: {template_path}, 大小: {len(template_content)} 字节")
        
        # 使用FileResponse返回文件
        return FileResponse(
            path=str(template_path),
            filename="AI_TestCase_Template.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        logger.error(f"生成Excel模板失败: {str(e)}", exc_info=True)
        return error_response(message=f"生成模板失败: {str(e)}")


# ==================== AI执行记录 ====================

@router.get("/ai-execution-records")
async def get_ai_execution_records(
    ui_project_id: Optional[int] = None,
    ai_case_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取AI执行记录列表
    
    支持的查询参数：
    - ui_project_id: UI项目ID
    - ai_case_id: AI用例ID
    - status: 执行状态（pending/running/completed/success/failed/stopped）
    - start_date: 开始日期（YYYY-MM-DD）
    - end_date: 结束日期（YYYY-MM-DD）
    - page: 页码
    - page_size: 每页数量
    """
    try:
        from .crud import AIExecutionRecordCRUD
        from .model import AIExecutionRecordModel, AICaseModel, AIModelConfigModel
        from sqlalchemy import and_, or_, select
        from datetime import datetime
        
        record_crud = AIExecutionRecordCRUD(db)
        
        # 构建查询条件
        conditions = [AIExecutionRecordModel.enabled_flag == 1]
        
        if ui_project_id:
            conditions.append(AIExecutionRecordModel.ui_project_id == ui_project_id)
        
        if ai_case_id:
            conditions.append(AIExecutionRecordModel.ai_case_id == ai_case_id)
        
        if status:
            # 兼容多种状态值
            if status in ['completed', 'success']:
                conditions.append(or_(
                    AIExecutionRecordModel.status == 'completed',
                    AIExecutionRecordModel.status == 'success'
                ))
            else:
                conditions.append(AIExecutionRecordModel.status == status)
        
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                conditions.append(AIExecutionRecordModel.start_time >= start_dt)
            except ValueError:
                logger.warning(f"Invalid start_date format: {start_date}")
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                # 包含结束日期的全天
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                conditions.append(AIExecutionRecordModel.start_time <= end_dt)
            except ValueError:
                logger.warning(f"Invalid end_date format: {end_date}")
        
        # 分页查询
        skip = (page - 1) * page_size
        items, total = await record_crud.get_list_crud(
            conditions=conditions,
            skip=skip,
            limit=page_size,
            order_by=[AIExecutionRecordModel.start_time.desc()]
        )
        
        # 获取Browser-use角色的AI模型配置（用于显示）
        browser_use_config = None
        stmt = select(AIModelConfigModel).where(
            AIModelConfigModel.role == 'browser_use_text',
            AIModelConfigModel.is_active == True,
            AIModelConfigModel.enabled_flag == 1
        ).order_by(AIModelConfigModel.creation_date.desc())
        result = await db.execute(stmt)
        browser_use_config = result.scalar_one_or_none()
        
        # 增强返回数据，添加用例名称和AI模型配置
        enhanced_items = []
        for item in items:
            item_dict = {
                'id': item.id,
                'ui_project_id': item.ui_project_id,
                'ai_case_id': item.ai_case_id,
                'case_name': item.case_name,  # 用例名称快照
                'task_description': item.task_description,
                'execution_mode': item.execution_mode,
                'status': item.status,
                'start_time': item.start_time.isoformat() if item.start_time else None,
                'end_time': item.end_time.isoformat() if item.end_time else None,
                'duration': item.duration,
                'logs': item.logs,
                'error_message': item.error_message,
                'steps_completed': item.steps_completed,
                'planned_tasks': item.planned_tasks,
                'executed_by': item.executed_by,
                'gif_path': item.gif_path,
                'screenshots_sequence': item.screenshots_sequence,
                'total_tokens': item.total_tokens,
                'prompt_tokens': item.prompt_tokens,
                'completion_tokens': item.completion_tokens,
                'api_calls': item.api_calls,
                'creation_date': item.creation_date.isoformat() if item.creation_date else None,
                'updation_date': item.updation_date.isoformat() if item.updation_date else None,
                # 添加AI模型配置信息
                'llm_config_name': browser_use_config.name if browser_use_config else None,
                'llm_model_name': browser_use_config.model_name if browser_use_config else None,
            }
            enhanced_items.append(item_dict)
        
        return success_response(data={
            'items': enhanced_items,
            'total': total,
            'page': page,
            'page_size': page_size
        })
    except Exception as e:
        logger.error(f"获取AI执行记录失败: {str(e)}", exc_info=True)
        return error_response(message=f"获取AI执行记录失败: {str(e)}")


@router.post("/ai-execution-records")
async def create_ai_execution_record(
    record_data: AIExecutionRecordCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建AI执行记录"""
    try:
        from .crud import AIExecutionRecordCRUD
        record_crud = AIExecutionRecordCRUD(db)
        record_dict = record_data.dict()
        record_dict['executed_by'] = current_user_id
        
        record = await record_crud.create_crud(data=record_dict)
        return success_response(data=record)
    except Exception as e:
        return error_response(message=f"创建AI执行记录失败: {str(e)}")


@router.get("/ai-execution-records/{execution_id}")
async def get_execution_record(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取AI执行记录详情
    
    Args:
        execution_id: 执行记录ID
    
    Returns:
        执行记录详细信息
    """
    try:
        from .crud import AIExecutionRecordCRUD
        from .model import AIModelConfigModel
        from sqlalchemy import select
        
        record_crud = AIExecutionRecordCRUD(db)
        execution = await record_crud.get_by_id_crud(execution_id)
        
        if not execution:
            return error_response(message="执行记录不存在", code=404)
        
        # 获取Browser-use角色的AI模型配置
        stmt = select(AIModelConfigModel).where(
            AIModelConfigModel.role == 'browser_use_text',
            AIModelConfigModel.is_active == True,
            AIModelConfigModel.enabled_flag == 1
        ).order_by(AIModelConfigModel.creation_date.desc())
        result = await db.execute(stmt)
        browser_use_config = result.scalar_one_or_none()
        
        # 增强返回数据
        execution_dict = {
            'id': execution.id,
            'ui_project_id': execution.ui_project_id,
            'ai_case_id': execution.ai_case_id,
            'case_name': execution.case_name,
            'task_description': execution.task_description,
            'execution_mode': execution.execution_mode,
            'status': execution.status,
            'start_time': execution.start_time.isoformat() if execution.start_time else None,
            'end_time': execution.end_time.isoformat() if execution.end_time else None,
            'duration': execution.duration,
            'logs': execution.logs,
            'error_message': execution.error_message,
            'steps_completed': execution.steps_completed,
            'planned_tasks': execution.planned_tasks,
            'executed_by': execution.executed_by,
            'gif_path': execution.gif_path,
            'screenshots_sequence': execution.screenshots_sequence,
            'total_tokens': execution.total_tokens,
            'prompt_tokens': execution.prompt_tokens,
            'completion_tokens': execution.completion_tokens,
            'api_calls': execution.api_calls,
            'creation_date': execution.creation_date.isoformat() if execution.creation_date else None,
            'updation_date': execution.updation_date.isoformat() if execution.updation_date else None,
            # 添加AI模型配置信息
            'llm_config_name': browser_use_config.name if browser_use_config else None,
            'llm_model_name': browser_use_config.model_name if browser_use_config else None,
        }
        
        return success_response(data=execution_dict)
    except Exception as e:
        logger.error(f"获取执行记录详情失败: {str(e)}")
        return error_response(message=f"获取执行记录详情失败: {str(e)}")


@router.get("/ai-execution-records/{execution_id}/status")
async def get_execution_status(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取AI执行状态（用于轮询）
    
    Args:
        execution_id: 执行记录ID
    
    Returns:
        执行状态信息
    """
    try:
        from .crud import AIExecutionRecordCRUD
        record_crud = AIExecutionRecordCRUD(db)
        execution = await record_crud.get_by_id_crud(execution_id)
        
        if not execution:
            return error_response(message="执行记录不存在")
        
        # 计算进度
        steps_count = len(execution.steps_completed or [])
        
        return success_response(data={
            'id': execution.id,
            'status': execution.status,
            'progress': steps_count,
            'logs': execution.logs or "",
            'duration': execution.duration,
            'error_message': execution.error_message,
            'gif_path': execution.gif_path
        })
    except Exception as e:
        logger.error(f"获取执行状态失败: {str(e)}")
        return error_response(message=f"获取状态失败: {str(e)}")


@router.delete("/ai-execution-records/{execution_id}")
async def delete_execution_record(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除AI执行记录（硬删除）
    
    Args:
        execution_id: 执行记录ID
    
    Returns:
        删除结果
    """
    try:
        from .crud import AIExecutionRecordCRUD
        from .model import AIExecutionRecordModel
        from sqlalchemy import select, delete
        import os
        
        record_crud = AIExecutionRecordCRUD(db)
        
        # 先查询记录是否存在
        execution = await record_crud.get_by_id_crud(execution_id)
        if not execution:
            return error_response(message="执行记录不存在", code=404)
        
        # 删除关联的GIF文件
        if execution.gif_path:
            gif_full_path = os.path.join('static', execution.gif_path)
            if os.path.exists(gif_full_path):
                try:
                    os.remove(gif_full_path)
                    logger.info(f"已删除GIF文件: {gif_full_path}")
                except Exception as e:
                    logger.warning(f"删除GIF文件失败: {str(e)}")
        
        # 硬删除记录
        stmt = delete(AIExecutionRecordModel).where(AIExecutionRecordModel.id == execution_id)
        await db.execute(stmt)
        await db.commit()
        
        logger.info(f"✅ 硬删除执行记录成功: execution_id={execution_id}")
        
        return success_response(message="删除成功")
    except Exception as e:
        logger.error(f"删除执行记录失败: {str(e)}", exc_info=True)
        await db.rollback()
        return error_response(message=f"删除失败: {str(e)}")


# ==================== 项目关联查询 ====================

@router.get("/projects/{project_id}/sub-projects")
async def get_sub_projects(
    project_id: int,
    project_type: Optional[str] = Query(None, description="子项目类型: ui/api/performance"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取主项目下的子项目列表"""
    try:
        from sqlalchemy import select, text
        
        result_data = {
            'ui_projects': [],
            'api_projects': [],
            'performance_projects': []
        }
        
        # 查询UI项目
        if not project_type or project_type == 'ui':
            ui_query = text("""
                SELECT id, name, description, base_url
                FROM ui_projects
                WHERE project_id = :project_id AND enabled_flag = 1
                ORDER BY creation_date DESC
            """)
            ui_result = await db.execute(ui_query, {'project_id': project_id})
            ui_projects = ui_result.fetchall()
            result_data['ui_projects'] = [
                {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'base_url': row[3],
                    'type': 'ui'
                }
                for row in ui_projects
            ]
        
        # 查询API项目
        if not project_type or project_type == 'api':
            api_query = text("""
                SELECT id, name, description, base_url
                FROM api_projects
                WHERE project_id = :project_id AND enabled_flag = 1
                ORDER BY creation_date DESC
            """)
            api_result = await db.execute(api_query, {'project_id': project_id})
            api_projects = api_result.fetchall()
            result_data['api_projects'] = [
                {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'base_url': row[3],
                    'type': 'api'
                }
                for row in api_projects
            ]
        
        # 查询性能测试项目（预留）
        if not project_type or project_type == 'performance':
            # TODO: 实现性能测试项目查询
            pass
        
        return success_response(data=result_data)
    except Exception as e:
        logger.error(f"获取子项目失败: {str(e)}")
        return error_response(message=f"获取子项目失败: {str(e)}")


# ==================== 测试用例模板管理 ====================

@router.get("/testcase-templates")
async def get_testcase_templates(
    template_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取测试用例模板列表"""
    try:
        templates = await TestCaseTemplateService.get_list(db, template_type)
        return success_response(data=templates)
    except Exception as e:
        logger.error(f"获取模板列表失败: {str(e)}")
        return error_response(message=f"获取模板列表失败: {str(e)}")


@router.get("/testcase-templates/{template_id}")
async def get_testcase_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取测试用例模板详情"""
    try:
        template = await TestCaseTemplateService.get_by_id(db, template_id)
        if not template:
            return error_response(message="模板不存在", code=404)
        return success_response(data=template)
    except Exception as e:
        logger.error(f"获取模板详情失败: {str(e)}")
        return error_response(message=f"获取模板详情失败: {str(e)}")


@router.post("/testcase-templates")
async def create_testcase_template(
    template_data: TestCaseTemplateCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建测试用例模板"""
    try:
        template = await TestCaseTemplateService.create(db, template_data, current_user_id)
        await db.commit()
        return success_response(data=template, message="模板创建成功")
    except Exception as e:
        logger.error(f"创建模板失败: {str(e)}")
        return error_response(message=f"创建模板失败: {str(e)}")


@router.put("/testcase-templates/{template_id}")
async def update_testcase_template(
    template_id: int,
    template_data: TestCaseTemplateUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新测试用例模板"""
    try:
        template = await TestCaseTemplateService.update(db, template_id, template_data, current_user_id)
        if not template:
            return error_response(message="模板不存在", code=404)
        await db.commit()
        return success_response(data=template, message="模板更新成功")
    except Exception as e:
        logger.error(f"更新模板失败: {str(e)}")
        return error_response(message=f"更新模板失败: {str(e)}")


@router.delete("/testcase-templates/{template_id}")
async def delete_testcase_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除测试用例模板"""
    try:
        success = await TestCaseTemplateService.delete(db, template_id)
        if not success:
            return error_response(message="模板不存在", code=404)
        await db.commit()
        return success_response(message="模板删除成功")
    except Exception as e:
        logger.error(f"删除模板失败: {str(e)}")
        return error_response(message=f"删除模板失败: {str(e)}")


@router.get("/testcase-templates/{template_id}/export")
async def export_testcase_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """导出测试用例模板"""
    try:
        from fastapi.responses import JSONResponse
        
        template = await TestCaseTemplateService.get_by_id(db, template_id)
        if not template:
            return error_response(message="模板不存在", code=404)
        
        # 构建导出数据
        export_data = {
            'name': template.name,
            'description': template.description,
            'template_type': template.template_type,
            'field_mapping': template.field_mapping,
            'version': '1.0',
            'exported_at': datetime.now().isoformat()
        }
        
        return JSONResponse(
            content=export_data,
            headers={
                'Content-Disposition': f'attachment; filename=template_{template_id}_{template.name}.json'
            }
        )
    except Exception as e:
        logger.error(f"导出模板失败: {str(e)}")
        return error_response(message=f"导出模板失败: {str(e)}")


@router.post("/testcase-templates/import")
async def import_testcase_template(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """导入测试用例模板"""
    try:
        import json
        
        # 读取文件内容
        content = await file.read()
        template_data = json.loads(content.decode('utf-8'))
        
        # 验证必需字段
        required_fields = ['name', 'template_type', 'field_mapping']
        for field in required_fields:
            if field not in template_data:
                return error_response(message=f"缺少必需字段: {field}", code=400)
        
        # 创建模板
        create_schema = TestCaseTemplateCreateSchema(
            name=template_data['name'],
            description=template_data.get('description', ''),
            template_type=template_data['template_type'],
            field_mapping=template_data['field_mapping'],
            is_default=False,
            is_active=True
        )
        
        template = await TestCaseTemplateService.create(db, create_schema, current_user_id)
        await db.commit()
        
        return success_response(data=template, message="模板导入成功")
    except json.JSONDecodeError:
        return error_response(message="无效的JSON文件", code=400)
    except Exception as e:
        logger.error(f"导入模板失败: {str(e)}")
        return error_response(message=f"导入模板失败: {str(e)}")


@router.post("/testcase-templates/{template_id}/preview")
async def preview_testcase_template(
    template_id: int,
    sample_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """预览模板映射效果"""
    try:
        template = await TestCaseTemplateService.get_by_id(db, template_id)
        if not template:
            return error_response(message="模板不存在", code=404)
        
        # 使用模板映射示例数据
        mapped_data = TestCaseParserService.map_fields(sample_data, template.field_mapping)
        
        return success_response(data={
            'template': {
                'id': template.id,
                'name': template.name,
                'template_type': template.template_type
            },
            'sample_input': sample_data,
            'mapped_output': mapped_data
        })
    except Exception as e:
        logger.error(f"预览模板失败: {str(e)}")
        return error_response(message=f"预览模板失败: {str(e)}")


# ==================== 保存到测试用例管理 ====================

@router.post("/generation-tasks/{task_id}/save-to-testcases")
async def save_to_testcases(
    task_id: str,
    save_data: SaveToTestCaseSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """将生成的测试用例保存到测试用例管理模块"""
    try:
        # 验证task_id一致性
        if save_data.task_id != task_id:
            return error_response(message="任务ID不匹配", code=400)
        
        # 根据保存类型调用不同的服务
        if save_data.save_type == 'main':
            # 保存到主项目测试用例
            saved_count = await TestCaseParserService.save_to_main_project_testcases(
                db,
                task_id,
                save_data.project_id,
                save_data.template_id,
                current_user_id,
                save_data.module_id
            )
        elif save_data.save_type == 'sub':
            # 保存到子项目测试用例
            if not save_data.sub_project_type:
                return error_response(message="子项目类型不能为空", code=400)
            if not save_data.sub_project_id:
                return error_response(message="子项目ID不能为空", code=400)
            
            # 根据子项目类型选择保存方法
            if save_data.sub_project_type == 'ui':
                saved_count = await TestCaseParserService.save_to_testcases(
                    db,
                    task_id,
                    save_data.sub_project_id,
                    save_data.template_id,
                    current_user_id
                )
            elif save_data.sub_project_type == 'api':
                # 保存到API项目
                saved_count = await TestCaseParserService.save_to_api_testcases(
                    db,
                    task_id,
                    save_data.sub_project_id,
                    save_data.template_id,
                    current_user_id
                )
            elif save_data.sub_project_type == 'performance':
                # TODO: 实现性能测试项目保存
                return error_response(message="性能测试项目保存功能开发中", code=501)
            else:
                return error_response(message="无效的子项目类型", code=400)
        else:
            return error_response(message="无效的保存类型", code=400)
        
        return success_response(
            data={'saved_count': saved_count},
            message=f"成功保存 {saved_count} 条测试用例"
        )
    except Exception as e:
        logger.error(f"保存测试用例失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return error_response(message=f"保存测试用例失败: {str(e)}")


@router.delete("/generation-tasks/{task_id}")
async def delete_generation_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除测试用例生成任务（硬删除）"""
    try:
        from .model import TestCaseGenerationTaskModel
        from sqlalchemy import delete
        
        # 检查任务是否存在
        task = await TestCaseGenerationTaskService.get_task_by_id(db, task_id)
        if not task:
            return error_response(message="任务不存在", code=404)
        
        # 硬删除任务
        stmt = delete(TestCaseGenerationTaskModel).where(
            TestCaseGenerationTaskModel.task_id == task_id
        )
        await db.execute(stmt)
        await db.commit()
        
        logger.info(f"删除生成任务成功: {task_id}")
        return success_response(message="删除成功")
    except Exception as e:
        logger.error(f"删除生成任务失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return error_response(message=f"删除失败: {str(e)}")


@router.post("/generation-tasks/batch-delete")
async def batch_delete_generation_tasks(
    task_ids: List[str],
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """批量删除测试用例生成任务（硬删除）"""
    try:
        from .model import TestCaseGenerationTaskModel
        from sqlalchemy import delete
        
        if not task_ids:
            return error_response(message="请选择要删除的任务", code=400)
        
        # 硬删除任务
        stmt = delete(TestCaseGenerationTaskModel).where(
            TestCaseGenerationTaskModel.task_id.in_(task_ids)
        )
        result = await db.execute(stmt)
        await db.commit()
        
        deleted_count = result.rowcount
        logger.info(f"批量删除生成任务成功: {deleted_count} 条")
        return success_response(
            data={'deleted_count': deleted_count},
            message=f"成功删除 {deleted_count} 条任务"
        )
    except Exception as e:
        logger.error(f"批量删除生成任务失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return error_response(message=f"批量删除失败: {str(e)}")


# ==================== 后台任务 ====================

async def start_generation_task(task_id: str):
    """启动生成任务的后台处理"""
    from app.db.sqlalchemy import engine
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    import traceback
    
    # 创建新的数据库会话
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as db:
        try:
            # 获取任务详情
            task = await TestCaseGenerationTaskService.get_task_by_id(db, task_id)
            if not task:
                logger.error(f"任务不存在: {task_id}")
                return
            
            # 更新任务状态为运行中
            from .schema import TestCaseGenerationTaskUpdateSchema
            await TestCaseGenerationTaskService.update_task(
                db,
                task_id,
                TestCaseGenerationTaskUpdateSchema(status='running', progress=0)
            )
            await db.commit()
            
            logger.info(f"开始生成任务: {task_id}, 输出模式: {task.output_mode}")
            
            # 记录Writer模型配置信息
            if task.writer_model_config:
                logger.info(f"Writer模型配置: ID={task.writer_model_config.id}, "
                          f"名称={task.writer_model_config.name}, "
                          f"模型={task.writer_model_config.model_name}, "
                          f"Base URL={task.writer_model_config.base_url}, "
                          f"API Key前缀={task.writer_model_config.api_key[:10] if task.writer_model_config.api_key else 'None'}")
            else:
                logger.error(f"Writer模型配置未加载: writer_model_config_id={task.writer_model_config_id}")
            
            # 定义流式回调函数
            async def stream_callback(chunk: str):
                """流式输出回调"""
                await TestCaseGenerationTaskService.update_stream_buffer(db, task_id, chunk)
                await db.commit()
            
            # 根据输出模式选择生成方式
            if task.output_mode == 'stream':
                # 流式生成
                generated_content = await AIModelService.generate_test_cases_stream(
                    db, task, callback=stream_callback
                )
            else:
                # 批量生成
                generated_content = await AIModelService.generate_test_cases(db, task)
            
            logger.info(f"Writer生成完成，内容长度: {len(generated_content)}")
            logger.info(f"Writer生成内容前100字符: {generated_content[:100]}")
            
            # 更新进度到50%，保存Writer生成的内容
            update_result = await TestCaseGenerationTaskService.update_task(
                db,
                task_id,
                TestCaseGenerationTaskUpdateSchema(
                    progress=50,
                    generated_test_cases=generated_content
                )
            )
            await db.commit()
            
            if update_result:
                logger.info(f"Writer内容已保存到数据库")
            else:
                logger.error(f"Writer内容保存失败")
            
            # 如果配置了Reviewer，进行评审
            if task.reviewer_model_config_id and task.reviewer_prompt_config_id:
                logger.info(f"开始Reviewer评审")
                
                try:
                    # 重新获取任务以获取最新的关联数据
                    task = await TestCaseGenerationTaskService.get_task_by_id(db, task_id)
                    
                    # 验证Writer内容是否正确保存
                    if not task.generated_test_cases:
                        logger.error(f"重新获取任务后，generated_test_cases为空！")
                        logger.error(f"使用内存中的generated_content: {len(generated_content)}")
                    else:
                        logger.info(f"重新获取任务后，generated_test_cases长度: {len(task.generated_test_cases)}")
                    
                    # 确保关联对象已加载
                    if not task.reviewer_model_config:
                        logger.error(f"Reviewer模型配置未加载: reviewer_model_config_id={task.reviewer_model_config_id}")
                        raise Exception("Reviewer模型配置未加载")
                    
                    if not task.reviewer_prompt_config:
                        logger.error(f"Reviewer提示词配置未加载: reviewer_prompt_config_id={task.reviewer_prompt_config_id}")
                        raise Exception("Reviewer提示词配置未加载")
                    
                    # 直接从数据库重新查询Reviewer模型配置，确保API Key正确
                    from sqlalchemy import select
                    from .model import AIModelConfigModel
                    reviewer_config_stmt = select(AIModelConfigModel).where(
                        AIModelConfigModel.id == task.reviewer_model_config_id
                    )
                    reviewer_config_result = await db.execute(reviewer_config_stmt)
                    reviewer_model_config = reviewer_config_result.scalar_one_or_none()
                    
                    if not reviewer_model_config:
                        raise Exception(f"Reviewer模型配置不存在: ID={task.reviewer_model_config_id}")
                    
                    # 记录Reviewer配置信息
                    logger.info(f"Reviewer模型配置: ID={reviewer_model_config.id}, "
                              f"名称={reviewer_model_config.name}, "
                              f"模型={reviewer_model_config.model_name}, "
                              f"Base URL={reviewer_model_config.base_url}, "
                              f"API Key前缀={reviewer_model_config.api_key[:10] if reviewer_model_config.api_key else 'None'}")
                    
                    reviewer_prompt = task.reviewer_prompt_config.content
                    messages = [
                        {"role": "system", "content": reviewer_prompt},
                        {"role": "user", "content": f"请评审以下测试用例：\n\n{generated_content}"}
                    ]
                    
                    # 使用重新查询的配置对象
                    review_response = await AIModelService.call_openai_compatible_api(
                        reviewer_model_config,
                        messages
                    )
                    
                    # 检查响应格式
                    if 'choices' not in review_response:
                        logger.error(f"Reviewer API返回格式错误: {review_response}")
                        raise Exception(f"Reviewer API返回格式错误，缺少choices字段。响应: {review_response}")
                    
                    review_feedback = review_response['choices'][0]['message']['content']
                    logger.info(f"Reviewer评审完成，反馈长度: {len(review_feedback)}")
                    
                    # 更新评审结果
                    await TestCaseGenerationTaskService.update_task(
                        db,
                        task_id,
                        TestCaseGenerationTaskUpdateSchema(
                            progress=75,
                            review_feedback=review_feedback
                        )
                    )
                    await db.commit()
                    
                    # 根据评审反馈优化测试用例
                    logger.info(f"根据评审反馈优化测试用例")
                    
                    # 重新查询Writer模型配置
                    writer_config_stmt = select(AIModelConfigModel).where(
                        AIModelConfigModel.id == task.writer_model_config_id
                    )
                    writer_config_result = await db.execute(writer_config_stmt)
                    writer_model_config = writer_config_result.scalar_one_or_none()
                    
                    if not writer_model_config:
                        raise Exception(f"Writer模型配置不存在: ID={task.writer_model_config_id}")
                    
                    optimize_messages = [
                        {"role": "system", "content": task.writer_prompt_config.content},
                        {"role": "user", "content": f"原始测试用例：\n{generated_content}\n\n评审反馈：\n{review_feedback}\n\n请根据评审反馈优化测试用例。"}
                    ]
                    
                    optimize_response = await AIModelService.call_openai_compatible_api(
                        writer_model_config,
                        optimize_messages
                    )
                    
                    # 检查响应格式
                    if 'choices' not in optimize_response:
                        logger.error(f"优化API返回格式错误: {optimize_response}")
                        raise Exception(f"优化API返回格式错误，缺少choices字段。响应: {optimize_response}")
                    
                    final_content = optimize_response['choices'][0]['message']['content']
                    logger.info(f"优化完成，最终内容长度: {len(final_content)}")
                    
                except Exception as reviewer_error:
                    logger.error(f"Reviewer评审失败: {reviewer_error}")
                    # Reviewer失败不影响整体流程，直接使用Writer生成的内容
                    final_content = generated_content
                    review_feedback_error = f"Reviewer评审失败: {str(reviewer_error)}"
                    
                    # 更新任务，记录Reviewer错误
                    await TestCaseGenerationTaskService.update_task(
                        db,
                        task_id,
                        TestCaseGenerationTaskUpdateSchema(
                            progress=75,
                            review_feedback=review_feedback_error
                        )
                    )
                    await db.commit()
            else:
                # 没有配置Reviewer，直接使用生成的内容
                final_content = generated_content
            
            # 更新任务为完成状态，显式保留generated_test_cases
            await TestCaseGenerationTaskService.update_task(
                db,
                task_id,
                TestCaseGenerationTaskUpdateSchema(
                    status='completed',
                    progress=100,
                    generated_test_cases=generated_content,  # 显式保留Writer生成的内容
                    final_test_cases=final_content,
                    generation_log=f"生成成功\n生成内容长度: {len(generated_content)}\n最终内容长度: {len(final_content)}"
                )
            )
            await db.commit()
            
            logger.info(f"任务完成: {task_id}")
            
        except Exception as e:
            logger.error(f"生成任务失败: {task_id}, 错误: {str(e)}")
            logger.error(traceback.format_exc())
            
            # 更新任务为失败状态
            try:
                await TestCaseGenerationTaskService.update_task(
                    db,
                    task_id,
                    TestCaseGenerationTaskUpdateSchema(
                        status='failed',
                        error_message=str(e),
                        generation_log=f"生成失败\n错误: {str(e)}\n{traceback.format_exc()}"
                    )
                )
                await db.commit()
            except Exception as update_error:
                logger.error(f"更新失败状态时出错: {update_error}")



# ==================== Figma配置管理 ====================

@router.get("/figma-configs")
async def get_figma_configs(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取Figma配置列表"""
    try:
        from .crud import FigmaConfigCRUD
        
        config_crud = FigmaConfigCRUD(db)
        
        if project_id:
            configs = await config_crud.get_by_project(project_id)
        else:
            from .model import FigmaConfigModel
            conditions = [FigmaConfigModel.enabled_flag == 1]
            items, _ = await config_crud.get_list_crud(
                conditions=conditions,
                order_by=[FigmaConfigModel.creation_date.desc()]
            )
            configs = items
        
        # 脱敏access_token
        result = []
        for config in configs:
            config_dict = {
                'id': config.id,
                'project_id': config.project_id,
                'file_key': config.file_key,
                'file_name': config.file_name,
                'file_url': config.file_url,
                'last_sync_time': config.last_sync_time.isoformat() if config.last_sync_time else None,
                'creation_date': config.creation_date.isoformat() if config.creation_date else None,
                'access_token_masked': config.access_token[:10] + "****" if config.access_token else None
            }
            result.append(config_dict)
        
        return success_response(data=result)
    except Exception as e:
        logger.error(f"获取Figma配置失败: {str(e)}")
        return error_response(message=f"获取失败: {str(e)}")


@router.post("/figma-configs")
async def create_figma_config(
    config_data: FigmaConfigCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建Figma配置"""
    try:
        from .crud import FigmaConfigCRUD
        from .model import FigmaConfigModel
        
        config_crud = FigmaConfigCRUD(db)
        
        # 检查是否已存在相同file_key的配置
        existing = await config_crud.get_by_file_key(config_data.file_key)
        if existing:
            return error_response(message="该Figma文件已配置，请勿重复添加")
        
        config_dict = config_data.dict()
        config_dict['created_by'] = current_user_id
        
        config = await config_crud.create_crud(data=config_dict)
        
        return success_response(data={
            'id': config.id,
            'project_id': config.project_id,
            'file_key': config.file_key,
            'file_name': config.file_name,
            'file_url': config.file_url
        })
    except Exception as e:
        logger.error(f"创建Figma配置失败: {str(e)}")
        return error_response(message=f"创建失败: {str(e)}")


@router.get("/figma-configs/{config_id}")
async def get_figma_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取Figma配置详情"""
    try:
        from .crud import FigmaConfigCRUD
        
        config_crud = FigmaConfigCRUD(db)
        config = await config_crud.get_by_id_crud(config_id)
        
        if not config:
            return error_response(message="配置不存在", code=404)
        
        return success_response(data={
            'id': config.id,
            'project_id': config.project_id,
            'file_key': config.file_key,
            'file_name': config.file_name,
            'file_url': config.file_url,
            'last_sync_time': config.last_sync_time.isoformat() if config.last_sync_time else None,
            'access_token_masked': config.access_token[:10] + "****" if config.access_token else None
        })
    except Exception as e:
        logger.error(f"获取Figma配置失败: {str(e)}")
        return error_response(message=f"获取失败: {str(e)}")


@router.put("/figma-configs/{config_id}")
async def update_figma_config(
    config_id: int,
    config_data: FigmaConfigUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新Figma配置"""
    try:
        from .crud import FigmaConfigCRUD
        
        config_crud = FigmaConfigCRUD(db)
        config = await config_crud.update_crud(config_id, config_data.dict(exclude_unset=True))
        
        if not config:
            return error_response(message="配置不存在", code=404)
        
        return success_response(data={
            'id': config.id,
            'project_id': config.project_id,
            'file_key': config.file_key,
            'file_name': config.file_name
        })
    except Exception as e:
        logger.error(f"更新Figma配置失败: {str(e)}")
        return error_response(message=f"更新失败: {str(e)}")


@router.delete("/figma-configs/{config_id}")
async def delete_figma_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除Figma配置"""
    try:
        from .crud import FigmaConfigCRUD
        
        config_crud = FigmaConfigCRUD(db)
        config = await config_crud.get_by_id_crud(config_id)
        
        if not config:
            return error_response(message="配置不存在", code=404)
        
        await config_crud.soft_delete_crud([config_id])
        
        return success_response(message="删除成功")
    except Exception as e:
        logger.error(f"删除Figma配置失败: {str(e)}")
        return error_response(message=f"删除失败: {str(e)}")


@router.post("/figma-configs/{config_id}/extract")
async def extract_figma_requirements(
    config_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """从Figma提取需求"""
    try:
        from .crud import FigmaConfigCRUD, AIModelConfigCRUD
        from .model import FigmaConfigModel
        from app.services.ai.figma_requirement_service import FigmaRequirementService
        from app.db.sqlalchemy import async_session_factory
        from datetime import datetime
        
        # 获取Figma配置
        config_crud = FigmaConfigCRUD(db)
        config = await config_crud.get_by_id_crud(config_id)
        
        if not config:
            return error_response(message="Figma配置不存在", code=404)
        
        # 获取Vision模型配置（使用writer角色的配置）
        model_config_crud = AIModelConfigCRUD(db)
        vision_model = await model_config_crud.get_active_by_role('writer')
        
        if not vision_model:
            return error_response(message="未找到AI模型配置，请先在AI模型配置中添加writer角色的配置")
        
        # 后台执行提取
        async def run_extraction():
            """后台执行Figma需求提取"""
            async with async_session_factory() as db_session:
                try:
                    logger.info(f"开始提取Figma需求: config_id={config_id}, file_key={config.file_key}")
                    
                    # 创建提取服务
                    service = FigmaRequirementService(
                        figma_token=config.access_token,
                        ai_model_config={
                            'api_key': vision_model.api_key,
                            'base_url': vision_model.base_url,
                            'model_name': vision_model.model_name,
                            'temperature': vision_model.temperature or 0.3,
                            'max_tokens': vision_model.max_tokens or 4096
                        }
                    )
                    
                    # 获取项目名称
                    project_name = ""
                    if config.project_id:
                        from sqlalchemy import text
                        stmt = text("SELECT name FROM projects WHERE id = :project_id")
                        result = await db_session.execute(stmt, {"project_id": config.project_id})
                        row = result.fetchone()
                        if row:
                            project_name = row[0]
                    
                    # 执行提取
                    result = await service.extract_requirements_from_figma(
                        file_key=config.file_key,
                        project_name=project_name
                    )
                    
                    logger.info(f"Figma需求提取完成: {result['summary']}")
                    
                    # 保存为需求文档
                    from .model import RequirementDocumentModel, RequirementAnalysisModel, BusinessRequirementModel
                    
                    document = RequirementDocumentModel(
                        project_id=config.project_id,
                        title=f"Figma需求-{config.file_name or config.file_key}",
                        file_path=config.file_url or f"figma://{config.file_key}",
                        document_type="figma",
                        status="analyzed",
                        uploaded_by=current_user_id,
                        created_by=current_user_id
                    )
                    db_session.add(document)
                    await db_session.flush()
                    
                    # 保存分析结果
                    analysis = RequirementAnalysisModel(
                        document_id=document.id,
                        analysis_report=result['summary'],
                        requirements_count=len(result['requirements']),
                        analysis_time=0,
                        created_by=current_user_id
                    )
                    db_session.add(analysis)
                    await db_session.flush()
                    
                    # 保存需求
                    for req_data in result['requirements']:
                        requirement = BusinessRequirementModel(
                            analysis_id=analysis.id,
                            requirement_id=req_data.get('requirement_id', ''),
                            requirement_name=req_data.get('requirement_name', ''),
                            requirement_type=req_data.get('requirement_type', '功能需求'),
                            module=req_data.get('module', ''),
                            requirement_level=req_data.get('requirement_level', '中'),
                            description=req_data.get('description', ''),
                            acceptance_criteria=req_data.get('acceptance_criteria', ''),
                            parent_requirement_id=req_data.get('parent_requirement_id'),
                            created_by=current_user_id
                        )
                        db_session.add(requirement)
                    
                    # 更新Figma配置的同步时间
                    config.last_sync_time = datetime.now()
                    
                    await db_session.commit()
                    
                    logger.info(f"Figma需求保存成功: document_id={document.id}, analysis_id={analysis.id}")
                    
                except Exception as e:
                    logger.error(f"Figma需求提取失败: {str(e)}", exc_info=True)
                    await db_session.rollback()
        
        # 添加后台任务
        background_tasks.add_task(run_extraction)
        
        return success_response(message="Figma需求提取已启动，请稍后在需求文档管理中查看结果")
        
    except Exception as e:
        logger.error(f"启动Figma需求提取失败: {str(e)}")
        return error_response(message=f"启动失败: {str(e)}")


@router.post("/figma-configs/{config_id}/extract-with-mode")
async def extract_figma_with_mode(
    config_id: int,
    extraction_mode: str = Query("simple", description="提取模式: simple/complete"),
    force_refresh: bool = Query(False, description="是否强制刷新，忽略缓存"),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    带模式选择的Figma需求提取（智能缓存）
    
    Args:
        config_id: Figma配置ID
        extraction_mode: 提取模式
            - simple: 快速提取（5-10秒，不使用AI Vision）
            - complete: 完整分析（5-10分钟，使用AI Vision）
        force_refresh: 是否强制刷新，忽略缓存
    
    Returns:
        task_id: 任务ID，用于查询进度
    """
    try:
        from app.db.sqlalchemy import async_session_factory
        from .crud import FigmaConfigCRUD, AIModelConfigCRUD
        from app.services.ai.figma_extraction_service import FigmaExtractionService
        from app.services.ai.figma_cache_service import FigmaCacheService
        from app.services.ai.figma_update_checker import FigmaUpdateChecker
        
        # 验证提取模式
        if extraction_mode not in ['simple', 'complete']:
            return error_response(message="无效的提取模式，请选择 simple 或 complete")
        
        # 获取Figma配置
        config_crud = FigmaConfigCRUD(db)
        config = await config_crud.get_by_id_crud(config_id)
        
        if not config:
            return error_response(message="Figma配置不存在", code=404)
        
        # 智能缓存检查（如果不是强制刷新）
        if not force_refresh:
            logger.info(f"检查缓存和更新状态: config_id={config_id}")
            
            # 1. 检查缓存
            cache_info = await FigmaCacheService.get_cache_info(db, config.file_key)
            
            if cache_info and not cache_info['is_expired']:
                logger.info(f"发现有效缓存: {config.file_key}")
                
                # 2. 检查更新
                try:
                    update_info = await FigmaUpdateChecker.check_for_updates(
                        db, config_id, config.file_key, config.access_token
                    )
                    
                    if not update_info['has_updates']:
                        logger.info(f"设计稿无更新，使用缓存数据（0次API调用）")
                        
                        # 查找最近的成功提取任务
                        from sqlalchemy import select
                        from .model import FigmaExtractionTaskModel
                        
                        stmt = select(FigmaExtractionTaskModel).where(
                            FigmaExtractionTaskModel.config_id == config_id,
                            FigmaExtractionTaskModel.status == 'completed',
                            FigmaExtractionTaskModel.enabled_flag == 1
                        ).order_by(FigmaExtractionTaskModel.creation_date.desc()).limit(1)
                        
                        result = await db.execute(stmt)
                        last_task = result.scalar_one_or_none()
                        
                        if last_task and last_task.result_document_id:
                            return success_response(
                                data={
                                    'task_id': last_task.task_id,
                                    'from_cache': True,
                                    'cache_time': cache_info['cache_time'],
                                    'document_id': last_task.result_document_id
                                },
                                message="设计稿无更新，已使用缓存数据（0次API调用，1秒完成）"
                            )
                    else:
                        logger.info(f"检测到更新: {update_info['changes_summary']}")
                
                except Exception as e:
                    logger.warning(f"检查更新失败，继续提取: {str(e)}")
        
        # 如果是完整模式，检查AI模型配置
        if extraction_mode == 'complete':
            model_config_crud = AIModelConfigCRUD(db)
            vision_model = await model_config_crud.get_active_by_role('writer')
            
            if not vision_model:
                return error_response(
                    message="完整模式需要AI模型配置，请先在AI模型配置中添加writer角色的配置"
                )
        
        # 创建提取任务
        task_id = await FigmaExtractionService.create_extraction_task(
            db, config_id, extraction_mode, current_user_id
        )
        
        # 后台执行提取
        async def run_extraction():
            """后台执行提取"""
            async with async_session_factory() as db_session:
                try:
                    logger.info(f"开始Figma提取: task_id={task_id}, mode={extraction_mode}")
                    
                    # 获取配置
                    config_crud = FigmaConfigCRUD(db_session)
                    config = await config_crud.get_by_id_crud(config_id)
                    
                    # 获取项目名称
                    project_name = ""
                    if config.project_id:
                        from sqlalchemy import text
                        stmt = text("SELECT name FROM projects WHERE id = :project_id")
                        result = await db_session.execute(stmt, {"project_id": config.project_id})
                        row = result.fetchone()
                        if row:
                            project_name = row[0]
                    
                    # 根据模式执行提取
                    if extraction_mode == 'simple':
                        document_id = await FigmaExtractionService.extract_simple(
                            db_session, task_id, config, project_name, current_user_id
                        )
                    else:  # complete
                        # 获取AI模型配置
                        model_config_crud = AIModelConfigCRUD(db_session)
                        vision_model = await model_config_crud.get_active_by_role('writer')
                        
                        ai_config = {
                            'api_key': vision_model.api_key,
                            'base_url': vision_model.base_url,
                            'model_name': vision_model.model_name,
                            'temperature': vision_model.temperature or 0.3,
                            'max_tokens': vision_model.max_tokens or 4096
                        }
                        
                        document_id = await FigmaExtractionService.extract_complete(
                            db_session, task_id, config, ai_config, project_name, current_user_id
                        )
                    
                    # 完成任务
                    await FigmaExtractionService.complete_task(db_session, task_id, document_id)
                    
                    logger.info(f"Figma提取完成: task_id={task_id}, document_id={document_id}")
                    
                except Exception as e:
                    logger.error(f"Figma提取失败: task_id={task_id}, error={str(e)}", exc_info=True)
                    await FigmaExtractionService.fail_task(db_session, task_id, str(e))
        
        # 添加后台任务
        background_tasks.add_task(run_extraction)
        
        return success_response(
            data={'task_id': task_id},
            message=f"Figma需求提取已启动（{extraction_mode}模式），请通过task_id查询进度"
        )
        
    except Exception as e:
        logger.error(f"启动Figma提取失败: {str(e)}")
        return error_response(message=f"启动失败: {str(e)}")


@router.get("/figma-extraction-tasks/{task_id}")
async def get_extraction_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    查询提取任务状态和进度
    
    Args:
        task_id: 任务ID
    
    Returns:
        任务详情，包括状态、进度、当前步骤等
    """
    try:
        from .crud import FigmaExtractionTaskCRUD
        
        task_crud = FigmaExtractionTaskCRUD(db)
        task = await task_crud.get_by_task_id(task_id)
        
        if not task:
            return error_response(message="任务不存在", code=404)
        
        # 转换为字典
        task_dict = {
            'id': task.id,
            'task_id': task.task_id,
            'config_id': task.config_id,
            'extraction_mode': task.extraction_mode,
            'status': task.status,
            'progress': task.progress,
            'current_step': task.current_step,
            'total_frames': task.total_frames,
            'processed_frames': task.processed_frames,
            'error_message': task.error_message,
            'result_document_id': task.result_document_id,
            'start_time': task.start_time.isoformat() if task.start_time else None,
            'end_time': task.end_time.isoformat() if task.end_time else None,
            'creation_date': task.creation_date.isoformat() if task.creation_date else None
        }
        
        return success_response(data=task_dict)
        
    except Exception as e:
        logger.error(f"查询任务状态失败: {str(e)}")
        return error_response(message=f"查询失败: {str(e)}")


@router.get("/figma-configs/{config_id}/latest-task")
async def get_latest_extraction_task(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    获取配置的最新提取任务
    
    Args:
        config_id: Figma配置ID
    
    Returns:
        最新的任务信息，如果没有则返回null
    """
    try:
        from .crud import FigmaExtractionTaskCRUD
        
        task_crud = FigmaExtractionTaskCRUD(db)
        task = await task_crud.get_latest_by_config(config_id)
        
        if not task:
            return success_response(data=None, message="暂无提取任务")
        
        # 转换为字典
        task_dict = {
            'id': task.id,
            'task_id': task.task_id,
            'config_id': task.config_id,
            'extraction_mode': task.extraction_mode,
            'status': task.status,
            'progress': task.progress,
            'current_step': task.current_step,
            'total_frames': task.total_frames,
            'processed_frames': task.processed_frames,
            'error_message': task.error_message,
            'result_document_id': task.result_document_id,
            'start_time': task.start_time.isoformat() if task.start_time else None,
            'end_time': task.end_time.isoformat() if task.end_time else None,
            'creation_date': task.creation_date.isoformat() if task.creation_date else None
        }
        
        return success_response(data=task_dict)
        
    except Exception as e:
        logger.error(f"获取最新任务失败: {str(e)}")
        return error_response(message=f"获取失败: {str(e)}")


@router.get("/figma-configs/{config_id}/preview")
async def preview_figma_file(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    预览Figma文件信息
    
    不执行完整提取，只返回文件的基本信息：
    - 文件名
    - 页面列表
    - Frame列表
    - 预计需求数量
    
    Args:
        config_id: Figma配置ID
    
    Returns:
        文件预览信息
    """
    try:
        from app.services.ai.figma_service import FigmaService
        from .crud import FigmaConfigCRUD
        
        # 获取配置
        config_crud = FigmaConfigCRUD(db)
        config = await config_crud.get_by_id_crud(config_id)
        
        if not config:
            return error_response(message="Figma配置不存在", code=404)
        
        # 创建Figma服务
        figma_service = FigmaService(access_token=config.access_token)
        
        # 获取文件数据
        file_data = await figma_service.get_file(config.file_key)
        file_name = file_data.get('name', 'Unknown')
        
        # 提取页面和Frame
        pages = await figma_service.extract_pages_and_frames(file_data)
        
        # 统计信息
        total_frames = sum(len(page.get('frames', [])) for page in pages)
        
        # 构建预览数据
        preview_data = {
            'file_name': file_name,
            'file_key': config.file_key,
            'total_pages': len(pages),
            'total_frames': total_frames,
            'estimated_requirements': total_frames,  # 简化模式：每个Frame一个需求
            'pages': [
                {
                    'name': page.get('name'),
                    'frame_count': len(page.get('frames', [])),
                    'frames': [
                        {
                            'name': frame.get('name'),
                            'width': frame.get('width'),
                            'height': frame.get('height')
                        }
                        for frame in page.get('frames', [])[:10]  # 最多显示10个
                    ]
                }
                for page in pages
            ]
        }
        
        return success_response(data=preview_data, message="预览成功")
        
    except Exception as e:
        logger.error(f"预览Figma文件失败: {str(e)}")
        return error_response(message=f"预览失败: {str(e)}")


# ==================== Figma高级功能API ====================

@router.get("/figma-configs/{config_id}/rate-limit-status")
async def get_rate_limit_status(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取速率限制状态"""
    try:
        from app.services.ai.figma_rate_limiter import FigmaRateLimiter
        
        status = await FigmaRateLimiter.check_rate_limit(db, config_id)
        return success_response(data=status)
    except Exception as e:
        logger.error(f"获取速率限制状态失败: {str(e)}")
        return error_response(message=f"获取失败: {str(e)}")


@router.get("/figma-configs/{config_id}/cache-info")
async def get_cache_info(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取缓存信息"""
    try:
        from .crud import FigmaConfigCRUD
        from app.services.ai.figma_cache_service import FigmaCacheService
        
        config_crud = FigmaConfigCRUD(db)
        config = await config_crud.get_by_id_crud(config_id)
        
        if not config:
            return error_response(message="配置不存在", code=404)
        
        cache_info = await FigmaCacheService.get_cache_info(db, config.file_key)
        
        if not cache_info:
            return success_response(data=None, message="暂无缓存数据")
        
        return success_response(data=cache_info)
    except Exception as e:
        logger.error(f"获取缓存信息失败: {str(e)}")
        return error_response(message=f"获取失败: {str(e)}")


@router.get("/figma-configs/{config_id}/cached-data")
async def get_cached_data(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取缓存的Figma数据（离线查看）"""
    try:
        from .crud import FigmaConfigCRUD
        from app.services.ai.figma_cache_service import FigmaCacheService
        from app.services.ai.figma_service import FigmaService
        
        config_crud = FigmaConfigCRUD(db)
        config = await config_crud.get_by_id_crud(config_id)
        
        if not config:
            return error_response(message="配置不存在", code=404)
        
        cached_data = await FigmaCacheService.get_cached_file(
            db, config.file_key, force_refresh=False
        )
        
        if not cached_data:
            return error_response(message="暂无缓存数据，请先进行一次提取", code=404)
        
        figma_service = FigmaService()
        pages = await figma_service.extract_pages_and_frames(cached_data)
        cache_info = await FigmaCacheService.get_cache_info(db, config.file_key)
        
        return success_response(data={
            'file_name': cached_data.get('name'),
            'last_modified': cached_data.get('lastModified'),
            'pages': pages,
            'total_pages': len(pages),
            'total_frames': sum(len(p.get('frames', [])) for p in pages),
            'is_cached': True,
            'cache_time': cache_info.get('cache_time') if cache_info else None,
            'cache_age_hours': cache_info.get('cache_age_hours') if cache_info else None
        })
    except Exception as e:
        logger.error(f"获取缓存数据失败: {str(e)}")
        return error_response(message=f"获取失败: {str(e)}")


@router.delete("/figma-configs/{config_id}/cache")
async def clear_cache(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """清除缓存"""
    try:
        from .crud import FigmaConfigCRUD
        from app.services.ai.figma_cache_service import FigmaCacheService
        
        config_crud = FigmaConfigCRUD(db)
        config = await config_crud.get_by_id_crud(config_id)
        
        if not config:
            return error_response(message="配置不存在", code=404)
        
        deleted_count = await FigmaCacheService.clear_cache_by_file_key(db, config.file_key)
        
        if deleted_count > 0:
            return success_response(message=f"已清除 {deleted_count} 条缓存")
        else:
            return success_response(message="无缓存数据需要清除")
    except Exception as e:
        logger.error(f"清除缓存失败: {str(e)}")
        return error_response(message=f"清除失败: {str(e)}")


@router.get("/figma-configs/{config_id}/check-updates")
async def check_figma_updates(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """检查Figma文件是否有更新"""
    try:
        from .crud import FigmaConfigCRUD
        from app.services.ai.figma_update_checker import FigmaUpdateChecker
        
        config_crud = FigmaConfigCRUD(db)
        config = await config_crud.get_by_id_crud(config_id)
        
        if not config:
            return error_response(message="配置不存在", code=404)
        
        update_info = await FigmaUpdateChecker.check_for_updates(
            db, config_id, config.file_key, config.access_token
        )
        
        await FigmaUpdateChecker.mark_as_updated(db, config_id, update_info['has_updates'])
        
        return success_response(data=update_info)
    except Exception as e:
        logger.error(f"检查更新失败: {str(e)}")
        return error_response(message=f"检查失败: {str(e)}")



# ==================== AI测试套件管理 ====================

@router.get("/ai-test-suites")
async def get_ai_test_suites(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取AI测试套件列表"""
    try:
        from .test_suite_service import AITestSuiteService
        
        result = await AITestSuiteService.get_suite_list(
            db, project_id, status, page, page_size
        )
        
        return success_response(data=result)
    except Exception as e:
        logger.error(f"获取测试套件列表失败: {str(e)}", exc_info=True)
        return error_response(message=f"获取测试套件列表失败: {str(e)}")


@router.post("/ai-test-suites")
async def create_ai_test_suite(
    suite_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建AI测试套件"""
    try:
        from .test_suite_service import AITestSuiteService
        from .schema import AITestSuiteCreateSchema
        
        # 验证数据
        create_schema = AITestSuiteCreateSchema(**suite_data)
        
        suite = await AITestSuiteService.create_suite(
            db, create_schema, current_user_id
        )
        
        return success_response(
            data={'id': suite.id, 'name': suite.name},
            message="创建测试套件成功"
        )
    except Exception as e:
        logger.error(f"创建测试套件失败: {str(e)}", exc_info=True)
        return error_response(message=f"创建测试套件失败: {str(e)}")


@router.get("/ai-test-suites/{suite_id}")
async def get_ai_test_suite_detail(
    suite_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取AI测试套件详情"""
    try:
        from .test_suite_service import AITestSuiteService
        
        result = await AITestSuiteService.get_suite_detail(db, suite_id)
        
        return success_response(data=result)
    except ValueError as e:
        return error_response(message=str(e), code=404)
    except Exception as e:
        logger.error(f"获取测试套件详情失败: {str(e)}", exc_info=True)
        return error_response(message=f"获取测试套件详情失败: {str(e)}")


@router.put("/ai-test-suites/{suite_id}")
async def update_ai_test_suite(
    suite_id: int,
    suite_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新AI测试套件"""
    try:
        from .test_suite_service import AITestSuiteService
        from .schema import AITestSuiteUpdateSchema
        
        # 验证数据
        update_schema = AITestSuiteUpdateSchema(**suite_data)
        
        suite = await AITestSuiteService.update_suite(
            db, suite_id, update_schema, current_user_id
        )
        
        return success_response(
            data={'id': suite.id, 'name': suite.name},
            message="更新测试套件成功"
        )
    except ValueError as e:
        return error_response(message=str(e), code=404)
    except Exception as e:
        logger.error(f"更新测试套件失败: {str(e)}", exc_info=True)
        return error_response(message=f"更新测试套件失败: {str(e)}")


@router.delete("/ai-test-suites/{suite_id}")
async def delete_ai_test_suite(
    suite_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除AI测试套件"""
    try:
        from .test_suite_service import AITestSuiteService
        
        await AITestSuiteService.delete_suite(db, suite_id)
        
        return success_response(message="删除测试套件成功")
    except Exception as e:
        logger.error(f"删除测试套件失败: {str(e)}", exc_info=True)
        return error_response(message=f"删除测试套件失败: {str(e)}")


@router.post("/ai-test-suites/{suite_id}/execute")
async def execute_ai_test_suite(
    suite_id: int,
    execution_data: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """执行AI测试套件"""
    try:
        from .test_suite_service import AITestSuiteExecutionService
        from .schema import AITestSuiteExecutionCreateSchema
        from app.db.sqlalchemy import async_session_factory
        
        # 验证数据
        exec_schema = AITestSuiteExecutionCreateSchema(
            suite_id=suite_id,
            **execution_data
        )
        
        # 创建执行记录
        execution = await AITestSuiteExecutionService.execute_suite(
            db, suite_id, exec_schema, current_user_id
        )
        
        # 后台执行任务
        async def run_execution():
            """后台执行测试套件"""
            async with async_session_factory() as db_session:
                try:
                    await AITestSuiteExecutionService.run_suite_execution(
                        db_session, execution.id
                    )
                except Exception as e:
                    logger.error(f"后台执行测试套件失败: {str(e)}", exc_info=True)
        
        # 添加后台任务
        background_tasks.add_task(run_execution)
        
        return success_response(
            data={
                'execution_id': execution.id,
                'execution_name': execution.execution_name,
                'total_modules': execution.total_modules,
                'total_cases': execution.total_cases
            },
            message="测试套件执行已启动"
        )
    except ValueError as e:
        return error_response(message=str(e), code=404)
    except Exception as e:
        logger.error(f"执行测试套件失败: {str(e)}", exc_info=True)
        return error_response(message=f"执行测试套件失败: {str(e)}")


@router.get("/ai-test-suite-executions")
async def get_suite_executions(
    suite_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取套件执行记录列表"""
    try:
        from .test_suite_service import AITestSuiteExecutionService
        
        result = await AITestSuiteExecutionService.get_execution_list(
            db, suite_id, status, page, page_size
        )
        
        return success_response(data=result)
    except Exception as e:
        logger.error(f"获取执行记录列表失败: {str(e)}", exc_info=True)
        return error_response(message=f"获取执行记录列表失败: {str(e)}")


@router.get("/ai-test-suite-executions/{execution_id}")
async def get_suite_execution_detail(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取套件执行记录详情"""
    try:
        from .test_suite_service import AITestSuiteExecutionService
        
        result = await AITestSuiteExecutionService.get_execution_detail(
            db, execution_id
        )
        
        return success_response(data=result)
    except ValueError as e:
        return error_response(message=str(e), code=404)
    except Exception as e:
        logger.error(f"获取执行记录详情失败: {str(e)}", exc_info=True)
        return error_response(message=f"获取执行记录详情失败: {str(e)}")


# ==================== AI测试报告相关接口 ====================

@router.post("/ai-test-reports")
async def create_test_report(
    report_data: AITestReportCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建AI测试报告"""
    try:
        from .model import AITestReportModel
        from datetime import datetime
        import uuid
        
        # 生成报告ID
        report_id = f"RPT_{report_data.project_id or 0}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        # 创建报告记录
        report = AITestReportModel(
            report_id=report_id,
            report_name=report_data.report_name,
            project_id=report_data.project_id,
            project_name=report_data.project_name,
            start_date=datetime.strptime(report_data.start_date, '%Y-%m-%d') if report_data.start_date and report_data.start_date != '-' else None,
            end_date=datetime.strptime(report_data.end_date, '%Y-%m-%d') if report_data.end_date and report_data.end_date != '-' else None,
            date_range=report_data.date_range,
            status='generated',
            total_cases=report_data.total_cases,
            total_executions=report_data.total_executions,
            success_count=report_data.success_count,
            failed_count=report_data.failed_count,
            success_rate=report_data.success_rate,
            total_duration=report_data.total_duration,
            avg_duration=report_data.avg_duration,
            total_tokens=report_data.total_tokens,
            report_data=report_data.report_data,
            created_by=current_user_id,
            enabled_flag=1
        )
        
        db.add(report)
        await db.commit()
        await db.refresh(report)
        
        logger.info(f"创建AI测试报告成功: {report_id}")
        return success_response(data={'report_id': report_id, 'id': report.id})
        
    except Exception as e:
        logger.error(f"创建AI测试报告失败: {str(e)}", exc_info=True)
        await db.rollback()
        return error_response(message=f"创建AI测试报告失败: {str(e)}")


@router.get("/ai-test-reports")
async def get_test_reports(
    project_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取AI测试报告列表"""
    try:
        from .model import AITestReportModel
        from sqlalchemy import and_, select, func
        from datetime import datetime
        
        # 构建查询条件
        conditions = [AITestReportModel.enabled_flag == 1]
        
        if project_id:
            conditions.append(AITestReportModel.project_id == project_id)
        
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                conditions.append(AITestReportModel.start_date >= start_dt)
            except:
                pass
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                conditions.append(AITestReportModel.end_date <= end_dt)
            except:
                pass
        
        # 查询总数
        count_stmt = select(func.count(AITestReportModel.id)).where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # 查询数据
        skip = (page - 1) * page_size
        stmt = (
            select(AITestReportModel)
            .where(and_(*conditions))
            .order_by(AITestReportModel.creation_date.desc())
            .offset(skip)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        reports = result.scalars().all()
        
        # 转换为字典
        report_list = []
        for report in reports:
            report_dict = {
                'id': report.id,
                'report_id': report.report_id,
                'report_name': report.report_name,
                'project_id': report.project_id,
                'project_name': report.project_name,
                'date_range': report.date_range,
                'status': report.status,
                'total_cases': report.total_cases,
                'total_executions': report.total_executions,
                'success_count': report.success_count,
                'failed_count': report.failed_count,
                'success_rate': float(report.success_rate) if report.success_rate else 0,
                'total_duration': float(report.total_duration) if report.total_duration else 0,
                'avg_duration': float(report.avg_duration) if report.avg_duration else 0,
                'total_tokens': report.total_tokens,
                'created_time': report.creation_date.isoformat() if report.creation_date else None,
                'report_data': report.report_data
            }
            report_list.append(report_dict)
        
        return success_response(data={
            'items': report_list,
            'total': total,
            'page': page,
            'page_size': page_size
        })
        
    except Exception as e:
        logger.error(f"获取AI测试报告列表失败: {str(e)}", exc_info=True)
        return error_response(message=f"获取AI测试报告列表失败: {str(e)}")


@router.delete("/ai-test-reports/{report_id}")
async def delete_test_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除AI测试报告（硬删除）"""
    try:
        from .model import AITestReportModel
        from sqlalchemy import select, delete, and_
        
        # 查询报告
        stmt = select(AITestReportModel).where(
            and_(
                AITestReportModel.report_id == report_id,
                AITestReportModel.enabled_flag == 1
            )
        )
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()
        
        if not report:
            return error_response(message="报告不存在")
        
        # 硬删除
        delete_stmt = delete(AITestReportModel).where(AITestReportModel.report_id == report_id)
        await db.execute(delete_stmt)
        await db.commit()
        
        logger.info(f"删除AI测试报告成功: {report_id}")
        return success_response(message="删除成功")
        
    except Exception as e:
        logger.error(f"删除AI测试报告失败: {str(e)}", exc_info=True)
        await db.rollback()
        return error_response(message=f"删除AI测试报告失败: {str(e)}")
