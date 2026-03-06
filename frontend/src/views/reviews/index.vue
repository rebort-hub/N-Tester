<template>
	<div class="reviews-container">
		<!-- 页面头部 -->
		<el-card shadow="hover" class="page-header-card">
			<div class="page-header">
				<div class="header-left">
					<h2 class="page-title">
						<el-icon><Document /></el-icon>
						用例评审
					</h2>
					<p class="page-description">管理测试用例评审流程，提升用例质量</p>
				</div>
				<div class="header-right">
					<el-button type="primary" @click="showCreateDialog = true">
						<el-icon><Plus /></el-icon>
						创建评审
					</el-button>
					<el-button @click="showStatistics = true">
						<el-icon><DataAnalysis /></el-icon>
						统计信息
					</el-button>
					<el-button @click="$router.push('/reviews/templates')">
						<el-icon><Setting /></el-icon>
						模板管理
					</el-button>
				</div>
			</div>
		</el-card>

		<!-- 筛选条件 -->
		<el-card shadow="hover" class="filter-card">
			<el-form :model="filterForm" inline>
				<el-form-item label="项目">
					<el-select v-model="filterForm.project_id" placeholder="选择项目" clearable style="width: 200px">
						<el-option
							v-for="project in projects"
							:key="project.id"
							:label="project.name"
							:value="project.id"
						/>
					</el-select>
				</el-form-item>
				<el-form-item label="状态">
					<el-select v-model="filterForm.status" placeholder="选择状态" clearable style="width: 150px">
						<el-option label="待开始" value="pending" />
						<el-option label="进行中" value="in_progress" />
						<el-option label="已完成" value="completed" />
						<el-option label="已取消" value="cancelled" />
					</el-select>
				</el-form-item>
				<el-form-item label="优先级">
					<el-select v-model="filterForm.priority" placeholder="选择优先级" clearable style="width: 150px">
						<el-option label="低" value="low" />
						<el-option label="中" value="medium" />
						<el-option label="高" value="high" />
						<el-option label="紧急" value="urgent" />
					</el-select>
				</el-form-item>
				<el-form-item>
					<el-button type="primary" @click="loadReviews">
						<el-icon><Search /></el-icon>
						查询
					</el-button>
					<el-button @click="resetFilter">重置</el-button>
				</el-form-item>
			</el-form>
		</el-card>

		<!-- 评审列表 -->
		<el-card shadow="hover" class="table-card">
			<el-table
				v-loading="loading"
				:data="reviews"
				stripe
				style="width: 100%"
			>
				<el-table-column prop="title" label="评审标题" min-width="200">
					<template #default="{ row }">
						<el-link type="primary" @click="viewReview(row.id)">
							{{ row.title }}
						</el-link>
					</template>
				</el-table-column>
				<el-table-column prop="status" label="状态" width="100">
					<template #default="{ row }">
						<el-tag :type="getStatusType(row.status)">
							{{ getStatusText(row.status) }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="priority" label="优先级" width="100">
					<template #default="{ row }">
						<el-tag :type="getPriorityType(row.priority)">
							{{ getPriorityText(row.priority) }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="deadline" label="截止日期" width="160">
					<template #default="{ row }">
						<span v-if="row.deadline">{{ formatDateTime(row.deadline) }}</span>
						<span v-else>-</span>
					</template>
				</el-table-column>
				<el-table-column prop="creator_name" label="创建人" width="100" />
				<el-table-column prop="creation_date" label="创建时间" width="160">
					<template #default="{ row }">
						{{ formatDateTime(row.creation_date) }}
					</template>
				</el-table-column>
				<el-table-column label="操作" width="200" fixed="right">
					<template #default="{ row }">
						<el-button size="small" @click="viewReview(row.id)">查看</el-button>
						<el-button size="small" type="primary" @click="editReview(row)">编辑</el-button>
						<el-button size="small" type="danger" @click="deleteReview(row)">删除</el-button>
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
					@size-change="loadReviews"
					@current-change="loadReviews"
				/>
			</div>
		</el-card>

		<!-- 创建评审对话框 -->
		<CreateReviewDialog
			v-model="showCreateDialog"
			@success="loadReviews"
		/>

		<!-- 编辑评审对话框 -->
		<EditReviewDialog
			v-model="showEditDialog"
			:review="editingReview"
			@success="loadReviews"
		/>

		<!-- 评审详情对话框 -->
		<ReviewDetailDialog
			v-model="showDetailDialog"
			:review-id="viewingReviewId"
			@edit="editFromDetail"
		/>

		<!-- 统计信息对话框 -->
		<StatisticsDialog
			v-model="showStatistics"
		/>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Document, Plus, DataAnalysis, Setting, Search } from '@element-plus/icons-vue';
import { getReviewList, deleteReview as deleteReviewApi, type Review } from '/@/api/v1/reviews';
import { getProjectList } from '/@/api/v1/project';
import CreateReviewDialog from './components/CreateReviewDialog.vue';
import EditReviewDialog from './components/EditReviewDialog.vue';
import ReviewDetailDialog from './components/ReviewDetailDialog.vue';
import StatisticsDialog from './components/StatisticsDialog.vue';

// 响应式数据
const loading = ref(false);
const reviews = ref<Review[]>([]);
const projects = ref<any[]>([]);
const showCreateDialog = ref(false);
const showEditDialog = ref(false);
const showDetailDialog = ref(false);
const showStatistics = ref(false);
const editingReview = ref<Review | null>(null);
const viewingReviewId = ref<number | null>(null);

// 筛选表单
const filterForm = reactive({
	project_id: undefined,
	status: '',
	priority: '',
});

// 分页数据
const pagination = reactive({
	page: 1,
	pageSize: 10,
	total: 0,
});

// 加载评审列表
const loadReviews = async () => {
	loading.value = true;
	try {
		const params = {
			page: pagination.page,
			page_size: pagination.pageSize,
			...filterForm,
		};
		
		const response = await getReviewList(params);
		if (response.code === 200) {
			reviews.value = response.data.rows || [];
			pagination.total = response.data.rowTotal || 0;
		}
	} catch (error) {
		console.error('加载评审列表失败:', error);
		ElMessage.error('加载评审列表失败');
	} finally {
		loading.value = false;
	}
};

// 加载项目列表
const loadProjects = async () => {
	try {
		const response = await getProjectList({ page: 1, page_size: 100 });
		if (response.code === 200) {
			projects.value = response.data.rows || [];
		}
	} catch (error) {
		console.error('加载项目列表失败:', error);
		ElMessage.error('加载项目列表失败');
	}
};

// 重置筛选条件
const resetFilter = () => {
	filterForm.project_id = undefined;
	filterForm.status = '';
	filterForm.priority = '';
	pagination.page = 1;
	loadReviews();
};

// 查看评审详情
const viewReview = (id: number) => {
	viewingReviewId.value = id;
	showDetailDialog.value = true;
};

// 编辑评审
const editReview = (review: Review) => {
	// 打开编辑对话框
	editingReview.value = review;
	showEditDialog.value = true;
};

// 从详情对话框编辑评审
const editFromDetail = (review: Review) => {
	editingReview.value = review;
	showEditDialog.value = true;
};

// 删除评审
const deleteReview = async (review: Review) => {
	try {
		await ElMessageBox.confirm(
			`确定要删除评审"${review.title}"吗？`,
			'确认删除',
			{
				confirmButtonText: '确定',
				cancelButtonText: '取消',
				type: 'warning',
			}
		);

		const response = await deleteReviewApi(review.id);
		if (response.code === 200) {
			ElMessage.success('删除成功');
			loadReviews();
		}
	} catch (error) {
		if (error !== 'cancel') {
			console.error('删除评审失败:', error);
			ElMessage.error('删除评审失败');
		}
	}
};

// 获取状态类型
const getStatusType = (status: string) => {
	const types: Record<string, string> = {
		pending: 'info',
		in_progress: 'warning',
		completed: 'success',
		cancelled: 'danger',
	};
	return types[status] || 'info';
};

// 获取状态文本
const getStatusText = (status: string) => {
	const texts: Record<string, string> = {
		pending: '待开始',
		in_progress: '进行中',
		completed: '已完成',
		cancelled: '已取消',
	};
	return texts[status] || status;
};

// 获取优先级类型
const getPriorityType = (priority: string) => {
	const types: Record<string, string> = {
		low: 'info',
		medium: '',
		high: 'warning',
		urgent: 'danger',
	};
	return types[priority] || '';
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

// 格式化日期 - 统一格式为 YYYY-MM-DD
const formatDate = (date: string) => {
	if (!date) return '-';
	const d = new Date(date);
	const year = d.getFullYear();
	const month = String(d.getMonth() + 1).padStart(2, '0');
	const day = String(d.getDate()).padStart(2, '0');
	return `${year}-${month}-${day}`;
};

// 格式化日期时间 - 统一格式为 YYYY-MM-DD HH:MM:SS
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

// 组件挂载时加载数据
onMounted(() => {
	loadProjects();
	loadReviews();
});
</script>

<style scoped>
.reviews-container {
	padding: 20px;
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
	color: #303133;
}

.page-description {
	margin: 0;
	color: #909399;
	font-size: 14px;
}

.header-right {
	display: flex;
	gap: 12px;
}

.filter-card {
	margin-bottom: 20px;
}

.table-card {
	margin-bottom: 20px;
}

.pagination-container {
	display: flex;
	justify-content: center;
	margin-top: 20px;
}
</style>