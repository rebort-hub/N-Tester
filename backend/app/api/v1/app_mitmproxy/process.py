"""
mitmproxy 进程管理
"""

from __future__ import annotations

import os
import subprocess
import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from config import config


@dataclass
class MitmproxyProcessInfo:
    port: int
    pid: int
    cmd: str


class MitmproxyProcessManager:
    """
    - 按端口管理 mitmweb 进程
    - 通过 adb 写入/清理设备 http_proxy
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._ports: set[int] = set()
        self._proc_by_port: Dict[int, subprocess.Popen] = {}

    def port_check(self, port: int) -> Tuple[bool, str]:
        with self._lock:
            if port in self._ports:
                return False, f"端口{port}已被占用, 请重新选择其他端口"
            self._ports.add(port)
            return True, "端口可用"

    def mitmproxy_start(self, port: int, addon_script_path: str, web_host: str) -> Tuple[bool, Dict[str, Any]]:
        """
        启动 mitmweb
        注意：mitmweb 需要已安装在运行环境中
        """
        try:
            cmd = [
                "mitmweb",
                "-p",
                str(port),
                "--set",
                "block_global=false",
                "-s",
                addon_script_path,
                "--web-host",
                web_host,
            ]

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=os.getcwd(),
                shell=False,
            )
            with self._lock:
                self._proc_by_port[port] = proc
            return True, {"port": port, "status": "running", "message": "mitmproxy启动成功", "pid": proc.pid}
        except Exception as e:
            return False, {"message": f"mitmproxy启动失败，原因：{e}"}

    async def change_agent(self, device_list: List[Dict[str, Any]], port: int) -> bool:
        """
        修改代理：adb settings put global http_proxy {DEVICE_IP}:{port}
        """
        try:
            host = str(config.IP)
            for d in device_list:
                deviceid = d.get("deviceid")
                if not deviceid:
                    continue
                cmd = ["adb", "-s", str(deviceid), "shell", "settings", "put", "global", "http_proxy", f"{host}:{port}"]
                subprocess.run(cmd, capture_output=True, text=True)
            return True
        except Exception:
            return False

    def mitmproxy_stop(self, pid: int, port: int, device_list: List[Dict[str, Any]]) -> Tuple[bool, str]:
        try:
            with self._lock:
                proc = self._proc_by_port.get(port)
            if proc:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except Exception:
                    pass
            # Windows 下兜底 taskkill
            if pid:
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, text=True)
            with self._lock:
                self._ports.discard(port)
                self._proc_by_port.pop(port, None)

            for d in device_list or []:
                deviceid = d.get("deviceid")
                if not deviceid:
                    continue
                subprocess.run(
                    ["adb", "-s", str(deviceid), "shell", "settings", "put", "global", "http_proxy", ":0"],
                    capture_output=True,
                    text=True,
                )
            return True, "mitmproxy停止成功"
        except Exception as e:
            return False, f"mitmproxy停止失败，原因：{e}"


process_mitmproxy = MitmproxyProcessManager()

