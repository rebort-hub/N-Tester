# -*- coding: utf-8 -*-
"""
Figma高级功能Controller
包含：速率限制、缓存、更新检测等API
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.sqlalchemy import get_db
from app.core.dependencies import get_current_user_id
from app.common.response import success_response, error_response

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 速率限制API ====================

@router.get("/figma-configs/{config_id}/rate-limit-status")
async def get_rate_limit_status(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取速率限制状态
    
    Args:
        config_id: Figma配置ID
    
    Returns:
        速率限制状态信息
    """
    try:
        from app.services.ai.figma_rate_limiter import FigmaRateLimiter
        
        status = await FigmaRateLimiter.check_rate_limit(db, config_id)
        
        return success_response(data=status)
        
    except Exception as e:
        logger.error(f"获取速率限制状态失败: {str(e)}")
        return error_response(message=f"获取失败: {str(e)}")


# ==================== 缓存管理API ====================

@router.get("/figma-configs/{config_id}/cache-info")
async def get_cache_info(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取缓存信息
    
    Args:
        config_id: Figma配置ID
    
    Returns:
        缓存信息
    """
    try:
        from .crud import FigmaConfigCRUD
        from app.services.ai.figma_cache_service import FigmaCacheService
        
        # 获取配置
        config_crud = FigmaConfigCRUD(db)
        config = await config_crud.get_by_id_crud(config_id)
        
        if not config:
            return error_response(message="配置不存在", code=404)
        
        # 获取缓存信息
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
    """获取缓存的Figma数据（离线查看）
    
    Args:
        config_id: Figma配置ID
    
    Returns:
        缓存的文件数据
    """
    try:
        from .crud import FigmaConfigCRUD
        from app.services.ai.figma_cache_service import FigmaCacheService
        from app.services.ai.figma_service import FigmaService
        
        # 获取配置
        config_crud = FigmaConfigCRUD(db)
        config = await config_crud.get_by_id_crud(config_id)
        
        if not config:
            return error_response(message="配置不存在", code=404)
        
        # 从缓存获取数据
        cached_data = await FigmaCacheService.get_cached_file(
            db, config.file_key, force_refresh=False
        )
        
        if not cached_data:
            return error_response(
                message="暂无缓存数据，请先进行一次提取",
                code=404
            )
        
        # 提取页面和Frame信息
        figma_service = FigmaService()
        pages = await figma_service.extract_pages_and_frames(cached_data)
        
        # 获取缓存信息
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
    """清除缓存
    
    Args:
        config_id: Figma配置ID
    
    Returns:
        操作结果
    """
    try:
        from .crud import FigmaConfigCRUD
        from app.services.ai.figma_cache_service import FigmaCacheService
        
        # 获取配置
        config_crud = FigmaConfigCRUD(db)
        config = await config_crud.get_by_id_crud(config_id)
        
        if not config:
            return error_response(message="配置不存在", code=404)
        
        # 清除缓存
        deleted_count = await FigmaCacheService.clear_cache_by_file_key(
            db, config.file_key
        )
        
        if deleted_count > 0:
            return success_response(message=f"已清除 {deleted_count} 条缓存")
        else:
            return success_response(message="无缓存数据需要清除")
        
    except Exception as e:
        logger.error(f"清除缓存失败: {str(e)}")
        return error_response(message=f"清除失败: {str(e)}")


# ==================== 更新检测API ====================

@router.get("/figma-configs/{config_id}/check-updates")
async def check_figma_updates(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """检查Figma文件是否有更新
    
    Args:
        config_id: Figma配置ID
    
    Returns:
        更新检测结果
    """
    try:
        from .crud import FigmaConfigCRUD
        from app.services.ai.figma_update_checker import FigmaUpdateChecker
        
        # 获取配置
        config_crud = FigmaConfigCRUD(db)
        config = await config_crud.get_by_id_crud(config_id)
        
        if not config:
            return error_response(message="配置不存在", code=404)
        
        # 检查更新
        update_info = await FigmaUpdateChecker.check_for_updates(
            db, config_id, config.file_key, config.access_token
        )
        
        # 更新配置表
        await FigmaUpdateChecker.mark_as_updated(
            db, config_id, update_info['has_updates']
        )
        
        return success_response(data=update_info)
        
    except Exception as e:
        logger.error(f"检查更新失败: {str(e)}")
        return error_response(message=f"检查失败: {str(e)}")


# ==================== 统计API ====================

@router.get("/figma-configs/{config_id}/statistics")
async def get_figma_statistics(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取Figma配置的统计信息
    
    Args:
        config_id: Figma配置ID
    
    Returns:
        统计信息
    """
    try:
        from sqlalchemy import select, func
        from app.api.v1.ai_intelligence.model import (
            FigmaAPICallLogModel,
            FigmaExtractionTaskModel
        )
        from datetime import datetime, timedelta
        
        # 统计API调用次数
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        stmt = select(func.count(FigmaAPICallLogModel.id)).where(
            FigmaAPICallLogModel.config_id == config_id,
            FigmaAPICallLogModel.call_time >= today_start,
            FigmaAPICallLogModel.enabled_flag == 1
        )
        result = await db.execute(stmt)
        today_calls = result.scalar() or 0
        
        # 统计提取任务
        stmt = select(func.count(FigmaExtractionTaskModel.id)).where(
            FigmaExtractionTaskModel.config_id == config_id,
            FigmaExtractionTaskModel.enabled_flag == 1
        )
        result = await db.execute(stmt)
        total_tasks = result.scalar() or 0
        
        # 统计成功的任务
        stmt = select(func.count(FigmaExtractionTaskModel.id)).where(
            FigmaExtractionTaskModel.config_id == config_id,
            FigmaExtractionTaskModel.status == 'completed',
            FigmaExtractionTaskModel.enabled_flag == 1
        )
        result = await db.execute(stmt)
        completed_tasks = result.scalar() or 0
        
        return success_response(data={
            'today_api_calls': today_calls,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'success_rate': round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0
        })
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        return error_response(message=f"获取失败: {str(e)}")
