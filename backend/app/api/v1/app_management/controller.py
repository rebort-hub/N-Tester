"""
APP管理模块 - 控制器
处理APP自动化测试、脚本管理、执行监控等相关API请求
"""
from typing import Optional

from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import psutil
from app.db.sqlalchemy import get_db
from app.core.dependencies import get_current_user_id
from app.common.response import success_response, error_response
from app.utils.common import body_to_json
from app.api.v1.system.file.service import FileService

from .service import AppManagementService
from .model import AppResultModel

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
    """对齐旧：获取 pid 下脚本列表"""
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
    """对齐旧：获取所有 type=2 的脚本菜单"""
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
    """对齐旧：查看脚本内容"""
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
    """对齐旧：错误修正"""
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
    """对齐旧：菜单选择器（type=1）"""
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
    """对齐旧：检查进程状态"""
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
    """对齐旧：获取结果汇总详情"""
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
    """对齐旧：单设备执行汇总（script_total/script_pass/...）"""
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
    """对齐旧：获取单设备执行详情列表"""
    try:
        body = await body_to_json(request)
        # 兼容旧前端：有时仅传 result_id/device，不传 menu_id
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
    """对齐旧：图像库列表"""
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
    """对齐旧：图像级联选择"""
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
    """对齐旧：删除图片"""
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
    """对齐旧：编辑图片"""
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
        ok = await AppManagementService.delete_app_menu(db, int(body["id"]), current_user_id)
        if ok:
            return success_response({}, message="删除成功")
        return error_response("目录下存在子节点，无法删除")
    except Exception as e:
        return error_response(str(e))


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
    """获取APP执行结果：传 device 时对齐旧版返回步骤列表，否则返回任务汇总对象"""
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
    """对齐旧：单独触发失败告警（轮询场景）；平时由 get_app_result 带 device 时自动调用"""
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
    """对齐旧：暂停子进程（仅 POSIX 有效）"""
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
    """对齐旧：恢复子进程（仅 POSIX 有效）"""
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
        # 对齐旧：如果传 pid/deviceid/result_id，则以旧协议处理（目前仅释放设备并返回执行结束）
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


@router.post("/pid_status")
async def get_process_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """查询APP进程状态"""
    try:
        body = await body_to_json(request)
        # 对齐旧：前端只依赖 res.message（"正在执行"/"执行结束"）
        if body.get("pid") is not None:
            pid = int(body.get("pid"))
            try:
                if psutil.pid_exists(pid):
                    return success_response({}, message="正在执行")
            except Exception:
                # ignore psutil errors
                pass
            # 进程已结束：释放设备（对齐旧架构：执行结束自动置空闲）
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