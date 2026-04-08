from __future__ import annotations

import uuid
import inspect
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Optional

from apscheduler.events import (
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_MISSED,
    EVENT_JOB_SUBMITTED,
    JobExecutionEvent,
    JobSubmissionEvent,
)
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import create_engine
from app.corelibs.logger import logger
from config import config


_scheduler: Optional[AsyncIOScheduler] = None
_execution_cache: dict[str, dict[str, Any]] = {}


def _to_json_safe(value: Any) -> Any:
    
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if inspect.iscoroutine(value):
        return repr(value)
    if isinstance(value, dict):
        return {str(k): _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_json_safe(v) for v in value]
    return repr(value)


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        # 为生产环境提供可持久化的调度内核：JobStore + Executors + 事件监听日志
        # 注意：SQLAlchemyJobStore 使用同步 engine/url（避免与异步引擎耦合）
        sync_engine = create_engine(config.DATABASE_URI_SYNC, pool_pre_ping=True)
        _scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        _scheduler.configure(
            jobstores={
                "default": MemoryJobStore(),
                "sqlalchemy": SQLAlchemyJobStore(engine=sync_engine),
            },
            executors={
                "default": AsyncIOExecutor(),
                "threadpool": ThreadPoolExecutor(max_workers=10),
                "processpool": ProcessPoolExecutor(max_workers=1),
            },
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
            },
        )
    return _scheduler


def start_scheduler() -> None:
    scheduler = get_scheduler()
    if not scheduler.running:
        _add_event_listeners(scheduler)
        scheduler.start()


def shutdown_scheduler() -> None:
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)


def _add_event_listeners(scheduler: AsyncIOScheduler) -> None:
  
    scheduler.add_listener(
        _scheduler_event_listener,
        EVENT_JOB_SUBMITTED | EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED,
    )


def _scheduler_event_listener(event) -> None:
   
    job_id = str(getattr(event, "job_id", ""))
    if not job_id:
        return

    try:
        if isinstance(event, JobSubmissionEvent) and event.code == EVENT_JOB_SUBMITTED:
            execution_id = str(uuid.uuid4())
            _execution_cache[job_id] = {"execution_id": execution_id, "start_time": datetime.now()}
            _write_history(
                task_id=_safe_int(job_id),
                execution_id=execution_id,
                status="running",
                start_time=_execution_cache[job_id]["start_time"],
                end_time=None,
                duration=None,
                result=None,
                error_message=None,
                trigger_type="scheduled",
            )
            return

        if isinstance(event, JobExecutionEvent) and event.code in (EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED):
            cached = _execution_cache.pop(job_id, None) or {}
            execution_id = cached.get("execution_id") or str(uuid.uuid4())
            start_time = cached.get("start_time") or datetime.now()
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())

            if event.code == EVENT_JOB_EXECUTED:
                status = "success"
                error_message = None
                result = _to_json_safe(getattr(event, "retval", None))
            elif event.code == EVENT_JOB_ERROR:
                status = "failed"
                exc = getattr(event, "exception", None)
                error_message = str(exc) if exc else "unknown error"
                result = None
            else:
                status = "timeout"
                error_message = "job missed run time"
                result = None

            _write_history(
                task_id=_safe_int(job_id),
                execution_id=execution_id,
                status=status,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                result=result,
                error_message=error_message,
                trigger_type="scheduled",
            )
            return
    except Exception as e:
        logger.warning(f"Scheduler event log failed(job_id={job_id}): {e}")


def _safe_int(v: str) -> int:
    try:
        return int(v)
    except Exception:
        return 0


def _write_history(
    *,
    task_id: int,
    execution_id: str,
    status: str,
    start_time: datetime,
    end_time: Optional[datetime],
    duration: Optional[int],
    result: Any,
    error_message: Optional[str],
    trigger_type: str,
) -> None:
    
    from sqlalchemy.orm import Session
    from app.api.v1.task_scheduler.model import TaskExecutionHistoryModel

    sync_engine = create_engine(config.DATABASE_URI_SYNC, pool_pre_ping=True)
    with Session(sync_engine) as session:
        row = TaskExecutionHistoryModel(
            task_id=task_id,
            execution_id=execution_id,
            status=status,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            result=result,
            error_message=error_message,
            trigger_type=trigger_type,
        )
        session.add(row)
        session.commit()


def _parse_run_at(v: Any) -> datetime:
    
    if v is None:
        raise ValueError("执行时间不能为空")
    if isinstance(v, datetime):
        return v
    s = str(v).strip()
    if not s:
        raise ValueError("执行时间不能为空")
    normalized = s.replace("T", " ", 1)
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue
    raise ValueError(f"无法解析执行时间: {s!r}，请使用 YYYY-MM-DD HH:mm:ss 格式")


def build_trigger(time_config: dict[str, Any]):
    """
  

    - type=1: DateTrigger，key: run_time
    - type=2: IntervalTrigger，key: interval(分钟)
    - type=3: CronTrigger，每天固定时间，key: week_run_time("HH:MM")
    - type=4: CronTrigger，每周固定星期+时间，key: week_date(list[str]), week_run_time("HH:MM")
    """
    t = int(time_config.get("type", 0))
    if t == 1:
        run_date = _parse_run_at(time_config.get("run_time"))
        return DateTrigger(run_date=run_date)
    if t == 2:
        interval_minutes = int(time_config.get("interval", 0))
        return IntervalTrigger(seconds=interval_minutes * 60)
    if t == 3:
        hh, mm = str(time_config.get("week_run_time", "0:0")).split(":")[:2]
        return CronTrigger(hour=int(hh), minute=int(mm))
    if t == 4:
        hh, mm = str(time_config.get("week_run_time", "0:0")).split(":")[:2]
        week_date = time_config.get("week_date") or []
        day_of_week = ",".join([str(x) for x in week_date])
        return CronTrigger(day_of_week=day_of_week, hour=int(hh), minute=int(mm))
    raise ValueError(f"Unsupported scheduler time type: {t}")


def get_next_run_time(job_id: str) -> str:
    scheduler = get_scheduler()
    job = scheduler.get_job(job_id=str(job_id))
    next_run_time = getattr(job, "next_run_time", None) if job else None
    if not next_run_time:
        return ""
    # APScheduler 返回的 next_run_time 通常带 tzinfo；这里统一转北京时间字符串
    try:
        utc_time = datetime.fromisoformat(str(next_run_time))
    except Exception:
        utc_time = next_run_time
    beijing_time = utc_time.astimezone(timezone(timedelta(hours=8)))
    return beijing_time.strftime("%Y-%m-%d %H:%M:%S")


def add_or_replace_job(job_id: str, func: Callable[..., Awaitable[Any]], trigger, args: list[Any]):
    scheduler = get_scheduler()
    if scheduler.get_job(job_id=str(job_id)):
        scheduler.remove_job(str(job_id))
    # jobstore 固定走 sqlalchemy
    scheduler.add_job(
        func,
        trigger=trigger,
        id=str(job_id),
        args=args,
        replace_existing=True,
        jobstore="sqlalchemy",
        executor="default",
        max_instances=1,
    )

