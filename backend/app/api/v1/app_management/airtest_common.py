# -*- coding: utf-8 -*-
"""
APP 自动化 Airtest 运行时公共函数
一比一从 l-tester/views/app/app_common.py + l-tester/common/device.py 迁移（同步化，供子进程调用）
"""
from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Airtest 在步骤执行时才会被 import（避免未安装时影响整个后端启动）
try:
    from airtest.core.api import assert_exists, exists, keyevent, sleep, start_app, text, touch
    from airtest.core.cv import Template
except ImportError:  # pragma: no cover
    assert_exists = exists = keyevent = sleep = start_app = text = touch = None  # type: ignore
    Template = None  # type: ignore


def _config_str(*attr_names: str) -> str:
    """优先从 config（.env / pydantic-settings）读取，子进程 import config 时会重新加载 .env"""
    try:
        from config import config

        for name in attr_names:
            v = getattr(config, name, None)
            if v is not None and str(v).strip():
                return str(v).strip()
    except Exception:
        pass
    return ""


def get_project_root() -> Path:
    """仓库/项目根：config(.env) > 系统环境变量 > 自动推断"""
    root = _config_str("APP_PROJECT_ROOT", "PROJECT_PATH")
    if root:
        return Path(root).resolve()
    env = os.getenv("APP_PROJECT_ROOT") or os.getenv("PROJECT_PATH")
    if env:
        return Path(env).resolve()
    # .../backend/app/api/v1/app_management/airtest_common.py -> parents[5] = repo root
    return Path(__file__).resolve().parents[5]


def get_public_base_url() -> str:
    """对外访问基址：APP_PUBLIC_BASE_URL > PUBLIC_BASE_URL(env) > config.BASE_URL > 默认"""
    u = _config_str("APP_PUBLIC_BASE_URL")
    if u:
        return u.rstrip("/")
    env_u = os.getenv("PUBLIC_BASE_URL") or os.getenv("APP_PUBLIC_BASE_URL")
    if env_u and str(env_u).strip():
        return str(env_u).strip().rstrip("/")
    try:
        from config import config

        bu = getattr(config, "BASE_URL", None)
        if bu:
            return str(bu).rstrip("/")
    except Exception:
        pass
    return "http://127.0.0.1:8000"


def _template_path(raw: str, project_root: Path) -> str:
    if not raw:
        return raw
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    p = raw.strip()
    if p.startswith("."):
        p = str(project_root / p.lstrip("./").replace("\\", "/"))
    elif not os.path.isabs(p):
        p = str(project_root / p.replace("\\", "/"))
    return p


def wait_until_exists(device: str, target: str, timeout: float, interval: float = 1.0, project_root: Optional[Path] = None) -> bool:
    if Template is None or exists is None:
        return False
    root = project_root or get_project_root()
    target = _template_path(target, root)
    start_time = time.time()
    while True:
        if exists(Template(target)):
            return True
        elapsed = time.time() - start_time
        if elapsed > 20:
            for rel in [
                "media/app_img/allow_confirm.png",
                "media/app_img/vivo_s19_allow_app.png",
                "media/app_img/vivo_s19_allow_use.png",
                "media/app_img/android_确定.png",
                "media/app_img/android_初始同意隐私协议.png",
                "media/app_img/android_关闭公告按钮.png",
            ]:
                close_target(str(root / rel))
        if elapsed > timeout:
            return False
        time.sleep(interval)


def wait_until_install(device_id: str, timeout: float = 300, interval: float = 3.0) -> bool:
    root = get_project_root()
    res = close_target(str(root / "media/app_img/vivos19_check.png"))
    res = close_target(str(root / "media/app_img/vivos19_install.png"))
    return res


def close_target(target: str) -> bool:
    if Template is None or exists is None or touch is None:
        return False
    if exists(Template(target)):
        touch(Template(target))
        return True
    return False


def wait_until_download(target: str, timeout: float, interval: float = 3.0, project_root: Optional[Path] = None) -> bool:
    if Template is None or exists is None:
        return False
    root = project_root or get_project_root()
    target = _template_path(target, root)
    try:
        start_time = time.time()
        while True:
            if exists(Template(target, threshold=0.7)):
                return True
            if time.time() - start_time > timeout:
                return False
            sleep(interval)
    except Exception:
        return False


