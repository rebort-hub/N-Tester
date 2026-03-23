"""
APP 抓包 - Schema
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MitmproxyDeviceItem(BaseModel):
    deviceid: str
    id: int
    wifi_ip: Optional[str] = None


class MitmproxyStartRequest(BaseModel):
    device_list: List[MitmproxyDeviceItem]
    result_id: str


class MitmproxySingleStartRequest(BaseModel):
    deviceid: str
    id: int
    wifi_ip: str
    port: int = 8088
    result_id: str


class MitmproxyCheckRequest(BaseModel):
    deviceid: str


class MitmproxyStopRequest(BaseModel):
    pid: int
    port: int
    device: List[Dict[str, Any]]


class MitmproxyCloseAgentRequest(BaseModel):
    deviceid: str


class MitmproxyRunLogRequest(BaseModel):
    search: Dict[str, Any] = Field(default_factory=dict)
    currentPage: int = 1
    pageSize: int = 18


class MitmproxyWriteApiRequest(BaseModel):
    request_list: List[Dict[str, Any]]


class MitmproxySingleWriteRequest(BaseModel):
    device_id: int
    request_list: List[Dict[str, Any]]

