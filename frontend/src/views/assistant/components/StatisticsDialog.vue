<template>
	<el-dialog
		v-model="visible"
		title="AI助手统计信息"
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
								<el-icon><Avatar /></el-icon>
							</div>
							<div class="stat-info">
								<div class="stat-number">{{ statistics.total_configs }}</div>
								<div class="stat-label">助手配置</div>
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
								<div class="stat-label">启用配置</div>
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
								<div class="stat-label">对话数量</div>
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
								<div class="stat-label">消息数量</div>
							</div>
						</div>
					</el-card>
				</el-col>
			</el-row>

			<!-- 使用统计 -->
			<el-row :gutter="20" class="usage-stats">
				<el-col :span="8">
					<el-card shadow="hover" class="usage-card">
						<div class="usage-content">
							<div class="usage-icon today">
								<el-icon><Calendar /></el-icon>
							</div>
							<div class="usage-info">
								<div class="usage-number">{{ statistics.usage_stats?.today || 0 }}</div>
								<div class="usage-label">今日使用</div>
							</div>
						</div>
					</el-card>
				</el-col>
				<el-col :span="8">
					<el-card shadow="hover" class="usage-card">
						<div class="usage-content">
							<div class="usage-icon week">
								<el-icon><Calendar /></el-icon>
							</div>
							<div class="usage-info">
								<div class="usage-number">{{ statistics.usage_stats?.this_week || 0 }}</div>
								<div class="usage-label">本周使用</div>
							</div>
						</div>
					</el-card>
				</el-col>
				<el-col :span="8">
					<el-card shadow="hover" class="usage-card">
						<div class="usage-content">
							<div class="usage-icon month">
								<el-icon><Calendar /></el-icon>
							</div>
							<div class="usage-info">
								<div class="usage-number">{{ statistics.usage_stats?.this_month || 0 }}</div>
								<div class="usage-label">本月使用</div>
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
								<span>助手类型分布</span>
							</div>
						</template>
						<div ref="typeChartRef" class="chart-container"></div>
					</el-card>
				</el-col>
				<el-col :span="12">
					<el-card shadow="hover" class="chart-card">
						<template #header>
							<div class="card-header">
								<span>使用趋势</span>
							</div>
						</template>
						<div ref="trendChartRef" class="chart-container"></div>
					</el-card>
				</el-col>
			</el-row>

			<!-- 最近对话 -->
			<el-card shadow="hover" class="recent-card">
				<template #header>
					<div class="card-header">
						<span>最近对话</span>
					</div>
				</template>
				<el-table :data="statistics.recent_conversations || []" style="width: 100%">
					<el-table-column prop="title" label="对话标题" min-width="200">
						<template #default="{ row }">
							{{ row.title || '未命名对话' }}
						</template>
					</el-table-column>
					<el-table-column prop="assistant_name" label="助手名称" width="150" />
					<el-table-column prop="message_count" label="消息数" width="100" align="center">
						<template #default="{ row }">
							<el-tag type="info">{{ row.message_count || 0 }}</el-tag>
						</template>
					</el-table-column>
					<el-table-column prop="created_at" label="创建时间" width="160">
						<template #default="{ row }">
							{{ formatDateTime(row.created_at || row.creation_date) }}
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
import { ref, reactive, watch, onMounted, nextTick } from 'vue';
import { Avatar, Check, ChatDotRound, ChatLineRound, Calendar } from '@element-plus/icons-vue';
import { getStatistics, type AssistantStatistics } from '/@/api/v1/assistant';
import * as echarts from 'echarts';

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
const typeChartRef = ref<HTMLDivElement>();
const trendChartRef = ref<HTMLDivElement>();

// 统计数据
const statistics = reactive<AssistantStatistics>({
	total_configs: 0,
	active_configs: 0,
	total_conversations: 0,
	total_messages: 0,
	type_distribution: {},
	recent_conversations: [],
	usage_stats: {
		today: 0,
		this_week: 0,
		this_month: 0,
	},
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
});

