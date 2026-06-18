# -*- coding: utf-8 -*-
# @author: rebort
import os
import secrets
import uuid
import re
import json
from datetime import datetime
from typing import Dict, Any
from fastapi import Request


def get_str_uuid():
    return str(uuid.uuid4()).replace("-", "")


async def body_to_json(request: Request) -> Dict[str, Any]:
    """
    处理请求体，将其转换为JSON格式
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        解析后的JSON数据
    """
    data = await request.body()
    return json.loads(data)


def get_current_time_str() -> str:
    """
    获取当前时间字符串
    
    Returns:
        格式化的时间字符串
    """
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        格式化后的文件大小字符串
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    if i == 0:
        return f"{int(size)} {size_names[i]}"
    else:
        return f"{size:.2f} {size_names[i]}"


def get_content_type(filename: str) -> str:
    """
    根据文件扩展名推断 MIME 类型。

    Args:
        filename: 原始文件名（含扩展名）
    Returns:
        str: MIME 类型字符串，未匹配时返回 application/octet-stream
    """
    ext = os.path.splitext(filename)[-1].lower()
    mapping = {
        ".jmx":  "application/xml",
        ".csv":  "text/csv",
        ".txt":  "text/plain",
        ".json": "application/json",
        ".yaml": "application/yaml",
        ".yml":  "application/yaml",
        ".xls":  "application/vnd.ms-excel",
        ".xlsx": "application/vnd.ms-excel",
        ".zip":  "application/zip",
        ".gz":   "application/gzip",
        # Web 静态资源（供报告在线预览使用）
        ".html": "text/html; charset=utf-8",
        ".htm":  "text/html; charset=utf-8",
        ".css":  "text/css; charset=utf-8",
        ".js":   "application/javascript; charset=utf-8",
        ".svg":  "image/svg+xml",
        ".png":  "image/png",
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif":  "image/gif",
        ".ico":  "image/x-icon",
        ".woff": "font/woff",
        ".woff2":"font/woff2",
        ".ttf":  "font/ttf",
    }
    return mapping.get(ext, "application/octet-stream")

def build_object_key(file_name: str, file_type: str) -> str:
    """
    构建 MinIO 对象路径（bucket 内的相对路径，不含 bucket 名称）。
    格式：{file_type}/{yyyyMMdd}/{uuid}_{原始文件名}
    示例：jmx/20260519/a1b2c3d4e5f6_myscript.jmx
    完整 URL 由 MinIO 自动拼接为：http://host/{bucket}/{object_key}
    Args:
        file_type: 文件类型，如 jmx、csv、txt 等
        file_name: 原始文件名（含扩展名），如 myscript.jmx
    Returns:
        str: {file_type}/{yyyyMMdd}/{uuid}_{原始文件名}
    """
    date_str = datetime.now().strftime('%Y%m%d')
    uid = uuid.uuid4().hex
    return f"{file_type}/{date_str}/{uid}_{file_name}"


def parse_user_agent(user_agent: str) -> Dict[str, str]:
    """
    解析用户代理字符串，提取浏览器和操作系统信息
    
    Args:
        user_agent: 用户代理字符串
        
    Returns:
        包含浏览器和操作系统信息的字典
    """
    if not user_agent:
        return {"browser": "Unknown", "os": "Unknown"}
    
    browser = "Unknown"
    os = "Unknown"
    
    # 检测操作系统
    if "Windows NT 10.0" in user_agent:
        os = "Windows 10"
    elif "Windows NT 6.3" in user_agent:
        os = "Windows 8.1"
    elif "Windows NT 6.2" in user_agent:
        os = "Windows 8"
    elif "Windows NT 6.1" in user_agent:
        os = "Windows 7"
    elif "Windows NT" in user_agent:
        os = "Windows"
    elif "Mac OS X" in user_agent:
        os = "macOS"
    elif "Linux" in user_agent:
        os = "Linux"
    elif "Android" in user_agent:
        os = "Android"
    elif "iPhone" in user_agent or "iPad" in user_agent:
        os = "iOS"
    
    # 检测浏览器
    if "Edg/" in user_agent:
        browser = "Microsoft Edge"
    elif "Chrome/" in user_agent and "Safari/" in user_agent:
        browser = "Google Chrome"
    elif "Firefox/" in user_agent:
        browser = "Mozilla Firefox"
    elif "Safari/" in user_agent and "Chrome/" not in user_agent:
        browser = "Safari"
    elif "Opera/" in user_agent or "OPR/" in user_agent:
        browser = "Opera"
    elif "MSIE" in user_agent or "Trident/" in user_agent:
        browser = "Internet Explorer"
    
    return {"browser": browser, "os": os}


