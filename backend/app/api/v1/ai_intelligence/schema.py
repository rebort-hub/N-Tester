# -*- coding: utf-8 -*-
"""
AI智能化模块数据模式
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.base import BaseSchema


# ==================== 需求文档管理 ====================

class RequirementDocumentCreateSchema(BaseSchema):
    """需求文档创建模式"""
    project_id: int = Field(..., description="关联项目ID")
    title: str = Field(..., max_length=200, description="文档标题")
    document_type: str = Field(..., description="文档类型: pdf/docx/txt/md")


class RequirementDocumentUpdateSchema(BaseSchema):
    """需求文档更新模式"""
    title: Optional[str] = Field(None, max_length=200, description="文档标题")
    status: Optional[str] = Field(None, description="状态")
    extracted_text: Optional[str] = Field(None, description="提取的文本内容")


class RequirementDocumentOutSchema(BaseModel):
    """需求文档输出模式"""
    model_config = ConfigDict(from_attributes=True)
    
    project_id: int
    title: str
    file_path: str
    document_type: str
    status: str
    file_size: Optional[int]
    extracted_text: Optional[str]
    uploaded_by: int
    has_analysis: bool = Field(default=False, description="是否已分析")


# ==================== 需求分析 ====================

class RequirementAnalysisCreateSchema(BaseSchema):
    """需求分析创建模式"""
    document_id: int = Field(..., description="关联文档ID")
    analysis_report: Optional[str] = Field(None, description="分析报告")
    requirements_count: int = Field(default=0, description="需求数量")
    analysis_time: Optional[float] = Field(None, description="分析耗时(秒)")


class RequirementAnalysisOutSchema(BaseModel):
    """需求分析输出模式"""
    model_config = ConfigDict(from_attributes=True)
    
    document_id: int
    analysis_report: Optional[str]
    requirements_count: int
    analysis_time: Optional[float]


# ==================== 业务需求 ====================

class BusinessRequirementCreateSchema(BaseSchema):
    """业务需求创建模式"""
    analysis_id: int = Field(..., description="关联分析ID")
    requirement_id: str = Field(..., max_length=50, description="需求编号")
    requirement_name: str = Field(..., max_length=200, description="需求名称")
    requirement_type: str = Field(..., description="需求类型")
    parent_requirement_id: Optional[int] = Field(None, description="父级需求ID")
    module: str = Field(..., max_length=100, description="所属模块")
    requirement_level: str = Field(..., description="需求级别")
    reviewer: str = Field(default="admin", description="评审人")
    estimated_hours: int = Field(default=8, description="预计工时")
    description: str = Field(..., description="需求描述")
    acceptance_criteria: str = Field(..., description="验收标准")


class BusinessRequirementOutSchema(BaseModel):
    """业务需求输出模式"""
    model_config = ConfigDict(from_attributes=True)
    
    analysis_id: int
    requirement_id: str
    requirement_name: str
    requirement_type: str
    parent_requirement_id: Optional[int]
    module: str
    requirement_level: str
    reviewer: str
    estimated_hours: int
    description: str
    acceptance_criteria: str


# ==================== AI模型配置 ====================

class AIModelConfigCreateSchema(BaseSchema):
    """AI模型配置创建模式"""
    name: str = Field(..., max_length=100, description="配置名称")
    model_type: str = Field(..., description="模型类型: deepseek/qwen/siliconflow/zhipu/other")
    role: str = Field(..., description="角色: writer/reviewer/browser_use_text")
    api_key: Optional[str] = Field(None, max_length=200, description="API Key（如果提供llm_config_id则可选）")
    base_url: Optional[str] = Field(None, max_length=500, description="API Base URL（如果提供llm_config_id则可选）")
    model_name: Optional[str] = Field(None, max_length=100, description="模型名称（如果提供llm_config_id则可选）")
    max_tokens: Optional[int] = Field(None, description="最大Token数")
    temperature: Optional[float] = Field(None, description="温度参数")
    top_p: Optional[float] = Field(None, description="Top P参数")
    is_active: bool = Field(default=True, description="是否启用")
    llm_config_id: Optional[int] = Field(None, description="关联的LLM配置ID")


class AIModelConfigUpdateSchema(BaseSchema):
    """AI模型配置更新模式"""
    name: Optional[str] = Field(None, max_length=100, description="配置名称")
    api_key: Optional[str] = Field(None, max_length=200, description="API Key")
    base_url: Optional[str] = Field(None, max_length=500, description="API Base URL")
    model_name: Optional[str] = Field(None, max_length=100, description="模型名称")
    max_tokens: Optional[int] = Field(None, description="最大Token数")
    temperature: Optional[float] = Field(None, description="温度参数")
    top_p: Optional[float] = Field(None, description="Top P参数")
    is_active: Optional[bool] = Field(None, description="是否启用")
    llm_config_id: Optional[int] = Field(None, description="关联的LLM配置ID")


class AIModelConfigOutSchema(BaseModel):
    """AI模型配置输出模式"""
    model_config = ConfigDict(from_attributes=True)
    
    name: str
    model_type: str
    role: str
    api_key: Optional[str] = Field(None, description="API Key（脱敏）")
    base_url: str
    model_name: str
    max_tokens: int
    temperature: float
    top_p: float
    is_active: bool
    created_by: int


# ==================== 提示词配置 ====================

class PromptConfigCreateSchema(BaseSchema):
    """提示词配置创建模式"""
    name: str = Field(..., max_length=100, description="配置名称")
    prompt_type: str = Field(..., description="提示词类型: writer/reviewer")
    content: str = Field(..., description="提示词内容")
    is_active: bool = Field(default=True, description="是否启用")


class PromptConfigUpdateSchema(BaseSchema):
    """提示词配置更新模式"""
    name: Optional[str] = Field(None, max_length=100, description="配置名称")
    content: Optional[str] = Field(None, description="提示词内容")
    is_active: Optional[bool] = Field(None, description="是否启用")


class PromptConfigOutSchema(BaseModel):
    """提示词配置输出模式"""
    model_config = ConfigDict(from_attributes=True)
    
    name: str
    prompt_type: str
    content: str
    is_active: bool
    created_by: int


# ==================== 生成行为配置 ====================

class GenerationConfigCreateSchema(BaseSchema):
    """生成行为配置创建模式"""
    name: str = Field(default="默认生成配置", description="配置名称")
    default_output_mode: str = Field(default="stream", description="默认输出模式")
    enable_auto_review: bool = Field(default=True, description="启用AI评审和改进")
    review_timeout: int = Field(default=120, description="评审和改进超时时间（秒）")
    is_active: bool = Field(default=True, description="是否启用")


class GenerationConfigUpdateSchema(BaseSchema):
    """生成行为配置更新模式"""
    name: Optional[str] = Field(None, description="配置名称")
    default_output_mode: Optional[str] = Field(None, description="默认输出模式")
    enable_auto_review: Optional[bool] = Field(None, description="启用AI评审和改进")
    review_timeout: Optional[int] = Field(None, description="评审和改进超时时间（秒）")
    is_active: Optional[bool] = Field(None, description="是否启用")


class GenerationConfigOutSchema(BaseModel):
    """生成行为配置输出模式"""
    model_config = ConfigDict(from_attributes=True)
    
    name: str
    default_output_mode: str
    enable_auto_review: bool
    review_timeout: int
    is_active: bool


# ==================== 测试用例生成任务 ====================

class TestCaseGenerationTaskCreateSchema(BaseSchema):
    """测试用例生成任务创建模式"""
    project_id: Optional[int] = Field(None, description="关联项目ID")
    title: str = Field(..., max_length=200, description="任务标题")
    requirement_text: str = Field(..., description="需求描述")
    output_mode: str = Field(default="stream", description="输出模式: stream/complete")
    writer_model_config_id: Optional[int] = Field(None, description="编写模型配置ID")
    reviewer_model_config_id: Optional[int] = Field(None, description="评审模型配置ID")
    writer_prompt_config_id: Optional[int] = Field(None, description="编写提示词配置ID")
    reviewer_prompt_config_id: Optional[int] = Field(None, description="评审提示词配置ID")


class TestCaseGenerationTaskUpdateSchema(BaseSchema):
    """测试用例生成任务更新模式"""
    status: Optional[str] = Field(None, description="状态")
    progress: Optional[int] = Field(None, description="进度百分比")
    stream_buffer: Optional[str] = Field(None, description="流式输出缓冲区")
    stream_position: Optional[int] = Field(None, description="流式输出位置")
    last_stream_update: Optional[datetime] = Field(None, description="最后流式更新时间")
    generated_test_cases: Optional[str] = Field(None, description="生成的测试用例")
    review_feedback: Optional[str] = Field(None, description="评审反馈")
    final_test_cases: Optional[str] = Field(None, description="最终测试用例")
    generation_log: Optional[str] = Field(None, description="生成日志")
    error_message: Optional[str] = Field(None, description="错误信息")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    is_saved_to_records: Optional[bool] = Field(None, description="是否已保存到记录")
    saved_at: Optional[datetime] = Field(None, description="保存到记录时间")


class TestCaseGenerationTaskOutSchema(BaseModel):
    """测试用例生成任务输出模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: Optional[int]
    task_id: str
    title: str
    requirement_text: str
    status: str
    progress: int
    output_mode: str
    stream_buffer: Optional[str]
    stream_position: int
    last_stream_update: Optional[datetime]
    writer_model_config_id: Optional[int]
    reviewer_model_config_id: Optional[int]
    writer_prompt_config_id: Optional[int]
    reviewer_prompt_config_id: Optional[int]
    generated_test_cases: Optional[str]
    review_feedback: Optional[str]
    final_test_cases: Optional[str]
    generation_log: Optional[str]
    error_message: Optional[str]
    created_by: int
    creation_date: Optional[datetime]
    completed_at: Optional[datetime]
    is_saved_to_records: bool
    saved_at: Optional[datetime]


