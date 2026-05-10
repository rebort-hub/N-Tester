#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort
from typing import List, Optional, Dict, Any
import asyncio
import os
import shutil
import multiprocessing
import psutil
import random
import time
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, delete
from sqlalchemy.orm.attributes import flag_modified
from app.api.v1.system.file.service import FileService

from .model import (
    AppMenuModel,
    AppScriptModel,
    AppResultListModel,
    AppResultModel,
    AppAirtestImageModel,
    AppUiElementModel,
)
from .airtest_runner import run_airtest_script_process
from .executor import run_appium_process


class AppManagementService:
    """APP管理服务"""

    
    _pid_index: Dict[int, Dict[str, str]] = {}
    _proc_index: Dict[int, multiprocessing.Process] = {}

    @staticmethod
    def _use_appium_executor() -> bool:
        """USE_APPIUM_APP_EXECUTOR=1/true（.env / config）时使用 Appium+OpenCV 执行器"""
        try:
            from config import config

            s = str(getattr(config, "USE_APPIUM_APP_EXECUTOR", "") or "").strip().lower()
            if s:
                return s in ("1", "true", "yes")
        except Exception:
            pass
        return os.getenv("USE_APPIUM_APP_EXECUTOR", "").strip().lower() in ("1", "true", "yes")

    @staticmethod
    def _appium_server_url() -> str:
        try:
            from config import config

            u = str(getattr(config, "APPIUM_SERVER_URL", "") or "").strip()
            if u:
                return u
        except Exception:
            pass
        return str(os.getenv("APPIUM_SERVER_URL") or "http://127.0.0.1:4723")

    @staticmethod
    def _app_template_root() -> str:
        try:
            from config import config

            t = str(getattr(config, "APP_TEMPLATE_ROOT", "") or "").strip()
            if t:
                return t
        except Exception:
            pass
        return str(os.getenv("APP_TEMPLATE_ROOT") or "backend")

    @staticmethod
    async def _resolve_ntest_appium_session(
        db: AsyncSession,
        user_id: int,
        server_id: Any,
        phone_id: Any,
        package: str,
        app_activity: str,
    ) -> Optional[Dict[str, Any]]:
       
        if server_id is None or phone_id is None:
            return None
        try:
            sid = int(server_id)
            pid = int(phone_id)
        except (TypeError, ValueError):
            return None
        from .device_service import AppDeviceCenterService

        try:
            srv = await AppDeviceCenterService.server_get(db, user_id, sid)
            phone = await AppDeviceCenterService.phone_get(db, user_id, pid)
        except ValueError:
            return None
        act = (app_activity or "").strip() or ".MainActivity"
        full = AppDeviceCenterService.build_appium_capabilities(
            server_ip=srv.ip,
            server_port=str(srv.port),
            appium_version=srv.appium_version or "2.x",
            phone_os=phone.phone_os or "Android",
            os_version=phone.os_version or "",
            device_id=phone.device_id,
            app_package=package or "",
            app_activity=act,
            no_reset=True,
            command_timeout=3600,
        )
        remote = AppDeviceCenterService.ntest_remote_url(
            full["host"], str(full["port"]), full.get("remote_path")
        )
        caps = AppDeviceCenterService.session_capabilities_only(full)
        return {"remote_url": remote, "capabilities": caps, "udid": phone.device_id}
    
    @staticmethod
    async def get_app_menu(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        """获取APP脚本菜单树"""
 
        root_row = (
            await db.execute(
                select(AppMenuModel).where(
                    AppMenuModel.user_id == user_id,
                    AppMenuModel.enabled_flag == 1,
                    AppMenuModel.type == 0,
                    AppMenuModel.pid == 0,
                )
            )
        ).scalar_one_or_none()
        if not root_row:
            root_row = AppMenuModel(name="根目录", pid=0, type=0, user_id=user_id)
            db.add(root_row)
            await db.commit()

        result = await db.execute(
            select(AppMenuModel)
            .where(AppMenuModel.user_id == user_id, AppMenuModel.enabled_flag == 1)
            .order_by(AppMenuModel.id)
        )
        menus = result.scalars().all()

        nodes = [{"id": m.id, "name": m.name, "pid": int(m.pid), "type": int(m.type)} for m in menus]
        node_map: Dict[int, Dict[str, Any]] = {n["id"]: {**n, "children": []} for n in nodes}
        roots: List[Dict[str, Any]] = []

        for n in nodes:
            pid = int(n["pid"])
            if pid and pid in node_map:
                node_map[pid]["children"].append(node_map[n["id"]])
            else:
                roots.append(node_map[n["id"]])

       
        root_node = node_map.get(int(root_row.id))
        if not root_node:
          
            return [{"id": int(root_row.id), "name": root_row.name, "pid": 0, "type": 0, "children": roots}]

        
        return [root_node]
    @staticmethod
    async def recover_root_menu(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """恢复被软删除的根目录"""
     
        soft_deleted_root = (
            await db.execute(
                select(AppMenuModel).where(
                    AppMenuModel.user_id == user_id,
                    AppMenuModel.enabled_flag == 0,
                    AppMenuModel.type == 0,
                    AppMenuModel.pid == 0,
                )
            )
        ).scalar_one_or_none()

        if soft_deleted_root:
            # 恢复根目录
            await db.execute(
                update(AppMenuModel)
                .where(AppMenuModel.id == soft_deleted_root.id)
                .values(enabled_flag=1)
            )

            # 恢复相关的脚本记录
            await db.execute(
                update(AppScriptModel)
                .where(AppScriptModel.menu_id == soft_deleted_root.id)
                .values(enabled_flag=1)
            )

            await db.commit()
            return {"success": True, "message": "根目录已恢复", "recovered": True}
        else:
            # 检查是否已经存在启用的根目录
            existing_root = (
                await db.execute(
                    select(AppMenuModel).where(
                        AppMenuModel.user_id == user_id,
                        AppMenuModel.enabled_flag == 1,
                        AppMenuModel.type == 0,
                        AppMenuModel.pid == 0,
                    )
                )
            ).scalar_one_or_none()
            
            if existing_root:
                return {"success": True, "message": "根目录已存在", "recovered": False}
            
            # 没有找到软删除的根目录，创建新的
            root_row = AppMenuModel(name="根目录", pid=0, type=0, user_id=user_id)
            db.add(root_row)
            await db.flush()

            # 检查是否已存在APP自动化文件夹
            existing_app_folder = (
                await db.execute(
                    select(AppMenuModel).where(
                        AppMenuModel.user_id == user_id,
                        AppMenuModel.name == "APP自动化",
                        AppMenuModel.pid == int(root_row.id),
                        AppMenuModel.type == 1,
                        AppMenuModel.enabled_flag == 1,
                    )
                )
            ).scalar_one_or_none()
            
            if not existing_app_folder:
                # 创建默认的APP自动化文件夹
                db.add(AppMenuModel(name="APP自动化", pid=int(root_row.id), type=1, user_id=user_id))
            
            await db.commit()
            return {"success": True, "message": "根目录已创建", "recovered": False}

    
    @staticmethod
    async def get_app_script(db: AsyncSession, menu_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """获取APP脚本内容"""
        result = await db.execute(
            select(AppScriptModel).where(
                AppScriptModel.menu_id == menu_id, AppScriptModel.user_id == user_id, AppScriptModel.enabled_flag == 1
            )
        )
        row = result.scalar_one_or_none()
        if not row:
         
            return {"id": None, "menu_id": menu_id, "script": []}
        return {"id": row.id, "menu_id": row.menu_id, "script": row.script or []}
    
    @staticmethod
    async def save_app_script(db: AsyncSession, script_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """保存APP脚本"""
        menu_id = int(script_data["id"])
        script = script_data.get("script") or []
        result = await db.execute(
            select(AppScriptModel).where(AppScriptModel.menu_id == menu_id, AppScriptModel.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        if row:
            row.script = script
        else:
            db.add(AppScriptModel(menu_id=menu_id, script=script, user_id=user_id))
        await db.commit()
        return {"success": True}

    @staticmethod
    async def menu_script_list(db: AsyncSession, pid: int, user_id: int) -> List[Dict[str, Any]]:
        """查询 pid 下的菜单列表"""
        result = await db.execute(
            select(AppMenuModel).where(
                AppMenuModel.pid == pid, AppMenuModel.user_id == user_id, AppMenuModel.enabled_flag == 1
            )
        )
        rows = result.scalars().all()
        return [{"id": r.id, "name": r.name, "type": r.type} for r in rows]

    @staticmethod
    async def get_script_list(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        """查询 type=2 的脚本菜单"""
        result = await db.execute(
            select(AppMenuModel).where(
                AppMenuModel.type == 2, AppMenuModel.user_id == user_id, AppMenuModel.enabled_flag == 1
            )
        )
        rows = result.scalars().all()
        return [{"id": r.id, "name": r.name, "pid": int(r.pid), "type": r.type} for r in rows]

    @staticmethod
    async def view_script_list(db: AsyncSession, menu_id: int, user_id: int) -> List[Dict[str, Any]]:
        """返回脚本内容列表"""
        row = (
            await db.execute(
                select(AppScriptModel).where(
                    AppScriptModel.menu_id == menu_id, AppScriptModel.user_id == user_id, AppScriptModel.enabled_flag == 1
                )
            )
        ).scalar_one_or_none()
        return (row.script or []) if row else []

    @staticmethod
    async def _resolve_img_field(db: AsyncSession, ref: Any) -> Any:
        """解析为可给 Airtest Template 使用的路径"""
        if ref is None:
            return None
        if isinstance(ref, (list, tuple)) and len(ref) >= 2:
            img_id = int(ref[-1])
            row = (
                await db.execute(
                    select(AppAirtestImageModel).where(
                        AppAirtestImageModel.id == img_id, AppAirtestImageModel.enabled_flag == 1
                    )
                )
            ).scalar_one_or_none()
            if row and row.file_path:
                fp = str(row.file_path).strip()
                if fp.startswith("http://") or fp.startswith("https://"):
                    return fp
                return f".{fp}" if not fp.startswith(".") else fp
            return ref
        return ref

    @staticmethod
    async def resolve_script_steps(db: AsyncSession, steps: List[Dict[str, Any]], user_id: int) -> List[Dict[str, Any]]:
        """执行前解析脚本里引用的图像库 id"""
        _ = user_id  # 预留：可按菜单归属做强校验
        resolved: List[Dict[str, Any]] = []
        type_need = {0, 2, 3, 4, 5}
        for raw in steps or []:
            item = dict(raw)
            try:
                eid = item.get("element_id")
                if eid is not None and str(eid).strip() != "":
                    er = (
                        await db.execute(
                            select(AppUiElementModel).where(
                                AppUiElementModel.id == int(eid),
                                AppUiElementModel.user_id == user_id,
                                AppUiElementModel.enabled_flag == 1,
                            )
                        )
                    ).scalar_one_or_none()
                    if er:
                        android = dict(item.get("android") or {})
                        android["locate_type"] = er.locate_type
                        android["locate_value"] = er.locate_value
                        item["android"] = android
            except (TypeError, ValueError):
                pass
            try:
                t = int(item.get("type") if item.get("type") is not None else -999)
            except (TypeError, ValueError):
                t = -999
            if t in type_need:
                android = dict(item.get("android") or {})
                ios = dict(item.get("ios") or {})
                android["img"] = await AppManagementService._resolve_img_field(db, android.get("img"))
                ios["img"] = await AppManagementService._resolve_img_field(db, ios.get("img"))
                android["assert"] = await AppManagementService._resolve_img_field(db, android.get("assert"))
                ios["assert"] = await AppManagementService._resolve_img_field(db, ios.get("assert"))
                item["android"] = android
                item["ios"] = ios
            resolved.append(item)
        return resolved
    
    @staticmethod
    async def execute_app_script(db: AsyncSession, script_config: Dict[str, Any], device_id: str, user_id: int) -> Dict[str, Any]:
        """执行单个APP脚本（子进程跑 Airtest"""
        menu_id = int(script_config["id"])
        task_name = str(script_config.get("task_name") or "APP自动化任务")
        result_id = str(script_config.get("result_id") or str(int(time.time() * 1000)))
        device_list = script_config.get("device_list") or []
        run_type = int(script_config.get("run_type") if script_config.get("run_type") is not None else 3)
        version = str(script_config.get("version") or "")
        channel_id = str(script_config.get("channel_id") or "")

        # 读取脚本步骤（数据库存储）
        script_row = (
            await db.execute(
                select(AppScriptModel).where(
                    AppScriptModel.menu_id == menu_id,
                    AppScriptModel.user_id == user_id,
                    AppScriptModel.enabled_flag == 1,
                )
            )
        ).scalar_one_or_none()
        raw_steps = (script_row.script or []) if script_row else []
        steps = await AppManagementService.resolve_script_steps(db, list(raw_steps), user_id)
        script_blocks = [{"id": menu_id, "script": steps}]

        pid_list: List[Dict[str, Any]] = []
        script_status: List[Dict[str, Any]] = []
        device_store: List[Dict[str, Any]] = []
        for d in device_list:
            deviceid = str(d.get("deviceid") or "")
            pkg = str(d.get("package") or script_config.get("package") or "")
            app_act = str(d.get("app_activity") or script_config.get("app_activity") or "")
            ntest_ctx = None
            need_session = AppManagementService._use_appium_executor() or (
                d.get("server_id") is not None and d.get("phone_id") is not None
            )
            if need_session:
                ntest_ctx = await AppManagementService._resolve_ntest_appium_session(
                    db,
                    user_id,
                    d.get("server_id") or script_config.get("server_id"),
                    d.get("phone_id") or script_config.get("phone_id"),
                    pkg,
                    app_act,
                )
            exec_id = (ntest_ctx or {}).get("udid") or deviceid
            if not exec_id:
                continue
            device_name = str(d.get("name") or d.get("device_name") or "")
            os_type = str(d.get("os_type") or "android")
            install_path = str(d.get("path") or script_config.get("path") or "")
            appium_url = AppManagementService._appium_server_url()
            if AppManagementService._use_appium_executor():
                appium_kw: Dict[str, Any] = {
                    "deviceid": exec_id,
                    "scripts": steps,
                    "result_id": result_id,
                    "menu_id": menu_id,
                    "package": pkg,
                    "user_id": int(user_id),
                    "template_root": AppManagementService._app_template_root(),
                    "appium_server_url": "",
                    "ntest_remote_url": "",
                    "ntest_capabilities": None,
                }
                if ntest_ctx:
                    appium_kw["ntest_remote_url"] = ntest_ctx["remote_url"]
                    appium_kw["ntest_capabilities"] = ntest_ctx["capabilities"]
                else:
                    appium_kw["appium_server_url"] = appium_url
                p = multiprocessing.Process(
                    target=run_appium_process,
                    kwargs=appium_kw,
                    daemon=True,
                )
            else:
                p = multiprocessing.Process(
                    target=run_airtest_script_process,
                    kwargs={
                        "deviceid": exec_id,
                        "script_blocks": script_blocks,
                        "result_id": result_id,
                        "user_id": int(user_id),
                        "run_type": run_type,
                        "os_type": os_type,
                        "version": version,
                        "channel_id": channel_id,
                        "package": pkg,
                        "install_path": install_path,
                    },
                    daemon=True,
                )
            p.start()
            pid_list.append({"deviceid": exec_id, "pid": int(p.pid), "name": device_name})
            script_status.append(
                {
                    "device": exec_id,
                    "pid": int(p.pid),
                    "percent": 0,
                    "passed": 0,
                    "fail": 0,
                    "total": 0,
                    "un_run": 0,
                    "status": "running",
                }
            )
            device_store.append(
                {
                    "deviceid": exec_id,
                    "pid": int(p.pid),
                    "name": device_name,
                    "notify": 0,
                    "notice_time": 0,
                }
            )
            AppManagementService._pid_index[int(p.pid)] = {"result_id": result_id, "deviceid": exec_id}
            AppManagementService._proc_index[int(p.pid)] = p

        if not pid_list:
            raise ValueError(
                "未启动任何执行进程：请确认设备列表中已选择设备中心的服务器与手机并填写包名；"
                "若使用 Appium/Android 步骤执行，请在环境变量或配置中启用 USE_APPIUM_APP_EXECUTOR=1。"
            )

        # 写入汇总记录
        db.add(
            AppResultListModel(
                task_name=task_name,
                device_list=device_store,
                script_list=[{"id": menu_id, "name": str(script_config.get("menu_name") or "")}],
                script_status=script_status,
                result_id=result_id,
                user_id=user_id,
            )
        )
        await db.commit()
        return {"pid_list": pid_list, "result_id": result_id}
    
    @staticmethod
    async def execute_script_list(
        db: AsyncSession,
        script_ids: List[int],
        device_list: List[Dict[str, Any]],
        user_id: int,
        run_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行APP脚本集"""
        ro = run_options or {}
        result_id = str(ro.get("result_id") or int(time.time() * 1000))
        task_name = str(ro.get("task_name") or "APP自动化任务")
        run_type = int(ro.get("run_type") if ro.get("run_type") is not None else 3)
        version = str(ro.get("version") or "")
        channel_id = str(ro.get("channel_id") or "")

        script_items = list(ro.get("script_items") or [])
        if script_items:
            ordered_ids: List[int] = [int(x.get("id")) for x in script_items if x.get("id") is not None]
        else:
            ordered_ids = [int(x) for x in (script_ids or [])]

        script_blocks: List[Dict[str, Any]] = []
        for sid in ordered_ids:
            row = (
                await db.execute(
                    select(AppScriptModel).where(
                        AppScriptModel.menu_id == int(sid),
                        AppScriptModel.user_id == user_id,
                        AppScriptModel.enabled_flag == 1,
                    )
                )
            ).scalar_one_or_none()
            if row and row.script:
                steps = await AppManagementService.resolve_script_steps(db, list(row.script), user_id)
                script_blocks.append({"id": int(sid), "script": steps})

        pid_list: List[Dict[str, Any]] = []
        script_status: List[Dict[str, Any]] = []
        device_store: List[Dict[str, Any]] = []

        for d in (device_list or []):
            deviceid = str(d.get("deviceid") or "")
            device_package = str(d.get("package") or ro.get("package") or "")
            app_act = str(d.get("app_activity") or ro.get("app_activity") or "")
            ntest_ctx = None
            need_session = AppManagementService._use_appium_executor() or (
                d.get("server_id") is not None and d.get("phone_id") is not None
            )
            if need_session:
                ntest_ctx = await AppManagementService._resolve_ntest_appium_session(
                    db,
                    user_id,
                    d.get("server_id") or ro.get("server_id"),
                    d.get("phone_id") or ro.get("phone_id"),
                    device_package,
                    app_act,
                )
            exec_id = (ntest_ctx or {}).get("udid") or deviceid
            if not exec_id:
                continue
            device_name = str(d.get("name") or d.get("device_name") or "")
            os_type = str(d.get("os_type") or "android")
            install_path = str(d.get("path") or "")

            appium_url = AppManagementService._appium_server_url()
            merged_steps: List[Dict[str, Any]] = []
            for blk in script_blocks:
                merged_steps.extend(blk.get("script") or [])
            first_menu = int(script_blocks[0].get("id") or 0) if script_blocks else 0
            if AppManagementService._use_appium_executor():
                appium_kw2: Dict[str, Any] = {
                    "deviceid": exec_id,
                    "scripts": merged_steps,
                    "result_id": result_id,
                    "menu_id": first_menu,
                    "package": device_package,
                    "user_id": int(user_id),
                    "template_root": AppManagementService._app_template_root(),
                    "appium_server_url": "",
                    "ntest_remote_url": "",
                    "ntest_capabilities": None,
                }
                if ntest_ctx:
                    appium_kw2["ntest_remote_url"] = ntest_ctx["remote_url"]
                    appium_kw2["ntest_capabilities"] = ntest_ctx["capabilities"]
                else:
                    appium_kw2["appium_server_url"] = appium_url
                p = multiprocessing.Process(
                    target=run_appium_process,
                    kwargs=appium_kw2,
                    daemon=True,
                )
            else:
                p = multiprocessing.Process(
                    target=run_airtest_script_process,
                    kwargs={
                        "deviceid": exec_id,
                        "script_blocks": script_blocks,
                        "result_id": result_id,
                        "user_id": int(user_id),
                        "run_type": run_type,
                        "os_type": os_type,
                        "version": version,
                        "channel_id": channel_id,
                        "package": device_package,
                        "install_path": install_path,
                    },
                    daemon=True,
                )
            p.start()
            pid_list.append({"deviceid": exec_id, "pid": int(p.pid), "name": device_name})
            script_status.append(
                {
                    "device": exec_id,
                    "name": device_name,
                    "pid": int(p.pid),
                    "percent": 0,
                    "passed": 0,
                    "fail": 0,
                    "total": 0,
                    "un_run": 0,
                    "status": "running",
                }
            )
            device_store.append(
                {
                    "deviceid": exec_id,
                    "pid": int(p.pid),
                    "name": device_name,
                    "notify": 0,
                    "notice_time": 0,
                }
            )
            AppManagementService._pid_index[int(p.pid)] = {"result_id": result_id, "deviceid": exec_id}
            AppManagementService._proc_index[int(p.pid)] = p

        if not pid_list:
            raise ValueError(
                "未启动任何执行进程：请检查设备列表（设备 ID 或设备中心服务器/手机）与包名配置；"
                "Appium 模式需启用 USE_APPIUM_APP_EXECUTOR=1。"
            )

        script_list_payload: List[Dict[str, Any]] = []
        if script_items:
            for x in script_items:
                if x.get("id") is None:
                    continue
                script_list_payload.append(
                    {
                        "id": int(x.get("id")),
                        "name": str(x.get("name") or ""),
                        "step": int(x.get("step") or 0),
                    }
                )
        else:
            script_list_payload = [{"id": int(sid), "name": ""} for sid in (ordered_ids or [])]

        db.add(
            AppResultListModel(
                task_name=task_name,
                device_list=device_store,
                script_list=script_list_payload,
                script_status=script_status,
                result_id=result_id,
                user_id=user_id,
            )
        )
        await db.commit()
        return {"pid_list": pid_list, "result_id": result_id}
    
    @staticmethod
    async def add_app_menu(db: AsyncSession, menu_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """新增APP菜单"""
        name = str(menu_data["name"])
        pid = int(menu_data["pid"])
        mtype = int(menu_data["type"])
        menu = AppMenuModel(name=name, pid=pid, type=mtype, user_id=user_id)
        db.add(menu)
        await db.flush()
        
        db.add(AppScriptModel(menu_id=menu.id, script=[], user_id=user_id))
        await db.commit()
        return {"id": menu.id, "name": name, "pid": pid, "type": mtype}
    
    @staticmethod
    async def delete_app_menu(db: AsyncSession, menu_id: int, user_id: int) -> bool:
        """删除APP菜单"""
        try:
            # 检查是否为根目录
            menu_row = (
                await db.execute(
                    select(AppMenuModel).where(
                        AppMenuModel.id == menu_id, 
                        AppMenuModel.user_id == user_id,
                        AppMenuModel.enabled_flag == 1
                    )
                )
            ).scalar_one_or_none()
            
            if not menu_row:
                return False
                
            # 防止删除根目录
            if menu_row.type == 0:
                raise ValueError("根目录不能删除")
            
            # 递归删除所有子节点
            await AppManagementService._delete_menu_recursive(db, menu_id, user_id)
            
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            raise e
    
    @staticmethod
    async def _delete_menu_recursive(db: AsyncSession, menu_id: int, user_id: int):
        """递归删除菜单及其所有子节点"""
        # 查找所有子节点
        child_menus = await db.execute(
            select(AppMenuModel).where(
                AppMenuModel.pid == menu_id, 
                AppMenuModel.user_id == user_id,
                AppMenuModel.enabled_flag == 1
            )
        )
        child_list = child_menus.scalars().all()
        
        # 递归删除每个子节点
        for child in child_list:
            await AppManagementService._delete_menu_recursive(db, child.id, user_id)
        
        # 删除当前节点的脚本记录
        await db.execute(
            delete(AppScriptModel).where(
                AppScriptModel.menu_id == menu_id, 
                AppScriptModel.user_id == user_id
            )
        )
        
        # 删除当前节点
        result = await db.execute(
            delete(AppMenuModel).where(
                AppMenuModel.id == menu_id, 
                AppMenuModel.user_id == user_id
            )
        )
        print(f"删除菜单 {menu_id}, 影响行数: {result.rowcount}")  # 调试日志
    
    @staticmethod
    async def rename_app_menu(db: AsyncSession, menu_id: int, new_name: str, user_id: int) -> Dict[str, Any]:
        """重命名APP菜单"""
        await db.execute(
            update(AppMenuModel).where(AppMenuModel.id == menu_id, AppMenuModel.user_id == user_id).values(name=str(new_name))
        )
        await db.commit()
        return {"success": True}
    
    @staticmethod
    async def get_app_result(db: AsyncSession, result_id: str, user_id: int) -> Dict[str, Any]:
        """获取APP执行"""
        result = await db.execute(
            select(AppResultListModel).where(AppResultListModel.result_id == result_id, AppResultListModel.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            return {}
        return {
            "id": row.id,
            "task_name": row.task_name,
            "device_list": row.device_list,
            "script_list": row.script_list,
            "script_status": row.script_status,
            "result_id": row.result_id,
            "start_time": row.start_time,
            "end_time": row.end_time,
        }

    @staticmethod
    async def get_app_result_steps_for_device(
        db: AsyncSession, result_id: str, device: str, user_id: int
    ) -> List[Dict[str, Any]]:
        """单设备步骤结果列表（order_by -id）"""
        result = await db.execute(
            select(AppResultModel)
            .where(
                AppResultModel.result_id == result_id,
                AppResultModel.device == device,
                AppResultModel.user_id == user_id,
                AppResultModel.enabled_flag == 1,
            )
            .order_by(AppResultModel.id.desc())
        )
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "device": r.device,
                "result_id": r.result_id,
                "name": r.name,
                "status": r.status,
                "log": r.log,
                "assert_value": r.assert_value,
                "before_img": r.before_img,
                "after_img": r.after_img,
                "video": r.video,
                "performance": r.performance,
                "menu_id": r.menu_id,
                "create_time": r.create_time,
            }
            for r in rows
        ]

    @staticmethod
    async def get_app_result_detail(db: AsyncSession, result_id: str, user_id: int) -> Dict[str, Any]:
        """get_app_result_detail：返回汇总详情 + 设备状态/统计"""
        row = (
            await db.execute(
                select(AppResultListModel).where(
                    AppResultListModel.result_id == result_id, AppResultListModel.user_id == user_id, AppResultListModel.enabled_flag == 1
                )
            )
        ).scalar_one_or_none()
        if not row:
            return {}

        data = {
            "id": row.id,
            "task_name": row.task_name,
            "device_list": row.device_list or [],
            "script_list": row.script_list or [],
            "script_status": row.script_status or [],
            "result_id": row.result_id,
            "start_time": row.start_time,
            "end_time": row.end_time,
        }

        device_dict = {i.get("device"): i for i in (data["script_status"] or []) if i}
        for d in data["device_list"]:
            deviceid = d.get("deviceid")
            s = device_dict.get(deviceid)
            
            if s:
                if d.get("pid") is None and s.get("pid") is not None:
                    d["pid"] = s.get("pid")
                if (d.get("name") is None or d.get("name") == "") and s.get("name") is not None:
                    d["name"] = s.get("name")
            if s and (s.get("fail") or 0) > 0:
                d["status"] = 0
            else:
                d["status"] = 1

        percent = passed = fail = total = un_run = 0
        for s in data["script_status"] or []:
            percent += float(s.get("percent") or 0)
            passed += int(s.get("passed") or 0)
            fail += int(s.get("fail") or 0)
            total += int(s.get("total") or 0)
            un_run += int(s.get("un_run") or 0)
        if data["script_status"]:
            data["percent"] = round(percent / len(data["script_status"]), 2)
        else:
            data["percent"] = 0
        data["passed"] = passed
        data["fail"] = fail
        data["total"] = total
        data["un_run"] = un_run
        return data

    @staticmethod
    async def get_result_detail(
        db: AsyncSession, result_id: str, device: str, user_id: int
    ) -> Dict[str, Any]:
        """get_result_detail：单设备在 script_status 中的汇总（用于实时监控顶部统计）"""
        row = (
            await db.execute(
                select(AppResultListModel).where(
                    AppResultListModel.result_id == result_id,
                    AppResultListModel.user_id == user_id,
                    AppResultListModel.enabled_flag == 1,
                )
            )
        ).scalar_one_or_none()
        if not row:
            return {}
        script_fail = script_pass = script_total = script_un_run = 0
        percent = 0.0
        end_time: Any = ""
        start_time = row.start_time
        for j in row.script_status or []:
            if j.get("device") == device:
                script_fail = int(j.get("fail") or 0)
                script_pass = int(j.get("passed") or 0)
                script_total = int(j.get("total") or 0)
                script_un_run = int(j.get("un_run") or 0)
                percent = float(j.get("percent") or 0)
                end_time = j.get("end_time") or ""
                break
        return {
            "script_total": script_total,
            "script_pass": script_pass,
            "script_fail": script_fail,
            "percent": percent,
            "end_time": end_time,
            "start_time": start_time,
            "script_un_run": script_un_run,
        }

    @staticmethod
    async def get_result_list(db: AsyncSession, result_id: str, menu_id: int, device: str, user_id: int) -> List[Dict[str, Any]]:
        """get_result_list：返回单设备单脚本的结果记录"""
        result = await db.execute(
            select(AppResultModel)
            .where(
                AppResultModel.result_id == result_id,
                AppResultModel.menu_id == menu_id,
                AppResultModel.device == device,
                AppResultModel.user_id == user_id,
                AppResultModel.enabled_flag == 1,
            )
            .order_by(AppResultModel.id.desc())
        )
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "device": r.device,
                "result_id": r.result_id,
                "name": r.name,
                "status": r.status,
                "log": r.log,
                "assert_value": r.assert_value,
                "before_img": r.before_img,
                "after_img": r.after_img,
                "video": r.video,
                "performance": r.performance,
                "menu_id": r.menu_id,
                "create_time": r.create_time,
            }
            for r in rows
        ]

    @staticmethod
    async def app_correction(db: AsyncSession, result_id: str, device: str, user_id: int) -> None:
        """app_correction：将失败(0)置为成功(1)"""
        await db.execute(
            update(AppResultModel)
            .where(
                AppResultModel.result_id == result_id,
                AppResultModel.device == device,
                AppResultModel.status == 0,
                AppResultModel.user_id == user_id,
            )
            .values(status=1)
        )
        await db.commit()

    @staticmethod
    async def app_menu_select(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        """app_menu_select：返回 type=1 的菜单 id/name"""
        result = await db.execute(
            select(AppMenuModel).where(
                AppMenuModel.type == 1, AppMenuModel.user_id == user_id, AppMenuModel.enabled_flag == 1
            )
        )
        rows = result.scalars().all()
        return [{"id": r.id, "name": r.name} for r in rows]

    @staticmethod
    async def get_process(db: AsyncSession, device_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """get_process：检查进程是否存在（基于持久化 pid 判断）"""
        running = False
        for d in device_list or []:
            pid = d.get("pid")
            try:
                if pid is not None and psutil.pid_exists(int(pid)):
                    running = True
                    break
            except Exception:
                continue
        if running:
            return {"message": "进程已存在", "status": "running"}
        return {"status": "stop", "message": "进程不存在"}

    # ===== 图像库（airtest_img）=====
    @staticmethod
    async def _menu_owned_by_user(db: AsyncSession, menu_id: int, user_id: int) -> bool:
        r = await db.execute(
            select(AppMenuModel.id).where(
                AppMenuModel.id == menu_id,
                AppMenuModel.user_id == user_id,
                AppMenuModel.enabled_flag == 1,
            )
        )
        return r.scalar_one_or_none() is not None

    @staticmethod
    async def img_list(db: AsyncSession, page: int, page_size: int, search: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """img_list：分页查询图像库（仅当前用户名下脚本菜单下的图片，按 menu_id 与 img_select 一致隔离）"""
        owned_menus = select(AppMenuModel.id).where(
            AppMenuModel.user_id == user_id,
            AppMenuModel.enabled_flag == 1,
        )
        stmt = select(AppAirtestImageModel).where(
            AppAirtestImageModel.enabled_flag == 1,
            AppAirtestImageModel.menu_id.in_(owned_menus),
        )
        file_name = (search or {}).get("file_name__icontains") or ""
        menu_id = (search or {}).get("menu_id") or None
        if file_name:
            stmt = stmt.where(AppAirtestImageModel.file_name.like(f"%{file_name}%"))
        if menu_id:
            stmt = stmt.where(AppAirtestImageModel.menu_id == int(menu_id))

        total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
        rows = (await db.execute(stmt.order_by(AppAirtestImageModel.id.desc()).offset((page - 1) * page_size).limit(page_size))).scalars().all()
        content = [{"id": r.id, "file_name": r.file_name, "file_path": r.file_path, "create_time": r.create_time, "menu_id": r.menu_id} for r in rows]
        return {"content": content, "total": int(total), "currentPage": page, "pageSize": page_size}

    @staticmethod
    async def add_img(db: AsyncSession, file_name: str, file_path: str, menu_id: Optional[int], user_id: int) -> Dict[str, Any]:
        """新增图像库记录，将通用文件上传结果挂到 app_airtest_images 下"""
        img = AppAirtestImageModel(
            file_name=file_name,
            file_path=file_path,
            menu_id=menu_id or None,
        )
        db.add(img)
        await db.commit()
        await db.refresh(img)
        return {
            "id": img.id,
            "file_name": img.file_name,
            "file_path": img.file_path,
            "menu_id": img.menu_id,
        }

    @staticmethod
    async def img_select(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        """返回级联选择数据"""
        menus = (
            await db.execute(
                select(AppMenuModel).where(
                    AppMenuModel.type == 1, AppMenuModel.user_id == user_id, AppMenuModel.enabled_flag == 1
                )
            )
        ).scalars().all()
        result: List[Dict[str, Any]] = []
        for m in menus:
            node = {"value": m.id, "label": m.name, "children": [], "file_path": ""}
            imgs = (
                await db.execute(
                    select(AppAirtestImageModel).where(
                        AppAirtestImageModel.menu_id == m.id, AppAirtestImageModel.enabled_flag == 1
                    )
                )
            ).scalars().all()
            for img in imgs:
                node["children"].append({"value": img.id, "label": img.file_name, "file_path": img.file_path})
            result.append(node)
        return result

    @staticmethod
    async def delete_img(db: AsyncSession, img_id: int, user_id: int) -> None:
        img = (
            await db.execute(
                select(AppAirtestImageModel).where(
                    AppAirtestImageModel.id == img_id, AppAirtestImageModel.enabled_flag == 1
                )
            )
        ).scalar_one_or_none()
        if not img:
            raise ValueError("记录不存在或已删除")
        if not img.menu_id or not await AppManagementService._menu_owned_by_user(db, int(img.menu_id), user_id):
            raise ValueError("无权删除该图片")
        await db.execute(update(AppAirtestImageModel).where(AppAirtestImageModel.id == img_id).values(enabled_flag=0))
        await db.commit()

    @staticmethod
    async def edit_img(db: AsyncSession, img_id: int, file_name: str, file_path: str, user_id: int) -> None:
        img = (
            await db.execute(
                select(AppAirtestImageModel).where(
                    AppAirtestImageModel.id == img_id, AppAirtestImageModel.enabled_flag == 1
                )
            )
        ).scalar_one_or_none()
        if not img:
            raise ValueError("记录不存在或已删除")
        if not img.menu_id or not await AppManagementService._menu_owned_by_user(db, int(img.menu_id), user_id):
            raise ValueError("无权编辑该图片")
        await db.execute(
            update(AppAirtestImageModel).where(AppAirtestImageModel.id == img_id).values(file_name=file_name, file_path=file_path)
        )
        await db.commit()
    
    @staticmethod
    async def get_app_result_list(
        db: AsyncSession, user_id: int, search_task_name: str = ""
    ) -> List[Dict[str, Any]]:
        """获取APP结果列表"""
        stmt = select(AppResultListModel).where(
            AppResultListModel.user_id == user_id,
            AppResultListModel.enabled_flag == 1,
        )
        if search_task_name:
            stmt = stmt.where(AppResultListModel.task_name.like(f"%{search_task_name}%"))
        result = await db.execute(stmt.order_by(AppResultListModel.id.desc()))
        rows = result.scalars().all()
        data: List[Dict[str, Any]] = []
        for r in rows:
            item = {
                "id": r.id,
                "task_name": r.task_name,
                "device_list": r.device_list,
                "script_list": r.script_list,
                "script_status": r.script_status,
                "result_id": r.result_id,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "username": "admin",
                "status": 0 if r.end_time is None else 1,
            }
            ss = item.get("script_status") or []
            if any(bool((j or {}).get("stopped")) for j in ss):
                item["status"] = 2
            if ss:
                p = 0.0
                count = 0
                for j in ss:
                    if "percent" not in (j or {}):
                        continue
                    p += float((j or {}).get("percent") or 0)
                    count += 1
                item["percent"] = round(p / count, 2) if count else 0
            data.append(item)
        return data

    @staticmethod
    async def delete_app_result(db: AsyncSession, result_id: str, user_id: int) -> Dict[str, Any]:
        """删除 APP 执行汇总及明细；若仍在执行则先尝试停止进程"""
        row = (
            await db.execute(
                select(AppResultListModel).where(
                    AppResultListModel.result_id == result_id,
                    AppResultListModel.user_id == user_id,
                    AppResultListModel.enabled_flag == 1,
                )
            )
        ).scalar_one_or_none()
        if not row:
            return {"deleted": False, "message": "未找到执行记录"}
        if row.end_time is None:
            await AppManagementService.stop_app_process(db, str(result_id), user_id)
        await db.execute(
            delete(AppResultModel).where(
                AppResultModel.result_id == result_id,
                AppResultModel.user_id == user_id,
            )
        )
        await db.execute(
            delete(AppResultListModel).where(
                AppResultListModel.result_id == result_id,
                AppResultListModel.user_id == user_id,
            )
        )
        await db.commit()
        try:
            from .airtest_common import get_project_root

            project_root = get_project_root()
            for rel in (
                project_root / "media" / "app_result" / str(result_id),
                project_root / "static" / "app_result" / str(result_id),
            ):
                if rel.exists():
                    shutil.rmtree(rel, ignore_errors=True)
        except Exception:
            pass
        return {"deleted": True, "message": "已删除"}
    
    @staticmethod
    async def send_app_warn(db: AsyncSession, result_id: str, user_id: int) -> None:
        """有失败步骤时按频次发通知 27（app_error_report）"""
        from app.api.v1.api_automation.service import ApiAutomationService

        row = (
            await db.execute(
                select(AppResultListModel).where(
                    AppResultListModel.result_id == result_id,
                    AppResultListModel.user_id == user_id,
                    AppResultListModel.enabled_flag == 1,
                )
            )
        ).scalar_one_or_none()
        if not row or not row.device_list:
            return
        device_list = [dict(x) for x in (row.device_list or [])]
        updated = False
        for i in device_list:
            did = i.get("deviceid")
            if not did:
                continue
            cnt = (
                await db.execute(
                    select(func.count())
                    .select_from(AppResultModel)
                    .where(
                        AppResultModel.result_id == result_id,
                        AppResultModel.device == str(did),
                        AppResultModel.status == 0,
                        AppResultModel.user_id == user_id,
                        AppResultModel.enabled_flag == 1,
                    )
                )
            ).scalar_one()
            if int(cnt or 0) > 0:
                now_time = time.time()
                notify = int(i.get("notify") or 0)
                notice_time = float(i.get("notice_time") or 0)
                if notify < 10 and now_time > notice_time:
                    i["notify"] = notify + 1
                    await ApiAutomationService._send_notice(
                        db,
                        27,
                        "app_error_report",
                        {"device_name": i.get("name") or did, "result_id": result_id},
                        user_id,
                    )
                    i["notice_time"] = time.time() + 3 * 60
                    updated = True
        if updated:
            row.device_list = device_list
            flag_modified(row, "device_list")
            await db.commit()

    @staticmethod
    async def stop_app_process(
        db: AsyncSession,
        result_id: str,
        user_id: int,
        pid: Optional[int] = None,
        deviceid: Optional[str] = None,
    ) -> bool:
        """停止APP执行进程；传 pid+deviceid 时对齐 stop_process（写结束日志、追加 script_status、通知）"""
        from app.api.v1.api_automation.service import ApiAutomationService
        from .airtest_common import get_performance

        if pid:
            try:
                if psutil.pid_exists(int(pid)):
                    psutil.Process(int(pid)).terminate()
            except Exception:
                pass
            AppManagementService._pid_index.pop(int(pid), None)
            AppManagementService._proc_index.pop(int(pid), None)

        row = (
            await db.execute(
                select(AppResultListModel).where(
                    AppResultListModel.result_id == result_id,
                    AppResultListModel.user_id == user_id,
                    AppResultListModel.enabled_flag == 1,
                )
            )
        ).scalar_one_or_none()
        if not row:
            return False

        if pid and deviceid:
            total = 0
            for sl in row.script_list or []:
                mid = sl.get("id")
                if mid is None:
                    continue
                srow = (
                    await db.execute(
                        select(AppScriptModel).where(
                            AppScriptModel.menu_id == int(mid),
                            AppScriptModel.user_id == user_id,
                            AppScriptModel.enabled_flag == 1,
                        )
                    )
                ).scalar_one_or_none()
                if srow and srow.script:
                    total += len(srow.script)

            res_rows = (
                await db.execute(
                    select(AppResultModel)
                    .where(
                        AppResultModel.result_id == result_id,
                        AppResultModel.device == str(deviceid),
                        AppResultModel.user_id == user_id,
                        AppResultModel.enabled_flag == 1,
                        AppResultModel.status != 2,
                    )
                    .order_by(AppResultModel.id.asc())
                )
            ).scalars().all()

            fail = 0
            passed = 0
            for i in res_rows:
                if int(i.status) == 0:
                    fail += 1
                elif int(i.status) == 1:
                    passed += 1
            un_run = total - passed - fail
            if total == 0:
                percent = 0.0
            else:
                percent = round(((total - fail - 1 - un_run) / total) * 100, 2)

            last = res_rows[-1] if res_rows else None
            if last is None:
                last = (
                    await db.execute(
                        select(AppResultModel)
                        .where(
                            AppResultModel.result_id == result_id,
                            AppResultModel.device == str(deviceid),
                            AppResultModel.user_id == user_id,
                            AppResultModel.enabled_flag == 1,
                        )
                        .order_by(AppResultModel.id.desc())
                        .limit(1)
                    )
                ).scalar_one_or_none()
            menu_id = 0
            if last and last.menu_id is not None:
                menu_id = int(last.menu_id)
            elif row.script_list and row.script_list[0].get("id") is not None:
                menu_id = int(row.script_list[0]["id"])

            base_perf: Dict[str, Any] = {}
            if last and last.performance and isinstance(last.performance, dict):
                base_perf = dict(last.performance)
            for k in ("time", "memory", "cpu", "temperature", "up_network", "down_network"):
                base_perf.setdefault(k, [])
            perf = await asyncio.to_thread(get_performance, str(deviceid), base_perf)

            db.add(
                AppResultModel(
                    device=str(deviceid),
                    result_id=result_id,
                    name="执行结束",
                    status=1,
                    log="自动化任务执行完成，请查看执行结果",
                    before_img="",
                    after_img="",
                    video="",
                    performance=perf,
                    menu_id=menu_id,
                    user_id=user_id,
                    assert_value={},
                )
            )

            ss = list(row.script_status or [])
            ss.append(
                {
                    "device": str(deviceid),
                    "fail": fail,
                    "passed": passed,
                    "un_run": un_run,
                    "total": total,
                    "percent": percent,
                    "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "stopped": True,
                }
            )
            row.script_status = ss
            row.end_time = datetime.now()
            flag_modified(row, "script_status")

            device_name = str(deviceid)
            await ApiAutomationService._send_notice(
                db,
                26,
                "app_report",
                {
                    "device_name": device_name,
                    "result_id": result_id,
                    "total": total,
                    "fail": fail,
                    "passed": passed,
                    "un_run": total - fail - passed,
                    "percent": percent,
                },
                user_id,
            )
            await db.commit()
            return True

        for d in row.device_list or []:
            did = d.get("deviceid")
            pid_in_row = d.get("pid")
            try:
                if pid_in_row is not None and psutil.pid_exists(int(pid_in_row)):
                    psutil.Process(int(pid_in_row)).terminate()
            except Exception:
                pass
            try:
                if pid_in_row is not None:
                    AppManagementService._pid_index.pop(int(pid_in_row), None)
                    AppManagementService._proc_index.pop(int(pid_in_row), None)
            except Exception:
                pass
        row.end_time = datetime.now()
        ss = list(row.script_status or [])
        ss.append({"stopped": True, "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        row.script_status = ss
        flag_modified(row, "script_status")
        await db.commit()
        return True
    
    @staticmethod
    async def get_process_status(db: AsyncSession, result_id: str, user_id: int) -> Dict[str, Any]:
        """获取APP进程状态"""
    
        return {"status": "stop"}

    @staticmethod
    def pause_app_worker(pid: int) -> bool:
        """优先 psutil.suspend，失败再用 POSIX SIGSTOP"""
        import signal

        try:
            if psutil.pid_exists(int(pid)):
                psutil.Process(int(pid)).suspend()
                return True
        except Exception:
            pass
        if os.name == "nt":
            return False
        try:
            os.kill(int(pid), signal.SIGSTOP)
            return True
        except Exception:
            return False

    @staticmethod
    def resume_app_worker(pid: int) -> bool:
        """psutil.resume，失败再用 POSIX SIGCONT"""
        import signal

        try:
            if psutil.pid_exists(int(pid)):
                psutil.Process(int(pid)).resume()
                return True
        except Exception:
            pass
        if os.name == "nt":
            return False
        try:
            os.kill(int(pid), signal.SIGCONT)
            return True
        except Exception:
            return False
    
    @staticmethod
    async def capture_app_screenshots(device, step_name: str) -> str:
        """捕获APP截图"""
        pass
    
    @staticmethod
    async def record_app_video(device, output_path: str) -> str:
        """录制APP视频"""
        pass
    
    @staticmethod
    async def collect_app_performance(device) -> Dict[str, Any]:
        """收集APP性能数据"""
        pass
    
    @staticmethod
    async def validate_app_assertions(assertions: List[Dict[str, Any]], device) -> List[Dict[str, Any]]:
        """验证APP断言"""
        pass