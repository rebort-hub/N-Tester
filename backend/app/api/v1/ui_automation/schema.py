"""
UI自动化模块 - 数据模式
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.core.base_schema import TimestampSchema


# ==================== UI项目 ====================
class UIProjectCreateSchema(BaseModel):
    """UI项目创建"""
    project_id: int = Field(..., description='关联项目ID')
    name: str = Field(..., max_length=200, description='UI项目名称')
    description: Optional[str] = Field(None, description='项目描述')
    base_url: Optional[str] = Field(None, max_length=500, description='基础URL')
    browser_type: str = Field('chromium', description='浏览器类型: chromium/firefox/webkit')
    viewport_width: int = Field(1920, description='视口宽度')
    viewport_height: int = Field(1080, description='视口高度')
    timeout: int = Field(30000, description='默认超时时间(毫秒)')


class UIProjectUpdateSchema(BaseModel):
    """UI项目更新"""
    name: Optional[str] = Field(None, max_length=200, description='UI项目名称')
    description: Optional[str] = Field(None, description='项目描述')
    base_url: Optional[str] = Field(None, max_length=500, description='基础URL')
    browser_type: Optional[str] = Field(None, description='浏览器类型')
    viewport_width: Optional[int] = Field(None, description='视口宽度')
    viewport_height: Optional[int] = Field(None, description='视口高度')
    timeout: Optional[int] = Field(None, description='默认超时时间(毫秒)')


class UIProjectOutSchema(TimestampSchema):
    """UI项目输出"""
    id: int
    project_id: int
    name: str
    description: Optional[str] = None
    base_url: Optional[str] = None
    browser_type: str
    viewport_width: int
    viewport_height: int
    timeout: int
    creation_date: Optional[datetime] = None
    updation_date: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# ==================== UI元素分组 ====================
class UIElementGroupCreateSchema(BaseModel):
    """UI元素分组创建"""
    ui_project_id: int = Field(..., description='关联UI项目ID')
    name: str = Field(..., max_length=200, description='分组名称')
    description: Optional[str] = Field(None, description='分组描述')
    parent_id: Optional[int] = Field(None, description='父分组ID')
    order_num: int = Field(0, description='排序')


class UIElementGroupUpdateSchema(BaseModel):
    """UI元素分组更新"""
    name: Optional[str] = Field(None, max_length=200, description='分组名称')
    description: Optional[str] = Field(None, description='分组描述')
    parent_id: Optional[int] = Field(None, description='父分组ID')
    order_num: Optional[int] = Field(None, description='排序')


class UIElementGroupOutSchema(TimestampSchema):
    """UI元素分组输出"""
    id: int
    ui_project_id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    order_num: int
    children: Optional[List['UIElementGroupOutSchema']] = []


# ==================== UI元素 ====================
class UIElementCreateSchema(BaseModel):
    """UI元素创建"""
    group_id: int = Field(..., description='关联分组ID')
    name: str = Field(..., max_length=200, description='元素名称')
    description: Optional[str] = Field(None, description='元素描述')
    element_type: str = Field('button', description='元素类型')
    locator_strategy: str = Field(..., description='定位策略')
    locator_value: str = Field(..., description='定位器值')
    backup_locators: Optional[List[Dict[str, str]]] = Field(None, description='备用定位器列表')
    wait_time: int = Field(5000, description='等待时间(毫秒)')
    is_dynamic: bool = Field(False, description='是否动态元素')
    screenshot: Optional[str] = Field(None, description='元素截图路径')


class UIElementUpdateSchema(BaseModel):
    """UI元素更新"""
    name: Optional[str] = Field(None, max_length=200, description='元素名称')
    description: Optional[str] = Field(None, description='元素描述')
    element_type: Optional[str] = Field(None, description='元素类型')
    locator_strategy: Optional[str] = Field(None, description='定位策略')
    locator_value: Optional[str] = Field(None, description='定位器值')
    backup_locators: Optional[List[Dict[str, str]]] = Field(None, description='备用定位器列表')
    wait_time: Optional[int] = Field(None, description='等待时间(毫秒)')
    is_dynamic: Optional[bool] = Field(None, description='是否动态元素')
    screenshot: Optional[str] = Field(None, description='元素截图路径')


class UIElementOutSchema(TimestampSchema):
    """UI元素输出"""
    id: int
    group_id: int
    name: str
    description: Optional[str] = None
    element_type: str
    locator_strategy: str
    locator_value: str
    backup_locators: Optional[List[Dict[str, str]]] = None
    wait_time: int
    is_dynamic: bool
    screenshot: Optional[str] = None


# ==================== UI页面对象 ====================
class UIPageObjectCreateSchema(BaseModel):
    """UI页面对象创建"""
    ui_project_id: int = Field(..., description='关联UI项目ID')
    name: str = Field(..., max_length=200, description='页面对象名称')
    class_name: str = Field(..., max_length=200, description='类名')
    description: Optional[str] = Field(None, description='页面对象描述')
    url_pattern: Optional[str] = Field(None, description='URL模式')


class UIPageObjectUpdateSchema(BaseModel):
    """UI页面对象更新"""
    name: Optional[str] = Field(None, max_length=200, description='页面对象名称')
    class_name: Optional[str] = Field(None, max_length=200, description='类名')
    description: Optional[str] = Field(None, description='页面对象描述')
    url_pattern: Optional[str] = Field(None, description='URL模式')
    elements: Optional[List[Dict[str, Any]]] = Field(None, description='关联元素列表')


class UIPageObjectOutSchema(TimestampSchema):
    """UI页面对象输出"""
    id: int
    ui_project_id: int
    name: str
    class_name: str
    description: Optional[str] = None
    url_pattern: Optional[str] = None
    template_code: Optional[str] = None


# ==================== 页面对象元素关联 ====================
class UIPageObjectElementCreateSchema(BaseModel):
    """页面对象元素关联创建"""
    page_object_id: int = Field(..., description='关联页面对象ID')
    element_id: int = Field(..., description='关联元素ID')
    method_name: str = Field(..., max_length=200, description='方法名称')
    is_property: bool = Field(False, description='是否为属性')
    order_num: int = Field(0, description='排序')


class UIPageObjectElementOutSchema(BaseModel):
    """页面对象元素关联输出"""
    id: int
    page_object_id: int
    element_id: int
    method_name: str
    is_property: bool
    order_num: int
    creation_date: datetime


# ==================== 代码生成 ====================
class CodeGenerationSchema(BaseModel):
    """代码生成请求"""
    language: str = Field('javascript', description='编程语言: javascript/python')
    framework: str = Field('playwright', description='框架: playwright/selenium')
    include_comments: bool = Field(True, description='是否包含注释')


# ==================== UI测试用例 ====================
class UITestCaseCreateSchema(BaseModel):
    """UI测试用例创建"""
    ui_project_id: int = Field(..., description='关联UI项目ID')
    name: str = Field(..., max_length=200, description='用例名称')
    description: Optional[str] = Field(None, description='用例描述')
    priority: str = Field('medium', description='优先级: low/medium/high')
    tags: Optional[List[str]] = Field(None, description='标签列表')
    preconditions: Optional[str] = Field(None, description='前置条件')
    expected_result: Optional[str] = Field(None, description='预期结果')


class UITestCaseUpdateSchema(BaseModel):
    """UI测试用例更新"""
    name: Optional[str] = Field(None, max_length=200, description='用例名称')
    description: Optional[str] = Field(None, description='用例描述')
    priority: Optional[str] = Field(None, description='优先级')
    tags: Optional[List[str]] = Field(None, description='标签列表')
    preconditions: Optional[str] = Field(None, description='前置条件')
    expected_result: Optional[str] = Field(None, description='预期结果')


class UITestCaseOutSchema(TimestampSchema):
    """UI测试用例输出"""
    id: int
    ui_project_id: int
    name: str
    description: Optional[str] = None
    priority: str
    tags: Optional[List[str]] = None
    preconditions: Optional[str] = None
    expected_result: Optional[str] = None
    steps_count: Optional[int] = Field(None, description='步骤数量')


# ==================== UI测试步骤 ====================
class UITestStepCreateSchema(BaseModel):
    """UI测试步骤创建"""
    test_case_id: int = Field(..., description='关联测试用例ID')
    step_number: int = Field(..., description='步骤序号')
    action_type: str = Field(..., description='操作类型')
    element_id: Optional[int] = Field(None, description='关联元素ID')
    action_value: Optional[str] = Field(None, description='操作值')
    description: Optional[str] = Field(None, description='步骤描述')
    assertion_type: Optional[str] = Field(None, description='断言类型')
    assertion_value: Optional[str] = Field(None, description='断言值')
    screenshot_on_failure: bool = Field(True, description='失败时截图')
    continue_on_failure: bool = Field(False, description='失败时继续')


class UITestStepUpdateSchema(BaseModel):
    """UI测试步骤更新"""
    step_number: Optional[int] = Field(None, description='步骤序号')
    action_type: Optional[str] = Field(None, description='操作类型')
    element_id: Optional[int] = Field(None, description='关联元素ID')
    action_value: Optional[str] = Field(None, description='操作值')
    description: Optional[str] = Field(None, description='步骤描述')
    assertion_type: Optional[str] = Field(None, description='断言类型')
    assertion_value: Optional[str] = Field(None, description='断言值')
    screenshot_on_failure: Optional[bool] = Field(None, description='失败时截图')
    continue_on_failure: Optional[bool] = Field(None, description='失败时继续')


class UITestStepOutSchema(BaseModel):
    """UI测试步骤输出"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    test_case_id: int
    step_number: int
    action_type: str
    element_id: Optional[int] = None
    action_value: Optional[str] = None
    description: Optional[str] = None
    assertion_type: Optional[str] = None
    assertion_value: Optional[str] = None
    screenshot_on_failure: bool
    continue_on_failure: bool
    creation_date: datetime


