/**
 * 兼容旧版 APP管理相关的 device API
 * 旧前端路径：/api/device/*
 * 新后端路径：/api/v1/cloud_device/*
 */
import request from '/@/utils/request';

export const get_device_list = (data: any) => request.post('/v1/cloud_device/device_list', data);
export const devices_install = (data: any) => request.post('/v1/cloud_device/device_install', data);
export const devices_uninstall = (data: any) => request.post('/v1/cloud_device/device_uninstall', data);
export const device_info_list = (data: any) => request.post('/v1/cloud_device/device_info_list', data);
export const use_device = (data: any) => request.post('/v1/cloud_device/use_device', data);
export const stop_device = (data: any) => request.post('/v1/cloud_device/stop_device', data);
export const get_device_log = (data: any) => request.post('/v1/cloud_device/get_device_log', data);
export const get_history_list = (data: any) => request.post('/v1/cloud_device/get_history_list', data);
export const device_install_app = (data: any) => request.post('/v1/cloud_device/device_install_app', data);
export const direct_install_app = (data: any) => request.post('/v1/cloud_device/direct_install_app', data);
export const app_view_device = (data: any) => request.post('/v1/cloud_device/app_view_device', data);
export const add_device = (data: any) => request.post('/v1/cloud_device/add_device', data);
export const device_performance = (data: any) => request.post('/v1/cloud_device/device_performance', data);

