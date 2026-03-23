/**
 * 接口自动化模块接口
 * 对应后端 /api/v1/api_automation/*
 *
 * 注意：接口路径与入参字段严格按新架构后端 controller/schema 定义编写：
 * - 前端 request.baseURL 已包含 /api 前缀（见后端 config.API_PREFIX）
 * - 这里的 url 以 /v1 开头
 */
import request from '/@/utils/request';

// ---------- 项目 ----------
export const api_project = (data: { page?: number; pageSize?: number } = {}) => {
	return request.post('/v1/api_automation/api_project', data);
};

export const add_api_project = (data: { name: string; img?: string | null; description?: string | null }) => {
	return request.post('/v1/api_automation/add_api_project', data);
};

export const edit_api_project = (data: { id: number; name?: string; img?: string | null; description?: string | null }) => {
	return request.post('/v1/api_automation/edit_api_project', data);
};

export const del_api_project = (data: { id: number }) => {
	return request.post('/v1/api_automation/del_api_project', data);
};

// ---------- 服务 ----------
export const api_service = (data: { page?: number; pageSize?: number; search?: { api_project_id?: number | null } } = {}) => {
	return request.post('/v1/api_automation/api_service', data);
};

export const add_api_service = (data: { name: string; api_project_id: number; img?: string | null; description?: string | null }) => {
	return request.post('/v1/api_automation/add_api_service', data);
};

export const edit_api_service = (data: { id: number; name?: string; api_project_id?: number; img?: string | null; description?: string | null }) => {
	return request.post('/v1/api_automation/edit_api_service', data);
};

export const del_api_service = (data: { id: number }) => {
	return request.post('/v1/api_automation/del_api_service', data);
};

export const api_service_list = (data: { project_id?: number | null } = {}) => {
	return request.post('/v1/api_automation/api_service_list', data);
};

// ---------- 树/菜单 ----------
export const api_tree = (data: { search?: Record<string, any> } = {}) => {
	return request.post('/v1/api_automation/api_tree', data);
};

export const api_tree_list = (data: Record<string, any> = {}) => {
	return request.post('/v1/api_automation/api_tree_list', data);
};

export const add_menu = (data: { name: string; pid: number; type: number; api_service_id: number }) => {
	return request.post('/v1/api_automation/add_menu', data);
};

export const edit_menu = (data: { id: number; name: string }) => {
	return request.post('/v1/api_automation/edit_menu', data);
};

export const del_menu = (data: { id: number; type?: number }) => {
	return request.post('/v1/api_automation/del_menu', data);
};

export const copy_menu = (data: { id: number; api_id: number }) => {
	return request.post('/v1/api_automation/copy_menu', data);
};

// ---------- API 接口详情/保存/发送 ----------
export const api_info = (data: { api_id: number }) => {
	return request.post('/v1/api_automation/api_info', data);
};

export const save_api = (data: { id: number; url?: string; req?: Record<string, any> }) => {
	return request.post('/v1/api_automation/save_api', data);
};

export const save_api_case = (data: Record<string, any>) => {
	return request.post('/v1/api_automation/save_api_case', data);
};

export const api_send = (data: { id?: number; env_id?: number; url?: string; req?: Record<string, any> }) => {
	return request.post('/v1/api_automation/api_send', data);
};

export const req_history = (data: Record<string, any> = {}) => {
	return request.post('/v1/api_automation/req_history', data);
};

export const edit_history = (data: { api_id: number }) => {
	return request.post('/v1/api_automation/edit_history', data);
};

// ---------- 环境 ----------
export const api_env = (data: Record<string, any> = {}) => {
	return request.post('/v1/api_automation/api_env', data);
};

export const env_info = (data: { id: number }) => {
	return request.post('/v1/api_automation/env_info', data);
};

export const save_env = (data: { env_list: Array<Record<string, any>> }) => {
	return request.post('/v1/api_automation/save_env', data);
};

export const add_env = (data: { name: string; config?: any[]; variable?: any[] }) => {
	return request.post('/v1/api_automation/add_env', data);
};

export const del_env = (data: { id: number }) => {
	return request.post('/v1/api_automation/del_env', data);
};

// ---------- 全局变量 ----------
export const api_var_list = (data: Record<string, any> = {}) => {
	return request.post('/v1/api_automation/api_var_list', data);
};

export const add_var = (data: { name: string; value: string }) => {
	return request.post('/v1/api_automation/add_var', data);
};

export const edit_var = (data: { id: number; name: string; value: string }) => {
	return request.post('/v1/api_automation/edit_var', data);
};

export const del_var = (data: { id: number }) => {
	return request.post('/v1/api_automation/del_var', data);
};

// ---------- 数据库配置 ----------
export const api_db = (data: Record<string, any> = {}) => {
	return request.post('/v1/api_automation/api_db', data);
};

export const api_db_list = (data: Record<string, any> = {}) => {
	return request.post('/v1/api_automation/api_db_list', data);
};

export const add_api_db = (data: { name: string; config?: Record<string, any> }) => {
	return request.post('/v1/api_automation/add_api_db', data);
};

export const edit_api_db = (data: { id: number; name?: string; config?: Record<string, any> }) => {
	return request.post('/v1/api_automation/edit_api_db', data);
};

