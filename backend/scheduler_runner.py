from __future__ import annotations

import asyncio
import signal
from typing import Optional

from app.corelibs.logger import init_logger, logger
from app.db import get_redis_pool
from app.db.sqlalchemy import async_session
from config import config


class SchedulerRunner:
    def __init__(self) -> None:
        self._stopping: bool = False
        self._stop_event: Optional[asyncio.Event] = None
        self._redis = None
        self._cmd_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        init_logger()
        logger.info("SchedulerRunner starting...")

        # Redis（如任务执行需要缓存/锁等，保持与主服务一致的初始化方式）
        redis_pool_instance = get_redis_pool()
        redis_pool_instance.init_by_config(config=config)
        self._redis = redis_pool_instance.redis

        # 启动调度器
        from app.api.v1.task_scheduler.scheduler import start_scheduler
        from app.api.v1.task_scheduler.service import TaskSchedulerService

        start_scheduler()

        # 加载数据库中启用的任务
        async with async_session() as session:
            await TaskSchedulerService.load_enabled_tasks(session)

        # 启动控制命令监听（API 通过 Redis 远程控制）
        self._cmd_task = asyncio.create_task(self._command_loop())

        self._stop_event = asyncio.Event()
        logger.info("SchedulerRunner started. Waiting for shutdown signal.")
        await self._stop_event.wait()

        # 关闭
        await self.stop()

    async def stop(self) -> None:
        if self._stopping:
            return
        self._stopping = True
        logger.info("SchedulerRunner stopping...")
        try:
            if self._cmd_task:
                self._cmd_task.cancel()
        except Exception:
            pass
        try:
            from app.api.v1.task_scheduler.scheduler import shutdown_scheduler

            shutdown_scheduler()
        except Exception as e:
            logger.warning(f"Scheduler shutdown failed: {e}")
        logger.info("SchedulerRunner stopped.")

    def request_stop(self) -> None:
        if self._stop_event and not self._stop_event.is_set():
            self._stop_event.set()

    async def _command_loop(self) -> None:
        """
        监听 Redis 队列命令并执行。
        命令格式参见 `app/api/v1/task_scheduler/remote_control.py`。
        """
        if not self._redis:
            return

        from app.api.v1.task_scheduler.remote_control import QUEUE_KEY
        from app.api.v1.task_scheduler.scheduler import get_scheduler
        from apscheduler.triggers.date import DateTrigger
        from datetime import datetime, timedelta
        import json

        redis = self._redis
        while True:
            try:
                item = await redis.brpop(QUEUE_KEY, timeout=1)
                if not item:
                    await asyncio.sleep(0.05)
                    continue

                _key, raw = item
                cmd = json.loads(raw) if isinstance(raw, (bytes, str)) else raw
                if not isinstance(cmd, dict):
                    continue

                action = cmd.get("action")
                payload = cmd.get("payload") or {}
                reply_key = cmd.get("reply_key")

                data: dict = {}
                scheduler = get_scheduler()

                if action == "scheduler.status":
                    data = {
                        "running": bool(scheduler.running),
                        "state": int(scheduler.state),
                        "job_count": len(scheduler.get_jobs()),
                    }
                elif action == "scheduler.jobs":
                    jobs = scheduler.get_jobs()
                    data = {
                        "jobs": [
                            {
                                "id": j.id,
                                "name": j.name,
                                "trigger": str(j.trigger),
                                "next_run_time": str(j.next_run_time) if j.next_run_time else None,
                            }
                            for j in jobs
                        ]
                    }
                elif action == "scheduler.reload":
                    # 清空现有 job，并从 DB 重新加载启用任务
                    from app.api.v1.task_scheduler.service import TaskSchedulerService
                    from app.db.sqlalchemy import async_session

                    before_jobs = scheduler.get_jobs()
                    before_ids = [str(j.id) for j in before_jobs]
                    try:
                        scheduler.remove_all_jobs()
                    except Exception:
                        # 兼容部分 jobstore/版本差异：逐个 remove
                        for j in before_jobs:
                            try:
                                scheduler.remove_job(j.id)
                            except Exception:
                                pass

                    async with async_session() as session:
                        report = await TaskSchedulerService.load_enabled_tasks_report(session)

                    after_jobs = scheduler.get_jobs()
                    after_ids = [str(j.id) for j in after_jobs]

                    before_set = set(before_ids)
                    after_set = set(after_ids)

                    removed_ids = sorted(list(before_set - after_set))
                    added_ids = sorted(list(after_set - before_set))
                    reloaded_ids = sorted(list(before_set & after_set))
                    data = {
                        "before_job_count": len(before_ids),
                        "after_job_count": len(after_ids),
                        "removed_job_ids": removed_ids,
                        "added_job_ids": added_ids,
                        "reloaded_job_ids": reloaded_ids,
                        "loaded_ids": report.get("loaded_ids") or [],
                        "failed": report.get("failed") or [],
                        "db_total_enabled": int(report.get("total") or 0),
                    }
                elif action == "job.pause":
                    job_id = str(payload.get("job_id"))
                    scheduler.pause_job(job_id)
                    data = {"job_id": job_id}
                elif action == "job.resume":
                    job_id = str(payload.get("job_id"))
                    scheduler.resume_job(job_id)
                    data = {"job_id": job_id}
                elif action == "job.remove":
                    job_id = str(payload.get("job_id"))
                    scheduler.remove_job(job_id)
                    data = {"job_id": job_id}
                elif action == "job.run_now":
                    job_id = str(payload.get("job_id"))
                    job = scheduler.get_job(job_id)
                    if not job:
                        raise RuntimeError("job not found")
                    temp_id = f"{job_id}:run_now:{datetime.now().timestamp()}"
                    trigger = DateTrigger(run_date=datetime.now() + timedelta(seconds=0.1))
                    scheduler.add_job(
                        func=job.func,
                        trigger=trigger,
                        args=job.args,
                        kwargs=job.kwargs,
                        id=temp_id,
                        name=f"{job.name}(run_now)",
                        jobstore="sqlalchemy",
                        executor="threadpool",
                        max_instances=1,
                        replace_existing=True,
                    )
                    data = {"job_id": job_id, "temp_job_id": temp_id}
                else:
                    raise RuntimeError(f"unsupported action: {action}")

                if reply_key:
                    await redis.set(reply_key, {"ok": True, "data": data}, ex=15)
            except asyncio.CancelledError:
                return
            except Exception as e:
                try:
                    reply_key = None
                    if isinstance(locals().get("cmd"), dict):
                        reply_key = locals()["cmd"].get("reply_key")
                    if reply_key:
                        await redis.set(reply_key, {"ok": False, "error": str(e)}, ex=15)
                except Exception:
                    pass
                # 保持循环继续
                await asyncio.sleep(0.1)


def _install_signal_handlers(runner: SchedulerRunner) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    def _handler() -> None:
        runner.request_stop()

    for s in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(s, _handler)
        except NotImplementedError:
            # Windows / ProactorLoop：忽略，依赖 Ctrl+C 触发的 CancelledError
            pass


async def main() -> None:
    runner = SchedulerRunner()
    _install_signal_handlers(runner)
    await runner.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

