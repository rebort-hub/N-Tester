#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
from sqlalchemy import Column, String, Text, Integer, DateTime, BigInteger, JSON

from app.models.base import Base

"""
性能测试 - 压测场景模型
"""
class PerfScenarioModel(Base):
    """
    压测场景主表（perf_scenarios）。

    code 由后端自动生成，格式：JMX + 8位数字，如 JMX00000001。
    并发数（concurrent_count）不存数据库，由场景列表接口实时聚合：
      service.get_list 按 SUM(thread_count × workers) 聚合启用的 Stepping/Ultimate 子配置返回。
    """
    __tablename__ = 'perf_scenarios'

    name               = Column(String(200), nullable=False, comment='场景名称，中文说明，最长200字符')
    code               = Column(String(20),  nullable=False, unique=True, index=True,
                                comment='场景编号，JMX前缀+6位随机数字，后端自动生成，如 JMX452511')
    script_id          = Column(BigInteger,  nullable=False, comment='引用的 JMX 脚本文件 ID（perf_files.id）')
    script_name        = Column(String(200), nullable=True,  comment='JMX 脚本文件名快照（冗余，避免频繁联查）')
    test_type          = Column(String(50),  nullable=True,  comment='测试类型（字典 perf_test_category）')
    run_env            = Column(String(50),  nullable=True,  comment='运行环境（字典 sys_env）')
    is_distributed     = Column(Integer,     nullable=False, default=0,
                                comment='是否分布式（字典 perf_is_distributed）：0-否 1-是')
    node_count         = Column(Integer,     nullable=True,  default=1,  comment='节点数量，分布式时必填')
    status             = Column(Integer,     nullable=False, default=0,
                                comment='执行状态（字典 perf_case_status）：0待联调 1待开始 2进行中 3已完成 4已取消 5失败')
    progress           = Column(Integer,     nullable=False, default=0,  comment='压测进度（百分比 0-100）')
    estimated_duration = Column(Integer,     nullable=True,  comment='预计耗时（秒）')
    executed_at        = Column(DateTime(),  nullable=True,  comment='执行开始时间')
    error_info         = Column(Text,        nullable=True,  comment='执行过程中的错误日志')
    remark             = Column(Text,        nullable=True,  comment='备注')


class PerfScenarioConfigModel(Base):
    """
    压测场景子配置表（perf_scenario_configs）。

    一个场景可挂多条配置；concurrent_count 计算只取 status=1 的记录。
    loop_forever=1 时必须填 duration，loop_count 此时无效。
    is_distributed / node_count 已迁移至主表 perf_scenarios，子配置不再存储节点信息。
    """
    __tablename__ = 'perf_scenario_configs'

    scenario_id    = Column(BigInteger, nullable=False, index=True, comment='所属场景 ID（perf_scenarios.id）')
    thread_type    = Column(String(20),  nullable=False, default='1',
                            comment='线程组类型（字典 perf_thread_group_type）：1-ThreadGroup 2-SteppingThreadGroup 3-UltimateThreadGroup，创建后不可修改')
    status         = Column(Integer,    nullable=False, default=1,  comment='状态：1启用 0禁用')
    thread_count   = Column(Integer,    nullable=False,             comment='单节点线程数（>1 的正整数）；ultimate 类型时为各行 start_threads 之和')
    ramp_up_time   = Column(Integer,    nullable=True,              comment='Ramp-up 时间（秒），仅 standard 类型有效')
    loop_count     = Column(Integer,    nullable=True,              comment='循环次数；loop_forever=1 时忽略，仅 standard 类型有效')
    loop_forever   = Column(Integer,    nullable=False, default=0,  comment='永远循环：0-否 1-是，仅 standard 类型有效')
    duration       = Column(Integer,    nullable=True,              comment='持续时间（秒），loop_forever=1 时必填，仅 standard 类型有效')
    startup_delay  = Column(Integer,    nullable=True,              comment='启动延迟（秒），仅 standard 类型有效')
    # ── Stepping 特有字段（仅 thread_type=stepping 时写入，前缀 step_ 与标准字段区分）──
    step_initial_delay      = Column(Integer, nullable=True, comment='初始延迟（秒，Threads initial delay）')
    step_start_users_count  = Column(Integer, nullable=True, comment='每步新增线程数（Start users count）')
    step_start_users_burst  = Column(Integer, nullable=True, comment='突发加载线程数（Start users count burst）')
    step_start_users_period = Column(Integer, nullable=True, comment='每步时间间隔（秒，Start users period）')
    step_stop_users_count   = Column(Integer, nullable=True, comment='每步减少线程数（Stop users count）')
    step_stop_users_period  = Column(Integer, nullable=True, comment='停止步骤间隔（秒，Stop users period）')
    step_flight_time        = Column(Integer, nullable=True, comment='保持满载时间（秒，flighttime）')
    step_ramp_up            = Column(Integer, nullable=True, comment='爬坡时间（秒，rampUp）')
    # ── Ultimate 特有字段 ──
    ultimate_rows  = Column(JSON, nullable=True,
                            comment='UltimateThreadGroup 阶段行数组，每项含 start_threads/initial_delay/startup_time/hold_load_for/shutdown_time')
    tg_name        = Column(String(200), nullable=True,              comment='线程组名称（来自JMX testname属性，创建时由前端从解析配置传入）')
    estimated_duration = Column(Integer, nullable=True,              comment='该子配置预计耗时（秒），选填；场景总耗时 = 各启用子配置耗时之和')
    remark         = Column(Text,       nullable=True,              comment='备注')