"""
云真机模块 - 控制器
处理设备管理、远程控制、APP安装等相关API请求
迁移自 l-tester/views/app/device_view.py
"""
import os
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sqlalchemy import get_db
from app.core.dependencies import get_current_user_id
from app.common.response import success_response, error_response
from app.utils.common import body_to_json

from .service import DeviceService

router = APIRouter()


@router.post("/device_install")
async def device_install(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """批量安装APP"""
    try:
        data = await body_to_json(request)
        result = await DeviceService.batch_install_apps(db, data["config"], current_user_id)
        
        if result["success"]:
            return success_response({}, message=result["message"])
        else:
            return error_response(result["message"])
    except Exception as e:
        return error_response(str(e))


@router.post("/device_list")
async def device_list(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取设备列表"""
    try:
        devices = await DeviceService.list_devices(db, current_user_id)
        return success_response(devices)
    except Exception as e:
        return error_response(str(e))


@router.post("/sync_stf_devices")
async def sync_stf_devices(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """从 STF 设备池同步设备到本地库"""
    try:
        result = await DeviceService.sync_stf_devices(db, current_user_id)
        if result.get("success"):
            return success_response(result, message=result.get("message") or "同步成功")
        return error_response(result.get("message") or "同步失败")
    except Exception as e:
        return error_response(str(e))


@router.post("/device_info_list")
async def device_info_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取设备详细信息"""
    try:
        body = await body_to_json(request)
        # 对齐旧架构：支持 search + currentPage/pageSize 的分页结构
        page = int((body or {}).get("currentPage") or 1)
        page_size = int((body or {}).get("pageSize") or 24)
        search = (body or {}).get("search") or {}

        data = await DeviceService.get_device_details_paged(
            db=db,
            user_id=current_user_id,
            page=page,
            page_size=page_size,
            search=search,
        )
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@router.post("/use_device")
async def use_device(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """使用设备（获取远程控制链接）"""
    try:
        data = await body_to_json(request)
        result = await DeviceService.acquire_device(db, data["id"], current_user_id)
        
        if result["success"]:
            return success_response({
                "device_url": result["device_url"],
                "file_url": result["file_url"],
                "log_id": result["log_id"]
            })
        else:
            return error_response(result["message"])
    except Exception as e:
        return error_response(str(e))


@router.post("/app_view_device")
async def app_view_device(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """APP查看设备"""
    try:
        data = await body_to_json(request)
        from config import config
        device_url = f"{config.DEVICE_URL}/#!action=stream&udid={data['device_id']}&player=mse&ws=ws%3A%2F%2F{config.IP}%3A8000%2F%3Faction%3Dproxy-adb%26remote%3Dtcp%253A8886%26udid%3D{data['device_id']}"
        return success_response({"device_url": device_url})
    except Exception as e:
        return error_response(str(e))


@router.post("/stop_device")
async def stop_device(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """释放设备"""
    try:
        data = await body_to_json(request)
        result = await DeviceService.release_device(db, data["id"], data["log_id"], current_user_id)
        
        if result:
            return success_response({})
        else:
            return error_response("释放设备失败")
    except Exception as e:
        return error_response(str(e))


@router.post("/device_install_app")
async def device_install_app(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """安装APP"""
    try:
        data = await body_to_json(request)
        result = await DeviceService.install_application(db, data["phone_id"], data, current_user_id)
        
        if result["success"]:
            return success_response({})
        else:
            return error_response(result["message"])
    except Exception as e:
        return error_response(str(e))


@router.post("/direct_install_app")
async def direct_install_app(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """直接安装APP（从历史记录）"""
    try:
        data = await body_to_json(request)
        result = await DeviceService.direct_install_app(db, data["id"], current_user_id)
        
        if result["success"]:
            return success_response({"message": result["message"]})
        else:
            return error_response(result["message"])
    except Exception as e:
        return error_response(str(e))


@router.post("/device_uninstall")
async def device_uninstall(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """批量卸载APP"""
    try:
        data = await body_to_json(request)
        result = await DeviceService.batch_uninstall_apps(db, data["package"], data["device_list"], current_user_id)
        
        if result["success"]:
            return success_response({}, message=result["message"])
        else:
            return error_response(result["message"])
    except Exception as e:
        return error_response(str(e))


@router.post("/device_performance")
async def device_performance(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取设备性能数据"""
    try:
        data = await body_to_json(request)
        performance_data = await DeviceService.collect_performance_data(db, data["device_id"], data["performance"])
        return success_response(performance_data)
    except Exception as e:
        return error_response(str(e))


@router.post("/get_device_log")
async def get_device_log(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取设备使用日志"""
    try:
        logs = await DeviceService.get_device_usage_log(db, current_user_id)
        data = {
            "content": logs,
            "total": len(logs),
            "page": 1,
            "size": len(logs)
        }
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@router.post("/get_history_list")
async def get_history_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取APP安装历史"""
    try:
        history = await DeviceService.get_install_history(db, current_user_id)
        data = {
            "content": history,
            "total": len(history),
            "page": 1,
            "size": len(history)
        }
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@router.post("/package_list")
async def package_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取包列表"""
    try:
        data = await body_to_json(request)
        folder_path = data["folder_path"]
        n = 0
        result = []
        
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                n = n + 1
                sdk_dict = {"id": n, "file_name": filename}
                result.append(sdk_dict)
        
        return success_response(result)
    except Exception as e:
        return error_response(str(e))


@router.post("/add_device")
async def add_device(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """添加设备"""
    try:
        data = await body_to_json(request)
        result = await DeviceService.add_device(db, data, current_user_id)
        
        if result["success"]:
            return success_response({"device_id": result["device_id"]}, message=result["message"])
        else:
            return error_response(result["message"])
    except Exception as e:
        return error_response(str(e))


@router.post("/edit_device")
async def edit_device(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """编辑设备"""
    try:
        data = await body_to_json(request)
        device_id = data.pop("id")  # 从数据中取出设备ID
        result = await DeviceService.edit_device(db, device_id, data, current_user_id)
        
        if result["success"]:
            return success_response({}, message=result["message"])
        else:
            return error_response(result["message"])
    except Exception as e:
        return error_response(str(e))