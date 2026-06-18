#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas

from __future__ import annotations
import json
from datetime import datetime

from app.corelibs.logger import logger

"""
性能测试 - 定时任务 APScheduler 集成层

对外接口：
  register_scheduler_job    新建/更新定时任务时注册 DateTrigger 一次性触发
  remove_scheduler_job      取消/删除任务时从调度器移除
  load_perf_pending_jobs    应用启动时从 DB 恢复所有待触发任务（MemoryJobStore 重启后清空）

内部触发回调：
  run_perf_scheduler_job    到达 plan_time 后：校验 → 进行中 → 驱动 execute_sse → 失败回退

任务状态流转（由本模块 + perf_log_collector 共同驱动）：
  待触发(0) --[plan_time 到达]--> 进行中(1) --[JMeter 进程结束]--> 已结束(2)
  待触发(0) --[用户禁用/取消]--> 移除 APScheduler 任务
  进行中(1) --[execute_sse error]--> 回退待触发(0)，remark 记录原因
"""

def _job_id(scheduler_id: int) -> str:
    """APScheduler job_id 命名空间前缀，避免与其他模块任务冲突。"""
    return f"perf_sched_{scheduler_id}"


def register_scheduler_job(scheduler_id: int, plan_time: datetime | str, is_active: int) -> None:
    """注册（或重注册）定时压测触发任务。

    - is_active=0：仅移除旧任务，不注册新任务
    - 使用 MemoryJobStore + AsyncIOExecutor：异步函数无需 pickle
    - misfire_grace_time=300：进程重启后 5 分钟内的漏触发仍会补执行
    - 由 load_perf_pending_jobs 保证重启后从 DB 恢复，无需 SQLAlchemyJobStore

    Args:
        scheduler_id: 定时任务主键 ID
        plan_time:    计划执行时间（datetime 或 ISO 字符串）
        is_active:    启用状态（1=启用 0=禁用）
    """
    from app.api.v1.task_scheduler.scheduler import get_scheduler
    from apscheduler.triggers.date import DateTrigger

    scheduler = get_scheduler()
    job_id = _job_id(scheduler_id)

    # 先移除旧任务（如有），避免重复触发
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    if not is_active:
        logger.info(f"[PerfScheduler] 任务已禁用，跳过注册 scheduler_id={scheduler_id}")
        return

    # 字符串时间解析（兼容 YYYY-MM-DDTHH:mm:ss 和 YYYY-MM-DD HH:mm:ss）
    if isinstance(plan_time, str):
        normalized = plan_time.replace("T", " ").replace("Z", "")
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
            try:
                plan_time = datetime.strptime(normalized, fmt)
                break
            except ValueError:
                continue

    trigger = DateTrigger(run_date=plan_time, timezone="Asia/Shanghai")
    scheduler.add_job(
        run_perf_scheduler_job,
        trigger=trigger,
        id=job_id,
        args=[scheduler_id],
        replace_existing=True,
        jobstore="default",       # MemoryJobStore，异步函数无需序列化
        executor="default",       # AsyncIOExecutor
        misfire_grace_time=300,   # 5 分钟宽限期
    )
    logger.info(f"[PerfScheduler] 任务已注册 scheduler_id={scheduler_id} plan_time={plan_time}")


def remove_scheduler_job(scheduler_id: int) -> None:
    """从 APScheduler 移除定时任务（取消/删除时调用）。

    DateTrigger 任务触发后自动从调度器移除，重复调用无副作用。
    """
    try:
        from app.api.v1.task_scheduler.scheduler import get_scheduler
        scheduler = get_scheduler()
        job_id = _job_id(scheduler_id)
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info(f"[PerfScheduler] 任务已移除 scheduler_id={scheduler_id}")
    except Exception as e:
        logger.warning(f"[PerfScheduler] 移除任务失败 scheduler_id={scheduler_id}: {e}")


