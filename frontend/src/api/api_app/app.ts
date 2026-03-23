// 1:1 迁移自 l-vue-ui/src/api/api_app/app.ts
// 仅将 base url 从旧 /api/app/* 映射到新 /api/v1/app_management/*
import axios from '@/utils/axios.ts';

enum API {
	APP_MENU = '/api/v1/app_management/app_menu',
	SCRIPT_INFO = '/api/v1/app_management/get_app_script',
	SAVE_SCRIPT = '/api/v1/app_management/save_app_script',
	RUN_SCRIPT = '/api/v1/app_management/run_app_script',
	ADD_MENU = '/api/v1/app_management/add_menu',
	DEL_MENU = '/api/v1/app_management/del_menu',
	RENAME_MENU = '/api/v1/app_management/rename_menu',
	// 对齐旧 get_app_result：单设备步骤列表（传 result_id + device）
	APP_RESULT = '/api/v1/app_management/get_app_result',
	PID_STATUS = '/api/v1/app_management/pid_status',
	STOP_PROCESS = '/api/v1/app_management/stop_process',
	// 对齐旧 get_result_detail：单设备汇总统计
	APP_RESULT_DETAIL = '/api/v1/app_management/get_result_detail',
	MENU_SCRIPT_LIST = '/api/v1/app_management/menu_script_list',
	RUN_SCRIPT_LIST = '/api/v1/app_management/run_script_list',
	APP_RESULT_LIST = '/api/v1/app_management/app_result_list',
	GET_APP_RESULT_DETAIL = '/api/v1/app_management/get_app_result_detail',
	GET_RESULT_LIST = '/api/v1/app_management/get_result_list',
	SEND_APP_WARN = '/api/v1/app_management/send_app_warn',
	GET_SCRIPT_LIST = '/api/v1/app_management/get_script_list',
	GET_PROCESS = '/api/v1/app_management/get_process',
	VIEW_SCRIPT_LIST = '/api/v1/app_management/view_script_list',
	APP_CORRECTION = '/api/v1/app_management/app_correction',
	APP_MENU_SELECT = '/api/v1/app_management/app_menu_select',
}

export const app_menu = (params: any) => axios.post(API.APP_MENU, params);
export const get_script = (params: any) => axios.post(API.SCRIPT_INFO, params);
export const get_script_list = (params: any) => axios.post(API.MENU_SCRIPT_LIST, params);
export const save_app_script = (params: any) => axios.post(API.SAVE_SCRIPT, params);
export const run_app_script = (params: any) => axios.post(API.RUN_SCRIPT, params);
export const run_scripts = (params: any) => axios.post(API.RUN_SCRIPT_LIST, params);
export const add_app_menu = (params: any) => axios.post(API.ADD_MENU, params);
export const del_app_menu = (params: any) => axios.post(API.DEL_MENU, params);
export const rename_app_menu = (params: any) => axios.post(API.RENAME_MENU, params);
export const app_result = (params: any) => axios.post(API.APP_RESULT, params);
export const app_result_detail = (params: any) => axios.post(API.APP_RESULT_DETAIL, params);
export const pid_status = (params: any) => axios.post(API.PID_STATUS, params);
export const stop_process = (params: any) => axios.post(API.STOP_PROCESS, params);
export const get_result_list = (params: any) => axios.post(API.APP_RESULT_LIST, params);
export const get_app_result_detail = (params: any) => axios.post(API.GET_APP_RESULT_DETAIL, params);
export const get_result_log = (params: any) => axios.post(API.GET_RESULT_LIST, params);
export const send_app_warn = (params: any) => axios.post(API.SEND_APP_WARN, params);
export const get_app_script_list = (params: any) => axios.post(API.GET_SCRIPT_LIST, params);
export const get_process = (params: any) => axios.post(API.GET_PROCESS, params);
export const view_script_list = (params: any) => axios.post(API.VIEW_SCRIPT_LIST, params);
export const app_correction = (params: any) => axios.post(API.APP_CORRECTION, params);
export const app_menu_select = (params: any) => axios.post(API.APP_MENU_SELECT, params);

