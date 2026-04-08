import request from '/@/utils/request';

const postApiAutomation = <T = any>(url: string, data?: any) => {
  return request<T>({
    url,
    method: 'post',
    data,
  });
};

export function useApiAutomationApi() {
  return {
    // ---------- 项目 ----------
    api_project: (data: { page?: number; pageSize?: number } = {}) => postApiAutomation('/v1/api_automation/api_project', data),
    add_api_project: (data: { name: string; img?: string | null; description?: string | null }) =>
      postApiAutomation('/v1/api_automation/add_api_project', data),
    edit_api_project: (data: { id: number; name?: string; img?: string | null; description?: string | null }) =>
      postApiAutomation('/v1/api_automation/edit_api_project', data),
    del_api_project: (data: { id: number }) => postApiAutomation('/v1/api_automation/del_api_project', data),

    // ---------- 服务 ----------
    api_service: (data: { page?: number; pageSize?: number; search?: { api_project_id?: number | null } } = {}) =>
      postApiAutomation('/v1/api_automation/api_service', data),
    add_api_service: (data: { name: string; api_project_id: number; img?: string | null; description?: string | null }) =>
      postApiAutomation('/v1/api_automation/add_api_service', data),
    edit_api_service: (data: { id: number; name?: string; api_project_id?: number; img?: string | null; description?: string | null }) =>
      postApiAutomation('/v1/api_automation/edit_api_service', data),
    del_api_service: (data: { id: number }) => postApiAutomation('/v1/api_automation/del_api_service', data),
    api_service_list: (data: { project_id?: number | null } = {}) => postApiAutomation('/v1/api_automation/api_service_list', data),

    // ---------- 树/菜单 ----------
    api_tree: (data: { search?: Record<string, any> } = {}) => postApiAutomation('/v1/api_automation/api_tree', data),
    api_tree_list: (data: Record<string, any> = {}) => postApiAutomation('/v1/api_automation/api_tree_list', data),
    add_menu: (data: { name: string; pid: number; type: number; api_service_id: number }) =>
      postApiAutomation('/v1/api_automation/add_menu', data),
    edit_menu: (data: { id: number; name: string }) => postApiAutomation('/v1/api_automation/edit_menu', data),
    del_menu: (data: { id: number; type?: number }) => postApiAutomation('/v1/api_automation/del_menu', data),
    copy_menu: (data: { id: number; api_id: number }) => postApiAutomation('/v1/api_automation/copy_menu', data),

    // ---------- API 接口详情/保存/发送 ----------
    api_info: (data: { api_id: number }) => postApiAutomation('/v1/api_automation/api_info', data),
    save_api: (data: { id: number; url?: string; req?: Record<string, any> }) => postApiAutomation('/v1/api_automation/save_api', data),
    save_api_case: (data: Record<string, any>) => postApiAutomation('/v1/api_automation/save_api_case', data),
    api_send: (data: { id?: number; env_id?: number; url?: string; req?: Record<string, any> }) =>
      postApiAutomation('/v1/api_automation/api_send', data),
    req_history: (data: Record<string, any> = {}) => postApiAutomation('/v1/api_automation/req_history', data),
    edit_history: (data: { api_id: number }) => postApiAutomation('/v1/api_automation/edit_history', data),

    // ---------- 环境 ----------
    api_env: (data: Record<string, any> = {}) => postApiAutomation('/v1/api_automation/api_env', data),
    env_info: (data: { id: number }) => postApiAutomation('/v1/api_automation/env_info', data),
    save_env: (data: { env_list: Array<Record<string, any>> }) => postApiAutomation('/v1/api_automation/save_env', data),
    add_env: (data: { name: string; config?: any[]; variable?: any[] }) => postApiAutomation('/v1/api_automation/add_env', data),
    del_env: (data: { id: number }) => postApiAutomation('/v1/api_automation/del_env', data),

    // ---------- 全局变量 ----------
    api_var_list: (data: Record<string, any> = {}) => postApiAutomation('/v1/api_automation/api_var_list', data),
    add_var: (data: { name: string; value: string }) => postApiAutomation('/v1/api_automation/add_var', data),
    edit_var: (data: { id: number; name: string; value: string }) => postApiAutomation('/v1/api_automation/edit_var', data),
    del_var: (data: { id: number }) => postApiAutomation('/v1/api_automation/del_var', data),

    // ---------- 数据库配置 ----------
    api_db: (data: Record<string, any> = {}) => postApiAutomation('/v1/api_automation/api_db', data),
    api_db_list: (data: Record<string, any> = {}) => postApiAutomation('/v1/api_automation/api_db_list', data),
    add_api_db: (data: { name: string; config?: Record<string, any> }) => postApiAutomation('/v1/api_automation/add_api_db', data),
    edit_api_db: (data: { id: number; name?: string; config?: Record<string, any> }) => postApiAutomation('/v1/api_automation/edit_api_db', data),
    del_api_db: (data: { id: number }) => postApiAutomation('/v1/api_automation/del_api_db', data),
    test_db_conn: (data: { id: number }) => postApiAutomation('/v1/api_automation/test_db_conn', data),

    // ---------- 参数依赖 ----------
    api_params_list: (data: Record<string, any> = {}) => postApiAutomation('/v1/api_automation/api_params_list', data),
    add_api_params: (data: { name: string; value?: Record<string, any> }) => postApiAutomation('/v1/api_automation/add_api_params', data),
    edit_api_params: (data: { id: number; name?: string; value?: Record<string, any> }) => postApiAutomation('/v1/api_automation/edit_api_params', data),
    del_api_params: (data: { id: number }) => postApiAutomation('/v1/api_automation/del_api_params', data),
    api_params: (data: Record<string, any> = {}) => postApiAutomation('/v1/api_automation/api_params', data),
    add_params: (data: Record<string, any>) => postApiAutomation('/v1/api_automation/add_params', data),
    edit_params: (data: Record<string, any>) => postApiAutomation('/v1/api_automation/edit_params', data),
    del_params: (data: Record<string, any>) => postApiAutomation('/v1/api_automation/del_params', data),
    params_select: (data: Record<string, any> = {}) => postApiAutomation('/v1/api_automation/params_select', data),

    // ---------- 公共函数 ----------
    api_function_list: (data: Record<string, any> = {}) => postApiAutomation('/v1/api_automation/api_function_list', data),
    add_api_function: (data: { name: string; description?: string | null }) => postApiAutomation('/v1/api_automation/add_api_function', data),
    edit_api_function: (data: { id: number; name?: string; description?: string | null }) => postApiAutomation('/v1/api_automation/edit_api_function', data),
    del_api_function: (data: { id: number }) => postApiAutomation('/v1/api_automation/del_api_function', data),
    api_function: (data: Record<string, any> = {}) => postApiAutomation('/v1/api_automation/api_function', data),
    add_function: (data: Record<string, any>) => postApiAutomation('/v1/api_automation/add_function', data),
    edit_function: (data: Record<string, any>) => postApiAutomation('/v1/api_automation/edit_function', data),
    del_function: (data: Record<string, any>) => postApiAutomation('/v1/api_automation/del_function', data),

    // ---------- 错误码 ----------
    api_code_list: (data: Record<string, any> = {}) => postApiAutomation('/v1/api_automation/api_code_list', data),
    api_code: (data: Record<string, any> = {}) => postApiAutomation('/v1/api_automation/api_code', data),
    add_code: (data: Record<string, any>) => postApiAutomation('/v1/api_automation/add_code', data),
    edit_code: (data: Record<string, any>) => postApiAutomation('/v1/api_automation/edit_code', data),
    del_code: (data: Record<string, any>) => postApiAutomation('/v1/api_automation/del_code', data),

    // ---------- 文档同步变更 ----------
    api_update_list: (data: { api_service_id?: number | null } = {}) => postApiAutomation('/v1/api_automation/api_update_list', data),
    pull_api_doc: (data: {
      api_service_id: number;
      source_type: 'swagger' | 'apifox';
      doc_url?: string;
      cookies?: string;
      doc_content?: Record<string, any>;
    }) => postApiAutomation('/v1/api_automation/pull_api_doc', data),

    // ---------- 场景/执行 ----------
    api_script_list: (data: { page?: number; pageSize?: number } = {}) => postApiAutomation('/v1/api_automation/api_script_list', data),
    add_api_script: (data: Record<string, any>) => postApiAutomation('/v1/api_automation/add_api_script', data),
    edit_api_script: (data: Record<string, any>) => postApiAutomation('/v1/api_automation/edit_api_script', data),
    del_api_script: (data: { id: number }) => postApiAutomation('/v1/api_automation/del_api_script', data),
    get_api_script_list: (data: Record<string, any> = {}) => postApiAutomation('/v1/api_automation/get_api_script_list', data),
    get_api_case: (data: { script?: any[] } = {}) => postApiAutomation('/v1/api_automation/get_api_case', data),
    run_api_script: (data: Record<string, any>) => postApiAutomation('/v1/api_automation/run_api_script', data),
    get_api_script_result: (data: { result_id: number }) => postApiAutomation('/v1/api_automation/get_api_script_result', data),
    get_api_script_result_list: (data: { page?: number; pageSize?: number } = {}) =>
      postApiAutomation('/v1/api_automation/get_api_script_result_list', data),
    get_api_script_result_detail: (data: { result_id: number }) => postApiAutomation('/v1/api_automation/get_api_script_result_detail', data),
    get_api_script_result_detail_list: (data: { result_id: number; menu_id: string }) =>
      postApiAutomation('/v1/api_automation/get_api_script_result_detail_list', data),
    get_api_script_result_report_list: (data: { result_id: number; menu_id: string }) =>
      postApiAutomation('/v1/api_automation/get_api_script_result_report_list', data),
    get_api_script_log: (data: { result_id: string }) => postApiAutomation('/v1/api_automation/get_api_script_log', data),
    get_api_script_report_log: (data: { result_id: string; menu_id: string }) =>
      postApiAutomation('/v1/api_automation/get_api_script_report_log', data),

    // ---------- 外部调用 ----------
    service_api_update: (data: Record<string, any>) => postApiAutomation('/v1/api_automation/service_api_update', data),
    gitlab_ci_notice: (data: Record<string, any>) => postApiAutomation('/v1/api_automation/gitlab_ci_notice', data),
  };
}

