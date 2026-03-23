"""
云真机模块 - 数据验证模式
迁移自 l-tester 项目的数据结构
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class DeviceBase(BaseModel):
    """设备基础模式"""
    device_name: str
    device_id: str
    device_type: str
    device_version: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    file_path: str
    device_description: Optional[str] = None


class DeviceCreate(DeviceBase):
    """创建设备模式"""
    pass


class DeviceUpdate(BaseModel):
    """更新设备模式"""
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    device_version: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    device_description: Optional[str] = None


class DeviceResponse(DeviceBase):
    """设备响应模式"""
    id: int
    device_status: int
    user_id: int
    wifi_ip: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """设备列表响应模式"""
    deviceid: str
    name: str
    os_type: str
    version: str
    wifi_ip: Optional[str] = None
    id: Optional[int] = None


class DeviceControlRequest(BaseModel):
    """设备控制请求模式"""
    id: int
    device_id: str
    user_id: int


class DeviceControlResponse(BaseModel):
    """设备控制响应模式"""
    device_url: str
    file_url: str
    log_id: int


class DeviceReleaseRequest(BaseModel):
    """设备释放请求模式"""
    id: int
    log_id: int


class AppInstallRequest(BaseModel):
    """APP安装请求模式"""
    filename: str
    file_url: str
    phone_id: int
    device_id: str
    user_id: int


class AppUninstallRequest(BaseModel):
    """APP卸载请求模式"""
    deviceid: str
    package: str


class PerformanceRequest(BaseModel):
    """性能数据请求模式"""
    device_id: str
    performance: Dict[str, List]


class PerformanceResponse(BaseModel):
    """性能数据响应模式"""
    time: List[str]
    memory: List[float]
    cpu: List[float]
    temperature: List[float]
    up_network: List[float]
    down_network: List[float]


class DeviceLogResponse(BaseModel):
    """设备日志响应模式"""
    id: int
    device_id: int
    device_name: str
    start_time: str
    end_time: Optional[str] = None
    user_id: int


class InstallHistoryResponse(BaseModel):
    """安装历史响应模式"""
    id: int
    apk_name: str
    apk_path: str
    device_id: int
    device_name: str
    create_time: str
    user_id: int


class PackageListRequest(BaseModel):
    """包列表请求模式"""
    folder_path: str


class PackageListResponse(BaseModel):
    """包列表响应模式"""
    id: int
    file_name: str


class DirectInstallRequest(BaseModel):
    """直接安装请求模式"""
    id: int  # 安装历史记录ID


class AddDeviceRequest(BaseModel):
    """添加设备请求模式"""
    device_name: str
    device_id: str
    device_type: str
    device_version: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    file_path: str
    device_description: Optional[str] = None


class EditDeviceRequest(BaseModel):
    """编辑设备请求模式"""
    id: int
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    device_version: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    device_description: Optional[str] = None


class BatchInstallRequest(BaseModel):
    """批量安装请求模式"""
    config: List[Dict[str, Any]]  # 包含path和config的配置列表


class BatchUninstallRequest(BaseModel):
    """批量卸载请求模式"""
    package: str
    device_list: List[str]