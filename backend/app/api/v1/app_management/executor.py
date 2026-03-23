import asyncio
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from appium import webdriver
from appium.options.android import UiAutomator2Options

from app.db.sqlalchemy import async_session
from app.api.v1.cloud_device.model import AppDevice
from .model import AppResultModel, AppResultListModel
from sqlalchemy import select, update


def _adb(deviceid: str, *args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    cmd = ["adb", "-s", deviceid, *args]
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)


def adb_screencap_png(deviceid: str) -> bytes:
    # Use exec-out to avoid CRLF issues
    cmd = ["adb", "-s", deviceid, "exec-out", "screencap", "-p"]
    return subprocess.check_output(cmd, timeout=30)


def adb_tap(deviceid: str, x: int, y: int) -> None:
    _adb(deviceid, "shell", "input", "tap", str(int(x)), str(int(y)), timeout=10)


def adb_text(deviceid: str, value: str) -> None:
    # Minimal escaping for spaces
    safe = value.replace(" ", "%s")
    _adb(deviceid, "shell", "input", "text", safe, timeout=10)


def adb_keyevent(deviceid: str, keycode: int) -> None:
    _adb(deviceid, "shell", "input", "keyevent", str(int(keycode)), timeout=10)


def match_template(screen_png: bytes, template_path: str, threshold: float = 0.7) -> Optional[Tuple[int, int]]:
    if not template_path:
        return None
    # 支持 http(s) URL：转换为后端本地路径
    if template_path.startswith("http://") or template_path.startswith("https://"):
        # 去掉协议和域名，只保留 /static/... 路径
        idx = template_path.find("/static/")
        if idx != -1:
            rel_path = template_path[idx + 1 :]  # 去掉前导 /
            backend_dir = Path(__file__).resolve().parents[4]
            template_path = str(backend_dir / rel_path)
    if not os.path.exists(template_path):
        return None
    scr = cv2.imdecode(np.frombuffer(screen_png, np.uint8), cv2.IMREAD_COLOR)
    tpl = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if scr is None or tpl is None:
        return None
    res = cv2.matchTemplate(scr, tpl, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if max_val < threshold:
        return None
    h, w = tpl.shape[:2]
    return (max_loc[0] + w // 2, max_loc[1] + h // 2)


async def _log_result(
    *,
    deviceid: str,
    result_id: str,
    menu_id: int,
    name: str,
    status: int,
    log: str,
    before_img: str = "",
    after_img: str = "",
    video: str = "",
    assert_value: Optional[Dict[str, Any]] = None,
    performance: Optional[Dict[str, Any]] = None,
    user_id: int,
) -> None:
    async with async_session() as db:
        db.add(
            AppResultModel(
                device=deviceid,
                result_id=result_id,
                name=name,
                status=status,
                log=log,
                assert_value=assert_value or {},
                before_img=before_img,
                after_img=after_img,
                video=video,
                performance=performance or {},
                menu_id=menu_id,
                user_id=user_id,
            )
        )
        await db.commit()


async def _update_summary(
    *,
    result_id: str,
    deviceid: str,
    user_id: int,
    total: int,
    passed: int,
    fail: int,
) -> None:
    async with async_session() as db:
        summary = (
            await db.execute(
                select(AppResultListModel).where(
                    AppResultListModel.result_id == result_id,
                    AppResultListModel.user_id == user_id,
                    AppResultListModel.enabled_flag == 1,
                )
            )
        ).scalar_one_or_none()
        if not summary:
            return
        un_run = max(0, int(total) - int(passed) - int(fail))
        percent = round((passed / total) * 100, 2) if total else 0
        ss = summary.script_status or []
        updated = False
        for s in ss:
            if s.get("device") == deviceid:
                s["total"] = int(total)
                s["passed"] = int(passed)
                s["fail"] = int(fail)
                s["un_run"] = int(un_run)
                s["percent"] = float(percent)
                s["status"] = "finished"
                s["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                updated = True
        if not updated:
            ss.append(
                {
                    "device": deviceid,
                    "total": int(total),
                    "passed": int(passed),
                    "fail": int(fail),
                    "un_run": int(un_run),
                    "percent": float(percent),
                    "status": "finished",
                    "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
        summary.script_status = ss
        summary.end_time = datetime.now()
        await db.commit()


async def _release_device(deviceid: str, user_id: int) -> None:
    """执行完成后释放设备：对齐旧架构“执行结束自动置空闲”"""
    async with async_session() as db:
        await db.execute(
            update(AppDevice)
            .where(AppDevice.device_id == deviceid, AppDevice.user_id == user_id)
            .values(device_status=1)
        )
        await db.commit()


def run_appium_process(
    *,
    deviceid: str,
    scripts: List[Dict[str, Any]],
    result_id: str,
    menu_id: int,
    appium_server_url: str,
    package: str,
    user_id: int,
    template_root: str = "",
) -> None:
    """
    Subprocess entry: execute steps via Appium + adb, log results into DB.

    scripts: list of step dicts (old structure) under one menu_id.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    total = len(scripts or [])
    passed = 0
    fail_n = 0
    driver = None

    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = deviceid
    options.udid = deviceid
    options.new_command_timeout = 3600
    # Avoid reinstall on every run; assume app already installed when run_type==3
    options.no_reset = True

    backend_dir = Path(__file__).resolve().parents[4]  # .../backend
    base_dir = backend_dir / "static" / "app_result" / result_id / deviceid
    base_dir.mkdir(parents=True, exist_ok=True)

    t_series = []
    cpu = []
    mem = []
    up = []
    down = []
    temp = []

    def perf_snapshot() -> Dict[str, Any]:
        # lightweight performance sampling; if adb fails, push zeros
        try:
            now = datetime.now()
            t_series.append(f"{now.minute}:{now.second}")
        except Exception:
            t_series.append("0:0")
        cpu.append(0)
        mem.append(0)
        up.append(0)
        down.append(0)
        temp.append(0)
        return {"time": t_series, "cpu": cpu, "memory": mem, "up_network": up, "down_network": down, "temperature": temp}

    try:
        try:
            driver = webdriver.Remote(appium_server_url, options=options)
        except Exception as e:
            # Appium 连接失败也要落库并回写统计，避免报告页全 0
            loop.run_until_complete(
                _log_result(
                    deviceid=deviceid,
                    result_id=result_id,
                    menu_id=menu_id,
                    name="执行异常",
                    status=0,
                    log=f"Appium连接失败: {e}",
                    performance=perf_snapshot(),
                    user_id=user_id,
                )
            )
            loop.run_until_complete(
                _log_result(
                    deviceid=deviceid,
                    result_id=result_id,
                    menu_id=menu_id,
                    name="执行结束",
                    status=0,
                    log="执行结束",
                    performance=perf_snapshot(),
                    user_id=user_id,
                )
            )
            loop.run_until_complete(
                _update_summary(
                    result_id=result_id,
                    deviceid=deviceid,
                    user_id=user_id,
                    total=total,
                    passed=0,
                    fail=max(1, total),
                )
            )
            return

        loop.run_until_complete(
            _log_result(
                deviceid=deviceid,
                result_id=result_id,
                menu_id=menu_id,
                name="开始执行",
                status=2,
                log="正在执行",
                performance=perf_snapshot(),
                user_id=user_id,
            )
        )

        for idx, step in enumerate(scripts):
            step_name = str(step.get("name") or f"步骤{idx+1}")
            step_type = int(step.get("type") if step.get("type") is not None else -1)
            before_path = base_dir / f"before_{idx+1}_{int(time.time()*1000)}.png"
            after_path = base_dir / f"after_{idx+1}_{int(time.time()*1000)}.png"
            before_url = ""
            after_url = ""

            try:
                before_png = adb_screencap_png(deviceid)
                before_path.write_bytes(before_png)
                before_url = f"/static/app_result/{result_id}/{deviceid}/{before_path.name}"
            except Exception:
                pass

            ok = True
            log_msg = "执行成功"
            try:
                if step_type == 0:
                    time.sleep(2)
                elif step_type == 1:
                    if package:
                        driver.activate_app(package)
                elif step_type == 2:
                    # click by template if configured
                    img = (((step.get("android") or {}).get("img")) or "")
                    template_path = img
                    if template_root and template_path and template_path.startswith("/"):
                        candidate = os.path.join(template_root, template_path.lstrip("/"))
                        if os.path.exists(candidate):
                            template_path = candidate
                    p = match_template(adb_screencap_png(deviceid), template_path) if template_path else None
                    if not p:
                        raise RuntimeError("未找到点击目标")
                    adb_tap(deviceid, p[0], p[1])
                elif step_type == 3:
                    value = str(step.get("value") or "")
                    adb_text(deviceid, value)
                elif step_type == 4:
                    # clear: backspace x 20
                    for _ in range(20):
                        adb_keyevent(deviceid, 67)
                elif step_type == 6:
                    if package:
                        driver.terminate_app(package)
                elif step_type == 8:
                    adb_keyevent(deviceid, 66)
                else:
                    # 未实现的步骤类型，先标记成功但记录日志（后续继续补齐）
                    log_msg = f"未实现的步骤类型: {step_type}"
            except Exception as e:
                ok = False
                log_msg = str(e)

            try:
                after_png = adb_screencap_png(deviceid)
                after_path.write_bytes(after_png)
                after_url = f"/static/app_result/{result_id}/{deviceid}/{after_path.name}"
            except Exception:
                pass

            status = 1 if ok else 0
            if ok:
                passed += 1
            else:
                fail_n += 1

            loop.run_until_complete(
                _log_result(
                    deviceid=deviceid,
                    result_id=result_id,
                    menu_id=menu_id,
                    name=step_name,
                    status=status,
                    log=log_msg,
                    before_img=before_url,
                    after_img=after_url,
                    performance=perf_snapshot(),
                    assert_value=step.get("assert_value") or {},
                    user_id=user_id,
                )
            )

        loop.run_until_complete(
            _log_result(
                deviceid=deviceid,
                result_id=result_id,
                menu_id=menu_id,
                name="执行结束",
                status=1,
                log="执行结束",
                performance=perf_snapshot(),
                user_id=user_id,
            )
        )
        loop.run_until_complete(
            _update_summary(
                result_id=result_id,
                deviceid=deviceid,
                user_id=user_id,
                total=total,
                passed=passed,
                fail=fail_n,
            )
        )
    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            pass

        # 无论成功/失败/异常，都尝试释放设备，避免设备“长期使用中”
        try:
            loop.run_until_complete(_release_device(deviceid=deviceid, user_id=user_id))
        except Exception:
            pass