# ==================== AI智能浏览器用例 ====================

class AICaseCreateSchema(BaseSchema):
    """AI用例创建模式"""
    ui_project_id: Optional[int] = Field(None, description="所属UI项目ID")
    source_project_id: Optional[int] = Field(None, description="来源项目ID")
    source_module_id: Optional[int] = Field(None, description="来源模块ID")
    name: str = Field(..., max_length=200, description="用例名称")
    description: Optional[str] = Field(None, description="描述")
    task_description: str = Field(..., description="任务描述")
    status: Optional[str] = Field('active', description="状态: draft/active/archived")
    source_type: Optional[str] = Field('manual', description="来源类型: manual/import/testcase")
    priority: Optional[str] = Field('P2', description="优先级: P0/P1/P2/P3")
    precondition: Optional[str] = Field(None, description="前置条件")
    test_steps: Optional[list] = Field(None, description="测试步骤")
    expected_result: Optional[str] = Field(None, description="预期结果")
    execution_mode: Optional[str] = Field('headless', description="执行模式: headless/headed")
    timeout: Optional[int] = Field(300, description="超时时间(秒)")


class AICaseUpdateSchema(BaseSchema):
    """AI用例更新模式"""
    name: Optional[str] = Field(None, max_length=200, description="用例名称")
    description: Optional[str] = Field(None, description="描述")
    task_description: Optional[str] = Field(None, description="任务描述")
    status: Optional[str] = Field(None, description="状态: draft/active/archived")
    source_type: Optional[str] = Field(None, description="来源类型: manual/import/testcase")
    priority: Optional[str] = Field(None, description="优先级: P0/P1/P2/P3")
    precondition: Optional[str] = Field(None, description="前置条件")
    test_steps: Optional[list] = Field(None, description="测试步骤")
    expected_result: Optional[str] = Field(None, description="预期结果")
    execution_mode: Optional[str] = Field(None, description="执行模式: headless/headed")
    timeout: Optional[int] = Field(None, description="超时时间(秒)")


