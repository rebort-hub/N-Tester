"""
云真机模块 - 数据模型
迁移自 l-tester/views/app/app_model.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class AppDevice(Base):
    """云真机设备模型 - 对应旧架构 App_device"""
    __tablename__ = 'app_devices'
    __table_args__ = {'comment': '云真机设备表'}
    
    device_name = Column(String(255), nullable=False, comment='设备名称')
    device_id = Column(String(255), nullable=False, comment='设备ID')
    device_status = Column(Integer, nullable=False, default=1, comment='设备状态: 1-空闲, 2-使用中, 3-离线')
    device_type = Column(String(255), nullable=False, comment='设备类型')
    device_version = Column(String(255), comment='设备版本')
    device_info = Column(JSON, comment='设备详细信息')
    file_path = Column(Text, nullable=False, comment='设备图片路径')
    device_description = Column(Text, comment='设备描述')
    user_id = Column(Integer, ForeignKey('sys_user.id'), nullable=False, comment='用户ID')
    
    # 兼容字段（数据库表有created_at和updated_at）
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    device_logs = relationship("AppDeviceLog", back_populates="device")
    device_installs = relationship("AppDeviceInstall", back_populates="device")


class AppDeviceLog(Base):
    """设备使用日志模型 - 对应旧架构 App_device_log"""
    __tablename__ = 'app_device_logs'
    __table_args__ = {'comment': '设备使用日志表'}
    
    device_id = Column(Integer, ForeignKey('app_devices.id'), nullable=False, comment='设备ID')
    user_id = Column(Integer, ForeignKey('sys_user.id'), nullable=False, comment='用户ID')
    start_time = Column(DateTime, server_default=func.now(), comment='开始使用时间')
    end_time = Column(DateTime, comment='结束使用时间')
    
    # 兼容字段
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    device = relationship("AppDevice", back_populates="device_logs")


class AppDeviceInstall(Base):
    """设备APP安装历史模型 - 对应旧架构 App_device_install"""
    __tablename__ = 'app_device_installs'
    __table_args__ = {'comment': '设备APP安装历史表'}
    
    apk_name = Column(Text, nullable=False, comment='APK名称')
    apk_path = Column(Text, nullable=False, comment='APK路径')
    device_id = Column(Integer, ForeignKey('app_devices.id'), nullable=False, comment='设备ID')
    user_id = Column(Integer, ForeignKey('sys_user.id'), nullable=False, comment='用户ID')
    create_time = Column(DateTime, server_default=func.now(), comment='安装时间')
    
    # 兼容字段
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    device = relationship("AppDevice", back_populates="device_installs")


class AppDeviceLogList(Base):
    """设备日志列表模型 - 对应旧架构 App_device_log_list"""
    __tablename__ = 'app_device_log_lists'
    __table_args__ = {'comment': '设备日志列表表'}
    
    name = Column(String(255), nullable=False, comment='名称')
    together_id = Column(Integer, nullable=False, comment='关联ID')
    
    # 兼容字段
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')