import request from '/@/utils/request';

/**
 * Web 管理模块 API
 */
export function useWebManagementApi() {
  return {
    // -------------------- 元素菜单 & 元素管理 --------------------

    // 获取元素菜单树（only_menu=true：目录树；false：包含叶子元素）
    element_tree: (data: any) => {
      return request({
        url: '/v1/web_management/web_element/element_tree',
        method: 'POST',
        data,
      });
    },

    // 新增元素菜单
    add_element_menu: (data: any) => {
      return request({
        url: '/v1/web_management/web_element/add_menu',
        method: 'POST',
        data,
      });
    },

    // 编辑元素菜单
    edit_element_menu: (data: any) => {
      return request({
        url: '/v1/web_management/web_element/edit_menu',
        method: 'POST',
        data,
      });
    },

    // 删除元素菜单
    del_element_menu: (data: any) => {
      return request({
        url: '/v1/web_management/web_element/del_menu',
        method: 'POST',
        data,
      });
    },

    // 获取元素列表
    get_element_list: (data: any) => {
      return request({
        url: '/v1/web_management/web_element/get_element_list',
        method: 'POST',
        data,
      });
    },

    // 新增元素
    add_element: (data: any) => {
      return request({
        url: '/v1/web_management/web_element/add_element',
        method: 'POST',
        data,
      });
    },

    // 编辑元素
    edit_element: (data: any) => {
      return request({
        url: '/v1/web_management/web_element/edit_element',
        method: 'POST',
        data,
      });
    },

    // 删除元素
    del_element: (data: any) => {
      return request({
        url: '/v1/web_management/web_element/del_element',
        method: 'POST',
        data,
      });
    },

    // 获取元素选择树（脚本编辑时选择元素）
    get_element_select: (data: any) => {
      return request({
        url: '/v1/web_management/web_element/get_element_select',
        method: 'POST',
        data,
      });
    },

    // -------------------- Web 脚本 & 菜单 --------------------

    // 获取 Web 脚本菜单树
    web_menu: (data: any) => {
      return request({
        url: '/v1/web_management/web/web_menu',
        method: 'POST',
        data,
      });
    },

    // 新增 Web 脚本菜单
    add_web_menu: (data: any) => {
      return request({
        url: '/v1/web_management/web/add_menu',
        method: 'POST',
        data,
      });
    },

    // 删除 Web 脚本菜单
    del_web_menu: (data: any) => {
      return request({
        url: '/v1/web_management/web/del_menu',
        method: 'POST',
        data,
      });
    },

    // 重命名 Web 脚本菜单
    rename_web_menu: (data: any) => {
      return request({
        url: '/v1/web_management/web/rename_menu',
        method: 'POST',
        data,
      });
    },

    // 根据菜单 ID 获取子脚本列表
    menu_script_list: (data: any) => {
      return request({
        url: '/v1/web_management/web/menu_script_list',
        method: 'POST',
        data,
      });
    },

    // 获取单个 Web 脚本
    get_web_script: (data: any) => {
      return request({
        url: '/v1/web_management/web/get_web_script',
        method: 'POST',
        data,
      });
    },

    // 保存 Web 脚本
    save_web_script: (data: any) => {
      return request({
        url: '/v1/web_management/web/save_script',
        method: 'POST',
        data,
      });
    },

    // 导入元素脚本（从文件生成脚本）
    input_element: (data: any) => {
      return request({
        url: '/v1/web_management/web/input_element',
        method: 'POST',
        data,
      });
    },

    // 获取全部脚本菜单列表
    get_web_script_list: (data: any) => {
      return request({
        url: '/v1/web_management/web/get_script_list',
        method: 'POST',
        data,
      });
    },

    // Web 脚本集列表
    web_group_list: (data: any) => {
      return request({
        url: '/v1/web_management/web/web_group_list',
        method: 'POST',
        data,
      });
    },

    // 新增 Web 脚本集
    add_web_group: (data: any) => {
      return request({
        url: '/v1/web_management/web/add_web_group',
        method: 'POST',
        data,
      });
    },

    // 编辑 Web 脚本集
    edit_web_group: (data: any) => {
      return request({
        url: '/v1/web_management/web/edit_web_group',
        method: 'POST',
        data,
      });
    },

    // 删除 Web 脚本集
    del_web_group: (data: any) => {
      return request({
        url: '/v1/web_management/web/del_web_group',
        method: 'POST',
        data,
      });
    },

    // 获取全部 Web 脚本集（选择器）
    web_group_select: (data: any) => {
      return request({
        url: '/v1/web_management/web/web_group_select',
        method: 'POST',
        data,
      });
    },

    // 场景编辑时根据脚本树选择脚本
    group_add_script: (data: any) => {
      return request({
        url: '/v1/web_management/web/group_add_script',
        method: 'POST',
        data,
      });
    },

    // -------------------- Web 执行 & 结果 --------------------

    // 执行 Web 脚本
    run_web_script: (data: any) => {
      return request({
        url: '/v1/web_management/web/run_web_script',
        method: 'POST',
        data,
      });
    },

    // 停止 Web 执行进程
    stop_web_script: (data: any) => {
      return request({
        url: '/v1/web_management/web/stop_web_script',
        method: 'POST',
        data,
      });
    },

    // 停止一次 Web 执行（按 result_id 停止并更新状态）
    stop_web_result: (data: any) => {
      return request({
        url: '/v1/web_management/web/stop_web_result',
        method: 'POST',
        data,
      });
    },

    // 删除一次 Web 执行记录（按 result_id，必要时先停止进程）
    del_web_result: (data: any) => {
      return request({
        url: '/v1/web_management/web/del_web_result',
        method: 'POST',
        data,
      });
    },

    // 获取单次执行的步骤结果
    get_web_result: (data: any) => {
      return request({
        url: '/v1/web_management/web/get_web_result',
        method: 'POST',
        data,
      });
    },

    // 获取执行日志（按浏览器）
    get_web_result_log: (data: any) => {
      return request({
        url: '/v1/web_management/web/get_web_result_log',
        method: 'POST',
        data,
      });
    },

    // 获取 Web 结果列表（任务历史）
    get_web_result_list: (data: any) => {
      return request({
        url: '/v1/web_management/web/get_web_result_list',
        method: 'POST',
        data,
      });
    },

    // 获取执行汇总报告
    get_web_result_report: (data: any) => {
      return request({
        url: '/v1/web_management/web/get_web_result_report',
        method: 'POST',
        data,
      });
    },

    // 获取单个脚本在某浏览器下的执行详情
    get_web_result_detail: (data: any) => {
      return request({
        url: '/v1/web_management/web/get_web_result_detail',
        method: 'POST',
        data,
      });
    },
  };
}

