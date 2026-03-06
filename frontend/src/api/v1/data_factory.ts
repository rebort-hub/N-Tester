/**
 * 数据工厂API接口
 */
import request from '/@/utils/request';

// ========== 数据工厂工具相关接口 ==========

/**
 * 获取工具分类和工具列表
 */
export function getToolCategories() {
	return request({
		url: '/v1/data-factory/categories',
		method: 'get',
	});
}

/**
 * 执行工具
 */
export function executeTool(data: {
	tool_name: string;
	tool_category: string;
	tool_scenario: string;
	input_data: Record<string, any>;
	is_saved?: boolean;
	tags?: string[];
}) {
	return request({
		url: '/v1/data-factory/execute',
		method: 'post',
		data,
	});
}

/**
 * 批量生成数据
 */
export function batchGenerate(data: {
	tool_name: string;
	tool_category: string;
	tool_scenario: string;
	count: number;
	input_data: Record<string, any>;
	is_saved?: boolean;
	tags?: string[];
}) {
	return request({
		url: '/v1/data-factory/batch-generate',
		method: 'post',
		data,
	});
}

// ========== 工具使用记录相关接口 ==========

/**
 * 获取工具使用记录列表
 */
export function getRecordList(params: {
	page?: number;
	page_size?: number;
	tool_category?: string;
	tool_name?: string;
}) {
	return request({
		url: '/v1/data-factory/records',
		method: 'get',
		params,
	});
}

/**
 * 获取工具使用记录详情
 */
export function getRecordDetail(id: number) {
	return request({
		url: `/v1/data-factory/records/${id}`,
		method: 'get',
	});
}

/**
 * 删除工具使用记录
 */
export function deleteRecord(id: number) {
	return request({
		url: `/v1/data-factory/records/${id}`,
		method: 'delete',
	});
}

/**
 * 批量删除工具使用记录
 */
export function batchDeleteRecords(ids: number[]) {
	return request({
		url: '/v1/data-factory/records/batch-delete',
		method: 'post',
		data: { ids },
	});
}

// ========== 统计相关接口 ==========

/**
 * 获取使用统计
 */
export function getStatistics() {
	return request({
		url: '/v1/data-factory/statistics',
		method: 'get',
	});
}

/**
 * 获取标签列表
 */
export function getTagList() {
	return request({
		url: '/v1/data-factory/tags',
		method: 'get',
	});
}

// ========== 工具相关类型定义 ==========

/**
 * 工具分类
 */
export interface ToolCategory {
	category: string;
	name: string;
	scenario: string;
	icon: string;
	tools: Tool[];
}

/**
 * 工具定义
 */
export interface Tool {
	name: string;
	display_name: string;
	description: string;
	scenario: string;
	icon: string;
}

/**
 * 工具执行结果
 */
export interface ToolExecuteResult {
	result: any;
	record_id?: number;
	created_at?: string;
}

/**
 * 工具使用记录
 */
export interface ToolRecord {
	id: number;
	tool_name: string;
	tool_category: string;
	tool_scenario: string;
	input_data: Record<string, any>;
	output_data: any;
	is_saved: boolean;
	tags: string[];
	creation_date: string;
	updation_date: string;
}

/**
 * 使用统计
 */
export interface Statistics {
	total_records: number;
	category_stats: Record<string, number>;
	scenario_stats: Record<string, number>;
	recent_tools: Array<{
		tool_name: string;
		tool_category_display: string;
		tool_scenario_display: string;
		created_at: string;
	}>;
}

/**
 * 批量生成结果
 */
export interface BatchGenerateResult {
	results: any[];
	count: number;
	tool_name: string;
	tool_category: string;
	success_count: number;
	failed_count: number;
}