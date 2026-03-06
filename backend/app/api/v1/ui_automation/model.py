"""
UI自动化模块 - 数据模型
"""
from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class UIProjectModel(Base):
    """UI自动化项目模型"""
    __tablename__ = 'ui_projects'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(BigInteger, nullable=False, index=True, comment='关联项目ID')
    name = Column(String(200), nullable=False, comment='UI项目名称')
    description = Column(Text, comment='项目描述')
    base_url = Column(String(500), comment='基础URL')
    browser_type = Column(String(20), default='chromium', comment='浏览器类型')
    viewport_width = Column(Integer, default=1920, comment='视口宽度')
    viewport_height = Column(Integer, default=1080, comment='视口高度')
    timeout = Column(Integer, default=30000, comment='默认超时时间(毫秒)')
    
    # 基础字段
    creation_date = Column(DateTime, server_default=func.now(), comment='创建时间')
    created_by = Column(BigInteger, comment='创建人ID')
    updation_date = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    updated_by = Column(BigInteger, comment='更新人ID')
    enabled_flag = Column(Boolean, default=True, comment='启用标志')
    trace_id = Column(String(50), comment='追踪ID')


class UIElementGroupModel(Base):
    """UI元素分组模型"""
    __tablename__ = 'ui_element_groups'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    ui_project_id = Column(BigInteger, nullable=False, index=True, comment='关联UI项目ID')
    name = Column(String(200), nullable=False, comment='分组名称')
    description = Column(Text, comment='分组描述')
    parent_id = Column(BigInteger, index=True, comment='父分组ID')
    order_num = Column(Integer, default=0, comment='排序')
    
    # 基础字段
    creation_date = Column(DateTime, server_default=func.now(), comment='创建时间')
    created_by = Column(BigInteger, comment='创建人ID')
    updation_date = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    updated_by = Column(BigInteger, comment='更新人ID')
    enabled_flag = Column(Boolean, default=True, comment='启用标志')
    trace_id = Column(String(50), comment='追踪ID')


class UIElementModel(Base):
    """UI元素模型"""
    __tablename__ = 'ui_elements'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    group_id = Column(BigInteger, nullable=False, index=True, comment='关联分组ID')
    name = Column(String(200), nullable=False, comment='元素名称')
    description = Column(Text, comment='元素描述')
    element_type = Column(String(50), default='button', comment='元素类型')
    locator_strategy = Column(String(50), nullable=False, comment='定位策略')
    locator_value = Column(String(1000), nullable=False, comment='定位器值')
    backup_locators = Column(JSON, comment='备用定位器列表')
    wait_time = Column(Integer, default=5000, comment='等待时间(毫秒)')
    is_dynamic = Column(Boolean, default=False, comment='是否动态元素')
    screenshot = Column(String(500), comment='元素截图路径')
    
    # 基础字段
    creation_date = Column(DateTime, server_default=func.now(), comment='创建时间')
    created_by = Column(BigInteger, comment='创建人ID')
    updation_date = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    updated_by = Column(BigInteger, comment='更新人ID')
    enabled_flag = Column(Boolean, default=True, comment='启用标志')
    trace_id = Column(String(50), comment='追踪ID')


class UIPageObjectModel(Base):
    """UI页面对象模型"""
    __tablename__ = 'ui_page_objects'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    ui_project_id = Column(BigInteger, nullable=False, index=True, comment='关联UI项目ID')
    name = Column(String(200), nullable=False, comment='页面对象名称')
    class_name = Column(String(200), nullable=False, comment='类名')
    description = Column(Text, comment='页面对象描述')
    url_pattern = Column(String(500), comment='URL模式')
    template_code = Column(Text, comment='生成的代码模板')
    
    # 基础字段
    creation_date = Column(DateTime, server_default=func.now(), comment='创建时间')
    created_by = Column(BigInteger, comment='创建人ID')
    updation_date = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    updated_by = Column(BigInteger, comment='更新人ID')
    enabled_flag = Column(Boolean, default=True, comment='启用标志')
    trace_id = Column(String(50), comment='追踪ID')


class UIPageObjectElementModel(Base):
    """页面对象元素关联模型"""
    __tablename__ = 'ui_page_object_elements'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    page_object_id = Column(BigInteger, nullable=False, index=True, comment='关联页面对象ID')
    element_id = Column(BigInteger, nullable=False, index=True, comment='关联元素ID')
    method_name = Column(String(200), nullable=False, comment='方法名称')
    is_property = Column(Boolean, default=False, comment='是否为属性')
    order_num = Column(Integer, default=0, comment='排序')
    
    # 基础字段
    creation_date = Column(DateTime, server_default=func.now(), comment='创建时间')
    created_by = Column(BigInteger, comment='创建人ID')


