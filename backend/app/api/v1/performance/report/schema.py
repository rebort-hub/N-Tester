#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

"""
性能测试 - 压测报告 Schema
"""


# ====================== 通用 ID 请求体（删除 / 强制停止 / 恢复 共用）======================

class PerfReportIdReqSchema(BaseModel):
    """压测报告操作通用请求体（删除 / 强制停止 / 恢复均只需 id）"""
    id: int = Field(..., gt=0, description='报告主键 ID')


# ====================== 列表查询 ======================

class PerfReportListRespSchema(BaseModel):
    """压测报告列表条目【响应】体"""
    model_config = {"from_attributes": True}

    id:            int
    report_code:   str
    scenario_id:   int
    scenario_code: str
    scenario_name: str
    report_name:   str
    file_size:     int
    report_status: int
    trigger_type:  int
    remark:        Optional[str]      = None
    generated_at:  Optional[datetime] = None
    creator:       Optional[str]      = None
    creator_id:    Optional[int]      = None
    creation_date: Optional[datetime] = None