class AICaseOutSchema(BaseModel):
    """AI用例输出模式"""
    model_config = ConfigDict(from_attributes=True)
    
    ui_project_id: Optional[int]
    name: str
    description: Optional[str]
    task_description: str
    created_by: Optional[int]


# ==================== AI执行记录 ====================

class AIExecutionRecordCreateSchema(BaseSchema):
    """AI执行记录创建模式"""
    ui_project_id: Optional[int] = Field(None, description="所属UI项目ID")
    ai_case_id: Optional[int] = Field(None, description="关联AI用例ID")
    case_name: str = Field(..., max_length=200, description="用例名称快照")
    task_description: Optional[str] = Field(None, description="任务描述")
    execution_mode: str = Field(default="text", description="执行模式")


class AIExecutionRecordUpdateSchema(BaseSchema):
    """AI执行记录更新模式"""
    status: Optional[str] = Field(None, description="执行状态")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration: Optional[float] = Field(None, description="执行时长(秒)")
    logs: Optional[str] = Field(None, description="执行日志")
    error_message: Optional[str] = Field(None, description="错误信息")
    steps_completed: Optional[Dict[str, Any]] = Field(None, description="已完成步骤")
    planned_tasks: Optional[Dict[str, Any]] = Field(None, description="规划任务")
    gif_path: Optional[str] = Field(None, description="GIF录制路径")
    screenshots_sequence: Optional[Dict[str, Any]] = Field(None, description="截图序列")


