#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
import math

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseCRUD
from .model import PerfScenarioConfigModel, PerfScenarioModel

"""
性能测试 - 压测场景 CRUD
"""
def _calc_config_duration(config: PerfScenarioConfigModel) -> tuple[int, bool]:
    """计算单条启用子配置的已知耗时（秒）和是否含有未知时间段。

    - estimated_duration 已填写：直接使用，无未知
    - 标准/SetUp（'0'/'1'）loop_forever + duration：ramp_up_time + startup_delay + duration
    - 标准/SetUp（'0'/'1'）loop_count：ramp_up_time + startup_delay（执行段未知），has_unknown=True
    - SteppingThreadGroup（'2'）：由爬坡/满载/减压参数精确计算，无未知
    - UltimateThreadGroup（'3'）：各 stage 总时长的最大值，无未知
    """
    if config.estimated_duration is not None:
        return config.estimated_duration, False

    tt = config.thread_type or '1'

    if tt in ('0', '1'):
        known = (config.ramp_up_time or 0) + (config.startup_delay or 0)
        if config.loop_forever and (config.duration or 0) > 0:
            return known + (config.duration or 0), False
        return known, True

    if tt == '2':
        max_t  = config.thread_count or 0
        burst  = config.step_start_users_burst or 0
        count  = config.step_start_users_count or 0
        period = config.step_start_users_period or 0
        ramp   = config.step_ramp_up or 0
        s_cnt  = config.step_stop_users_count or 0
        s_per  = config.step_stop_users_period or 0
        flight = config.step_flight_time or 0
        init   = config.step_initial_delay or 0
        steps_up   = math.ceil((max_t - burst) / count) if count > 0 and max_t > burst else 0
        steps_down = math.ceil(max_t / s_cnt) if s_cnt > 0 and max_t > 0 else 0
        # period 是前批爬坡结束后再等待的间隔，每批（含初始burst）各自占用 ramp 秒
        # 总时长 = 初始延迟 + (steps_up+1)×ramp + steps_up×period + 满载持续 + 减压
        return init + (steps_up + 1) * ramp + steps_up * period + flight + steps_down * s_per, False

    if tt == '3':
        rows = config.ultimate_rows or []
        if not rows:
            return 0, False
        row_times = [
            (r.get('initial_delay') or 0) + (r.get('startup_time') or 0) +
            (r.get('hold_load_for') or 0) + (r.get('shutdown_time') or 0)
            for r in rows
        ]
        return max(row_times) if row_times else 0, False

    return 0, False


class PerfScenarioConfigCRUD(BaseCRUD):
    """场景子配置 CRUD。

    封装公共查询，供 PerfScenarioService 和 PerfScenarioConfigService 共用，
    避免两个 Service 各自重复定义相同逻辑。
    """

    def __init__(self, db: AsyncSession):
        super().__init__(PerfScenarioConfigModel, db)

    async def get_configs(self, scenario_id: int) -> list[PerfScenarioConfigModel]:
        """查询场景下所有未软删除的子配置（含启用与禁用两种状态）。

        Args:
            scenario_id: 场景主键 ID
        Returns:
            list[PerfScenarioConfigModel]: 按 id 升序排列的子配置列表；无数据时返回空列表
        """
        items, _ = await self.get_list_crud(
            conditions=[
                PerfScenarioConfigModel.scenario_id == scenario_id,
                PerfScenarioConfigModel.enabled_flag == 1,
            ],
            order_by=[PerfScenarioConfigModel.id.asc()],
            limit=1000,
        )
        return items

    async def get_sub_duration_stats_map(
        self, scenario_ids: list[int]
    ) -> tuple[dict[int, int | None], set[int]]:
        """批量聚合各场景启用子配置的预计耗时统计。

        计算规则（per-config）：
          - estimated_duration 已填写：直接使用
          - 标准线程组 loop_count：ramp_up_time + startup_delay 为已知部分，标记未知
          - 标准线程组 loop_forever + duration：ramp_up_time + startup_delay + duration
          - Stepping/Ultimate：由参数精确计算，无未知部分

        Args:
            scenario_ids: 场景主键 ID 列表（空列表直接返回空结构）
        Returns:
            (known_times_map, has_unknown_set)
              known_times_map:  {scenario_id: known_secs_or_none}
              has_unknown_set:  含有至少一条执行时长不确定子配置的 scenario_id 集合
        """
        if not scenario_ids:
            return {}, set()

        stmt = (
            select(PerfScenarioConfigModel)
            .where(and_(
                PerfScenarioConfigModel.enabled_flag == 1,
                PerfScenarioConfigModel.status == 1,
                PerfScenarioConfigModel.scenario_id.in_(scenario_ids),
            ))
        )
        result = await self.db.execute(stmt)
        configs = result.scalars().all()

        totals: dict[int, int] = {}
        has_unknown_set: set[int] = set()
        for config in configs:
            sid = config.scenario_id
            secs, unknown = _calc_config_duration(config)
            totals[sid] = totals.get(sid, 0) + secs
            if unknown:
                has_unknown_set.add(sid)

        known_times_map: dict[int, int | None] = {
            sid: (v if v > 0 else None) for sid, v in totals.items()
        }
        return known_times_map, has_unknown_set

    async def get_concurrent_count_map(self, scenario_ids: list[int]) -> dict[int, int]:
        """批量计算多个场景的并发数（不存数据库，按需实时聚合）。

        计算规则：
            SUM(thread_count × workers) 累加每个场景下启用(status=1)的
            ThreadGroup('1')/Stepping('2')/Ultimate('3') 子配置；workers = is_distributed=1 时 node_count，否则 1。
            SetUp/TearDown('0') 是预/后处理逻辑，不参与并发数累加。
            Ultimate 类型的 thread_count 由后端写入时自动汇总各 stage 的 start_threads（model.py 注释）。

        Args:
            scenario_ids: 场景主键 ID 列表（空列表直接返回 {}）
        Returns:
            dict[int, int]: {scenario_id: concurrent_count}；未匹配到子配置的场景不在字典中（调用方自行兜底为 0）
        """
        if not scenario_ids:
            return {}

        workers_expr = case(
            (PerfScenarioModel.is_distributed == 1, PerfScenarioModel.node_count),
            else_=1,
        )
        stmt = (
            select(
                PerfScenarioConfigModel.scenario_id,
                func.coalesce(
                    func.sum(PerfScenarioConfigModel.thread_count * workers_expr),
                    0,
                ).label('concurrent_count'),
            )
            .join(PerfScenarioModel, PerfScenarioModel.id == PerfScenarioConfigModel.scenario_id)
            .where(and_(
                PerfScenarioConfigModel.enabled_flag == 1,
                PerfScenarioConfigModel.status == 1,
                PerfScenarioConfigModel.thread_type.in_(['1', '2', '3']),
                PerfScenarioConfigModel.scenario_id.in_(scenario_ids),
            ))
            .group_by(PerfScenarioConfigModel.scenario_id)
        )
        result = await self.db.execute(stmt)
        return {sid: int(cc or 0) for sid, cc in result.all()}
