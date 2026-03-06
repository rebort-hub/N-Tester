<template>
	<div class="statistics-view">
		<!-- 总体统计 -->
		<div class="overview-stats">
			<el-row :gutter="20">
				<el-col :span="8">
					<div class="stat-card" :style="{ '--stat-bg': getStatCardColor('total') }">
						<div class="stat-icon">
							<el-icon :size="24"><DataAnalysis /></el-icon>
						</div>
						<div class="stat-content">
							<div class="stat-value">{{ statistics.total_records }}</div>
							<div class="stat-title">总使用次数</div>
						</div>
					</div>
				</el-col>
				<el-col :span="8">
					<div class="stat-card" :style="{ '--stat-bg': getStatCardColor('tools') }">
						<div class="stat-icon">
							<el-icon :size="24"><Grid /></el-icon>
						</div>
						<div class="stat-content">
							<div class="stat-value">{{ usedToolsCount }}</div>
							<div class="stat-title">使用工具数</div>
						</div>
					</div>
				</el-col>
				<el-col :span="8">
					<div class="stat-card" :style="{ '--stat-bg': getStatCardColor('days') }">
						<div class="stat-icon">
							<el-icon :size="24"><Clock /></el-icon>
						</div>
						<div class="stat-content">
							<div class="stat-value">{{ activeDays }}</div>
							<div class="stat-title">活跃天数</div>
						</div>
					</div>
				</el-col>
			</el-row>
		</div>

		<!-- 分类使用统计 -->
		<div class="category-stats">
			<h3>分类使用统计</h3>
			<div class="category-stats-grid">
				<div
					v-for="(count, category) in statistics.category_stats"
					:key="category"
					class="category-stat-item"
					:style="{ '--category-color': getCategoryStatColor(category) }"
				>
					<div class="category-stat-header">
						<div class="category-icon">
							<el-icon :size="20">
								<component :is="getCategoryIcon(category)" />
							</el-icon>
						</div>
						<div class="category-info">
							<div class="category-name">{{ getCategoryDisplayName(category) }}</div>
							<div class="category-count">{{ count }} 次</div>
						</div>
					</div>
					<div class="category-progress">
						<div class="progress-bar">
							<div 
								class="progress-fill"
								:style="{ width: getPercentage(count, statistics.total_records) + '%' }"
							></div>
						</div>
						<div class="progress-text">{{ getPercentage(count, statistics.total_records) }}%</div>
					</div>
				</div>
			</div>
		</div>

		<!-- 使用趋势图表 -->
		<div class="trend-chart">
			<h3>使用趋势</h3>
			<div class="chart-container">
				<div class="trend-chart-content">
					<div class="chart-header">
						<el-radio-group v-model="trendPeriod" size="small" @change="updateTrendChart">
							<el-radio-button label="7">最近7天</el-radio-button>
							<el-radio-button label="30">最近30天</el-radio-button>
						</el-radio-group>
					</div>
					<div class="chart-body">
						<div v-if="trendData.length === 0" class="chart-empty">
							<el-empty description="暂无使用数据" :image-size="80" />
						</div>
						<div v-else class="trend-bars">
							<div
								v-for="(item, index) in trendData"
								:key="index"
								class="trend-bar-item"
								:title="`${item.label}: ${item.count} 次使用`"
							>
								<div class="bar-container">
									<div
										class="bar-fill"
										:style="{
											height: getTrendBarHeight(item.count) + '%',
											background: `linear-gradient(to top, var(--el-color-primary), var(--el-color-primary-light-3))`
										}"
									></div>
								</div>
								<div class="bar-label">{{ item.label }}</div>
								<div class="bar-count">{{ item.count }}</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- 最近使用的工具 -->
		<div class="recent-tools">
			<h3>最近使用</h3>
			<div class="recent-tools-container">
				<el-table :data="statistics.recent_tools" stripe max-height="300" style="width: 100%">
					<el-table-column label="工具名称" min-width="200">
						<template #default="{ row }">
							<div class="tool-info">
								<div class="tool-name">{{ getToolDisplayName(row.tool_name) }}</div>
								<el-tag size="small" type="info">{{ row.tool_category_display }}</el-tag>
							</div>
						</template>
					</el-table-column>
					<el-table-column label="使用场景" prop="tool_scenario_display" min-width="120" />
					<el-table-column label="使用时间" min-width="160">
						<template #default="{ row }">
							{{ formatDateTime(row.created_at) }}
						</template>
					</el-table-column>
					<el-table-column label="相对时间" min-width="100">
						<template #default="{ row }">
							<el-tag size="small" type="success">
								{{ getRelativeTime(row.created_at) }}
							</el-tag>
						</template>
					</el-table-column>
				</el-table>
			</div>
		</div>

		<!-- 使用习惯分析 -->
		<div class="usage-analysis">
			<h3>使用习惯分析</h3>
			<el-row :gutter="20">
				<el-col :span="12">
					<div class="analysis-card">
						<h4>最常用工具</h4>
						<div class="top-tools">
							<div
								v-for="(tool, index) in topTools"
								:key="tool.name"
								class="tool-item"
							>
								<div class="tool-rank">{{ index + 1 }}</div>
								<div class="tool-details">
									<div class="tool-name">{{ tool.displayName }}</div>
									<div class="tool-count">{{ tool.count }} 次使用</div>
								</div>
							</div>
						</div>
					</div>
				</el-col>
				<el-col :span="12">
					<div class="analysis-card">
						<h4>使用时间分布</h4>
						<div class="time-distribution">
							<div
								v-for="(count, hour) in hourlyDistribution"
								:key="hour"
								class="hour-item"
							>
								<div class="hour-label">{{ hour }}:00</div>
								<div class="hour-bar">
									<div
										class="hour-fill"
										:style="{ width: getHourPercentage(count) + '%' }"
									></div>
								</div>
								<div class="hour-count">{{ count }}</div>
							</div>
						</div>
					</div>
				</el-col>
			</el-row>
		</div>

		<!-- 导出统计报告 -->
		<div class="export-actions">
			<el-button type="primary" @click="exportReport">
				<el-icon><Download /></el-icon>
				导出统计报告
			</el-button>
			<el-button @click="refreshStatistics">
				<el-icon><Refresh /></el-icon>
				刷新统计
			</el-button>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue';
