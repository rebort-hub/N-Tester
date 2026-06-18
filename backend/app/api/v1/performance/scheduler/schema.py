#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

"""
性能测试 - 定时任务 Schema
"""


# ====================== 新建 ======================

class PerfSchedulerCreateReqSchema(BaseModel):
    """定时任务【新建】请求体"""
    name:        str           = Field(..., max_length=100, description='任务名称，最长100字符')
    scenario_id: int           = Field(..., gt=0,           description='关联压测场景ID')
    is_active:   int           = Field(1,                   description='启用状态：1-启用 0-禁用')
    plan_time:   datetime      = Field(...,                  description='计划执行时间')
    remark:      Optional[str] = Field(None,                description='备注')


# ====================== 修改 ======================

class PerfSchedulerUpdateReqSchema(BaseModel):
    """定时任务【修改】请求体；id 必填，其余字段按需传入"""
    id:          int            = Field(..., gt=0,           description='任务主键ID')
    name:        Optional[str]  = Field(None, max_length=100, description='任务名称')
    scenario_id: Optional[int]  = Field(None, gt=0,          description='关联压测场景ID')
    is_active:   Optional[int]  = Field(None,                description='启用状态：1-启用 0-禁用')
    plan_time:   Optional[datetime] = Field(None,            description='计划执行时间')
    remark:      Optional[str]  = Field(None,                description='备注')


# ====================== 取消 ======================

class PerfSchedulerCancelReqSchema(BaseModel):
    """定时任务【取消】请求体"""
    id: int = Field(..., gt=0, description='任务主键ID')


# ====================== 列表响应 ======================

class PerfSchedulerListRespSchema(BaseModel):
    """定时任务列表条目【响应】体"""
    model_config = {"from_attributes": True}

    id:            int
    name:          str
    scenario_id:   int
    scenario_code: Optional[str]      = None  # JOIN perf_scenarios.code
    script_name:   Optional[str]      = None  # JOIN perf_scenarios.script_name
    is_active:     int
    task_status:   int
    plan_time:     Optional[datetime] = None
    end_time:      Optional[datetime] = None
    remark:        Optional[str]      = None
    creation_date: Optional[datetime] = None
    created_by:    Optional[int]      = None
    operator_name: Optional[str]      = None  # JOIN sys_users.username