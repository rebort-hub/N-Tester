/**
 * 云真机模块接口
 * 对应后端 /api/v1/cloud_device/*
 */
import request from '/@/utils/request';

// 获取设备列表
export const device_list = (data: any) => {
    return request.post("/v1/cloud_device/device_list", data);
};

// 获取设备详细信息列表
export const device_info_list = (data: any) => {
    return request.post("/v1/cloud_device/device_info_list", data);
};

// 使用设备（获取远程控制链接）
export const use_device = (data: any) => {
    return request.post("/v1/cloud_device/use_device", data);
};

// 释放设备
export const stop_device = (data: any) => {
    return request.post("/v1/cloud_device/stop_device", data);
};

// 安装APP
export const device_install_app = (data: any) => {
    return request.post("/v1/cloud_device/device_install_app", data);
};

// 直接安装APP（从历史记录）
export const direct_install_app = (data: any) => {
    return request.post("/v1/cloud_device/direct_install_app", data);
};

// 批量卸载APP
export const device_uninstall = (data: any) => {
    return request.post("/v1/cloud_device/device_uninstall", data);
};

// 获取设备性能数据
export const device_performance = (data: any) => {
    return request.post("/v1/cloud_device/device_performance", data);
};

// 获取设备使用日志
export const get_device_log = (data: any) => {
    return request.post("/v1/cloud_device/get_device_log", data);
};

// 获取APP安装历史
export const get_history_list = (data: any) => {
    return request.post("/v1/cloud_device/get_history_list", data);
};

// 获取包列表
export const package_list = (data: any) => {
    return request.post("/v1/cloud_device/package_list", data);
};

// 添加设备
export const add_device = (data: any) => {
    return request.post("/v1/cloud_device/add_device", data);
};

// 编辑设备
export const edit_device = (data: any) => {
    return request.post("/v1/cloud_device/edit_device", data);
};

// 批量安装APP
export const device_install = (data: any) => {
    return request.post("/v1/cloud_device/device_install", data);
};

// APP查看设备
export const app_view_device = (data: any) => {
    return request.post("/v1/cloud_device/app_view_device", data);
};

// 同步 STF 设备池
export const sync_stf_devices = () => {
    return request.post("/v1/cloud_device/sync_stf_devices", {});
};