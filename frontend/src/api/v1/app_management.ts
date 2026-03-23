/**
 * APP 自动化模块接口
 * 对应后端 /api/v1/app_management/*
 * 迁移自 l-vue-ui/src/api/api_app/app.ts
 */
import request from '/@/utils/request';

export const app_menu = (data: any) => request.post('/v1/app_management/app_menu', data);
export const get_app_script = (data: any) => request.post('/v1/app_management/get_app_script', data);
export const save_app_script = (data: any) => request.post('/v1/app_management/save_app_script', data);
export const run_app_script = (data: any) => request.post('/v1/app_management/run_app_script', data);
export const run_script_list = (data: any) => request.post('/v1/app_management/run_script_list', data);
export const add_menu = (data: any) => request.post('/v1/app_management/add_menu', data);
export const del_menu = (data: any) => request.post('/v1/app_management/del_menu', data);
export const rename_menu = (data: any) => request.post('/v1/app_management/rename_menu', data);
export const pid_status = (data: any) => request.post('/v1/app_management/pid_status', data);
export const stop_process = (data: any) => request.post('/v1/app_management/stop_process', data);
export const get_app_result = (data: any) => request.post('/v1/app_management/get_app_result', data);
export const app_result_list = (data: any) => request.post('/v1/app_management/app_result_list', data);

// 以下为旧版 app_view/app.vue 依赖接口（将由后端按旧协议补齐）
export const get_script_list = (data: any) => request.post('/v1/app_management/menu_script_list', data);
export const run_scripts = (data: any) => request.post('/v1/app_management/run_script_list', data);
export const app_result = (data: any) => request.post('/v1/app_management/get_app_result', data);
export const app_result_detail = (data: any) => request.post('/v1/app_management/get_result_detail', data);
export const get_process = (data: any) => request.post('/v1/app_management/get_process', data);
export const get_app_result_detail = (data: any) => request.post('/v1/app_management/get_app_result_detail', data);
export const get_result_list = (data: any) => request.post('/v1/app_management/app_result_list', data);
export const get_result_log = (data: any) => request.post('/v1/app_management/get_result_list', data);
export const view_script_list = (data: any) => request.post('/v1/app_management/view_script_list', data);
export const app_correction = (data: any) => request.post('/v1/app_management/app_correction', data);
export const app_menu_select = (data: any) => request.post('/v1/app_management/app_menu_select', data);
export const send_app_warn = (data: any) => request.post('/v1/app_management/send_app_warn', data);

