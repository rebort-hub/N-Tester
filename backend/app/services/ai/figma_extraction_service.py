# -*- coding: utf-8 -*-
"""
Figma提取服务 - 支持简化和完整两种模式
"""

import uuid
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from .figma_service import FigmaService
from .figma_requirement_service import FigmaRequirementService

logger = logging.getLogger(__name__)


class FigmaExtractionService:
    """Figma提取服务"""
    
    @staticmethod
    async def create_extraction_task(
        db_session,
        config_id: int,
        extraction_mode: str,
        current_user_id: int
    ) -> str:
        """创建提取任务
        
        Args:
            db_session: 数据库会话
            config_id: Figma配置ID
            extraction_mode: 提取模式 (simple/complete)
            current_user_id: 当前用户ID
        
        Returns:
            task_id: 任务ID
        """
        from app.api.v1.ai_intelligence.model import FigmaExtractionTaskModel
        
        task_id = str(uuid.uuid4())
        
        task = FigmaExtractionTaskModel(
            task_id=task_id,
            config_id=config_id,
            extraction_mode=extraction_mode,
            status='pending',
            progress=0,
            start_time=datetime.now(),
            created_by=current_user_id,
            enabled_flag=1
        )
        
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        
        logger.info(f"创建提取任务: task_id={task_id}, mode={extraction_mode}")
        
        return task_id
    
    @staticmethod
    async def update_task_progress(
        db_session,
        task_id: str,
        progress: int,
        current_step: str,
        processed_frames: int = None
    ):
        """更新任务进度"""
        from app.api.v1.ai_intelligence.crud import FigmaExtractionTaskCRUD
        
        task_crud = FigmaExtractionTaskCRUD(db_session)
        task = await task_crud.get_by_task_id(task_id)
        
        if task:
            update_data = {
                'progress': progress,
                'current_step': current_step,
                'status': 'processing'
            }
            if processed_frames is not None:
                update_data['processed_frames'] = processed_frames
            
            await task_crud.update_crud(task.id, update_data)
            await db_session.commit()
            
            logger.info(f"更新任务进度: {task_id} - {progress}% - {current_step}")
    
    @staticmethod
    async def complete_task(
        db_session,
        task_id: str,
        result_document_id: int
    ):
        """完成任务"""
        from app.api.v1.ai_intelligence.crud import FigmaExtractionTaskCRUD
        
        task_crud = FigmaExtractionTaskCRUD(db_session)
        task = await task_crud.get_by_task_id(task_id)
        
        if task:
            await task_crud.update_crud(task.id, {
                'status': 'completed',
                'progress': 100,
                'current_step': '提取完成',
                'result_document_id': result_document_id,
                'end_time': datetime.now()
            })
            await db_session.commit()
            
            logger.info(f"任务完成: {task_id}, document_id={result_document_id}")
    
    @staticmethod
    async def fail_task(
        db_session,
        task_id: str,
        error_message: str
    ):
        """任务失败"""
        from app.api.v1.ai_intelligence.crud import FigmaExtractionTaskCRUD
        
        task_crud = FigmaExtractionTaskCRUD(db_session)
        task = await task_crud.get_by_task_id(task_id)
        
        if task:
            await task_crud.update_crud(task.id, {
                'status': 'failed',
                'error_message': error_message,
                'end_time': datetime.now()
            })
            await db_session.commit()
            
            logger.error(f"任务失败: {task_id}, error={error_message}")
    
    @staticmethod
    async def extract_simple(
        db_session,
        task_id: str,
        config,
        project_name: str,
        current_user_id: int
    ) -> int:
        """简化提取 - 不使用AI Vision"""
        from app.api.v1.ai_intelligence.model import (
            RequirementDocumentModel,
            RequirementAnalysisModel,
            BusinessRequirementModel
        )
        
        try:
            # 更新进度: 开始
            await FigmaExtractionService.update_task_progress(
                db_session, task_id, 10, "连接Figma API..."
            )
            
            # 创建Figma服务（传入db_session和config_id以支持缓存）
            figma_service = FigmaService(
                access_token=config.access_token,
                config_id=config.id,
                db_session=db_session,
                current_user_id=current_user_id
            )
            
            # 获取文件数据（会自动使用缓存和保存缓存）
            await FigmaExtractionService.update_task_progress(
                db_session, task_id, 20, "获取文件数据..."
            )
            file_data = await figma_service.get_file(config.file_key, use_cache=True)
            file_name = file_data.get('name', 'Unknown')
            
            # 提取页面和Frame
            await FigmaExtractionService.update_task_progress(
                db_session, task_id, 40, "提取页面和Frame..."
            )
            pages = await figma_service.extract_pages_and_frames(file_data)
            
            # 统计Frame数量
            total_frames = sum(len(page.get('frames', [])) for page in pages)
            
            # 更新总Frame数
            from app.api.v1.ai_intelligence.crud import FigmaExtractionTaskCRUD
            task_crud = FigmaExtractionTaskCRUD(db_session)
            task = await task_crud.get_by_task_id(task_id)
            await task_crud.update_crud(task.id, {'total_frames': total_frames})
            await db_session.commit()
            
            # 生成基础需求
            await FigmaExtractionService.update_task_progress(
                db_session, task_id, 60, f"生成需求（共{total_frames}个Frame）..."
            )
            
            requirements = []
            for page_idx, page in enumerate(pages, 1):
                page_name = page.get('name', f'Page {page_idx}')
                frames = page.get('frames', [])
                
                for frame_idx, frame in enumerate(frames, 1):
                    frame_name = frame.get('name', f'Frame {frame_idx}')
                    req_id = f"REQ-{page_idx:02d}-{frame_idx:02d}"
                    
                    requirement = {
                        'requirement_id': req_id,
                        'requirement_name': f"{page_name} - {frame_name}",
                        'requirement_type': '功能需求',
                        'module': page_name,
                        'requirement_level': '中',
                        'description': f"实现{frame_name}的功能界面",
                        'acceptance_criteria': f"1. {frame_name}界面正常显示\n2. 界面元素布局正确"
                    }
                    requirements.append(requirement)
            
            # 保存到数据库
            await FigmaExtractionService.update_task_progress(
                db_session, task_id, 80, "保存需求到数据库..."
            )
            
            # 创建需求文档
            document = RequirementDocumentModel(
                project_id=config.project_id,
                title=f"Figma需求-{file_name}",
                file_path=config.file_url or f"figma://{config.file_key}",
                document_type="figma",
                status="analyzed",
                uploaded_by=current_user_id,
                created_by=current_user_id,
                enabled_flag=1
            )
            db_session.add(document)
            await db_session.flush()
            
            # 创建分析记录
            summary = f"从Figma设计稿《{file_name}》提取了{len(requirements)}个需求，涵盖{len(pages)}个页面（简化模式）"
            analysis = RequirementAnalysisModel(
                document_id=document.id,
                analysis_report=summary,
                requirements_count=len(requirements),
                analysis_time=0,
                created_by=current_user_id,
                enabled_flag=1
            )
            db_session.add(analysis)
            await db_session.flush()
            
            # 保存需求
            for req in requirements:
                requirement = BusinessRequirementModel(
                    analysis_id=analysis.id,
                    requirement_id=req['requirement_id'],
                    requirement_name=req['requirement_name'],
                    requirement_type=req['requirement_type'],
                    module=req['module'],
                    requirement_level=req['requirement_level'],
                    description=req['description'],
                    acceptance_criteria=req['acceptance_criteria'],
                    created_by=current_user_id,
                    enabled_flag=1
                )
                db_session.add(requirement)
            
            # 更新Figma配置的同步时间
            config.last_sync_time = datetime.now()
            
            await db_session.commit()
            
            logger.info(f"简化提取完成: document_id={document.id}, requirements={len(requirements)}")
            
            return document.id
            
        except Exception as e:
            logger.error(f"简化提取失败: {str(e)}", exc_info=True)
            raise e
    
    @staticmethod
    async def extract_complete(
        db_session,
        task_id: str,
        config,
        ai_model_config: Dict[str, Any],
        project_name: str,
        current_user_id: int
    ) -> int:
        """完整提取 - 使用AI Vision分析"""
        from app.api.v1.ai_intelligence.model import (
            RequirementDocumentModel,
            RequirementAnalysisModel,
            BusinessRequirementModel
        )
        
        try:
            # 更新进度
            await FigmaExtractionService.update_task_progress(
                db_session, task_id, 10, "初始化AI Vision服务..."
            )
            
            # 创建提取服务
            service = FigmaRequirementService(
                figma_token=config.access_token,
                ai_model_config=ai_model_config
            )
            
            # 执行提取（带进度回调）
            await FigmaExtractionService.update_task_progress(
                db_session, task_id, 20, "开始AI分析..."
            )
            
            result = await service.extract_requirements_from_figma(
                file_key=config.file_key,
                project_name=project_name
            )
            
            # 保存结果
            await FigmaExtractionService.update_task_progress(
                db_session, task_id, 80, "保存分析结果..."
            )
            
            # 创建需求文档
            file_name = result.get('summary', '').split('《')[1].split('》')[0] if '《' in result.get('summary', '') else 'Unknown'
            
            document = RequirementDocumentModel(
                project_id=config.project_id,
                title=f"Figma需求-{file_name}",
                file_path=config.file_url or f"figma://{config.file_key}",
                document_type="figma",
                status="analyzed",
                uploaded_by=current_user_id,
                created_by=current_user_id,
                enabled_flag=1
            )
            db_session.add(document)
            await db_session.flush()
            
            # 创建分析记录
            analysis = RequirementAnalysisModel(
                document_id=document.id,
                analysis_report=result['summary'],
                requirements_count=len(result['requirements']),
                analysis_time=0,
                created_by=current_user_id,
                enabled_flag=1
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
                    created_by=current_user_id,
                    enabled_flag=1
                )
                db_session.add(requirement)
            
            # 更新同步时间
            config.last_sync_time = datetime.now()
            
            await db_session.commit()
            
            logger.info(f"完整提取完成: document_id={document.id}")
            
            return document.id
            
        except Exception as e:
            logger.error(f"完整提取失败: {str(e)}", exc_info=True)
            raise e
