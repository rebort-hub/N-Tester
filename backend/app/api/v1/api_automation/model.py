"""
接口自动化模块
"""

from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, BigInteger, Float
from sqlalchemy.sql import func

from app.models.base import Base


class ApiProjectModel(Base):
    """API项目模型"""
    __tablename__ = 'api_automation_projects'
    
    name = Column(String(255), nullable=False, comment='项目名称')
    img = Column(String(255), comment='项目图标')
    description = Column(Text, comment='项目描述')


class ApiServiceModel(Base):
    """API服务模型"""
    __tablename__ = 'api_automation_services'
    
    name = Column(String(255), nullable=False, comment='服务名称')
    api_project_id = Column(BigInteger, nullable=False, comment='项目ID')
    img = Column(String(255), comment='服务图标')
    description = Column(Text, comment='服务描述')
    source_type = Column(String(50), comment='接口文档类型：swagger/apifox')
    source_addr = Column(String(500), comment='接口文档地址')
    last_pull_status = Column(Integer, default=0, comment='拉取状态：0=未拉取，1=成功，2=失败')
    manager = Column(BigInteger, comment='负责人用户ID')
    business_id = Column(BigInteger, comment='业务线ID')
    sort = Column(Integer, default=0, comment='排序权重')


class ApiEnvironmentModel(Base):
    """API环境模型"""
    __tablename__ = 'api_automation_environments'
    
    name = Column(String(255), nullable=False, comment='环境名称')
    config = Column(JSON, comment='环境配置')
    variable = Column(JSON, comment='环境变量')
    description = Column(Text, comment='环境描述')


class ApiVariableModel(Base):
    """API全局变量模型"""
    __tablename__ = 'api_automation_variables'
    
    name = Column(String(255), nullable=False, comment='变量名')
    value = Column(String(255), nullable=False, comment='变量值')
    description = Column(Text, comment='变量描述')


class ApiModel(Base):
    """API接口模型"""
    __tablename__ = 'api_automation_apis'
    
    url = Column(String(255), nullable=False, comment='接口URL')
    req = Column(JSON, comment='请求配置')
    document = Column(JSON, comment='接口文档')
    api_service_id = Column(BigInteger, nullable=False, comment='服务ID')
    name = Column(String(255), comment='接口名称')
    description = Column(Text, comment='接口描述')


class ApiMenuModel(Base):
    """API菜单模型"""
    __tablename__ = 'api_automation_menus'
    
    name = Column(String(255), nullable=False, comment='菜单名称')
    type = Column(Integer, nullable=False, comment='菜单类型')
    pid = Column(BigInteger, nullable=False, comment='父菜单ID')
    api_id = Column(BigInteger, comment='接口ID')
    api_service_id = Column(BigInteger, nullable=False, comment='服务ID')
    status = Column(Integer, nullable=False, comment='状态')


class ApiResultModel(Base):
    """API执行结果模型"""
    __tablename__ = 'api_automation_results'
    
    req = Column(JSON, comment='请求数据')
    res = Column(JSON, comment='响应数据')
    api_id = Column(BigInteger, nullable=False, comment='接口ID')
    status_code = Column(Integer, comment='状态码')
    response_time = Column(Float, comment='响应时间')
    error_message = Column(Text, comment='错误信息')


class ApiScriptModel(Base):
    """API场景模型"""
    __tablename__ = 'api_automation_scripts'
    
    name = Column(String(255), nullable=False, comment='场景名称')
    type = Column(Integer, default=1, comment='场景类型')
    script = Column(JSON, nullable=False, comment='场景步骤')
    config = Column(JSON, comment='场景配置')
    description = Column(String(255), default='', comment='场景描述')


class ApiScriptResultListModel(Base):
    """API场景执行汇总模型"""
    __tablename__ = 'api_automation_script_result_lists'
    
    result_id = Column(BigInteger, nullable=False, comment='执行ID')
    name = Column(String(255), nullable=False, comment='场景名称')
    script = Column(JSON, comment='场景配置')
    config = Column(JSON, comment='执行配置')
    result = Column(JSON, comment='执行结果')
    start_time = Column(DateTime, server_default=func.now(), comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    api_service_id = Column(BigInteger, comment='关联服务ID，可为空（兼容历史数据）')


class ApiScriptResultModel(Base):
    """API场景执行详情模型"""
    __tablename__ = 'api_automation_script_results'
    
    name = Column(String(255), nullable=False, comment='步骤名称')
    uuid = Column(String(255), comment='唯一标识')
    menu_id = Column(String(255), nullable=False, comment='菜单ID')
    result_id = Column(BigInteger, nullable=False, comment='执行ID')
    status = Column(Integer, default=1, comment='执行状态')
    req = Column(JSON, comment='请求数据')
    res = Column(JSON, comment='响应数据')


class ApiDatabaseModel(Base):
    """API数据库配置模型"""
    __tablename__ = 'api_automation_databases'
    
    name = Column(String(255), nullable=False, comment='数据库名称')
    config = Column(JSON, comment='数据库配置')
    db_type = Column(String(50), comment='数据库类型')
    host = Column(String(255), comment='主机地址')
    port = Column(Integer, comment='端口')
    database_name = Column(String(255), comment='数据库名')
    username = Column(String(255), comment='用户名')
    password = Column(String(500), comment='密码')


class ApiCodeModel(Base):
    """API错误码模型"""
    __tablename__ = 'api_automation_codes'
    
    code = Column(String(255), nullable=False, comment='错误码')
    name = Column(String(255), nullable=False, comment='错误码名称')
    description = Column(Text, comment='错误码描述')


class ApiParamsModel(Base):
    """API参数依赖"""
    __tablename__ = "api_automation_params"

    name = Column(String(255), nullable=False, comment="参数名称")
    value = Column(JSON, comment="参数值")


class ApiEditModel(Base):
    """API编辑历史"""
    __tablename__ = "api_automation_edits"

    api_id = Column(BigInteger, nullable=False, comment="接口ID")
    edit = Column(JSON, comment="变更内容")


class ApiFunctionModel(Base):
    """公共函数"""
    __tablename__ = "api_automation_functions"

    name = Column(String(255), nullable=False, comment="公共函数名称")
    description = Column(String(255), comment="公共函数描述")


class ApiUpdateModel(Base):
    """API 文档同步变更记录"""
    __tablename__ = "api_automation_updates"

    req = Column(JSON, comment="变更内容")
    api_id = Column(BigInteger, nullable=False, comment="接口ID")
    api_service_id = Column(BigInteger, nullable=False, comment="服务ID")


class ApiSuiteModel(Base):
    """API用例集模型"""
    __tablename__ = 'api_automation_suites'

    name = Column(String(255), nullable=False, comment='用例集名称')
    parent = Column(BigInteger, comment='父用例集ID，顶级为null')
    api_service_id = Column(BigInteger, nullable=False, comment='所属服务ID')
    sort = Column(Integer, default=0, comment='同级排序权重')


class ApiCaseModel(Base):
    """API用例模型"""
    __tablename__ = 'api_automation_cases'

    name = Column(String(255), nullable=False, comment='用例名称')
    description = Column(String(500), comment='用例描述')
    suite_id = Column(BigInteger, nullable=False, comment='所属用例集ID')
    script = Column(JSON, comment='步骤列表（接口步骤数组）')
    status = Column(Integer, default=0, comment='状态：0=未执行，1=通过，2=失败')
    case_type = Column(Integer, default=1, comment='用例类型：1=正向，2=负向，3=边界值，4=安全性，5=其他')
