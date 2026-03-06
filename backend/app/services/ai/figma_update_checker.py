# -*- coding: utf-8 -*-
"""
Figma文件更新检测服务
"""

from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class FigmaUpdateChecker:
    """Figma文件更新检测"""
    
    @staticmethod
    async def check_for_updates(
        db_session,
        config_id: int,
        file_key: str,
        access_token: Optional[str] = None
    ) -> Dict:
        """检查文件是否有更新
        
        Args:
            db_session: 数据库会话
            config_id: Figma配置ID
            file_key: 文件ID
            access_token: 访问令牌
        
        Returns:
            {
                'has_updates': bool,
                'last_modified': str,
                'cached_modified': str,
                'changes_summary': str,
                'cache_exists': bool
            }
        """
        from app.services.ai.figma_cache_service import FigmaCacheService
        from app.services.ai.figma_service import FigmaService
        
        # 获取缓存信息
        cache_info = await FigmaCacheService.get_cache_info(db_session, file_key)
        
        if not cache_info:
            logger.info(f"无缓存数据: {file_key}")
            return {
                'has_updates': True,
                'last_modified': None,
                'cached_modified': None,
                'changes_summary': '首次提取，无缓存数据',
                'cache_exists': False
            }
        
        # 获取缓存的修改时间
        cached_modified = cache_info.get('last_modified')
        
        try:
            # 创建Figma服务
            figma_service = FigmaService(access_token=access_token)
            
            # 获取最新的文件信息（只获取元数据，不获取完整数据）
            # 注意：这里仍然需要调用get_file，但我们只关心lastModified字段
            file_data = await figma_service.get_file(file_key)
            latest_modified = file_data.get('lastModified')
            
            if not latest_modified:
                logger.warning(f"无法获取文件修改时间: {file_key}")
                return {
                    'has_updates': False,
                    'last_modified': None,
                    'cached_modified': cached_modified,
                    'changes_summary': '无法获取文件修改时间',
                    'cache_exists': True
                }
            
            # 标准化时间格式进行比较
            # Figma API返回: "2024-02-28T01:42:04Z"
            # 缓存返回: "2024-02-28T01:42:04+00:00" (from datetime.isoformat())
            # 需要统一格式后再比较
            try:
                # 将两个时间都转换为datetime对象进行比较
                latest_dt = datetime.fromisoformat(latest_modified.replace('Z', '+00:00'))
                
                # cached_modified可能是ISO字符串或None
                if cached_modified:
                    cached_dt = datetime.fromisoformat(cached_modified)
                    has_updates = latest_dt != cached_dt
                else:
                    has_updates = True
                    
                logger.info(
                    f"时间比较: latest={latest_dt.isoformat()}, "
                    f"cached={cached_dt.isoformat() if cached_modified else 'None'}, "
                    f"has_updates={has_updates}"
                )
            except Exception as e:
                logger.error(f"时间格式转换失败: {str(e)}")
                # 如果转换失败，回退到字符串比较
                has_updates = latest_modified != cached_modified
            
            # 生成变更摘要
            if has_updates:
                changes_summary = f"设计稿已更新（最后修改: {latest_modified}）"
            else:
                changes_summary = '设计稿无更新，已是最新版本'
            
            logger.info(
                f"更新检测: {file_key}, "
                f"has_updates={has_updates}, "
                f"latest={latest_modified}, "
                f"cached={cached_modified}"
            )
            
            return {
                'has_updates': has_updates,
                'last_modified': latest_modified,
                'cached_modified': cached_modified,
                'changes_summary': changes_summary,
                'cache_exists': True
            }
            
        except Exception as e:
            logger.error(f"检查更新失败: {file_key}, error={str(e)}")
            return {
                'has_updates': False,
                'last_modified': None,
                'cached_modified': cached_modified,
                'changes_summary': f'检查失败: {str(e)}',
                'cache_exists': True
            }
    
    @staticmethod
    async def mark_as_updated(db_session, config_id: int, has_updates: bool = True):
        """标记配置为已更新或已同步
        
        Args:
            db_session: 数据库会话
            config_id: Figma配置ID
            has_updates: 是否有更新
        """
        from sqlalchemy import update
        from app.api.v1.ai_intelligence.model import FigmaConfigModel
        
        stmt = update(FigmaConfigModel).where(
            FigmaConfigModel.id == config_id
        ).values(
            has_updates=1 if has_updates else 0,
            updation_date=datetime.now()
        )
        
        await db_session.execute(stmt)
        await db_session.commit()
        
        logger.info(f"标记配置更新状态: config_id={config_id}, has_updates={has_updates}")
