# -*- coding: utf-8 -*-
"""
APP 自动化执行器（Airtest 子进程入口）
一比一迁移自 l-tester/views/app/app_script.py::run_script
"""
from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from app.db.sqlalchemy import async_session

from .airtest_common import (
    SMS_DEVICE_BY_TEST_DEVICE,
    EMAIL_BY_DEVICE,
    PHONE_BY_DEVICE,
    allocate_install_app,
    allocate_package,
    assert_img_exists,
    check_app_install,
    device_rm_file,
    get_performance,
    get_project_root,
    get_public_base_url,
    get_sms,
    ocr_version,
    wait_until_download,
    wait_until_exists,
    wait_until_install,
)
from .executor import _log_result, _release_device
from .model import AppDevice, AppResultListModel, AppResultModel


async def _task_end_legacy(
    *,
    result_id: str,
    deviceid: str,
    user_id: int,
    total: int,
    end_time: str,
) -> None:
    """对齐旧 task_end：统计 app_results、追加 script_status、通知 app_report"""
    from app.api.v1.api_automation.service import ApiAutomationService

    async with async_session() as db:
        res = await db.execute(
            select(AppResultModel.status).where(
                AppResultModel.result_id == result_id,
                AppResultModel.device == deviceid,
                AppResultModel.user_id == user_id,
                AppResultModel.enabled_flag == 1,
                AppResultModel.status != 2,
            )
        )
        statuses = list(res.scalars().all())
        fail = 0
        passed = 0
        for st in statuses:
            if int(st or 0) == 0:
                fail += 1
            else:
                passed += 1
        un_run = total - passed - fail
        if total == 0:
            percent = 0.0
        else:
            percent = round(((total - fail - un_run) / total) * 100, 2)

        row = (
            await db.execute(
                select(AppResultListModel).where(
                    AppResultListModel.result_id == result_id,
                    AppResultListModel.user_id == user_id,
                    AppResultListModel.enabled_flag == 1,
                )
            )
        ).scalar_one_or_none()
        if row:
            ss = list(row.script_status or [])
            ss.append(
                {
                    "device": deviceid,
                    "fail": fail,
                    "passed": passed,
                    "un_run": un_run,
                    "total": total,
                    "percent": percent,
                    "end_time": end_time,
                }
            )
            row.script_status = ss
            row.end_time = datetime.now()
            await db.commit()

        dn = (
            await db.execute(
                select(AppDevice.device_name).where(
                    AppDevice.device_id == deviceid, AppDevice.user_id == user_id, AppDevice.enabled_flag == 1
                )
            )
        ).scalar_one_or_none()
        device_name = str(dn or deviceid)
        data = {
            "device_name": device_name,
            "result_id": result_id,
            "total": total,
            "fail": fail,
            "passed": passed,
            "un_run": un_run,
            "percent": percent,
        }
        await ApiAutomationService._send_notice(db, 26, "app_report", data, user_id)


def _airtest_snapshot(driver, device: str, result_id: str, project_root: Path) -> str:
    base = project_root / "media" / "app_result" / result_id / device
    base.mkdir(parents=True, exist_ok=True)
    filename = f"{int(time.time())}.png"
    fp = base / filename
    try:
        driver.snapshot(str(fp))
    except Exception as e:
        return str(e)
    rel = f"media/app_result/{result_id}/{device}/{filename}"
    return f"{get_public_base_url()}/{rel}"


