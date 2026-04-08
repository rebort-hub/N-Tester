"""
Web管理模块 - Playwright 执行引擎
"""

from __future__ import annotations
import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from config import config as app_config
from .model import WebResultDetailModel, WebResultListModel


def _playwright_base_dir() -> Path:
    
    backend_root = Path(__file__).resolve().parents[4]
    return backend_root / app_config.STATIC_DIR / "media" / "playwright"

async def _ai_action_on_page(page, cmd: str, result_id: str, browser: int) -> tuple[bool, str]:
    """
    使用项目内置 LLM（AIModelService）在当前 playwright page 上执行自然语言指令。
    流程：截图 → 发给 LLM（视觉模型）→ 解析返回的操作 → 在 page 上执行。
    """
    import base64
    import json as _json
    from app.db.sqlalchemy import async_session_factory
    from app.models.ai.llm_config import LLMConfigModel
    from app.services.ai.ai_model_service import AIModelService
    from sqlalchemy import select as _select

    # 1. 获取默认 LLM 配置
    async with async_session_factory() as db:
        res = await db.execute(
            _select(LLMConfigModel).where(
                LLMConfigModel.is_default == True,
                LLMConfigModel.is_active == True,
                LLMConfigModel.enabled_flag == 1,
            )
        )
        llm_config = res.scalar_one_or_none()
        if not llm_config:
            # 没有默认配置时取第一个可用的
            res2 = await db.execute(
                _select(LLMConfigModel).where(
                    LLMConfigModel.is_active == True,
                    LLMConfigModel.enabled_flag == 1,
                ).limit(1)
            )
            llm_config = res2.scalar_one_or_none()

    if not llm_config:
        return False, "AI操作失败：未找到可用的LLM配置，请在系统设置中配置AI模型"

    # 2. 截取当前页面截图（base64）
    try:
        screenshot_bytes = await page.screenshot(type="jpeg", quality=80)
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
    except Exception as e:
        return False, f"AI操作失败：截图异常 {str(e)}"

    # 3. 构造 prompt，要求 LLM 返回结构化操作
    system_prompt = (
        "你是一个网页自动化助手。用户会给你一张网页截图和一个操作指令，"
        "你需要分析截图并返回一个JSON对象，描述要执行的操作。\n"
        "返回格式（只返回JSON，不要有其他文字）：\n"
        '{"action": "click|fill|select|press|scroll", '
        '"selector": "CSS选择器或空字符串", '
        '"x": 点击的X坐标（仅click时使用，无selector时填写）, '
        '"y": 点击的Y坐标（仅click时使用，无selector时填写）, '
        '"value": "输入值（fill/select/press时使用）", '
        '"description": "操作描述"}'
    )

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{screenshot_b64}", "detail": "high"},
                },
                {"type": "text", "text": f"请根据截图执行以下操作：{cmd}"},
            ],
        }
    ]

    # 4. 调用 LLM
    try:
        resp = await AIModelService.call_openai_compatible_api(llm_config, messages, max_tokens=512)
        content = resp["choices"][0]["message"]["content"].strip()
        # 提取 JSON（兼容 LLM 在 JSON 前后加了说明文字的情况）
        start = content.find("{")
        end = content.rfind("}") + 1
        if start == -1 or end == 0:
            return False, f"AI操作失败：LLM未返回有效JSON，原始回复：{content[:200]}"
        op = _json.loads(content[start:end])
    except Exception as e:
        return False, f"AI操作失败：LLM调用异常 {str(e)}"

    # 5. 在 page 上执行操作
    action = op.get("action", "")
    selector = op.get("selector", "")
    value = op.get("value", "")
    desc = op.get("description", cmd)

    try:
        if action == "click":
            if selector:
                await page.locator(selector).first.click(timeout=10000)
            else:
                await page.mouse.click(float(op.get("x", 0)), float(op.get("y", 0)))
        elif action == "fill":
            await page.locator(selector).first.fill(str(value), timeout=10000)
        elif action == "select":
            await page.locator(selector).first.select_option(str(value), timeout=10000)
        elif action == "press":
            if selector:
                await page.locator(selector).first.press(str(value), timeout=10000)
            else:
                await page.keyboard.press(str(value))
        elif action == "scroll":
            await page.mouse.wheel(0, float(value) if value else 300)
        else:
            return False, f"AI操作失败：不支持的操作类型 '{action}'"

        await write_log(f"AI操作执行成功：{desc}", browser, result_id)
        return True, f"AI操作执行成功：{desc}"
    except Exception as e:
        return False, f"AI操作执行失败：{desc}，原因：{str(e)}"