def assert_img_exists(target: str, project_root: Optional[Path] = None) -> bool:
    if assert_exists is None or Template is None:
        return False
    root = project_root or get_project_root()
    target = _template_path(target, root)
    try:
        return bool(assert_exists(Template(target)))
    except Exception:
        return False


def allocate_install_app(device_id: str, apk_path: str) -> bool:
    try:
        cmd = ["adb", "-s", device_id, "install", "-r", apk_path]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=6000)
        out = (res.stdout or "") + (res.stderr or "")
        return "Success" in out
    except Exception:
        return False


def allocate_package(device_id: str, version: str, channel_id: str) -> bool:
    """从共享目录选包安装（对齐旧逻辑，修复原 for 循环里 file_path 未定义问题）"""
    try:
        if channel_id == "1000":
            folder_path = rf"\\Share\upload\包体共享\国服{version}正式包\android\官包"
        elif channel_id in ["1006", "1007", "1008", "1019", "1020"]:
            folder_path = rf"\\Share\upload\包体共享\国服{version}正式包\android\cps"
        else:
            folder_path = rf"\\Share\upload\包体共享\国服{version}正式包\android\广告"
        if not os.path.isdir(folder_path):
            return False
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path) and channel_id in filename:
                return allocate_install_app(device_id, file_path)
        return False
    except Exception:
        return False


def check_app_install(device_id: str, package_name: str) -> bool:
    if not package_name:
        return True
    try:
        cmd = ["adb", "-s", device_id, "shell", "pm", "path", package_name]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        out = (res.stdout or "") + (res.stderr or "")
        return "package:" in out
    except Exception:
        return False


def device_rm_file(device_id: str) -> None:
    """删除差更文件：路径由环境变量 APP_DEVICE_RM_PATHS 分号分隔"""
    raw = os.getenv("APP_DEVICE_RM_PATHS", "")
    if not raw.strip():
        return
    for p in raw.split(";"):
        p = p.strip()
        if not p:
            continue
        subprocess.run(["adb", "-s", device_id, "shell", "rm", "-rf", p], capture_output=True, text=True, timeout=120)


def ocr_version(image_path: str) -> str:
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(image_path)
        return (pytesseract.image_to_string(img, lang="chi_sim+eng") or "").strip() or "unknown"
    except Exception:
        return "unknown"


# ---------- 性能（同步 adb，对齐旧 get_performance 数据结构） ----------


def _shell(device_id: str, *args: str, timeout: int = 30) -> str:
    try:
        r = subprocess.run(["adb", "-s", device_id, "shell", *args], capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "") + (r.stderr or "")
    except Exception:
        return ""


def get_now_str() -> str:
    now = time.localtime()
    return f"{now.tm_min}:{now.tm_sec}"


def get_memory(device_id: str) -> float:
    try:
        out = _shell(device_id, "cat", "/proc/meminfo")
        parts = out.split()
        if len(parts) < 8:
            return 0.0
        return round((int(parts[1]) - int(parts[7])) / int(parts[1]) * 100, 2)
    except Exception:
        return 0.0


def get_cpu(device_id: str) -> float:
    try:
        def stat():
            out = _shell(device_id, "cat", "/proc/stat")
            line = [x for x in out.splitlines() if x.startswith("cpu ")]
            if not line:
                return None
            return [int(x) for x in line[0].split()[1:8]]

        s1 = stat()
        time.sleep(0.1)
        s2 = stat()
        if not s1 or not s2:
            return 0.0
        total1, total2 = sum(s1), sum(s2)
        idle1, idle2 = s1[3], s2[3]
        total = total2 - total1
        idle = idle2 - idle1
        if total <= 0:
            return 0.0
        return round((total - idle) / total * 100, 2)
    except Exception:
        return 0.0


def get_temperature(device_id: str) -> float:
    try:
        out = _shell(device_id, "dumpsys", "battery")
        for line in out.splitlines():
            if "temperature" in line.lower():
                return int(line.split(":")[1].strip()) / 10
        return 0.0
    except Exception:
        return 0.0


