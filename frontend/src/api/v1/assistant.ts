/**
 * AI助手模块API接口
 */
import request from '/@/utils/request';

// ========== AI助手配置相关接口 ==========

/**
 * 获取助手配置列表
 */
export function getConfigList(params: {
	page?: number;
	page_size?: number;
}) {
	return request({
		url: '/v1/assistant/configs',
		method: 'get',
		params,
	});
}

/**
 * 获取助手配置详情
 */
export function getConfigDetail(id: number) {
	return request({
		url: `/v1/assistant/configs/${id}`,
		method: 'get',
	});
}

/**
 * 创建助手配置
 */
export function createConfig(data: {
	name: string;
	dify_api_key: string;
	dify_base_url: string;
	assistant_type?: string;
}) {
	return request({
		url: '/v1/assistant/configs',
		method: 'post',
		data,
	});
}

/**
 * 更新助手配置
 */
export function updateConfig(id: number, data: {
	name?: string;
	dify_api_key?: string;
	dify_base_url?: string;
	assistant_type?: string;
	is_active?: boolean;
}) {
	return request({
		url: `/v1/assistant/configs/${id}`,
		method: 'put',
		data,
	});
}

/**
 * 删除助手配置
 */
export function deleteConfig(id: number) {
	return request({
		url: `/v1/assistant/configs/${id}`,
		method: 'delete',
	});
}

// ========== 对话相关接口 ==========

/**
 * 获取对话列表
 */
export function getConversationList(params: {
	page?: number;
	page_size?: number;
	assistant_config_id?: number;
}) {
	return request({
		url: '/v1/assistant/conversations',
		method: 'get',
		params,
	});
}

/**
 * 获取对话详情
 */
export function getConversationDetail(id: number) {
	return request({
		url: `/v1/assistant/conversations/${id}`,
		method: 'get',
	});
}

/**
 * 创建对话
 */
export function createConversation(data: {
	assistant_config_id: number;
	title?: string;
}) {
	return request({
		url: '/v1/assistant/conversations',
		method: 'post',
		data,
	});
}

/**
 * 更新对话
 */
export function updateConversation(id: number, data: {
	title?: string;
}) {
	return request({
		url: `/v1/assistant/conversations/${id}`,
		method: 'put',
		data,
	});
}

/**
 * 删除对话
 */
export function deleteConversation(id: number) {
	return request({
		url: `/v1/assistant/conversations/${id}`,
		method: 'delete',
	});
}

// ========== 消息相关接口 ==========

/**
 * 获取对话消息列表
 */
export function getMessageList(conversationId: number, params?: {
	page?: number;
	page_size?: number;
}) {
	return request({
		url: `/v1/assistant/conversations/${conversationId}/messages`,
		method: 'get',
		params,
	});
}

/**
 * 获取对话消息列表 (别名函数，保持兼容性)
 */
export function getConversationMessages(conversationId: number, params?: {
	page?: number;
	page_size?: number;
}) {
	return getMessageList(conversationId, params);
}

/**
 * 发送消息
 */
export function sendMessage(conversationId: number, data: {
	content: string;
}) {
	return request({
		url: `/v1/assistant/conversations/${conversationId}/messages`,
		method: 'post',
		data,
	});
}

/**
 * 与Dify聊天
 */
export function chatWithDify(data: {
	assistant_config_id: number;
	conversation_id?: number;
	message: string;
	user_id?: number;
}) {
	return request({
		url: '/v1/assistant/chat',
		method: 'post',
		data,
	});
}

// ========== 统计相关接口 ==========

/**
 * 获取助手统计信息
 */
export function getStatistics() {
	return request({
		url: '/v1/assistant/statistics',
		method: 'get',
	});
}

// ========== 类型定义 ==========

/**
 * 助手类型
 */
export type AssistantType = 'chatbot' | 'workflow' | 'agent';

/**
 * 消息角色
 */
export type MessageRole = 'user' | 'assistant';

/**
 * AI助手配置
 */
export interface AssistantConfig {
	id: number;
	name: string;
	dify_api_key: string;
	dify_base_url: string;
	assistant_type: AssistantType;
	is_active: boolean;
	created_by: number;
	creation_date: string;
	updation_date: string;
}

/**
 * 对话
 */
export interface Conversation {
	id: number;
	user_id: number;
	assistant_config_id: number;
	conversation_id?: string;
	title?: string;
	creation_date: string;
	updation_date: string;
	assistant_config?: AssistantConfig;
	message_count?: number;
	last_message?: string;
	last_message_time?: string;
}

/**
 * 消息
 */
export interface Message {
	id: number;
	conversation_id: number;
	role: MessageRole;
	content: string;
	created_at: string;
}

/**
 * 聊天响应
 */
export interface ChatResponse {
	message: string;
	conversation_id?: string;
	message_id?: string;
}

/**
 * 助手统计
 */
export interface AssistantStatistics {
	total_configs: number;
	active_configs: number;
	total_conversations: number;
	total_messages: number;
	type_distribution: Record<string, number>;
	config_type_distribution: Record<string, number>;
	daily_message_count: Array<{date: string, count: number}>;
	config_stats: Array<any>;
	recent_conversations: Conversation[];
	usage_stats: {
		today: number;
		this_week: number;
		this_month: number;
	};
}