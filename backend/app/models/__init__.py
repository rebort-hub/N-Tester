# -*- coding: utf-8 -*-
# @author: rebort

# 导入 Base，这是必需的
from app.models.base import Base

# 只在直接运行或应用启动时导入这些
if __name__ != "__main__":
    try:
        # 尝试导入所有模型（用于 Alembic）
        from app.models.rbac_models import *
        from app.models.celery_beat_models import *
        from app.models.api_models import *
    except ImportError as e:
        # 如果导入失败（比如在 Alembic 环境中缺少某些依赖），忽略
        print(f"模型导入警告: {e}")
        pass

# 只在应用运行时需要的功能
def init_db_module():
    """延迟导入需要完整依赖的模块"""
    import asyncio
    try:
        from loguru import logger
    except ImportError:
        import logging
        logger = logging.getLogger(__name__)
    
    from app.db.sqlalchemy import engine
    
    async def init_db():
        """
        初始化数据库
        :return:
        """
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    
    return init_db

# 导出 init_db 函数
try:
    init_db = init_db_module()
except Exception:
    # 如果无法创建 init_db（比如在 Alembic 环境中），提供一个占位符
    async def init_db():
        raise NotImplementedError("init_db is not available in this context")
