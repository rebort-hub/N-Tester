#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
from sqlalchemy import Column, String, Text, Integer, DateTime, BigInteger

from app.models.base import Base

"""
性能测试 - 定时任务模型
"""


class PerfSchedulerModel(Base):
    """
    定时任务主表（perf_schedulers）。

    task_status 取字典 perf_scheduler_status：0-待触发 1-进行中 2-已结束 3-已取消。
    场景编号和脚本名通过 scenario_id JOIN perf_scenarios 实时获取，不存快照。
    """
    __tablename__ = 'perf_schedulers'

    name        = Column(String(100),  nullable=False,             comment='任务名称，最长100字符')
    scenario_id = Column(BigInteger,   nullable=False, index=True, comment='关联压测场景ID（perf_scenarios.id）')
    is_active   = Column(Integer,      nullable=False, default=1,  comment='启用状态：1-启用 0-禁用')
    task_status = Column(Integer,      nullable=False, default=0,  comment='任务状态（字典 perf_scheduler_status）：0-待触发 1-进行中 2-已结束 3-已取消')
    plan_time   = Column(DateTime(),   nullable=False,             comment='计划执行时间')
    end_time    = Column(DateTime(),   nullable=True,              comment='实际结束时间（调度完成后写入）')
    remark      = Column(Text,         nullable=True,              comment='备注')