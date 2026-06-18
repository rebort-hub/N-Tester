#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas

from typing import Annotated, List, Literal, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

"""
性能测试 - 压测场景 Schema
子配置按 thread_type 拆分为 3 套 Schema，通过判别联合体（discriminated union）
让 FastAPI/Pydantic 按 thread_type 字段自动路由到对应类型，OpenAPI 文档展示 oneOf 结构。
SetUp('0') 与 ThreadGroup('1') 参数完全相同，合并为同一个 Schema 类处理。

  '0'/'1' → StandardThreadGroup（SetUp 与标准线程组，字段相同）
  '2'      → SteppingThreadGroup（阶梯加压）
  '3'      → UltimateThreadGroup（自定义阶段）
"""
# ====================== UltimateThreadGroup 单行配置 ======================

class UltimateRowReqSchema(BaseModel):
    """UltimateThreadGroup 的单行阶段配置，对应 oper_jmx.UltimateConfig 字段。
    字段名与 JSON 存储格式一致，可直接存入 ultimate_rows（JSON 列）。
    """
    start_threads: int = Field(..., ge=1,  description='该阶段线程数')
    initial_delay: int = Field(0,  ge=0,  description='初始延迟（秒）')
    startup_time:  int = Field(0,  ge=0,  description='爬坡时间（秒）')
    hold_load_for: int = Field(0,  ge=0,  description='持续时间（秒）')
    shutdown_time: int = Field(0,  ge=0,  description='停止时间（秒）')


# ====================== 子配置 — 新建（3 种类型）======================

class _PerfScenarioConfigStandardCreateBase(BaseModel):
    """SetUp/ThreadGroup 标准线程组新建请求公共字段基类（不含 thread_type，由子类指定 Literal）"""
    tg_name:        Optional[str] = Field(None, max_length=200, description='线程组名称（来自JMX，前端解析后传入）')
    status:         int           = Field(1,    description='状态：1启用 0禁用')
    thread_count:   int           = Field(..., ge=1, description='单节点线程数')
    ramp_up_time:   Optional[int] = Field(None, ge=0,  description='Ramp-up 时间（秒）')
    loop_count:     Optional[int] = Field(None, ge=0,  description='循环次数，loop_forever=1 时忽略')
    loop_forever:   int           = Field(0,    description='永远循环：0-否 1-是')
    duration:       Optional[int] = Field(None, ge=1,  description='持续时间（秒），loop_forever=1 时必填')
    startup_delay:  Optional[int] = Field(None, ge=0,  description='启动延迟（秒）')
    estimated_duration: Optional[int] = Field(None, ge=1, description='该子配置预计耗时（秒），选填')
    remark:         Optional[str] = None

    @model_validator(mode='after')
    def validate_standard(self):
        if self.loop_forever == 1 and not self.duration:
            raise ValueError('勾选永远循环时 duration 必填')
        return self


class PerfScenarioConfigCreateStandardReqSchema(_PerfScenarioConfigStandardCreateBase):
    """SetUp/ThreadGroup 标准线程组子配置【新建】请求体，两种类型参数完全相同，统一处理"""
    thread_type: Literal['0', '1'] = '1'


class PerfScenarioConfigCreateSteppingReqSchema(BaseModel):
    """SteppingThreadGroup（阶梯加压）子配置【新建】请求体"""
    thread_type:             Literal['2'] = '2'
    tg_name:                 Optional[str] = Field(None, max_length=200)
    status:                  int           = Field(1)
    thread_count:            int           = Field(..., ge=1, description='最大总线程数（SteppingThreadGroup.num_threads）')
    step_initial_delay:      int           = Field(0,  ge=0, description='初始延迟（秒）')
    step_start_users_count:  int           = Field(..., ge=1, description='每步新增线程数')
    step_start_users_burst:  int           = Field(0,  ge=0, description='突发加载线程数')
    step_start_users_period: int           = Field(..., ge=1, description='每步时间间隔（秒）')
    step_stop_users_count:   int           = Field(0,  ge=0, description='每步减少线程数')
    step_stop_users_period:  int           = Field(0,  ge=0, description='停止步骤间隔（秒）')
    step_flight_time:        int           = Field(0,  ge=0, description='保持满载时间（秒）')
    step_ramp_up:            int           = Field(0,  ge=0, description='爬坡时间（秒）')
    estimated_duration:      Optional[int] = Field(None, ge=1, description='该子配置预计耗时（秒），选填')
    remark:                  Optional[str] = None


