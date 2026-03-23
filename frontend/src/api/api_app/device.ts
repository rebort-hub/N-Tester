// 1:1 迁移自 l-vue-ui/src/api/api_app/device.ts
// 映射到新后端 /api/v1/cloud_device/*
import axios from '@/utils/axios.ts';

enum API {
	DEVICES_LIST = '/api/v1/cloud_device/device_list',
	DEVICES_INSTALL = '/api/v1/cloud_device/device_install',
	DEVICES_UNINSTALL = '/api/v1/cloud_device/device_uninstall',
	DEVICE_INFO_LIST = '/api/v1/cloud_device/device_info_list',
	USE_DEVICE = '/api/v1/cloud_device/use_device',
	STOP_DEVICE = '/api/v1/cloud_device/stop_device',
	GET_DEVICES_LOG = '/api/v1/cloud_device/get_device_log',
	GET_HISTORY_LIST = '/api/v1/cloud_device/get_history_list',
	DEVICE_INSTALL_APP = '/api/v1/cloud_device/device_install_app',
	DIRECT_INSTALL_APP = '/api/v1/cloud_device/direct_install_app',
	APP_VIEW_DEVICE = '/api/v1/cloud_device/app_view_device',
	ADD_DEVICE = '/api/v1/cloud_device/add_device',
	DEVICE_PERFORMANCE = '/api/v1/cloud_device/device_performance',
}

export const get_device_list = (params: any) => axios.post(API.DEVICES_LIST, params);
export const devices_install = (params: any) => axios.post(API.DEVICES_INSTALL, params);
export const devices_uninstall = (params: any) => axios.post(API.DEVICES_UNINSTALL, params);
export const device_info_list = (params: any) => axios.post(API.DEVICE_INFO_LIST, params);
export const use_device = (params: any) => axios.post(API.USE_DEVICE, params);
export const stop_device = (params: any) => axios.post(API.STOP_DEVICE, params);
export const get_device_log = (params: any) => axios.post(API.GET_DEVICES_LOG, params);
export const get_history_list = (params: any) => axios.post(API.GET_HISTORY_LIST, params);
export const device_install_app = (params: any) => axios.post(API.DEVICE_INSTALL_APP, params);
export const direct_install_app = (params: any) => axios.post(API.DIRECT_INSTALL_APP, params);
export const app_view_device = (params: any) => axios.post(API.APP_VIEW_DEVICE, params);
export const add_device = (params: any) => axios.post(API.ADD_DEVICE, params);
export const device_performance = (params: any) => axios.post(API.DEVICE_PERFORMANCE, params);

