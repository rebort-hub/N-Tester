"""
定时数据验证模式
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


# 请求模式
class TaskListRequest(BaseModel):
    """任务列表请求"""
    name: Optional[str] = Field(None, description="任务名称（模糊匹配）")
    type: Optional[int] = Field(None, description="任务类型: 1-APP自动化, 2-Web UI自动化, 3-接口自动化")
    status: Optional[int] = Field(None, description="任务状态: 0-停用, 1-启用")
    page: int = Field(1, ge=1, description="页码，从1开始")
    size: int = Field(10, ge=1, le=200, description="每页数量")


class CreateTaskRequest(BaseModel):
    """创建任务请求"""
    name: str = Field(..., description="任务名称")
    type: int = Field(..., description="任务类型: 1-APP自动化, 2-Web UI自动化, 3-接口自动化")
    script: Dict[str, Any] = Field(..., description="任务脚本配置")
    time: Dict[str, Any] = Field(..., description="时间配置")
    notice: Optional[Dict[str, Any]] = Field(None, description="通知配置")
    description: Optional[str] = Field(None, description="任务描述")


class UpdateTaskRequest(BaseModel):
    """更新任务请求"""
    task_id: int = Field(..., description="任务ID")
    name: Optional[str] = Field(None, description="任务名称")
    type: Optional[int] = Field(None, description="任务类型")
    status: Optional[int] = Field(None, description="任务状态")
    script: Optional[Dict[str, Any]] = Field(None, description="任务脚本配置")
    time: Optional[Dict[str, Any]] = Field(None, description="时间配置")
    notice: Optional[Dict[str, Any]] = Field(None, description="通知配置")
    description: Optional[str] = Field(None, description="任务描述")


class DeleteTaskRequest(BaseModel):
    """删除任务请求"""
    task_id: int = Field(..., description="任务ID")


class NoticeListRequest(BaseModel):
    """通知列表请求"""
    name: Optional[str] = Field(None, description="通知名称（模糊匹配）")
    type: Optional[int] = Field(None, description="通知类型")
    status: Optional[int] = Field(None, description="通知状态: 0-停用, 1-启用")
    page: int = Field(1, ge=1, description="页码，从1开始")
    size: int = Field(10, ge=1, le=200, description="每页数量")


class CreateNoticeRequest(BaseModel):
    """创建通知请求"""
    name: str = Field(..., description="通知名称")
    type: int = Field(..., description="通知类型")
    value: str = Field(..., description="通知地址")
    script: Optional[Dict[str, Any]] = Field(None, description="通知脚本配置")
    description: Optional[str] = Field(None, description="通知描述")


class UpdateNoticeRequest(BaseModel):
    """更新通知请求"""
    notice_id: int = Field(..., description="通知ID")
    name: Optional[str] = Field(None, description="通知名称")
    type: Optional[int] = Field(None, description="通知类型")
    value: Optional[str] = Field(None, description="通知地址")
    status: Optional[int] = Field(None, description="通知状态")
    script: Optional[Dict[str, Any]] = Field(None, description="通知脚本配置")
    description: Optional[str] = Field(None, description="通知描述")


class DeleteNoticeRequest(BaseModel):
    """删除通知请求"""
    notice_id: int = Field(..., description="通知ID")


class TaskHistoryRequest(BaseModel):
    """任务历史请求"""
    task_id: Optional[int] = Field(None, description="任务ID")
    status: Optional[str] = Field(None, description="执行状态: success/failed/running/timeout")
    page: int = Field(1, ge=1, description="页码，从1开始")
    size: int = Field(10, ge=1, le=200, description="每页数量")


# 响应模式
class SchedulerTaskResponse(BaseModel):
    """定时任务响应"""
    id: int
    name: str
    type: int
    status: int
    script: Optional[Dict[str, Any]]
    time: Optional[Dict[str, Any]]
    notice: Optional[Dict[str, Any]]
    description: Optional[str]
    scheduler_job_id: Optional[str]
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    total_run_count: int
    creation_date: datetime
    
    class Config:
        from_attributes = True


class MsgNoticeResponse(BaseModel):
    """消息通知响应"""
    id: int
    name: str
    type: int
    value: str
    status: int
    script: Optional[Dict[str, Any]]
    description: Optional[str]
    creation_date: datetime
    
    class Config:
        from_attributes = True


class TaskExecutionHistoryResponse(BaseModel):
    """任务执行历史响应"""
    id: int
    task_id: int
    execution_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[int]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    trigger_type: Optional[str]
    
    class Config:
        from_attributes = True


class TaskScheduleResponse(BaseModel):
    """任务调度响应"""
    task_id: int
    scheduler_job_id: str
    status: str
    message: str
    next_run_time: Optional[datetime]