"""
APP管理模块 - 数据验证模式
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


# 请求模式
class AppMenuRequest(BaseModel):
    """APP菜单请求"""
    pass


class AppScriptRequest(BaseModel):
    """APP脚本请求"""
    menu_id: int = Field(..., description="菜单ID")


class SaveAppScriptRequest(BaseModel):
    """保存APP脚本请求"""
    menu_id: int = Field(..., description="菜单ID")
    script: List[Dict[str, Any]] = Field(..., description="脚本步骤")


class RunAppScriptRequest(BaseModel):
    """执行APP脚本请求"""
    script_id: int = Field(..., description="脚本ID")
    device_list: List[str] = Field(..., description="设备列表")
    task_name: Optional[str] = Field(None, description="任务名称")


class RunScriptListRequest(BaseModel):
    """执行APP脚本集请求"""
    script_ids: List[int] = Field(..., description="脚本ID列表")
    device_list: List[str] = Field(..., description="设备列表")
    task_name: str = Field(..., description="任务名称")


class AddAppMenuRequest(BaseModel):
    """新增APP菜单请求"""
    name: str = Field(..., description="菜单名称")
    pid: int = Field(..., description="父菜单ID")
    type: int = Field(..., description="菜单类型")


class DeleteAppMenuRequest(BaseModel):
    """删除APP菜单请求"""
    menu_id: int = Field(..., description="菜单ID")


class RenameAppMenuRequest(BaseModel):
    """重命名APP菜单请求"""
    menu_id: int = Field(..., description="菜单ID")
    new_name: str = Field(..., description="新名称")


class AppResultRequest(BaseModel):
    """APP结果请求"""
    result_id: str = Field(..., description="执行批次ID")


class AppResultListRequest(BaseModel):
    """APP结果列表请求"""
    pass


class StopProcessRequest(BaseModel):
    """停止进程请求"""
    result_id: str = Field(..., description="执行批次ID")


class ProcessStatusRequest(BaseModel):
    """进程状态请求"""
    result_id: str = Field(..., description="执行批次ID")


# 响应模式
class AppMenuResponse(BaseModel):
    """APP菜单响应"""
    id: int
    name: str
    pid: int
    type: int
    creation_date: datetime
    
    class Config:
        from_attributes = True


class AppScriptResponse(BaseModel):
    """APP脚本响应"""
    id: int
    script: List[Dict[str, Any]]
    menu_id: int
    creation_date: datetime
    
    class Config:
        from_attributes = True


class AppResultResponse(BaseModel):
    """APP结果响应"""
    id: int
    device: str
    result_id: str
    name: str
    status: int
    log: Optional[str]
    assert_value: Optional[Dict[str, Any]]
    before_img: Optional[str]
    after_img: Optional[str]
    video: Optional[str]
    performance: Optional[Dict[str, Any]]
    menu_id: int
    creation_date: datetime
    
    class Config:
        from_attributes = True


class AppResultListResponse(BaseModel):
    """APP结果列表响应"""
    id: int
    task_name: str
    device_list: List[Dict[str, Any]]
    result_id: str
    script_list: List[Dict[str, Any]]
    script_status: List[Dict[str, Any]]
    start_time: datetime
    end_time: Optional[datetime]
    
    class Config:
        from_attributes = True


class AppExecutionResponse(BaseModel):
    """APP执行响应"""
    result_id: str
    pid_list: List[Dict[str, Any]]
    status: str
    message: str


class ProcessStatusResponse(BaseModel):
    """进程状态响应"""
    result_id: str
    processes: List[Dict[str, Any]]
    overall_status: str