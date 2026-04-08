"""
Web管理模块业务逻辑服务
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any, Tuple
import os
from datetime import datetime, timedelta
from pathlib import Path
import json
import subprocess
import signal
import multiprocessing
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from .model import (
    WebElementMenuModel,
    WebElementModel,
    WebMenuModel,
    WebScriptModel,
    WebGroupModel,
    WebResultListModel,
    WebResultDetailModel,
)

from config import config as app_config

from app.db.sqlalchemy import async_session_factory

from .playwright_runner import run_web_async
from .web_worker import run_web_task_in_process


async def _get_username_map(db: AsyncSession, user_ids: List[int]) -> Dict[int, str]:

    if not user_ids:
        return {}
    try:
        res = await db.execute(
            text("SELECT id, COALESCE(nickname, username, '') AS name FROM sys_user WHERE id IN :ids"),
            {"ids": tuple(set(user_ids))},
        )
        rows = res.fetchall()
        return {r.id: (r.name or "") for r in rows}
    except Exception:
        return {}


def _build_tree(items: List[Dict[str, Any]], pid_key: str = "pid", id_key: str = "id") -> List[Dict[str, Any]]:

    by_id: Dict[Any, Dict[str, Any]] = {}
    roots: List[Dict[str, Any]] = []
    for it in items:
        node = dict(it)
        node.setdefault("children", [])
        by_id[node.get(id_key)] = node
    for node in by_id.values():
        pid = node.get(pid_key)
        if pid in (None, 0, "0"):
            roots.append(node)
        else:
            parent = by_id.get(pid)
            if parent:
                parent.setdefault("children", []).append(node)
            else:
                roots.append(node)
    return roots


class WebManagementService:


    @staticmethod
    async def get_element_tree(db: AsyncSession, *, only_menu: bool = True) -> List[Dict[str, Any]]:

        result = await db.execute(
            select(
                WebElementMenuModel.id,
                WebElementMenuModel.name,
                WebElementMenuModel.pid,
                WebElementMenuModel.type,
                WebElementMenuModel.element_id,
            ).where(WebElementMenuModel.enabled_flag == 1)
        )
        rows = [
            {
                "id": r.id,
                "name": r.name,
                "pid": r.pid,
                "type": r.type,
                "element_id": r.element_id,
            }
            for r in result.fetchall()
        ]

        if only_menu:
            rows = [r for r in rows if r.get("type") != 2]

        return _build_tree(rows)

    @staticmethod
    async def add_menu(
        db: AsyncSession,
        *,
        name: str,
        pid: int,
        type: int,
        user_id: int,
    ) -> None:
        menu = WebElementMenuModel(
            name=name,
            pid=pid,
            type=type,
            created_by=user_id,
        )
        db.add(menu)
        await db.flush()

    @staticmethod
    async def edit_menu(db: AsyncSession, *, menu_id: int, name: str, user_id: int) -> None:
        result = await db.execute(
            select(WebElementMenuModel).where(
                WebElementMenuModel.id == menu_id,
                WebElementMenuModel.enabled_flag == 1,
            )
        )
        menu = result.scalar_one_or_none()
        if not menu:
            return
        menu.name = name
        menu.last_updated_by = user_id

    @staticmethod
    async def delete_menu(db: AsyncSession, *, menu_id: int) -> None:
        result = await db.execute(
            select(WebElementMenuModel).where(
                WebElementMenuModel.id == menu_id,
                WebElementMenuModel.enabled_flag == 1,
            )
        )
        menu = result.scalar_one_or_none()
        if menu:
            menu.enabled_flag = 0

    @staticmethod
    async def get_element_list(
        db: AsyncSession,
        *,
        page: int,
        page_size: int,
        user_id: int,
    ) -> Dict[str, Any]:

        if page <= 0:
            page = 1
        if page_size <= 0:
            page_size = 10

        base_query = select(WebElementModel).where(
            WebElementModel.enabled_flag == 1,
            WebElementModel.created_by == user_id,
        ).order_by(WebElementModel.id.desc())

        total_result = await db.execute(base_query)
        all_rows = total_result.scalars().all()
        total = len(all_rows)

        start = (page - 1) * page_size
        end = start + page_size
        page_rows = all_rows[start:end]

        content = [
            {
                "id": r.id,
                "name": r.name,
                "element": r.element,
                "menu_id": r.menu_id,
                "creation_date": r.creation_date,
            }
            for r in page_rows
        ]

        return {
            "content": content,
            "totalElements": total,
            "page": page,
            "pageSize": page_size,
        }

    @staticmethod
    async def add_element(
        db: AsyncSession,
        *,
        name: str,
        element: Dict[str, Any],
        menu_id: int,
        user_id: int,
    ) -> None:
        elem = WebElementModel(
            name=name,
            element=element,
            menu_id=menu_id,
            created_by=user_id,
        )
        db.add(elem)
        await db.flush()

        menu = WebElementMenuModel(
            name=name,
            pid=menu_id,
            type=2,
            element_id=elem.id,
            created_by=user_id,
        )
        db.add(menu)

    @staticmethod
    async def edit_element(
        db: AsyncSession,
        *,
        element_id: int,
        name: str,
        element: Dict[str, Any],
        user_id: int,
    ) -> None:
        result = await db.execute(
            select(WebElementModel).where(
                WebElementModel.id == element_id,
                WebElementModel.enabled_flag == 1,
            )
        )
        elem = result.scalar_one_or_none()
        if not elem:
            return

        elem.name = name
        elem.element = element
        elem.last_updated_by = user_id

        menu_result = await db.execute(
            select(WebElementMenuModel).where(
                WebElementMenuModel.element_id == element_id,
                WebElementMenuModel.enabled_flag == 1,
            )
        )
        menu = menu_result.scalar_one_or_none()
        if menu:
            menu.name = name
            menu.last_updated_by = user_id

    @staticmethod
    async def delete_element(db: AsyncSession, *, element_id: int) -> None:
        result = await db.execute(
            select(WebElementModel).where(
                WebElementModel.id == element_id,
                WebElementModel.enabled_flag == 1,
            )
        )
        elem = result.scalar_one_or_none()
        if elem:
            elem.enabled_flag = 0

        menu_result = await db.execute(
            select(WebElementMenuModel).where(
                WebElementMenuModel.element_id == element_id,
                WebElementMenuModel.enabled_flag == 1,
            )
        )
        menu = menu_result.scalar_one_or_none()
        if menu:
            menu.enabled_flag = 0


    @staticmethod
    async def get_web_menu(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:

        result = await db.execute(
            select(
                WebMenuModel.id,
                WebMenuModel.name,
                WebMenuModel.pid,
                WebMenuModel.type,
            ).where(WebMenuModel.enabled_flag == 1)
        )
        rows = [
            {
                "id": r.id,
                "name": r.name,
                "pid": r.pid,
                "type": r.type,
            }
            for r in result.fetchall()
        ]
        return _build_tree(rows)

    @staticmethod
    async def create_web_menu(
        db: AsyncSession,
        *,
        name: str,
        pid: int,
        type: int,
        user_id: int,
    ) -> Dict[str, Any]:

        menu = WebMenuModel(
            name=name,
            pid=pid,
            type=type,
            created_by=user_id,
        )
        db.add(menu)
        await db.flush()


        if type == 2:
            default_script = [
                {
                    "name": "打开",
                    "type": 0,
                    "children": [],
                    "action": {
                        "type": 1,
                        "input": "",
                        "assert": [],
                        "target": "",
                        "element": "",
                        "cookies": [],
                        "localstorage": [],
                        "locator": 1,
                        "up_type": 1,
                        "before_wait": 1,
                        "after_wait": 1,
                        "sway_type": 1,
                        "target_id": "",
                        "wait_time": 1,
                        "element_id": None,
                        "target_type": 1,
                        "locator_select": 1,
                        "target_locator": 1,
                        "target_locator_select": 1,
                        "timeout": 15,
                    },
                    "status": True,
                }
            ]
            script_row = WebScriptModel(
                script=default_script,
                menu_id=menu.id,
                created_by=user_id,
            )
            db.add(script_row)

        return {
            "id": menu.id,
            "name": name,
            "pid": pid,
            "type": type,
        }

    @staticmethod
    async def get_menu_script_list(db: AsyncSession, *, pid: int) -> List[Dict[str, Any]]:

        result = await db.execute(
            select(WebMenuModel).where(
                WebMenuModel.pid == pid,
                WebMenuModel.enabled_flag == 1,
            )
        )
        rows = result.scalars().all()
        return [{"id": r.id, "name": r.name, "type": r.type} for r in rows]

    @staticmethod
    async def delete_web_menu(
        db: AsyncSession,
        *,
        menu_id: int,
        type: int,
    ) -> Tuple[bool, str]:

        if type in (0, 1):
            child_res = await db.execute(
                select(WebMenuModel).where(
                    WebMenuModel.enabled_flag == 1,
                    WebMenuModel.pid == menu_id,
                )
            )
            if child_res.scalars().first():
                return False, "删除失败，该菜单下仍存在子节点"

        res = await db.execute(
            select(WebMenuModel).where(
                WebMenuModel.id == menu_id,
                WebMenuModel.enabled_flag == 1,
            )
        )
        menu = res.scalar_one_or_none()
        if not menu:
            return False, "菜单不存在或已删除"

        menu.enabled_flag = 0


        script_res = await db.execute(
            select(WebScriptModel).where(
                WebScriptModel.menu_id == menu_id,
                WebScriptModel.enabled_flag == 1,
            )
        )
        script = script_res.scalar_one_or_none()
        if script:
            script.enabled_flag = 0

        return True, "删除成功"

    @staticmethod
    async def rename_web_menu(
        db: AsyncSession,
        *,
        menu_id: int,
        name: str,
        user_id: int,
    ) -> None:
        res = await db.execute(
            select(WebMenuModel).where(
                WebMenuModel.id == menu_id,
                WebMenuModel.enabled_flag == 1,
            )
        )
        menu = res.scalar_one_or_none()
        if not menu:
            return
        menu.name = name
        menu.last_updated_by = user_id

    @staticmethod
    async def get_web_script(db: AsyncSession, menu_id: int, user_id: int) -> Optional[Dict[str, Any]]:

        result = await db.execute(
            select(WebScriptModel).where(
                WebScriptModel.menu_id == menu_id,
                WebScriptModel.enabled_flag == 1,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return {
            "id": row.id,
            "menu_id": row.menu_id,
            "script": row.script,
            "creation_date": row.creation_date,
        }

    @staticmethod
    async def save_web_script(db: AsyncSession, script_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:

        menu_id = int(script_data["id"])
        script = script_data["script"]

        result = await db.execute(
            select(WebScriptModel).where(
                WebScriptModel.menu_id == menu_id,
                WebScriptModel.enabled_flag == 1,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            row.script = script
            row.last_updated_by = user_id
        else:
            row = WebScriptModel(
                script=script,
                menu_id=menu_id,
                created_by=user_id,
            )
            db.add(row)

        return {"id": getattr(row, "id", None)}

    @staticmethod
    async def execute_web_script(
        db: AsyncSession,
        script_config: Dict[str, Any],
        browsers: List[str],
        user_id: int,
    ) -> Dict[str, Any]:
        """执行Web脚本"""
        result_id = str(script_config["result_id"])

        # 只检查同一个 result_id 是否正在执行，且超过30分钟的执行视为僵尸自动忽略
        from datetime import timedelta
        zombie_threshold = datetime.now() - timedelta(minutes=30)
        running = await db.execute(
            select(WebResultListModel).where(
                WebResultListModel.enabled_flag == 1,
                WebResultListModel.status == 0,
                WebResultListModel.result_id == result_id,
                WebResultListModel.start_time >= zombie_threshold,
            )
        )
        if running.scalars().first():
            raise Exception("执行失败，当前脚本正在执行中，请稍后再试")

        status, msg, script_list, browser_type = await WebManagementService.analysis_web_script(db, script_config)

        task_name = script_config.get("task_name") or ""

        row = WebResultListModel(
            task_name=task_name,
            result_id=result_id,
            script_list=script_config.get("script") or [],
            browser_list=script_config.get("browser") or [],
            result=[],
            status=0,
            created_by=user_id,
            start_time=datetime.now(),
            end_time=None,
        )
        db.add(row)
        await db.flush()
        await db.commit()

        pid_list: List[int] = []
        if status:

            ctx = multiprocessing.get_context("spawn")
            for item in script_list:
                p = ctx.Process(target=run_web_task_in_process, args=(item, browser_type), daemon=True)
                p.start()
                pid_list.append(int(p.pid or 0))

            # 回写 pid_list，便于 stop_web_script 使用
            refetch = await db.execute(
                select(WebResultListModel).where(WebResultListModel.enabled_flag == 1, WebResultListModel.id == row.id)
            )
            saved = refetch.scalar_one_or_none()
            if saved:
                saved.pid_list = pid_list
            await db.commit()

        # 最终状态由执行引擎在每个 browser 完成后更新
        return {"status": status, "message": msg, "result_id": result_id, "pid_list": pid_list}


    @staticmethod
    def _safe_join(base: Path, *parts: str) -> Path:
        p = base
        for part in parts:
            part = part.replace("\\", "/").lstrip("/")
            if ".." in part.split("/"):
                raise ValueError("非法路径")
            p = p / part
        return p

    @staticmethod
    async def _handle_element_value(data: List[Dict[str, Any]]) -> str:
        values = [item.get("value") for item in (data or []) if item.get("value") is not None]
        return ",".join([str(v) for v in values])

    @staticmethod
    async def _analysis_element(file_name: str, user_id: int, pid: int, data: List[Dict[str, Any]]) -> Tuple[bool, str, List[Dict[str, Any]]]:
        
        try:
            script: List[Dict[str, Any]] = []
            for i in data:
                script_info: Dict[str, Any] = {}
                action = i.get("action")
                if action == "open_page":
                    script_info.update(
                        {
                            "name": i.get("fill_name") or "打开",
                            "type": 0,
                            "children": [],
                            "action": {
                                "type": 1,
                                "input": "",
                                "assert": [],
                                "target": "",
                                "element": i.get("action_detail", {}).get("open_page", {}).get("url", ""),
                                "up_type": 1,
                                "sway_type": 1,
                                "target_id": "",
                                "locator": 1,
                                "locator_select": 1,
                                "target_locator": 1,
                                "target_locator_select": 1,
                                "wait_time": 1,
                                "element_id": None,
                                "target_type": 1,
                                "before_wait": 1,
                                "after_wait": 1,
                                "cookies": [],
                                "localstorage": [],
                                "timeout": 15,
                            },
                            "status": True,
                        }
                    )
                elif action == "mouse_clicking":
                    action_detail = i.get("action_detail", {}).get("mouse_clicking", {})
                    element = await WebManagementService._handle_element_value(
                        action_detail.get("element", {}).get("custom_locators") or []
                    )
                    click_type = action_detail.get("type")
                    if click_type == "single_click_left":
                        step_type = 1
                    elif click_type == "double_click":
           
                        step_type = 1
                    elif click_type == "single_click_right":
                        step_type = 16
                    else:
                        step_type = 1
                    script_info.update(
                        {
                            "name": i.get("fill_name") or "点击",
                            "type": step_type,
                            "children": [],
                            "action": {
                                "type": 1,
                                "input": "",
                                "assert": [],
                                "target": "",
                                "element": element,
                                "up_type": 1,
                                "sway_type": 1,
                                "target_id": "",
                                "wait_time": 1,
                                "locator": 1,
                                "locator_select": 1,
                                "target_locator": 1,
                                "target_locator_select": 1,
                                "element_id": None,
                                "target_type": 1,
                                "before_wait": 1,
                                "after_wait": 1,
                                "cookies": [],
                                "localstorage": [],
                                "timeout": 15,
                            },
                            "status": True,
                        }
                    )
                elif action == "input_operations":
                    action_detail = i.get("action_detail", {}).get("input_operations", {})
                    value = action_detail.get("input_content", "")
                    element = await WebManagementService._handle_element_value(
                        action_detail.get("element", {}).get("custom_locators") or []
                    )
                    if value != "":
                        step_type = 5
                        name = i.get("fill_name") or "输入"
                    else:
                        step_type = 7
                        name = "清空文本"
                    script_info.update(
                        {
                            "name": name,
                            "type": step_type,
                            "children": [],
                            "action": {
                                "type": 1,
                                "input": value,
                                "assert": [],
                                "target": "",
                                "element": element,
                                "up_type": 1,
                                "sway_type": 1,
                                "target_id": "",
                                "locator": 1,
                                "locator_select": 1,
                                "target_locator": 1,
                                "target_locator_select": 1,
                                "wait_time": 1,
                                "element_id": None,
                                "target_type": 1,
                                "before_wait": 1,
                                "after_wait": 1,
                                "cookies": [],
                                "localstorage": [],
                                "timeout": 15,
                            },
                            "status": True,
                        }
                    )

                if script_info:
                    script.append(script_info)
            return True, "文件导入解析成功", script
        except Exception as e:
            return False, str(e), []

    @staticmethod
    async def input_element_from_file(
        db: AsyncSession,
        *,
        file_url: str,
        file_name: str,
        pid: int,
        user_id: int,
    ) -> Dict[str, Any]:
       
        base = Path(app_config.BASEDIR)
        file_path = WebManagementService._safe_join(base, file_url, file_name)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        ok, msg, script = await WebManagementService._analysis_element(file_name, user_id, pid, data)
        if not ok:
            raise Exception(msg)

        menu = WebMenuModel(
            name=file_name,
            pid=pid,
            type=2,
            created_by=user_id,
        )
        db.add(menu)
        await db.flush()

        ws = WebScriptModel(
            script=script,
            menu_id=menu.id,
            created_by=user_id,
        )
        db.add(ws)
        await db.flush()
        return {"message": msg, "menu_id": menu.id}

 

    @staticmethod
    async def stop_web_script(pid: int) -> Dict[str, Any]:
       
        if pid <= 0:
            raise ValueError("pid 非法")
        try:
            if os.name == "nt":
                cp = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, text=True)
                return {"pid": pid, "stopped": cp.returncode == 0, "stdout": cp.stdout, "stderr": cp.stderr}
            os.kill(pid, signal.SIGTERM)
            return {"pid": pid, "stopped": True}
        except Exception as e:
            # 再尝试强杀
            try:
                if os.name != "nt":
                    os.kill(pid, signal.SIGKILL)
                    return {"pid": pid, "stopped": True}
            except Exception as kill_error:
                return {"pid": pid, "stopped": False, "error": f"{str(e)}; SIGKILL失败: {str(kill_error)}"}
            return {"pid": pid, "stopped": False, "error": str(e)}

    @staticmethod
    async def stop_web_result(db: AsyncSession, *, result_id: str, user_id: int) -> Dict[str, Any]:
      
        res = await db.execute(
            select(WebResultListModel)
            .where(
                WebResultListModel.enabled_flag == 1,
                WebResultListModel.result_id == str(result_id),
                WebResultListModel.created_by == user_id,
            )
            .order_by(WebResultListModel.id.desc())
            .limit(1)
        )
        row = res.scalar_one_or_none()
        if not row:
            return {"result_id": result_id, "stopped": False, "message": "未找到执行记录"}

        pid_list = row.pid_list or []
        stopped_count = 0
        for pid in pid_list:
            try:
                r = await WebManagementService.stop_web_script(int(pid))
                if r.get("stopped") is True:
                    stopped_count += 1
            except Exception:
                continue

     
        row.status = 1
        row.end_time = datetime.now()
        
        await db.commit()

        return {
            "result_id": result_id,
            "stopped": True,
            "pid_total": len(pid_list),
            "pid_stopped": stopped_count,
        }

    @staticmethod
    async def del_web_result(db: AsyncSession, *, result_id: str, user_id: int) -> Dict[str, Any]:
      
        rid = str(result_id)
        res = await db.execute(
            select(WebResultListModel)
            .where(
                WebResultListModel.enabled_flag == 1,
                WebResultListModel.result_id == rid,
                WebResultListModel.created_by == user_id,
            )
            .order_by(WebResultListModel.id.desc())
            .limit(1)
        )
        row = res.scalar_one_or_none()
        if not row:
            return {"result_id": rid, "deleted": False, "message": "未找到执行记录"}

        # 若仍在执行中，先尝试停止所有进程
        if int(getattr(row, "status", 0) or 0) == 0:
            pid_list = row.pid_list or []
            for pid in pid_list:
                try:
                    await WebManagementService.stop_web_script(int(pid))
                except Exception:
                    continue

        # 硬删除明细
        await db.execute(
            WebResultDetailModel.__table__.delete().where(WebResultDetailModel.result_id == rid)
        )
        # 硬删除主记录
        await db.execute(
            WebResultListModel.__table__.delete().where(
                WebResultListModel.result_id == rid,
                WebResultListModel.created_by == user_id,
            )
        )
        await db.commit()

        return {"result_id": rid, "deleted": True}

    @staticmethod
    async def analysis_web_script(db: AsyncSession, data: Dict[str, Any]) -> Tuple[bool, str, List[Dict[str, Any]], int]:
        
        try:
            script: List[Dict[str, Any]] = []
            for i in data.get("script") or []:
                menu_id = int(i["id"])
                script_row = await db.execute(
                    select(WebScriptModel).where(WebScriptModel.menu_id == menu_id, WebScriptModel.enabled_flag == 1)
                )
                row = script_row.scalar_one_or_none()
                if not row:
                    continue
                ok, msg, result = await WebManagementService.analysis_web_script_detail(db, row.script or [], menu_id)
                if not ok:
                    return False, msg, [], int(data.get("browser_type") or 2)
                script.extend(result)

            script_list: List[Dict[str, Any]] = []
            for b in data.get("browser") or []:
                script_list.append(
                    {
                        "script": script,
                        "result_id": str(data["result_id"]),
                        "browser": int(b),
                        "width": data.get("width"),
                        "height": data.get("height"),
                    }
                )
            return True, "任务创建成功", script_list, int(data.get("browser_type") or 2)
        except Exception as e:
            return False, str(e), [], int(data.get("browser_type") or 2)

    @staticmethod
    async def analysis_web_script_detail(
        db: AsyncSession, script: List[Dict[str, Any]], menu_id: int
    ) -> Tuple[bool, str, List[Dict[str, Any]]]:
        
        try:
            result: List[Dict[str, Any]] = []
            for step in script:
                step["menu_id"] = menu_id

                # 目标元素处理（拖拽等）
                if step.get("type") == 4 and step.get("action", {}).get("target_type") == 2:
                    target_id_path = step["action"].get("target_id") or []
                    if target_id_path:
                        tid = int(target_id_path[-1])
                        el_res = await db.execute(
                            select(WebElementModel).where(WebElementModel.id == tid, WebElementModel.enabled_flag == 1)
                        )
                        web_el = el_res.scalar_one_or_none()
                        if web_el and web_el.element:
                            element = web_el.element
                            step["action"]["target"] = element.get("value")
                            if element.get("type") == 1:
                                step["action"]["target_locator"] = 1
                            if element.get("type") == 2:
                                if element.get("locator_type") == 3:
                                    step["action"]["type"] = 1
                                    step["action"]["target_locator"] = 1
                                elif element.get("locator_type") == 4:
                                    step["action"]["target_locator"] = 2
                                    step["action"]["target_locator_select"] = element.get("locator_select_type")
                                    step["action"]["role"] = element.get("locator_role_type")

                # 主元素处理
                if step.get("action", {}).get("type") == 2:
                    eid_path = step["action"].get("element_id") or []
                    if eid_path:
                        eid = int(eid_path[-1])
                        el_res = await db.execute(
                            select(WebElementModel).where(WebElementModel.id == eid, WebElementModel.enabled_flag == 1)
                        )
                        web_el = el_res.scalar_one_or_none()
                        if web_el and web_el.element:
                            element = web_el.element
                            step["action"]["element"] = element.get("value")
                            if element.get("type") == 1:
                                step["action"]["locator"] = 1
                            if element.get("type") == 2:
                                step["action"]["type"] = 1
                                if element.get("locator_type") == 3:
                                    step["action"]["locator"] = 1
                                elif element.get("locator_type") == 4:
                                    step["action"]["locator"] = 2
                                    step["action"]["locator_select"] = element.get("locator_select_type")
                                    step["action"]["role"] = element.get("locator_role_type")

                if step.get("children"):
                    ok, msg, child = await WebManagementService.analysis_web_script_detail(
                        db, step["children"], menu_id
                    )
                    if ok:
                        step["children"] = child
                result.append(step)
            return True, "任务创建成功", result
        except Exception as e:
            return False, str(e), []

    @staticmethod
    async def import_elements(db: AsyncSession, elements: List[Dict[str, Any]], user_id: int) -> Dict[str, Any]:

    
        created = 0
        updated = 0
        skipped = 0

        for item in elements or []:
            name = str(item.get("name") or item.get("fill_name") or "").strip()
            payload = item.get("element") if isinstance(item.get("element"), dict) else item
            if not name:
                skipped += 1
                continue

            
            res = await db.execute(
                select(WebElementModel).where(
                    WebElementModel.enabled_flag == 1,
                    WebElementModel.created_by == user_id,
                    WebElementModel.name == name,
                )
            )
            row = res.scalar_one_or_none()
            if row:
                row.element = payload
                row.last_updated_by = user_id
                updated += 1
            else:
                row = WebElementModel(
                    name=name,
                    element=payload if isinstance(payload, dict) else {"value": payload},
                    menu_id=item.get("menu_id"),
                    created_by=user_id,
                )
                db.add(row)
                await db.flush()

                # 同步创建 element menu 叶子节点（若提供 pid，则挂到 pid 下；否则不建菜单节点）
                pid = item.get("pid") or item.get("menu_id")
                if pid:
                    menu = WebElementMenuModel(
                        name=name,
                        pid=int(pid),
                        type=2,
                        element_id=row.id,
                        created_by=user_id,
                    )
                    db.add(menu)
                created += 1

        return {"created": created, "updated": updated, "skipped": skipped}

    @staticmethod
    async def get_web_result(
        db: AsyncSession, result_id: str, browser: int, user_id: int
    ) -> List[Dict[str, Any]]:
        result = await db.execute(
            select(WebResultDetailModel).where(
                WebResultDetailModel.enabled_flag == 1,
                WebResultDetailModel.result_id == result_id,
                WebResultDetailModel.browser == str(browser),
            ).order_by(WebResultDetailModel.id.desc())
        )
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "name": r.name,
                "result_id": r.result_id,
                "browser": r.browser,
                "log": r.log,
                "status": r.status,
                "before_img": r.before_img,
                "after_img": r.after_img,
                "video": r.video,
                "trace": r.trace,
                "assert_result": r.assert_result,
                "menu_id": r.menu_id,
                "creation_date": r.creation_date,
            }
            for r in rows
        ]

    @staticmethod
    def _playwright_base_dir() -> Path:
        
        backend_root = Path(__file__).resolve().parents[4]
        return backend_root / app_config.STATIC_DIR / "media" / "playwright"

    @staticmethod
    async def get_web_result_log(*, result_id: str, browser: int) -> List[str]:
        base_dir = WebManagementService._playwright_base_dir() / str(result_id) / str(browser)
        base_dir.mkdir(parents=True, exist_ok=True)
        path = base_dir / f"{browser}_result.txt"
        if not path.exists():
            return []
        content = path.read_text(encoding="utf-8", errors="ignore")
        log = content.split("\n")
        log_list = log[::-1]
        return log_list[1:]

    @staticmethod
    async def get_web_result_list(db: AsyncSession, body: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        page = int(body.get("page") or 1)
        page_size = int(body.get("pageSize") or 10)
        if page <= 0:
            page = 1
        if page_size <= 0:
            page_size = 10

        q = select(WebResultListModel).where(
            WebResultListModel.enabled_flag == 1,
            WebResultListModel.created_by == user_id,
        ).order_by(WebResultListModel.id.desc())
        res = await db.execute(q)
        all_rows = res.scalars().all()
        total = len(all_rows)
        start = (page - 1) * page_size
        end = start + page_size
        page_rows = all_rows[start:end]

        user_ids = [int(r.created_by) for r in page_rows if getattr(r, "created_by", None)]
        username_map = await _get_username_map(db, user_ids)
        content = []
        for r in page_rows:
            total_num = 0
            total_fail = 0
            for j in (r.result or []):
                total_num += int(j.get("total") or 0)
                total_fail += int(j.get("run_false") or 0)
            percent = round((total_num - total_fail) / total_num * 100, 2) if total_num > 0 else 0
            uid = getattr(r, "created_by", None)
            content.append(
                {
                    "id": r.id,
                    "task_name": r.task_name,
                    "result_id": r.result_id,
                    "script_list": r.script_list,
                    "browser_list": r.browser_list,
                    "pid_list": r.pid_list or [],
                    "result": r.result,
                    "start_time": r.start_time,
                    "end_time": r.end_time,
                    "status": r.status,
                    "percent": percent,
                    "username": username_map.get(int(uid), "") if uid else "",
                }
            )

        return {
            "content": content,
            "totalElements": total,
            "page": page,
            "pageSize": page_size,
        }

   

    @staticmethod
    async def get_web_result_report(db: AsyncSession, *, result_id: str, user_id: int) -> Dict[str, Any]:
      
        res = await db.execute(
            select(WebResultListModel).where(
                WebResultListModel.enabled_flag == 1,
                WebResultListModel.result_id == result_id,
                WebResultListModel.created_by == user_id,
            )
        )
        row = res.scalar_one_or_none()
        if not row:
            return {}

        result_list = row.result or []
        total = 0
        total_fail = 0
        for i in result_list:
            total += int(i.get("total") or 0)
            total_fail += int(i.get("run_false") or 0)

        percent = round((total - total_fail) / total * 100, 2) if total > 0 else 0

        # 标记 script_list 中每个脚本的整体 status
        script_list = list(row.script_list or [])
        for j in script_list:
            mid = int(j.get("id") or 0)
            if not mid:
                j["status"] = 1
                continue
            cnt = await db.execute(
                select(func.count(WebResultDetailModel.id)).where(
                    WebResultDetailModel.enabled_flag == 1,
                    WebResultDetailModel.result_id == result_id,
                    WebResultDetailModel.menu_id == mid,
                    WebResultDetailModel.status == 0,
                )
            )
            fail_num = int(cnt.scalar() or 0)
            j["status"] = 0 if fail_num > 0 else 1

        uid = getattr(row, "created_by", None)
        username_map = await _get_username_map(db, [int(uid)] if uid else [])
        username = username_map.get(int(uid), "") if uid else ""

        return {
            "id": row.id,
            "task_name": row.task_name,
            "result_id": row.result_id,
            "script_list": script_list,
            "browser_list": row.browser_list,
            "result": result_list,
            "start_time": row.start_time,
            "end_time": row.end_time,
            "status": row.status,
            "percent": percent,
            "total": total,
            "total_fail": total_fail,
            "username": username,
        }

    @staticmethod
    def _parse_timestamp(line: str):
        try:
            timestamp_str = line.split(" ")[0] + " " + line.split(" ")[1]
            return True, int(datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").timestamp())
        except Exception as e:
            return False, e

    @staticmethod
    def _time_add_3s(t: str) -> str:
        try:
            original_time = datetime.strptime(str(t), "%Y-%m-%d %H:%M:%S")
            return (original_time + timedelta(seconds=3)).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return t

    @staticmethod
    def _filter_by_time_range(lines: List[str], start_time: str, end_time: str) -> List[str]:
        start = int(datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").timestamp())
        end = int(datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S").timestamp())
        filtered: List[str] = []
        for line in lines:
            ok, ts = WebManagementService._parse_timestamp(line)
            if ok and start <= ts <= end:
                filtered.append(line)
        return filtered

    @staticmethod
    async def get_web_result_detail(
        db: AsyncSession,
        *,
        result_id: str,
        browser: int,
        menu_id: int,
        user_id: int,
    ) -> Dict[str, Any]:
       
        # media（执行结束记录上挂 video/trace）
        media_res = await db.execute(
            select(WebResultDetailModel).where(
                WebResultDetailModel.enabled_flag == 1,
                WebResultDetailModel.result_id == result_id,
                WebResultDetailModel.browser == str(browser),
                WebResultDetailModel.log == "执行结束",
            )
        )
        media = media_res.scalar_one_or_none()
        video = media.video if media else ""
        trace = media.trace if media else ""

        detail_res = await db.execute(
            select(WebResultDetailModel).where(
                WebResultDetailModel.enabled_flag == 1,
                WebResultDetailModel.result_id == result_id,
                WebResultDetailModel.browser == str(browser),
                WebResultDetailModel.menu_id == menu_id,
            ).order_by(WebResultDetailModel.id.desc())
        )
        rows = detail_res.scalars().all()
        content = [
            {
                "id": r.id,
                "name": r.name,
                "result_id": r.result_id,
                "browser": r.browser,
                "log": r.log,
                "status": r.status,
                "before_img": r.before_img,
                "after_img": r.after_img,
                "video": r.video,
                "trace": r.trace,
                "assert_result": r.assert_result,
                "menu_id": r.menu_id,
                "create_time": r.creation_date.strftime("%Y-%m-%d %H:%M:%S") if r.creation_date else "",
            }
            for r in rows
        ]

        # 日志按步骤时间范围过滤
        log_list: List[str] = []
        if content:
            start_time = content[-1]["create_time"]
            end_time = WebManagementService._time_add_3s(content[0]["create_time"])
            base_dir = WebManagementService._playwright_base_dir() / str(result_id) / str(browser)
            base_dir.mkdir(parents=True, exist_ok=True)
            log_path = base_dir / f"{browser}_result.txt"
            if log_path.exists():
                raw = log_path.read_text(encoding="utf-8", errors="ignore")
                lines = raw.split("\n")
                log_list = WebManagementService._filter_by_time_range(lines, start_time, end_time)[::-1]

        return {"content": content, "log": log_list, "video": video, "trace": trace}

    @staticmethod
    async def get_web_groups(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:

        result = await db.execute(
            select(WebGroupModel).where(
                WebGroupModel.enabled_flag == 1,
                WebGroupModel.created_by == user_id,
            ).order_by(WebGroupModel.id.desc())
        )
        rows = result.scalars().all()
        user_ids = []
        for r in rows:
            uid = getattr(r, "updated_by", None) or getattr(r, "created_by", None)
            if uid:
                user_ids.append(int(uid))
        username_map = await _get_username_map(db, user_ids)
        out = []
        for r in rows:
            uid = getattr(r, "updated_by", None) or getattr(r, "created_by", None)
            creation_date = getattr(r, "creation_date", None)
            updation_date = getattr(r, "updation_date", None)
            
            if creation_date is not None and hasattr(creation_date, "isoformat"):
                creation_date = creation_date.isoformat()
            if updation_date is not None and hasattr(updation_date, "isoformat"):
                updation_date = updation_date.isoformat()
            out.append({
                "id": r.id,
                "name": r.name or "",
                "script": r.script if r.script is not None else [],
                "description": r.description or "",
                "creation_date": creation_date,
                "updation_date": updation_date,
                "created_by": getattr(r, "created_by", None),
                "updated_by": getattr(r, "updated_by", None),
                "username": username_map.get(int(uid), "") if uid else "",
            })
        return out

    @staticmethod
    async def create_web_group(db: AsyncSession, group_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """创建Web脚本集"""
        grp = WebGroupModel(
            name=group_data["name"],
            script=group_data.get("script") or [],
            description=group_data.get("description") or "",
            created_by=user_id,
        )
        db.add(grp)
        await db.flush()
        return {"id": grp.id}

    @staticmethod
    async def edit_web_group(db: AsyncSession, group_data: Dict[str, Any], user_id: int) -> None:

        result = await db.execute(
            select(WebGroupModel).where(
                WebGroupModel.id == int(group_data["id"]),
                WebGroupModel.enabled_flag == 1,
            )
        )
        grp = result.scalar_one_or_none()
        if not grp:
            return
        grp.name = group_data["name"]
        grp.script = group_data["script"]
        grp.description = group_data.get("description") or ""
        grp.last_updated_by = user_id

    @staticmethod
    async def delete_web_group(db: AsyncSession, group_id: int) -> None:

        result = await db.execute(
            select(WebGroupModel).where(
                WebGroupModel.id == group_id,
                WebGroupModel.enabled_flag == 1,
            )
        )
        grp = result.scalar_one_or_none()
        if grp:
            grp.enabled_flag = 0

    @staticmethod
    async def get_web_group_all(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:

        result = await db.execute(
            select(WebGroupModel).where(
                WebGroupModel.enabled_flag == 1,
                WebGroupModel.created_by == user_id,
            ).order_by(WebGroupModel.id.desc())
        )
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "name": r.name,
                "script": r.script,
                "description": r.description,
            }
            for r in rows
        ]

    @staticmethod
    async def get_script_list(db: AsyncSession) -> List[Dict[str, Any]]:

        result = await db.execute(
            select(WebMenuModel).where(
                WebMenuModel.enabled_flag == 1,
                WebMenuModel.type == 2,
            )
        )
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "name": r.name,
                "pid": r.pid,
                "type": r.type,
            }
            for r in rows
        ]

    @staticmethod
    async def group_add_script(db: AsyncSession, web_list: List[List[int]]) -> List[Dict[str, Any]]:

        result: List[Dict[str, Any]] = []
        for path in web_list:
            if not path:
                continue
            menu_id = int(path[-1])
            row_res = await db.execute(
                select(WebMenuModel).where(
                    WebMenuModel.id == menu_id,
                    WebMenuModel.enabled_flag == 1,
                )
            )
            menu = row_res.scalar_one_or_none()
            if menu and menu.type == 2:
                result.append(
                    {
                        "id": menu.id,
                        "name": menu.name,
                        "pid": menu.pid,
                        "type": menu.type,
                    }
                )
        return result



    @staticmethod
    async def capture_screenshots(page, step_name: str) -> str:
        """捕获截图"""
        from pathlib import Path
        from datetime import datetime
        import re

        safe_step = re.sub(r"[^\w\u4e00-\u9fff\-_.]+", "_", str(step_name or "step"))[:60]
        
        base_dir = WebManagementService._playwright_base_dir() / "common"
        base_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{safe_step}.png"
        path = base_dir / filename
        await page.screenshot(path=path, full_page=True)
        return f"/media/playwright/common/{filename}"

    @staticmethod
    async def record_video(page, output_path: str) -> str:
        """录制视频"""
        import shutil
        from pathlib import Path

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        
        video = getattr(page, "video", None)
        if not video:
            raise ValueError("page.video 不存在：请确保创建 context 时开启 record_video_dir")
        src = Path(await video.path())
        shutil.copyfile(src, out)
        return str(out)

    @staticmethod
    async def save_trace(page, trace_path: str) -> str:
        """保存trace文件"""
        from pathlib import Path

        out = Path(trace_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        ctx = getattr(page, "context", None)
        tracing = getattr(ctx, "tracing", None) if ctx else None
        if not tracing:
            raise ValueError("page.context.tracing 不可用：请确保使用 Playwright BrowserContext")
        await tracing.stop(path=out)
        return str(out)

    @staticmethod
    async def validate_web_assertions(assertions: List[Dict[str, Any]], page) -> List[Dict[str, Any]]:
        """验证Web断言"""
        results: List[Dict[str, Any]] = []
        for a in assertions or []:
            item = dict(a)
            status = 1
            result_msg = "断言成功"
            try:
                t = int(item.get("type") or 1)
                expected = str(item.get("element") or "")

                if t in (1, 2):
          
                    locator = expected
                    el = page.locator(locator)
                    exists = await el.is_visible()
                    if (t == 1 and exists) or (t == 2 and (not exists)):
                        status = 1
                        result_msg = "断言成功"
                    else:
                        status = 0
                        result_msg = "断言失败"

                elif t in (3, 4):
                    # HTML 包含/不包含
                    html = await page.content()
                    contains = expected in html
                    if (t == 3 and contains) or (t == 4 and (not contains)):
                        status = 1
                        result_msg = "断言成功"
                    else:
                        status = 0
                        result_msg = "断言失败"

                elif t == 5:
                    # URL/Title 等于
                    page_type = int(item.get("page_type") or 1)  # 1 url, 2 title
                    if page_type == 1:
                        ok = (page.url == expected)
                    else:
                        ok = ((await page.title()) == expected)
                    status = 1 if ok else 0
                    result_msg = "断言成功" if ok else "断言失败"

                elif t == 6:
                    # eval 自定义脚本（提供 page）
                    from playwright.async_api import expect  # noqa: F401
                    eval(expected, {"page": page, "expect": expect})
                    status = 1
                    result_msg = "断言成功"

                else:

                    status = 1
                    result_msg = "断言跳过(未知类型)"

            except Exception as e:
                status = 0
                result_msg = f"断言失败，原因是：{str(e)}"

            item["status"] = status
            item["result"] = result_msg
            results.append(item)

        return results
