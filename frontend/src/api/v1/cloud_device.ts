/**
 * 云真机模块接口
 */
import request from '/@/utils/request';

const postCloudDevice = <T = any>(url: string, data?: any) =>
  request<T>({
    url,
    method: 'post',
    data,
  });

export function useCloudDeviceApi() {
  return {
    // 获取设备列表
    device_list: (data: any) => postCloudDevice('/v1/cloud_device/device_list', data),
    // 获取设备详细信息列表
    device_info_list: (data: any) => postCloudDevice('/v1/cloud_device/device_info_list', data),
    // 使用设备（获取远程控制链接）
    use_device: (data: any) => postCloudDevice('/v1/cloud_device/use_device', data),
    // 释放设备
    stop_device: (data: any) => postCloudDevice('/v1/cloud_device/stop_device', data),
    // 安装APP
    device_install_app: (data: any) => postCloudDevice('/v1/cloud_device/device_install_app', data),
    // 直接安装APP（从历史记录）
    direct_install_app: (data: any) => postCloudDevice('/v1/cloud_device/direct_install_app', data),
    // 批量卸载APP
    device_uninstall: (data: any) => postCloudDevice('/v1/cloud_device/device_uninstall', data),
    // 获取设备性能数据
    device_performance: (data: any) => postCloudDevice('/v1/cloud_device/device_performance', data),
    // 获取设备使用日志
    get_device_log: (data: any) => postCloudDevice('/v1/cloud_device/get_device_log', data),
    // 获取APP安装历史
    get_history_list: (data: any) => postCloudDevice('/v1/cloud_device/get_history_list', data),
    // 获取包列表
    package_list: (data: any) => postCloudDevice('/v1/cloud_device/package_list', data),
    // 添加设备
    add_device: (data: any) => postCloudDevice('/v1/cloud_device/add_device', data),
    // 编辑设备
    edit_device: (data: any) => postCloudDevice('/v1/cloud_device/edit_device', data),
    // 批量安装APP
    device_install: (data: any) => postCloudDevice('/v1/cloud_device/device_install', data),
    // APP查看设备
    app_view_device: (data: any) => postCloudDevice('/v1/cloud_device/app_view_device', data),
    // 同步 STF 设备池
    sync_stf_devices: () => postCloudDevice('/v1/cloud_device/sync_stf_devices', {}),
  };
}

export const cloudDeviceApi = useCloudDeviceApi();
export const {
  device_list,
  device_info_list,
  use_device,
  stop_device,
  device_install_app,
  direct_install_app,
  device_uninstall,
  device_performance,
  get_device_log,
  get_history_list,
  package_list,
  add_device,
  edit_device,
  device_install,
  app_view_device,
  sync_stf_devices,
} = cloudDeviceApi;