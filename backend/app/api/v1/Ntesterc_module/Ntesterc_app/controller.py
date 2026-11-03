#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort
from typing import Optional

from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import psutil
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.common.response import success_response, error_response
from app.utils.common import body_to_json
from app.api.v1.system.file.service import FileService
from app.core.logger import logger

from .service import AppManagementService
from .model import AppResultModel
from .device_service import AppDeviceCenterService
from .device_schema import (
    PhoneAddBody,
    PhoneIdBody,
    PhoneListBody,
    PhoneSortBody,
    PhoneUpdateBody,
    ServerAddBody,
    ServerIdBody,
    ServerListBody,
    ServerSortBody,
    ServerUpdateBody,
)
from .page_schema import (
    ElementAddBody,
    ElementIdBody,
    ElementImportBody,
    ElementListBody,
    ElementSortBody,
    ElementUpdateBody,
    PageAddBody,
    PageIdBody,
    PageListBody,
    PageSortBody,
    PageUpdateBody,
)
from .page_service import AppPageService

router = APIRouter()


@router.post("/app_menu")
async def get_app_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取APP脚本菜单树"""
    try:
        data = await AppManagementService.get_app_menu(db, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(str(e))
@router.post("/recover_root_menu")
async def recover_root_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """恢复被软删除的根目录"""
    try:
        result = await AppManagementService.recover_root_menu(db, current_user_id)
        return success_response(result, message=result["message"])
    except Exception as e:
        logger.error(f"恢复根目录失败: {e}")
        return error_response(message="恢复根目录失败")


@router.post("/get_app_script")
async def get_app_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取APP脚本内容"""
    try:
        body = await body_to_json(request)
        data = await AppManagementService.get_app_script(db, int(body["id"]), current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/save_app_script")
async def save_app_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """保存APP脚本"""
    try:
        body = await body_to_json(request)
        await AppManagementService.save_app_script(db, body, current_user_id)
        return success_response({}, message="保存成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/run_app_script")
async def run_app_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """执行单个APP脚本"""
    try:
        body = await body_to_json(request)
        data = await AppManagementService.execute_app_script(db, body, "", current_user_id)
        return success_response(data, message="启动成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/run_script_list")
async def run_script_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """执行APP脚本集"""
    try:
        body = await body_to_json(request)
        script_items = sorted(body.get("script_list") or [], key=lambda x: int(x.get("step") or 0))
        data = await AppManagementService.execute_script_list(
            db,
            script_ids=[int(x.get("id")) for x in script_items if x.get("id") is not None],
            device_list=[
                {
                    "deviceid": str(x.get("deviceid")) if x.get("deviceid") is not None else "",
                    "name": str(x.get("name") or x.get("device_name") or x.get("deviceid") or ""),
                    "package": x.get("package") or "",
                    "os_type": str(x.get("os_type") or "android"),
                    "path": str(x.get("path") or ""),
                }
                for x in (body.get("device_list") or [])
                if x.get("deviceid")
            ],
            user_id=current_user_id,
            run_options={
                "run_type": body.get("run_type"),
                "version": body.get("version"),
                "channel_id": body.get("channel_id"),
                "task_name": body.get("task_name"),
                "result_id": body.get("result_id"),
                "script_items": script_items,
            },
        )
        return success_response(data, message="启动成功")
    except Exception as e:
        return error_response(str(e))

@router.post("/menu_script_list")
async def menu_script_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取 pid 下脚本列表"""
    try:
        body = await body_to_json(request)
        data = await AppManagementService.menu_script_list(db, int(body["id"]), current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/get_script_list")
async def get_script_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取所有 type=2 的脚本菜单"""
    try:
        data = await AppManagementService.get_script_list(db, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/view_script_list")
async def view_script_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """查看脚本内容"""
    try:
        body = await body_to_json(request)
        data = await AppManagementService.view_script_list(db, int(body["menu_id"]), current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/app_correction")
async def app_correction(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """错误修正"""
    try:
        body = await body_to_json(request)
        await AppManagementService.app_correction(db, str(body["result_id"]), str(body["device"]), current_user_id)
        return success_response({}, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/app_menu_select")
async def app_menu_select(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """菜单选择器（type=1）"""
    try:
        data = await AppManagementService.app_menu_select(db, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/get_process")
async def get_process(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """检查进程状态"""
    try:
        body = await body_to_json(request)
        data = await AppManagementService.get_process(db, body.get("device_list") or [])
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/get_app_result_detail")
async def get_app_result_detail(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取结果汇总详情"""
    try:
        body = await body_to_json(request)
        data = await AppManagementService.get_app_result_detail(db, str(body["result_id"]), current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/get_result_detail")
async def get_result_detail(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """单设备执行汇总（script_total/script_pass/...）"""
    try:
        body = await body_to_json(request)
        data = await AppManagementService.get_result_detail(
            db, str(body["result_id"]), str(body["device"]), current_user_id
        )
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/get_result_list")
async def get_result_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取单设备执行详情列表"""
    try:
        body = await body_to_json(request)
        # 有时仅传 result_id/device，不传 menu_id
        if body.get("menu_id") is None:
            result = await db.execute(
                select(AppResultModel)
                .where(
                    AppResultModel.result_id == str(body["result_id"]),
                    AppResultModel.device == str(body["device"]),
                    AppResultModel.user_id == current_user_id,
                    AppResultModel.enabled_flag == 1,
                )
                .order_by(AppResultModel.id.desc())
            )
            rows = result.scalars().all()
            data = [
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
        else:
            data = await AppManagementService.get_result_list(
                db=db,
                result_id=str(body["result_id"]),
                menu_id=int(body["menu_id"]),
                device=str(body["device"]),
                user_id=current_user_id,
            )
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/img_list")
async def img_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """图像库列表"""
    try:
        body = await body_to_json(request)
        page = int((body or {}).get("currentPage") or 1)
        page_size = int((body or {}).get("pageSize") or 10)
        search = (body or {}).get("search") or {}
        data = await AppManagementService.img_list(db, page, page_size, search, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/img_select")
async def img_select(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """图像级联选择"""
    try:
        data = await AppManagementService.img_select(db, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/add_img")
async def add_img(
    request: Request,
    file: UploadFile = File(...),
    # 必须从 multipart 表单读取，否则前端 FormData 里的 menu_id 不会绑定，列表按 menu_id 筛选会查不到
    menu_id: Optional[int] = Form(default=None),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """上传图片并写入 APP 图像库（优先落到 static）"""
    try:
        base_url = str(request.base_url)
        upload_res = await FileService.upload_file_service(
            file=file,
            current_user_id=current_user_id,
            description=None,
            tags=None,
            is_public=1,
            request_base_url=base_url,
            store_in_database=False,  # 强制落盘，返回 /static/... 形式 URL
            db=db,
        )
        mid = int(menu_id) if menu_id is not None else None
        if not mid:
            return error_response("请选择所属项目后再上传（图像按项目隔离）")
        if not await AppManagementService._menu_owned_by_user(db, mid, current_user_id):
            return error_response("项目不存在或无权向该项目上传")
        data = await AppManagementService.add_img(
            db,
            file_name=upload_res.original_name or upload_res.file_name,
            file_path=upload_res.file_url,
            menu_id=mid,
            user_id=current_user_id,
        )
        return success_response(data, message="上传成功")
    except Exception as e:
        return error_response(str(e))

@router.post("/delete_img")
async def delete_img(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除图片"""
    try:
        body = await body_to_json(request)
        await AppManagementService.delete_img(db, int(body["id"]), current_user_id)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/edit_img")
async def edit_img(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """编辑图片"""
    try:
        body = await body_to_json(request)
        await AppManagementService.edit_img(
            db, int(body["id"]), str(body["file_name"]), str(body["file_path"]), current_user_id
        )
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/add_menu")
async def add_app_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """新增APP菜单"""
    try:
        body = await body_to_json(request)
        data = await AppManagementService.add_app_menu(db, body, current_user_id)
        return success_response(data, message="添加成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/del_menu")
async def delete_app_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除APP菜单"""
    try:
        body = await body_to_json(request)
        menu_id = int(body["id"])
        logger.info(f"尝试删除菜单 ID: {menu_id}, 用户ID: {current_user_id}")
        
        ok = await AppManagementService.delete_app_menu(db, menu_id, current_user_id)
        
        if ok:
            logger.info(f"菜单 {menu_id} 删除成功")
            return success_response({}, message="删除成功")
        else:
            logger.warning(f"菜单 {menu_id} 删除失败 - 可能不存在或有其他问题")
            return error_response("删除失败")
    except ValueError as e:
        logger.error(f"删除菜单失败 - 值错误: {e}")
        return error_response(str(e))
    except Exception as e:
        logger.error(f"删除菜单失败 - 未知错误: {e}")
        return error_response(f"删除失败: {str(e)}")


@router.post("/rename_menu")
async def rename_app_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """重命名APP菜单"""
    try:
        body = await body_to_json(request)
        await AppManagementService.rename_app_menu(db, int(body["id"]), str(body["name"]), current_user_id)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/get_app_result")
async def get_app_result(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取APP执行结果：传 device 时对齐返回步骤列表，否则返回任务汇总对象"""
    try:
        body = await body_to_json(request)
        if body.get("device") is not None:
            await AppManagementService.send_app_warn(db, str(body["result_id"]), current_user_id)
            data = await AppManagementService.get_app_result_steps_for_device(
                db, str(body["result_id"]), str(body["device"]), current_user_id
            )
        else:
            data = await AppManagementService.get_app_result(db, str(body["result_id"]), current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/send_app_warn")
async def send_app_warn_api(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """单独触发失败告警（轮询场景）；平时由 get_app_result 带 device 时自动调用"""
    try:
        body = await body_to_json(request)
        await AppManagementService.send_app_warn(db, str(body["result_id"]), current_user_id)
        return success_response({}, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/app_result_list")
async def get_app_result_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取APP结果列表"""
    try:
        body = await body_to_json(request)
        page = int((body or {}).get("currentPage") or 1)
        page_size = int((body or {}).get("pageSize") or 10)

        search = (body or {}).get("search") or {}
        search_task_name = str(search.get("task_name__icontaints") or "").strip()
        rows = await AppManagementService.get_app_result_list(db, current_user_id, search_task_name)
        total = len(rows)
        start = max(0, (page - 1) * page_size)
        end = start + page_size
        content = rows[start:end]

        return success_response(
            {"content": content, "total": total, "currentPage": page, "pageSize": page_size},
            message="请求成功",
        )
    except Exception as e:
        return error_response(str(e))


@router.post("/pause_process")
async def pause_app_process(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """暂停子进程（仅 POSIX 有效）"""
    try:
        body = await body_to_json(request)
        pid = int(body.get("pid") or 0)
        if AppManagementService.pause_app_worker(pid):
            return success_response({}, message="请求成功")
        return error_response("当前环境不支持暂停（或非 POSIX 系统）")
    except Exception as e:
        return error_response(str(e))


@router.post("/resume_process")
async def resume_app_process(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """恢复子进程（仅 POSIX 有效）"""
    try:
        body = await body_to_json(request)
        pid = int(body.get("pid") or 0)
        if AppManagementService.resume_app_worker(pid):
            return success_response({}, message="请求成功")
        return error_response("当前环境不支持恢复（或非 POSIX 系统）")
    except Exception as e:
        return error_response(str(e))


@router.post("/stop_process")
async def stop_app_process(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """停止APP执行"""
    try:
        body = await body_to_json(request)
        # 如果传 pid/deviceid/result_id
        if body.get("pid") is not None and body.get("deviceid") is not None:
            ok = await AppManagementService.stop_app_process(
                db,
                str(body["result_id"]),
                current_user_id,
                pid=int(body["pid"]),
                deviceid=str(body["deviceid"]),
            )
            if ok:
                return success_response({}, message="执行结束")
            return error_response("停止失败")

        ok = await AppManagementService.stop_app_process(db, str(body["result_id"]), current_user_id)
        if ok:
            return success_response({}, message="停止成功")
        return error_response("停止失败")
    except Exception as e:
        return error_response(str(e))


@router.post("/del_app_result")
async def del_app_result(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除 APP 执行记录（执行中会先停止进程）"""
    try:
        body = await body_to_json(request)
        result_id = str(body.get("result_id") or "")
        if not result_id:
            return error_response("缺少 result_id")
        data = await AppManagementService.delete_app_result(db, result_id, current_user_id)
        if not data.get("deleted"):
            return error_response(data.get("message") or "删除失败")
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/pid_status")
async def get_process_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """查询APP进程状态"""
    try:
        body = await body_to_json(request)
        # 前端只依赖 res.message（"正在执行"/"执行结束"）
        if body.get("pid") is not None:
            pid = int(body.get("pid"))
            try:
                if psutil.pid_exists(pid):
                    return success_response({}, message="正在执行")
            except Exception:
                # ignore psutil errors
                pass
            # 进程已结束：释放设备
            try:
                mapping = (AppManagementService._pid_index or {}).get(pid)
                if mapping and mapping.get("result_id"):
                    await AppManagementService.stop_app_process(
                        db,
                        str(mapping.get("result_id")),
                        current_user_id,
                        pid=pid,
                    )
            except Exception:
                # 即使释放失败，也不影响返回“执行结束”
                pass
            return success_response({}, message="执行结束")

        data = await AppManagementService.get_process_status(db, str(body.get("result_id") or ""), current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(str(e))


# ----- APP 设备中心（Appium 服务器 / 运行终端，对齐 ntest 设备模块） -----


@router.post("/device/server/list")
async def device_server_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        form = ServerListBody.model_validate(body or {})
        srv_os = form.os or form.server_os
        total, rows = await AppDeviceCenterService.server_list(
            db,
            current_user_id,
            form.currentPage,
            form.pageSize,
            form.name,
            srv_os,
            form.ip,
            form.port,
        )
        return success_response({"total": total, "data": rows}, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/device/server/detail")
async def device_server_detail(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        sid = ServerIdBody.model_validate(body or {}).id
        row = await AppDeviceCenterService.server_get(db, current_user_id, sid)
        return success_response(
            {
                "id": row.id,
                "name": row.name,
                "num": row.num,
                "os": row.server_os,
                "server_os": row.server_os,
                "ip": row.ip,
                "port": row.port,
                "appium_version": row.appium_version,
                "status": row.status,
            },
            message="请求成功",
        )
    except Exception as e:
        return error_response(str(e))


@router.post("/device/server/add")
async def device_server_add(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        form = ServerAddBody.model_validate(body or {})
        await AppDeviceCenterService.server_add(
            db, current_user_id, [x.model_dump() for x in form.data_list]
        )
        return success_response({}, message="新增成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/device/server/update")
async def device_server_update(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        form = ServerUpdateBody.model_validate(body or {})
        await AppDeviceCenterService.server_update(
            db, current_user_id, form.id, form.model_dump(exclude={"id"})
        )
        return success_response({}, message="更新成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/device/server/delete")
async def device_server_delete(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        sid = ServerIdBody.model_validate(body or {}).id
        await AppDeviceCenterService.server_delete(db, current_user_id, sid)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/device/server/copy")
async def device_server_copy(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        sid = ServerIdBody.model_validate(body or {}).id
        data = await AppDeviceCenterService.server_copy(db, current_user_id, sid)
        return success_response(data, message="复制成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/device/server/sort")
async def device_server_sort(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        form = ServerSortBody.model_validate(body or {})
        await AppDeviceCenterService.server_sort(db, current_user_id, form.id_list)
        return success_response({}, message="排序已保存")
    except Exception as e:
        return error_response(str(e))


@router.post("/device/server/run")
async def device_server_run(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        sid = ServerIdBody.model_validate(body or {}).id
        msg = await AppDeviceCenterService.server_run_check(db, current_user_id, sid)
        return success_response({}, message=msg)
    except Exception as e:
        return error_response(str(e))


@router.post("/device/phone/list")
async def device_phone_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        form = PhoneListBody.model_validate(body or {})
        ph_os = form.os or form.phone_os
        total, rows = await AppDeviceCenterService.phone_list(
            db,
            current_user_id,
            form.currentPage,
            form.pageSize,
            form.name,
            ph_os,
            form.os_version,
        )
        return success_response({"total": total, "data": rows}, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/device/phone/detail")
async def device_phone_detail(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        pid = PhoneIdBody.model_validate(body or {}).id
        row = await AppDeviceCenterService.phone_get(db, current_user_id, pid)
        return success_response(
            {
                "id": row.id,
                "name": row.name,
                "num": row.num,
                "os": row.phone_os,
                "phone_os": row.phone_os,
                "os_version": row.os_version,
                "device_id": row.device_id,
                "extends": row.extends or {},
                "screen": row.screen,
            },
            message="请求成功",
        )
    except Exception as e:
        return error_response(str(e))


@router.post("/device/phone/add")
async def device_phone_add(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        form = PhoneAddBody.model_validate(body or {})
        await AppDeviceCenterService.phone_add(
            db, current_user_id, [x.model_dump() for x in form.data_list]
        )
        return success_response({}, message="新增成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/device/phone/update")
async def device_phone_update(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        form = PhoneUpdateBody.model_validate(body or {})
        await AppDeviceCenterService.phone_update(
            db, current_user_id, form.id, form.model_dump(exclude={"id"})
        )
        return success_response({}, message="更新成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/device/phone/delete")
async def device_phone_delete(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        pid = PhoneIdBody.model_validate(body or {}).id
        await AppDeviceCenterService.phone_delete(db, current_user_id, pid)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/device/phone/copy")
async def device_phone_copy(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        pid = PhoneIdBody.model_validate(body or {}).id
        data = await AppDeviceCenterService.phone_copy(db, current_user_id, pid)
        return success_response(data, message="复制成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/device/phone/sort")
async def device_phone_sort(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        form = PhoneSortBody.model_validate(body or {})
        await AppDeviceCenterService.phone_sort(db, current_user_id, form.id_list)
        return success_response({}, message="排序已保存")
    except Exception as e:
        return error_response(str(e))


# ----- APP 页面 / 元素（对齐 ntest 页面管理） -----


@router.post("/page/list")
async def app_page_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        form = PageListBody.model_validate(body or {})
        total, rows = await AppPageService.page_list(
            db,
            current_user_id,
            form.module_menu_id,
            form.currentPage,
            form.pageSize,
        )
        return success_response({"total": total, "data": rows}, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/page/add")
async def app_page_add(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        form = PageAddBody.model_validate(body or {})
        data = await AppPageService.page_add(db, current_user_id, form.model_dump())
        return success_response(data, message="新增成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/page/update")
async def app_page_update(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        form = PageUpdateBody.model_validate(body or {})
        data = await AppPageService.page_update(db, current_user_id, form.model_dump())
        return success_response(data, message="保存成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/page/delete")
async def app_page_delete(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        pid = PageIdBody.model_validate(body or {}).id
        await AppPageService.page_delete(db, current_user_id, pid)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/page/sort")
async def app_page_sort(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        form = PageSortBody.model_validate(body or {})
        await AppPageService.page_sort(db, current_user_id, form.id_list)
        return success_response({}, message="排序已保存")
    except Exception as e:
        return error_response(str(e))


@router.post("/page/copy")
async def app_page_copy(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        pid = PageIdBody.model_validate(body or {}).id
        data = await AppPageService.page_copy(db, current_user_id, pid)
        return success_response(data, message="复制成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/page/element/list")
async def app_page_element_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        page_id = ElementListBody.model_validate(body or {}).page_id
        rows = await AppPageService.element_list(db, current_user_id, page_id)
        return success_response(rows, message="请求成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/page/element/add")
async def app_page_element_add(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        form = ElementAddBody.model_validate(body or {})
        data = await AppPageService.element_add(db, current_user_id, form.model_dump())
        return success_response(data, message="新增成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/page/element/update")
async def app_page_element_update(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        form = ElementUpdateBody.model_validate(body or {})
        data = await AppPageService.element_update(db, current_user_id, form.model_dump())
        return success_response(data, message="保存成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/page/element/delete")
async def app_page_element_delete(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        eid = ElementIdBody.model_validate(body or {}).id
        await AppPageService.element_delete(db, current_user_id, eid)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(str(e))


@router.post("/page/element/sort")
async def app_page_element_sort(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        form = ElementSortBody.model_validate(body or {})
        await AppPageService.element_sort(db, current_user_id, form.id_list)
        return success_response({}, message="排序已保存")
    except Exception as e:
        return error_response(str(e))


@router.post("/page/element/import")
async def app_page_element_import(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        form = ElementImportBody.model_validate(body or {})
        n = await AppPageService.element_import_bulk(
            db,
            current_user_id,
            form.page_id,
            [e.model_dump() for e in form.elements],
        )
        return success_response({"imported": n}, message=f"已导入 {n} 条元素")
    except Exception as e:
        return error_response(str(e))