class PerfScenarioConfigCreateUltimateReqSchema(BaseModel):
    """UltimateThreadGroup（自定义阶段）子配置【新建】请求体。
    thread_count 无需传入，由后端从 ultimate_rows 自动汇总 start_threads 之和。
    """
    thread_type:    Literal['3'] = '3'
    tg_name:        Optional[str] = Field(None, max_length=200)
    status:         int           = Field(1)
    ultimate_rows:  List[UltimateRowReqSchema] = Field(..., min_length=1,
                    description='阶段行列表，至少一行')
    estimated_duration: Optional[int] = Field(None, ge=1, description='该子配置预计耗时（秒），选填')
    remark:         Optional[str] = None


# 新建请求判别联合体 —— Pydantic 按 thread_type 自动路由
PerfScenarioConfigCreateReqSchema = Annotated[
    Union[
        PerfScenarioConfigCreateStandardReqSchema,
        PerfScenarioConfigCreateSteppingReqSchema,
        PerfScenarioConfigCreateUltimateReqSchema,
    ],
    Field(discriminator='thread_type')
]


# ====================== 子配置 — 修改（3 种类型）======================
# thread_type 作为必填字段用于判别联合体路由，服务端不会将其写入 DB（已在 model_dump exclude 中排除）

class _PerfScenarioConfigStandardUpdateBase(BaseModel):
    """SetUp/ThreadGroup 标准线程组修改请求公共字段基类"""
    tg_name:        Optional[str] = Field(None, max_length=200)
    status:         Optional[int] = None
    thread_count:   Optional[int] = Field(None, ge=1)
    ramp_up_time:   Optional[int] = Field(None, ge=0)
    loop_count:     Optional[int] = Field(None, ge=0)
    loop_forever:   Optional[int] = None
    duration:       Optional[int] = Field(None, ge=1)
    startup_delay:  Optional[int] = Field(None, ge=0)
    estimated_duration: Optional[int] = Field(None, ge=1, description='该子配置预计耗时（秒），选填')
    remark:         Optional[str] = None


class PerfScenarioConfigUpdateStandardReqSchema(_PerfScenarioConfigStandardUpdateBase):
    """SetUp/ThreadGroup 标准线程组子配置【修改】请求体，两种类型参数完全相同，统一处理"""
    thread_type: Literal['0', '1']


class PerfScenarioConfigUpdateSteppingReqSchema(BaseModel):
    """SteppingThreadGroup（阶梯加压）子配置【修改】请求体"""
    thread_type:             Literal['2']
    tg_name:                 Optional[str] = Field(None, max_length=200)
    status:                  Optional[int] = None
    thread_count:            Optional[int] = Field(None, ge=1)
    step_initial_delay:      Optional[int] = Field(None, ge=0)
    step_start_users_count:  Optional[int] = Field(None, ge=1)
    step_start_users_burst:  Optional[int] = Field(None, ge=0)
    step_start_users_period: Optional[int] = Field(None, ge=1)
    step_stop_users_count:   Optional[int] = Field(None, ge=0)
    step_stop_users_period:  Optional[int] = Field(None, ge=0)
    step_flight_time:        Optional[int] = Field(None, ge=0)
    step_ramp_up:            Optional[int] = Field(None, ge=0)
    estimated_duration:      Optional[int] = Field(None, ge=1, description='该子配置预计耗时（秒），选填')
    remark:                  Optional[str] = None


class PerfScenarioConfigUpdateUltimateReqSchema(BaseModel):
    """UltimateThreadGroup（自定义阶段）子配置【修改】请求体"""
    thread_type:    Literal['3']
    tg_name:        Optional[str] = Field(None, max_length=200)
    status:         Optional[int] = None
    ultimate_rows:  Optional[List[UltimateRowReqSchema]] = Field(None, min_length=1,
                    description='阶段行列表，传入时至少一行')
    estimated_duration: Optional[int] = Field(None, ge=1, description='该子配置预计耗时（秒），选填')
    remark:         Optional[str] = None


# 修改请求判别联合体
PerfScenarioConfigUpdateReqSchema = Annotated[
    Union[
        PerfScenarioConfigUpdateStandardReqSchema,
        PerfScenarioConfigUpdateSteppingReqSchema,
        PerfScenarioConfigUpdateUltimateReqSchema,
    ],
    Field(discriminator='thread_type')
]


