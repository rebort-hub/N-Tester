from app.corelibs.logger import logger


def init_scheduler():
    """启动 APScheduler 定时任务调度器"""
    try:
        from app.api.v1.task_scheduler.scheduler import start_scheduler
        start_scheduler()
        logger.info("APScheduler 启动成功")
    except Exception as e:
        logger.warning(f"APScheduler 启动失败：{e}")


def shutdown_scheduler():
    """关闭 APScheduler 定时任务调度器"""
    try:
        from app.api.v1.task_scheduler.scheduler import shutdown_scheduler
        shutdown_scheduler()
    except Exception:
        pass


async def load_perf_pending_jobs():
    """应用启动时恢复性能测试定时任务（MemoryJobStore 重启后清空）"""
    try:
        from app.api.v1.performance.scheduler.jobs import load_perf_pending_jobs as _load
        await _load()
    except Exception as e:
        logger.warning(f"恢复性能测试定时任务失败：{e}")