async def run_perf_scheduler_job(scheduler_id: int) -> None:
    """APScheduler 触发回调：到达 plan_time 后驱动压测启动。

    流程：
      1. 重新校验记录状态（task_status=0 且 is_active=1），防止重复触发或误触发
      2. 更新 task_status=1（进行中）
      3. 消费 execute_sse 生成器，驱动 Stage1~3（注入参数 → 上传 JMX → nohup 启动）
      4. 成功（done 事件）：task_status 保持 1，由 perf_log_collector 在 JMeter 进程结束后更新为 2
      5. 失败（error 事件或异常）：task_status 回退至 0，remark 记录失败原因供用户排查

    Args:
        scheduler_id: 定时任务主键 ID
    """
    from app.db.sqlalchemy import async_session_factory
    from app.core.base_crud import BaseCRUD
    from .model import PerfSchedulerModel

    logger.info(f"[PerfScheduler] 触发回调开始 scheduler_id={scheduler_id}")

    # ── 1. 校验 + 更新进行中 ──────────────────────────────────────────────
    scenario_id: int | None = None
    async with async_session_factory() as db:
        crud = BaseCRUD(PerfSchedulerModel, db)
        obj = await crud.get_by_id_crud(scheduler_id)
        # 判断定时任务记录存在
        if not obj or not obj.enabled_flag:
            logger.warning(f"[PerfScheduler] 任务记录不存在，跳过 scheduler_id={scheduler_id}")
            return
        # 判断定时任务状态=待触发（0）且开启状态
        if obj.task_status != 0 or not obj.is_active:
            logger.info(
                f"[PerfScheduler] 任务跳过（状态不符）"
                f" scheduler_id={scheduler_id}"
                f" task_status={obj.task_status} is_active={obj.is_active}"
            )
            return

        await crud.update_crud(scheduler_id, {'task_status': 1})
        await db.commit()
        scenario_id = obj.scenario_id

    # ── 2. 驱动压测启动（消费 execute_sse 生成器）────────────────────────
    error_msg: str | None = None
    try:
        from app.api.v1.performance.scenario.service import PerfScenarioService

        async with async_session_factory() as db:
            svc = PerfScenarioService(db)
            async for raw_event in svc.execute_sse(scenario_id, 'execute'):
                # SSE 格式："data: {...}\n\n"，逐行解析 data 字段
                for line in raw_event.split("\n"):
                    if not line.startswith("data:"):
                        continue
                    try:
                        evt = json.loads(line[5:].strip())
                        evt_type = evt.get('type')
                        if evt_type == 'error':
                            error_msg = evt.get('message') or '执行失败'
                        elif evt_type == 'done':
                            logger.info(
                                f"[PerfScheduler] JMeter 已后台启动"
                                f" scheduler_id={scheduler_id} scenario_id={scenario_id}"
                            )
                    except Exception:
                        pass
    except Exception as e:
        logger.exception(f"[PerfScheduler] execute_sse 异常 scheduler_id={scheduler_id}")
        error_msg = str(e)[:400]

    # ── 3. 失败：task_status=4，is_active=0，remark 记录原因 ─────────────
    if error_msg:
        logger.error(f"[PerfScheduler] 压测启动失败 scheduler_id={scheduler_id}: {error_msg}")
        async with async_session_factory() as db:
            crud = BaseCRUD(PerfSchedulerModel, db)
            await crud.update_crud(scheduler_id, {
                'task_status': 4,
                'is_active':   0,
                'remark': f'[自动触发失败] {error_msg[:400]}',
            })
            await db.commit()


async def load_perf_pending_jobs() -> None:
    """应用启动时，从 DB 恢复所有待触发任务到 APScheduler。

    MemoryJobStore 在进程重启后清空，通过此函数补回尚未执行的任务。
    仅恢复 task_status=0（待触发）且 is_active=1（启用）的记录。
    """
    from sqlalchemy import select, and_
    from app.db.sqlalchemy import async_session_factory
    from .model import PerfSchedulerModel

    try:
        async with async_session_factory() as db:
            stmt = (
                select(PerfSchedulerModel)
                .where(and_(
                    PerfSchedulerModel.task_status == 0,
                    PerfSchedulerModel.is_active == 1,
                    PerfSchedulerModel.enabled_flag == 1,
                ))
            )
            rows = (await db.execute(stmt)).scalars().all()

        count = 0
        for row in rows:
            try:
                register_scheduler_job(row.id, row.plan_time, row.is_active)
                count += 1
            except Exception as e:
                logger.warning(f"[PerfScheduler] 恢复任务失败 id={row.id}: {e}")

        logger.info(f"[PerfScheduler] 已恢复 {count} 个待触发定时任务")
    except Exception as e:
        logger.warning(f"[PerfScheduler] 恢复定时任务失败: {e}")