# ====================== 子配置 — 随场景主表一起修改（含 id）======================

class PerfScenarioConfigInScenarioUpdateStandardReqSchema(PerfScenarioConfigUpdateStandardReqSchema):
    """嵌套在场景修改请求中的标准线程组子配置条目（SetUp/ThreadGroup），必须携带 id"""
    id: int = Field(..., gt=0)


class PerfScenarioConfigInScenarioUpdateSteppingReqSchema(PerfScenarioConfigUpdateSteppingReqSchema):
    """嵌套在场景修改请求中的 SteppingThreadGroup 子配置条目，必须携带 id"""
    id: int = Field(..., gt=0)


class PerfScenarioConfigInScenarioUpdateUltimateReqSchema(PerfScenarioConfigUpdateUltimateReqSchema):
    """嵌套在场景修改请求中的 UltimateThreadGroup 子配置条目，必须携带 id"""
    id: int = Field(..., gt=0)


PerfScenarioConfigInScenarioUpdateReqSchema = Annotated[
    Union[
        PerfScenarioConfigInScenarioUpdateStandardReqSchema,
        PerfScenarioConfigInScenarioUpdateSteppingReqSchema,
        PerfScenarioConfigInScenarioUpdateUltimateReqSchema,
    ],
    Field(discriminator='thread_type')
]


# ====================== 子配置 — 响应（3 种类型）======================

class _PerfScenarioConfigBaseRespSchema(BaseModel):
    """子配置响应公共字段（3 种类型共用），不直接对外暴露"""
    model_config = {"from_attributes": True}
    id:             int
    tg_name:        Optional[str] = None
    thread_type:    str
    status:         int
    thread_count:   int
    estimated_duration: Optional[int] = None
    remark:         Optional[str] = None
    creation_date:  Optional[datetime] = None
    updation_date:  Optional[datetime] = None


class PerfScenarioConfigStandardRespSchema(_PerfScenarioConfigBaseRespSchema):
    """ThreadGroup（标准）子配置【响应】体"""
    ramp_up_time:   Optional[int] = None
    loop_count:     Optional[int] = None
    loop_forever:   int = 0
    duration:       Optional[int] = None
    startup_delay:  Optional[int] = None


class PerfScenarioConfigSteppingRespSchema(_PerfScenarioConfigBaseRespSchema):
    """SteppingThreadGroup（阶梯加压）子配置【响应】体"""
    step_initial_delay:      Optional[int] = None
    step_start_users_count:  Optional[int] = None
    step_start_users_burst:  Optional[int] = None
    step_start_users_period: Optional[int] = None
    step_stop_users_count:   Optional[int] = None
    step_stop_users_period:  Optional[int] = None
    step_flight_time:        Optional[int] = None
    step_ramp_up:            Optional[int] = None


class PerfScenarioConfigUltimateRespSchema(_PerfScenarioConfigBaseRespSchema):
    """UltimateThreadGroup（自定义阶段）子配置【响应】体"""
    ultimate_rows: Optional[List[dict]] = None


# ====================== 压测场景主表 ======================

class PerfScenarioCreateReqSchema(BaseModel):
    """场景【新建】请求体 — POST /add
    configs 支持混合 3 种子配置类型，按 thread_type 各自校验。
    """
    name:               str           = Field(..., max_length=200, description='场景名称')
    script_id:          int           = Field(..., gt=0, description='JMX 脚本文件 ID')
    test_type:          Optional[str] = Field(None, description='测试类型（字典 perf_test_category）')
    run_env:            Optional[str] = Field(None, description='运行环境（字典 sys_env）')
    is_distributed:     int           = Field(0,    description='是否分布式：0-否 1-是')
    node_count:         Optional[int] = Field(None, ge=1, description='节点数量，分布式时必填')
    estimated_duration: Optional[int] = Field(None, ge=1, description='预计耗时（秒）')
    remark:             Optional[str] = Field(None, description='备注')
    configs:            Optional[List[PerfScenarioConfigCreateReqSchema]] = Field(
        None, description='同步创建的子配置列表，每条按 thread_type 独立校验'
    )

    @model_validator(mode='after')
    def validate_scenario(self):
        if self.is_distributed == 1 and not self.node_count:
            raise ValueError('分布式模式下 node_count 必填')
        return self