// 兼容旧用法：逐步迁移页面 import 后可移除
export const apiAutomationApi = useApiAutomationApi();
export const {
  api_project,
  add_api_project,
  edit_api_project,
  del_api_project,
  api_service,
  add_api_service,
  edit_api_service,
  del_api_service,
  api_service_list,
  api_tree,
  api_tree_list,
  add_menu,
  edit_menu,
  del_menu,
  copy_menu,
  api_info,
  save_api,
  save_api_case,
  api_send,
  req_history,
  edit_history,
  api_env,
  env_info,
  save_env,
  add_env,
  del_env,
  api_var_list,
  add_var,
  edit_var,
  del_var,
  api_db,
  api_db_list,
  add_api_db,
  edit_api_db,
  del_api_db,
  test_db_conn,
  api_params_list,
  add_api_params,
  edit_api_params,
  del_api_params,
  api_params,
  add_params,
  edit_params,
  del_params,
  params_select,
  api_function_list,
  add_api_function,
  edit_api_function,
  del_api_function,
  api_function,
  add_function,
  edit_function,
  del_function,
  api_code_list,
  api_code,
  add_code,
  edit_code,
  del_code,
  api_update_list,
  pull_api_doc,
  api_script_list,
  add_api_script,
  edit_api_script,
  del_api_script,
  get_api_script_list,
  get_api_case,
  run_api_script,
  get_api_script_result,
  get_api_script_result_list,
  get_api_script_result_detail,
  get_api_script_result_detail_list,
  get_api_script_result_report_list,
  get_api_script_log,
  get_api_script_report_log,
  service_api_update,
  gitlab_ci_notice,
} = apiAutomationApi;

