"""
接口自动化模块 - 数据验证模式
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime




class ApiProjectRequest(BaseModel):
    """获取项目列表 - 无必填参数，body 可为空"""
    page: Optional[int] = Field(None, description="页码")
    pageSize: Optional[int] = Field(None, description="每页条数")


class ApiServiceRequest(BaseModel):
    """获取服务列表"""
    project_id: Optional[int] = Field(None, description="项目ID，不传则返回全部")

class AddApiProjectRequest(BaseModel):
    """新增项目"""
    name: str = Field(..., description="项目名称")
    img: Optional[str] = Field(None, description="项目图标")
    description: Optional[str] = Field(None, description="项目描述")


class EditApiProjectRequest(BaseModel):
    """编辑项目"""
    id: int = Field(..., description="项目ID")
    name: Optional[str] = Field(None, description="项目名称")
    img: Optional[str] = Field(None, description="项目图标")
    description: Optional[str] = Field(None, description="项目描述")


class DelApiProjectRequest(BaseModel):
    """删除项目"""
    id: int = Field(..., description="项目ID")


class AddApiServiceRequest(BaseModel):
    """新增服务"""
    name: str = Field(..., description="服务名称")
    api_project_id: int = Field(..., description="所属项目ID")
    img: Optional[str] = Field(None, description="服务图标")
    description: Optional[str] = Field(None, description="服务描述")


class EditApiServiceRequest(BaseModel):
    """编辑服务"""
    id: int = Field(..., description="服务ID")
    name: Optional[str] = Field(None, description="服务名称")
    api_project_id: Optional[int] = Field(None, description="所属项目ID")
    img: Optional[str] = Field(None, description="服务图标")
    description: Optional[str] = Field(None, description="服务描述")


class DelApiServiceRequest(BaseModel):
    """删除服务"""
    id: int = Field(..., description="服务ID")


class ApiTreeRequest(BaseModel):
    """获取接口菜单树 - search 与 service get_api_tree(search) 一致"""
    search: Optional[Dict[str, Any]] = Field(None, description="查询条件：api_service_id, name 等")


class AddMenuRequest(BaseModel):
    """新增菜单/目录"""
    name: str = Field(..., description="菜单名称")
    pid: int = Field(..., description="父节点ID，根为 0")
    type: int = Field(..., description="类型：1=目录 2=用例等")
    api_service_id: int = Field(..., description="所属服务ID")


class EditMenuRequest(BaseModel):
    """编辑菜单"""
    id: int = Field(..., description="菜单ID")
    name: str = Field(..., description="新名称")


class DelMenuRequest(BaseModel):
    """删除菜单"""
    id: int = Field(..., description="菜单ID")
    type: Optional[int] = Field(None, description="菜单类型，用于级联删 API")


class CopyMenuRequest(BaseModel):
    """复制菜单及关联接口"""
    id: int = Field(..., description="源菜单ID")
    api_id: int = Field(..., description="源接口ID")


class ApiInfoRequest(BaseModel):
    """获取接口详情"""
    api_id: int = Field(..., description="接口ID")


class SaveApiRequest(BaseModel):
    """保存接口（编辑） - 与 service save_api 入参一致"""
    id: int = Field(..., description="接口ID")
    url: Optional[str] = Field(None, description="请求 URL")
    req: Optional[Dict[str, Any]] = Field(None, description="完整请求配置(header/params/body/before/after/assert 等)")


class ApiSendRequest(BaseModel):
    """发送单接口请求 - 与 service execute_api_send 入参一致"""
    id: Optional[int] = Field(None, description="接口ID，可选")
    env_id: Optional[int] = Field(None, description="环境ID")
    url: Optional[str] = Field(None, description="请求 URL（可含变量）")
    req: Optional[Dict[str, Any]] = Field(None, description="请求配置(header/params/body/before/after/assert 等)")


class ReqHistoryRequest(BaseModel):
    """请求历史 - 无必填参数"""
    pass


class EditHistoryRequest(BaseModel):
    """接口编辑历史"""
    api_id: int = Field(..., description="接口ID")


# ---------- 环境 ----------
class EnvInfoRequest(BaseModel):
    """获取环境详情"""
    id: int = Field(..., description="环境ID")


class SaveEnvRequest(BaseModel):
    """批量保存环境"""
    env_list: List[Dict[str, Any]] = Field(default_factory=list, description="环境列表，每项含 id/name/config/variable")


class AddEnvRequest(BaseModel):
    """新增环境"""
    name: str = Field(..., description="环境名称")
    config: Optional[List[Dict[str, Any]]] = Field(None, description="环境配置项")
    variable: Optional[List[Dict[str, Any]]] = Field(None, description="环境变量")


class DelEnvRequest(BaseModel):
    """删除环境"""
    id: int = Field(..., description="环境ID")


# ---------- 全局变量 ----------
class AddVarRequest(BaseModel):
    """新增全局变量"""
    name: str = Field(..., description="变量名")
    value: str = Field(..., description="变量值")


class EditVarRequest(BaseModel):
    """编辑全局变量"""
    id: int = Field(..., description="变量ID")
    name: str = Field(..., description="变量名")
    value: str = Field(..., description="变量值")


class DelVarRequest(BaseModel):
    """删除全局变量"""
    id: int = Field(..., description="变量ID")


# ---------- 数据库配置 ----------
class AddApiDbRequest(BaseModel):
    """新增数据库配置"""
    name: str = Field(..., description="配置名称")
    config: Optional[Dict[str, Any]] = Field(None, description="连接配置 host/user/password/database/port 等")


class EditApiDbRequest(BaseModel):
    """编辑数据库配置"""
    id: int = Field(..., description="配置ID")
    name: Optional[str] = Field(None, description="配置名称")
    config: Optional[Dict[str, Any]] = Field(None, description="连接配置")


class DelApiDbRequest(BaseModel):
    """删除数据库配置"""
    id: int = Field(..., description="配置ID")


# ---------- 场景脚本 ----------
class ApiScriptListRequest(BaseModel):
    """场景列表分页"""
    page: Optional[int] = Field(1, description="页码")
    pageSize: Optional[int] = Field(1000, description="每页条数")


class ApiScriptRequest(BaseModel):
    """场景列表请求 - 与 get_api_script_list 一致"""
    page: Optional[int] = Field(1, description="页码")
    pageSize: Optional[int] = Field(1000, description="每页条数")


class AddApiScriptRequest(BaseModel):
    """新增场景脚本"""
    name: str = Field(..., description="场景名称")
    type: Optional[int] = Field(1, description="类型")
    script: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="步骤列表")
    config: Optional[Dict[str, Any]] = Field(None, description="场景配置")
    description: Optional[str] = Field("", description="描述")


class EditApiScriptRequest(BaseModel):
    """编辑场景脚本"""
    id: int = Field(..., description="场景ID")
    name: Optional[str] = Field(None, description="场景名称")
    type: Optional[int] = Field(None, description="类型")
    script: Optional[List[Dict[str, Any]]] = Field(None, description="步骤列表")
    config: Optional[Dict[str, Any]] = Field(None, description="场景配置")
    description: Optional[str] = Field(None, description="描述")


class DelApiScriptRequest(BaseModel):
    """删除场景脚本"""
    id: int = Field(..., description="场景ID")


class RunApiScriptRequest(BaseModel):
    """执行场景 - 与 service run_api_script 入参一致"""
    result_id: str = Field(..., description="本次执行批次ID（如 UUID）")
    name: str = Field(..., description="任务名称")
    config: Dict[str, Any] = Field(default_factory=dict, description="执行配置，含 env_id 等")
    run_list: List[Dict[str, Any]] = Field(default_factory=list, description="用例列表，每项含 script/config 等")


class ApiScriptResultRequest(BaseModel):
    """获取场景执行结果"""
    result_id: int = Field(..., description="执行批次ID")


class ApiScriptResultListRequest(BaseModel):
    """执行结果汇总列表分页"""
    page: Optional[int] = Field(1, description="页码")
    pageSize: Optional[int] = Field(1000, description="每页条数")


class ApiScriptResultDetailRequest(BaseModel):
    """执行结果详情（按批次）"""
    result_id: int = Field(..., description="执行批次ID")


class ApiScriptResultDetailListRequest(BaseModel):
    """执行结果详情列表（按菜单/用例）"""
    result_id: int = Field(..., description="执行批次ID")
    menu_id: str = Field(..., description="用例/菜单 UUID")


class ApiScriptLogRequest(BaseModel):
    """脚本执行日志（整体）"""
    result_id: str = Field(..., description="执行ID")


class ApiScriptReportLogRequest(BaseModel):
    """脚本执行日志（按菜单）"""
    result_id: str = Field(..., description="执行ID")
    menu_id: str = Field(..., description="菜单/用例 UUID")




class ApiProjectResponse(BaseModel):
    """API 项目"""
    id: int
    name: str
    img: Optional[str] = None
    description: Optional[str] = None
    creation_date: datetime

    class Config:
        from_attributes = True


class ApiServiceResponse(BaseModel):
    """API 服务"""
    id: int
    name: str
    api_project_id: int
    img: Optional[str] = None
    description: Optional[str] = None
    creation_date: datetime

    class Config:
        from_attributes = True


class ApiResponse(BaseModel):
    """API 接口"""
    id: int
    name: Optional[str] = None
    url: str
    req: Optional[Dict[str, Any]] = None
    document: Optional[Dict[str, Any]] = None
    api_service_id: int
    creation_date: datetime

    class Config:
        from_attributes = True


class ApiEnvironmentResponse(BaseModel):
    """API 环境"""
    id: int
    name: str
    config: Optional[List[Dict[str, Any]]] = None
    variable: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None
    creation_date: datetime

    class Config:
        from_attributes = True


class ApiScriptResponse(BaseModel):
    """API 场景"""
    id: int
    name: str
    type: int
    script: List[Dict[str, Any]]
    config: Optional[Dict[str, Any]] = None
    description: str = ""
    creation_date: datetime

    class Config:
        from_attributes = True


class ApiExecutionResponse(BaseModel):
    """单接口执行结果"""
    status_code: int
    response_time: float
    response_data: Dict[str, Any]
    request_data: Dict[str, Any]
    assertions_passed: bool
    error_message: Optional[str] = None


# ---------- 参数依赖 ----------
class ApiParamsListRequest(BaseModel):
    """参数依赖列表"""
    pass


class AddApiParamsRequest(BaseModel):
    """新增参数依赖"""
    name: str = Field(..., description="参数名称")
    value: Dict[str, Any] = Field(default_factory=dict, description="参数值(JSON对象)")


class EditApiParamsRequest(BaseModel):
    """编辑参数依赖"""
    id: int = Field(..., description="参数ID")
    name: Optional[str] = Field(None, description="参数名称")
    value: Optional[Dict[str, Any]] = Field(None, description="参数值(JSON对象)")


class DelApiParamsRequest(BaseModel):
    """删除参数依赖"""
    id: int = Field(..., description="参数ID")


# ---------- 公共函数 ----------
class ApiFunctionListRequest(BaseModel):
    """公共函数列表"""
    pass


class AddApiFunctionRequest(BaseModel):
    """新增公共函数"""
    name: str = Field(..., description="函数名称")
    description: Optional[str] = Field(None, description="函数描述")


class EditApiFunctionRequest(BaseModel):
    """编辑公共函数"""
    id: int = Field(..., description="函数ID")
    name: Optional[str] = Field(None, description="函数名称")
    description: Optional[str] = Field(None, description="函数描述")


class DelApiFunctionRequest(BaseModel):
    """删除公共函数"""
    id: int = Field(..., description="函数ID")


# ---------- 文档同步变更 ----------
class ApiUpdateListRequest(BaseModel):
    """同步变更列表"""
    api_service_id: Optional[int] = Field(None, description="服务ID，不传返回全部")
