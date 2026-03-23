"""
Web管理模块 - 数据验证模式
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


# 请求模式
class WebMenuRequest(BaseModel):
    """Web菜单请求"""
    id: int = Field(..., description="菜单ID（父级ID）")


class WebScriptRequest(BaseModel):
    """Web脚本请求"""
    id: int = Field(..., description="菜单ID")


class SaveWebScriptRequest(BaseModel):
    """保存Web脚本请求"""
    id: int = Field(..., description="菜单ID")
    script: List[Dict[str, Any]] = Field(..., description="脚本步骤")


class RunWebScriptRequest(BaseModel):
    """执行Web脚本请求"""
    result_id: str = Field(..., description="执行ID")
    script: List[Dict[str, Any]] = Field(..., description="脚本配置（选择的脚本菜单列表等）")
    browser: List[str] = Field(..., description="浏览器列表")
    browser_type: int = Field(2, description="浏览器运行模式：1有头/2无头（按旧逻辑）")
    width: Optional[int] = Field(None, description="浏览器宽度")
    height: Optional[int] = Field(None, description="浏览器高度")
    task_name: Optional[str] = Field(None, description="任务名称")


class ImportElementsRequest(BaseModel):
    """导入元素请求"""
    elements: List[Dict[str, Any]] = Field(..., description="元素列表")


class WebResultRequest(BaseModel):
    """Web结果请求"""
    result_id: str = Field(..., description="执行ID")
    browser: Optional[int] = Field(None, description="浏览器类型（获取详情时需要）")


class WebResultListRequest(BaseModel):
    """Web结果列表请求"""
    page: int = Field(1, description="页码")
    pageSize: int = Field(10, description="每页条数")


class WebGroupListRequest(BaseModel):
    """Web脚本集列表请求"""
    # 旧接口无参数，保留空请求体但不使用 pass
    dummy: Optional[int] = Field(None, description="占位字段（可不传）")


class CreateWebGroupRequest(BaseModel):
    """创建Web脚本集请求"""
    name: str = Field(..., description="脚本集名称")
    script: List[Dict[str, Any]] = Field(..., description="脚本配置")
    description: Optional[str] = Field(None, description="脚本集描述")


# 响应模式
class WebMenuResponse(BaseModel):
    """Web菜单响应"""
    id: int
    name: str
    pid: int
    type: int
    creation_date: datetime
    
    class Config:
        from_attributes = True


class WebScriptResponse(BaseModel):
    """Web脚本响应"""
    id: int
    script: List[Dict[str, Any]]
    menu_id: int
    creation_date: datetime
    
    class Config:
        from_attributes = True


class WebElementResponse(BaseModel):
    """Web元素响应"""
    id: int
    name: str
    element: Dict[str, Any]
    menu_id: Optional[int]
    element_type: Optional[str]
    locator_strategy: Optional[str]
    locator_value: Optional[str]
    creation_date: datetime
    
    class Config:
        from_attributes = True


class WebGroupResponse(BaseModel):
    """Web脚本集响应"""
    id: int
    name: str
    script: Optional[List[Dict[str, Any]]]
    description: Optional[str]
    creation_date: datetime
    
    class Config:
        from_attributes = True


class WebResultListResponse(BaseModel):
    """Web结果列表响应"""
    id: int
    task_name: str
    result_id: str
    script_list: List[Dict[str, Any]]
    browser_list: List[Dict[str, Any]]
    result: Dict[str, Any]
    start_time: datetime
    end_time: Optional[datetime]
    status: int
    
    class Config:
        from_attributes = True


class WebExecutionResponse(BaseModel):
    """Web执行响应"""
    result_id: str
    status: str
    message: str
    start_time: datetime