class AIExecutionRecordOutSchema(BaseModel):
    """AI执行记录输出模式"""
    model_config = ConfigDict(from_attributes=True)
    
    ui_project_id: Optional[int]
    ai_case_id: Optional[int]
    case_name: str
    task_description: Optional[str]
    execution_mode: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[float]
    logs: Optional[str]
    error_message: Optional[str]
    steps_completed: Optional[Dict[str, Any]]
    planned_tasks: Optional[Dict[str, Any]]
    executed_by: Optional[int]
    gif_path: Optional[str]
    screenshots_sequence: Optional[Dict[str, Any]]


# ==================== 流式输出相关 ====================

class StreamChunkSchema(BaseModel):
    """流式输出块模式"""
    task_id: str = Field(..., description="任务ID")
    chunk: str = Field(..., description="输出块内容")
    position: int = Field(..., description="当前位置")
    is_complete: bool = Field(default=False, description="是否完成")


class TaskStatusSchema(BaseModel):
    """任务状态模式"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    progress: int = Field(..., description="进度百分比")
    error_message: Optional[str] = Field(None, description="错误信息")



# ==================== 测试用例模板 ====================

class TestCaseTemplateCreateSchema(BaseSchema):
    """测试用例模板创建模式"""
    name: str = Field(..., max_length=100, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    template_type: str = Field('ui', description="模板类型: ui/api/performance")
    field_mapping: dict = Field(..., description="字段映射配置")
    is_default: bool = Field(False, description="是否默认模板")
    is_active: bool = Field(True, description="是否启用")


class TestCaseTemplateUpdateSchema(BaseSchema):
    """测试用例模板更新模式"""
    name: Optional[str] = Field(None, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    field_mapping: Optional[dict] = Field(None, description="字段映射配置")
    is_default: Optional[bool] = Field(None, description="是否默认模板")
    is_active: Optional[bool] = Field(None, description="是否启用")


class TestCaseTemplateOutSchema(BaseModel):
    """测试用例模板输出模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    template_type: str
    field_mapping: dict
    is_default: bool
    is_active: bool
    created_by: int
    creation_date: Optional[datetime]


class SaveToTestCaseSchema(BaseSchema):
    """保存到测试用例模式"""
    task_id: str = Field(..., description="生成任务ID")
    save_type: str = Field('main', description="保存类型: main(主项目)/sub(子项目)")
    project_id: int = Field(..., description="主项目ID")
    module_id: Optional[int] = Field(None, description="模块ID (save_type=main时可选)")
    sub_project_type: Optional[str] = Field(None, description="子项目类型: ui/api/performance (save_type=sub时必填)")
    sub_project_id: Optional[int] = Field(None, description="子项目ID (save_type=sub时必填)")
    template_id: Optional[int] = Field(None, description="模板ID，不传则使用默认模板")
    override_fields: Optional[dict] = Field(None, description="覆盖字段")



# ==================== Figma配置 ====================

class FigmaConfigCreateSchema(BaseSchema):
    """Figma配置创建模式"""
    project_id: int = Field(..., description="关联项目ID")
    access_token: Optional[str] = Field(None, max_length=500, description="Figma Access Token（公开文件可选）")
    file_key: str = Field(..., max_length=100, description="Figma文件ID")
    file_name: Optional[str] = Field(None, max_length=200, description="文件名称")
    file_url: Optional[str] = Field(None, description="Figma文件URL")


class FigmaConfigUpdateSchema(BaseSchema):
    """Figma配置更新模式"""
    access_token: Optional[str] = Field(None, max_length=500, description="Figma Access Token")
    file_key: Optional[str] = Field(None, max_length=100, description="Figma文件ID")
    file_name: Optional[str] = Field(None, max_length=200, description="文件名称")
    file_url: Optional[str] = Field(None, description="Figma文件URL")


