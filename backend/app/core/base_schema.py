"""
基础Schema
提供通用的数据验证和序列化
"""

from datetime import datetime
from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel, Field, ConfigDict


class BaseSchema(BaseModel):
    """基础Schema"""
    
    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(BaseSchema):
    """时间戳Schema"""
    
    created_at: Optional[datetime] = Field(None, alias="creation_date", description="创建时间")
    updated_at: Optional[datetime] = Field(None, alias="updation_date", description="更新时间")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AuditSchema(BaseSchema):
    """审计Schema"""
    
    created_by: Optional[int] = Field(None, description="创建人ID")
    updated_by: Optional[int] = Field(None, description="更新人ID")


class PageQuerySchema(BaseSchema):
    """分页查询Schema"""
    
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=1000, description="每页数量")
    
    @property
    def skip(self) -> int:
        """计算跳过的记录数"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """获取限制数量"""
        return self.page_size


T = TypeVar('T')


class PageSchema(BaseSchema, Generic[T]):
    """分页响应Schema"""
    
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    items: List[T] = Field(..., description="数据列表")
    
    @property
    def total_pages(self) -> int:
        """总页数"""
        return (self.total + self.page_size - 1) // self.page_size
