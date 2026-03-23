"""
APP 抓包
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Tuple
import yaml
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.cloud_device.model import AppDevice
from app.common.response import success_response, error_response
from config import config
from .model import MitmproxyApi
from .process import process_mitmproxy


class MitmproxyService:
    @staticmethod
    def _yaml_path() -> Path:
       
        return Path(config.BASEDIR) / "static" / "mitmproxy" / "mitmproxy_config_file.yaml"

    @staticmethod
    def _ensure_yaml() -> None:
        p = MitmproxyService._yaml_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_text(yaml.safe_dump({"device_list": []}, allow_unicode=True), encoding="utf-8")

    @staticmethod
    def _read_yaml() -> Dict[str, Any]:
        MitmproxyService._ensure_yaml()
        p = MitmproxyService._yaml_path()
        content = p.read_text(encoding="utf-8").strip()
        if not content:
            return {"device_list": []}
        return yaml.safe_load(content) or {"device_list": []}

    @staticmethod
    def _write_yaml(data: Dict[str, Any]) -> None:
        MitmproxyService._ensure_yaml()
        p = MitmproxyService._yaml_path()
        p.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")

    @staticmethod
    def _addon_script_path() -> str:
        """
        mitmweb -s 的脚本路径。
        这里先放到 static/mitmproxy 下，后续你们改成独立部署的 addon。
        """
        addon = Path(config.BASEDIR) / "static" / "mitmproxy" / "mitmproxy_save_to_db.py"
        return str(addon)

    @staticmethod
    def _web_host() -> str:
        """
        mitmweb Web UI 绑定地址
        这里用 0.0.0.0 便于局域网访问（可按需收紧）。
        """
        return "0.0.0.0"

    @staticmethod
    async def mitmproxy_start(data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        body: { device_list: [...], result_id: "" }
        """
        yaml_data = MitmproxyService._read_yaml()
        yaml_data.setdefault("device_list", [])

        device_id_to_index: Dict[str, int] = {}
        for idx, d in enumerate(yaml_data["device_list"]):
            deviceid = d.get("deviceid")
            if deviceid:
                device_id_to_index[str(deviceid)] = idx

        for new_device in data.get("device_list") or []:
            deviceid = new_device.get("deviceid")
            if not deviceid:
                continue
            if str(deviceid) in device_id_to_index:
                yaml_data["device_list"][device_id_to_index[str(deviceid)]]["result_id"] = data.get("result_id")
            else:
                to_add = dict(new_device)
                to_add["result_id"] = data.get("result_id")
                yaml_data["device_list"].append(to_add)

        MitmproxyService._write_yaml(yaml_data)

        port = 8088
        ok, _ = process_mitmproxy.port_check(port)
        if ok:
            # 尝试启动 mitmweb，并设置代理
            process_mitmproxy.mitmproxy_start(
                port=port,
                addon_script_path=MitmproxyService._addon_script_path(),
                web_host=MitmproxyService._web_host(),
            )
        await process_mitmproxy.change_agent(data.get("device_list") or [], port)
        return True, "启动成功"

    @staticmethod
    async def mitmproxy_single_start(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        body: { deviceid, result_id, wifi_ip, id, port }
        """
        yaml_data = MitmproxyService._read_yaml()
        yaml_data.setdefault("device_list", [])

        device_list_item = {
            "deviceid": data["deviceid"],
            "result_id": data["result_id"],
            "wifi_ip": data["wifi_ip"],
            "id": data["id"],
        }

        found = False
        for d in yaml_data["device_list"]:
            if d.get("deviceid") == data["deviceid"]:
                d.update(device_list_item)
                found = True
        if not found:
            yaml_data["device_list"].append(device_list_item)
        MitmproxyService._write_yaml(yaml_data)

        port = int(data.get("port") or 8088)
        ok, message = process_mitmproxy.port_check(port)
        if ok:
            started, res = process_mitmproxy.mitmproxy_start(
                port=port,
                addon_script_path=MitmproxyService._addon_script_path(),
                web_host=MitmproxyService._web_host(),
            )
            await process_mitmproxy.change_agent([device_list_item], port)
            return started, (res if started else {"message": res.get("message")})
        else:
            await process_mitmproxy.change_agent([device_list_item], port)
            return True, {}

    @staticmethod
    async def mitmproxy_check(deviceid: str) -> Dict[str, Any]:
        import subprocess

        try:
            res = subprocess.check_output(
                ["adb", "-s", str(deviceid), "shell", "settings", "get", "global", "http_proxy"],
                text=True,
            ).strip()
            if res == ":0" or res == "":
                return {"status": "stop"}
            return {"status": "running"}
        except Exception:
            return {"status": "stop"}

    @staticmethod
    async def mitmproxy_stop(pid: int, port: int, device_list: List[Dict[str, Any]]) -> Tuple[bool, str]:
        return process_mitmproxy.mitmproxy_stop(pid=pid, port=port, device_list=device_list)

    @staticmethod
    async def mitmproxy_close_agent(deviceid: str) -> bool:
        import subprocess

        try:
            subprocess.run(
                ["adb", "-s", str(deviceid), "shell", "settings", "put", "global", "http_proxy", ":0"],
                capture_output=True,
                text=True,
            )
            return True
        except Exception:
            return False

    @staticmethod
    async def mitmproxy_write_api(db: AsyncSession, request_list: List[Dict[str, Any]], current_user_id: int) -> None:
        """
        从 request_list 逆序写入。
        """
        for i in (request_list or [])[::-1]:
            device_pk = int(i.get("device_id") or 0)
            if not device_pk:
                continue
            db.add(
                MitmproxyApi(
                    user_id=current_user_id,
                    device_id=device_pk,
                    result_id=str(i.get("result_id") or ""),
                    url=str(i.get("url") or ""),
                    method=str(i.get("method") or "POST"),
                    request_headers=i.get("request_headers") or {},
                    request_body=i.get("request_body") or {},
                    response_headers=i.get("response_headers") or {},
                    response_body=i.get("response_body") or {},
                    status=1 if int(i.get("status_code") or 0) == 200 else 0,
                    res_time=str(round(float(i.get("res_time") or 0) * 1000)),
                )
            )

    @staticmethod
    async def single_write(db: AsyncSession, device_id: int, request_list: List[Dict[str, Any]], current_user_id: int) -> None:
        for i in (request_list or [])[::-1]:
            db.add(
                MitmproxyApi(
                    user_id=current_user_id,
                    device_id=int(device_id),
                    result_id=str(i.get("result_id") or ""),
                    url=str(i.get("url") or ""),
                    method=str(i.get("method") or "POST"),
                    request_headers=i.get("headers") or i.get("request_headers") or {},
                    request_body=i.get("body") or i.get("request_body") or {},
                    response_headers=i.get("response_headers") or {},
                    response_body=i.get("response_body") or {},
                    status=1 if str(i.get("status_code") or "") == "200" else 0,
                    res_time=str(i.get("res_time") or ""),
                )
            )

    @staticmethod
    async def run_log_paged(
        db: AsyncSession,
        current_user_id: int,
        search: Dict[str, Any],
        page: int,
        page_size: int,
    ) -> Dict[str, Any]:
        conditions = [MitmproxyApi.user_id == current_user_id]
        device_id = (search or {}).get("device_id")
        result_id = (search or {}).get("result_id")
        if device_id not in (None, "", 0):
            conditions.append(MitmproxyApi.device_id == int(device_id))
        if result_id not in (None, ""):
            conditions.append(MitmproxyApi.result_id == str(result_id))

        total_result = await db.execute(select(func.count()).select_from(MitmproxyApi).where(*conditions))
        total = int(total_result.scalar() or 0)

        offset = max(page - 1, 0) * page_size
        result = await db.execute(
            select(MitmproxyApi)
            .where(*conditions)
            .order_by(MitmproxyApi.id.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = result.scalars().all()
        content = []
        for r in rows:
            content.append(
                {
                    "id": r.id,
                    "device_id": r.device_id,
                    "result_id": r.result_id,
                    "url": r.url,
                    "method": r.method,
                    "request_headers": r.request_headers,
                    "request_body": r.request_body,
                    "response_headers": r.response_headers,
                    "response_body": r.response_body,
                    "status": r.status,
                    "res_time": r.res_time,
                    "create_time": r.create_time.strftime("%Y-%m-%d %H:%M:%S") if r.create_time else "",
                }
            )

        return {"content": content, "total": total, "currentPage": page, "pageSize": page_size}

