<template>
	<div class="assistant-statistics-container">
		<!-- 页面头部 -->
		<el-card shadow="hover" class="page-header-card">
			<div class="page-header">
				<div class="header-left">
					<h2 class="page-title">
						<el-icon><DataAnalysis /></el-icon>
						助手统计
					</h2>
					<p class="page-description">查看AI助手的使用统计和分析数据</p>
				</div>
				<div class="header-right">
					<el-button @click="loadStatistics">
						<el-icon><Refresh /></el-icon>
						刷新数据
					</el-button>
					<el-button type="primary" @click="exportReport">
						<el-icon><Download /></el-icon>
						导出报告
					</el-button>
				</div>
			</div>
		</el-card>

		<!-- 统计卡片 -->
		<el-row :gutter="20" class="stats-cards">
			<el-col :span="6">
				<el-card shadow="hover" class="stat-card">
					<div class="stat-content">
						<div class="stat-icon total">
							<el-icon><Avatar /></el-icon>
						</div>
						<div class="stat-info">
							<div class="stat-number">{{ statistics.total_configs }}</div>
							<div class="stat-label">总配置数</div>
						</div>
					</div>
				</el-card>
			</el-col>
			<el-col :span="6">
				<el-card shadow="hover" class="stat-card">
					<div class="stat-content">
						<div class="stat-icon active">
							<el-icon><Check /></el-icon>
						</div>
						<div class="stat-info">
							<div class="stat-number">{{ statistics.active_configs }}</div>
							<div class="stat-label">活跃配置</div>
						</div>
					</div>
				</el-card>
			</el-col>
			<el-col :span="6">
				<el-card shadow="hover" class="stat-card">
					<div class="stat-content">
						<div class="stat-icon conversations">
							<el-icon><ChatDotRound /></el-icon>
						</div>
						<div class="stat-info">
							<div class="stat-number">{{ statistics.total_conversations }}</div>
							<div class="stat-label">总对话数</div>
						</div>
					</div>
				</el-card>
			</el-col>
			<el-col :span="6">
				<el-card shadow="hover" class="stat-card">
					<div class="stat-content">
						<div class="stat-icon messages">
							<el-icon><ChatLineRound /></el-icon>
						</div>
						<div class="stat-info">
							<div class="stat-number">{{ statistics.total_messages }}</div>
							<div class="stat-label">总消息数</div>
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
							<span>配置类型分布</span>
						</div>
					</template>
					<div class="chart-container">
						<div ref="typeChartRef" class="chart"></div>
					</div>
				</el-card>
			</el-col>
			<el-col :span="12">
				<el-card shadow="hover" class="chart-card">
					<template #header>
						<div class="card-header">
							<span>对话活跃度</span>
						</div>
					</template>
					<div class="chart-container">
						<div ref="activityChartRef" class="chart"></div>
					</div>
				</el-card>
			</el-col>
		</el-row>

		<!-- 详细统计表格 -->
		<el-card shadow="hover" class="table-card">
			<template #header>
				<div class="card-header">
					<span>配置详细统计</span>
				</div>
			</template>
			<el-table
				v-loading="loading"
				:data="configStats"
				stripe
				style="width: 100%"
			>
				<el-table-column prop="config_name" label="配置名称" min-width="150" show-overflow-tooltip />
				<el-table-column prop="config_type" label="类型" width="120">
					<template #default="{ row }">
						<el-tag :type="getTypeTagType(row.config_type)">
							{{ getTypeText(row.config_type) }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="conversation_count" label="对话数" width="100" align="center" />
				<el-table-column prop="message_count" label="消息数" width="100" align="center" />
				<el-table-column prop="avg_messages_per_conversation" label="平均消息数" width="120" align="center">
					<template #default="{ row }">
						{{ row.avg_messages_per_conversation?.toFixed(1) || '0.0' }}
					</template>
				</el-table-column>
				<el-table-column prop="last_used" label="最后使用" width="160">
					<template #default="{ row }">
						{{ formatDateTime(row.last_used) }}
					</template>
				</el-table-column>
				<el-table-column prop="is_active" label="状态" width="80">
					<template #default="{ row }">
						<el-tag :type="row.is_active ? 'success' : 'danger'">
							{{ row.is_active ? '启用' : '禁用' }}
						</el-tag>
					</template>
				</el-table-column>
			</el-table>
		</el-card>

		<!-- 统计详情对话框 -->
		<!-- <StatisticsDialog v-model="statisticsDialogVisible" /> -->
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue';
import { ElMessage } from 'element-plus';
import { DataAnalysis, Refresh, Download, Avatar, Check, ChatDotRound, ChatLineRound } from '@element-plus/icons-vue';
import * as echarts from 'echarts';
import { getStatistics, type AssistantStatistics } from '/@/api/v1/assistant';

// 响应式数据
const loading = ref(false);
const statisticsDialogVisible = ref(false);

// 统计数据
const statistics = reactive<AssistantStatistics>({
	total_configs: 0,
	active_configs: 0,
	total_conversations: 0,
	total_messages: 0,
	type_distribution: {},
	config_type_distribution: {},
	daily_message_count: [],
	config_stats: [],
	recent_conversations: [],
	usage_stats: {
		today: 0,
		this_week: 0,
		this_month: 0
	}
});

// 配置统计数据
const configStats = ref<any[]>([]);

// 图表引用
const typeChartRef = ref();
const activityChartRef = ref();
let typeChart: echarts.ECharts | null = null;
let activityChart: echarts.ECharts | null = null;

// 加载统计数据
const loadStatistics = async () => {
	loading.value = true;
	try {
		const response = await getStatistics();
		
		if (response.code === 200) {
			Object.assign(statistics, response.data);
			configStats.value = response.data.config_stats || [];
			
			// 更新图表
			await nextTick();
			updateCharts();
		} else {
			ElMessage.error(response.message || '加载统计数据失败');
		}
		
	} catch (error) {
		console.error('加载统计数据失败:', error);
		ElMessage.error('加载统计数据失败');
	} finally {
		loading.value = false;
	}
};

// 初始化图表
const initCharts = () => {
	if (typeChartRef.value) {
		typeChart = echarts.init(typeChartRef.value);
	}
	if (activityChartRef.value) {
		activityChart = echarts.init(activityChartRef.value);
	}
	
	// 监听窗口大小变化
	window.addEventListener('resize', () => {
		typeChart?.resize();
		activityChart?.resize();
	});
};

// 更新图表
const updateCharts = () => {
	updateTypeChart();
	updateActivityChart();
};

// 更新配置类型分布图表
const updateTypeChart = () => {
	if (!typeChart) return;
	
	const typeData = statistics.config_type_distribution || {};
	const hasData = Object.keys(typeData).length > 0 && Object.values(typeData).some(v => v > 0);
	
	if (hasData) {
		const chartData = Object.entries(typeData).map(([type, count]) => ({
			name: getTypeText(type),
			value: count
		}));
		
		const option = {
			tooltip: {
				trigger: 'item',
				formatter: '{a} <br/>{b}: {c} ({d}%)'
			},
			legend: {
				orient: 'vertical',
				left: 'left',
				data: chartData.map(item => item.name)
			},
			series: [
				{
					name: '配置类型',
					type: 'pie',
					radius: ['40%', '70%'],
					center: ['60%', '50%'],
					data: chartData,
					emphasis: {
						itemStyle: {
							shadowBlur: 10,
							shadowOffsetX: 0,
							shadowColor: 'rgba(0, 0, 0, 0.5)'
						}
					},
					itemStyle: {
						borderRadius: 8,
						borderColor: '#fff',
						borderWidth: 2
					}
				}
			]
		};
		
		typeChart.setOption(option);
	} else {
		// 显示无数据提示
		typeChart.setOption({
			title: {
				text: '暂无数据',
				left: 'center',
				top: 'middle',
				textStyle: {
					color: '#999',
					fontSize: 14
				}
			}
		});
	}
};

// 更新活跃度图表
const updateActivityChart = () => {
	if (!activityChart) return;
	
	const activityData = statistics.daily_message_count || [];
	
	// 只要有数据数组就显示，即使所有值都是0
	const hasData = activityData.length > 0;
	
	if (hasData) {
		const dates = activityData.map(item => item.date);
		const counts = activityData.map(item => item.count);
		
		const option = {
			tooltip: {
				trigger: 'axis',
				formatter: function(params: any) {
					return `${params[0].name}<br/>消息数量: ${params[0].value}`;
				}
			},
			grid: {
				left: '3%',
				right: '4%',
				bottom: '3%',
				containLabel: true
			},
			xAxis: {
				type: 'category',
				data: dates,
				axisLabel: {
					fontSize: 12
				}
			},
			yAxis: {
				type: 'value',
				axisLabel: {
					fontSize: 12
				},
				min: 0  // 确保Y轴从0开始
			},
			series: [
				{
					name: '消息数量',
					type: 'line',
					data: counts,
					smooth: true,
					areaStyle: {
						opacity: 0.3,
						color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
							{ offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
							{ offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
						])
					},
					itemStyle: {
						color: '#409EFF'
					},
					lineStyle: {
						width: 3
					}
				}
			]
		};
		
		activityChart.setOption(option);
	} else {
		// 显示无数据提示
		activityChart.setOption({
			title: {
				text: '暂无数据',
				left: 'center',
				top: 'middle',
				textStyle: {
					color: '#999',
					fontSize: 14
				}
			}
		});
	}
};

// 导出报告
const exportReport = () => {
	ElMessage.info('导出功能开发中...');
};

// 获取类型标签类型
const getTypeTagType = (type: string) => {
	const types: Record<string, string> = {
		chatbot: 'primary',
		workflow: 'success',
		agent: 'warning',
	};
	return types[type] || 'info';
};

// 获取类型文本
const getTypeText = (type: string) => {
	const texts: Record<string, string> = {
		chatbot: '聊天机器人',
		workflow: '工作流',
		agent: '智能体',
	};
	return texts[type] || type;
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
onMounted(async () => {
	// 先初始化图表
	await nextTick();
	initCharts();
	// 然后加载数据
	await loadStatistics();
});

// 组件卸载时清理
onUnmounted(() => {
	typeChart?.dispose();
	activityChart?.dispose();
	window.removeEventListener('resize', () => {});
});
</script>

<style scoped>
.assistant-statistics-container {
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
	height: 120px;
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

.stat-icon.active {
	background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.conversations {
	background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.messages {
	background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info {
	flex: 1;
}

.stat-number {
	font-size: 32px;
	font-weight: bold;
	color: var(--el-text-color-primary);
	line-height: 1;
}

.stat-label {
	font-size: 14px;
	color: var(--el-text-color-regular);
	margin-top: 5px;
}

.charts-row {
	margin-bottom: 20px;
}

.chart-card {
	height: 400px;
}

.card-header {
	font-weight: 600;
	color: var(--el-text-color-primary);
}

.chart-container {
	height: 320px;
}

.chart {
	width: 100%;
	height: 100%;
}

.table-card {
	margin-bottom: 20px;
}
</style>