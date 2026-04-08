"""
核心基础设施模块提供基础类和通用功能
"""

from app.core.base_crud import BaseCRUD
from app.core.base_model import BaseModel, TimestampMixin
from app.core.base_schema import BaseSchema, PageSchema
from app.core.permission import Permission

__all__ = [
    "BaseCRUD",
    "BaseModel",
    "TimestampMixin",
    "BaseSchema",
    "PageSchema",
    "Permission",
]