def get_network(device_id: str) -> Tuple[float, float]:
    try:
        cmd = ["adb", "-s", device_id, "shell", "cat", "/proc/net/dev"]
        o1 = subprocess.check_output(cmd, timeout=10).decode().strip()
        rx1 = tx1 = 0
        for line in o1.splitlines():
            if ":" in line and "lo:" not in line:
                fields = line.split(":")[1].strip().split()
                rx1 += int(fields[0])
                tx1 += int(fields[8])
        time.sleep(1)
        o2 = subprocess.check_output(cmd, timeout=10).decode().strip()
        rx2 = tx2 = 0
        for line in o2.splitlines():
            if ":" in line and "lo:" not in line:
                fields = line.split(":")[1].strip().split()
                rx2 += int(fields[0])
                tx2 += int(fields[8])
        upload_speed = (tx2 - tx1) * 8 / 1024
        download_speed = (rx2 - rx1) * 8 / 1024 / 1024
        return round(upload_speed, 2), round(download_speed, 2)
    except Exception:
        return 0.0, 0.0


def get_performance(device_id: str, performance: Dict[str, Any]) -> Dict[str, Any]:
    try:
        memory = get_memory(device_id)
        cpu = get_cpu(device_id)
        temperature = get_temperature(device_id)
        network = get_network(device_id)
        performance.setdefault("time", []).append(get_now_str())
        performance.setdefault("memory", []).append(memory)
        performance.setdefault("cpu", []).append(cpu)
        performance.setdefault("temperature", []).append(temperature)
        performance.setdefault("up_network", []).append(network[0])
        performance.setdefault("down_network", []).append(network[1])
        return performance
    except Exception:
        performance.setdefault("time", []).append(get_now_str())
        performance.setdefault("memory", []).append(0)
        performance.setdefault("cpu", []).append(0)
        performance.setdefault("temperature", []).append(0)
        performance.setdefault("up_network", []).append(0)
        performance.setdefault("down_network", []).append(0)
        return performance


def get_sms(now_time: int, sms_device_id: str, timeout: int = 3000000, interval: float = 1.0) -> str:
    """从「验证码手机」读短信（adb content query），对齐旧 common/device.get_sms"""
    sms_code = "000000"
    if not sms_device_id:
        return sms_code
    pattern = _config_str("APP_SMS_BODY_KEYWORD") or os.getenv("APP_SMS_BODY_KEYWORD", "识别文案")
    while sms_code == "000000":
        try:
            cmd = ["adb", "-s", sms_device_id, "shell", "content", "query", "--uri", "content://sms/"]
            data = subprocess.check_output(cmd, timeout=30).decode("utf-8", errors="ignore")
            rows = data.split("Row: ")
            if len(rows) < 2:
                time.sleep(interval)
                continue
            key_value_pairs = rows[1].split(", ")
            my_dict: Dict[str, str] = {}
            for pair in key_value_pairs:
                if "body" in pair or "date" in pair:
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        my_dict[key.strip()] = value.strip()
            if int(my_dict.get("date", "0")) > now_time and pattern in my_dict.get("body", ""):
                m = re.search(r"\d+", my_dict.get("body", ""))
                if m:
                    return m.group(0)
        except Exception:
            pass
        if time.time() * 1000 - now_time > timeout:
            return sms_code
        time.sleep(interval)
    return sms_code


# 设备硬编码映射（与旧 app_script.py 一致）
PHONE_BY_DEVICE = {
    "10CE6R0NP7001KX": "19065402394",
    "10CE970KH2002YQ": "18127803668",
    "10AE8D2RXP001CT": "18148757543",
    "10CE9F1UHC0037A": "19928355488",
    "10AE650C38000QS": "13143723397",
    "10CE7U0CTD0023A": "19124175810",
}

EMAIL_BY_DEVICE = {
    "10CE6R0NP7001KX": "linjiyong@bluepoch.com",
    "10CE970KH2002YQ": "z19928355488@gmail.com",
    "10AE8D2RXP001CT": "ljy951697407@163.com",
    "10CE9F1UHC0037A": "linjiyong996@gmail.com",
    "10AE650C38000QS": "3110316730@qq.com",
    "10CE7U0CTD0023A": "ljy951697407@163.com",
}

SMS_DEVICE_BY_TEST_DEVICE = {
    "10CE6R0NP7001KX": "6HJDU19723002103",
    "10CE970KH2002YQ": "7fb1efb",
    "10AE8D2RXP001CT": "f87c1a21",
    "10CE9F1UHC0037A": "R5CW32RABBR",
    "10AE650C38000QS": "AXYFVB1C03005594",
    "10CE7U0CTD0023A": "22X0219924002278",
}
