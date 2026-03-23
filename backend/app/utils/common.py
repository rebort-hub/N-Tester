# -*- coding: utf-8 -*-
# @author: rebort
import uuid
import re
import json
from typing import Dict, Any
from fastapi import Request


def get_str_uuid():
    return str(uuid.uuid4()).replace("-", "")


async def body_to_json(request: Request) -> Dict[str, Any]:
    """
    处理请求体，将其转换为JSON格式
    迁移自 l-tester/common/request_to_json.py
    
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
