"""
数据工厂Schema
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== 工具分类和列表 ====================

class ToolInfo(BaseModel):
    """工具信息"""
    name: str = Field(..., description="工具名称")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(..., description="工具描述")
    scenario: str = Field(..., description="使用场景")
    icon: str = Field(..., description="图标")


class ToolCategory(BaseModel):
    """工具分类"""
    category: str = Field(..., description="分类标识")
    name: str = Field(..., description="分类名称")
    scenario: str = Field(..., description="场景标识")
    icon: str = Field(..., description="图标")
    tools: Optional[List[ToolInfo]] = Field(default=None, description="工具列表")


class ToolCategoriesResponse(BaseModel):
    """工具分类响应"""
    categories: List[ToolCategory] = Field(..., description="分类列表")
    total_tools: int = Field(..., description="工具总数")


# ==================== 工具执行 ====================

class ToolExecuteRequest(BaseModel):
    """工具执行请求"""
    tool_name: str = Field(..., description="工具名称")
    tool_category: str = Field(..., description="工具分类")
    tool_scenario: str = Field(..., description="使用场景")
    input_data: Optional[Dict[str, Any]] = Field(default={}, description="输入数据")
    is_saved: bool = Field(default=True, description="是否保存记录")
    tags: Optional[List[str]] = Field(default=None, description="标签")


class ToolExecuteResponse(BaseModel):
    """工具执行响应"""
    result: Dict[str, Any] = Field(..., description="执行结果")
    record_id: Optional[int] = Field(default=None, description="记录ID")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")


# ==================== 批量生成 ====================

class BatchGenerateRequest(BaseModel):
    """批量生成请求"""
    tool_name: str = Field(..., description="工具名称")
    tool_category: str = Field(..., description="工具分类")
    tool_scenario: str = Field(..., description="使用场景")
    count: int = Field(default=10, ge=1, le=100, description="生成数量")
    input_data: Optional[Dict[str, Any]] = Field(default={}, description="输入数据")
    is_saved: bool = Field(default=True, description="是否保存记录")


class BatchGenerateResponse(BaseModel):
    """批量生成响应"""
    results: List[Dict[str, Any]] = Field(..., description="生成结果列表")
    count: int = Field(..., description="实际生成数量")
    total_requested: int = Field(..., description="请求生成数量")


# ==================== 记录管理 ====================

class DataFactoryRecordBase(BaseModel):
    """数据工厂记录基础"""
    tool_name: str = Field(..., description="工具名称")
    tool_category: str = Field(..., description="工具分类")
    tool_scenario: str = Field(..., description="使用场景")
    input_data: Optional[Dict[str, Any]] = Field(default=None, description="输入数据")
    output_data: Dict[str, Any] = Field(..., description="输出数据")
    is_saved: bool = Field(default=True, description="是否保存")
    tags: Optional[List[str]] = Field(default=None, description="标签")


class DataFactoryRecordCreate(DataFactoryRecordBase):
    """创建数据工厂记录"""
    pass


class DataFactoryRecordUpdate(BaseModel):
    """更新数据工厂记录"""
    tags: Optional[List[str]] = Field(default=None, description="标签")
    is_saved: Optional[bool] = Field(default=None, description="是否保存")


class DataFactoryRecordOut(DataFactoryRecordBase):
    """数据工厂记录输出"""
    id: int = Field(..., description="记录ID")
    user_id: int = Field(..., description="用户ID")
    creation_date: datetime = Field(..., description="创建时间")
    updation_date: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class DataFactoryRecordListResponse(BaseModel):
    """数据工厂记录列表响应"""
    items: List[DataFactoryRecordOut] = Field(..., description="记录列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页数量")


# ==================== 统计 ====================

class RecentTool(BaseModel):
    """最近使用工具"""
    tool_name: str = Field(..., description="工具名称")
    tool_category_display: str = Field(..., description="工具分类显示名")
    tool_scenario_display: str = Field(..., description="使用场景显示名")
    created_at: datetime = Field(..., description="使用时间")


class StatisticsResponse(BaseModel):
    """统计响应"""
    total_records: int = Field(..., description="总记录数")
    category_stats: Dict[str, int] = Field(..., description="分类统计")
    scenario_stats: Dict[str, int] = Field(..., description="场景统计")
    recent_tools: List[RecentTool] = Field(..., description="最近使用工具")


class TagsResponse(BaseModel):
    """标签响应"""
    tags: List[str] = Field(..., description="标签列表")
    count: int = Field(..., description="标签数量")
