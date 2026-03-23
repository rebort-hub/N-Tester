# -*- coding: utf-8 -*-
"""
API 相关模型
"""
from sqlalchemy import Column, Integer, String, Text

from app.models.base import Base


class ProjectInfo(Base):
    """项目信息表"""
    __tablename__ = 'project_info'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='项目ID')
    name = Column(String(100), nullable=False, comment='项目名称')
    description = Column(Text, comment='项目描述')


class LegacyModuleInfo(Base):
    """旧版模块信息表（用于兼容）"""
    __tablename__ = 'legacy_module_info'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='模块ID')
    name = Column(String(100), nullable=False, comment='模块名称')
    project_id = Column(Integer, nullable=False, comment='所属项目ID')
    description = Column(Text, comment='模块描述')
