"""
Web管理模块 - 控制器
处理Web UI自动化测试、元素管理、脚本集管理等相关API请求

说明：
- 这里优先完成 L-Tester 旧架构中 web 元素管理相关接口的一比一迁移
- 与新架构其他 UI 自动化模块保持解耦，作为独立 WebUI 自动化子模块
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.sqlalchemy import get_db
from app.core.dependencies import get_current_user_id
from app.common.enums import ResponseCode
from app.common.response import success_response, error_response
from app.utils.common import body_to_json

from .service import WebManagementService

router = APIRouter()


# -------------------- 元素菜单 & 元素管理（迁移自 l-tester/views/web/element_view.py） --------------------

@router.post("/web_element/element_tree")
async def element_tree(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取元素菜单树（对齐旧 /api/web_element/element_tree）"""
    try:
        data = await WebManagementService.get_element_tree(db, only_menu=True)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web_element/add_menu")
async def add_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增元素菜单（对齐旧 /api/web_element/add_menu）"""
    try:
        body = await body_to_json(request)
        await WebManagementService.add_menu(
            db,
            name=str(body["name"]),
            pid=int(body["pid"]),
            type=int(body["type"]),
            user_id=current_user_id,
        )
        await db.commit()
        return success_response({}, message="添加成功")
    except Exception as e:
        await db.rollback()
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web_element/edit_menu")
async def edit_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """编辑元素菜单（对齐旧 /api/web_element/edit_menu）"""
    try:
        body = await body_to_json(request)
        await WebManagementService.edit_menu(
            db,
            menu_id=int(body["id"]),
            name=str(body["name"]),
            user_id=current_user_id,
        )
        await db.commit()
        return success_response({}, message="编辑成功")
    except Exception as e:
        await db.rollback()
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web_element/del_menu")
async def del_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除元素菜单（对齐旧 /api/web_element/del_menu）"""
    try:
        body = await body_to_json(request)
        await WebManagementService.delete_menu(db, menu_id=int(body["id"]))
        await db.commit()
        return success_response({}, message="删除成功")
    except Exception as e:
        await db.rollback()
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web_element/get_element_list")
async def get_element_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取元素列表（对齐旧 /api/web_element/get_element_list）"""
    try:
        body = await body_to_json(request)
        page = int(body.get("page") or 1)
        page_size = int(body.get("pageSize") or 10)
        data = await WebManagementService.get_element_list(
            db,
            page=page,
            page_size=page_size,
            user_id=current_user_id,
        )
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web_element/add_element")
async def add_element(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增元素（对齐旧 /api/web_element/add_element）"""
    try:
        body = await body_to_json(request)
        await WebManagementService.add_element(
            db,
            name=str(body["name"]),
            element=body["element"],
            menu_id=int(body["menu_id"]),
            user_id=current_user_id,
        )
        await db.commit()
        return success_response({}, message="添加成功")
    except Exception as e:
        await db.rollback()
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web_element/edit_element")
async def edit_element(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """编辑元素（对齐旧 /api/web_element/edit_element）"""
    try:
        body = await body_to_json(request)
        await WebManagementService.edit_element(
            db,
            element_id=int(body["id"]),
            name=str(body["name"]),
            element=body["element"],
            user_id=current_user_id,
        )
        await db.commit()
        return success_response({}, message="编辑成功")
    except Exception as e:
        await db.rollback()
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web_element/del_element")
async def del_element(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除元素（对齐旧 /api/web_element/del_element）"""
    try:
        body = await body_to_json(request)
        await WebManagementService.delete_element(db, element_id=int(body["id"]))
        await db.commit()
        return success_response({}, message="删除成功")
    except Exception as e:
        await db.rollback()
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web_element/get_element_select")
async def get_element_select(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取元素选择树（对齐旧 /api/web_element/get_element_select）"""
    try:
        data = await WebManagementService.get_element_tree(db, only_menu=False)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


# -------------------- Web 脚本 & 菜单（迁移自 l-tester/views/web/web_view.py） --------------------

@router.post("/web/add_menu")
async def add_web_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增 Web 脚本菜单（对齐旧 /api/web/add_menu）"""
    try:
        body = await body_to_json(request)
        data = await WebManagementService.create_web_menu(
            db,
            name=str(body["name"]),
            pid=int(body["pid"]),
            type=int(body["type"]),
            user_id=current_user_id,
        )
        await db.commit()
        return success_response(data, message="添加成功")
    except Exception as e:
        await db.rollback()
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/del_menu")
async def delete_web_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除 Web 脚本菜单（对齐旧 /api/web/del_menu）"""
    try:
        body = await body_to_json(request)
        ok, msg = await WebManagementService.delete_web_menu(
            db,
            menu_id=int(body["id"]),
            type=int(body.get("type") or 0),
        )
        if not ok:
            await db.rollback()
            return error_response(msg)
        await db.commit()
        return success_response({}, message=msg)
    except Exception as e:
        await db.rollback()
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/rename_menu")
async def rename_web_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """重命名 Web 脚本菜单（对齐旧 /api/web/rename_menu）"""
    try:
        body = await body_to_json(request)
        await WebManagementService.rename_web_menu(
            db,
            menu_id=int(body["id"]),
            name=str(body["name"]),
            user_id=current_user_id,
        )
        await db.commit()
        return success_response({}, message="编辑成功")
    except Exception as e:
        await db.rollback()
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/web_menu")
async def get_web_menu(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取Web脚本菜单"""
    try:
        data = await WebManagementService.get_web_menu(db, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/menu_script_list")
async def menu_script_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """根据菜单ID获取子脚本列表（对齐旧 /menu_script_list）"""
    try:
        body = await body_to_json(request)
        data = await WebManagementService.get_menu_script_list(db, pid=int(body["id"]))
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/get_web_script")
async def get_web_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取Web脚本"""
    try:
        body = await body_to_json(request)
        data = await WebManagementService.get_web_script(
            db, menu_id=int(body["id"]), user_id=current_user_id
        )
        return success_response(data or {}, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/save_script")
async def save_web_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """保存Web脚本"""
    try:
        body = await body_to_json(request)
        await WebManagementService.save_web_script(db, body, current_user_id)
        await db.commit()
        return success_response({}, message="编辑成功")
    except Exception as e:
        await db.rollback()
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/run_web_script")
async def run_web_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """执行Web脚本"""
    try:
        body = await body_to_json(request)
        res = await WebManagementService.execute_web_script(db, body, body.get("browser") or [], current_user_id)
        await db.commit()
        return success_response(res, message="请求成功")
    except Exception as e:
        await db.rollback()
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/input_element")
async def import_elements(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """导入元素"""
    try:
        body = await body_to_json(request)
        res = await WebManagementService.input_element_from_file(
            db,
            file_url=str(body["file_url"]),
            file_name=str(body["file_name"]),
            pid=int(body["pid"]),
            user_id=current_user_id,
        )
        await db.commit()
        return success_response(res, message="请求成功")
    except Exception as e:
        await db.rollback()
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/stop_web_script")
async def stop_web_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """停止Web执行进程（对齐旧 /stop_web_script）"""
    try:
        body = await body_to_json(request)
        pid = int(body["pid"])
        res = await WebManagementService.stop_web_script(pid)
        return success_response(res, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/get_web_result")
async def get_web_result(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取Web执行结果"""
    try:
        body = await body_to_json(request)
        data = await WebManagementService.get_web_result(
            db, result_id=str(body["result_id"]), browser=int(body["browser"]), user_id=current_user_id
        )
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")

@router.post("/web/get_web_result_log")
async def get_web_result_log(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取Web执行日志（对齐旧 /get_web_result_log）"""
    try:
        body = await body_to_json(request)
        data = await WebManagementService.get_web_result_log(
            result_id=str(body["result_id"]), browser=int(body["browser"])
        )
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/get_web_result_list")
async def get_web_result_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取Web结果列表"""
    try:
        body = await body_to_json(request)
        data = await WebManagementService.get_web_result_list(db, body, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")

@router.post("/web/get_web_result_report")
async def get_web_result_report(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取Web执行报告（对齐旧 /get_web_result_report）"""
    try:
        body = await body_to_json(request)
        result_id = str(body.get("result_id") or "").strip()
        if not result_id:
            return error_response("result_id不能为空", code=ResponseCode.BAD_REQUEST)
        data = await WebManagementService.get_web_result_report(
            db, result_id=result_id, user_id=current_user_id
        )
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/get_web_result_detail")
async def get_web_result_detail(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取Web执行详情（对齐旧 /get_web_result_detail）"""
    try:
        body = await body_to_json(request)
        data = await WebManagementService.get_web_result_detail(
            db,
            result_id=str(body["result_id"]),
            browser=int(body["browser"]),
            menu_id=int(body["menu_id"]),
            user_id=current_user_id,
        )
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/web_group_list")
async def get_web_group_list(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取Web脚本集列表（与旧框架 l-vue-ui 对齐：返回 { content: [], total }）"""
    try:
        data = await WebManagementService.get_web_groups(db, current_user_id)
        data = data if isinstance(data, list) else []
        return success_response({"content": data, "total": len(data)}, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/add_web_group")
async def create_web_group(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增Web脚本集"""
    try:
        body = await body_to_json(request)
        await WebManagementService.create_web_group(db, body, current_user_id)
        await db.commit()
        return success_response({}, message="添加成功")
    except Exception as e:
        await db.rollback()
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/edit_web_group")
async def edit_web_group(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """编辑Web脚本集（对齐旧 /edit_web_group）"""
    try:
        body = await body_to_json(request)
        await WebManagementService.edit_web_group(db, body, current_user_id)
        await db.commit()
        return success_response({}, message="编辑成功")
    except Exception as e:
        await db.rollback()
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/del_web_group")
async def del_web_group(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除Web脚本集（对齐旧 /del_web_group）"""
    try:
        body = await body_to_json(request)
        await WebManagementService.delete_web_group(db, int(body["id"]))
        await db.commit()
        return success_response({}, message="删除成功")
    except Exception as e:
        await db.rollback()
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/web_group_select")
async def web_group_select(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取全部Web脚本集（对齐旧 /web_group_select）"""
    try:
        data = await WebManagementService.get_web_group_all(db, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/get_script_list")
async def get_script_list(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取脚本菜单列表（对齐旧 /get_script_list）"""
    try:
        data = await WebManagementService.get_script_list(db)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/web/group_add_script")
async def group_add_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """根据脚本树选择返回脚本菜单列表（对齐旧 /group_add_script）"""
    try:
        body = await body_to_json(request)
        data = await WebManagementService.group_add_script(db, body.get("web_list") or [])
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")