import { ElMessage } from 'element-plus';
import { Download, Refresh, User, Edit, Document, DataAnalysis, Grid, Lock, Clock } from '@element-plus/icons-vue';
import { getStatistics, type Statistics } from '/@/api/v1/data_factory';

// 响应式数据
const loading = ref(false);
const trendPeriod = ref('7'); // 趋势图表时间周期
const trendData = ref<Array<{label: string, count: number, date: string}>>([]);
const statistics = reactive<Statistics>({
	total_records: 0,
	category_stats: {},
	scenario_stats: {},
	recent_tools: []
});

// 图标映射
const iconMap: Record<string, any> = {
	'测试数据': User,
	'JSON工具': Edit,
	'字符工具': Document,
	'编码工具': DataAnalysis,
	'随机工具': Grid,
	'加密工具': Lock,
	'Crontab工具': Clock,
};

// 工具显示名称映射（完整版）
const toolDisplayMap: Record<string, string> = {
	// 测试数据工具
	generate_chinese_name: '生成中文姓名',
	generate_chinese_phone: '生成手机号',
	generate_chinese_email: '生成邮箱',
	generate_chinese_address: '生成中文地址',
	generate_id_card: '生成身份证号',
	generate_company_name: '生成公司名称',
	generate_bank_card: '生成银行卡号',
	generate_hk_id_card: '生成香港身份证',
	generate_business_license: '生成营业执照号',
	generate_coordinates: '生成经纬度',
	generate_user_profile: '生成用户档案',
	
	// JSON工具
	format_json: 'JSON格式化',
	validate_json: 'JSON校验',
	json_diff_enhanced: 'JSON对比',
	jsonpath_query: 'JSONPath查询',
	json_flatten: 'JSON扁平化',
	json_path_list: 'JSON路径列表',
	json_to_xml: 'JSON转XML',
	xml_to_json: 'XML转JSON',
	json_to_yaml: 'JSON转YAML',
	yaml_to_json: 'YAML转JSON',
	
	// 字符工具
	text_diff: '文本对比',
	regex_test: '正则测试',
	remove_whitespace: '去除空格换行',
	replace_string: '字符串替换',
	escape_string: '字符串转义',
	unescape_string: '字符串反转义',
	word_count: '字数统计',
	case_convert: '大小写转换',
	string_format: '字符串格式化',
	
	// 编码工具
	generate_barcode: '生成条形码',
	generate_qrcode: '生成二维码',
	decode_qrcode: '二维码解析',
	timestamp_convert: '时间戳转换',
	base_convert: '进制转换',
	unicode_convert: 'Unicode转换',
	ascii_convert: 'ASCII转换',
	color_convert: '颜色值转换',
	url_encode: 'URL编码',
	url_decode: 'URL解码',
	jwt_decode: 'JWT解码',
	image_to_base64: '图片转Base64',
	base64_to_image: 'Base64转图片',
	base64_encode: 'Base64编码',
	base64_decode: 'Base64解码',
	
	// 随机工具
	random_int: '随机整数',
	random_float: '随机浮点数',
	random_string: '随机字符串',
	random_uuid: '随机UUID',
	random_boolean: '随机布尔值',
	random_mac_address: '随机MAC地址',
	random_ip_address: '随机IP地址',
	random_date: '随机日期',
	random_password: '随机密码',
	random_color: '随机颜色',
	random_sequence: '随机序列数据',
	
	// 加密工具
	md5_hash: 'MD5加密',
	sha1_hash: 'SHA1加密',
	sha256_hash: 'SHA256加密',
	sha512_hash: 'SHA512加密',
	hash_comparison: '哈希值比对',
	aes_encrypt: 'AES加密',
	aes_decrypt: 'AES解密',
	password_strength: '密码强度分析',
	generate_salt: '随机盐值',
	
	// Crontab工具
	generate_expression: '生成Crontab表达式',
	parse_expression: '解析Crontab表达式',
	get_next_runs: '获取下次执行时间',
	validate_expression: '验证Crontab表达式',
};

