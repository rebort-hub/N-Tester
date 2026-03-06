# -*- coding: utf-8 -*-
"""
Figma Controller扩展 - 新增的API接口
"""

from fastapi import APIRouter, Depends, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.db.sqlalchemy import get_db
from app.core.dependencies import get_current_user_id
from app.common.response import success_response, error_response

from .schema import (
    FigmaExtractionTaskCreateSchema,
    FigmaExtractionTaskOutSchema
)
from .crud import FigmaConfigCRUD, FigmaExtractionTaskCRUD, AIModelConfigCRUD
from app.services.ai.figma_extraction_service import FigmaExtractionService

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 新增的Figma提取API ====================

@router.post("/figma-configs/{config_id}/extract-with-mode")
async def extract_figma_with_mode(
    config_id: int,
    extraction_mode: str = Query("simple", description="提取模式: simple/complete"),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    带模式选择的Figma需求提取
    
    Args:
        config_id: Figma配置ID
        extraction_mode: 提取模式
            - simple: 快速提取（5-10秒，不使用AI Vision）
            - complete: 完整分析（5-10分钟，使用AI Vision）
    
    Returns:
        task_id: 任务ID，用于查询进度
    """
    try:
        from app.db.sqlalchemy import async_session_factory
        
        # 验证提取模式
        if extraction_mode not in ['simple', 'complete']:
            return error_response(message="无效的提取模式，请选择 simple 或 complete")
        
        # 获取Figma配置
        config_crud = FigmaConfigCRUD(db)
        config = await config_crud.get_by_id_crud(config_id)
        
        if not config:
            return error_response(message="Figma配置不存在", code=404)
        
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