async def run_web_async(
    data: Dict[str, Any],
    run_browser_type: int,
    *,
    session_factory: async_sessionmaker[AsyncSession],
) -> Tuple[bool, str]:
    browser_type = int(data["browser"])
    script = data["script"]
    result_id = str(data["result_id"])
    width = int(data["width"] or 1920) if data.get("width") is not None else 1920
    height = int(data["height"] or 1080) if data.get("height") is not None else 1080
    headless = False if int(run_browser_type) == 1 else True

    # channel 仅在 Windows 本地有效（需要系统安装对应浏览器）
    # Linux/Ubuntu 服务器上只有 playwright install 安装的浏览器，不能指定 channel
    import platform
    _is_linux = platform.system().lower() != "windows"

    launch_config = {
        1: {"browser": "chromium", "channel": "chrome"},
        2: {"browser": "firefox", "channel": None},
        3: {"browser": "chromium", "channel": "msedge"},
        4: {"browser": "webkit", "channel": None},
    }
    cfg = launch_config.get(browser_type, {"browser": "chromium", "channel": "chrome"})

    # Linux 服务器：不使用 channel（依赖 playwright install 的浏览器），强制 headless
    if _is_linux:
        channel = None
        headless = True
    else:
        channel = cfg.get("channel")

    base_dir = _playwright_base_dir() / result_id / str(browser_type)
    base_dir.mkdir(parents=True, exist_ok=True)

    try:
        async with async_playwright() as playwright:
            launch_kwargs = {"headless": headless}
            if channel:
                launch_kwargs["channel"] = channel
            browser = await getattr(playwright, cfg["browser"]).launch(**launch_kwargs)
            context = await browser.new_context(
                viewport={"width": width, "height": height},
                record_video_dir=base_dir,
            )
            await context.tracing.start(screenshots=True, snapshots=True, sources=True)

            ok, msg = await run_script_async(
                browser_type,
                script,
                result_id,
                context,
                session_factory=session_factory,
            )

            await context.close()
            await browser.close()

            # video 文件写回 DB
            video_files = [f for f in os.listdir(base_dir) if f.endswith(".webm")]
            if video_files:
                async with session_factory() as session:
                    res = await session.execute(
                        select(WebResultDetailModel).where(
                            WebResultDetailModel.enabled_flag == 1,
                            WebResultDetailModel.result_id == result_id,
                            WebResultDetailModel.browser == str(browser_type),
                            WebResultDetailModel.log == "执行结束",
                        )
                    )
                    end_row = res.scalar_one_or_none()
                    if end_row:
                        end_row.video = f"/media/playwright/{result_id}/{browser_type}/{video_files[0]}"
                    # 标记执行结束（单浏览器完成即结束状态；汇总统计在 run_end 中写入 result 字段）
                    l = await session.execute(
                        select(WebResultListModel).where(
                            WebResultListModel.enabled_flag == 1,
                            WebResultListModel.result_id == result_id,
                        )
                    )
                    list_row = l.scalar_one_or_none()
                    if list_row:
                        list_row.status = 1
                    await session.commit()

            return ok, msg
    except Exception as e:
        # 确保执行列表最终释放，并写入错误日志
        try:
            await write_log(f"Playwright 启动异常: {str(e)}", browser_type, result_id)
        except Exception:
            pass
        async with session_factory() as session:
            l = await session.execute(
                select(WebResultListModel).where(
                    WebResultListModel.enabled_flag == 1,
                    WebResultListModel.result_id == result_id,
                )
            )
            list_row = l.scalar_one_or_none()
            if list_row:
                list_row.status = 1
                list_row.end_time = datetime.now()
            await session.commit()
        return False, f"Playwright 执行失败: {str(e)}"


