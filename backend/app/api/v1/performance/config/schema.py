#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from app.core.base_schema import BaseSchema

"""
性能测试 - 配置管理 Schema
"""
# ============================== 压力机配置 ==================================

class PerfMachineCreateSchema(BaseModel):
    """压力机配置【新建】 - 请求体 Schema"""
    name:            str           = Field(..., max_length=100, description='自定义名称，如：jmeter-Master控制机、节点机1')
    machine_type:    int           = Field(..., description='压力机类型：1-Master，2-Slave，3-单机')
    status:          int           = Field(1, description='状态：1启用 0禁用')
    ip:              str           = Field(..., max_length=255, description='机器IP或DNS域名；物理机/云主机填IP，K8S Pod填Headless Service DNS')
    ssh_port:        int           = Field(22, ge=1, le=65535, description='SSH端口，默认22')
    rmi_port:        int           = Field(..., ge=1, le=65535, description='JMeter RMI监听端口，默认1099')
    monitor:         Optional[int] = Field(None, ge=1, le=65535, description='Prometheus监听端口')
    max_concurrency: Optional[int] = Field(None, description='最大并发数')
    ssh_user:        Optional[str] = Field(None, max_length=100, description='SSH登录用户名，空则用全局配置')
    ssh_password:    Optional[str] = Field(None, description='SSH登录密码（明文或Fernet token回传），后端自动处理')
    remark:          Optional[str] = Field(None, description='备注')


class PerfMachineUpdateSchema(BaseModel):
    """压力机配置【修改】 - 请求体 Schema（所有字段均为可选，仅传入需修改的字段）"""
    name:            Optional[str] = Field(None, max_length=100)
    machine_type:    Optional[int] = None
    status:          Optional[int] = None
    ip:              Optional[str] = Field(None, max_length=255)
    ssh_port:        Optional[int] = Field(None, ge=1, le=65535)
    rmi_port:        Optional[int] = Field(None, ge=1, le=65535)
    monitor:         Optional[int] = Field(None, ge=1, le=65535)
    max_concurrency: Optional[int] = None
    ssh_user:        Optional[str] = Field(None, max_length=100)
    ssh_password:    Optional[str] = None  # None=不更新，''=清空，明文/Fernet token=更新
    remark:          Optional[str] = None


class PerfMachineRespSchema(BaseModel):
    """压力机配置【响应】 - 响应体 Schema"""
    model_config = {"from_attributes": True}

    id:              int
    name:            str
    machine_type:    int
    status:          int
    ip:              Optional[str] = None
    ssh_port:        int = 22
    rmi_port:        int
    monitor:         Optional[int] = None
    max_concurrency: Optional[int] = None
    ssh_user:        Optional[str] = None
    ssh_password:    Optional[str] = None  # Fernet 密文（gAAAAA...），前端不可读；None 表示未配置
    remark:          Optional[str] = None
    creation_date:   Optional[datetime] = None
    updation_date:   Optional[datetime] = None
    operator_name:   Optional[str] = None   # 操作人昵称（新建=创建人，修改后=修改人）


class PerfMachinePageSchema(BaseSchema):
    """压力机配置【分页】 - 分页响应体 Schema"""
    total:     int
    page:      int
    page_size: int
    items:     List[PerfMachineRespSchema]


# ========================== 参数配置 =============================

class PerfParamCreateSchema(BaseModel):
    """性能参数配置【创建】 - 请求体 Schema"""
    name:        str           = Field(..., max_length=200, description='参数名称')
    param_key:   str           = Field(..., max_length=200, description='参数名')
    param_value: str           = Field(..., max_length=500, description='参数值')
    status:      int           = Field(1,                   description='状态：1启用 0禁用')
    is_system:   int           = Field(0, ge=0, le=1,       description='是否系统参数：1-是 0-否')
    remark:      Optional[str] = Field(None,               description='备注')


class PerfParamUpdateSchema(BaseModel):
    """性能参数配置【更新】 - 请求体 Schema（param_key 不允许修改，仅传入需修改的字段）"""
    name:        Optional[str] = Field(None, max_length=200)
    param_value: Optional[str] = Field(None, max_length=500)
    status:      Optional[int] = None
    remark:      Optional[str] = None


class PerfParamRespSchema(BaseModel):
    """性能参数配置【响应】 - 响应体 Schema"""
    model_config = {"from_attributes": True}

    id:            int
    name:          str
    param_key:     str
    param_value:   str
    status:        int
    is_system:     int             # 1=系统参数（前端据此禁用编辑/删除按钮）
    remark:        Optional[str] = None
    creation_date: Optional[datetime] = None
    updation_date: Optional[datetime] = None
    operator_name: Optional[str] = None   # 操作人昵称（新建=创建人，修改后=修改人）

class PerfParamPageSchema(BaseSchema):
    """性能参数配置【分页】 - 分页响应体 Schema"""
    total:     int
    page:      int
    page_size: int
    items:     List[PerfParamRespSchema]