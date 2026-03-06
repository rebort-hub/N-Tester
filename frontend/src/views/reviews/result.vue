<template>
	<div class="review-result-container">
		<!-- 选择评审界面 (当没有有效reviewId时显示) -->
		<div v-if="!reviewId" class="review-selection-container">
			<el-card shadow="hover" class="selection-card">
				<div class="selection-header">
					<h2 class="page-title">
						<el-icon><View /></el-icon>
						选择要查看结果的评审
					</h2>
					<p class="page-description">请从下面的列表中选择一个已完成的评审查看结果</p>
				</div>
				
				<div class="selection-content">
					<el-table 
						v-loading="selectionLoading"
						:data="availableReviews" 
						stripe 
						style="width: 100%"
						@row-click="selectReview"
					>
						<el-table-column prop="title" label="评审标题" min-width="200" show-overflow-tooltip />
						<el-table-column prop="priority" label="优先级" width="100">
							<template #default="{ row }">
								<el-tag :type="getPriorityType(row.priority)">
									{{ getPriorityText(row.priority) }}
								</el-tag>
							</template>
						</el-table-column>
						<el-table-column prop="my_status" label="状态" width="100">
							<template #default="{ row }">
								<el-tag :type="getStatusType(row.my_status)">
									{{ getStatusText(row.my_status) }}
								</el-tag>
							</template>
						</el-table-column>
						<el-table-column prop="my_progress" label="进度" width="120">
							<template #default="{ row }">
								<el-progress :percentage="row.my_progress" :stroke-width="6" />
							</template>
						</el-table-column>
						<el-table-column label="操作" width="120" fixed="right">
							<template #default="{ row }">
								<el-button size="small" type="primary" @click.stop="selectReview(row)">
									查看结果
								</el-button>
							</template>
						</el-table-column>
					</el-table>
				</div>
			</el-card>
		</div>

		<!-- 正常的评审结果界面 (当有有效reviewId时显示) -->
		<div v-else>
			<!-- 页面头部 -->
			<el-card shadow="hover" class="page-header-card">
				<div class="page-header">
					<div class="header-left">
						<h2 class="page-title">
							<el-icon><View /></el-icon>
							评审结果 - {{ reviewInfo.title }}
						</h2>
						<p class="page-description">{{ reviewInfo.description }}</p>
					</div>
					<div class="header-right">
						<el-button @click="$router.push('/reviews/my-tasks')">
							<el-icon><ArrowLeft /></el-icon>
							返回任务列表
						</el-button>
						<el-button type="primary" @click="exportResult">
							<el-icon><Download /></el-icon>
							导出结果
						</el-button>
					</div>
				</div>
			</el-card>

		<!-- 评审概览 -->
		<el-row :gutter="20" class="overview-cards">
			<el-col :span="6">
				<el-card shadow="hover" class="stat-card">
					<div class="stat-content">
						<div class="stat-icon total">
							<el-icon><Files /></el-icon>
						</div>
						<div class="stat-info">
							<div class="stat-number">{{ overview.totalCases }}</div>
							<div class="stat-label">总用例数</div>
						</div>
					</div>
				</el-card>
			</el-col>
			<el-col :span="6">
				<el-card shadow="hover" class="stat-card">
					<div class="stat-content">
						<div class="stat-icon pass">
							<el-icon><Check /></el-icon>
						</div>
						<div class="stat-info">
							<div class="stat-number">{{ overview.passedCases }}</div>
							<div class="stat-label">通过</div>
						</div>
					</div>
				</el-card>
			</el-col>
			<el-col :span="6">
				<el-card shadow="hover" class="stat-card">
					<div class="stat-content">
						<div class="stat-icon fail">
							<el-icon><Close /></el-icon>
						</div>
						<div class="stat-info">
							<div class="stat-number">{{ overview.failedCases }}</div>
							<div class="stat-label">不通过</div>
						</div>
					</div>
				</el-card>
			</el-col>
			<el-col :span="6">
				<el-card shadow="hover" class="stat-card">
					<div class="stat-content">
						<div class="stat-icon modify">
							<el-icon><Edit /></el-icon>
						</div>
						<div class="stat-info">
							<div class="stat-number">{{ overview.modifyCases }}</div>
							<div class="stat-label">需修改</div>
						</div>
					</div>
				</el-card>
			</el-col>
		</el-row>

		<!-- 评审进度图表 -->
		<el-card shadow="hover" class="chart-card">
			<div class="card-header">
				<h3>
					<el-icon><PieChart /></el-icon>
					评审结果分布
				</h3>
			</div>
			<div ref="chartContainer" class="chart-container"></div>
		</el-card>

		<!-- 详细结果列表 -->
		<el-card shadow="hover" class="result-list-card">
			<div class="card-header">
				<h3>
					<el-icon><List /></el-icon>
					详细评审结果
				</h3>
				<div class="filter-controls">
					<el-select v-model="filters.result" placeholder="筛选结果" clearable @change="loadResults">
						<el-option label="通过" value="pass" />
						<el-option label="不通过" value="fail" />
						<el-option label="需修改" value="modify" />
					</el-select>
					<el-input
						v-model="filters.keyword"
						placeholder="搜索用例标题"
						@keyup.enter="loadResults"
						style="width: 200px; margin-left: 10px;"
					>
						<template #append>
							<el-button @click="loadResults">
								<el-icon><Search /></el-icon>
							</el-button>
						</template>
					</el-input>
				</div>
			</div>

			<el-table
				v-loading="loading"
				:data="results"
				stripe
				style="width: 100%"
			>
				<el-table-column prop="testCaseTitle" label="测试用例" min-width="200" show-overflow-tooltip />
				<el-table-column prop="result" label="评审结果" width="100">
					<template #default="{ row }">
						<el-tag :type="getResultType(row.result)">
							{{ getResultText(row.result) }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="comment" label="评审意见" min-width="300" show-overflow-tooltip>
					<template #default="{ row }">
						<span v-if="row.comment">{{ row.comment }}</span>
						<span v-else class="no-comment">无意见</span>
					</template>
				</el-table-column>
				<el-table-column prop="reviewedAt" label="评审时间" width="160">
					<template #default="{ row }">
						{{ formatDateTime(row.reviewedAt) }}
					</template>
				</el-table-column>
				<el-table-column label="操作" width="120" fixed="right">
					<template #default="{ row }">
						<el-button size="small" @click="viewCaseDetail(row)">
							查看详情
						</el-button>
					</template>
				</el-table-column>
			</el-table>

			<!-- 分页 -->
			<div class="pagination-container">
				<el-pagination
					v-model:current-page="pagination.page"
					v-model:page-size="pagination.pageSize"
					:total="pagination.total"
					:page-sizes="[10, 20, 50, 100]"
					layout="total, sizes, prev, pager, next, jumper"
					@size-change="loadResults"
					@current-change="loadResults"
				/>
			</div>
		</el-card>

		<!-- 用例详情对话框 -->
		<el-dialog
			v-model="caseDetailVisible"
			title="测试用例详情"
			width="800px"
			:close-on-click-modal="false"
		>
			<div v-if="selectedCase" class="case-detail">
				<div class="case-info">
					<h4>{{ selectedCase.testCaseTitle }}</h4>
					<p v-if="selectedCase.description" class="case-description">
						{{ selectedCase.description }}
					</p>
				</div>

				<div class="review-result-detail">
					<h5>评审结果</h5>
					<div class="result-info">
						<el-tag :type="getResultType(selectedCase.result)" size="large">
							{{ getResultText(selectedCase.result) }}
						</el-tag>
						<span class="review-time">{{ formatDateTime(selectedCase.reviewedAt) }}</span>
					</div>
				</div>

				<div v-if="selectedCase.comment" class="review-comment-detail">
					<h5>评审意见</h5>
					<div class="comment-content">
						{{ selectedCase.comment }}
					</div>
				</div>

				<div v-if="selectedCase.steps && selectedCase.steps.length > 0" class="case-steps">
					<h5>测试步骤</h5>
					<div v-for="step in selectedCase.steps" :key="step.id" class="step-item">
						<div class="step-header">
							<span class="step-number">步骤 {{ step.stepNumber }}</span>
						</div>
						<div class="step-content">
							<p><strong>操作描述:</strong> {{ step.description }}</p>
							<p v-if="step.expectedResult"><strong>期望结果:</strong> {{ step.expectedResult }}</p>
						</div>
					</div>
				</div>
			</div>

			<template #footer>
				<el-button @click="caseDetailVisible = false">关闭</el-button>
			</template>
		</el-dialog>
		</div> <!-- 闭合正常评审结果界面的div -->
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { 
	View, ArrowLeft, Download, Files, Check, Close, Edit, 
	PieChart, List, Search 
} from '@element-plus/icons-vue';
import * as echarts from 'echarts';
import { 
	getReviewDetail, 
	getReviewTestCases,
	getReviewResults,
	getMyReviewTasks
} from '/@/api/v1/reviews';

const route = useRoute();
const router = useRouter();

// 响应式数据
const loading = ref(false);

// 获取并验证 reviewId
const getReviewId = () => {
	// 优先从路由参数获取
	let id = route.params.reviewId as string;
	
	// 如果路由参数没有，尝试从查询参数获取
	if (!id || id === ':reviewId' || id === 'undefined') {
		id = route.query.reviewId as string;
	}
	
	// 验证ID是否有效
	if (!id || isNaN(parseInt(id))) {
		return null;
	}
	return parseInt(id);
};

const reviewId = ref(getReviewId());
const chartContainer = ref<HTMLElement>();

// 选择评审相关数据
const selectionLoading = ref(false);
const availableReviews = ref<any[]>([]);

// 评审信息
const reviewInfo = reactive({
	id: 0,
	title: '',
	description: '',
	status: '',
	priority: '',
	deadline: '',
});

// 概览数据
const overview = reactive({
	totalCases: 0,
	passedCases: 0,
	failedCases: 0,
	modifyCases: 0,
});

// 筛选条件
const filters = reactive({
	result: '',
	keyword: '',
});

// 分页数据
const pagination = reactive({
	page: 1,
	pageSize: 20,
	total: 0,
});

// 结果列表
const results = ref<any[]>([]);

// 用例详情对话框
const caseDetailVisible = ref(false);
const selectedCase = ref<any>(null);

// 加载可用的评审任务
const loadAvailableReviews = async () => {
	selectionLoading.value = true;
	try {
		const response = await getMyReviewTasks({
			page: 1,
			page_size: 50,
			// 评审结果页面显示所有任务，但优先显示已完成的
			status: ''  // 不筛选状态，显示所有任务
		});
		
		if (response.code === 200) {
			// 按状态排序：已完成的在前面
			const allTasks = response.data.rows || [];
			availableReviews.value = allTasks.sort((a, b) => {
				if (a.my_status === 'completed' && b.my_status !== 'completed') return -1;
				if (a.my_status !== 'completed' && b.my_status === 'completed') return 1;
				return 0;
			});
		} else {
			ElMessage.error(response.message || '加载评审任务失败');
		}
	} catch (error) {
		console.error('加载评审任务失败:', error);
		ElMessage.error('加载评审任务失败');
	} finally {
		selectionLoading.value = false;
	}
};

// 选择评审
const selectReview = (review: any) => {
	router.push(`/reviews/result?reviewId=${review.id}`);
};

// 获取优先级类型
const getPriorityType = (priority: string) => {
	const types: Record<string, string> = {
		low: 'info',
		medium: 'warning',
		high: 'danger',
		urgent: 'danger',
	};
	return types[priority] || 'info';
};

// 获取优先级文本
const getPriorityText = (priority: string) => {
	const texts: Record<string, string> = {
		low: '低',
		medium: '中',
		high: '高',
		urgent: '紧急',
	};
	return texts[priority] || priority;
};

// 获取状态类型
const getStatusType = (status: string) => {
	const types: Record<string, string> = {
		pending: 'warning',
		in_progress: 'primary',
		completed: 'success',
	};
	return types[status] || 'info';
};

// 获取状态文本
const getStatusText = (status: string) => {
	const texts: Record<string, string> = {
		pending: '待开始',
		in_progress: '进行中',
		completed: '已完成',
	};
	return texts[status] || status;
};

// 加载评审详情
const loadReviewDetail = async () => {
	try {
		const response = await getReviewDetail(reviewId.value);
		
		if (response.code === 200) {
			Object.assign(reviewInfo, response.data);
		} else {
			ElMessage.error(response.message || '加载评审详情失败');
		}
	} catch (error) {
		console.error('加载评审详情失败:', error);
		ElMessage.error('加载评审详情失败');
	}
};

// 加载评审结果
const loadResults = async () => {
	loading.value = true;
	try {
		// 调用API获取评审结果
		const response = await getReviewResults(reviewId.value, {
			page: pagination.page,
			page_size: pagination.pageSize,
			result: filters.result,
			keyword: filters.keyword,
		});
		
		if (response.code === 200 && response.data) {
			results.value = response.data.rows || [];
			pagination.total = response.data.rowTotal || 0;
		} else {
			// 如果API调用失败，使用空数据
			results.value = [];
			pagination.total = 0;
			console.warn('获取评审结果失败:', response.message);
		}
		
		// 更新概览数据
		updateOverview();
		
		// 更新图表
		await nextTick();
		updateChart();
		
	} catch (error) {
		console.error('加载评审结果失败:', error);
		ElMessage.error('加载评审结果失败');
		
		// 出错时使用空数据
		results.value = [];
		pagination.total = 0;
		updateOverview();
	} finally {
		loading.value = false;
	}
};

// 更新概览数据
const updateOverview = () => {
	// 使用总数而不是当前页数据
	overview.totalCases = pagination.total;
	
	// 对于状态统计，需要重新计算所有数据
	// 这里暂时使用当前页数据，后续可以优化为单独的统计API
	overview.passedCases = results.value.filter(r => r.result === 'pass').length;
	overview.failedCases = results.value.filter(r => r.result === 'fail').length;
	overview.modifyCases = results.value.filter(r => r.result === 'modify').length;
};

// 更新图表
const updateChart = () => {
	if (!chartContainer.value) return;
	
	const chart = echarts.init(chartContainer.value);
	
	const option = {
		tooltip: {
			trigger: 'item',
			formatter: '{a} <br/>{b}: {c} ({d}%)'
		},
		legend: {
			orient: 'vertical',
			left: 'left',
			data: ['通过', '不通过', '需修改']
		},
		series: [
			{
				name: '评审结果',
				type: 'pie',
				radius: ['40%', '70%'],
				center: ['60%', '50%'],
				avoidLabelOverlap: false,
				itemStyle: {
					borderRadius: 10,
					borderColor: '#fff',
					borderWidth: 2
				},
				label: {
					show: false,
					position: 'center'
				},
				emphasis: {
					label: {
						show: true,
						fontSize: '30',
						fontWeight: 'bold'
					}
				},
				labelLine: {
					show: false
				},
				data: [
					{ 
						value: overview.passedCases, 
						name: '通过',
						itemStyle: { color: '#67c23a' }
					},
					{ 
						value: overview.failedCases, 
						name: '不通过',
						itemStyle: { color: '#f56c6c' }
					},
					{ 
						value: overview.modifyCases, 
						name: '需修改',
						itemStyle: { color: '#e6a23c' }
					}
				]
			}
		]
	};
	
	chart.setOption(option);
	
	// 响应式调整
	window.addEventListener('resize', () => {
		chart.resize();
	});
};

// 查看用例详情
const viewCaseDetail = (caseData: any) => {
	selectedCase.value = caseData;
	caseDetailVisible.value = true;
};

// 导出结果
const exportResult = () => {
	// TODO: 实现导出功能
	ElMessage.info('导出功能开发中...');
};

// 获取结果类型
const getResultType = (result: string) => {
	const types: Record<string, string> = {
		pass: 'success',
		fail: 'danger',
		modify: 'warning',
	};
	return types[result] || 'info';
};

// 获取结果文本
const getResultText = (result: string) => {
	const texts: Record<string, string> = {
		pass: '通过',
		fail: '不通过',
		modify: '需修改',
	};
	return texts[result] || result;
};

// 格式化日期时间
const formatDateTime = (date: string) => {
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

// 监听路由参数和查询参数变化
watch([() => route.params.reviewId, () => route.query.reviewId], () => {
	reviewId.value = getReviewId();
	// 重新加载数据
	if (reviewId.value) {
		loadReviewDetail();
		loadResults();
	} else {
		loadAvailableReviews();
	}
});

// 组件挂载时加载数据
onMounted(async () => {
	if (!reviewId.value) {
		// 如果没有有效的reviewId，加载可用的评审任务
		await loadAvailableReviews();
		return;
	}
	
	await Promise.all([
		loadReviewDetail(),
		loadResults()
	]);
});
</script>

<style scoped>
.review-result-container {
	padding: 20px;
}

/* 选择评审界面样式 */
.review-selection-container {
	padding: 20px;
}

.selection-card {
	margin-bottom: 20px;
}

.selection-header {
	text-align: center;
	margin-bottom: 30px;
}

.selection-header .page-title {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 8px;
	margin: 0 0 8px 0;
	font-size: 24px;
	font-weight: 600;
	color: var(--el-text-color-primary);
}

.selection-header .page-description {
	margin: 0;
	color: var(--el-text-color-regular);
	font-size: 14px;
}

.selection-content {
	margin-top: 20px;
}

.selection-content .el-table {
	cursor: pointer;
}

.selection-content .el-table tbody tr:hover {
	background-color: var(--el-table-row-hover-bg-color);
}

.page-header-card {
	margin-bottom: 20px;
}

.page-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.header-left {
	flex: 1;
}

.page-title {
	display: flex;
	align-items: center;
	gap: 8px;
	margin: 0 0 8px 0;
	font-size: 24px;
	font-weight: 600;
	color: var(--el-text-color-primary);
}

.page-description {
	margin: 0;
	color: var(--el-text-color-regular);
	font-size: 14px;
}

.header-right {
	display: flex;
	gap: 12px;
}

.overview-cards {
	margin-bottom: 20px;
}

.stat-card {
	height: 100px;
}

.stat-content {
	display: flex;
	align-items: center;
	height: 100%;
}

.stat-icon {
	width: 60px;
	height: 60px;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 15px;
	font-size: 24px;
	color: white;
}

.stat-icon.total {
	background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.pass {
	background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-icon.fail {
	background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
}

.stat-icon.modify {
	background: linear-gradient(135deg, #feca57 0%, #ff9ff3 100%);
}

.stat-info {
	flex: 1;
}

.stat-number {
	font-size: 28px;
	font-weight: bold;
	color: var(--el-text-color-primary);
	line-height: 1;
}

.stat-label {
	font-size: 14px;
	color: var(--el-text-color-regular);
	margin-top: 5px;
}

.chart-card,
.result-list-card {
	margin-bottom: 20px;
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
	padding-bottom: 15px;
	border-bottom: 1px solid var(--el-border-color-light);
}

.card-header h3 {
	display: flex;
	align-items: center;
	gap: 8px;
	margin: 0;
	color: var(--el-text-color-primary);
}

.filter-controls {
	display: flex;
	align-items: center;
}

.chart-container {
	height: 400px;
	width: 100%;
}

.pagination-container {
	display: flex;
	justify-content: center;
	margin-top: 20px;
}

.no-comment {
	color: var(--el-text-color-placeholder);
	font-style: italic;
}

/* 用例详情对话框样式 */
.case-detail {
	padding: 10px 0;
}

.case-info {
	margin-bottom: 25px;
	padding: 15px;
	background: var(--el-bg-color-page);
	border-radius: 6px;
}

.case-info h4 {
	margin: 0 0 10px 0;
	color: var(--el-text-color-primary);
	font-size: 18px;
}

.case-description {
	margin: 0;
	color: var(--el-text-color-regular);
	line-height: 1.6;
}

.review-result-detail,
.review-comment-detail,
.case-steps {
	margin-bottom: 25px;
}

.review-result-detail h5,
.review-comment-detail h5,
.case-steps h5 {
	margin: 0 0 15px 0;
	color: var(--el-text-color-primary);
	font-size: 16px;
}

.result-info {
	display: flex;
	align-items: center;
	gap: 15px;
}

.review-time {
	color: var(--el-text-color-regular);
	font-size: 14px;
}

.comment-content {
	padding: 15px;
	background: var(--el-bg-color-page);
	border-radius: 6px;
	border-left: 4px solid var(--el-color-primary);
	line-height: 1.6;
}

.step-item {
	margin-bottom: 15px;
	padding: 15px;
	border: 1px solid var(--el-border-color-light);
	border-radius: 6px;
	background: var(--el-bg-color);
}

.step-header {
	margin-bottom: 10px;
}

.step-number {
	display: inline-block;
	padding: 4px 8px;
	background: var(--el-color-primary);
	color: white;
	border-radius: 4px;
	font-size: 12px;
	font-weight: bold;
}

.step-content p {
	margin: 8px 0;
	line-height: 1.6;
}

/* 深色主题适配 */
.dark .case-info,
.dark .comment-content {
	background: var(--el-bg-color-overlay);
}

.dark .step-item {
	background: var(--el-bg-color-overlay);
	border-color: var(--el-border-color);
}
</style>