async def run_script_async(
    browser: int,
    script: List[Dict[str, Any]],
    result_id: str,
    context,
    *,
    session_factory: async_sessionmaker[AsyncSession],
) -> Tuple[bool, str]:
    driver = None
    for step in script:
        now_time = datetime.now()
        status = 1
        assert_list: List[Dict[str, Any]] = []
        result: Tuple[bool, str, Any] = (False, f"元素{step.get('action', {}).get('element')}识别失败，未找到元素", None)

        if not step.get("status", True):
            continue

        menu_id = step.get("menu_id")
        if step.get("type") not in (0, 13):
            before_img = await playwright_screenshot(driver, browser, result_id)
            await before_element_wait(driver, browser, result_id, int(step["action"].get("before_wait") or 1))
        else:
            before_img = ""

        try:
            await write_log(f"正在执行步骤：{step['name']}", browser, result_id)
            t = int(step["type"])
            action = step.get("action") or {}

            if t == 0:
                if action.get("localstorage"):
                    await set_localstorage(context, action["localstorage"], browser, result_id)
                if action.get("cookies"):
                    await set_cookie(context, action["cookies"], browser, result_id, action.get("element") or "")
                ok, msg, driver = await open_url(browser, action, result_id, context)
                result = (ok, msg, driver)
            elif t == 13:
                # 新窗口
                if action.get("localstorage"):
                    await set_localstorage(context, action["localstorage"], browser, result_id)
                if action.get("cookies"):
                    await set_cookie(context, action["cookies"], browser, result_id, action.get("element") or "")
                ok, msg, driver, context = await element_new_page(context, step["name"], browser, result_id, action.get("element") or "")
                result = (ok, msg, driver)
            else:
                ok, el = await handle_element(driver, action, result_id, browser)
                if t == 1 and ok:
                    result = (await element_click(step["name"], browser, result_id, el)) + (None,)
                elif t == 2 and ok:
                    result = (await element_dblclick(step["name"], browser, result_id, el)) + (None,)
                elif t == 3 and ok:
                    result = (await element_longclick(driver, step["name"], browser, result_id, el)) + (None,)
                elif t == 4:
                    ta_ok, target = await ta_handle_element(driver, action, result_id, browser)
                    if ok and ta_ok:
                        result = (await element_drop(driver, step["name"], browser, result_id, el, target)) + (None,)
                    elif not ok:
                        result = (False, str(el), None)
                    else:
                        result = (False, str(target), None)
                elif t == 5 and ok:
                    result = (await element_input(step["name"], browser, result_id, el, action.get("input") or "")) + (None,)
                elif t == 6 and ok:
                    result = (await element_add_input(step["name"], browser, result_id, el, action.get("input") or "")) + (None,)
                elif t == 7 and ok:
                    result = (await element_input_clear(step["name"], browser, result_id, el)) + (None,)
                elif t == 8:
                    result = (await element_sway_up(driver, step["name"], browser, result_id, action)) + (None,)
                elif t == 9:
                    result = (await element_sway_left(driver, step["name"], browser, result_id, action)) + (None,)
                elif t == 10:
                    if_dict = {
                        "type": action.get("type"),
                        "element": action.get("element"),
                        "locator": action.get("locator"),
                        "locator_select": action.get("locator_select"),
                        "page_type": action.get("target_type"),
                        "role": action.get("input"),
                    }
                    ok_if, msg_if = await element_if(driver, step["name"], browser, result_id, if_dict, None)
                    result = (ok_if, msg_if, None)
                    if ok_if and step.get("children"):
                        await element_for(
                            driver,
                            step["name"],
                            browser,
                            result_id,
                            1,
                            step["children"],
                            context,
                            session_factory=session_factory,
                        )
                elif t == 11:
                    if step.get("children"):
                        loop_num = int(action.get("element") or 1)
                        ok_for, msg_for = await element_for(
                            driver,
                            step["name"],
                            browser,
                            result_id,
                            loop_num,
                            step["children"],
                            context,
                            session_factory=session_factory,
                        )
                        result = (ok_for, msg_for, None)
                    else:
                        result = (True, f"{step['name']}执行成功", None)
                elif t == 12:
                    result = (await element_wait(driver, step["name"], browser, result_id, int(action.get("element") or 1))) + (None,)
                elif t == 14:
                    ok_sw, msg_sw, driver = await element_switch_page(context, step["name"], browser, result_id, "previous", driver)
                    result = (ok_sw, msg_sw, driver)
                elif t == 15:
                    ok_sw, msg_sw, driver = await element_switch_page(context, step["name"], browser, result_id, "next", driver)
                    result = (ok_sw, msg_sw, driver)
                elif t == 16 and ok:
                    result = (await element_right_click(step["name"], browser, result_id, el)) + (None,)
                elif t == 17:
                    ok_ev, msg_ev = await element_eval(driver, str(action.get("element") or ""), result_id, browser)
                    result = (ok_ev, msg_ev, None)
                elif t == 18 and ok:
                    ok_up, msg_up = await element_upload_file(el, step["name"], browser, result_id, str(action.get("input") or ""))
                    result = (ok_up, msg_up, None)
                elif t == 19:
                    cmd = str(action.get("element") or "")
                    await write_log(f"开始执行AI操作：{cmd}", browser, result_id)
                    ok_ai, msg_ai = await _ai_action_on_page(driver, cmd, result_id, browser)
                    result = (ok_ai, msg_ai, None)
                elif t == 20:
                    ok_rl, msg_rl = await element_reload_page(driver, step["name"], browser, result_id)
                    result = (ok_rl, msg_rl, None)
                elif t == 21:
                    ok_cl, msg_cl, driver, context = await element_close_page(
                        context,
                        step["name"],
                        browser,
                        result_id,
                        str(action.get("target") or "now"),
                        action.get("element"),
                        driver,
                    )
                    result = (ok_cl, msg_cl, driver)
                else:
                    if not ok:
                        result = (False, str(el), None)
                    else:
                        result = (True, f"{step['name']}执行成功", None)

 
            if action.get("assert"):
                status, assert_list = await element_assert(driver, browser, result_id, action["assert"], None)

            await write_result(
                step["name"],
                result[1],
                browser,
                result_id,
                status if result[0] else 0,
                before_img,
                after_img,
                "",
                assert_list,
                menu_id,
                now_time,
                "",
                session_factory=session_factory,
            )
            await after_element_wait(driver, browser, result_id, int(action.get("after_wait") or 1))
        except Exception as e:
            after_img = await playwright_screenshot(driver, browser, result_id)
            await write_result(
                step.get("name") or "未知步骤",
                f"{result[1]}",
                browser,
                result_id,
                0,
                before_img,
                after_img,
                "",
                assert_list,
                menu_id,
                now_time,
                "",
                session_factory=session_factory,
            )
            await write_log(f"步骤异常：{str(e)}", browser, result_id)

    # trace & end
    base_dir = _playwright_base_dir() / result_id / str(browser)
    base_dir.mkdir(parents=True, exist_ok=True)
    trace_path = base_dir / "trace.zip"
    try:
        await context.tracing.stop(path=trace_path)
    except Exception as e:
        await write_log(f"trace保存失败：{str(e)}", browser, result_id)

    if driver:
        try:
            await driver.close()
        except Exception as e:
            await write_log(f"页面关闭失败：{str(e)}", browser, result_id)

    await write_result(
        "执行结束",
        "执行结束",
        browser,
        result_id,
        1,
        "",
        "",
        "",
        [],
        None,
        datetime.now(),
        f"/media/playwright/{result_id}/{browser}/trace.zip",
        session_factory=session_factory,
    )
    await write_log("执行结束", browser, result_id)
    await run_end(result_id, browser, session_factory=session_factory)
    return True, "任务执行成功"


