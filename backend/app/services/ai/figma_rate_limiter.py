# -*- coding: utf-8 -*-
"""
Figma API速率限制管理服务
"""

from datetime import datetime, timedelta
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class FigmaRateLimiter:
    """Figma API速率限制管理"""
    
    # 限制规则（基于Figma官方文档的保守估计）
    RATE_LIMITS = {
        'per_minute': 60,      # 每分钟60次
        'per_hour': 1000,      # 每小时1000次
        'per_day': 10000       # 每天10000次
    }
    
    @staticmethod
    async def check_rate_limit(db_session, config_id: int) -> Dict:
        """检查速率限制状态
        
        Args:
            db_session: 数据库会话
            config_id: Figma配置ID
        
        Returns:
            {
                'can_call': bool,
                'remaining_minute': int,
                'remaining_hour': int,
                'remaining_day': int,
                'wait_seconds': int,
                'warning_level': str  # 'safe', 'warning', 'danger'
            }
        """
        from sqlalchemy import select, func
        from app.api.v1.ai_intelligence.model import FigmaAPICallLogModel
        
        now = datetime.now()
        
        # 查询最近1分钟的调用次数
        minute_ago = now - timedelta(minutes=1)
        stmt = select(func.count(FigmaAPICallLogModel.id)).where(
            FigmaAPICallLogModel.config_id == config_id,
            FigmaAPICallLogModel.call_time >= minute_ago,
            FigmaAPICallLogModel.enabled_flag == 1
        )
        result = await db_session.execute(stmt)
        minute_calls = result.scalar() or 0
        
        # 查询最近1小时的调用次数
        hour_ago = now - timedelta(hours=1)
        stmt = select(func.count(FigmaAPICallLogModel.id)).where(
            FigmaAPICallLogModel.config_id == config_id,
            FigmaAPICallLogModel.call_time >= hour_ago,
            FigmaAPICallLogModel.enabled_flag == 1
        )
        result = await db_session.execute(stmt)
        hour_calls = result.scalar() or 0
        
        # 查询今天的调用次数
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(func.count(FigmaAPICallLogModel.id)).where(
            FigmaAPICallLogModel.config_id == config_id,
            FigmaAPICallLogModel.call_time >= day_start,
            FigmaAPICallLogModel.enabled_flag == 1
        )
        result = await db_session.execute(stmt)
        day_calls = result.scalar() or 0
        
        # 计算剩余配额
        remaining_minute = max(0, FigmaRateLimiter.RATE_LIMITS['per_minute'] - minute_calls)
        remaining_hour = max(0, FigmaRateLimiter.RATE_LIMITS['per_hour'] - hour_calls)
        remaining_day = max(0, FigmaRateLimiter.RATE_LIMITS['per_day'] - day_calls)
        
        # 判断是否可以调用
        can_call = (
            remaining_minute > 0 and 
            remaining_hour > 0 and 
            remaining_day > 0
        )
        
        # 计算需要等待的时间
        wait_seconds = 0
        if not can_call:
            if remaining_minute == 0:
                wait_seconds = 60
            elif remaining_hour == 0:
                wait_seconds = 3600
            elif remaining_day == 0:
                wait_seconds = 86400
        
        # 判断警告级别
        warning_level = 'safe'
        if remaining_minute < 10 or remaining_hour < 100:
            warning_level = 'warning'
        if remaining_minute < 5 or remaining_hour < 50:
            warning_level = 'danger'
        
        logger.info(
            f"速率限制检查: config_id={config_id}, "
            f"minute={minute_calls}/{FigmaRateLimiter.RATE_LIMITS['per_minute']}, "
            f"hour={hour_calls}/{FigmaRateLimiter.RATE_LIMITS['per_hour']}, "
            f"day={day_calls}/{FigmaRateLimiter.RATE_LIMITS['per_day']}, "
            f"can_call={can_call}"
        )
        
        return {
            'can_call': can_call,
            'remaining_minute': remaining_minute,
            'remaining_hour': remaining_hour,
            'remaining_day': remaining_day,
            'total_minute': FigmaRateLimiter.RATE_LIMITS['per_minute'],
            'total_hour': FigmaRateLimiter.RATE_LIMITS['per_hour'],
            'total_day': FigmaRateLimiter.RATE_LIMITS['per_day'],
            'wait_seconds': wait_seconds,
            'warning_level': warning_level
        }
    
    @staticmethod
    async def log_api_call(
        db_session, 
        config_id: int, 
        endpoint: str,
        status_code: int,
        response_time: int,
        current_user_id: int = None
    ):
        """记录API调用
        
        Args:
            db_session: 数据库会话
            config_id: Figma配置ID
            endpoint: API端点
            status_code: HTTP状态码
            response_time: 响应时间(ms)
            current_user_id: 当前用户ID
        """
        from app.api.v1.ai_intelligence.model import FigmaAPICallLogModel
        
        log = FigmaAPICallLogModel(
            config_id=config_id,
            endpoint=endpoint,
            call_time=datetime.now(),
            status_code=status_code,
            response_time=response_time,
            is_rate_limited=1 if status_code == 429 else 0,
            created_by=current_user_id,
            enabled_flag=1
        )
        db_session.add(log)
        await db_session.commit()
        
        logger.info(
            f"记录API调用: config_id={config_id}, endpoint={endpoint}, "
            f"status={status_code}, time={response_time}ms"
        )
    
    @staticmethod
    async def clean_old_logs(db_session, days: int = 30):
        """清理旧日志
        
        Args:
            db_session: 数据库会话
            days: 保留天数
        """
        from sqlalchemy import delete
        from app.api.v1.ai_intelligence.model import FigmaAPICallLogModel
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        stmt = delete(FigmaAPICallLogModel).where(
            FigmaAPICallLogModel.call_time < cutoff_date
        )
        result = await db_session.execute(stmt)
        await db_session.commit()
        
        logger.info(f"清理旧日志: 删除{result.rowcount}条记录")
        
        return result.rowcount
