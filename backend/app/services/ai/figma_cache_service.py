# -*- coding: utf-8 -*-
"""
Figma数据缓存服务
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
import json
import logging

logger = logging.getLogger(__name__)


class FigmaCacheService:
    """Figma数据缓存服务"""
    
    CACHE_EXPIRY_HOURS = 24  # 缓存有效期24小时
    
    @staticmethod
    async def get_cached_file(
        db_session, 
        file_key: str,
        force_refresh: bool = False
    ) -> Optional[Dict]:
        """获取缓存的文件数据
        
        Args:
            db_session: 数据库会话
            file_key: 文件ID
            force_refresh: 是否强制刷新
        
        Returns:
            文件数据或None
        """
        if force_refresh:
            logger.info(f"强制刷新，跳过缓存: {file_key}")
            return None
        
        from sqlalchemy import select
        from app.api.v1.ai_intelligence.model import FigmaFileCacheModel
        
        # 查询缓存
        stmt = select(FigmaFileCacheModel).where(
            FigmaFileCacheModel.file_key == file_key,
            FigmaFileCacheModel.enabled_flag == 1
        )
        result = await db_session.execute(stmt)
        cache = result.scalar_one_or_none()
        
        if not cache:
            logger.info(f"缓存不存在: {file_key}")
            return None
        
        # 检查缓存是否过期
        cache_age = datetime.now() - cache.cache_time
        if cache_age.total_seconds() > FigmaCacheService.CACHE_EXPIRY_HOURS * 3600:
            logger.info(f"缓存已过期: {file_key}, 年龄: {cache_age}")
            return None
        
        # 更新命中次数
        cache.hit_count += 1
        await db_session.commit()
        
        logger.info(
            f"使用缓存数据: {file_key}, "
            f"命中次数: {cache.hit_count}, "
            f"缓存年龄: {cache_age}"
        )
        
        try:
            return json.loads(cache.file_data)
        except json.JSONDecodeError as e:
            logger.error(f"缓存数据解析失败: {file_key}, error={str(e)}")
            return None
    
    @staticmethod
    async def save_file_cache(
        db_session,
        config_id: int,
        file_key: str,
        file_data: Dict,
        file_version: str = None,
        current_user_id: int = None
    ):
        """保存文件缓存
        
        Args:
            db_session: 数据库会话
            config_id: Figma配置ID
            file_key: 文件ID
            file_data: 文件数据
            file_version: 文件版本
            current_user_id: 当前用户ID
        """
        from sqlalchemy import select
        from app.api.v1.ai_intelligence.model import FigmaFileCacheModel
        
        # 检查是否已存在
        stmt = select(FigmaFileCacheModel).where(
            FigmaFileCacheModel.file_key == file_key
        )
        result = await db_session.execute(stmt)
        cache = result.scalar_one_or_none()
        
        file_data_json = json.dumps(file_data, ensure_ascii=False)
        cache_size = len(file_data_json.encode('utf-8'))
        
        # 提取最后修改时间
        last_modified = file_data.get('lastModified')
        if last_modified and isinstance(last_modified, str):
            try:
                # Figma返回的是ISO格式时间字符串
                last_modified = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
            except:
                last_modified = None
        
        if cache:
            # 更新缓存
            cache.file_data = file_data_json
            cache.file_version = file_version
            cache.cache_time = datetime.now()
            cache.cache_size = cache_size
            cache.last_modified = last_modified
            cache.updation_date = datetime.now()
            
            logger.info(f"更新文件缓存: {file_key}, 大小: {cache_size} bytes")
        else:
            # 创建新缓存
            cache = FigmaFileCacheModel(
                config_id=config_id,
                file_key=file_key,
                file_data=file_data_json,
                file_version=file_version,
                cache_time=datetime.now(),
                cache_size=cache_size,
                last_modified=last_modified,
                hit_count=0,
                created_by=current_user_id,
                enabled_flag=1
            )
            db_session.add(cache)
            
            logger.info(f"创建文件缓存: {file_key}, 大小: {cache_size} bytes")
        
        await db_session.commit()
    
    @staticmethod
    async def get_cache_info(db_session, file_key: str) -> Optional[Dict]:
        """获取缓存信息（不返回数据）
        
        Args:
            db_session: 数据库会话
            file_key: 文件ID
        
        Returns:
            缓存信息或None
        """
        from sqlalchemy import select
        from app.api.v1.ai_intelligence.model import FigmaFileCacheModel
        
        stmt = select(FigmaFileCacheModel).where(
            FigmaFileCacheModel.file_key == file_key,
            FigmaFileCacheModel.enabled_flag == 1
        )
        result = await db_session.execute(stmt)
        cache = result.scalar_one_or_none()
        
        if not cache:
            return None
        
        cache_age = datetime.now() - cache.cache_time
        is_expired = cache_age.total_seconds() > FigmaCacheService.CACHE_EXPIRY_HOURS * 3600
        
        return {
            'file_key': cache.file_key,
            'cache_time': cache.cache_time.isoformat() if cache.cache_time else None,
            'cache_age_hours': round(cache_age.total_seconds() / 3600, 2),
            'cache_size': cache.cache_size,
            'hit_count': cache.hit_count,
            'is_expired': is_expired,
            'last_modified': cache.last_modified.isoformat() if cache.last_modified else None
        }
    
    @staticmethod
    async def clear_expired_cache(db_session):
        """清理过期缓存
        
        Args:
            db_session: 数据库会话
        
        Returns:
            清理的记录数
        """
        from sqlalchemy import delete
        from app.api.v1.ai_intelligence.model import FigmaFileCacheModel
        
        expiry_time = datetime.now() - timedelta(hours=FigmaCacheService.CACHE_EXPIRY_HOURS)
        
        stmt = delete(FigmaFileCacheModel).where(
            FigmaFileCacheModel.cache_time < expiry_time
        )
        result = await db_session.execute(stmt)
        await db_session.commit()
        
        logger.info(f"清理过期缓存: {result.rowcount} 条")
        
        return result.rowcount
    
    @staticmethod
    async def clear_cache_by_file_key(db_session, file_key: str):
        """清除指定文件的缓存
        
        Args:
            db_session: 数据库会话
            file_key: 文件ID
        """
        from sqlalchemy import delete
        from app.api.v1.ai_intelligence.model import FigmaFileCacheModel
        
        stmt = delete(FigmaFileCacheModel).where(
            FigmaFileCacheModel.file_key == file_key
        )
        result = await db_session.execute(stmt)
        await db_session.commit()
        
        logger.info(f"清除文件缓存: {file_key}, 删除{result.rowcount}条")
        
        return result.rowcount