export const del_api_db = (data: { id: number }) => {
	return request.post('/v1/api_automation/del_api_db', data);
};

export const test_db_conn = (data: { id: number }) => {
	return request.post('/v1/api_automation/test_db_conn', data);
};

// ---------- 参数依赖 ----------
export const api_params_list = (data: Record<string, any> = {}) => {
	return request.post('/v1/api_automation/api_params_list', data);
};

export const add_api_params = (data: { name: string; value?: Record<string, any> }) => {
	return request.post('/v1/api_automation/add_api_params', data);
};

export const edit_api_params = (data: { id: number; name?: string; value?: Record<string, any> }) => {
	return request.post('/v1/api_automation/edit_api_params', data);
};

export const del_api_params = (data: { id: number }) => {
	return request.post('/v1/api_automation/del_api_params', data);
};

// 兼容旧接口命名（controller 也提供了 /api_params + add/edit/del_params + params_select）
export const api_params = (data: Record<string, any> = {}) => {
	return request.post('/v1/api_automation/api_params', data);
};
export const add_params = (data: Record<string, any>) => request.post('/v1/api_automation/add_params', data);
export const edit_params = (data: Record<string, any>) => request.post('/v1/api_automation/edit_params', data);
export const del_params = (data: Record<string, any>) => request.post('/v1/api_automation/del_params', data);
export const params_select = (data: Record<string, any> = {}) => request.post('/v1/api_automation/params_select', data);

// ---------- 公共函数 ----------
export const api_function_list = (data: Record<string, any> = {}) => {
	return request.post('/v1/api_automation/api_function_list', data);
};
export const add_api_function = (data: { name: string; description?: string | null }) => {
	return request.post('/v1/api_automation/add_api_function', data);
};
export const edit_api_function = (data: { id: number; name?: string; description?: string | null }) => {
	return request.post('/v1/api_automation/edit_api_function', data);
};
export const del_api_function = (data: { id: number }) => {
	return request.post('/v1/api_automation/del_api_function', data);
};
// 兼容旧分页接口
export const api_function = (data: Record<string, any> = {}) => request.post('/v1/api_automation/api_function', data);
export const add_function = (data: Record<string, any>) => request.post('/v1/api_automation/add_function', data);
export const edit_function = (data: Record<string, any>) => request.post('/v1/api_automation/edit_function', data);
export const del_function = (data: Record<string, any>) => request.post('/v1/api_automation/del_function', data);

// ---------- 错误码 ----------
export const api_code_list = (data: Record<string, any> = {}) => request.post('/v1/api_automation/api_code_list', data);
export const api_code = (data: Record<string, any> = {}) => request.post('/v1/api_automation/api_code', data);
export const add_code = (data: Record<string, any>) => request.post('/v1/api_automation/add_code', data);
export const edit_code = (data: Record<string, any>) => request.post('/v1/api_automation/edit_code', data);
export const del_code = (data: Record<string, any>) => request.post('/v1/api_automation/del_code', data);

// ---------- 文档同步变更 ----------
export const api_update_list = (data: { api_service_id?: number | null } = {}) => {
	return request.post('/v1/api_automation/api_update_list', data);
};

// ---------- 场景/执行 ----------
export const api_script_list = (data: { page?: number; pageSize?: number } = {}) => {
	return request.post('/v1/api_automation/api_script_list', data);
};
export const add_api_script = (data: Record<string, any>) => request.post('/v1/api_automation/add_api_script', data);
export const edit_api_script = (data: Record<string, any>) => request.post('/v1/api_automation/edit_api_script', data);
export const del_api_script = (data: { id: number }) => request.post('/v1/api_automation/del_api_script', data);
export const get_api_script_list = (data: Record<string, any> = {}) => request.post('/v1/api_automation/get_api_script_list', data);

export const get_api_case = (data: { script?: any[] } = {}) => request.post('/v1/api_automation/get_api_case', data);
export const run_api_script = (data: Record<string, any>) => request.post('/v1/api_automation/run_api_script', data);

export const get_api_script_result = (data: { result_id: number }) => request.post('/v1/api_automation/get_api_script_result', data);
export const get_api_script_result_list = (data: { page?: number; pageSize?: number } = {}) =>
	request.post('/v1/api_automation/get_api_script_result_list', data);
export const get_api_script_result_detail = (data: { result_id: number }) => request.post('/v1/api_automation/get_api_script_result_detail', data);
export const get_api_script_result_detail_list = (data: { result_id: number; menu_id: string }) =>
	request.post('/v1/api_automation/get_api_script_result_detail_list', data);
export const get_api_script_result_report_list = (data: { result_id: number; menu_id: string }) =>
	request.post('/v1/api_automation/get_api_script_result_report_list', data);
export const get_api_script_log = (data: { result_id: string }) => request.post('/v1/api_automation/get_api_script_log', data);
export const get_api_script_report_log = (data: { result_id: string; menu_id: string }) =>
	request.post('/v1/api_automation/get_api_script_report_log', data);

// ---------- 外部调用 ----------
export const service_api_update = (data: Record<string, any>) => request.post('/v1/api_automation/service_api_update', data);
export const gitlab_ci_notice = (data: Record<string, any>) => request.post('/v1/api_automation/gitlab_ci_notice', data);

