# 用例评审模块 - 数据传输对象层

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# 基础Schema
class ReviewBase(BaseModel):
    """评审基础Schema"""
    title: str = Field(..., description="评审标题", max_length=500)
    description: Optional[str] = Field(None, description="评审描述")
    priority: str = Field("medium", description="优先级: low/medium/high/urgent")
    deadline: Optional[datetime] = Field(None, description="截止日期")
    template_id: Optional[int] = Field(None, description="使用的模板ID")


class ReviewCreate(ReviewBase):
    """创建评审请求"""
    project_id: int = Field(..., description="关联项目ID")
    module_ids: Optional[List[int]] = Field([], description="关联的模块ID列表，系统将自动包含模块下的所有测试用例")
    test_case_ids: Optional[List[int]] = Field([], description="直接指定的测试用例ID列表（可选）")
    reviewer_ids: List[int] = Field([], description="评审人ID列表")


class ReviewUpdate(BaseModel):
    """更新评审请求"""
    title: Optional[str] = Field(None, description="评审标题", max_length=500)
    description: Optional[str] = Field(None, description="评审描述")
    priority: Optional[str] = Field(None, description="优先级")
    deadline: Optional[datetime] = Field(None, description="截止日期")
    status: Optional[str] = Field(None, description="评审状态")


class ReviewResponse(ReviewBase):
    """评审响应"""
    id: int = Field(..., description="评审ID")
    project_id: int = Field(..., description="关联项目ID")
    status: str = Field(..., description="评审状态")
    creator_id: int = Field(..., description="创建人ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    # 关联数据
    test_case_count: int = Field(0, description="关联用例数量")
    reviewer_count: int = Field(0, description="评审人数量")
    comment_count: int = Field(0, description="评论数量")
    progress: float = Field(0.0, description="评审进度")

    class Config:
        from_attributes = True


# 评审分配相关Schema
class AssignmentBase(BaseModel):
    """评审分配基础Schema"""
    reviewer_id: int = Field(..., description="评审人ID")


class AssignmentCreate(AssignmentBase):
    """创建评审分配请求"""
    pass


class AssignmentUpdate(BaseModel):
    """更新评审分配请求"""
    status: Optional[str] = Field(None, description="评审状态")
    comment: Optional[str] = Field(None, description="评审意见")
    checklist_results: Optional[Dict[str, Any]] = Field(None, description="检查清单结果")


class AssignmentResponse(AssignmentBase):
    """评审分配响应"""
    id: int = Field(..., description="分配ID")
    review_id: int = Field(..., description="评审ID")
    status: str = Field(..., description="评审状态")
    comment: Optional[str] = Field(None, description="评审意见")
    checklist_results: Optional[Dict[str, Any]] = Field(None, description="检查清单结果")
    reviewed_at: Optional[datetime] = Field(None, description="评审时间")
    assigned_at: datetime = Field(..., description="分配时间")
    
    # 关联数据
    reviewer_name: Optional[str] = Field(None, description="评审人姓名")

    class Config:
        from_attributes = True


# 评审意见相关Schema
class CommentBase(BaseModel):
    """评审意见基础Schema"""
    test_case_id: Optional[int] = Field(None, description="相关用例ID")
    comment_type: str = Field("general", description="意见类型: general/suggestion/issue/question")
    content: str = Field(..., description="意见内容")
    step_number: Optional[int] = Field(None, description="步骤序号")


class CommentCreate(CommentBase):
    """创建评审意见请求"""
    pass


class CommentUpdate(BaseModel):
    """更新评审意见请求"""
    content: Optional[str] = Field(None, description="意见内容")
    is_resolved: Optional[bool] = Field(None, description="是否已解决")


class CommentResponse(CommentBase):
    """评审意见响应"""
    id: int = Field(..., description="意见ID")
    review_id: int = Field(..., description="评审ID")
    author_id: int = Field(..., description="评论者ID")
    is_resolved: bool = Field(..., description="是否已解决")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 关联数据
    author_name: Optional[str] = Field(None, description="评论者姓名")
    test_case_title: Optional[str] = Field(None, description="相关用例标题")

    class Config:
        from_attributes = True


# 评审模板相关Schema
class TemplateBase(BaseModel):
    """评审模板基础Schema"""
    name: str = Field(..., description="模板名称", max_length=200)
    description: Optional[str] = Field(None, description="模板描述")
    checklist: Optional[Dict[str, Any]] = Field(None, description="检查清单")


class TemplateCreate(TemplateBase):
    """创建评审模板请求"""
    project_ids: List[int] = Field([], description="关联项目ID列表")
    default_reviewer_ids: List[int] = Field([], description="默认评审人ID列表")


class TemplateUpdate(BaseModel):
    """更新评审模板请求"""
    name: Optional[str] = Field(None, description="模板名称", max_length=200)
    description: Optional[str] = Field(None, description="模板描述")
    checklist: Optional[Dict[str, Any]] = Field(None, description="检查清单")
    is_active: Optional[bool] = Field(None, description="是否启用")


class TemplateResponse(TemplateBase):
    """评审模板响应"""
    id: int = Field(..., description="模板ID")
    is_active: bool = Field(..., description="是否启用")
    creator_id: int = Field(..., description="创建人ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 关联数据
    project_count: int = Field(0, description="关联项目数量")
    reviewer_count: int = Field(0, description="默认评审人数量")
    usage_count: int = Field(0, description="使用次数")

    class Config:
        from_attributes = True


# 统计相关Schema
class ReviewStatistics(BaseModel):
    """评审统计"""
    total_reviews: int = Field(0, description="总评审数")
    pending_reviews: int = Field(0, description="待评审数")
    in_progress_reviews: int = Field(0, description="进行中评审数")
    completed_reviews: int = Field(0, description="已完成评审数")
    cancelled_reviews: int = Field(0, description="已取消评审数")
    overdue_reviews: int = Field(0, description="逾期评审数")
    avg_completion_time: float = Field(0.0, description="平均完成时间(小时)")
    total_comments: int = Field(0, description="总评论数")
    unresolved_comments: int = Field(0, description="未解决评论数")


# 分页响应Schema
class PaginatedResponse(BaseModel):
    """分页响应"""
    items: List[Any] = Field([], description="数据列表")
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页")
    page_size: int = Field(20, description="每页大小")
    pages: int = Field(0, description="总页数")