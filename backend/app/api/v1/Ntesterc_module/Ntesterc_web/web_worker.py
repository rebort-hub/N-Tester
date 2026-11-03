#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

from __future__ import annotations

import asyncio
from typing import Any, Dict

from app.core.database import async_session_factory

from .playwright_runner import run_web_async


def run_web_task_in_process(data: Dict[str, Any], run_browser_type: int) -> None:
    """
    multiprocessing 进程入口：执行单个浏览器任务。
    """
    asyncio.run(run_web_async(data, run_browser_type, session_factory=async_session_factory))

