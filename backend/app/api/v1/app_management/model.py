"""
APP自动化模块 - 数据模型
一比一迁移自 l-tester/views/app/app_model.py（Tortoise ORM）
"""

from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, BigInteger, ForeignKey
from sqlalchemy.sql import func

from app.models.base import Base


class AppMenuModel(Base):
    """脚本菜单（目录树）"""

    __tablename__ = "app_menus"
    __table_args__ = {"comment": "APP自动化菜单表"}

    name = Column(String(255), nullable=False, unique=True, comment="名称")
    pid = Column(BigInteger, nullable=False, comment="父id")
    type = Column(Integer, nullable=False, comment="类型")
    user_id = Column(BigInteger, ForeignKey("sys_user.id"), nullable=False, comment="用户ID")


class AppScriptModel(Base):
    """脚本内容"""

    __tablename__ = "app_scripts"
    __table_args__ = {"comment": "APP自动化脚本表"}

    script = Column(JSON, nullable=False, comment="脚本")
    menu_id = Column(BigInteger, ForeignKey("app_menus.id"), nullable=False, unique=True, comment="菜单ID")
    user_id = Column(BigInteger, ForeignKey("sys_user.id"), nullable=False, comment="用户ID")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class AppResultModel(Base):
    """单步执行结果（每个脚本步骤/断言等都会写一条）"""

    __tablename__ = "app_results"
    __table_args__ = {"comment": "APP自动化执行结果表"}

    device = Column(String(255), nullable=False, comment="设备")
    result_id = Column(String(255), nullable=False, comment="结果id")
    name = Column(String(255), nullable=False, comment="脚本名称")
    status = Column(Integer, nullable=False, comment="状态 0失败 1成功 2进行中(兼容旧)")
    log = Column(Text, nullable=True, comment="详情")
    assert_value = Column(JSON, nullable=True, comment="断言详情")
    before_img = Column(Text, nullable=True, comment="执行前截图地址")
    after_img = Column(Text, nullable=True, comment="执行后截图地址")
    video = Column(Text, nullable=True, comment="视频地址")
    performance = Column(JSON, nullable=True, comment="实时性能")
    menu_id = Column(BigInteger, ForeignKey("app_menus.id"), nullable=False, comment="菜单ID")
    create_time = Column(DateTime, server_default=func.now(), comment="执行时间")
    user_id = Column(BigInteger, ForeignKey("sys_user.id"), nullable=False, comment="用户ID")


class AppResultListModel(Base):
    """一次任务执行的汇总（任务名、设备列表、脚本列表、执行统计等）"""

    __tablename__ = "app_result_lists"
    __table_args__ = {"comment": "APP自动化结果汇总表"}

    task_name = Column(String(255), nullable=False, comment="任务名称")
    device_list = Column(JSON, nullable=False, comment="设备列表")
    result_id = Column(String(255), unique=True, nullable=False, comment="结果id")
    script_list = Column(JSON, nullable=False, comment="脚本列表")
    script_status = Column(JSON, nullable=False, comment="脚本执行情况")
    start_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    end_time = Column(DateTime, nullable=True, comment="更新时间")
    user_id = Column(BigInteger, ForeignKey("sys_user.id"), nullable=False, comment="用户ID")


class AppAirtestImageModel(Base):
    """Airtest 图像库（迁移自 l-tester/views/common/upload_model.py airtest_img）"""

    __tablename__ = "app_airtest_images"
    __table_args__ = {"comment": "APP自动化 Airtest 图像库"}

    file_name = Column(String(255), nullable=False, comment="图片名称")
    file_path = Column(Text, nullable=False, comment="图片地址")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    menu_id = Column(BigInteger, ForeignKey("app_menus.id"), nullable=True, comment="所属菜单")