// 加载统计数据
const loadStatistics = async () => {
	loading.value = true;
	try {
		const response = await getStatistics();
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
	// 渲染助手类型分布柱状图
	if (typeChartRef.value) {
		const typeChart = echarts.init(typeChartRef.value);
		const typeData = statistics.type_distribution || {};
		
		// 确保有数据才渲染图表
		const hasData = Object.keys(typeData).length > 0 && Object.values(typeData).some(v => v > 0);
		
		if (hasData) {
			const option = {
				tooltip: {
					trigger: 'axis',
					axisPointer: {
						type: 'shadow'
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
					data: ['聊天机器人', '工作流', '智能代理'],
					axisLabel: {
						fontSize: 12
					}
				},
				yAxis: {
					type: 'value',
					axisLabel: {
						fontSize: 12
					}
				},
				series: [{
					name: '数量',
					type: 'bar',
					data: [
						typeData.chatbot || 0,
						typeData.workflow || 0,
						typeData.agent || 0
					],
					itemStyle: {
						color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
							{ offset: 0, color: '#83bff6' },
							{ offset: 0.5, color: '#188df0' },
							{ offset: 1, color: '#188df0' }
						])
					},
					emphasis: {
						itemStyle: {
							color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
								{ offset: 0, color: '#2378f7' },
								{ offset: 0.7, color: '#2378f7' },
								{ offset: 1, color: '#83bff6' }
							])
						}
					}
				}]
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
	}
	
	// 渲染使用趋势柱状图
	if (trendChartRef.value) {
		const trendChart = echarts.init(trendChartRef.value);
		const usageStats = statistics.usage_stats || {};
		
		// 确保有数据才渲染图表
		const hasData = Object.values(usageStats).some(v => v > 0);
		
		if (hasData) {
			const option = {
				tooltip: {
					trigger: 'axis',
					axisPointer: {
						type: 'shadow'
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
					data: ['今日', '本周', '本月'],
					axisLabel: {
						fontSize: 12
					}
				},
				yAxis: {
					type: 'value',
					axisLabel: {
						fontSize: 12
					}
				},
				series: [{
					name: '使用次数',
					type: 'bar',
					data: [
						usageStats.today || 0,
						usageStats.this_week || 0,
						usageStats.this_month || 0
					],
					itemStyle: {
						color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
							{ offset: 0, color: '#ffecd2' },
							{ offset: 0.5, color: '#fcb69f' },
							{ offset: 1, color: '#fcb69f' }
						])
					},
					emphasis: {
						itemStyle: {
							color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
								{ offset: 0, color: '#fcb69f' },
								{ offset: 0.7, color: '#fcb69f' },
								{ offset: 1, color: '#ffecd2' }
							])
						}
					}
				}]
			};
			
			trendChart.setOption(option);
		} else {
			// 显示无数据提示
			trendChart.setOption({
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
	}
};

// 处理关闭
const handleClose = () => {
	visible.value = false;
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
});
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

.stat-icon.active {
	background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-icon.conversations {
	background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.messages {
	background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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

.usage-stats {
	margin-bottom: 20px;
}

.usage-card {
	height: 100px;
}

.usage-content {
	display: flex;
	align-items: center;
	height: 100%;
	padding: 10px;
}

.usage-icon {
	width: 50px;
	height: 50px;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 15px;
	font-size: 20px;
	color: white;
	flex-shrink: 0;
}

.usage-icon.today {
	background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.usage-icon.week {
	background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.usage-icon.month {
	background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.usage-info {
	flex: 1;
	min-width: 0;
}

.usage-number {
	font-size: 24px;
	font-weight: bold;
	color: #303133;
	line-height: 1;
	margin-bottom: 5px;
}

.usage-label {
	font-size: 12px;
	color: #909399;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.charts-row {
	margin-bottom: 20px;
}

.chart-card {
	height: 300px;
}

.chart-container {
	height: 220px;
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