/**
 * L-Tester Web 管理模块接口（元素管理 / Web 自动化 / Web 场景 / Web 结果）
 * 对应后端 `app.api.v1.web_management.controller`，统一前缀 `/v1/web_management`
 */
import request from '/@/utils/request'

// -------------------- 元素菜单 & 元素管理 --------------------

// 获取元素菜单树（only_menu=true：目录树；false：包含叶子元素）
export const element_tree = (data: any) =>
  request.post('/v1/web_management/web_element/element_tree', data)

// 新增元素菜单
export const add_element_menu = (data: any) =>
  request.post('/v1/web_management/web_element/add_menu', data)

// 编辑元素菜单
export const edit_element_menu = (data: any) =>
  request.post('/v1/web_management/web_element/edit_menu', data)

// 删除元素菜单
export const del_element_menu = (data: any) =>
  request.post('/v1/web_management/web_element/del_menu', data)

// 获取元素列表
export const get_element_list = (data: any) =>
  request.post('/v1/web_management/web_element/get_element_list', data)

// 新增元素
export const add_element = (data: any) =>
  request.post('/v1/web_management/web_element/add_element', data)

// 编辑元素
export const edit_element = (data: any) =>
  request.post('/v1/web_management/web_element/edit_element', data)

// 删除元素
export const del_element = (data: any) =>
  request.post('/v1/web_management/web_element/del_element', data)

// 获取元素选择树（脚本编辑时选择元素）
export const get_element_select = (data: any) =>
  request.post('/v1/web_management/web_element/get_element_select', data)

// -------------------- Web 脚本 & 菜单 --------------------

// 获取 Web 脚本菜单树
export const web_menu = (data: any) =>
  request.post('/v1/web_management/web/web_menu', data)

// 新增 Web 脚本菜单
export const add_web_menu = (data: any) =>
  request.post('/v1/web_management/web/add_menu', data)

// 删除 Web 脚本菜单
export const del_web_menu = (data: any) =>
  request.post('/v1/web_management/web/del_menu', data)

// 重命名 Web 脚本菜单
export const rename_web_menu = (data: any) =>
  request.post('/v1/web_management/web/rename_menu', data)

// 根据菜单 ID 获取子脚本列表
export const menu_script_list = (data: any) =>
  request.post('/v1/web_management/web/menu_script_list', data)

// 获取单个 Web 脚本
export const get_web_script = (data: any) =>
  request.post('/v1/web_management/web/get_web_script', data)

// 保存 Web 脚本
export const save_web_script = (data: any) =>
  request.post('/v1/web_management/web/save_script', data)

// 导入元素脚本（从文件生成脚本）
export const input_element = (data: any) =>
  request.post('/v1/web_management/web/input_element', data)

// 获取全部脚本菜单列表
export const get_web_script_list = (data: any) =>
  request.post('/v1/web_management/web/get_script_list', data)

// Web 脚本集列表
export const web_group_list = (data: any) =>
  request.post('/v1/web_management/web/web_group_list', data)

// 新增 Web 脚本集
export const add_web_group = (data: any) =>
  request.post('/v1/web_management/web/add_web_group', data)

// 编辑 Web 脚本集
export const edit_web_group = (data: any) =>
  request.post('/v1/web_management/web/edit_web_group', data)

// 删除 Web 脚本集
export const del_web_group = (data: any) =>
  request.post('/v1/web_management/web/del_web_group', data)

// 获取全部 Web 脚本集（选择器）
export const web_group_select = (data: any) =>
  request.post('/v1/web_management/web/web_group_select', data)

// 场景编辑时根据脚本树选择脚本
export const group_add_script = (data: any) =>
  request.post('/v1/web_management/web/group_add_script', data)

// -------------------- Web 执行 & 结果 --------------------

// 执行 Web 脚本
export const run_web_script = (data: any) =>
  request.post('/v1/web_management/web/run_web_script', data)

// 停止 Web 执行进程
export const stop_web_script = (data: any) =>
  request.post('/v1/web_management/web/stop_web_script', data)

// 获取单次执行的步骤结果
export const get_web_result = (data: any) =>
  request.post('/v1/web_management/web/get_web_result', data)

// 获取执行日志（按浏览器）
export const get_web_result_log = (data: any) =>
  request.post('/v1/web_management/web/get_web_result_log', data)

// 获取 Web 结果列表（任务历史）
export const get_web_result_list = (data: any) =>
  request.post('/v1/web_management/web/get_web_result_list', data)

// 获取执行汇总报告
export const get_web_result_report = (data: any) =>
  request.post('/v1/web_management/web/get_web_result_report', data)

// 获取单个脚本在某浏览器下的执行详情
export const get_web_result_detail = (data: any) =>
  request.post('/v1/web_management/web/get_web_result_detail', data)

