"""
云真机模块 - 业务逻辑服务
迁移自 l-tester/views/app/device_view.py 和 l-tester/common/device.py
"""
import os
import re
import subprocess
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload

from .model import AppDevice, AppDeviceLog, AppDeviceInstall
from app.common.response import success_response, error_response
from app.utils.common import get_current_time_str
from config import config


class DeviceService:
    """设备管理服务"""

    @staticmethod
    def _with_base_url(path: Any) -> Any:
        """
        对齐旧架构 img_review：把相对路径补全为可访问的绝对URL。
        - 旧：source_ip + /xxx
        - 新：使用 config.BASE_URL 作为对外访问基地址
        """
        if not path or not isinstance(path, str):
            return path
        if path.startswith("http://") or path.startswith("https://"):
            return path
        base = str(getattr(config, "BASE_URL", "") or "").rstrip("/")
        if not base:
            return path
        if path.startswith("/"):
            return f"{base}{path}"
        return f"{base}/{path}"
    
    @staticmethod
    async def list_devices(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        """获取设备列表"""
        try:
            # 获取数据库中的设备列表
            result = await db.execute(
                select(AppDevice).where(AppDevice.user_id == user_id)
            )
            device_list = result.scalars().all()
            
            # 获取实际连接的设备信息
            device_info_result = await DeviceService._get_device_info()
            if not device_info_result[0]:
                return []
            
            # 合并数据库信息和实际设备信息
            devices = []
            for actual_device in device_info_result[1]:
                for db_device in device_list:
                    if actual_device["deviceid"] == db_device.device_id:
                        actual_device["id"] = db_device.id
                        # 对齐旧架构：如果数据库中维护了设备名称，则覆盖探测到的名称
                        actual_device["name"] = db_device.device_name
                        devices.append(actual_device)
                        break
            
            return devices
        except Exception as e:
            print(f"获取设备列表失败: {e}")
            return []
    
    @staticmethod
    async def get_device_details(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        """获取设备详细信息列表"""
        try:
            # 先将所有空闲设备标记为离线
            await db.execute(
                update(AppDevice)
                .where(AppDevice.device_status == 1)
                .values(device_status=3)
            )
            
            # 获取实际连接的设备信息
            device_info_result = await DeviceService._get_device_info()
            if device_info_result[0]:
                # 将实际连接的设备状态更新为空闲
                for device_info in device_info_result[1]:
                    await db.execute(
                        update(AppDevice)
                        .where(AppDevice.device_id == device_info["deviceid"], AppDevice.device_status == 3)
                        .values(device_status=1)
                    )
            
            # 获取分页数据
            result = await db.execute(
                select(AppDevice)
                .where(AppDevice.user_id == user_id)
                .order_by(AppDevice.device_status)
            )
            devices = result.scalars().all()
            
            # 转换为字典格式并添加wifi_ip信息
            device_list = []
            for device in devices:
                device_dict = {
                    "id": device.id,
                    "device_name": device.device_name,
                    "device_id": device.device_id,
                    "device_status": device.device_status,
                    "device_type": device.device_type,
                    "device_version": device.device_version,
                    "device_info": device.device_info,
                    "file_path": device.file_path,
                    "device_description": device.device_description,
                    "wifi_ip": None
                }
                
                # 添加wifi_ip信息
                if device_info_result[0]:
                    for actual_device in device_info_result[1]:
                        if device.device_id == actual_device["deviceid"]:
                            device_dict["wifi_ip"] = actual_device.get("wifi_ip")
                            break
                
                device_list.append(device_dict)
            
            await db.commit()
            return device_list
            
        except Exception as e:
            await db.rollback()
            print(f"获取设备详细信息失败: {e}")
            return []

    @staticmethod
    async def sync_stf_devices(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """
        从 STF 设备池同步设备到 app_devices
        - 不依赖本机 adb 预先添加
        - 同步后仍可被 device_info_list/use_device 等流程使用
        """
        if not getattr(config, "STF_BASE_URL", ""):
            return {"success": False, "message": "未配置 STF_BASE_URL"}
        if not getattr(config, "STF_TOKEN", ""):
            return {"success": False, "message": "未配置 STF_TOKEN"}

        base = str(config.STF_BASE_URL).rstrip("/")
        url = f"{base}/api/v1/devices"
        headers = {"Authorization": f"Bearer {config.STF_TOKEN}"}

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            payload = resp.json()
            devices = payload.get("devices") or payload.get("data") or []
        except Exception as e:
            return {"success": False, "message": f"拉取 STF 设备失败: {e}"}

        created = 0
        updated = 0

        for d in devices:
            # STF 常见字段：serial / udid / present / ready / using / manufacturer / model / version
            device_id = str(d.get("serial") or d.get("udid") or d.get("id") or "").strip()
            if not device_id:
                continue

            manufacturer = str(d.get("manufacturer") or d.get("brand") or "").strip()
            model = str(d.get("model") or d.get("name") or "").strip()
            version = d.get("version") or d.get("sdk") or d.get("abi")

            device_name = " ".join([x for x in [manufacturer, model] if x]).strip() or device_id
            device_type = (manufacturer or "Android").upper() or "ANDROID"
            device_version = str(version) if version is not None else ""

            present = d.get("present")
            ready = d.get("ready")
            using = d.get("using") or d.get("owner") or d.get("booked")
            if present is False:
                device_status = 3
            elif using:
                device_status = 2
            else:
                device_status = 1 if ready is not False else 3

            device_info = d

            # STF 不一定提供图片，保持空串；前端做兜底占位图
            file_path = ""

            # upsert by (user_id, device_id)
            existing_result = await db.execute(
                select(AppDevice).where(AppDevice.user_id == user_id, AppDevice.device_id == device_id)
            )
            existing = existing_result.scalar_one_or_none()
            if existing:
                existing.device_name = device_name
                existing.device_type = device_type
                existing.device_version = device_version
                existing.device_info = device_info
                existing.device_status = device_status
                if file_path != "":
                    existing.file_path = file_path
                updated += 1
            else:
                db.add(
                    AppDevice(
                        user_id=user_id,
                        device_id=device_id,
                        device_name=device_name,
                        device_type=device_type,
                        device_version=device_version,
                        device_info=device_info,
                        device_status=device_status,
                        file_path=file_path,
                        device_description="",
                    )
                )
                created += 1

        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": f"同步入库失败: {e}"}

        return {"success": True, "message": "同步完成", "created": created, "updated": updated, "total": len(devices)}

    @staticmethod
    async def get_device_details_paged(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 24,
        search: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        获取设备详细信息（分页 + 筛选）
        对齐旧架构 device_info_list：body.search + currentPage/pageSize
        """
        try:
            # 先将所有空闲设备标记为离线
            await db.execute(
                update(AppDevice)
                .where(AppDevice.device_status == 1)
                .values(device_status=3)
            )

            device_info_result = await DeviceService._get_device_info()
            if device_info_result[0]:
                for device_info in device_info_result[1]:
                    await db.execute(
                        update(AppDevice)
                        .where(
                            AppDevice.device_id == device_info["deviceid"],
                            AppDevice.device_status == 3,
                        )
                        .values(device_status=1)
                    )

            search = search or {}
            device_version = search.get("device_version")
            device_type = search.get("device_type")
            device_status = search.get("device_status")

            conditions = [AppDevice.user_id == user_id]
            if device_version not in (None, ""):
                conditions.append(AppDevice.device_version == str(device_version))
            if device_type not in (None, ""):
                conditions.append(AppDevice.device_type == str(device_type))
            if device_status not in (None, ""):
                conditions.append(AppDevice.device_status == int(device_status))

            # total
            total_result = await db.execute(
                select(func.count()).select_from(AppDevice).where(*conditions)
            )
            total = int(total_result.scalar() or 0)

            # page items
            offset = max(page - 1, 0) * page_size
            result = await db.execute(
                select(AppDevice)
                .where(*conditions)
                .order_by(AppDevice.device_status)
                .offset(offset)
                .limit(page_size)
            )
            devices = result.scalars().all()

            # wifi_ip map
            wifi_ip_map: Dict[str, Any] = {}
            if device_info_result[0]:
                for actual in device_info_result[1]:
                    wifi_ip_map[str(actual.get("deviceid"))] = actual.get("wifi_ip")

            content: List[Dict[str, Any]] = []
            for device in devices:
                content.append(
                    {
                        "id": device.id,
                        "device_name": device.device_name,
                        "device_id": device.device_id,
                        "device_status": device.device_status,
                        "device_type": device.device_type,
                        "device_version": device.device_version,
                        "device_info": device.device_info,
                        "file_path": DeviceService._with_base_url(device.file_path),
                        "device_description": device.device_description,
                        "wifi_ip": wifi_ip_map.get(str(device.device_id)),
                    }
                )

            await db.commit()
            return {
                "content": content,
                "total": total,
                "currentPage": page,
                "pageSize": page_size,
            }
        except Exception as e:
            await db.rollback()
            print(f"获取设备详细信息(分页)失败: {e}")
            return {
                "content": [],
                "total": 0,
                "currentPage": page,
                "pageSize": page_size,
            }
    
    @staticmethod
    async def acquire_device(db: AsyncSession, device_id: str, user_id: int) -> Dict[str, Any]:
        """获取设备控制权，返回远程控制链接"""
        try:
            # 检查设备状态
            result = await db.execute(
                select(AppDevice).where(AppDevice.id == int(device_id))
            )
            device = result.scalar_one_or_none()
            
            if not device:
                return {"success": False, "message": "设备不存在"}
            
            if device.device_status != 1:
                return {"success": False, "message": "该设备正在使用中"}
            
            # 生成控制链接
            from config import config
            device_url = f"{config.DEVICE_URL}/#!action=stream&udid={device.device_id}&player=mse&ws=ws%3A%2F%2F{config.IP}%3A8000%2F%3Faction%3Dproxy-adb%26remote%3Dtcp%253A8886%26udid%3D{device.device_id}"
            file_url = f"{config.DEVICE_URL}/#!action=list-files&udid={device.device_id}&path=%2Fsdcard"
            
            # 更新设备状态为使用中
            await db.execute(
                update(AppDevice)
                .where(AppDevice.id == int(device_id))
                .values(device_status=2)
            )
            
            # 创建使用日志
            log = AppDeviceLog(
                user_id=user_id,
                device_id=int(device_id),
                start_time=datetime.now()
            )
            db.add(log)
            await db.flush()
            
            await db.commit()
            
            return {
                "success": True,
                "device_url": device_url,
                "file_url": file_url,
                "log_id": log.id
            }
            
        except Exception as e:
            await db.rollback()
            print(f"获取设备控制权失败: {e}")
            return {"success": False, "message": str(e)}
    
    @staticmethod
    async def release_device(db: AsyncSession, device_id: str, log_id: str, user_id: int) -> bool:
        """释放设备"""
        try:
            # 更新设备状态为空闲
            await db.execute(
                update(AppDevice)
                .where(AppDevice.id == int(device_id))
                .values(device_status=1)
            )
            
            # 更新日志结束时间
            await db.execute(
                update(AppDeviceLog)
                .where(AppDeviceLog.id == int(log_id))
                .values(end_time=datetime.now())
            )
            
            await db.commit()
            return True
            
        except Exception as e:
            await db.rollback()
            print(f"释放设备失败: {e}")
            return False
    
    @staticmethod
    async def install_application(db: AsyncSession, device_id: str, apk_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """在设备上安装APP"""
        try:
            # 记录安装历史
            install_record = AppDeviceInstall(
                apk_name=apk_data["filename"],
                apk_path=apk_data["file_url"],
                device_id=int(apk_data["phone_id"]),
                user_id=user_id
            )
            db.add(install_record)
            
            # 执行安装
            install_result = await DeviceService._app_install(apk_data)
            
            await db.commit()
            
            if install_result[0]:
                return {"success": True, "message": "安装成功"}
            else:
                return {"success": False, "message": install_result[1]}
                
        except Exception as e:
            await db.rollback()
            print(f"安装APP失败: {e}")
            return {"success": False, "message": str(e)}
    
    @staticmethod
    async def uninstall_application(db: AsyncSession, device_id: str, package_name: str, user_id: int) -> Dict[str, Any]:
        """从设备上卸载APP"""
        try:
            uninstall_data = {
                "deviceid": device_id,
                "package": package_name
            }
            result = await DeviceService._uninstall_app(uninstall_data)
            
            if result[0]:
                return {"success": True, "message": "卸载成功"}
            else:
                return {"success": False, "message": result[1]}
                
        except Exception as e:
            print(f"卸载APP失败: {e}")
            return {"success": False, "message": str(e)}
    
    @staticmethod
    async def collect_performance_data(db: AsyncSession, device_id: str, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """收集设备性能数据"""
        try:
            return await DeviceService._get_performance(device_id, performance_data)
        except Exception as e:
            print(f"收集性能数据失败: {e}")
            return performance_data
    
    @staticmethod
    async def get_device_usage_log(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        """获取设备使用日志"""
        try:
            result = await db.execute(
                select(AppDeviceLog)
                .options(selectinload(AppDeviceLog.device))
                .where(AppDeviceLog.user_id == user_id)
                .order_by(AppDeviceLog.id.desc())
            )
            logs = result.scalars().all()
            
            log_list = []
            for log in logs:
                log_dict = {
                    "id": log.id,
                    "device_id": log.device_id,
                    "device_name": log.device.device_name if log.device else "",
                    "start_time": log.start_time.strftime("%Y-%m-%d %H:%M:%S") if log.start_time else "",
                    "end_time": log.end_time.strftime("%Y-%m-%d %H:%M:%S") if log.end_time else "",
                    "user_id": log.user_id
                }
                log_list.append(log_dict)
            
            return log_list
            
        except Exception as e:
            print(f"获取设备使用日志失败: {e}")
            return []
    
    @staticmethod
    async def get_install_history(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        """获取APP安装历史"""
        try:
            result = await db.execute(
                select(AppDeviceInstall)
                .options(selectinload(AppDeviceInstall.device))
                .where(AppDeviceInstall.user_id == user_id)
                .order_by(AppDeviceInstall.id.desc())
            )
            installs = result.scalars().all()
            
            install_list = []
            for install in installs:
                install_dict = {
                    "id": install.id,
                    "apk_name": install.apk_name,
                    "apk_path": install.apk_path,
                    "device_id": install.device_id,
                    "device_name": install.device.device_name if install.device else "",
                    "create_time": install.create_time.strftime("%Y-%m-%d %H:%M:%S") if install.create_time else "",
                    "user_id": install.user_id
                }
                install_list.append(install_dict)
            
            return install_list
            
        except Exception as e:
            print(f"获取安装历史失败: {e}")
            return []
    
    @staticmethod
    async def direct_install_app(db: AsyncSession, install_id: int, user_id: int) -> Dict[str, Any]:
        """直接安装APP（从历史记录）"""
        try:
            # 获取安装记录
            result = await db.execute(
                select(AppDeviceInstall).where(AppDeviceInstall.id == install_id)
            )
            install_record = result.scalar_one_or_none()
            
            if not install_record:
                return {"success": False, "message": "安装记录不存在"}
            
            # 构造安装数据
            install_data = {
                "file_url": install_record.apk_path,
                "device_id": str(install_record.device_id),
                "filename": install_record.apk_name
            }
            
            # 执行安装
            result = await DeviceService._app_install(install_data)
            
            if result[0]:
                return {"success": True, "message": result[1]}
            else:
                return {"success": False, "message": result[1]}
                
        except Exception as e:
            print(f"直接安装APP失败: {e}")
            return {"success": False, "message": str(e)}
    
    @staticmethod
    async def add_device(db: AsyncSession, device_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """添加设备"""
        try:
            # 创建设备记录
            device = AppDevice(
                device_name=device_data["device_name"],
                device_id=device_data["device_id"],
                device_type=device_data["device_type"],
                device_version=device_data.get("device_version", ""),
                device_info=device_data.get("device_info", {}),
                file_path=device_data["file_path"],
                device_description=device_data.get("device_description", ""),
                device_status=1,  # 默认空闲状态
                user_id=user_id
            )
            
            db.add(device)
            await db.commit()
            await db.refresh(device)
            
            return {
                "success": True,
                "message": "添加成功",
                "device_id": device.id
            }
            
        except Exception as e:
            await db.rollback()
            print(f"添加设备失败: {e}")
            return {"success": False, "message": str(e)}
    
    @staticmethod
    async def batch_install_apps(db: AsyncSession, install_config: List[Dict[str, Any]], user_id: int) -> Dict[str, Any]:
        """批量安装APP - 对应旧架构的device_install接口"""
        try:
            import multiprocessing
            from concurrent.futures import ProcessPoolExecutor
            
            # 构建安装任务列表
            install_tasks = []
            for config_group in install_config:
                path = config_group["path"]
                for device_config in config_group["config"]:
                    task_data = {
                        "path": path,
                        "deviceid": device_config["deviceid"],
                        "package": device_config["package"]
                    }
                    install_tasks.append(task_data)
            
            # 使用进程池执行批量安装
            with ProcessPoolExecutor() as executor:
                futures = [executor.submit(DeviceService._install_app_sync, task) for task in install_tasks]
                # 不等待结果，立即返回（异步执行）
            
            return {"success": True, "message": "启动app安装成功，等待安装中", "task_count": len(install_tasks)}
            
        except Exception as e:
            print(f"批量安装APP失败: {e}")
            return {"success": False, "message": str(e)}
    
    @staticmethod
    def _install_app_sync(data: Dict[str, Any]) -> bool:
        """同步安装APP方法，用于多进程调用"""
        try:
            import subprocess
            path = data["path"]
            device_id = data["deviceid"]
            package = data["package"]
            cmd = f"adb -s {device_id} install -r {path}/{package}"
            subprocess.check_output(cmd, shell=True)
            return True
        except Exception as e:
            print(f"安装APP失败: {e}")
            return False
    
    @staticmethod
    async def batch_uninstall_apps(db: AsyncSession, package_name: str, device_list: List[str], user_id: int) -> Dict[str, Any]:
        """批量卸载APP - 对应旧架构的device_uninstall接口"""
        try:
            import multiprocessing
            from concurrent.futures import ProcessPoolExecutor
            
            # 构建卸载任务列表
            uninstall_tasks = []
            for device_id in device_list:
                task_data = {
                    "deviceid": device_id,
                    "package": package_name
                }
                uninstall_tasks.append(task_data)
            
            # 使用进程池执行批量卸载
            with ProcessPoolExecutor() as executor:
                futures = [executor.submit(DeviceService._uninstall_app_sync, task) for task in uninstall_tasks]
                # 不等待结果，立即返回（异步执行）
            
            return {"success": True, "message": "启动app卸载成功，等待卸载中", "task_count": len(uninstall_tasks)}
            
        except Exception as e:
            print(f"批量卸载APP失败: {e}")
            return {"success": False, "message": str(e)}
    
    @staticmethod
    def _uninstall_app_sync(data: Dict[str, Any]) -> bool:
        """同步卸载APP方法，用于多进程调用"""
        try:
            import subprocess
            device_id = data["deviceid"]
            package = data["package"]
            cmd = f"adb -s {device_id} uninstall {package}"
            subprocess.check_output(cmd, shell=True)
            return True
        except Exception as e:
            print(f"卸载APP失败: {e}")
            return False
    
    @staticmethod
    async def edit_device(db: AsyncSession, device_id: int, device_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """编辑设备"""
        try:
            # 更新设备信息
            update_data = {}
            if "device_name" in device_data:
                update_data["device_name"] = device_data["device_name"]
            if "device_type" in device_data:
                update_data["device_type"] = device_data["device_type"]
            if "device_version" in device_data:
                update_data["device_version"] = device_data["device_version"]
            if "device_info" in device_data:
                update_data["device_info"] = device_data["device_info"]
            if "file_path" in device_data:
                update_data["file_path"] = device_data["file_path"]
            if "device_description" in device_data:
                update_data["device_description"] = device_data["device_description"]
            
            await db.execute(
                update(AppDevice)
                .where(AppDevice.id == device_id, AppDevice.user_id == user_id)
                .values(**update_data)
            )
            
            await db.commit()
            
            return {"success": True, "message": "编辑成功"}
            
        except Exception as e:
            await db.rollback()
            print(f"编辑设备失败: {e}")
            return {"success": False, "message": str(e)}
    
    # 私有方法 - 迁移自 l-tester/common/device.py
    
    @staticmethod
    async def _get_device_info():
        """获取设备信息 - 迁移自 device_info()"""
        try:
            device_info_list = []
            
            # iOS设备检测
            try:
                cmd = "tidevice list --json"
                ios_result = os.popen(cmd).read().replace("\\n", "").replace("\u001b[0m", "")
                if eval(ios_result):
                    for i in eval(ios_result):
                        name = i["market_name"] if i["market_name"] != "-" else i["name"]
                        ios = {
                            "deviceid": i["udid"],
                            "name": name,
                            "os_type": "ios",
                            "version": i["product_version"],
                        }
                        device_info_list.append(ios)
            except:
                pass
            
            # Android设备检测
            try:
                devices_output = subprocess.check_output("adb devices", shell=True).decode().strip()
                if devices_output != "List of devices attached":
                    devices_list = devices_output.split("\n")[1:]
                    for device in devices_list:
                        if device.strip():
                            device_id = device.split("\t")[0]
                            
                            # 获取设备属性
                            output = subprocess.check_output(f"adb -s {device_id} shell getprop", shell=True).decode()
                            
                            brand = await DeviceService._get_property(output, "ro.product.brand")
                            device_name, version = await DeviceService._get_device_name_and_version(output, brand)
                            wifi_ip = await DeviceService._get_wifi_ip(device_id)
                            
                            device_info_list.append({
                                "deviceid": device_id,
                                "name": device_name,
                                "os_type": "android",
                                "version": version,
                                "wifi_ip": wifi_ip,
                            })
            except Exception as e:
                print(f"Android设备检测失败: {e}")
            
            return True, device_info_list
            
        except Exception as e:
            print(f"获取设备信息失败: {e}")
            return False, str(e)
    
    @staticmethod
    async def _get_property(device_info_output, type_name):
        """获取设备属性"""
        for line in device_info_output.split("\n"):
            if line.startswith(f"[{type_name}]"):
                return line.split(":")[-1][2:-1]
        return ""
    
    @staticmethod
    async def _get_device_name_and_version(output, brand):
        """根据品牌获取设备名称和版本"""
        if brand == "OPPO":
            device_name = await DeviceService._get_property(output, "ro.oppo.market.name")
            if not device_name:
                device_name = await DeviceService._get_property(output, "ro.vendor.oplus.market.name")
            version = await DeviceService._get_property(output, "ro.product.build.version.release")
        elif brand == "HUAWEI":
            version = "Harmony OS " + await DeviceService._get_property(output, "hw_sc.build.platform.version")
            device_name = await DeviceService._get_property(output, "ro.config.marketing_name")
        elif brand == "Redmi":
            device_name = await DeviceService._get_property(output, "ro.product.marketname")
            version = await DeviceService._get_property(output, "ro.product.build.version.release")
        elif brand == "XIAOMI":
            device_name = await DeviceService._get_property(output, "ro.product.model")
            version = await DeviceService._get_property(output, "ro.product.build.version.release")
        elif brand == "OnePlus":
            device_name = await DeviceService._get_property(output, "ro.product.device")
            version = await DeviceService._get_property(output, "ro.product.build.version.release")
        elif brand == "google":
            device_name = await DeviceService._get_property(output, "ro.product.model")
            version = await DeviceService._get_property(output, "ro.product.build.version.release")
        elif brand == "HONOR":
            device_name = await DeviceService._get_property(output, "ro.config.marketing_name")
            version = await DeviceService._get_property(output, "ro.product.build.version.release")
        elif brand == "samsung":
            device_name = await DeviceService._get_property(output, "ro.product.model")
            version = await DeviceService._get_property(output, "ro.product.build.version.release")
        elif brand == "vivo":
            device_name = await DeviceService._get_property(output, "net.hostname")
            version = await DeviceService._get_property(output, "ro.build.version.release")
        else:
            device_name = await DeviceService._get_property(output, "ro.product.brand")
            version = "未知操作系统版本"
        
        return device_name, version
    
    @staticmethod
    async def _get_wifi_ip(device_id):
        """获取WiFi IP地址"""
        try:
            methods = [
                ("ip addr show wlan0", r"inet (\d+\.\d+\.\d+\.\d+)/"),
                ("ifconfig wlan0", r"inet addr:(\d+\.\d+\.\d+\.\d+)"),
                ("netcfg", r"wlan0\s+[^\s]+\s+[^\s]+\s+(\d+\.\d+\.\d+\.\d+)/"),
                ("dumpsys wifi", r"ipAddress=(\d+\.\d+\.\d+\.\d+)"),
            ]
            
            for cmd, pattern in methods:
                try:
                    result = subprocess.run(
                        ["adb", "-s", device_id, "shell", cmd],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.stdout.strip():
                        match = re.search(pattern, result.stdout.strip())
                        if match:
                            return match.group(1)
                except:
                    continue
            return None
        except Exception as e:
            return None
    
    @staticmethod
    async def _app_install(data):
        """安装APP"""
        try:
            path = data["file_url"]
            device_id = data["device_id"]
            package = data["filename"]
            cmd = f"adb -s {device_id} install -r .{path}/{package}"
            subprocess.check_output(cmd, shell=True)
            return True, "安装成功"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    async def _uninstall_app(data):
        """卸载APP"""
        try:
            device_id = data["deviceid"]
            package = data["package"]
            cmd = f"adb -s {device_id} uninstall {package}"
            subprocess.check_output(cmd, shell=True)
            return True, "卸载成功"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    async def _get_performance(device_id, device_performance):
        """获取性能数据"""
        try:
            memory = await DeviceService._get_memory(device_id)
            cpu = await DeviceService._get_cpu(device_id)
            temperature = await DeviceService._get_temperature(device_id)
            network = await DeviceService._get_network(device_id)
            now_time = await DeviceService._get_now()
            
            device_performance["time"].append(now_time)
            device_performance["memory"].append(memory)
            device_performance["cpu"].append(cpu)
            device_performance["temperature"].append(temperature)
            device_performance["up_network"].append(network[0])
            device_performance["down_network"].append(network[1])
            
            return device_performance
        except Exception as e:
            device_performance["time"].append(await DeviceService._get_now())
            device_performance["memory"].append(0)
            device_performance["cpu"].append(0)
            device_performance["temperature"].append(0)
            device_performance["up_network"].append(0)
            device_performance["down_network"].append(0)
            return device_performance
    
    @staticmethod
    async def _get_now():
        """获取当前时间"""
        now = datetime.now()
        return f"{now.minute}:{now.second}"
    
    @staticmethod
    async def _get_memory(device_id):
        """获取内存使用率"""
        try:
            cmd = f"adb -s {device_id} shell cat /proc/meminfo"
            result = os.popen(cmd).read().split()
            memory = (int(result[1]) - int(result[7])) / int(result[1]) * 100
            return round(memory, 2)
        except:
            return 0
    
    @staticmethod
    async def _get_cpu(device_id):
        """获取CPU使用率"""
        try:
            # 获取第一个时间点的CPU信息
            stat1 = await DeviceService._get_cpu_info(device_id)
            time.sleep(0.1)
            # 获取第二个时间点的CPU信息
            stat2 = await DeviceService._get_cpu_info(device_id)
            
            # 计算总的CPU时间
            total1 = sum([int(stat1[i]) for i in range(1, 8)])
            total2 = sum([int(stat2[i]) for i in range(1, 8)])
            
            # 计算空闲的CPU时间
            idle1 = int(stat1[4])
            idle2 = int(stat2[4])
            
            total = total2 - total1
            idle = idle2 - idle1
            
            # 计算CPU使用率
            cpu_usage = (total - idle) / total * 100
            return round(cpu_usage, 2)
        except:
            return 0
    
    @staticmethod
    async def _get_cpu_info(device_id):
        """获取CPU信息"""
        cmd = f"adb -s {device_id} shell cat /proc/stat"
        result = os.popen(cmd).read().split()
        return result
    
    @staticmethod
    async def _get_temperature(device_id):
        """获取设备温度"""
        try:
            command = f"adb -s {device_id} shell dumpsys battery"
            output = subprocess.check_output(command, shell=True).decode("utf-8")
            temperature_line = next(
                line for line in output.splitlines() if "temperature" in line
            )
            temperature_value = int(temperature_line.split(":")[1].strip()) / 10
            return temperature_value
        except:
            return 0
    
    @staticmethod
    async def _get_network(device_id):
        """获取网络速度"""
        try:
            # 获取第一次网络统计数据
            cmd = f"adb -s {device_id} shell cat /proc/net/dev"
            output1 = subprocess.check_output(cmd, shell=True).decode().strip()
            rx1 = tx1 = 0
            for line in output1.splitlines():
                if ":" in line and "lo:" not in line:
                    fields = line.split(":")[1].strip().split()
                    rx1 += int(fields[0])
                    tx1 += int(fields[8])
            
            time.sleep(1)
            
            # 获取第二次网络统计数据
            output2 = subprocess.check_output(cmd, shell=True).decode().strip()
            rx2 = tx2 = 0
            for line in output2.splitlines():
                if ":" in line and "lo:" not in line:
                    fields = line.split(":")[1].strip().split()
                    rx2 += int(fields[0])
                    tx2 += int(fields[8])
            
            # 计算速度
            download_speed = (rx2 - rx1) * 8 / 1024 / 1024
            upload_speed = (tx2 - tx1) * 8 / 1024
            
            return round(upload_speed, 2), round(download_speed, 2)
        except Exception as e:
            return 0, 0