def run_airtest_script_process(
    *,
    deviceid: str,
    script_blocks: List[Dict[str, Any]],
    result_id: str,
    user_id: int,
    run_type: int,
    os_type: str,
    version: str,
    channel_id: str,
    package: str,
    install_path: str,
) -> None:
    """
    子进程入口：与旧 Multi_process -> run_script 参数语义一致。
    script_blocks: [{"id": menu_id, "script": [step,...]}, ...]
    """
    try:
        from airtest.core.api import connect_device, init_device
    except ImportError as e:  # pragma: no cover
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _fail():
            await _log_result(
                deviceid=deviceid,
                result_id=result_id,
                menu_id=0,
                name="环境错误",
                status=0,
                log=f"未安装 airtest: {e}",
                user_id=user_id,
            )

        loop.run_until_complete(_fail())
        loop.run_until_complete(_release_device(deviceid, user_id))
        return

    project_root = get_project_root()
    try:
        os.chdir(str(project_root))
    except Exception:
        pass

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    menu_id = 0
    performance: Dict[str, Any] = {
        "time": [],
        "memory": [],
        "cpu": [],
        "temperature": [],
        "up_network": [],
        "down_network": [],
    }

    base_img_dir = project_root / "media" / "app_result" / result_id / deviceid
    base_img_dir.mkdir(parents=True, exist_ok=True)
    video = str(base_img_dir / f"{result_id}.mp4")

    if os_type == "android":
        driver = connect_device(f"Android:///{deviceid}?cap_method=javacap&touch_method=adb")
    else:
        driver = init_device(platform="IOS", uuid=f"http+usbmux://{deviceid}")

    try:
        driver.start_recording(
            max_time=36000,
            fps=60,
            bitrate=2592000,
            mode="ffmpeg",
            max_size=5000000,
            output=video,
            snapshot_sleep=0.1,
        )
    except Exception:
        video = ""

    total_steps = 0
    for block in script_blocks or []:
        total_steps += len((block or {}).get("script") or [])

    first_menu = int((script_blocks[0] or {}).get("id") or 0) if script_blocks else 0

    # ---------- run_type 安装（对齐旧逻辑）----------
    if run_type == 1:
        file_path = os.path.join(install_path or "", package or "")
        performance = get_performance(deviceid, performance)
        loop.run_until_complete(
            _log_result(
                deviceid=deviceid,
                result_id=result_id,
                menu_id=first_menu,
                name="设备包体分配",
                status=2,
                log=f"开始分配设备，包体：{package}",
                before_img="",
                after_img="",
                performance=performance,
                video="",
                assert_value={},
                user_id=user_id,
            )
        )
        res = allocate_install_app(deviceid, file_path)
        performance = get_performance(deviceid, performance)
        loop.run_until_complete(
            _log_result(
                deviceid=deviceid,
                result_id=result_id,
                menu_id=first_menu,
                name="安装包体",
                status=2,
                log=f"正在安装包体：{package}",
                before_img="",
                after_img="",
                performance=performance,
                video="",
                assert_value={},
                user_id=user_id,
            )
        )
        if not res:
            performance = get_performance(deviceid, performance)
            loop.run_until_complete(
                _log_result(
                    deviceid=deviceid,
                    result_id=result_id,
                    menu_id=first_menu,
                    name="处理安装权限",
                    status=2,
                    log="正在处理安装权限...",
                    before_img="",
                    after_img="",
                    performance=performance,
                    video="",
                    assert_value={},
                    user_id=user_id,
                )
            )
            check_status = check_app_install(deviceid, package)
            while not check_status:
                if wait_until_install(deviceid, 300):
                    check_status = True
                else:
                    break
        performance = get_performance(deviceid, performance)
        loop.run_until_complete(
            _log_result(
                deviceid=deviceid,
                result_id=result_id,
                menu_id=first_menu,
                name="安装成功",
                status=2,
                log=f"{package}：安装成功",
                before_img="",
                after_img="",
                performance=performance,
                video="",
                assert_value={},
                user_id=user_id,
            )
        )
    else:
        res = allocate_package(deviceid, version, channel_id)
        if not res:
            check_status = check_app_install(deviceid, package)
            while not check_status:
                if wait_until_install(deviceid, 300):
                    check_status = True
                else:
                    break

    from airtest.core.api import keyevent, sleep, start_app, stop_app, text, touch
    from airtest.core.cv import Template

    pr = project_root

    for block in script_blocks or []:
        menu_id = int(block.get("id") or 0)
        for j in block.get("script") or []:
            if not j.get("status", True):
                continue
            before_img = _airtest_snapshot(driver, deviceid, result_id, pr)
            jtype = int(j.get("type") if j.get("type") is not None else -1)

            try:
                if jtype == 0:
                    time.sleep(1)
                    after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                    performance = get_performance(deviceid, performance)
                    res_log = "等待热更..."
                    loop.run_until_complete(
                        _log_result(
                            deviceid=deviceid,
                            result_id=result_id,
                            menu_id=menu_id,
                            name=str(j.get("name") or ""),
                            status=1,
                            log=res_log,
                            before_img=before_img,
                            after_img=after_img,
                            performance=performance,
                            video="",
                            assert_value={},
                            user_id=user_id,
                        )
                    )
                    img_key = ((j.get("android") or {}).get("img")) or ""
                    wait_until_download(img_key, 18000, project_root=pr)

                elif jtype == 1:
                    try:
                        sleep(5)
                        start_app(j["package"])
                        after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                        performance = get_performance(deviceid, performance)
                        res_log = f"启动APP：{j['package']}, 成功"
                        loop.run_until_complete(
                            _log_result(
                                deviceid=deviceid,
                                result_id=result_id,
                                menu_id=menu_id,
                                name=str(j.get("name") or ""),
                                status=1,
                                log=res_log,
                                before_img=before_img,
                                after_img=after_img,
                                performance=performance,
                                video="",
                                assert_value={},
                                user_id=user_id,
                            )
                        )
                    except Exception as e:
                        res_log = f"启动APP：{j['package']}, 失败，原因是：{str(e)}"
                        after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                        performance = get_performance(deviceid, performance)
                        loop.run_until_complete(
                            _log_result(
                                deviceid=deviceid,
                                result_id=result_id,
                                menu_id=menu_id,
                                name=str(j.get("name") or ""),
                                status=0,
                                log=res_log,
                                before_img=before_img,
                                after_img=after_img,
                                performance=performance,
                                video="",
                                assert_value={},
                                user_id=user_id,
                            )
                        )

                elif jtype == 2:
                    try:
                        res_msg = "点击成功"
                        now_time = time.time()
                        if j.get("name") == "检查热更version，并进入游戏":
                            path = str(pr) + before_img.replace(get_public_base_url(), "")
                            ocr_data = ocr_version(path)
                            res_msg = f"版本号：{ocr_data}，点击进入游戏成功"
                        android = j.get("android") or {}
                        img_t = android.get("img")
                        if wait_until_exists(deviceid, img_t, 180, project_root=pr):
                            target = Template(_template_abs(img_t, pr))
                            touch(target)
                            res_log = res_msg
                            performance = get_performance(deviceid, performance)
                            if android.get("assert") is not None:
                                if assert_img_exists(android.get("assert"), pr):
                                    if j.get("name") == "支付成功，点击返回游戏":
                                        time.sleep(3)
                                    after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                                    assert_value = {"img": after_img, "result": "断言通过"}
                                    loop.run_until_complete(
                                        _log_result(
                                            deviceid=deviceid,
                                            result_id=result_id,
                                            menu_id=menu_id,
                                            name=str(j.get("name") or ""),
                                            status=1,
                                            log=res_log,
                                            before_img=before_img,
                                            after_img=after_img,
                                            performance=performance,
                                            video="",
                                            assert_value=assert_value,
                                            user_id=user_id,
                                        )
                                    )
                                else:
                                    after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                                    assert_value = {"img": after_img, "result": "断言失败"}
                                    loop.run_until_complete(
                                        _log_result(
                                            deviceid=deviceid,
                                            result_id=result_id,
                                            menu_id=menu_id,
                                            name=str(j.get("name") or ""),
                                            status=0,
                                            log=res_log,
                                            before_img=before_img,
                                            after_img=after_img,
                                            performance=performance,
                                            video="",
                                            assert_value=assert_value,
                                            user_id=user_id,
                                        )
                                    )
                            else:
                                after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                                loop.run_until_complete(
                                    _log_result(
                                        deviceid=deviceid,
                                        result_id=result_id,
                                        menu_id=menu_id,
                                        name=str(j.get("name") or ""),
                                        status=1,
                                        log=res_log,
                                        before_img=before_img,
                                        after_img=after_img,
                                        performance=performance,
                                        video="",
                                        assert_value={},
                                        user_id=user_id,
                                    )
                                )
                        else:
                            res_log = f'{android.get("img")}，图像识别失败'
                            after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                            performance = get_performance(deviceid, performance)
                            loop.run_until_complete(
                                _log_result(
                                    deviceid=deviceid,
                                    result_id=result_id,
                                    menu_id=menu_id,
                                    name=str(j.get("name") or ""),
                                    status=0,
                                    log=res_log,
                                    before_img=before_img,
                                    after_img=after_img,
                                    performance=performance,
                                    video="",
                                    assert_value={},
                                    user_id=user_id,
                                )
                            )
                    except Exception as e:
                        res_log = f"点击失败，原因是：{str(e)}"
                        after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                        performance = get_performance(deviceid, performance)
                        loop.run_until_complete(
                            _log_result(
                                deviceid=deviceid,
                                result_id=result_id,
                                menu_id=menu_id,
                                name=str(j.get("name") or ""),
                                status=0,
                                log=res_log,
                                before_img=before_img,
                                after_img=after_img,
                                performance=performance,
                                video="",
                                assert_value={},
                                user_id=user_id,
                            )
                        )

                elif jtype == 3:
                    jj = dict(j)
                    if jj.get("name") == "输入正确的手机号" and deviceid in PHONE_BY_DEVICE:
                        jj["value"] = PHONE_BY_DEVICE[deviceid]
                    if jj.get("name") == "输入正确的邮箱" and deviceid in EMAIL_BY_DEVICE:
                        jj["value"] = EMAIL_BY_DEVICE[deviceid]
                    try:
                        android = jj.get("android") or {}
                        img_t = android.get("img")
                        if wait_until_exists(deviceid, img_t, 180, project_root=pr):
                            touch(Template(_template_abs(img_t, pr)))
                            text(jj["value"])
                            performance = get_performance(deviceid, performance)
                            after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                            res_log = f"输入：{jj['value']}， 成功"
                            loop.run_until_complete(
                                _log_result(
                                    deviceid=deviceid,
                                    result_id=result_id,
                                    menu_id=menu_id,
                                    name=str(jj.get("name") or ""),
                                    status=1,
                                    log=res_log,
                                    before_img=before_img,
                                    after_img=after_img,
                                    performance=performance,
                                    video="",
                                    assert_value={},
                                    user_id=user_id,
                                )
                            )
                        else:
                            res_log = f'{android.get("img")}，图像识别失败'
                            after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                            performance = get_performance(deviceid, performance)
                            loop.run_until_complete(
                                _log_result(
                                    deviceid=deviceid,
                                    result_id=result_id,
                                    menu_id=menu_id,
                                    name=str(jj.get("name") or ""),
                                    status=0,
                                    log=res_log,
                                    before_img=before_img,
                                    after_img=after_img,
                                    performance=performance,
                                    video="",
                                    assert_value={},
                                    user_id=user_id,
                                )
                            )
                    except Exception as e:
                        res_log = f"输入：{j.get('value')}，失败，原因是：{str(e)}"
                        after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                        performance = get_performance(deviceid, performance)
                        loop.run_until_complete(
                            _log_result(
                                deviceid=deviceid,
                                result_id=result_id,
                                menu_id=menu_id,
                                name=str(j.get("name") or ""),
                                status=0,
                                log=res_log,
                                before_img=before_img,
                                after_img=after_img,
                                performance=performance,
                                video="",
                                assert_value={},
                                user_id=user_id,
                            )
                        )

                elif jtype == 4:
                    try:
                        android = j.get("android") or {}
                        img_t = android.get("img")
                        if wait_until_exists(deviceid, img_t, 180, project_root=pr):
                            touch(Template(_template_abs(img_t, pr)))
                            for _i in range(20):
                                keyevent("KEYCODE_DEL")
                            performance = get_performance(deviceid, performance)
                            after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                            loop.run_until_complete(
                                _log_result(
                                    deviceid=deviceid,
                                    result_id=result_id,
                                    menu_id=menu_id,
                                    name=str(j.get("name") or ""),
                                    status=1,
                                    log="清空文本成功",
                                    before_img=before_img,
                                    after_img=after_img,
                                    performance=performance,
                                    video="",
                                    assert_value={},
                                    user_id=user_id,
                                )
                            )
                        else:
                            res_log = f'{android.get("img")}，图像识别失败'
                            after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                            performance = get_performance(deviceid, performance)
                            loop.run_until_complete(
                                _log_result(
                                    deviceid=deviceid,
                                    result_id=result_id,
                                    menu_id=menu_id,
                                    name=str(j.get("name") or ""),
                                    status=0,
                                    log=res_log,
                                    before_img=before_img,
                                    after_img=after_img,
                                    performance=performance,
                                    video="",
                                    assert_value={},
                                    user_id=user_id,
                                )
                            )
                    except Exception as e:
                        res_log = f"清空文本失败，原因是：{str(e)}"
                        after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                        performance = get_performance(deviceid, performance)
                        loop.run_until_complete(
                            _log_result(
                                deviceid=deviceid,
                                result_id=result_id,
                                menu_id=menu_id,
                                name=str(j.get("name") or ""),
                                status=0,
                                log=res_log,
                                before_img=before_img,
                                after_img=after_img,
                                performance=performance,
                                video="",
                                assert_value={},
                                user_id=user_id,
                            )
                        )

                elif jtype == 5:
                    now_time = time.time()
                    sms_dev = SMS_DEVICE_BY_TEST_DEVICE.get(deviceid, "")
                    try:
                        sms_code = get_sms(int(now_time * 1000), sms_dev)
                        android = j.get("android") or {}
                        img_t = android.get("img")
                        if wait_until_exists(deviceid, img_t, 180, project_root=pr):
                            touch(Template(_template_abs(img_t, pr)))
                            text(sms_code)
                            performance = get_performance(deviceid, performance)
                            after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                            res_log = f"输入手机验证码：{sms_code}， 成功"
                            loop.run_until_complete(
                                _log_result(
                                    deviceid=deviceid,
                                    result_id=result_id,
                                    menu_id=menu_id,
                                    name=str(j.get("name") or ""),
                                    status=1,
                                    log=res_log,
                                    before_img=before_img,
                                    after_img=after_img,
                                    performance=performance,
                                    video="",
                                    assert_value={},
                                    user_id=user_id,
                                )
                            )
                        else:
                            res_log = f'{android.get("img")}，图像识别失败'
                            after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                            performance = get_performance(deviceid, performance)
                            loop.run_until_complete(
                                _log_result(
                                    deviceid=deviceid,
                                    result_id=result_id,
                                    menu_id=menu_id,
                                    name=str(j.get("name") or ""),
                                    status=0,
                                    log=res_log,
                                    before_img=before_img,
                                    after_img=after_img,
                                    performance=performance,
                                    video="",
                                    assert_value={},
                                    user_id=user_id,
                                )
                            )
                    except Exception as e:
                        res_log = f"输入手机验证码，失败，原因是：{str(e)}"
                        after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                        performance = get_performance(deviceid, performance)
                        loop.run_until_complete(
                            _log_result(
                                deviceid=deviceid,
                                result_id=result_id,
                                menu_id=menu_id,
                                name=str(j.get("name") or ""),
                                status=0,
                                log=res_log,
                                before_img=before_img,
                                after_img=after_img,
                                performance=performance,
                                video="",
                                assert_value={},
                                user_id=user_id,
                            )
                        )

                elif jtype == 6:
                    try:
                        if j.get("name") == "关闭app，并删除差更文件":
                            device_rm_file(deviceid)
                        if j.get("package"):
                            try:
                                stop_app(j["package"])
                            except Exception:
                                pass
                        after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                        performance = get_performance(deviceid, performance)
                        res_log = f"关闭APP：{j.get('package')}, 成功"
                        loop.run_until_complete(
                            _log_result(
                                deviceid=deviceid,
                                result_id=result_id,
                                menu_id=menu_id,
                                name=str(j.get("name") or ""),
                                status=1,
                                log=res_log,
                                before_img=before_img,
                                after_img=after_img,
                                performance=performance,
                                video="",
                                assert_value={},
                                user_id=user_id,
                            )
                        )
                    except Exception as e:
                        res_log = f"关闭APP：{j.get('package')}, 失败，原因是：{str(e)}"
                        after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                        performance = get_performance(deviceid, performance)
                        loop.run_until_complete(
                            _log_result(
                                deviceid=deviceid,
                                result_id=result_id,
                                menu_id=menu_id,
                                name=str(j.get("name") or ""),
                                status=0,
                                log=res_log,
                                before_img=before_img,
                                after_img=after_img,
                                performance=performance,
                                video="",
                                assert_value={},
                                user_id=user_id,
                            )
                        )

                elif jtype == 7:
                    try:
                        performance = get_performance(deviceid, performance)
                        time.sleep(2)
                        keyevent("TAB")
                        time.sleep(2)
                        if j.get("value"):
                            res_log = f"输入：{j['value']}， 输入完成"
                            text(j["value"], enter=False)
                        else:
                            res_log = "Tab按键模拟成功"
                        time.sleep(2)
                        after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                        loop.run_until_complete(
                            _log_result(
                                deviceid=deviceid,
                                result_id=result_id,
                                menu_id=menu_id,
                                name=str(j.get("name") or ""),
                                status=1,
                                log=res_log,
                                before_img=before_img,
                                after_img=after_img,
                                performance=performance,
                                video="",
                                assert_value={},
                                user_id=user_id,
                            )
                        )
                    except Exception as e:
                        res_log = f"Tab操作失败，原因是：{str(e)}"
                        after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                        performance = get_performance(deviceid, performance)
                        loop.run_until_complete(
                            _log_result(
                                deviceid=deviceid,
                                result_id=result_id,
                                menu_id=menu_id,
                                name=str(j.get("name") or ""),
                                status=0,
                                log=res_log,
                                before_img=before_img,
                                after_img=after_img,
                                performance=performance,
                                video="",
                                assert_value={},
                                user_id=user_id,
                            )
                        )

                elif jtype == 8:
                    try:
                        performance = get_performance(deviceid, performance)
                        time.sleep(2)
                        keyevent("ENTER")
                        time.sleep(4)
                        if j.get("value"):
                            res_log = f"输入：{j['value']}， 输入完成"
                            text(j["value"], enter=False)
                        else:
                            res_log = "回车按键模拟成功"
                        time.sleep(2)
                        after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                        loop.run_until_complete(
                            _log_result(
                                deviceid=deviceid,
                                result_id=result_id,
                                menu_id=menu_id,
                                name=str(j.get("name") or ""),
                                status=1,
                                log=res_log,
                                before_img=before_img,
                                after_img=after_img,
                                performance=performance,
                                video="",
                                assert_value={},
                                user_id=user_id,
                            )
                        )
                    except Exception as e:
                        res_log = f"回车操作失败，原因是：{str(e)}"
                        after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                        performance = get_performance(deviceid, performance)
                        loop.run_until_complete(
                            _log_result(
                                deviceid=deviceid,
                                result_id=result_id,
                                menu_id=menu_id,
                                name=str(j.get("name") or ""),
                                status=0,
                                log=res_log,
                                before_img=before_img,
                                after_img=after_img,
                                performance=performance,
                                video="",
                                assert_value={},
                                user_id=user_id,
                            )
                        )
                elif jtype == 9:
                    pass
                else:
                    after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                    performance = get_performance(deviceid, performance)
                    loop.run_until_complete(
                        _log_result(
                            deviceid=deviceid,
                            result_id=result_id,
                            menu_id=menu_id,
                            name=str(j.get("name") or f"type{jtype}"),
                            status=0,
                            log=f"未知步骤类型: {jtype}",
                            before_img=before_img,
                            after_img=after_img,
                            performance=performance,
                            video="",
                            assert_value={},
                            user_id=user_id,
                        )
                    )

            except Exception as e:
                after_img = _airtest_snapshot(driver, deviceid, result_id, pr)
                performance = get_performance(deviceid, performance)
                loop.run_until_complete(
                    _log_result(
                        deviceid=deviceid,
                        result_id=result_id,
                        menu_id=menu_id,
                        name=str(j.get("name") or ""),
                        status=0,
                        log=f"步骤异常: {e}",
                        before_img=before_img,
                        after_img=after_img,
                        performance=performance,
                        video="",
                        assert_value={},
                        user_id=user_id,
                    )
                )

    try:
        driver.stop_recording()
    except Exception:
        pass

    end_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    loop.run_until_complete(_task_end_legacy(result_id=result_id, deviceid=deviceid, user_id=user_id, total=total_steps, end_time=end_ts))

    performance = get_performance(deviceid, performance)
    video_url = f"{get_public_base_url()}/media/app_result/{result_id}/{deviceid}/{result_id}.mp4" if video else ""
    loop.run_until_complete(
        _log_result(
            deviceid=deviceid,
            result_id=result_id,
            menu_id=menu_id,
            name="执行结束",
            status=1,
            log="自动化任务执行完成，请查看执行结果",
            before_img="",
            after_img="",
            performance=performance,
            video=video_url,
            assert_value={},
            user_id=user_id,
        )
    )
    loop.run_until_complete(_release_device(deviceid, user_id))


def _template_abs(img: Any, project_root: Path) -> str:
    from .airtest_common import _template_path

    if img is None:
        return ""
    s = str(img)
    return _template_path(s, project_root)