async def run_end(result_id: str, browser: int, *, session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        detail_res = await session.execute(
            select(WebResultDetailModel).where(
                WebResultDetailModel.enabled_flag == 1,
                WebResultDetailModel.result_id == result_id,
                WebResultDetailModel.browser == str(browser),
            )
        )
        details = detail_res.scalars().all()
        total = max(len(details) - 1, 0)
        run_false = len([d for d in details if int(d.status) == 0])
        run_true = total - run_false
        result = {"browser": browser, "total": total, "run_true": run_true, "run_false": run_false}

        list_res = await session.execute(
            select(WebResultListModel).where(
                WebResultListModel.enabled_flag == 1,
                WebResultListModel.result_id == result_id,
            )
        )
        row = list_res.scalar_one_or_none()
        if row:
            current = row.result or []
            current.append(result)
            row.result = current
            row.end_time = datetime.now()
        await session.commit()


async def playwright_screenshot(driver, browser: int, result_id: str) -> str:
    if not driver:
        return ""
    base_dir = _playwright_base_dir() / result_id / str(browser)
    base_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{browser}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}_web.png"
    path = base_dir / filename
    await driver.screenshot(path=path)
    return f"/media/playwright/{result_id}/{browser}/{filename}"


async def write_log(result: str, browser: int, result_id: str) -> None:
    base_dir = _playwright_base_dir() / result_id / str(browser)
    base_dir.mkdir(parents=True, exist_ok=True)
    path = base_dir / f"{browser}_result.txt"
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {result} \n")


