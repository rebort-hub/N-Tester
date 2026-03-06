<template>
	<el-dialog
		v-model="visible"
		title="评审统计信息"
		width="900px"
		:before-close="handleClose"
	>
		<div v-loading="loading" class="statistics-container">
			<!-- 统计卡片 -->
			<el-row :gutter="20" class="stats-cards">
				<el-col :span="6">
					<el-card shadow="hover" class="stat-card">
						<div class="stat-content">
							<div class="stat-icon total">
								<el-icon><Document /></el-icon>
							</div>
							<div class="stat-info">
								<div class="stat-number">{{ statistics.total_reviews }}</div>
								<div class="stat-label">总评审数</div>
							</div>
						</div>
					</el-card>
				</el-col>
				<el-col :span="6">
					<el-card shadow="hover" class="stat-card">
						<div class="stat-content">
							<div class="stat-icon pending">
								<el-icon><Clock /></el-icon>
							</div>
							<div class="stat-info">
								<div class="stat-number">{{ statistics.pending_reviews }}</div>
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
								<div class="stat-number">{{ statistics.in_progress_reviews }}</div>
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
								<div class="stat-number">{{ statistics.completed_reviews }}</div>
								<div class="stat-label">已完成</div>
							</div>
						</div>
					</el-card>
				</el-col>
			</el-row>

			<!-- 图表区域 -->
			<el-row :gutter="20" class="charts-row">
				<el-col :span="12">
					<el-card shadow="hover" class="chart-card">
						<template #header>
							<div class="card-header">
								<span>状态分布</span>
							</div>
						</template>
						<div ref="statusChartRef" class="chart-container"></div>
					</el-card>
				</el-col>
				<el-col :span="12">
					<el-card shadow="hover" class="chart-card">
						<template #header>
							<div class="card-header">
								<span>优先级分布</span>
							</div>
						</template>
						<div ref="priorityChartRef" class="chart-container"></div>
					</el-card>
				</el-col>
			</el-row>

			<!-- 最近评审 -->
			<el-card shadow="hover" class="recent-card">
				<template #header>
					<div class="card-header">
						<span>最近评审</span>
					</div>
				</template>
				<el-table :data="statistics.recent_reviews" style="width: 100%">
					<el-table-column prop="title" label="评审标题" min-width="200" />
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
					<el-table-column prop="creation_date" label="创建时间" width="160">
						<template #default="{ row }">
							{{ formatDateTime(row.creation_date) }}
						</template>
					</el-table-column>
				</el-table>
			</el-card>
		</div>

		<template #footer>
			<div class="dialog-footer">
				<el-button @click="handleClose">关闭</el-button>
			</div>
		</template>
	</el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted, onUnmounted, nextTick } from 'vue';
import { Document, Clock, Loading, Check } from '@element-plus/icons-vue';
import { getReviewStatistics, type ReviewStatistics } from '/@/api/v1/reviews';

// Props
interface Props {
	modelValue: boolean;
}