// 分类显示名称映射
const categoryDisplayMap: Record<string, string> = {
	'test_data': '测试数据',
	'json': 'JSON工具',
	'string': '字符工具',
	'encoding': '编码工具',
	'random': '随机工具',
	'encryption': '加密工具',
	'crontab': 'Crontab工具',
};

// 获取统计卡片颜色
const getStatCardColor = (type: string): string => {
	const colorMap: Record<string, string> = {
		'total': 'linear-gradient(135deg, #667eea, #764ba2)', // 紫蓝渐变
		'tools': 'linear-gradient(135deg, #43e97b, #38f9d7)', // 绿青渐变
		'days': 'linear-gradient(135deg, #fa709a, #fee140)', // 粉黄渐变
	};
	return colorMap[type] || 'linear-gradient(135deg, var(--el-color-primary), var(--el-color-success))';
};

// 获取分类统计颜色
const getCategoryStatColor = (category: string): string => {
	const colorMap: Record<string, string> = {
		'test_data': '#667eea',
		'json': '#f093fb',
		'string': '#4facfe',
		'encoding': '#43e97b',
		'random': '#fa709a',
		'encryption': '#a8edea',
		'crontab': '#ff9a9e',
	};
	return colorMap[category] || '#409eff';
};

// 获取分类显示名称
const getCategoryDisplayName = (category: string): string => {
	return categoryDisplayMap[category] || category;
};

// 计算属性
const usedToolsCount = computed(() => {
	// 从最近使用的工具中统计唯一工具数量
	const uniqueTools = new Set(statistics.recent_tools.map(tool => tool.tool_name));
	return uniqueTools.size;
});