class StepOrderSchema(BaseModel):
    """步骤顺序"""
    id: int = Field(..., description='步骤ID')
    step_number: int = Field(..., description='新的步骤序号')


class TestStepReorderSchema(BaseModel):
    """测试步骤重排序"""
    test_case_id: int = Field(..., description='测试用例ID')
    step_orders: List[StepOrderSchema] = Field(..., description='步骤顺序列表')


# ==================== UI测试套件 ====================
class UITestSuiteCreateSchema(BaseModel):
    """UI测试套件创建"""
    ui_project_id: int = Field(..., description='关联UI项目ID')
    name: str = Field(..., max_length=200, description='套件名称')
    description: Optional[str] = Field(None, description='套件描述')
    engine_type: str = Field('playwright', description='执行引擎')
    browser_type: str = Field('chromium', description='浏览器类型')
    headless: bool = Field(True, description='无头模式')
    parallel: bool = Field(False, description='并行执行')
    max_workers: int = Field(1, description='最大并行数')
    test_case_ids: Optional[List[int]] = Field(None, description='测试用例ID列表')


class UITestSuiteUpdateSchema(BaseModel):
    """UI测试套件更新"""
    name: Optional[str] = Field(None, max_length=200, description='套件名称')
    description: Optional[str] = Field(None, description='套件描述')
    engine_type: Optional[str] = Field(None, description='执行引擎')
    browser_type: Optional[str] = Field(None, description='浏览器类型')
    headless: Optional[bool] = Field(None, description='无头模式')
    parallel: Optional[bool] = Field(None, description='并行执行')
    max_workers: Optional[int] = Field(None, description='最大并行数')
    test_case_ids: Optional[List[int]] = Field(None, description='测试用例ID列表')


