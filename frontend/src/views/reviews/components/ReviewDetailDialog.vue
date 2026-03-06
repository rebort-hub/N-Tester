<template>
	<el-dialog
		v-model="visible"
		title="评审详情"
		width="900px"
		:before-close="handleClose"
	>
		<div v-loading="loading" class="review-detail">
			<el-descriptions :column="2" border>
				<el-descriptions-item label="评审标题" :span="2">
					<span class="review-title">{{ reviewDetail?.title }}</span>
				</el-descriptions-item>
				<el-descriptions-item label="项目ID">
					{{ reviewDetail?.project_id }}
				</el-descriptions-item>
				<el-descriptions-item label="状态">
					<el-tag :type="getStatusType(reviewDetail?.status)">
						{{ getStatusText(reviewDetail?.status) }}
					</el-tag>
				</el-descriptions-item>
				<el-descriptions-item label="优先级">
					<el-tag :type="getPriorityType(reviewDetail?.priority)">
						{{ getPriorityText(reviewDetail?.priority) }}
					</el-tag>
				</el-descriptions-item>
				<el-descriptions-item label="截止日期">
					<span v-if="reviewDetail?.deadline">{{ formatDateTime(reviewDetail.deadline) }}</span>
					<span v-else>-</span>
				</el-descriptions-item>
				<el-descriptions-item label="创建人">
					{{ reviewDetail?.creator_name || '未知用户' }}
				</el-descriptions-item>
				<el-descriptions-item label="创建时间">
					{{ formatDateTime(reviewDetail?.creation_date) }}
				</el-descriptions-item>
				<el-descriptions-item label="更新时间">
					{{ formatDateTime(reviewDetail?.updation_date) }}
				</el-descriptions-item>
				<el-descriptions-item label="完成时间">
					<span v-if="reviewDetail?.completed_at">{{ formatDateTime(reviewDetail.completed_at) }}</span>
					<span v-else>-</span>
				</el-descriptions-item>
				<el-descriptions-item label="评审描述" :span="2">
					<div class="review-description">
						{{ reviewDetail?.description || '暂无描述' }}
					</div>
				</el-descriptions-item>
			</el-descriptions>

			<!-- 统计信息 -->
			<div class="statistics-section">
				<h3>统计信息</h3>
				<el-row :gutter="20">
					<el-col :span="6">
						<el-statistic title="测试用例数" :value="reviewDetail?.test_case_count || 0" />
					</el-col>
					<el-col :span="6">
						<el-statistic title="评审人数" :value="reviewDetail?.reviewer_count || 0" />
					</el-col>
					<el-col :span="6">
						<el-statistic title="评论数量" :value="reviewDetail?.comment_count || 0" />
					</el-col>
					<el-col :span="6">
						<el-statistic title="完成进度" :value="reviewDetail?.progress || 0" suffix="%" />
					</el-col>
				</el-row>
			</div>

			<!-- 操作按钮 -->
			<div class="action-section">
				<h3>快速操作</h3>
				<el-space>
					<el-button type="primary" @click="editReview">
						<el-icon><Edit /></el-icon>
						编辑评审
					</el-button>
					<el-button @click="viewComments">
						<el-icon><ChatDotRound /></el-icon>
						查看评论
					</el-button>
					<el-button @click="viewTestCases">
						<el-icon><Document /></el-icon>
						查看用例
					</el-button>
					<el-button @click="viewReviewers">
						<el-icon><User /></el-icon>
						查看评审人
					</el-button>
				</el-space>
			</div>
		</div>

		<template #footer>
			<div class="dialog-footer">
				<el-button @click="handleClose">关闭</el-button>
			</div>
		</template>
	</el-dialog>

	<!-- 测试用例对话框 -->
	<el-dialog
		v-model="showTestCasesDialog"
		title="关联测试用例"
		width="800px"
	>
		<div class="test-cases-container">
			<el-table v-loading="testCasesLoading" :data="testCases" stripe height="400">
				<el-table-column prop="id" label="ID" width="80" />
				<el-table-column prop="title" label="用例标题" min-width="200" />
				<el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
				<el-table-column prop="priority" label="优先级" width="100">
					<template #default="{ row }">
						<el-tag :type="getPriorityType(row.priority)">
							{{ getPriorityText(row.priority) }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="module_id" label="模块ID" width="100" />
			</el-table>
			<div v-if="!testCasesLoading && testCases.length === 0" class="empty-data">
				暂无关联的测试用例
			</div>
		</div>
	</el-dialog>

	<!-- 评审人对话框 -->
	<el-dialog
		v-model="showReviewersDialog"
		title="评审人员"
		width="700px"
	>
		<el-table v-loading="reviewersLoading" :data="reviewers" stripe>
			<el-table-column prop="name" label="姓名" width="120" />
			<el-table-column prop="username" label="用户名" width="120" />
			<el-table-column prop="status" label="状态" width="100">
				<template #default="{ row }">
					<el-tag :type="getReviewerStatusType(row.status)">
						{{ getReviewerStatusText(row.status) }}
					</el-tag>
				</template>
			</el-table-column>
			<el-table-column prop="comment" label="评审意见" min-width="200" show-overflow-tooltip />
			<el-table-column prop="reviewed_at" label="评审时间" width="160">
				<template #default="{ row }">
					<span v-if="row.reviewed_at">{{ formatDateTime(row.reviewed_at) }}</span>
					<span v-else>-</span>
				</template>
			</el-table-column>
		</el-table>
		<div v-if="!reviewersLoading && reviewers.length === 0" class="empty-data">
			暂无评审人员
		</div>
	</el-dialog>

	<!-- 评论对话框 -->
	<el-dialog
		v-model="showCommentsDialog"
		title="评审意见"
		width="900px"
	>
		<el-table v-loading="commentsLoading" :data="comments" stripe>
			<el-table-column prop="test_case_title" label="测试用例" min-width="200" show-overflow-tooltip />
			<el-table-column prop="author_name" label="评审人" width="120" />
			<el-table-column prop="result" label="评审结果" width="100">
				<template #default="{ row }">
					<el-tag :type="getResultType(row.result)">
						{{ getResultText(row.result) }}
					</el-tag>
				</template>
			</el-table-column>
			<el-table-column prop="content" label="评审意见" min-width="300" show-overflow-tooltip />
			<el-table-column prop="created_at" label="评审时间" width="160">
				<template #default="{ row }">
					{{ formatDateTime(row.created_at) }}
				</template>
			</el-table-column>
		</el-table>
		<div v-if="!commentsLoading && comments.length === 0" class="empty-data">
			暂无评审意见
		</div>
	</el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { ElMessage, ElDialog } from 'element-plus';
import { Edit, ChatDotRound, Document, User } from '@element-plus/icons-vue';
import { 
	getReviewDetail, 
	getReviewTestCases, 
	getReviewReviewers, 
	getReviewComments,
	type Review 
} from '/@/api/v1/reviews';

// Props
interface Props {
	modelValue: boolean;
	reviewId?: number | null;
}

// Emits
interface Emits {
	(e: 'update:modelValue', value: boolean): void;
	(e: 'edit', review: Review): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// 响应式数据
const visible = ref(false);
const loading = ref(false);
const reviewDetail = ref<Review | null>(null);

// 子对话框状态
const showTestCasesDialog = ref(false);
const showReviewersDialog = ref(false);
const showCommentsDialog = ref(false);

// 子对话框数据
const testCases = ref<any[]>([]);
const reviewers = ref<any[]>([]);
const comments = ref<any[]>([]);
const testCasesLoading = ref(false);
const reviewersLoading = ref(false);
const commentsLoading = ref(false);

// 监听 modelValue 变化
watch(
	() => props.modelValue,
	(val) => {
		visible.value = val;
		if (val && props.reviewId) {
			loadReviewDetail();
		}
	}
);

// 监听 visible 变化
watch(visible, (val) => {
	emit('update:modelValue', val);
});

// 加载评审详情
const loadReviewDetail = async () => {
	if (!props.reviewId) return;
	
	loading.value = true;
	try {
		const response = await getReviewDetail(props.reviewId);
		if (response.code === 200) {
			reviewDetail.value = response.data;
		}
	} catch (error) {
		console.error('加载评审详情失败:', error);
		ElMessage.error('加载评审详情失败');
	} finally {
		loading.value = false;
	}
};

// 处理关闭
const handleClose = () => {
	visible.value = false;
	reviewDetail.value = null;
};

// 编辑评审
const editReview = () => {
	if (reviewDetail.value) {
		emit('edit', reviewDetail.value);
		handleClose();
	}
};

// 查看评论
const viewComments = async () => {
	if (!props.reviewId) return;
	
	showCommentsDialog.value = true;
	commentsLoading.value = true;
	
	try {
		const response = await getReviewComments(props.reviewId, { page: 1, page_size: 100 });
		if (response.code === 200) {
			comments.value = response.data.rows || [];
		}
	} catch (error) {
		console.error('加载评论失败:', error);
		ElMessage.error('加载评论失败');
	} finally {
		commentsLoading.value = false;
	}
};

// 查看测试用例
const viewTestCases = async () => {
	if (!props.reviewId) return;
	
	showTestCasesDialog.value = true;
	testCasesLoading.value = true;
	
	try {
		const response = await getReviewTestCases(props.reviewId);
		if (response.code === 200) {
			testCases.value = response.data || [];
		}
	} catch (error) {
		console.error('加载测试用例失败:', error);
		ElMessage.error('加载测试用例失败');
	} finally {
		testCasesLoading.value = false;
	}
};

// 查看评审人
const viewReviewers = async () => {
	if (!props.reviewId) return;
	
	showReviewersDialog.value = true;
	reviewersLoading.value = true;
	
	try {
		const response = await getReviewReviewers(props.reviewId);
		if (response.code === 200) {
			reviewers.value = response.data || [];
		}
	} catch (error) {
		console.error('加载评审人失败:', error);
		ElMessage.error('加载评审人失败');
	} finally {
		reviewersLoading.value = false;
	}
};

// 获取状态类型
const getStatusType = (status?: string) => {
	const types: Record<string, string> = {
		pending: 'info',
		in_progress: 'warning',
		completed: 'success',
		cancelled: 'danger',
	};
	return types[status || ''] || 'info';
};

// 获取状态文本
const getStatusText = (status?: string) => {
	const texts: Record<string, string> = {
		pending: '待开始',
		in_progress: '进行中',
		completed: '已完成',
		cancelled: '已取消',
	};
	return texts[status || ''] || status || '';
};

// 获取优先级类型
const getPriorityType = (priority?: string) => {
	const types: Record<string, string> = {
		low: 'info',
		medium: '',
		high: 'warning',
		urgent: 'danger',
	};
	return types[priority || ''] || '';
};

// 获取优先级文本
const getPriorityText = (priority?: string) => {
	const texts: Record<string, string> = {
		low: '低',
		medium: '中',
		high: '高',
		urgent: '紧急',
	};
	return texts[priority || ''] || priority || '';
};

// 格式化日期时间
const formatDateTime = (date?: string) => {
	if (!date) return '-';
	const d = new Date(date);
	const year = d.getFullYear();
	const month = String(d.getMonth() + 1).padStart(2, '0');
	const day = String(d.getDate()).padStart(2, '0');
	const hours = String(d.getHours()).padStart(2, '0');
	const minutes = String(d.getMinutes()).padStart(2, '0');
	const seconds = String(d.getSeconds()).padStart(2, '0');
	return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
};

// 获取评审人状态类型
const getReviewerStatusType = (status?: string) => {
	const types: Record<string, string> = {
		pending: 'info',
		in_progress: 'warning',
		completed: 'success',
		rejected: 'danger',
	};
	return types[status || ''] || 'info';
};

// 获取评审人状态文本
const getReviewerStatusText = (status?: string) => {
	const texts: Record<string, string> = {
		pending: '待评审',
		in_progress: '评审中',
		completed: '已完成',
		rejected: '已拒绝',
	};
	return texts[status || ''] || status || '';
};

// 获取评论类型
const getCommentType = (type?: string) => {
	const types: Record<string, string> = {
		general: '',
		suggestion: 'warning',
		issue: 'danger',
		question: 'info',
	};
	return types[type || ''] || '';
};

// 获取评论文本
const getCommentText = (type?: string) => {
	const texts: Record<string, string> = {
		general: '一般',
		suggestion: '建议',
		issue: '问题',
		question: '疑问',
		review_result: '评审结果',
	};
	return texts[type || ''] || type || '';
};

// 获取评审结果类型
const getResultType = (result?: string) => {
	const types: Record<string, string> = {
		pass: 'success',
		fail: 'danger',
		pending: 'warning',
		modify: 'warning',
		approved: 'success',
		rejected: 'danger',
	};
	return types[result || ''] || '';
};

// 获取评审结果文本
const getResultText = (result?: string) => {
	const texts: Record<string, string> = {
		pass: '通过',
		fail: '不通过',
		pending: '待定',
		modify: '需修改',
		approved: '通过',
		rejected: '不通过',
	};
	return texts[result || ''] || result || '';
};
</script>

<style scoped>
.review-detail {
	padding: 20px 0;
}

.review-title {
	font-size: 16px;
	font-weight: 600;
	color: var(--el-text-color-primary, #303133);
}

.review-description {
	line-height: 1.6;
	color: var(--el-text-color-regular, #606266);
	white-space: pre-wrap;
	word-break: break-word;
}

/* 深色主题适配 */
html.dark .review-title {
	color: #e5eaf3;
}

html.dark .review-description {
	color: #cfd3dc;
}

[data-theme="dark"] .review-title {
	color: #e5eaf3;
}

[data-theme="dark"] .review-description {
	color: #cfd3dc;
}

.statistics-section {
	margin-top: 30px;
	padding: 20px;
	background: var(--el-bg-color-page, #f8f9fa);
	border: 1px solid var(--el-border-color-light, #e4e7ed);
	border-radius: 8px;
}

.statistics-section h3 {
	margin: 0 0 20px 0;
	font-size: 16px;
	color: var(--el-text-color-primary, #303133);
}

.action-section {
	margin-top: 30px;
	padding: 20px;
	background: var(--el-bg-color-page, #f8f9fa);
	border: 1px solid var(--el-border-color-light, #e4e7ed);
	border-radius: 8px;
}

.action-section h3 {
	margin: 0 0 20px 0;
	font-size: 16px;
	color: var(--el-text-color-primary, #303133);
}

/* 深色主题适配 */
html.dark .statistics-section,
html.dark .action-section {
	background: #1d1e1f;
	border-color: #414243;
}

html.dark .statistics-section h3,
html.dark .action-section h3 {
	color: #e5eaf3;
}

/* 如果使用data-theme属性 */
[data-theme="dark"] .statistics-section,
[data-theme="dark"] .action-section {
	background: #1d1e1f;
	border-color: #414243;
}

[data-theme="dark"] .statistics-section h3,
[data-theme="dark"] .action-section h3 {
	color: #e5eaf3;
}

.dialog-footer {
	text-align: right;
}

:deep(.el-descriptions__label) {
	font-weight: 600;
}

:deep(.el-statistic__content) {
	font-size: 24px;
}

:deep(.el-statistic__title) {
	font-size: 14px;
	color: var(--el-text-color-regular, #909399);
}

.empty-data {
	text-align: center;
	padding: 40px 0;
	color: var(--el-text-color-placeholder, #909399);
	font-size: 14px;
}

/* 深色主题下的统计标题颜色 */
html.dark :deep(.el-statistic__title) {
	color: #a3a6ad;
}

html.dark .empty-data {
	color: #73767a;
}

[data-theme="dark"] :deep(.el-statistic__title) {
	color: #a3a6ad;
}

[data-theme="dark"] .empty-data {
	color: #73767a;
}

.test-cases-container {
	max-height: 450px;
	overflow-y: auto;
}

.test-cases-container .el-table {
	border-radius: 4px;
}

.test-cases-container .empty-data {
	text-align: center;
	padding: 40px 0;
	color: var(--el-text-color-placeholder, #909399);
	font-size: 14px;
}
</style>