// Emits
interface Emits {
	(e: 'update:modelValue', value: boolean): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// 响应式数据
const visible = ref(false);
const loading = ref(false);
const statusChartRef = ref<HTMLDivElement>();
const priorityChartRef = ref<HTMLDivElement>();

// 图表实例
let statusChart: any = null;
let priorityChart: any = null;

// 统计数据
const statistics = reactive<ReviewStatistics>({
	total_reviews: 0,
	pending_reviews: 0,
	in_progress_reviews: 0,
	completed_reviews: 0,
	cancelled_reviews: 0,
	status_distribution: {},
	priority_distribution: {},
	recent_reviews: [],
});

// 监听 modelValue 变化
watch(
	() => props.modelValue,
	(val) => {
		visible.value = val;
		if (val) {
			loadStatistics();
		}
	}
);

// 监听 visible 变化
watch(visible, (val) => {
	emit('update:modelValue', val);
	if (!val) {
		// 对话框关闭时清理图表实例
		if (statusChart) {
			statusChart.dispose();
			statusChart = null;
		}
		if (priorityChart) {
			priorityChart.dispose();
			priorityChart = null;
		}
	}
});

// 加载统计数据
const loadStatistics = async () => {
	loading.value = true;
	try {
		const response = await getReviewStatistics({});
		if (response.code === 200) {
			Object.assign(statistics, response.data);
			
			// 等待DOM更新后渲染图表
			await nextTick();
			renderCharts();
		}
	} catch (error) {
		console.error('加载统计数据失败:', error);
	} finally {
		loading.value = false;
	}
};

// 渲染图表
const renderCharts = () => {
	// 渲染状态分布柱状图
	if (statusChartRef.value) {
		renderStatusChart();
	}
	
	// 渲染优先级分布柱状图
	if (priorityChartRef.value) {
		renderPriorityChart();
	}
};

// 渲染状态分布图表
const renderStatusChart = () => {
	// 动态导入 ECharts
	import('echarts').then((echarts) => {
		// 销毁之前的图表实例
		if (statusChart) {
			statusChart.dispose();
		}
		
		statusChart = echarts.init(statusChartRef.value);
		
		const statusData = [
			{ name: '待开始', value: statistics.pending_reviews, color: '#f093fb' },
			{ name: '进行中', value: statistics.in_progress_reviews, color: '#4facfe' },
			{ name: '已完成', value: statistics.completed_reviews, color: '#43e97b' },
			{ name: '已取消', value: statistics.cancelled_reviews, color: '#ff6b6b' }
		];
		
		const option = {
			tooltip: {
				trigger: 'axis',
				axisPointer: {
					type: 'shadow'
				},
				formatter: function(params: any) {
					const data = params[0];
					return `${data.name}: ${data.value}`;
				},
				backgroundColor: 'rgba(0, 0, 0, 0.8)',
				borderColor: 'transparent',
				textStyle: {
					color: '#fff'
				}
			},
			grid: {
				left: '3%',
				right: '4%',
				bottom: '8%',
				top: '8%',
				containLabel: true
			},
			xAxis: {
				type: 'category',
				data: statusData.map(item => item.name),
				axisLine: {
					lineStyle: {
						color: '#e0e0e0'
					}
				},
				axisLabel: {
					color: '#666',
					fontSize: 11
				},
				axisTick: {
					show: false
				}
			},
			yAxis: {
				type: 'value',
				axisLine: {
					show: false
				},
				axisTick: {
					show: false
				},
				axisLabel: {
					color: '#666',
					fontSize: 11
				},
				splitLine: {
					lineStyle: {
						color: '#f0f0f0',
						type: 'dashed'
					}
				}
			},
			series: [
				{
					name: '评审数量',
					type: 'bar',
					data: statusData.map((item, index) => ({
						value: item.value,
						itemStyle: {
							color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
								{ offset: 0, color: item.color },
								{ offset: 1, color: item.color + '80' }
							]),
							borderRadius: [6, 6, 0, 0],
							shadowBlur: 8,
							shadowColor: item.color + '40',
							shadowOffsetY: 3
						}
					})),
					barWidth: '45%',
					emphasis: {
						itemStyle: {
							shadowBlur: 15,
							shadowColor: 'rgba(0, 0, 0, 0.3)'
						}
					},
					animationDelay: function (idx: number) {
						return idx * 80;
					}
				}
			],
			animationEasing: 'elasticOut',
			animationDelayUpdate: function (idx: number) {
				return idx * 40;
			}
		};
		
		statusChart.setOption(option);
	});
};