class UITestCaseModel(Base):
    """UI测试用例模型"""
    __tablename__ = 'ui_test_cases'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    ui_project_id = Column(BigInteger, nullable=False, index=True, comment='关联UI项目ID')
    name = Column(String(200), nullable=False, comment='用例名称')
    description = Column(Text, comment='用例描述')
    priority = Column(String(20), default='medium', comment='优先级')
    tags = Column(JSON, comment='标签列表')
    preconditions = Column(Text, comment='前置条件')
    expected_result = Column(Text, comment='预期结果')
    
    # 基础字段
    creation_date = Column(DateTime, server_default=func.now(), comment='创建时间')
    created_by = Column(BigInteger, comment='创建人ID')
    updation_date = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    updated_by = Column(BigInteger, comment='更新人ID')
    enabled_flag = Column(Boolean, default=True, comment='启用标志')
    trace_id = Column(String(50), comment='追踪ID')


class UITestStepModel(Base):
    """UI测试步骤模型"""
    __tablename__ = 'ui_test_steps'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    test_case_id = Column(BigInteger, nullable=False, index=True, comment='关联测试用例ID')
    step_number = Column(Integer, nullable=False, comment='步骤序号')
    action_type = Column(String(50), nullable=False, comment='操作类型')
    element_id = Column(BigInteger, comment='关联元素ID')
    action_value = Column(Text, comment='操作值')
    description = Column(Text, comment='步骤描述')
    assertion_type = Column(String(50), comment='断言类型')
    assertion_value = Column(Text, comment='断言值')
    screenshot_on_failure = Column(Boolean, default=True, comment='失败时截图')
    continue_on_failure = Column(Boolean, default=False, comment='失败时继续')
    
    # 基础字段
    creation_date = Column(DateTime, server_default=func.now(), comment='创建时间')
    created_by = Column(BigInteger, comment='创建人ID')


class UITestSuiteModel(Base):
    """UI测试套件模型"""
    __tablename__ = 'ui_test_suites'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    ui_project_id = Column(BigInteger, nullable=False, index=True, comment='关联UI项目ID')
    name = Column(String(200), nullable=False, comment='套件名称')
    description = Column(Text, comment='套件描述')
    engine_type = Column(String(20), default='playwright', comment='执行引擎')
    browser_type = Column(String(20), default='chromium', comment='浏览器类型')
    headless = Column(Boolean, default=True, comment='无头模式')
    parallel = Column(Boolean, default=False, comment='并行执行')
    max_workers = Column(Integer, default=1, comment='最大并行数')
    
    # 基础字段
    creation_date = Column(DateTime, server_default=func.now(), comment='创建时间')
    created_by = Column(BigInteger, comment='创建人ID')
    updation_date = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    updated_by = Column(BigInteger, comment='更新人ID')
    enabled_flag = Column(Boolean, default=True, comment='启用标志')
    trace_id = Column(String(50), comment='追踪ID')


class UISuiteCaseModel(Base):
    """UI套件用例关联模型"""
    __tablename__ = 'ui_suite_cases'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    suite_id = Column(BigInteger, nullable=False, index=True, comment='关联套件ID')
    test_case_id = Column(BigInteger, nullable=False, index=True, comment='关联测试用例ID')
    order_num = Column(Integer, default=0, comment='执行顺序')
    
    # 基础字段
    creation_date = Column(DateTime, server_default=func.now(), comment='创建时间')
    created_by = Column(BigInteger, comment='创建人ID')
    enabled_flag = Column(Boolean, default=True, comment='启用标志')
    trace_id = Column(String(50), comment='追踪ID')


class UIExecutionModel(Base):
    """UI执行记录模型"""
    __tablename__ = 'ui_executions'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    ui_project_id = Column(BigInteger, index=True, comment='UI项目ID')
    suite_id = Column(BigInteger, index=True, comment='关联套件ID')
    test_case_id = Column(BigInteger, index=True, comment='关联用例ID')
    engine_type = Column(String(20), nullable=False, comment='执行引擎')
    browser_type = Column(String(20), nullable=False, comment='浏览器类型')
    status = Column(String(20), nullable=False, index=True, comment='执行状态')
    start_time = Column(DateTime, index=True, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    duration = Column(Integer, comment='执行时长(毫秒)')
    total_steps = Column(Integer, default=0, comment='总步骤数')
    passed_steps = Column(Integer, default=0, comment='通过步骤数')
    failed_steps = Column(Integer, default=0, comment='失败步骤数')
    error_message = Column(Text, comment='错误信息')
    screenshots = Column(JSON, comment='截图列表')
    video_path = Column(String(500), comment='录屏路径')
    logs = Column(Text, comment='执行日志')
    executed_by = Column(BigInteger, comment='执行人ID')
    
    # 基础字段
    creation_date = Column(DateTime, server_default=func.now(), comment='创建时间')