class FigmaConfigOutSchema(BaseModel):
    """Figma配置输出模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    file_key: str
    file_name: Optional[str]
    file_url: Optional[str]
    last_sync_time: Optional[datetime]
    creation_date: Optional[datetime]


# ==================== Figma提取任务 ====================

class FigmaExtractionTaskCreateSchema(BaseSchema):
    """Figma提取任务创建模式"""
    config_id: int = Field(..., description="Figma配置ID")
    extraction_mode: str = Field(default="simple", description="提取模式: simple/complete")


class FigmaExtractionTaskUpdateSchema(BaseSchema):
    """Figma提取任务更新模式"""
    status: Optional[str] = Field(None, description="状态")
    progress: Optional[int] = Field(None, description="进度百分比")
    current_step: Optional[str] = Field(None, description="当前步骤")
    total_frames: Optional[int] = Field(None, description="总Frame数")
    processed_frames: Optional[int] = Field(None, description="已处理Frame数")
    error_message: Optional[str] = Field(None, description="错误信息")
    result_document_id: Optional[int] = Field(None, description="结果文档ID")
    end_time: Optional[datetime] = Field(None, description="结束时间")


class FigmaExtractionTaskOutSchema(BaseModel):
    """Figma提取任务输出模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    task_id: str
    config_id: int
    extraction_mode: str
    status: str
    progress: int
    current_step: Optional[str]
    total_frames: int
    processed_frames: int
    error_message: Optional[str]
    result_document_id: Optional[int]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    creation_date: Optional[datetime]




# ==================== AI测试套件管理 ====================

class AITestSuiteModuleSchema(BaseModel):
    """测试套件模块Schema"""
    module_id: int = Field(..., description="模块ID")
    module_name: Optional[str] = Field(None, description="模块名称")
    execution_order: int = Field(..., description="执行顺序")


class AITestSuiteCreateSchema(BaseSchema):
    """AI测试套件创建Schema"""
    name: str = Field(..., max_length=200, description="套件名称")
    description: Optional[str] = Field(None, description="套件描述")
    project_id: int = Field(..., description="关联项目ID")
    modules: List[AITestSuiteModuleSchema] = Field(..., description="关联的模块列表")


class AITestSuiteUpdateSchema(BaseSchema):
    """AI测试套件更新Schema"""
    name: Optional[str] = Field(None, max_length=200, description="套件名称")
    description: Optional[str] = Field(None, description="套件描述")
    status: Optional[str] = Field(None, description="状态")
    modules: Optional[List[AITestSuiteModuleSchema]] = Field(None, description="关联的模块列表")


class AITestSuiteOutSchema(BaseModel):
    """AI测试套件输出Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    project_id: int
    status: str
    module_count: int = Field(default=0, description="模块数量")
    case_count: int = Field(default=0, description="用例数量")
    created_by: Optional[int]
    creation_date: Optional[datetime]
    updated_by: Optional[int]
    updation_date: Optional[datetime]


class AITestSuiteDetailSchema(AITestSuiteOutSchema):
    """AI测试套件详情Schema"""
    modules: List[Dict[str, Any]] = Field(default_factory=list, description="模块列表")


class AITestSuiteExecutionCreateSchema(BaseSchema):
    """AI测试套件执行创建Schema"""
    suite_id: int = Field(..., description="套件ID")
    execution_name: Optional[str] = Field(None, description="执行名称")
    execution_mode: str = Field(default='headless', description="执行模式：headless/headed")


class AITestSuiteExecutionOutSchema(BaseModel):
    """AI测试套件执行记录输出Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    suite_id: int
    suite_name: Optional[str]
    execution_name: Optional[str]
    execution_mode: str
    status: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration: Optional[float]
    total_modules: int
    completed_modules: int
    failed_modules: int
    total_cases: int
    passed_cases: int
    failed_cases: int
    error_message: Optional[str]
    created_by: Optional[int]
    creation_date: Optional[datetime]


class AITestSuiteModuleExecutionOutSchema(BaseModel):
    """AI测试套件模块执行记录输出Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    suite_execution_id: int
    module_id: int
    module_name: Optional[str]
    execution_order: Optional[int]
    status: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration: Optional[float]
    total_cases: int
    passed_cases: int
    failed_cases: int
    error_message: Optional[str]
    creation_date: Optional[datetime]


# ==================== AI测试报告相关Schema ====================

class AITestReportCreateSchema(BaseModel):
    """AI测试报告创建Schema"""
    report_name: str
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    date_range: Optional[str] = None
    total_cases: int = 0
    total_executions: int = 0
    success_count: int = 0
    failed_count: int = 0
    success_rate: float = 0
    total_duration: float = 0
    avg_duration: float = 0
    total_tokens: int = 0
    report_data: Optional[dict] = None


class AITestReportOutSchema(BaseModel):
    """AI测试报告输出Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    report_id: str
    report_name: str
    project_id: Optional[int]
    project_name: Optional[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    date_range: Optional[str]
    status: str
    total_cases: int
    total_executions: int
    success_count: int
    failed_count: int
    success_rate: float
    total_duration: float
    avg_duration: float
    total_tokens: int
    report_data: Optional[dict]
    creation_date: Optional[datetime]
    created_by: Optional[int]