// 渲染优先级分布图表
const renderPriorityChart = () => {
	// 动态导入 ECharts
	import('echarts').then((echarts) => {
		// 销毁之前的图表实例
		if (priorityChart) {
			priorityChart.dispose();
		}
		
		priorityChart = echarts.init(priorityChartRef.value);
		
		const priorityData = [
			{ name: '低', value: statistics.priority_distribution.low || 0, color: '#95de64' },
			{ name: '中', value: statistics.priority_distribution.medium || 0, color: '#ffc53d' },
			{ name: '高', value: statistics.priority_distribution.high || 0, color: '#ff7a45' },
			{ name: '紧急', value: statistics.priority_distribution.urgent || 0, color: '#ff4d4f' }
		];
		
		const option = {
			tooltip: {
				trigger: 'axis',
				axisPointer: {
					type: 'shadow'
				},
				formatter: function(params: any) {
					const data = params[0];
					return `${data.name}: ${data.value}`;
				},
				backgroundColor: 'rgba(0, 0, 0, 0.8)',
				borderColor: 'transparent',
				textStyle: {
					color: '#fff'
				}
			},
			grid: {
				left: '3%',
				right: '4%',
				bottom: '8%',
				top: '8%',
				containLabel: true
			},
			xAxis: {
				type: 'category',
				data: priorityData.map(item => item.name),
				axisLine: {
					lineStyle: {
						color: '#e0e0e0'
					}
				},
				axisLabel: {
					color: '#666',
					fontSize: 11
				},
				axisTick: {
					show: false
				}
			},
			yAxis: {
				type: 'value',
				axisLine: {
					show: false
				},
				axisTick: {
					show: false
				},
				axisLabel: {
					color: '#666',
					fontSize: 11
				},
				splitLine: {
					lineStyle: {
						color: '#f0f0f0',
						type: 'dashed'
					}
				}
			},
			series: [
				{
					name: '评审数量',
					type: 'bar',
					data: priorityData.map((item, index) => ({
						value: item.value,
						itemStyle: {
							color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
								{ offset: 0, color: item.color },
								{ offset: 1, color: item.color + '80' }
							]),
							borderRadius: [6, 6, 0, 0],
							shadowBlur: 8,
							shadowColor: item.color + '40',
							shadowOffsetY: 3
						}
					})),
					barWidth: '45%',
					emphasis: {
						itemStyle: {
							shadowBlur: 15,
							shadowColor: 'rgba(0, 0, 0, 0.3)'
						}
					},
					animationDelay: function (idx: number) {
						return idx * 80;
					}
				}
			],
			animationEasing: 'elasticOut',
			animationDelayUpdate: function (idx: number) {
				return idx * 40;
			}
		};
		
		priorityChart.setOption(option);
	});
};

// 处理关闭
const handleClose = () => {
	visible.value = false;
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

// 组件挂载时初始化
onMounted(() => {
	if (props.modelValue) {
		visible.value = true;
		loadStatistics();
	}
	
	// 添加窗口大小变化监听
	window.addEventListener('resize', handleResize);
});

// 组件卸载时清理
onUnmounted(() => {
	// 销毁图表实例
	if (statusChart) {
		statusChart.dispose();
		statusChart = null;
	}
	if (priorityChart) {
		priorityChart.dispose();
		priorityChart = null;
	}
	
	// 移除事件监听
	window.removeEventListener('resize', handleResize);
});

// 处理窗口大小变化
const handleResize = () => {
	if (statusChart) {
		statusChart.resize();
	}
	if (priorityChart) {
		priorityChart.resize();
	}
};
</script>

<style scoped>
.statistics-container {
	min-height: 400px;
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

.stat-icon.total {
	background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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

.stat-info {
	flex: 1;
}

.stat-number {
	font-size: 28px;
	font-weight: bold;
	color: #303133;
	line-height: 1;
}

.stat-label {
	font-size: 14px;
	color: #909399;
	margin-top: 5px;
}

.charts-row {
	margin-bottom: 20px;
}

.chart-card {
	height: 280px;
}

.chart-container {
	height: 200px;
	width: 100%;
	padding: 5px;
}

.recent-card {
	margin-bottom: 20px;
}

.card-header {
	font-weight: 600;
	color: #303133;
}

.dialog-footer {
	text-align: right;
}
</style>