const activeDays = computed(() => {
	// 从最近使用记录中计算活跃天数
	const uniqueDates = new Set(
		statistics.recent_tools.map(tool => {
			const date = new Date(tool.created_at);
			return date.toDateString();
		})
	);
	return uniqueDates.size;
});

const topTools = computed(() => {
	// 统计工具使用频率
	const toolCounts: Record<string, number> = {};
	statistics.recent_tools.forEach(tool => {
		toolCounts[tool.tool_name] = (toolCounts[tool.tool_name] || 0) + 1;
	});
	
	return Object.entries(toolCounts)
		.map(([name, count]) => ({
			name,
			displayName: getToolDisplayName(name),
			count
		}))
		.sort((a, b) => b.count - a.count)
		.slice(0, 5);
});

const hourlyDistribution = computed(() => {
	// 统计每小时使用分布
	const hours: Record<string, number> = {};
	for (let i = 0; i < 24; i++) {
		hours[i.toString().padStart(2, '0')] = 0;
	}
	
	statistics.recent_tools.forEach(tool => {
		const hour = new Date(tool.created_at).getHours();
		const hourKey = hour.toString().padStart(2, '0');
		hours[hourKey]++;
	});
	
	return hours;
});

// 获取分类图标
const getCategoryIcon = (category: string) => {
	return iconMap[category] || Document;
};

// 获取工具显示名称
const getToolDisplayName = (toolName: string): string => {
	return toolDisplayMap[toolName] || toolName;
};

// 获取百分比
const getPercentage = (value: number, total: number): number => {
	if (total === 0) return 0;
	return Math.round((value / total) * 100);
};

// 获取小时使用百分比
const getHourPercentage = (count: number): number => {
	const maxCount = Math.max(...Object.values(hourlyDistribution.value));
	if (maxCount === 0) return 0;
	return (count / maxCount) * 100;
};

// 格式化日期时间
const formatDateTime = (dateTime: string): string => {
	if (!dateTime) return '';
	return new Date(dateTime).toLocaleString('zh-CN');
};

// 获取相对时间
const getRelativeTime = (dateTime: string): string => {
	if (!dateTime) return '';
	
	const now = new Date();
	const date = new Date(dateTime);
	const diffMs = now.getTime() - date.getTime();
	const diffMins = Math.floor(diffMs / (1000 * 60));
	const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
	const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
	
	if (diffMins < 1) return '刚刚';
	if (diffMins < 60) return `${diffMins}分钟前`;
	if (diffHours < 24) return `${diffHours}小时前`;
	if (diffDays < 7) return `${diffDays}天前`;
	return formatDateTime(dateTime);
};

// 加载统计数据
const loadStatistics = async () => {
	try {
		loading.value = true;
		const response = await getStatistics();
		if (response.data) {
			Object.assign(statistics, response.data);
			// 数据加载完成后更新趋势图表
			await nextTick();
			updateTrendChart();
		}
	} catch (error) {
		console.error('加载统计数据失败:', error);
		ElMessage.error('加载统计数据失败');
	} finally {
		loading.value = false;
	}
};

// 刷新统计
const refreshStatistics = async () => {
	await loadStatistics();
	ElMessage.success('统计数据已刷新');
};

