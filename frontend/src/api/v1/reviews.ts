/**
 * 用例评审模块API接口
 */
import request from '/@/utils/request';

// ========== 评审相关接口 ==========

/**
 * 获取评审列表
 */
export function getReviewList(params: {
	page?: number;
	page_size?: number;
	project_id?: number;
	status?: string;
	priority?: string;
}) {
	return request({
		url: '/v1/reviews',
		method: 'get',
		params,
	});
}

/**
 * 获取评审详情
 */
export function getReviewDetail(id: number) {
	return request({
		url: `/v1/reviews/${id}`,
		method: 'get',
	});
}

/**
 * 创建评审
 */
export function createReview(data: {
	project_id: number;
	title: string;
	description?: string;
	priority?: string;
	deadline?: string;
	template_id?: number;
	test_case_ids: number[];
	reviewer_ids: number[];
}) {
	return request({
		url: '/v1/reviews',
		method: 'post',
		data,
	});
}

/**
 * 更新评审
 */
export function updateReview(id: number, data: {
	title?: string;
	description?: string;
	priority?: string;
	deadline?: string;
	status?: string;
}) {
	return request({
		url: `/v1/reviews/${id}`,
		method: 'put',
		data,
	});
}

/**
 * 删除评审
 */
export function deleteReview(id: number) {
	return request({
		url: `/v1/reviews/${id}`,
		method: 'delete',
	});
}

/**
 * 获取评审统计
 */
export function getReviewStatistics(params: { project_id?: number }) {
	return request({
		url: '/v1/reviews/statistics',
		method: 'get',
		params,
	});
}

/**
 * 获取我的评审任务
 */
export function getMyReviewTasks(params: {
	page?: number;
	page_size?: number;
	status?: string;
	priority?: string;
	keyword?: string;
}) {
	return request({
		url: '/v1/reviews/my-tasks',
		method: 'get',
		params,
	});
}

/**
 * 开始评审任务
 */
export function startReviewTask(reviewId: number) {
	return request({
		url: `/v1/reviews/${reviewId}/start`,
		method: 'post',
	});
}

/**
 * 获取我的评审结果
 */
export function getMyReviewResults(reviewId: number) {
	return request({
		url: `/v1/reviews/${reviewId}/my-results`,
		method: 'get',
	});
}

/**
 * 获取评审结果
 */
export function getReviewResults(reviewId: number, params?: {
	page?: number;
	page_size?: number;
	result?: string;
	keyword?: string;
}) {
	return request({
		url: `/v1/reviews/${reviewId}/results`,
		method: 'get',
		params,
	});
}

/**
 * 保存评审结果
 */
export function saveReviewResult(reviewId: number, testCaseId: number, data: {
	result: string;
	comment?: string;
}) {
	return request({
		url: `/v1/reviews/${reviewId}/testcases/${testCaseId}/review`,
		method: 'post',
		data,
	});
}

/**
 * 完成评审
 */
export function completeReview(reviewId: number) {
	return request({
		url: `/v1/reviews/${reviewId}/complete`,
		method: 'post',
	});
}

/**
 * 获取评审关联的测试用例
 */
export function getReviewTestCases(reviewId: number) {
	return request({
		url: `/v1/reviews/${reviewId}/test-cases`,
		method: 'get',
	});
}

/**
 * 获取评审人员
 */
export function getReviewReviewers(reviewId: number) {
	return request({
		url: `/v1/reviews/${reviewId}/reviewers`,
		method: 'get',
	});
}

/**
 * 获取评审意见列表
 */
export function getReviewComments(reviewId: number, params?: {
	test_case_id?: number;
	is_resolved?: boolean;
	page?: number;
	page_size?: number;
}) {
	return request({
		url: `/v1/reviews/${reviewId}/comments`,
		method: 'get',
		params,
	});
}

// ========== AI评审相关接口 ==========

/**
 * 检查AI评审功能可用性
 */
export function checkAIReviewAvailability(reviewId: number) {
	return request({
		url: `/v1/reviews/${reviewId}/ai-review/availability`,
		method: 'get',
	});
}

/**
 * AI评审单个测试用例
 */
export function aiReviewSingleTestCase(reviewId: number, testCaseData: any) {
	return request({
		url: `/v1/reviews/${reviewId}/ai-review/single`,
		method: 'post',
		data: testCaseData,
	});
}

/**
 * 批量AI评审测试用例
 */
export function aiReviewBatchTestCases(reviewId: number, testCaseIds: number[]) {
	return request({
		url: `/v1/reviews/${reviewId}/ai-review/batch`,
		method: 'post',
		data: { test_case_ids: testCaseIds },
	});
}

/**
 * AI预评审所有测试用例
 */
