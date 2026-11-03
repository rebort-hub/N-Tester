#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from app.core.database import async_session
from .model import DesktopResultModel, DesktopResultListModel
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified


async def _send_finish_notification(
    result_id: str, task_name: str,
    total: int, passed: int, fail: int,
    user_id: int, module: str = "desktop",
) -> None:
    """执行完成后通过统一通知系统推送结果"""
    try:
        from app.api.v1.Ntesterc_module.Ntesterc_notifications.service import task_notification_service
        from app.core.database import async_session as _session
        percent = round(passed / total * 100, 2) if total else 0
        status = "success" if fail == 0 else "failed"
        message = (
            f"【{module}自动化】任务「{task_name}」执行完成\n"
            f"总步骤: {total} | 通过: {passed} | 失败: {fail} | 通过率: {percent}%\n"
            f"执行ID: {result_id}"
        )
        async with _session() as db:
            await task_notification_service.send_task_notification(
                db=db,
                task_type=module,
                task_id=result_id,
                status=status,
                message=message,
                user_id=user_id,
            )
    except Exception:
        pass  # 通知失败不影响主流程


async def _write_step(
    result_id: str,
    menu_id: int,
    user_id: int,
    name: str,
    status: int,
    log: str,
    before_img: str,
    after_img: str,
    assert_value: Dict,
) -> None:
    async with async_session() as db:
        db.add(DesktopResultModel(
            result_id=result_id,
            menu_id=menu_id,
            user_id=user_id,
            name=name,
            status=status,
            log=log,
            before_img=before_img,
            after_img=after_img,
            assert_value=assert_value,
        ))
        await db.commit()


async def _update_summary(
    result_id: str,
    user_id: int,
    total: int,
    passed: int,
    fail: int,
    finished: bool = False,
) -> None:
    async with async_session() as db:
        row = (await db.execute(
            select(DesktopResultListModel).where(
                DesktopResultListModel.result_id == result_id,
                DesktopResultListModel.user_id == user_id,
            )
        )).scalar_one_or_none()
        if not row:
            return
        un_run = max(0, total - passed - fail)
        percent = round(passed / total * 100, 2) if total else 0
        ss = list(row.script_status or [])
        entry = {
            "total": total, "passed": passed, "fail": fail,
            "un_run": un_run, "percent": percent,
            "status": "finished" if finished else "running",
            "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S") if finished else None,
        }
        if ss:
            ss[-1] = entry
        else:
            ss.append(entry)
        row.script_status = ss
        if finished:
            row.end_time = datetime.now()
        flag_modified(row, "script_status")
        await db.commit()


def run_desktop_process(
    *,
    result_id: str,
    menu_id: int,
    user_id: int,
    steps: List[Dict[str, Any]],
    framework: str,
    task_name: str,
) -> None:
    """
    子进程入口函数（由 multiprocessing.Process 调用）
    子进程必须重新初始化数据库连接，不能复用父进程连接池
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 截图保存目录（backend/static/desktop_result/<result_id>）
    from pathlib import Path
    from app.config.setting import config as app_config
    base_dir = Path(__file__).resolve().parents[4] / app_config.STATIC_DIR / "desktop_result" / result_id
    base_dir.mkdir(parents=True, exist_ok=True)

    # 子进程重新初始化数据库引擎，避免复用父进程连接池导致连接损坏
    from app.core.database import reinit_engine
    try:
        reinit_engine()
    except Exception:
        pass  # reinit_engine 不存在时降级，依赖 async_session 懒初始化

    total = len(steps)
    passed = 0
    fail = 0

    # 初始化汇总状态
    loop.run_until_complete(_update_summary(result_id, user_id, total, 0, 0))

    try:
        from .runners.factory import get_runner
        runner = get_runner(
            framework=framework,
            result_id=result_id,
            menu_id=menu_id,
            user_id=user_id,
            base_dir=base_dir,
        )

        # 写入"开始执行"
        loop.run_until_complete(_write_step(
            result_id, menu_id, user_id,
            "开始执行", 2, "正在执行", "", "", {},
        ))

        for step in steps:
            result = runner.execute_step(step)
            if result.status == 1:
                passed += 1
            else:
                fail += 1

            loop.run_until_complete(_write_step(
                result_id, menu_id, user_id,
                result.name, result.status, result.log,
                result.before_img, result.after_img, result.assert_value,
            ))
            loop.run_until_complete(_update_summary(result_id, user_id, total, passed, fail))

        # 写入"执行结束"
        loop.run_until_complete(_write_step(
            result_id, menu_id, user_id,
            "执行结束", 1, "执行完成", "", "", {},
        ))

    except Exception as e:
        fail = max(1, fail)
        loop.run_until_complete(_write_step(
            result_id, menu_id, user_id,
            "执行异常", 0, str(e), "", "", {},
        ))
    finally:
        loop.run_until_complete(_update_summary(
            result_id, user_id, total, passed, fail, finished=True
        ))
        # 执行完成后发送通知
        try:
            loop.run_until_complete(_send_finish_notification(
                result_id=result_id, task_name=task_name,
                total=total, passed=passed, fail=fail, user_id=user_id,
                module="desktop",
            ))
        except Exception:
            pass
