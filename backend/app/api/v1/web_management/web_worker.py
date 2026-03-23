"""
Web管理模块 - 后台执行 Worker（独立模块）

说明：
- 对齐旧版 Web_process + Multi_process 的“子进程执行”模式
- 每个浏览器任务用一个 OS 进程运行，PID 可用于 stop_web_script
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from app.db.sqlalchemy import async_session_factory

from .playwright_runner import run_web_async


def run_web_task_in_process(data: Dict[str, Any], run_browser_type: int) -> None:
    """
    multiprocessing 进程入口：执行单个浏览器任务。
    必须是模块级函数，才能被 spawn 方式 pickling。
    """
    asyncio.run(run_web_async(data, run_browser_type, session_factory=async_session_factory))