def get_location_by_ip(ip_address: str) -> str:
    """
    根据IP地址获取地理位置
    
    Args:
        ip_address: IP地址
        
    Returns:
        地理位置字符串
    """
    # 简化处理，实际项目中可以集成第三方IP定位服务
    if not ip_address or ip_address in ["127.0.0.1", "localhost", "::1"]:
        return "本地"
    
    # 检查是否为内网IP
    if (ip_address.startswith("192.168.") or 
        ip_address.startswith("10.") or 
        ip_address.startswith("172.")):
        return "内网"
    
    # 这里可以集成第三方IP定位服务，如：
    # - 高德地图IP定位API
    # - 百度地图IP定位API  
    # - ipapi.co
    # - ip-api.com
    
    return "未知位置"

def format_sse_event(data: dict) -> str:
    """将字典格式化为 SSE text/event-stream 协议数据帧。"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def get_temp_file_path(filename: str, sub_dir: str = 'jmx') -> 'Path':
    """返回后端根目录下临时文件路径，目录不存在时自动创建。

    路径：{project_root}/temp/{sub_dir}/{filename}
    project_root 以本文件（app/utils/common.py）向上两级推算，即 backend 根目录。

    Args:
        filename: 文件名（含扩展名），如 'JMX123456.jmx'
        sub_dir:  temp 下的子目录，默认 'jmx'
    Returns:
        Path 对象，父目录已保证存在
    """
    from pathlib import Path
    project_root = Path(__file__).resolve().parents[2]
    temp_dir = project_root / 'temp' / sub_dir
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir / filename


def get_next_code(prefix: str, length: int) -> str:
    """
    生成固定前缀 + 随机指定长度数字的编号。
    唯一性由数据库 unique 约束兜底，调用方捕获 IntegrityError 后重试即可。

    :param prefix: 编号前缀（如 "JMX"）
    :param length: 数字部分的长度（必须 >= 1）
    :return: 形如 "JMX123456" 的编号（数字部分无前导零）
    :raises ValueError: 当 length < 1 时抛出
    """
    if length < 1:
        raise ValueError("数字长度必须至少为 1")

    # 计算最小值和最大值（无前导零）
    min_value = 10 ** (length - 1) if length > 1 else 1
    max_value = (10 ** length) - 1

    # 生成安全随机整数
    num = secrets.randbelow(max_value - min_value + 1) + min_value
    return f"{prefix}{num}"


def fmt_cloudflare_html_resp(e: Exception, hint: str = '请检查地址或网络配置') -> str:
    """格式化可能含 HTML body 的异常信息（Cloudflare / nginx 等错误页），避免长 HTML 刷屏。

    :param e:    原始异常
    :param hint: HTML 被省略时附加的提示语，调用方按场景传入
    :return:     可读的单行错误描述
    """
    msg = str(e)
    body_idx = msg.find('Body: <')
    if body_idx != -1:
        head = msg[:body_idx].rstrip('; ')
        return f"{head} | Body: [HTML 已省略，{hint}]"
    if len(msg) > 300:
        return msg[:300] + ' ...[已截断]'
    return msg