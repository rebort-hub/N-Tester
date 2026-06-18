#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
from sqlalchemy import Column, String, Text, Integer, UniqueConstraint
from app.models.base import Base

"""
性能测试 - 配置管理模型
"""
class PerfConfigMachineModel(Base):
    """压力机配置"""
    __tablename__ = 'perf_config_machines'

    name            = Column(String(100), nullable=False, comment='自定义名称，如：jmeter-Master控制机、节点机1')
    machine_type    = Column(Integer,  nullable=False, comment='压力机类型：1-Master，2-Slave，3-单机')
    status          = Column(Integer, default=1, comment='状态：1启用 0禁用')
    ip              = Column(String(255), nullable=False, comment='机器IP或DNS域名；物理机/云主机填IP，K8S Pod填Headless Service DNS')
    ssh_port        = Column(Integer, default=22, nullable=False, comment='SSH端口，默认22')
    rmi_port        = Column(Integer, nullable=False, comment='JMeter RMI监听端口，默认1099')
    monitor         = Column(Integer, comment='Prometheus监听端口')
    max_concurrency = Column(Integer, comment='最大并发数')
    ssh_user        = Column(String(100), nullable=True, comment='SSH登录用户名，空则用全局 SSH_DEFAULT_USER')
    ssh_password    = Column(String(500), nullable=True, comment='SSH登录密码（Fernet加密），空则用全局 SSH_DEFAULT_PASSWORD')
    remark          = Column(Text, comment='备注')


class PerfConfigParamModel(Base):
    """性能参数配置"""
    __tablename__ = 'perf_config_params'
    __table_args__ = (
        UniqueConstraint('param_key', name='uq_perf_config_params_param_key'),
        {'mysql_charset': 'utf8'},
    )

    name        = Column(String(200), nullable=False, comment='参数名称')
    param_key   = Column(String(200), nullable=False, comment='参数名（英文标识，如 data_type）')
    param_value = Column(String(500), nullable=False, comment='参数值（均以字符串存储）')
    status      = Column(Integer, default=1, nullable=False,  comment='状态：1启用 0禁用')
    is_system   = Column(Integer, default=0, nullable=False,  comment='是否系统参数：1-是 0-否；系统参数不可删除，且 param_key 不可修改')
    remark      = Column(Text, comment='备注')