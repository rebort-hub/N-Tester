"""
Web管理模块 - 数据模型
"""
from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, Boolean, BigInteger
from sqlalchemy.sql import func
from app.models.base import Base


class WebMenuModel(Base):
    """Web脚本菜单模型"""
    __tablename__ = 'web_management_menus'
    
    name = Column(String(255), unique=True, nullable=False, comment='菜单名称')
    pid = Column(BigInteger, nullable=False, comment='父菜单ID')
    type = Column(Integer, nullable=False, comment='菜单类型: 0-文件夹, 1-脚本组, 2-脚本')


class WebScriptModel(Base):
    """Web脚本模型"""
    __tablename__ = 'web_management_scripts'
    
    script = Column(JSON, nullable=False, comment='脚本步骤')
    menu_id = Column(BigInteger, nullable=False, unique=True, comment='菜单ID')


class WebElementMenuModel(Base):
    """Web元素菜单模型"""
    __tablename__ = 'web_management_element_menus'
    
    name = Column(String(255), unique=True, nullable=False, comment='元素菜单名称')
    pid = Column(BigInteger, nullable=False, comment='父菜单ID')
    type = Column(Integer, nullable=False, comment='菜单类型')
    element_id = Column(BigInteger, comment='元素ID')


class WebElementModel(Base):
    """Web页面元素模型"""
    __tablename__ = 'web_management_elements'
    
    name = Column(String(255), nullable=False, comment='元素名称')
    element = Column(JSON, nullable=False, comment='元素选择器信息')
    menu_id = Column(BigInteger, comment='菜单ID')
    element_type = Column(String(50), comment='元素类型')
    locator_strategy = Column(String(50), comment='定位策略')
    locator_value = Column(String(1000), comment='定位器值')


class WebGroupModel(Base):
    """Web脚本集模型"""
    __tablename__ = 'web_management_groups'
    
    name = Column(String(255), unique=True, nullable=False, comment='脚本集名称')
    script = Column(JSON, comment='脚本集配置')
    description = Column(String(255), comment='脚本集描述')


class WebResultListModel(Base):
    """Web执行汇总模型"""
    __tablename__ = 'web_management_result_lists'
    
    task_name = Column(String(255), nullable=False, comment='任务名称')
    result_id = Column(String(255), nullable=False, comment='执行ID')
    script_list = Column(JSON, nullable=False, comment='脚本列表')
    browser_list = Column(JSON, nullable=False, comment='浏览器列表')
    result = Column(JSON, nullable=False, comment='执行结果')
    pid_list = Column(JSON, comment='执行进程PID列表（兼容旧 stop_web_script）')
    start_time = Column(DateTime, server_default=func.now(), comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    status = Column(Integer, default=1, comment='执行状态: 0-执行中, 1-完成')


class WebResultDetailModel(Base):
    """Web执行详情模型"""
    __tablename__ = 'web_management_result_details'
    
    name = Column(String(255), nullable=False, comment='脚本名称')
    result_id = Column(String(255), nullable=False, comment='执行ID')
    browser = Column(String(255), nullable=False, comment='浏览器类型')
    log = Column(Text, nullable=False, comment='执行日志')
    status = Column(Integer, nullable=False, comment='执行状态: 0-失败, 1-成功')
    before_img = Column(String(255), comment='执行前截图')
    after_img = Column(String(255), comment='执行后截图')
    video = Column(String(255), comment='视频地址')
    trace = Column(String(255), comment='Playwright trace文件')
    assert_result = Column(JSON, nullable=False, comment='断言结果')
    menu_id = Column(BigInteger, comment='脚本菜单ID')