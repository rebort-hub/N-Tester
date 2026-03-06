<template>
	<div class="my-tasks-container">
		<!-- 页面头部 -->
		<el-card shadow="hover" class="page-header-card">
			<div class="page-header">
				<div class="header-left">
					<h2 class="page-title">
						<el-icon><User /></el-icon>
						我的评审任务
					</h2>
					<p class="page-description">查看和管理分配给我的评审任务</p>
				</div>
				<div class="header-right">
					<el-button @click="$router.push('/reviews/index')">
						<el-icon><ArrowLeft /></el-icon>
						返回评审列表
					</el-button>
					<el-button type="primary" @click="loadTasks">
						<el-icon><Refresh /></el-icon>
						刷新任务
					</el-button>
				</div>
			</div>
		</el-card>

		<!-- 任务统计卡片 -->
		<el-row :gutter="20" class="stats-cards">
			<el-col :span="6">
				<el-card shadow="hover" class="stat-card">
					<div class="stat-content">
						<div class="stat-icon pending">
							<el-icon><Clock /></el-icon>
						</div>
						<div class="stat-info">
							<div class="stat-number">{{ statistics.pending }}</div>
							<div class="stat-label">待开始</div>
						</div>
					</div>
				</el-card>
			</el-col>
			<el-col :span="6">
				<el-card shadow="hover" class="stat-card">
					<div class="stat-content">
						<div class="stat-icon progress">
							<el-icon><Loading /></el-icon>
						</div>
						<div class="stat-info">
							<div class="stat-number">{{ statistics.in_progress }}</div>
							<div class="stat-label">进行中</div>
						</div>
					</div>
				</el-card>
			</el-col>
			<el-col :span="6">
				<el-card shadow="hover" class="stat-card">
					<div class="stat-content">
						<div class="stat-icon completed">
							<el-icon><Check /></el-icon>
						</div>
						<div class="stat-info">
							<div class="stat-number">{{ statistics.completed }}</div>
							<div class="stat-label">已完成</div>
						</div>
					</div>
				</el-card>
			</el-col>
			<el-col :span="6">
				<el-card shadow="hover" class="stat-card">
					<div class="stat-content">
						<div class="stat-icon overdue">
							<el-icon><Warning /></el-icon>
						</div>
						<div class="stat-info">
							<div class="stat-number">{{ statistics.overdue }}</div>
							<div class="stat-label">已逾期</div>
						</div>
					</div>
				</el-card>
			</el-col>
		</el-row>

		<!-- 筛选和搜索 -->
		<el-card shadow="hover" class="filter-card">
			<el-form :model="filters" inline>
				<el-form-item label="状态筛选">
					<el-select 
						v-model="filters.status" 
						placeholder="全部状态" 
						clearable 
						@change="loadTasks"
						style="width: 150px"
					>
						<el-option label="待开始" value="pending" />
						<el-option label="进行中" value="in_progress" />
						<el-option label="已完成" value="completed" />
					</el-select>
				</el-form-item>
				<el-form-item label="优先级">
					<el-select 
						v-model="filters.priority" 
						placeholder="全部优先级" 
						clearable 
						@change="loadTasks"
						style="width: 150px"
					>
						<el-option label="低" value="low" />
						<el-option label="中" value="medium" />
						<el-option label="高" value="high" />
						<el-option label="紧急" value="urgent" />
					</el-select>
				</el-form-item>
				<el-form-item label="搜索">
					<el-input
						v-model="filters.keyword"
						placeholder="搜索评审标题"
						@keyup.enter="loadTasks"
						style="width: 200px"
					>
						<template #append>
							<el-button @click="loadTasks">
								<el-icon><Search /></el-icon>
							</el-button>
						</template>
					</el-input>
				</el-form-item>
			</el-form>
		</el-card>

		<!-- 任务列表 -->
		<el-card shadow="hover" class="table-card">
			<el-table
				v-loading="loading"
				:data="tasks"
				stripe
				style="width: 100%"
			>
				<el-table-column prop="title" label="评审标题" min-width="200" show-overflow-tooltip />
				<el-table-column prop="priority" label="优先级" width="100">
					<template #default="{ row }">
						<el-tag :type="getPriorityType(row.priority)">
							{{ getPriorityText(row.priority) }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="status" label="我的状态" width="100">
					<template #default="{ row }">
						<el-tag :type="getMyStatusType(row.my_status)">
							{{ getMyStatusText(row.my_status) }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="progress" label="我的进度" width="120">
					<template #default="{ row }">
						<el-progress :percentage="row.my_progress || 0" :stroke-width="6" />
					</template>
				</el-table-column>
				<el-table-column prop="deadline" label="截止时间" width="160">
					<template #default="{ row }">
						<span :class="{ 'overdue': isOverdue(row.deadline) }">
							{{ formatDateTime(row.deadline) }}
						</span>
					</template>
				</el-table-column>
				<el-table-column prop="assigned_at" label="分配时间" width="160">
					<template #default="{ row }">
						{{ formatDateTime(row.assigned_at) }}
					</template>
				</el-table-column>
				<el-table-column label="操作" width="280" fixed="right">
					<template #default="{ row }">
						<el-button 
							v-if="row.my_status === 'pending'" 
							type="primary" 
							size="small" 
							@click="startReview(row)"
						>
							开始评审
						</el-button>
						<el-button 
							v-if="row.my_status === 'pending'" 
							type="success" 
							size="small" 
							@click="aiPreReview(row)"
						>
							AI初评
						</el-button>
						<el-button 
							v-else-if="row.my_status === 'in_progress'" 
							type="warning" 
							size="small" 
							@click="continueReview(row)"
						>
							继续评审
						</el-button>
						<el-button 
							v-else-if="row.my_status === 'human_review'" 
							type="info" 
							size="small" 
							@click="viewAIResults(row)"
						>
							查看AI结果
						</el-button>
						<el-button 
							v-else 
							size="small" 
							@click="viewReview(row)"
						>
							查看结果
						</el-button>
						<el-button size="small" @click="viewDetails(row)">详情</el-button>
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
					@size-change="loadTasks"
					@current-change="loadTasks"
				/>
			</div>
		</el-card>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { User, ArrowLeft, Refresh, Clock, Loading, Check, Warning, Search } from '@element-plus/icons-vue';
import { useRouter } from 'vue-router';
import { getMyReviewTasks, startReviewTask, aiPreReviewAllCases, getAIPreReviewSummary, checkAIReviewAvailability } from '/@/api/v1/reviews';

const router = useRouter();

// 响应式数据
const loading = ref(false);
const tasks = ref<any[]>([]);

// 统计数据
const statistics = reactive({
	pending: 0,
	in_progress: 0,
	completed: 0,
	overdue: 0,
});

// 筛选条件
const filters = reactive({
	status: '',
	priority: '',
	keyword: '',
});

// 分页数据
const pagination = reactive({
	page: 1,
	pageSize: 20,
	total: 0,
});

// 加载任务列表
const loadTasks = async () => {
	loading.value = true;
	try {
		const response = await getMyReviewTasks({
			page: pagination.page,
			page_size: pagination.pageSize,
			status: filters.status,
			priority: filters.priority,
			keyword: filters.keyword,
		});
		
		if (response.code === 200) {
			tasks.value = response.data.rows || [];
			pagination.total = response.data.rowTotal || 0;
			
			// 更新统计数据
			updateStatistics();
		} else {
			ElMessage.error(response.message || '加载任务列表失败');
		}
		
	} catch (error) {
		console.error('加载任务列表失败:', error);
		ElMessage.error('加载任务列表失败');
	} finally {
		loading.value = false;
	}
};

// 更新统计数据
const updateStatistics = () => {
	statistics.pending = tasks.value.filter(t => t.my_status === 'pending').length;
	statistics.in_progress = tasks.value.filter(t => t.my_status === 'in_progress').length;
	statistics.completed = tasks.value.filter(t => t.my_status === 'completed').length;
	statistics.overdue = tasks.value.filter(t => isOverdue(t.deadline) && t.my_status !== 'completed').length;
};

// 开始评审
const startReview = async (task: any) => {
	try {
		await ElMessageBox.confirm(
			`确定要开始评审"${task.title}"吗？`,
			'确认开始评审',
			{
				confirmButtonText: '开始评审',
				cancelButtonText: '取消',
				type: 'info',
			}
		);
		
		const response = await startReviewTask(task.id);
		
		if (response.code === 200) {
			ElMessage.success('开始评审成功');
			// 跳转到评审执行页面
			router.push(`/reviews/execute?reviewId=${task.id}`);
		} else {
			ElMessage.error(response.message || '开始评审失败');
		}
		
	} catch (error) {
		if (error !== 'cancel') {
			console.error('开始评审失败:', error);
			ElMessage.error('开始评审失败');
		}
	}
};

// AI预评审
const aiPreReview = async (task: any) => {
	try {
		// 先检查AI评审功能可用性
		const availabilityResponse = await checkAIReviewAvailability(task.id);
		if (availabilityResponse.code !== 200 || !availabilityResponse.data.available) {
			ElMessage.error(availabilityResponse.data?.error || 'AI评审功能不可用');
			return;
		}
		
		await ElMessageBox.confirm(
			`确定要对"${task.title}"进行AI初步评审吗？AI将自动评审所有测试用例，完成后您可以查看AI评审结果并进行人工调整。`,
			'确认AI初评',
			{
				confirmButtonText: '开始AI初评',
				cancelButtonText: '取消',
				type: 'info',
			}
		);
		
		const loadingMessage = ElMessage({
			message: 'AI正在评审中，请稍候...',
			type: 'info',
			duration: 0,
		});
		
		const response = await aiPreReviewAllCases(task.id);
		loadingMessage.close();
		
		if (response.code === 200) {
			const result = response.data;
			ElMessage.success(`AI初评完成！共处理 ${result.total_cases} 个用例，成功 ${result.processed_cases} 个`);
			// 刷新任务列表
			loadTasks();
		} else {
			ElMessage.error(response.message || 'AI初评失败');
		}
		
	} catch (error) {
		if (error !== 'cancel') {
			console.error('AI初评失败:', error);
			ElMessage.error('AI初评失败');
		}
	}
};

// 查看AI评审结果
const viewAIResults = async (task: any) => {
	try {
		// 获取AI预评审摘要
		const summaryResponse = await getAIPreReviewSummary(task.id);
		if (summaryResponse.code === 200) {
			const summary = summaryResponse.data;
			
			// 显示AI评审摘要对话框
			ElMessageBox.alert(
				`AI已完成初步评审，结果如下：
				
总用例数：${summary.total_cases}
通过：${summary.pass_count} 个
需修改：${summary.modify_count} 个  
不通过：${summary.fail_count} 个

您可以点击"继续评审"查看详细的AI评审意见并进行调整。`,
				'AI评审结果摘要',
				{
					confirmButtonText: '继续评审',
					type: 'info',
				}
			).then(() => {
				// 跳转到评审执行页面
				router.push(`/reviews/execute?reviewId=${task.id}`);
			}).catch(() => {
				// 用户取消，不做任何操作
			});
		} else {
			ElMessage.error('获取AI评审摘要失败');
		}
	} catch (error) {
		console.error('获取AI评审结果失败:', error);
		ElMessage.error('获取AI评审结果失败');
	}
};

// 继续评审
const continueReview = (task: any) => {
	router.push(`/reviews/execute?reviewId=${task.id}`);
};

// 查看评审结果
const viewReview = (task: any) => {
	router.push(`/reviews/result?reviewId=${task.id}`);
};

// 查看详情
const viewDetails = (task: any) => {
	router.push(`/reviews/index?reviewId=${task.id}`);
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

// 获取我的状态类型
const getMyStatusType = (status: string) => {
	const types: Record<string, string> = {
		pending: 'info',
		in_progress: 'warning',
		completed: 'success',
		human_review: 'primary',
	};
	return types[status] || 'info';
};

// 获取我的状态文本
const getMyStatusText = (status: string) => {
	const texts: Record<string, string> = {
		pending: '待开始',
		in_progress: '进行中',
		completed: '已完成',
		human_review: '人工审核',
	};
	return texts[status] || status;
};

// 检查是否逾期
const isOverdue = (deadline: string) => {
	if (!deadline) return false;
	return new Date(deadline) < new Date();
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

// 组件挂载时加载数据
onMounted(() => {
	loadTasks();
});
</script>

<style scoped>
.my-tasks-container {
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

.stats-cards {
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

.stat-icon.pending {
	background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.progress {
	background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.completed {
	background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-icon.overdue {
	background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
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

.overdue {
	color: #f56c6c;
	font-weight: bold;
}
</style>