export function aiPreReviewAllCases(reviewId: number) {
	return request({
		url: `/v1/reviews/my-tasks/${reviewId}/ai-pre-review`,
		method: 'post',
	});
}

/**
 * 获取AI预评审摘要
 */
export function getAIPreReviewSummary(reviewId: number) {
	return request({
		url: `/v1/reviews/my-tasks/${reviewId}/ai-pre-review/summary`,
		method: 'get',
	});
}

// ========== 评审分配相关接口 ==========

/**
 * 分配评审人
 */
export function assignReviewers(reviewId: number, data: {
	reviewer_ids: number[];
}) {
	return request({
		url: `/v1/reviews/${reviewId}/assign`,
		method: 'post',
		data,
	});
}

/**
 * 提交评审结果
 */
export function submitReview(reviewId: number, data: {
	status: string;
	comment?: string;
	checklist_results?: Record<string, any>;
}) {
	return request({
		url: `/v1/reviews/${reviewId}/submit`,
		method: 'post',
		data,
	});
}

// ========== 评审意见相关接口 ==========

/**
 * 添加评审意见
 */
export function addReviewComment(reviewId: number, data: {
	test_case_id?: number;
	comment_type: string;
	content: string;
	step_number?: number;
}) {
	return request({
		url: `/v1/reviews/${reviewId}/comments`,
		method: 'post',
		data,
	});
}

/**
 * 解决评审意见
 */
export function resolveComment(commentId: number) {
	return request({
		url: `/v1/reviews/comments/${commentId}/resolve`,
		method: 'post',
	});
}

// ========== 评审模板相关接口 ==========

/**
 * 获取评审模板列表
 */
export function getTemplateList(params: {
	page?: number;
	page_size?: number;
}) {
	return request({
		url: '/v1/reviews/templates',
		method: 'get',
		params,
	});
}

/**
 * 获取评审模板详情
 */
export function getTemplateDetail(id: number) {
	return request({
		url: `/v1/reviews/templates/${id}`,
		method: 'get',
	});
}

/**
 * 创建评审模板
 */
export function createTemplate(data: {
	name: string;
	description?: string;
	checklist: Record<string, any>;
	project_ids?: number[];
	default_reviewer_ids?: number[];
}) {
	return request({
		url: '/v1/reviews/templates',
		method: 'post',
		data,
	});
}

/**
 * 更新评审模板
 */
export function updateTemplate(id: number, data: {
	name?: string;
	description?: string;
	checklist?: Record<string, any>;
	is_active?: boolean;
}) {
	return request({
		url: `/v1/reviews/templates/${id}`,
		method: 'put',
		data,
	});
}

/**
 * 删除评审模板
 */
export function deleteTemplate(id: number) {
	return request({
		url: `/v1/reviews/templates/${id}`,
		method: 'delete',
	});
}

// ========== 类型定义 ==========

/**
 * 评审状态
 */
export type ReviewStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled';

/**
 * 评审优先级
 */
export type ReviewPriority = 'low' | 'medium' | 'high' | 'urgent';

/**
 * 评审意见类型
 */
export type CommentType = 'general' | 'suggestion' | 'issue' | 'question';

/**
 * 评审信息
 */
export interface Review {
	id: number;
	project_id: number;
	title: string;
	description?: string;
	status: ReviewStatus;
	priority: ReviewPriority;
	deadline?: string;
	template_id?: number;
	creator_id: number;
	completed_at?: string;
	creation_date: string;
	updation_date: string;
	test_cases?: TestCase[];
	reviewers?: Reviewer[];
}

/**
 * 测试用例
 */
export interface TestCase {
	id: number;
	title: string;
	description?: string;
}

/**
 * 评审人
 */
export interface Reviewer {
	id: number;
	username: string;
	nickname?: string;
	status: string;
	comment?: string;
	reviewed_at?: string;
}

/**
 * 评审意见
 */
export interface ReviewComment {
	id: number;
	review_id: number;
	test_case_id?: number;
	author_id: number;
	author_name: string;
	comment_type: CommentType;
	content: string;
	step_number?: number;
	is_resolved: boolean;
	creation_date: string;
}

/**
 * 评审模板
 */
export interface ReviewTemplate {
	id: number;
	name: string;
	description?: string;
	checklist: Record<string, any>;
	is_active: boolean;
	creator_id: number;
	creation_date: string;
}

/**
 * 评审统计
 */
export interface ReviewStatistics {
	total_reviews: number;
	pending_reviews: number;
	in_progress_reviews: number;
	completed_reviews: number;
	cancelled_reviews: number;
	status_distribution: Record<string, number>;
	priority_distribution: Record<string, number>;
	recent_reviews: Review[];
}