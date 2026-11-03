#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.common.response import success_response, error_response
from app.utils.common import body_to_json
from .service import ApiAutomationService

router = APIRouter()


@router.post("/api_service")
async def get_api_service(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取服务列表"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_services_paged(db, body or {}, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/add_api_service")
async def add_api_service(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增服务"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.add_service(db, body, current_user_id)
        return success_response({}, message="添加成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/edit_api_service")
async def edit_api_service(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """编辑服务"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.edit_service(db, int(body["id"]), body, current_user_id)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/get_common_params")
async def get_common_params(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取服务级全局参数（Header/Cookie/Query/Body）"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_common_params(
            db, int(body["api_service_id"]), current_user_id
        )
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/save_common_params")
async def save_common_params(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """保存服务级全局参数（Header/Cookie/Query/Body）"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.save_common_params(
            db,
            int(body["api_service_id"]),
            body.get("common_params") or {},
            current_user_id,
        )
        return success_response({}, message="保存成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/del_api_service")
async def del_api_service(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除服务"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.delete_service(db, int(body["id"]), current_user_id)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/api_service_list")
async def api_service_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """根据项目获取服务下拉列表"""
    try:
        body = await body_to_json(request)
        project_id = body.get("project_id")
        data = await ApiAutomationService.get_services(db, project_id, current_user_id)
        rows = [{"id": i["id"], "name": i["name"]} for i in data.get("content", [])]
        return success_response(rows, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/api_tree")
async def get_api_tree(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取接口菜单树"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_api_tree(db, body.get("search") or {}, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")

@router.post("/api_tree_list")
async def api_tree_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取全量接口菜单树"""
    try:
        data = await ApiAutomationService.api_tree_list(db, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/add_menu")
async def add_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增菜单"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.add_menu(db, body, current_user_id)
        return success_response({}, message="添加成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")

@router.post("/api_list")
async def api_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """根据菜单ID获取接口列表"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.api_list(db, int(body["id"]), current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/edit_menu")
async def edit_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """编辑菜单"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.edit_menu(db, int(body["id"]), str(body["name"]), current_user_id)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/del_menu")
async def del_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除菜单"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.del_menu(db, body, current_user_id)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/copy_menu")
async def copy_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """复制菜单"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.copy_menu(db, body, current_user_id)
        return success_response({}, message="添加成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/api_info")
async def get_api_info(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取接口信息"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_api_info(db, int(body["api_id"]), current_user_id)
        return success_response(data or {}, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/save_api")
async def save_api(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """保存接口"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.save_api(db, body, current_user_id)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")

@router.post("/save_api_case")
async def save_api_case(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """保存接口用例"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.save_api_case(db, body, current_user_id)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/save_api_case_to_suite")
async def save_api_case_to_suite(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """将接口调试结果保存为用例到指定用例集"""
    try:
        body = await body_to_json(request)
        result = await ApiAutomationService.save_api_case_to_suite(db, body, current_user_id)
        return success_response(result, message="保存成功")
    except Exception as e:
        return error_response(f"保存失败：{str(e)}")


@router.post("/api_send")
async def api_send(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """发送接口请求"""
    try:
        body = await body_to_json(request)
        res = await ApiAutomationService.execute_api_send(db, body, current_user_id)
        return success_response(res, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/req_history")
async def req_history(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """请求历史"""
    try:
        body = await body_to_json(request) or {}
        api_id = body.get("api_id") or body.get("id")
        page = int(body.get("page") or body.get("currentPage") or 1)
        page_size = int(body.get("pageSize") or body.get("limit") or 10)
        data = await ApiAutomationService.get_request_history(
            db,
            current_user_id,
            api_id=int(api_id) if api_id else None,
            page=page,
            page_size=page_size,
        )
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/del_req_history")
async def del_req_history(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """硬删除调试记录"""
    try:
        body = await body_to_json(request) or {}
        result_id = body.get("id") or body.get("result_id")
        if not result_id:
            return error_response("缺少记录 ID")
        await ApiAutomationService.delete_request_history(db, int(result_id), current_user_id)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/edit_history")
async def edit_history(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """接口编辑历史"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_edit_history(db, int(body["api_id"]), current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")

@router.post("/get_api_case")
async def get_api_case(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """根据脚本选择返回用例菜单"""
    try:
        body = await body_to_json(request)
        rows = await ApiAutomationService.get_api_case(db, body.get("script") or [], current_user_id)
        return success_response(rows, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/api_env")
async def get_api_env(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取环境列表"""
    try:
        data = await ApiAutomationService.get_envs(db, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/env_info")
async def env_info(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取环境详情"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_env_info(db, int(body["id"]), current_user_id)
        return success_response(data or {}, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/save_env")
async def save_env(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """批量保存环境配置"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.save_envs(db, body.get("env_list") or [], current_user_id)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/add_env")
async def add_env(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增环境"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.add_env(db, body, current_user_id)
        return success_response({}, message="添加成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/del_env")
async def del_env(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除环境"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.delete_env(db, int(body["id"]), current_user_id)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/api_var_list")
async def api_var_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """全局变量列表"""
    try:
        data = await ApiAutomationService.get_vars(db, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/add_var")
async def add_var(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增全局变量"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.add_var(db, body["name"], body["value"], current_user_id)
        return success_response({}, message="添加成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/edit_var")
async def edit_var(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """编辑全局变量"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.edit_var(db, int(body["id"]), body["name"], body["value"], current_user_id)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/del_var")
async def del_var(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除全局变量"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.delete_var(db, int(body["id"]), current_user_id)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/api_db")
async def get_api_db(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取数据库列表"""
    try:
        data = await ApiAutomationService.get_databases(db, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/api_db_list")
async def api_db_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """数据库列表（支持分页与名称搜索）"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_databases_paged(db, body or {}, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/add_api_db")
async def add_api_db(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增数据库配置"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.add_database(db, body, current_user_id)
        return success_response({}, message="添加成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/edit_api_db")
async def edit_api_db(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """编辑数据库配置"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.edit_database(db, int(body["id"]), body, current_user_id)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/del_api_db")
async def del_api_db(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除数据库配置"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.delete_database(db, int(body["id"]), current_user_id)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/test_db_conn")
async def test_db_conn(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    测试直连数据库连接
    入参：{ "id": 数据库配置ID }
    """
    try:
        body = await body_to_json(request)
        db_id = int(body.get("id"))
        data = await ApiAutomationService.test_db_connection(db, db_id, current_user_id)
        return success_response(data, message=data.get("message", "测试完成"))
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/pull_api_doc")
async def pull_api_doc(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """按文档地址拉取并解析 Swagger/Apifox 到接口树"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.pull_api_doc(db, body or {}, current_user_id)
        return success_response(data, message="拉取并解析成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/api_script_list")
async def get_api_script_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取用例列表"""
    try:
        body = await body_to_json(request)
        page = int(body.get("page") or 1)
        page_size = int(body.get("pageSize") or 1000)
        data = await ApiAutomationService.get_api_scripts(db, current_user_id, page, page_size)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/add_api_script")
async def add_api_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增用例"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.add_api_script(db, body, current_user_id)
        return success_response({}, message="添加成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/edit_api_script")
async def edit_api_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """编辑用例"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.edit_api_script(db, body, current_user_id)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/del_api_script")
async def del_api_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除用例"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.delete_api_script(db, int(body["id"]), current_user_id)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/get_api_script_list")
async def get_api_script_list_simple(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取全部用例(id/name)"""
    try:
        rows = await ApiAutomationService.get_api_script_simple_list(db, current_user_id)
        return success_response(rows, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/run_api_script")
async def run_api_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """执行用例"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.run_api_script(db, body, current_user_id)
        return success_response({}, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/get_api_script_result")
async def get_api_script_result(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取执行结果"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_script_result(db, int(body["result_id"]), current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/get_api_script_result_list")
async def get_api_script_result_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """脚本执行结果汇总列表"""
    try:
        body = await body_to_json(request)
        page = int(body.get("page") or body.get("currentPage") or 1)
        page_size = int(body.get("pageSize") or 1000)
        search = (body or {}).get("search") or {}
        search_name = str((search.get("name") or "")).strip()
        api_service_id = body.get("api_service_id") or search.get("api_service_id")
        data = await ApiAutomationService.get_script_result_list(
            db, current_user_id, page, page_size,
            search_name=search_name,
            api_service_id=int(api_service_id) if api_service_id else None,
        )
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/stop_api_script_result")
async def stop_api_script_result(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """停止接口自动化执行（运行中任务在步骤间隙响应停止）"""
    try:
        body = await body_to_json(request)
        rid = int(body["result_id"])
        data = await ApiAutomationService.stop_api_script_result(db, rid, current_user_id)
        if not data.get("stopped"):
            return error_response(data.get("message") or "停止失败")
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/del_api_script_result")
async def del_api_script_result(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除接口自动化执行记录（运行中会先请求停止）"""
    try:
        body = await body_to_json(request)
        rid = int(body["result_id"])
        data = await ApiAutomationService.delete_api_script_result(db, rid, current_user_id)
        if not data.get("deleted"):
            return error_response(data.get("message") or "删除失败")
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/get_api_script_result_detail")
async def get_api_script_result_detail(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """脚本执行结果详情（按批次）"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_script_result_detail(db, int(body["result_id"]))
        return success_response(data or {}, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/get_api_script_result_detail_list")
async def get_api_script_result_detail_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """脚本执行结果详情列表（按菜单ID）"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_script_result_detail_list(
            db, int(body["result_id"]), str(body["menu_id"])
        )
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")

@router.post("/get_api_script_result_report_list")
async def get_api_script_result_report_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """执行结果报告列表"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_script_result_report_list(
            db, int(body["result_id"]), str(body["menu_id"])
        )
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/get_api_script_log")
async def get_api_script_log(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """脚本执行日志（整体）"""
    try:
        body = await body_to_json(request)
        lines = await ApiAutomationService.read_script_log(str(body["result_id"]))
        return success_response(lines, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/get_api_script_report_log")
async def get_api_script_report_log(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """脚本执行日志（按菜单ID）"""
    try:
        body = await body_to_json(request)
        lines = await ApiAutomationService.read_script_report_log(
            str(body["result_id"]), str(body["menu_id"])
        )
        return success_response(lines, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/service_api_update")
async def service_api_update(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """开放接口给 API 文档平台使用"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.service_api_update(db, body)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/gitlab_ci_notice")
async def gitlab_ci_notice(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """开放接口给 Gitlab CI 构建"""
    try:
        body = await body_to_json(request)
        res = await ApiAutomationService.gitlab_ci_notice(db, body)
        return success_response(res, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


# ── 代码生成 ──────────────────────────────────────────────────────────

@router.post("/generate_code")
async def generate_code(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    生成测试框架代码。

    body:
      source_type: swagger | apifox | case | custom
      api_ids:     接口 ID 列表（source_type 为 swagger/apifox/case 时使用）
      custom_apis: 自定义接口列表（source_type 为 custom 时使用）
      framework:   pytest | unittest | testng | jest
      base_url:    服务基础 URL（可选，优先使用）
      class_name:  生成的类名（可选）
      service_id:  服务 ID（用于自动获取 base_url，可选）
    """
    from .code_generator import generate_test_code

    try:
        body = await body_to_json(request) or {}
        source_type = body.get("source_type", "custom")
        framework = body.get("framework", "pytest")
        base_url = body.get("base_url", "")
        class_name = body.get("class_name", "AutoGenerated")
        service_id = body.get("service_id")

        # 若未传 base_url，尝试从环境配置获取
        if not base_url and service_id:
            base_url = await ApiAutomationService.get_service_base_url(db, int(service_id))

        # 获取接口列表
        if source_type in ("swagger", "apifox", "case"):
            api_ids = [int(i) for i in (body.get("api_ids") or [])]
            apis = await ApiAutomationService.get_apis_by_ids(db, api_ids)
        else:
            # custom：直接使用前端传入的接口数据
            apis = body.get("custom_apis") or []

        code = generate_test_code(apis, framework, base_url, class_name)
        return success_response({"code": code, "framework": framework}, message="生成成功")
    except ValueError as e:
        return error_response(str(e))
    except Exception as e:
        return error_response(f"代码生成失败：{str(e)}")


@router.post("/run_generated_code")
async def run_generated_code(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    运行生成的 pytest / unittest 代码。

    body:
      code:      代码字符串
      framework: pytest | unittest
      exec_mode: sandbox | native（可选，默认读配置）
    """
    from .script_runtime import run_generated_code_async

    try:
        body = await body_to_json(request) or {}
        code = body.get("code", "")
        framework = str(body.get("framework", "pytest") or "pytest").lower()
        exec_mode = body.get("exec_mode") or body.get("script_exec_mode")

        if framework not in ("pytest", "unittest"):
            return error_response("运行调试仅支持 pytest / unittest（Python 框架）")
        if not str(code).strip():
            return error_response("代码不能为空")

        result = await run_generated_code_async(code, framework=framework, mode=exec_mode)
        output = result.output or ""
        if result.error and not result.success:
            if output:
                output = f"{output}\n{result.error}"
            else:
                output = result.error
        return success_response(
            {
                "output": output,
                "success": result.success,
                "exec_mode": result.mode,
            },
            message="执行完成",
        )
    except Exception as e:
        return error_response(f"执行失败：{str(e)}")


# ── 服务排序 ──────────────────────────────────────────────────────────

@router.post("/api_service_sort")
async def api_service_sort(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """服务排序"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.sort_services(db, body["ids"], current_user_id)
        return success_response({}, message="排序成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


# ── 用例集（Suite）CRUD ───────────────────────────────────────────────

@router.post("/api_suite_list")
async def api_suite_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取用例集树"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_suite_list(db, int(body["api_service_id"]), current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/add_api_suite")
async def add_api_suite(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增用例集"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.add_suite(db, body, current_user_id)
        return success_response(data, message="添加成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/edit_api_suite")
async def edit_api_suite(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """编辑用例集"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.edit_suite(db, int(body["id"]), str(body["name"]), current_user_id)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/del_api_suite")
async def del_api_suite(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除用例集（级联删除子集和用例）"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.delete_suite(db, int(body["id"]), current_user_id)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/api_suite_sort")
async def api_suite_sort(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """用例集排序"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.sort_suites(db, body["ids"], current_user_id)
        return success_response({}, message="排序成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


# ── 用例（Case）CRUD 及执行 ───────────────────────────────────────────

@router.post("/api_case_list")
async def api_case_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取用例列表"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_case_list(db, int(body["suite_id"]), current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/add_api_case")
async def add_api_case(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增用例"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.add_case(db, body, current_user_id)
        return success_response(data, message="添加成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/edit_api_case")
async def edit_api_case(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """编辑用例"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.edit_case(db, int(body["id"]), body, current_user_id)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/del_api_case")
async def del_api_case(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除用例"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.delete_case(db, int(body["id"]), current_user_id)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/run_api_case")
async def run_api_case(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """执行用例"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.run_api_case(db, body, current_user_id)
        return success_response(data, message="已触发执行")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


# ─── 脚本中心（NtestScript）接口 ──────────────────────────────────────────────

@router.post("/ntest_script_list")
async def ntest_script_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取公共脚本列表"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_ntest_scripts(db, int(body["api_service_id"]), current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/add_ntest_script")
async def add_ntest_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增公共脚本"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.add_ntest_script(db, body, current_user_id)
        return success_response({}, message="添加成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/edit_ntest_script")
async def edit_ntest_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """编辑公共脚本"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.edit_ntest_script(db, int(body["id"]), body, current_user_id)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/del_ntest_script")
async def del_ntest_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除公共脚本（软删除）"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.delete_ntest_script(db, int(body["id"]), current_user_id)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


# ─── 数据查询（QueryDB）接口 ──────────────────────────────────────────────────

@router.post("/get_db_databases")
async def get_db_databases(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取指定数据库连接下的所有数据库名"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_db_databases(db, int(body["db_id"]))
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/get_db_tables")
async def get_db_tables(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取指定数据库下的所有表名"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_db_tables(db, int(body["db_id"]), str(body["database"]))
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/execute_db_query")
async def execute_db_query(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """执行 SELECT 查询语句"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.execute_db_query(db, int(body["db_id"]), str(body["sql"]))
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")