class UITestSuiteOutSchema(TimestampSchema):
    """UI测试套件输出"""
    id: int
    ui_project_id: int
    name: str
    description: Optional[str] = None
    engine_type: str
    browser_type: str
    headless: bool
    parallel: bool
    max_workers: int


# ==================== UI执行记录 ====================
class UIExecutionScreenshotSchema(BaseModel):
    """执行截图数据"""
    step_number: int
    step_description: str
    error_message: str
    screenshot: str  # Base64 encoded image
    timestamp: str


class UIExecutionOutSchema(BaseModel):
    """UI执行记录输出"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    ui_project_id: Optional[int] = None
    suite_id: Optional[int] = None
    test_case_id: Optional[int] = None
    engine_type: str
    browser_type: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    total_steps: int
    passed_steps: int
    failed_steps: int
    error_message: Optional[str] = None
    screenshots: Optional[List[UIExecutionScreenshotSchema]] = None
    video_path: Optional[str] = None
    logs: Optional[str] = None
    executed_by: Optional[int] = None
    creation_date: datetime


# ==================== 执行请求 ====================
class ExecutionRequestSchema(BaseModel):
    """执行请求"""
    engine_type: str = Field('playwright', description='执行引擎: playwright/selenium')
    browser_type: str = Field('chromium', description='浏览器类型: chromium/firefox/webkit')
    headless: bool = Field(True, description='无头模式')
    timeout: Optional[int] = Field(30000, description='超时时间(毫秒)')


class ExecutionStatusSchema(BaseModel):
    """执行状态"""
    id: int
    status: str = Field(..., description='状态: running/success/failed/stopped')
    progress: int = Field(..., description='进度: 0-100')
    current_step: Optional[str] = Field(None, description='当前步骤')
    start_time: datetime
    end_time: Optional[datetime] = None
    total_steps: int
    completed_steps: int
    failed_steps: int


class ExecutionListQuerySchema(BaseModel):
    """执行列表查询"""
    ui_project_id: Optional[int] = Field(None, description='UI项目ID')
    suite_id: Optional[int] = Field(None, description='测试套件ID')
    test_case_id: Optional[int] = Field(None, description='测试用例ID')
    status: Optional[str] = Field(None, description='执行状态')
    start_date: Optional[datetime] = Field(None, description='开始日期')
    end_date: Optional[datetime] = Field(None, description='结束日期')


class ExecutionStatisticsSchema(BaseModel):
    """执行统计"""
    total_executions: int = Field(..., description='总执行次数')
    success_count: int = Field(..., description='成功次数')
    failed_count: int = Field(..., description='失败次数')
    success_rate: float = Field(..., description='成功率')
    avg_duration: float = Field(..., description='平均执行时长(秒)')
    trend_data: List[Dict[str, Any]] = Field(default_factory=list, description='趋势数据')
