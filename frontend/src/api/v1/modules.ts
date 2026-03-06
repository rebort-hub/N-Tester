/**
 * 模块管理API接口
 */
import request from '/@/utils/request';

/**
 * 获取模块列表
 */
export function getModuleList(params: {
	project_id: number;
	page?: number;
	page_size?: number;
	name?: string;
	parent_id?: number;
	include_children?: boolean;
}) {
	return request({
		url: '/v1/testcases/modules',
		method: 'get',
		params,
	});
}

/**
 * 获取项目的模块树形结构
 */
export function getModuleTree(projectId: number) {
	return request({
		url: `/v1/testcases/modules/tree/${projectId}`,
		method: 'get',
	});
}

/**
 * 获取模块详情
 */
export function getModuleDetail(moduleId: number) {
	return request({
		url: `/v1/testcases/modules/${moduleId}`,
		method: 'get',
	});
}

/**
 * 创建模块
 */
export function createModule(data: {
	project_id: number;
	name: string;
	description?: string;
	parent_id?: number;
	sort_order?: number;
}) {
	return request({
		url: '/v1/testcases/modules',
		method: 'post',
		data,
	});
}

/**
 * 更新模块
 */
export function updateModule(moduleId: number, data: {
	name?: string;
	description?: string;
	parent_id?: number;
	sort_order?: number;
}) {
	return request({
		url: `/v1/testcases/modules/${moduleId}`,
		method: 'put',
		data,
	});
}

/**
 * 删除模块
 */
export function deleteModule(moduleId: number) {
	return request({
		url: `/v1/testcases/modules/${moduleId}`,
		method: 'delete',
	});
}

/**
 * 移动模块
 */
export function moveModule(moduleId: number, targetParentId?: number) {
	return request({
		url: `/v1/testcases/modules/${moduleId}/move`,
		method: 'put',
		params: {
			target_parent_id: targetParentId
		}
	});
}

/**
 * 导出模块
 */
export function exportModules(params: {
	project_id: number;
	module_ids?: number[];
	include_testcases?: boolean;
}) {
	return request({
		url: '/v1/testcases/modules/export',
		method: 'post',
		params: params,  
	});
}

/**
 * 导入模块
 */
export function importModules(data: {
	project_id: number;
	modules: any[];
	override?: boolean;
}) {
	return request({
		url: '/v1/testcases/modules/import',
		method: 'post',
		data,
	});
}