"""
接口自动化模块
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sqlalchemy import get_db
from app.core.dependencies import get_current_user_id
from app.common.response import success_response, error_response
from app.utils.common import body_to_json
from .service import ApiAutomationService

router = APIRouter()


@router.post("/api_project")
async def get_api_project(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取项目列表"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_projects_paged(db, body or {}, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/add_api_project")
async def add_api_project(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增项目"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.add_project(db, body, current_user_id)
        return success_response({}, message="添加成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/edit_api_project")
async def edit_api_project(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """编辑项目"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.edit_project(db, int(body["id"]), body, current_user_id)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/del_api_project")
async def del_api_project(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除项目"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.delete_project(db, int(body["id"]), current_user_id)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


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
        data = await ApiAutomationService.get_request_history(db, current_user_id)
        return success_response(data, message="请求成功")
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
    """数据库下拉列表"""
    try:
        data = await ApiAutomationService.get_all_databases(db, current_user_id)
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


@router.post("/api_params_list")
async def api_params_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """参数依赖列表"""
    try:
        data = await ApiAutomationService.get_params_list(db, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/add_api_params")
async def add_api_params(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增参数依赖"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.add_params(db, body, current_user_id)
        return success_response({}, message="添加成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/edit_api_params")
async def edit_api_params(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """编辑参数依赖"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.edit_params(db, int(body["id"]), body, current_user_id)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/del_api_params")
async def del_api_params(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除参数依赖"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.delete_params(db, int(body["id"]), current_user_id)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")



@router.post("/api_params")
async def api_params(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """参数依赖分页列表"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_params_list_paged(db, body or {}, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/add_params")
async def add_params(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增参数依赖"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.add_params(db, body or {}, current_user_id)
        return success_response({}, message="添加成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/edit_params")
async def edit_params(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """编辑参数依赖"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.edit_params(db, int(body["id"]), body or {}, current_user_id)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/del_params")
async def del_params(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除参数依赖"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.delete_params(db, int(body["id"]), current_user_id)
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


@router.post("/params_select")
async def params_select(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """参数依赖下拉"""
    try:
        data = await ApiAutomationService.params_select(db, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/api_function_list")
async def api_function_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """公共函数列表"""
    try:
        data = await ApiAutomationService.get_functions(db, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/add_api_function")
async def add_api_function(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增公共函数"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.add_function(db, body, current_user_id)
        return success_response({}, message="添加成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/edit_api_function")
async def edit_api_function(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """编辑公共函数"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.edit_function(db, int(body["id"]), body, current_user_id)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/del_api_function")
async def del_api_function(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除公共函数"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.delete_function(db, int(body["id"]), current_user_id)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")



@router.post("/api_function")
async def api_function(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """公共函数分页列表"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_functions_paged(db, body or {}, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/add_function")
async def add_function(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增公共函数"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.add_function(db, body or {}, current_user_id)
        return success_response({}, message="添加成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/edit_function")
async def edit_function(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """编辑公共函数"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.edit_function(db, int(body["id"]), body or {}, current_user_id)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/del_function")
async def del_function(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除公共函数"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.delete_function(db, int(body["id"]), current_user_id)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/api_code_list")
async def api_code_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """错误码列表"""
    try:
        data = await ApiAutomationService.get_codes(db)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")



@router.post("/api_code")
async def api_code(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """错误码分页列表"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_codes_paged(db, body or {}, current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/add_code")
async def add_code(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """新增错误码"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.add_code(db, body or {}, current_user_id)
        return success_response({}, message="添加成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/edit_code")
async def edit_code(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """编辑错误码"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.edit_code(db, int(body["id"]), body or {}, current_user_id)
        return success_response({}, message="编辑成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/del_code")
async def del_code(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除错误码"""
    try:
        body = await body_to_json(request)
        await ApiAutomationService.delete_code(db, int(body["id"]), current_user_id)
        return success_response({}, message="删除成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/api_update_list")
async def api_update_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """文档同步变更记录列表"""
    try:
        body = await body_to_json(request)
        data = await ApiAutomationService.get_updates(db, body.get("api_service_id"), current_user_id)
        return success_response(data, message="请求成功")
    except Exception as e:
        return error_response(f"接口请求异常，原因是：{str(e)}")


@router.post("/api_script_list")
async def get_api_script_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取场景列表"""
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
    """新增场景脚本"""
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
    """编辑场景脚本"""
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
    """删除场景脚本"""
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
    """获取全部场景脚本(id/name)"""
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
    """执行场景"""
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
        page = int(body.get("page") or 1)
        page_size = int(body.get("pageSize") or 1000)
        data = await ApiAutomationService.get_script_result_list(db, current_user_id, page, page_size)
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