class PerfScenarioUpdateReqSchema(BaseModel):
    """场景【修改】请求体 — PUT /update/{scenario_id}"""
    name:               Optional[str] = Field(None, max_length=200)
    script_id:          Optional[int] = Field(None, gt=0)
    test_type:          Optional[str] = None
    run_env:            Optional[str] = None
    is_distributed:     Optional[int] = None
    node_count:         Optional[int] = Field(None, ge=1)
    estimated_duration: Optional[int] = Field(None, ge=1)
    remark:             Optional[str] = None
    configs:            Optional[List[PerfScenarioConfigInScenarioUpdateReqSchema]] = Field(
        None, description='高级设置开启时同步修改子配置，每条必须含 id 和 thread_type'
    )


class PerfScenarioListRespSchema(BaseModel):
    """场景列表条目【响应】体 — GET /list

    concurrent_count 由 service.get_list 动态聚合注入：
      SUM(thread_count × (is_distributed ? node_count : 1))
      WHERE status=1 AND thread_type IN ('2','3') AND enabled_flag=1
    （Stepping/Ultimate 类型；Ultimate 的 thread_count 已在写入时汇总各 stage 的 start_threads）
    """
    model_config = {"from_attributes": True}

    id:                 int
    name:               str
    code:               str
    script_id:          int
    script_name:        Optional[str] = None
    test_type:          Optional[str] = None
    run_env:            Optional[str] = None
    is_distributed:     int = 0
    node_count:         Optional[int] = None
    status:             int
    progress:           int
    estimated_duration: Optional[int] = None
    has_unknown_times:  bool = False  # 存在启用子配置未填写预计耗时时为 True，总耗时不完整
    known_times:        Optional[int] = None  # 各启用子配置 estimated_duration 之和（None 表示全部未填或无启用配置）
    executed_at:        Optional[datetime] = None
    remark:             Optional[str] = None
    error_info:         Optional[str] = None
    creation_date:      Optional[datetime] = None
    created_by:         Optional[int] = None
    operator_name:      Optional[str] = None
    concurrent_count:   int = 0


# ====================== sync_stats 接口 ======================

class ConfigSyncStatsReqSchema(BaseModel):
    """切换子配置启用状态并同步刷新场景统计字段请求体。"""
    scenario_id: int = Field(..., gt=0, description='场景主键 ID')
    config_id:   int = Field(..., gt=0, description='子配置主键 ID')
    status:      int = Field(..., ge=0, le=1, description='目标状态：1=启用 0=禁用')
    thread_type: str = Field(..., description="线程组类型（用于互斥判断）：'0'|'1'|'2'|'3'")


class ConfigSyncStatsRespSchema(BaseModel):
    """sync_stats 响应：更新后的启用子配置 + 场景统计字段"""
    configs:            List[dict]
    concurrent_count:   int           = 0
    known_times:        Optional[int] = None   # 可精确计算的耗时秒数（None 表示无可算线程组）
    has_unknown_times:  bool          = False  # True 表示存在循环次数线程组，estimated_duration 为估算值


# ====================== 联调 / 执行接口 ======================

class ScenarioUpdateStatusReqSchema(BaseModel):
    """更新场景状态 — PUT /updateStatus
    当前支持：status=1（确认联调通过，待开始）。
    """
    scenario_id: int = Field(..., gt=0, description='场景主键 ID')
    status:      int = Field(..., ge=0, le=5, description='目标状态：1=确认联调通过（待开始）')


class ScenarioExecuteReqSchema(BaseModel):
    """联调与执行【请求】体 — POST /{scenario_id}/execute

    联调参数不在此处传入，由后端从 perf_config_params 读取预置 JSON 配置：
      '1'（ThreadGroup）+ 非负载测试 → BASE_THREAD_GROUP_INSPECT
      '1'（ThreadGroup）+ 负载测试   → LOAD_THREAD_GROUP_INSPECT
      '2'（SteppingThreadGroup）     → STEPPING_THREAD_GROUP_INSPECT
      '3'（UltimateThreadGroup）     → ULTIMATE_THREAD_GROUP_INSPECT
    """
    action: Literal['inspect', 'execute', 'recover'] = Field(
        ..., description='inspect=联调  execute=正式执行  recover=恢复执行（不重传JMX，直接SSH启动）'
    )