async def write_result(
    name: str,
    log: str,
    browser: int,
    result_id: str,
    status: int,
    before_img: str,
    after_img: str,
    video: str,
    assert_result: List[Dict[str, Any]],
    menu_id: Optional[int],
    now_time: datetime,
    trace: str,
    *,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        row = WebResultDetailModel(
            name=name,
            result_id=result_id,
            browser=str(browser),
            log=log,
            status=int(status),
            before_img=before_img,
            after_img=after_img,
            video=video,
            trace=trace,
            assert_result=assert_result or [],
            menu_id=menu_id,
        )
        session.add(row)
        await session.commit()


async def open_url(browser: int, action: Dict[str, Any], result_id: str, context):
    driver = await context.new_page()
    url = action.get("element") or ""
    await driver.goto(url, wait_until="networkidle")
    await driver.wait_for_timeout(1000)
    await write_log(f"网页打开成功，网页地址：{url}", browser, result_id)
    return True, f"网页打开成功，网页地址：{url}", driver


async def set_localstorage(context, localstorage: List[Dict[str, Any]], browser: int, result_id: str) -> bool:
    await write_log("开始设置localStorage", browser, result_id)
    for i in localstorage:
        await context.add_init_script(script=f"localStorage.setItem('{i['name']}', '{i['value']}');")
        await write_log(f"localStorage设置成功,  key={i['name']}, value={i['value']}", browser, result_id)
    return True


async def set_cookie(context, cookies: List[Dict[str, Any]], browser: int, result_id: str, url: str) -> bool:
    parsed = urlparse(url) if url else None
    await write_log("开始设置cookie", browser, result_id)
    for c in cookies:
        if parsed:
            c["url"] = f"{parsed.scheme}://{parsed.netloc}"
    await context.add_cookies(cookies)
    return True


async def handle_element(driver, action: Dict[str, Any], result_id: str, browser: int):
    try:
        element_value = action.get("element") or ""
        if "," in element_value:
            for cand in element_value.split(","):
                action["element"] = cand
                ok, el = await locator_action(driver, action, result_id, browser)
                if ok:
                    return True, el
            return False, f"元素{element_value}识别失败，未找到元素"
        return await locator_action(driver, action, result_id, browser)
    except Exception as e:
        return False, str(e)

async def ta_handle_element(driver, action: Dict[str, Any], result_id: str, browser: int):

    try:
        element_value = action.get("target") or ""
        if not element_value:
            return False, "目标元素为空"
        target_locator = int(action.get("target_locator") or 1)
        target_locator_select = int(action.get("target_locator_select") or 1)
        role = action.get("role")
        timeout = int(action.get("timeout") or 15) * 1000

        if target_locator == 1:
            element = driver.locator(element_value)
        else:
            if target_locator_select == 1:
                element = driver.locator(f"#{element_value}")
            elif target_locator_select == 2:
                element = driver.get_by_text(element_value)
            elif target_locator_select == 3:
                element = driver.get_by_label(element_value)
            elif target_locator_select == 4:
                element = driver.get_by_title(element_value)
            elif target_locator_select == 5:
                element = driver.get_by_placeholder(element_value, exact=True)
            elif target_locator_select == 6:
                element = driver.get_by_alt_text(element_value)
            else:
                element = driver.get_by_role(role, name=element_value)
        await element.wait_for(state="visible", timeout=timeout)
        if await element.is_visible():
            return True, element
        return False, f"目标元素{element_value}识别失败，未找到元素"
    except Exception as e:
        await write_log(f"目标元素定位失败，原因是：{str(e)}", browser, result_id)
        return False, str(e)

async def locator_action(driver, action: Dict[str, Any], result_id: str, browser: int):
    try:
        element_value = action.get("element") or ""
        locator = int(action.get("locator") or 1)
        locator_select = int(action.get("locator_select") or 1)
        role = action.get("role")
        timeout = int(action.get("timeout") or 15) * 1000

        if locator == 1:
            element = driver.locator(element_value)
        else:
            if locator_select == 1:
                element = driver.locator(f"#{element_value}")
            elif locator_select == 2:
                element = driver.get_by_text(element_value)
            elif locator_select == 3:
                element = driver.get_by_label(element_value)
            elif locator_select == 4:
                element = driver.get_by_title(element_value)
            elif locator_select == 5:
                element = driver.get_by_placeholder(element_value, exact=True)
            elif locator_select == 6:
                element = driver.get_by_alt_text(element_value)
            else:
                element = driver.get_by_role(role, name=element_value)
        await element.wait_for(state="visible", timeout=timeout)
        if await element.is_visible():
            return True, element
        return False, f"元素{element_value}识别失败，未找到元素"
    except Exception as e:
        await write_log(f"元素定位失败，原因是：{str(e)}", browser, result_id)
        return False, str(e)

async def assert_locator_action(driver, action: Dict[str, Any], result_id: str, browser: int):

    element_value = action.get("element") or ""
    locator = int(action.get("locator") or 1)
    locator_select = int(action.get("locator_select") or 1)
    role = action.get("role")
    if locator == 1:
        return driver.locator(element_value)
    if locator_select == 1:
        return driver.locator(f"#{element_value}")
    if locator_select == 2:
        return driver.get_by_text(element_value)
    if locator_select == 3:
        return driver.get_by_label(element_value)
    if locator_select == 4:
        return driver.get_by_title(element_value)
    if locator_select == 5:
        return driver.get_by_placeholder(element_value, exact=True)
    if locator_select == 6:
        return driver.get_by_alt_text(element_value)
    return driver.get_by_role(role, name=element_value)


async def element_click(name: str, browser: int, result_id: str, element) -> Tuple[bool, str]:
    try:
        await element.click()
        await write_log(f"{name}：元素点击成功", browser, result_id)
        return True, f"{name}：元素点击成功"
    except Exception as e:
        await write_log(f"{name}：执行失败 原因是：{str(e)}", browser, result_id)
        return False, f"{name}：执行失败 原因是：{str(e)}"

async def element_right_click(name: str, browser: int, result_id: str, element) -> Tuple[bool, str]:
    try:
        await element.click(button="right")
        await write_log(f"{name}：元素右键点击成功", browser, result_id)
        return True, f"{name}：元素右键点击成功"
    except Exception as e:
        await write_log(f"{name}：执行失败 原因是：{str(e)}", browser, result_id)
        return False, f"{name}：执行失败 原因是：{str(e)}"


async def element_dblclick(name: str, browser: int, result_id: str, element) -> Tuple[bool, str]:
    try:
        await element.dblclick()
        await write_log(f"{name}：元素双击成功", browser, result_id)
        return True, f"{name}：元素双击成功"
    except Exception as e:
        await write_log(f"{name}：执行失败 原因是：{str(e)}", browser, result_id)
        return False, f"{name}：执行失败 原因是：{str(e)}"

async def element_longclick(driver, name: str, browser: int, result_id: str, element) -> Tuple[bool, str]:
    try:
        await element.hover()
        await driver.mouse.down(button="left")
        await driver.wait_for_timeout(2500)
        await driver.mouse.up()
        await write_log(f"{name}：元素长按成功", browser, result_id)
        return True, f"{name}：元素长按成功"
    except Exception as e:
        await write_log(f"{name}：执行失败 原因是：{str(e)}", browser, result_id)
        return False, f"{name}：执行失败 原因是：{str(e)}"

async def element_drop(driver, name: str, browser: int, result_id: str, element, target) -> Tuple[bool, str]:
    try:
        from_box = await element.bounding_box()
        await driver.mouse.move(from_box["x"] + from_box["width"] / 2, from_box["y"] + from_box["height"] / 2)
        await driver.mouse.down()
        target_box = await target.bounding_box()
        await driver.mouse.move(target_box["x"] + target_box["width"] / 2, target_box["y"] + target_box["height"] / 2)
        await driver.mouse.up()
        await write_log(f"{name}：元素拖拽成功", browser, result_id)
        return True, f"{name}：元素拖拽成功"
    except Exception as e:
        await write_log(f"{name}：执行失败 原因是：{str(e)}", browser, result_id)
        return False, f"{name}：执行失败 原因是：{str(e)}"


async def element_input(name: str, browser: int, result_id: str, element, input_value: str) -> Tuple[bool, str]:
    try:
        await element.fill(input_value)
        await write_log(f"{name}：输入值--{input_value}--成功", browser, result_id)
        return True, f"{name}：输入值--{input_value}--成功"
    except Exception as e:
        await write_log(f"{name}：执行失败 原因是：{str(e)}", browser, result_id)
        return False, f"{name}：执行失败 原因是：{str(e)}"

async def element_add_input(name: str, browser: int, result_id: str, element, input_value: str) -> Tuple[bool, str]:
    try:
        old_text = await element.input_value()
        await element.fill(old_text + input_value)
        await write_log(f"{name}：补充输入值--{input_value}--成功", browser, result_id)
        return True, f"{name}：补充输入值--{input_value}--成功"
    except Exception as e:
        await write_log(f"{name}：执行失败 原因是：{str(e)}", browser, result_id)
        return False, f"{name}：执行失败 原因是：{str(e)}"


async def element_input_clear(name: str, browser: int, result_id: str, element) -> Tuple[bool, str]:
    try:
        await element.fill("")
        await write_log(f"{name}：清空文本--成功", browser, result_id)
        return True, f"{name}：清空文本--成功"
    except Exception as e:
        await write_log(f"{name}：执行失败 原因是：{str(e)}", browser, result_id)
        return False, f"{name}：执行失败 原因是：{str(e)}"

async def element_sway_up(driver, name: str, browser: int, result_id: str, action: Dict[str, Any]) -> Tuple[bool, str]:
    try:
        num = int(action.get("element") or 0)
        up_type = int(action.get("up_type") or 1)
        if up_type == 1:
            await driver.mouse.wheel(0, delta_y=-num)
            msg = f"{name}：向上滑动像素--{num}--成功"
        else:
            await driver.mouse.wheel(0, delta_y=num)
            msg = f"{name}：向下滑动像素--{num}--成功"
        await write_log(msg, browser, result_id)
        return True, msg
    except Exception as e:
        msg = f"{name}：执行失败 原因是：{str(e)}"
        await write_log(msg, browser, result_id)
        return False, msg

async def element_sway_left(driver, name: str, browser: int, result_id: str, action: Dict[str, Any]) -> Tuple[bool, str]:
    try:
        num = int(action.get("element") or 0)
        sway_type = int(action.get("sway_type") or 1)
        if sway_type == 1:
            await driver.scroll_by(0, num)
            msg = f"{name}：向左滑动像素--{num}--成功"
        else:
            await driver.scroll_by(0, -num)
            msg = f"{name}：向右滑动像素--{num}--成功"
        await write_log(msg, browser, result_id)
        return True, msg
    except Exception as e:
        msg = f"{name}：执行失败 原因是：{str(e)}"
        await write_log(msg, browser, result_id)
        return False, msg

async def element_if(driver, name: str, browser: int, result_id: str, if_dict: Dict[str, Any], ai) -> Tuple[bool, str]:
    try:
        status, _ = await element_assert(driver, browser, result_id, [if_dict], None)
        if status == 1:
            msg = f"{name}：判断成功，元素存在"
            await write_log(msg, browser, result_id)
            return True, msg
        msg = f"{name}：判断失败，元素不存在"
        await write_log(msg, browser, result_id)
        return False, msg
    except Exception as e:
        msg = f"{name}：执行失败 原因是：{str(e)}"
        await write_log(msg, browser, result_id)
        return False, msg

async def element_for(
    driver,
    name: str,
    browser: int,
    result_id: str,
    num: int,
    script: List[Dict[str, Any]],
    context,
    *,
    session_factory: async_sessionmaker[AsyncSession],
) -> Tuple[bool, str]:
    try:
        for _ in range(0, int(num or 1)):
            await run_script_async(
                browser,
                script,
                result_id,
                context,
                session_factory=session_factory,
            )
        msg = f"{name}：执行成功"
        await write_log(msg, browser, result_id)
        return True, msg
    except Exception as e:
        msg = f"{name}：执行失败 原因是：{str(e)}"
        await write_log(msg, browser, result_id)
        return False, msg


async def element_wait(driver, name: str, browser: int, result_id: str, wait_time: int) -> Tuple[bool, str]:
    try:
        await driver.wait_for_timeout(int(wait_time))
        await write_log(f"{name}：等待--{wait_time}秒--成功", browser, result_id)
        return True, f"{name}：等待--{wait_time}秒--成功"
    except Exception as e:
        await write_log(f"{name}：执行失败 原因是：{str(e)}", browser, result_id)
        return False, f"{name}：执行失败 原因是：{str(e)}"


async def before_element_wait(driver, browser: int, result_id: str, wait_time: int) -> None:
    if driver:
        await driver.wait_for_timeout(int(wait_time))


async def after_element_wait(driver, browser: int, result_id: str, wait_time: int) -> None:
    if driver:
        await driver.wait_for_timeout(int(wait_time))

async def element_new_page(context, name: str, browser: int, result_id: str, element: str):
    try:
        await asyncio.sleep(1)
        driver = await context.new_page()
        await driver.goto(element)
        msg = f"{name}：打开新窗口--{element}--成功"
        await write_log(msg, browser, result_id)
        return True, msg, driver, context
    except Exception as e:
        msg = f"{name}：执行失败 原因是：{str(e)}"
        await write_log(msg, browser, result_id)
        return False, msg, None, context

async def element_switch_page(context, name: str, browser: int, result_id: str, direction: str, driver):
    try:
        pages = context.pages
        current_index = pages.index(driver) if driver in pages else 0
        if direction == "next":
            if current_index < len(pages) - 1:
                next_page = pages[current_index + 1]
                await next_page.bring_to_front()
                msg = "切换到下一个标签页，成功"
                await write_log(msg, browser, result_id)
                return True, msg, next_page
            msg = "执行失败，已经是最后一个标签页，无法向下切换"
            await write_log(msg, browser, result_id)
            return False, msg, driver
        if direction == "previous":
            if current_index > 0:
                prev_page = pages[current_index - 1]
                await prev_page.bring_to_front()
                msg = "切换到上一个标签页，成功"
                await write_log(msg, browser, result_id)
                return True, msg, prev_page
            msg = "执行失败，已经是第一个标签页，无法向下切换"
            await write_log(msg, browser, result_id)
            return False, msg, driver
        msg = "执行失败，无效的方向"
        await write_log(msg, browser, result_id)
        return False, msg, driver
    except Exception as e:
        msg = f"{name}：执行失败 原因是：{str(e)}"
        await write_log(msg, browser, result_id)
        return False, msg, driver

async def element_close_page(context, name: str, browser: int, result_id: str, direction: str, n: Any, driver):
    try:
        pages = context.pages
        current_index = pages.index(driver) if driver in pages else -1
        if direction == "now":
            if current_index == -1:
                return False, "执行失败，当前页面不存在", driver, context
            await driver.close()
            remaining = context.pages
            if remaining:
                new_index = min(current_index, len(remaining) - 1)
                new_driver = remaining[new_index]
                await new_driver.bring_to_front()
                msg = "成功关闭当前页面并切换到新页面"
            else:
                new_driver = await context.new_page()
                await new_driver.goto("about:blank")
                msg = "所有标签页已关闭，已创建新页面"
            await write_log(msg, browser, result_id)
            return True, msg, new_driver, context

        if direction == "next":
            target_index = current_index + 1
        elif direction == "previous":
            target_index = current_index - 1
        elif direction == "customize":
            target_index = int(n or 1) - 1
        else:
            return False, f"无效的方向: {direction}", driver, context

        if target_index < 0 or target_index >= len(pages):
            return False, f"目标页面索引 {target_index} 超出范围", driver, context

        await pages[target_index].close()
        msg = f"成功关闭{direction}方向的页面"
        await write_log(msg, browser, result_id)
        return True, msg, driver, context
    except Exception as e:
        msg = f"{name}操作失败: {str(e)}"
        await write_log(msg, browser, result_id)
        return False, msg, driver, context

async def element_upload_file(element_or_page, name: str, browser: int, result_id: str, element: str):
    try:
        # 优先 locator.set_input_files，否则退回 page.set_input_files
        file_path = element
        if file_path and not os.path.isabs(file_path):
    
            file_path = str(Path(app_config.BASEDIR) / file_path.lstrip("/\\"))
        if hasattr(element_or_page, "set_input_files"):
            await element_or_page.set_input_files(file_path)
        else:
            await element_or_page.set_input_files(file_path)
        await write_log("执行上传文件成功", browser, result_id)
        return True, "执行上传文件成功"
    except Exception as e:
        msg = f"{name}：执行失败 原因是：{str(e)}"
        await write_log(msg, browser, result_id)
        return False, msg

async def element_eval(driver, element: str, result_id: str, browser: int):
    try:
        from playwright.async_api import expect  # noqa: F401
        page = driver
        await write_log(f"正在执行自定义脚本：{element}", browser, result_id)

        eval(element, {"page": page, "driver": driver, "expect": expect})
        await write_log("执行自定义脚本成功", browser, result_id)
        return True, f"执行自定义脚本成功: {element}"
    except Exception as e:
        await write_log(f"执行自定义脚本失败，原因是：{str(e)}", browser, result_id)
        return False, str(e)

async def element_reload_page(driver, name: str, browser: int, result_id: str):
    try:
        await write_log(f"正在刷新当前页面：{name}", browser, result_id)
        await driver.reload()
        time.sleep(1)
        return True, "刷新当前页面成功"
    except Exception as e:
        msg = f"刷新当前页面失败，原因是：{str(e)}"
        await write_log(msg, browser, result_id)
        return False, msg


async def element_assert(driver, browser: int, result_id: str, assert_list: List[Dict[str, Any]], ai=None):
    status = 1
    for a in assert_list:
        try:
            a["img"] = await playwright_screenshot(driver, browser, result_id)
            t = int(a.get("type") or 1)
            if t in (1, 2):
                el = await assert_locator_action(driver, a, result_id, browser)
                exists = await el.is_visible()
                if t == 1 and exists:
                    a["status"] = 1
                    a["result"] = "断言成功，元素存在"
                elif t == 2 and (not exists):
                    a["status"] = 1
                    a["result"] = "断言成功，元素不存在"
                else:
                    status = 0
                    a["status"] = 0
                    a["result"] = "断言失败"
            elif t in (3, 4):
                html = await driver.content()
                contains = str(a.get("element") or "") in html
                if (t == 3 and contains) or (t == 4 and not contains):
                    a["status"] = 1
                    a["result"] = "断言成功"
                else:
                    status = 0
                    a["status"] = 0
                    a["result"] = "断言失败"
            elif t == 5:
                title = await driver.title()
                url = driver.url
                page_type = int(a.get("page_type") or 1)
                expected = str(a.get("element") or "")
                ok = (url == expected) if page_type == 1 else (title == expected)
                if ok:
                    a["status"] = 1
                    a["result"] = "断言成功"
                else:
                    status = 0
                    a["status"] = 0
                    a["result"] = "断言失败"
            elif t == 6:
                ok, _ = await assert_eval(driver, str(a.get("element") or ""), result_id, browser)
                if ok:
                    a["status"] = 1
                    a["result"] = "断言成功"
                else:
                    status = 0
                    a["status"] = 0
                    a["result"] = "断言失败"
            elif t == 7:
                if not ai or not hasattr(ai, "ai_assert"):
                    status = 0
                    a["status"] = 0
                    a["result"] = "断言失败，AI组件不可用"
                else:
                    ok = await ai.ai_assert(str(a.get("element") or ""))
                    if ok:
                        a["status"] = 1
                        a["result"] = "断言成功"
                    else:
                        status = 0
                        a["status"] = 0
                        a["result"] = "断言失败"
            else:
                a["status"] = 1
                a["result"] = "断言跳过(未知类型)"
        except Exception as e:
            status = 0
            a["status"] = 0
            a["result"] = f"断言失败，原因是：{str(e)}"
    return status, assert_list

async def assert_eval(driver, element: str, result_id: str, browser: int):
    try:
        from playwright.async_api import expect  # noqa: F401
        page = driver
        await write_log(f"正在执行断言脚本：{element}", browser, result_id)
        eval(element, {"page": page, "driver": driver, "expect": expect})
        await write_log("执行自定义断言成功", browser, result_id)
        return True, "执行断言脚本成功"
    except Exception as e:
        await write_log(f"执行断言脚本失败，原因是：{str(e)}", browser, result_id)
        return False, str(e)