// 导出报告
const exportReport = () => {
	try {
		const reportData = {
			总体统计: {
				总使用次数: statistics.total_records,
				使用工具数: usedToolsCount.value,
				活跃天数: activeDays.value
			},
			分类统计: statistics.category_stats,
			最常用工具: topTools.value,
			使用时间分布: hourlyDistribution.value,
			最近使用: statistics.recent_tools.slice(0, 10),
			导出时间: new Date().toLocaleString('zh-CN')
		};
		
		const dataStr = JSON.stringify(reportData, null, 2);
		const blob = new Blob([dataStr], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = url;
		link.download = `数据工厂使用统计_${new Date().toISOString().split('T')[0]}.json`;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		URL.revokeObjectURL(url);
		
		ElMessage.success('统计报告已导出');
	} catch (error) {
		console.error('导出报告失败:', error);
		ElMessage.error('导出报告失败');
	}
};

// 获取趋势柱状图高度百分比
const getTrendBarHeight = (count: number): number => {
	if (trendData.value.length === 0) return 0;
	const maxCount = Math.max(...trendData.value.map(item => item.count));
	if (maxCount === 0) return 0;
	return (count / maxCount) * 100;
};

// 更新趋势图表数据
const updateTrendChart = () => {
	const days = parseInt(trendPeriod.value);
	const now = new Date();
	const chartData: Array<{label: string, count: number, date: string}> = [];
	
	// 生成日期范围
	for (let i = days - 1; i >= 0; i--) {
		const date = new Date(now);
		date.setDate(date.getDate() - i);
		const dateStr = date.toISOString().split('T')[0];
		
		// 统计该日期的使用次数
		const dayCount = statistics.recent_tools.filter(tool => {
			if (!tool.created_at) return false;
			const toolDate = new Date(tool.created_at).toISOString().split('T')[0];
			return toolDate === dateStr;
		}).length;
		
		// 格式化标签
		let label: string;
		if (days === 7) {
			// 7天显示星期几
			const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
			const today = now.toISOString().split('T')[0];
			if (dateStr === today) {
				label = '今天';
			} else if (i === 1) {
				label = '昨天';
			} else {
				label = weekdays[date.getDay()];
			}
		} else {
			// 30天显示月/日格式
			label = `${date.getMonth() + 1}/${date.getDate()}`;
		}
		
		chartData.push({
			label,
			count: dayCount,
			date: dateStr
		});
	}
	
	trendData.value = chartData;
};

// 组件挂载时加载数据
onMounted(() => {
	loadStatistics();
});
</script>

<style scoped lang="scss">
.statistics-view {
	.overview-stats {
		margin-bottom: 30px;
		padding: 20px;
		background: var(--el-bg-color);
		border-radius: var(--el-border-radius-base);
		box-shadow: var(--el-box-shadow-light);
		border: 1px solid var(--el-border-color-light);
	}

	.category-stats,
	.trend-chart,
	.recent-tools,
	.usage-analysis {
		margin-bottom: 30px;
		padding: 20px;
		background: var(--el-bg-color);
		border-radius: var(--el-border-radius-base);
		box-shadow: var(--el-box-shadow-light);
		border: 1px solid var(--el-border-color-light);

		h3 {
			margin: 0 0 20px 0;
			font-size: 18px;
			color: var(--el-text-color-primary);
		}
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 16px;
	}

	.category-stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
		gap: 20px;
	}

	.category-stat-item {
		padding: 20px;
		background: var(--el-fill-color-lighter);
		border-radius: var(--el-border-radius-base);
		border: 1px solid var(--el-border-color-light);
		transition: all var(--el-transition-duration);
		cursor: pointer;

		&:hover {
			transform: translateY(-2px);
			box-shadow: var(--el-box-shadow);
			border-color: var(--category-color);
		}

		.category-stat-header {
			display: flex;
			align-items: center;
			margin-bottom: 16px;

			.category-icon {
				display: flex;
				align-items: center;
				justify-content: center;
				width: 40px;
				height: 40px;
				background: var(--category-color);
				border-radius: var(--el-border-radius-base);
				color: var(--el-color-white);
				margin-right: 12px;
				box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
			}

			.category-info {
				flex: 1;

				.category-name {
					font-size: 16px;
					font-weight: 600;
					color: var(--el-text-color-primary);
					margin-bottom: 2px;
				}

				.category-count {
					font-size: 14px;
					color: var(--el-text-color-regular);
				}
			}
		}

		.category-progress {
			.progress-bar {
				width: 100%;
				height: 8px;
				background: var(--el-border-color-light);
				border-radius: 4px;
				overflow: hidden;
				margin-bottom: 8px;

				.progress-fill {
					height: 100%;
					background: var(--category-color);
					border-radius: 4px;
					transition: width var(--el-transition-duration-slow);
					position: relative;

					&::after {
						content: '';
						position: absolute;
						top: 0;
						right: 0;
						width: 100%;
						height: 100%;
						background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3));
						animation: shimmer 2s infinite;
					}
				}
			}

			.progress-text {
				text-align: right;
				font-size: 12px;
				color: var(--el-text-color-placeholder);
				font-weight: 600;
			}
		}
	}

	.stat-card {
		display: flex;
		align-items: center;
		padding: 20px;
		background: var(--el-fill-color-lighter);
		border-radius: var(--el-border-radius-base);
		border: 1px solid var(--el-border-color-light);
		transition: all var(--el-transition-duration);
		cursor: pointer;

		&:hover {
			transform: translateY(-2px);
			box-shadow: var(--el-box-shadow);
		}

		.stat-icon {
			display: flex;
			align-items: center;
			justify-content: center;
			width: 56px;
			height: 56px;
			background: var(--stat-bg, linear-gradient(135deg, var(--el-color-primary), var(--el-color-success)));
			border-radius: var(--el-border-radius-base);
			color: var(--el-color-white);
			margin-right: 16px;
			box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
		}

		.stat-content {
			flex: 1;

			.stat-value {
				font-size: 28px;
				font-weight: 700;
				color: var(--el-text-color-primary);
				margin-bottom: 4px;
				line-height: 1;
			}

			.stat-title {
				font-size: 14px;
				color: var(--el-text-color-regular);
				font-weight: 500;
			}
		}
	}

	.chart-container {
		.trend-chart-content {
			.chart-header {
				display: flex;
				justify-content: center;
				margin-bottom: 20px;
			}

			.chart-body {
				.chart-empty {
					height: 200px;
					display: flex;
					align-items: center;
					justify-content: center;
				}

				.trend-bars {
					display: flex;
					align-items: end;
					justify-content: space-between;
					height: 200px;
					padding: 0 10px;
					gap: 4px;
					background: var(--el-fill-color-lighter);
					border-radius: var(--el-border-radius-base);
					border: 1px solid var(--el-border-color-light);

					.trend-bar-item {
						flex: 1;
						display: flex;
						flex-direction: column;
						align-items: center;
						min-width: 0;
						cursor: pointer;
						transition: all var(--el-transition-duration);

						&:hover {
							transform: translateY(-2px);

							.bar-fill {
								opacity: 0.8;
								box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
							}

							.bar-count {
								color: var(--el-color-primary);
								font-weight: 700;
							}
						}

						.bar-container {
							width: 100%;
							height: 160px;
							display: flex;
							align-items: end;
							justify-content: center;
							margin-bottom: 8px;

							.bar-fill {
								width: 80%;
								min-height: 2px;
								border-radius: 2px 2px 0 0;
								transition: all var(--el-transition-duration);
								position: relative;

								&::after {
									content: '';
									position: absolute;
									top: -4px;
									left: 50%;
									transform: translateX(-50%);
									width: 6px;
									height: 6px;
									background: var(--el-color-primary);
									border-radius: 50%;
									opacity: 0;
									transition: opacity var(--el-transition-duration);
								}

								&:hover::after {
									opacity: 1;
								}
							}
						}

						.bar-label {
							font-size: 12px;
							color: var(--el-text-color-regular);
							margin-bottom: 2px;
							text-align: center;
							white-space: nowrap;
							overflow: hidden;
							text-overflow: ellipsis;
							width: 100%;
						}

						.bar-count {
							font-size: 11px;
							color: var(--el-text-color-placeholder);
							font-weight: 600;
							text-align: center;
							transition: all var(--el-transition-duration);
						}
					}
				}
			}
		}

		.chart {
			width: 100%;
			height: 200px;
		}

		.chart-placeholder {
			height: 200px;
			display: flex;
			align-items: center;
			justify-content: center;
			background: var(--el-fill-color-lighter);
			border-radius: var(--el-border-radius-base);
			color: var(--el-text-color-placeholder);
			font-size: 14px;
		}
	}

	.recent-tools {
		.recent-tools-container {
			width: 100%;
			overflow: hidden;

			:deep(.el-table) {
				width: 100% !important;
			}

			:deep(.el-table__body-wrapper) {
				overflow-x: auto;
			}
		}

		.tool-info {
			.tool-name {
				font-weight: 600;
				margin-bottom: 4px;
				color: var(--el-text-color-primary);
			}
		}
	}

	.analysis-card {
		padding: 16px;
		background: var(--el-fill-color-lighter);
		border-radius: var(--el-border-radius-base);
		border: 1px solid var(--el-border-color-light);
		height: 100%;

		h4 {
			margin: 0 0 16px 0;
			font-size: 16px;
			color: var(--el-text-color-primary);
		}

		.top-tools {
			.tool-item {
				display: flex;
				align-items: center;
				padding: 8px 0;
				border-bottom: 1px solid var(--el-border-color-light);

				&:last-child {
					border-bottom: none;
				}

				.tool-rank {
					display: flex;
					align-items: center;
					justify-content: center;
					width: 24px;
					height: 24px;
					background: var(--el-color-primary);
					color: var(--el-color-white);
					border-radius: 50%;
					font-size: 12px;
					font-weight: 600;
					margin-right: 12px;
				}

				.tool-details {
					flex: 1;

					.tool-name {
						font-size: 14px;
						color: var(--el-text-color-primary);
						margin-bottom: 2px;
					}

					.tool-count {
						font-size: 12px;
						color: var(--el-text-color-placeholder);
					}
				}
			}
		}

		.time-distribution {
			max-height: 300px;
			overflow-y: auto;

			.hour-item {
				display: flex;
				align-items: center;
				padding: 4px 0;

				.hour-label {
					width: 40px;
					font-size: 12px;
					color: var(--el-text-color-regular);
				}

				.hour-bar {
					flex: 1;
					height: 8px;
					background: var(--el-border-color-light);
					border-radius: var(--el-border-radius-small);
					margin: 0 8px;
					overflow: hidden;

					.hour-fill {
						height: 100%;
						background: var(--el-color-primary);
						transition: width var(--el-transition-duration);
					}
				}

				.hour-count {
					width: 30px;
					text-align: right;
					font-size: 12px;
					color: var(--el-text-color-regular);
				}
			}
		}
	}

	.export-actions {
		display: flex;
		justify-content: center;
		gap: 12px;
		padding: 20px;
		background: var(--el-bg-color);
		border-radius: var(--el-border-radius-base);
		box-shadow: var(--el-box-shadow-light);
		border: 1px solid var(--el-border-color-light);
	}
}

// 动画效果
@keyframes shimmer {
	0% {
		transform: translateX(-100%);
	}
	100% {
		transform: translateX(100%);
	}
}

// 响应式设计
@media (max-width: 768px) {
	.statistics-view {
		.overview-stats {
			padding: 15px;

			.stat-card {
				padding: 12px;

				.stat-icon {
					width: 40px;
					height: 40px;
					margin-right: 12px;
				}

				.stat-content {
					.stat-value {
						font-size: 16px;
					}
				}
			}
		}

		.category-stats,
		.trend-chart,
		.recent-tools,
		.usage-analysis {
			padding: 15px;

			h3 {
				font-size: 16px;
			}
		}

		.chart-container .trend-chart-content .chart-body .trend-bars {
			gap: 2px;
			padding: 0 5px;

			.trend-bar-item {
				.bar-label {
					font-size: 10px;
				}

				.bar-count {
					font-size: 10px;
				}
			}
		}

		.export-actions {
			flex-direction: column;
			padding: 15px;

			.el-button {
				width: 100%;
			}
		}
	}
}
</style>