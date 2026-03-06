# -*- coding: utf-8 -*-
"""
AI智能化模块数据模型
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class RequirementDocumentModel(Base):
    """需求文档模型"""
    __tablename__ = 'requirement_documents'
    
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='关联项目ID')
    title = Column(String(200), nullable=False, comment='文档标题')
    file_path = Column(String(500), nullable=False, comment='文档文件路径')
    document_type = Column(String(10), nullable=False, comment='文档类型: pdf/docx/txt/md')
    status = Column(String(20), default='uploaded', comment='状态: uploaded/analyzing/analyzed/failed')
    file_size = Column(Integer, comment='文件大小(bytes)')
    extracted_text = Column(Text, comment='提取的文本内容')
    uploaded_by = Column(Integer, ForeignKey('sys_user.id'), nullable=False, comment='上传者ID')
    
    # 关系
    analysis = relationship("RequirementAnalysisModel", back_populates="document", uselist=False)


class RequirementAnalysisModel(Base):
    """需求分析记录"""
    __tablename__ = 'requirement_analyses'
    
    document_id = Column(Integer, ForeignKey('requirement_documents.id'), nullable=False, unique=True, comment='关联文档ID')
    analysis_report = Column(Text, comment='分析报告')
    requirements_count = Column(Integer, default=0, comment='需求数量')
    analysis_time = Column(Float, comment='分析耗时(秒)')
    
    # 关系
    document = relationship("RequirementDocumentModel", back_populates="analysis")
    requirements = relationship("BusinessRequirementModel", back_populates="analysis")


class BusinessRequirementModel(Base):
    """业务需求模型"""
    __tablename__ = 'business_requirements'
    
    analysis_id = Column(Integer, ForeignKey('requirement_analyses.id'), nullable=False, comment='关联分析ID')
    requirement_id = Column(String(50), nullable=False, comment='需求编号')
    requirement_name = Column(String(200), nullable=False, comment='需求名称')
    requirement_type = Column(String(20), nullable=False, comment='需求类型')
    parent_requirement_id = Column(Integer, ForeignKey('business_requirements.id'), comment='父级需求ID')
    module = Column(String(100), nullable=False, comment='所属模块')
    requirement_level = Column(String(10), nullable=False, comment='需求级别')
    reviewer = Column(String(50), default='admin', comment='评审人')
    estimated_hours = Column(Integer, default=8, comment='预计工时')
    description = Column(Text, nullable=False, comment='需求描述')
    acceptance_criteria = Column(Text, nullable=False, comment='验收标准')
    
    # 关系
    analysis = relationship("RequirementAnalysisModel", back_populates="requirements")
    parent_requirement = relationship("BusinessRequirementModel")
    test_cases = relationship("GeneratedTestCaseModel", back_populates="requirement")


class GeneratedTestCaseModel(Base):
    """AI生成测试用例模型"""
    __tablename__ = 'generated_test_cases'
    
    requirement_id = Column(Integer, ForeignKey('business_requirements.id'), nullable=False, comment='关联需求ID')
    case_id = Column(String(50), nullable=False, comment='用例编号')
    title = Column(String(300), nullable=False, comment='用例标题')
    priority = Column(String(5), nullable=False, comment='优先级: P0/P1/P2/P3')
    precondition = Column(Text, nullable=False, comment='前置条件')
    test_steps = Column(Text, nullable=False, comment='测试步骤')
    expected_result = Column(Text, nullable=False, comment='预期结果')
    status = Column(String(20), default='generated', comment='状态')
    generated_by_ai = Column(String(50), default='AI-A', comment='生成AI模型')
    reviewed_by_ai = Column(String(50), comment='评审AI模型')
    review_comments = Column(Text, comment='评审意见')
    
    # 关系
    requirement = relationship("BusinessRequirementModel", back_populates="test_cases")


class TestCaseGenerationTaskModel(Base):
    """测试用例生成任务模型"""
    __tablename__ = 'testcase_generation_tasks'
    
    project_id = Column(Integer, ForeignKey('projects.id'), comment='关联项目ID')
    task_id = Column(String(50), unique=True, nullable=False, comment='任务ID')
    title = Column(String(200), nullable=False, comment='任务标题')
    requirement_text = Column(Text, nullable=False, comment='需求描述')
    status = Column(String(20), default='pending', comment='状态')
    progress = Column(Integer, default=0, comment='进度百分比')
    output_mode = Column(String(10), default='stream', comment='输出模式: stream/complete')
    stream_buffer = Column(Text, comment='流式输出缓冲区')
    stream_position = Column(Integer, default=0, comment='流式输出位置')
    last_stream_update = Column(DateTime, comment='最后流式更新时间')
    
    # 配置参数
    writer_model_config_id = Column(Integer, ForeignKey('ai_model_configs.id'), comment='编写模型配置ID')
    reviewer_model_config_id = Column(Integer, ForeignKey('ai_model_configs.id'), comment='评审模型配置ID')
    writer_prompt_config_id = Column(Integer, ForeignKey('prompt_configs.id'), comment='编写提示词配置ID')
    reviewer_prompt_config_id = Column(Integer, ForeignKey('prompt_configs.id'), comment='评审提示词配置ID')
    
    # 生成结果
    generated_test_cases = Column(Text, comment='生成的测试用例')
    review_feedback = Column(Text, comment='评审反馈')
    final_test_cases = Column(Text, comment='最终测试用例')
    generation_log = Column(Text, comment='生成日志')
    error_message = Column(Text, comment='错误信息')
    created_by = Column(Integer, ForeignKey('sys_user.id'), nullable=False, comment='创建者ID')
    completed_at = Column(DateTime, comment='完成时间')
    is_saved_to_records = Column(Boolean, default=False, comment='是否已保存到记录')
    saved_at = Column(DateTime, comment='保存到记录时间')
    
    # 关系
    writer_model_config = relationship("AIModelConfigModel", foreign_keys=[writer_model_config_id])
    reviewer_model_config = relationship("AIModelConfigModel", foreign_keys=[reviewer_model_config_id])
    writer_prompt_config = relationship("PromptConfigModel", foreign_keys=[writer_prompt_config_id])
    reviewer_prompt_config = relationship("PromptConfigModel", foreign_keys=[reviewer_prompt_config_id])


class AIModelConfigModel(Base):
    """AI模型配置模型"""
    __tablename__ = 'ai_model_configs'
    
    name = Column(String(100), nullable=False, comment='配置名称')
    model_type = Column(String(20), nullable=False, comment='模型类型: deepseek/qwen/siliconflow/zhipu/other')
    role = Column(String(20), nullable=False, comment='角色: writer/reviewer/browser_use_text')
    api_key = Column(String(200), comment='API Key')
    base_url = Column(String(500), nullable=False, comment='API Base URL')
    model_name = Column(String(100), nullable=False, comment='模型名称')
    max_tokens = Column(Integer, default=4096, comment='最大Token数')
    temperature = Column(Float, default=0.7, comment='温度参数')
    top_p = Column(Float, default=0.9, comment='Top P参数')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_by = Column(Integer, ForeignKey('sys_user.id'), nullable=False, comment='创建者ID')
    llm_config_id = Column(Integer, comment='关联的LLM配置ID')


class PromptConfigModel(Base):
    """提示词配置模型"""
    __tablename__ = 'prompt_configs'
    
    name = Column(String(100), nullable=False, comment='配置名称')
    prompt_type = Column(String(20), nullable=False, comment='提示词类型: writer/reviewer')
    content = Column(Text, nullable=False, comment='提示词内容')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_by = Column(Integer, ForeignKey('sys_user.id'), nullable=False, comment='创建者ID')


class GenerationConfigModel(Base):
    """生成行为配置模型"""
    __tablename__ = 'generation_configs'
    
    name = Column(String(100), default='默认生成配置', comment='配置名称')
    default_output_mode = Column(String(10), default='stream', comment='默认输出模式')
    enable_auto_review = Column(Boolean, default=True, comment='启用AI评审和改进')
    review_timeout = Column(Integer, default=120, comment='评审和改进超时时间（秒）')
    is_active = Column(Boolean, default=True, comment='是否启用')


class AICaseModel(Base):
    """AI智能浏览器用例表"""
    __tablename__ = 'ai_cases'
    
    ui_project_id = Column(Integer, ForeignKey('ui_projects.id'), comment='所属UI项目ID')
    source_project_id = Column(Integer, comment='来源项目ID（测试管理项目）')
    source_module_id = Column(Integer, comment='来源模块ID（测试管理模块）')
    name = Column(String(200), nullable=False, comment='用例名称')
    description = Column(Text, comment='描述')
    task_description = Column(Text, nullable=False, comment='任务描述')
    status = Column(String(20), default='active', comment='状态: draft-草稿, active-激活, archived-归档')
    source_type = Column(String(20), default='manual', comment='来源类型: manual-手动创建, import-Excel导入, testcase-测试用例')
    priority = Column(String(10), default='P2', comment='优先级: P0-最高, P1-高, P2-中, P3-低')
    precondition = Column(Text, comment='前置条件')
    test_steps = Column(JSON, comment='测试步骤')
    expected_result = Column(Text, comment='预期结果')
    execution_mode = Column(String(20), default='headless', comment='执行模式: headless-无头, headed-有头')
    timeout = Column(Integer, default=300, comment='超时时间(秒)')
    created_by = Column(Integer, ForeignKey('sys_user.id'), comment='创建者ID')
    
    # 关系
    execution_records = relationship("AIExecutionRecordModel", back_populates="ai_case")


class AIExecutionRecordModel(Base):
    """AI执行记录表"""
    __tablename__ = 'ai_execution_records'
    
    ui_project_id = Column(Integer, ForeignKey('ui_projects.id'), comment='所属UI项目ID')
    ai_case_id = Column(Integer, ForeignKey('ai_cases.id'), comment='关联AI用例ID')
    case_name = Column(String(200), nullable=False, comment='用例名称快照')
    task_description = Column(Text, comment='任务描述')
    execution_mode = Column(String(20), default='text', comment='执行模式')
    status = Column(String(20), default='pending', comment='执行状态')
    start_time = Column(DateTime, default=func.now(), comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    duration = Column(Float, comment='执行时长(秒)')
    logs = Column(Text, comment='执行日志')
    error_message = Column(Text, comment='错误信息')
    steps_completed = Column(JSON, comment='已完成步骤')
    planned_tasks = Column(JSON, comment='规划任务')
    executed_by = Column(Integer, ForeignKey('sys_user.id'), comment='执行人ID')
    gif_path = Column(String(500), comment='GIF录制路径')
    screenshots_sequence = Column(JSON, comment='截图序列')
    
    # Token统计字段
    total_tokens = Column(Integer, default=0, comment='Token总使用量')
    prompt_tokens = Column(Integer, default=0, comment='提示词Token数')
    completion_tokens = Column(Integer, default=0, comment='完成Token数')
    api_calls = Column(Integer, default=0, comment='API调用次数')
    
    # 关系
    ai_case = relationship("AICaseModel", back_populates="execution_records")



class TestCaseTemplateModel(Base):
    """测试用例模板模型"""
    __tablename__ = 'testcase_templates'
    __table_args__ = {'extend_existing': True}
    
    # 明确定义不使用trace_id
    trace_id = None
    
    name = Column(String(100), nullable=False, comment='模板名称')
    description = Column(Text, comment='模板描述')
    template_type = Column(String(20), default='ui', comment='模板类型: ui/api/performance')
    field_mapping = Column(JSON, nullable=False, comment='字段映射配置')
    is_default = Column(Boolean, default=False, comment='是否默认模板')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_by = Column(Integer, ForeignKey('sys_user.id'), nullable=False, comment='创建者ID')



class FigmaConfigModel(Base):
    """Figma配置模型"""
    __tablename__ = 'figma_configs'
    
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='关联项目ID')
    access_token = Column(String(500), nullable=True, comment='Figma Access Token（公开文件可选）')
    file_key = Column(String(100), nullable=False, comment='Figma文件ID')
    file_name = Column(String(200), comment='文件名称')
    file_url = Column(Text, comment='Figma文件URL')
    last_sync_time = Column(DateTime, comment='最后同步时间')
    last_modified_time = Column(DateTime, comment='Figma文件最后修改时间')
    has_updates = Column(Integer, default=0, comment='是否有更新')


class FigmaExtractionTaskModel(Base):
    """Figma提取任务模型"""
    __tablename__ = 'figma_extraction_tasks'
    
    task_id = Column(String(50), nullable=False, unique=True, comment='任务ID（UUID）')
    config_id = Column(Integer, ForeignKey('figma_configs.id'), nullable=False, comment='关联Figma配置ID')
    extraction_mode = Column(String(20), nullable=False, default='simple', comment='提取模式: simple/complete')
    status = Column(String(20), nullable=False, default='pending', comment='状态: pending/processing/completed/failed')
    progress = Column(Integer, default=0, comment='进度百分比(0-100)')
    current_step = Column(String(200), comment='当前步骤描述')
    total_frames = Column(Integer, default=0, comment='总Frame数')
    processed_frames = Column(Integer, default=0, comment='已处理Frame数')
    error_message = Column(Text, comment='错误信息')
    result_document_id = Column(Integer, comment='结果文档ID')
    start_time = Column(DateTime, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')



class FigmaAPICallLogModel(Base):
    """Figma API调用日志模型"""
    __tablename__ = 'figma_api_call_logs'
    
    config_id = Column(Integer, ForeignKey('figma_configs.id'), nullable=False, comment='Figma配置ID')
    endpoint = Column(String(255), nullable=False, comment='API端点')
    call_time = Column(DateTime, nullable=False, comment='调用时间')
    status_code = Column(Integer, comment='HTTP状态码')
    response_time = Column(Integer, comment='响应时间(ms)')
    is_rate_limited = Column(Integer, default=0, comment='是否触发限制')


class FigmaFileCacheModel(Base):
    """Figma文件缓存模型"""
    __tablename__ = 'figma_file_cache'
    
    config_id = Column(Integer, ForeignKey('figma_configs.id'), nullable=False, comment='Figma配置ID')
    file_key = Column(String(255), nullable=False, unique=True, comment='文件ID')
    file_data = Column(Text, nullable=False, comment='文件数据(JSON)')
    file_version = Column(String(100), comment='文件版本')
    last_modified = Column(DateTime, comment='Figma文件最后修改时间')
    cache_time = Column(DateTime, nullable=False, comment='缓存时间')
    cache_size = Column(Integer, comment='缓存大小(bytes)')
    hit_count = Column(Integer, default=0, comment='命中次数')





# ==================== AI测试套件相关模型 ====================

class AITestSuiteModel(Base):
    """AI测试套件模型"""
    __tablename__ = 'ai_test_suites'
    
    name = Column(String(200), nullable=False, comment='套件名称')
    description = Column(Text, comment='套件描述')
    project_id = Column(Integer, nullable=False, comment='关联项目ID')
    status = Column(String(20), default='active', comment='状态：active/archived')


class AITestSuiteModuleModel(Base):
    """AI测试套件模块关联模型"""
    __tablename__ = 'ai_test_suite_modules'
    
    suite_id = Column(Integer, nullable=False, comment='套件ID')
    module_id = Column(Integer, nullable=False, comment='模块ID')
    module_name = Column(String(200), comment='模块名称（冗余字段）')
    execution_order = Column(Integer, nullable=False, comment='执行顺序')


class AITestSuiteExecutionModel(Base):
    """AI测试套件执行记录模型"""
    __tablename__ = 'ai_test_suite_executions'
    
    suite_id = Column(Integer, nullable=False, comment='套件ID')
    suite_name = Column(String(200), comment='套件名称（冗余字段）')
    execution_name = Column(String(200), comment='执行名称')
    execution_mode = Column(String(20), default='headless', comment='执行模式：headless/headed')
    status = Column(String(20), default='running', comment='状态：running/completed/failed')
    start_time = Column(DateTime, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    duration = Column(Numeric(10, 2), comment='执行时长（秒）')
    total_modules = Column(Integer, default=0, comment='总模块数')
    completed_modules = Column(Integer, default=0, comment='已完成模块数')
    failed_modules = Column(Integer, default=0, comment='失败模块数')
    total_cases = Column(Integer, default=0, comment='总用例数')
    passed_cases = Column(Integer, default=0, comment='通过用例数')
    failed_cases = Column(Integer, default=0, comment='失败用例数')
    error_message = Column(Text, comment='错误信息')


class AITestSuiteModuleExecutionModel(Base):
    """AI测试套件模块执行记录模型"""
    __tablename__ = 'ai_test_suite_module_executions'
    
    suite_execution_id = Column(Integer, nullable=False, comment='套件执行记录ID')
    module_id = Column(Integer, nullable=False, comment='模块ID')
    module_name = Column(String(200), comment='模块名称')
    execution_order = Column(Integer, comment='执行顺序')
    status = Column(String(20), default='pending', comment='状态：pending/running/completed/failed')
    start_time = Column(DateTime, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    duration = Column(Numeric(10, 2), comment='执行时长（秒）')
    total_cases = Column(Integer, default=0, comment='总用例数')
    passed_cases = Column(Integer, default=0, comment='通过用例数')
    failed_cases = Column(Integer, default=0, comment='失败用例数')
    error_message = Column(Text, comment='错误信息')


# ==================== AI测试报告相关模型 ====================

class AITestReportModel(Base):
    """AI测试报告模型"""
    __tablename__ = 'ai_test_reports'
    
    report_id = Column(String(100), nullable=False, unique=True, comment='报告ID')
    report_name = Column(String(200), nullable=False, comment='报告名称')
    project_id = Column(Integer, comment='项目ID')
    project_name = Column(String(200), comment='项目名称')
    start_date = Column(DateTime, comment='开始日期')
    end_date = Column(DateTime, comment='结束日期')
    date_range = Column(String(100), comment='时间范围')
    status = Column(String(50), default='generated', comment='报告状态')
    
    # 统计信息
    total_cases = Column(Integer, default=0, comment='总用例数')
    total_executions = Column(Integer, default=0, comment='总执行次数')
    success_count = Column(Integer, default=0, comment='成功次数')
    failed_count = Column(Integer, default=0, comment='失败次数')
    success_rate = Column(Numeric(5, 2), default=0, comment='成功率')
    total_duration = Column(Numeric(10, 2), default=0, comment='总执行时长(秒)')
    avg_duration = Column(Numeric(10, 2), default=0, comment='平均时长(秒)')
    total_tokens = Column(Integer, default=0, comment='总Token使用量')
    
    # 报告内容（JSON格式）
    report_data = Column(JSON, comment='报告详细数据')
