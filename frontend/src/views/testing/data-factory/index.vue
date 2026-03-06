<template>
	<div class="data-factory-container">
		<!-- 页面头部 -->
		<el-card shadow="hover" class="page-header-card">
			<div class="page-header">
				<div class="header-left">
					<h2 class="page-title">
						<el-icon><Tools /></el-icon>
						数据工厂
					</h2>
					<p class="page-description">提供70个数据生成和处理工具，助力测试数据准备</p>
				</div>
				<div class="header-right">
					<el-button type="primary" @click="showHistory = true">
						<el-icon><Clock /></el-icon>
						使用记录
					</el-button>
					<el-button @click="showStatistics = true">
						<el-icon><DataAnalysis /></el-icon>
						统计信息
					</el-button>
				</div>
			</div>
		</el-card>

		<!-- 工具分类卡片 -->
		<div class="categories-grid">
			<el-card
				v-for="category in categories"
				:key="category.category"
				shadow="hover"
				class="category-card"
				@click="selectCategory(category)"
			>
				<div class="category-content">
					<div 
						class="category-icon"
						:style="{ '--category-bg': getCategoryColor(category.category) }"
					>
						<el-icon :size="32">
							<component :is="getIconComponent(category.icon)" />
						</el-icon>
					</div>
					<div class="category-info">
						<h3 class="category-name">{{ category.name }}</h3>
						<p class="category-description">{{ category.tools.length }} 个工具</p>
					</div>
					<div class="category-arrow">
						<el-icon><ArrowRight /></el-icon>
					</div>
				</div>
			</el-card>
		</div>

		<!-- 工具列表抽屉 -->
		<el-drawer
			v-model="toolDrawerVisible"
			:title="selectedCategory?.name || '工具列表'"
			direction="rtl"
			size="60%"
		>
			<ToolList
				v-if="selectedCategory"
				:category="selectedCategory"
				@execute="handleToolExecute"
				@batch-generate="handleBatchGenerate"
			/>
		</el-drawer>

		<!-- 使用记录抽屉 -->
		<el-drawer
			v-model="showHistory"
			title="使用记录"
			direction="rtl"
			size="70%"
		>
			<HistoryList @execute-again="handleExecuteAgain" />
		</el-drawer>

		<!-- 统计信息对话框 -->
		<el-dialog
			v-model="showStatistics"
			title="使用统计"
			width="800px"
		>
			<StatisticsView />
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Tools, Clock, DataAnalysis, ArrowRight, User, Edit, Document, Grid, Setting, Lock } from '@element-plus/icons-vue';
import { getToolCategories, type ToolCategory } from '/@/api/v1/data_factory';
import ToolList from './components/ToolList.vue';
import HistoryList from './components/HistoryList.vue';
import StatisticsView from './components/StatisticsView.vue';

// 响应式数据
const categories = ref<ToolCategory[]>([]);
const selectedCategory = ref<ToolCategory | null>(null);
const toolDrawerVisible = ref(false);
const showHistory = ref(false);
const showStatistics = ref(false);
const loading = ref(false);

// 图标映射
const iconMap: Record<string, any> = {
	user: User,
	edit: Edit,
	document: Document,
	code: Grid,
	distribute: Setting,
	lock: Lock,
	clock: Clock,
};

// 为每个工具分类分配不同的颜色
const getCategoryColor = (category: string): string => {
	const colorMap: Record<string, string> = {
		'test_data': 'linear-gradient(135deg, #667eea, #764ba2)', // 紫蓝渐变
		'json': 'linear-gradient(135deg, #f093fb, #f5576c)', // 粉红渐变
		'string': 'linear-gradient(135deg, #4facfe, #00f2fe)', // 蓝青渐变
		'encoding': 'linear-gradient(135deg, #43e97b, #38f9d7)', // 绿青渐变
		'random': 'linear-gradient(135deg, #fa709a, #fee140)', // 粉黄渐变
		'encryption': 'linear-gradient(135deg, #a8edea, #fed6e3)', // 青粉渐变
		'crontab': 'linear-gradient(135deg, #ff9a9e, #fad0c4)', // 橙粉渐变
	};
	
	const color = colorMap[category] || 'linear-gradient(135deg, var(--el-color-primary), var(--el-color-success))';
	console.log(`Category: ${category}, Color: ${color}`); // 调试信息
	return color;
};

// 获取图标组件
const getIconComponent = (iconName: string) => {
	return iconMap[iconName] || Tools;
};

// 选择分类
const selectCategory = (category: ToolCategory) => {
	selectedCategory.value = category;
	toolDrawerVisible.value = true;
};

// 处理工具执行
const handleToolExecute = (result: any) => {
	console.log('handleToolExecute called with:', result);
	if (result && result.error) {
		ElMessage.error(`执行失败: ${result.error}`);
	} else {
		ElMessage.success(`${result.tool_name || '工具'}执行成功`);
	}
};

// 处理批量生成
const handleBatchGenerate = (result: any) => {
	console.log('handleBatchGenerate called with:', result);
	if (result && result.error) {
		ElMessage.error(`批量生成失败: ${result.error}`);
	} else {
		// 根据不同的数据结构获取数量
		let count = 0;
		if (result?.results?.length) {
			count = result.results.length;
		} else if (result?.count) {
			count = result.count;
		} else if (result?.success_count !== undefined) {
			count = result.success_count;
		} else if (Array.isArray(result)) {
			count = result.length;
		} else {
			count = 1; // 默认为1
		}
		
		ElMessage.success(`${result.tool_name || '工具'}批量生成成功，共生成 ${count} 条数据`);
	}
};

// 处理重新执行
const handleExecuteAgain = (record: any) => {
	// 根据记录信息重新执行工具
	const category = categories.value.find(c => c.category === record.tool_category);
	if (category) {
		selectCategory(category);
	}
};

// 加载工具分类
const loadCategories = async () => {
	try {
		loading.value = true;
		const response = await getToolCategories();
		if (response.data) {
			categories.value = response.data.categories || [];
		}
	} catch (error) {
		console.error('加载工具分类失败:', error);
		ElMessage.error('加载工具分类失败');
	} finally {
		loading.value = false;
	}
};

// 组件挂载时加载数据
onMounted(() => {
	loadCategories();
});
</script>

<style scoped lang="scss">
.data-factory-container {
	padding: 20px;

	.page-header-card {
		margin-bottom: 30px;

		.page-header {
			display: flex;
			justify-content: space-between;
			align-items: center;

			.header-left {
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
			}

			.header-right {
				display: flex;
				gap: 12px;
			}
		}
	}

	.categories-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 20px;
	}

	.category-card {
		cursor: pointer;
		transition: all var(--el-transition-duration);

		&:hover {
			transform: translateY(-2px);
		}

		.category-content {
			display: flex;
			align-items: center;

			.category-icon {
				display: flex;
				align-items: center;
				justify-content: center;
				width: 60px;
				height: 60px;
				background: var(--category-bg, linear-gradient(135deg, var(--el-color-primary), var(--el-color-success)));
				border-radius: var(--el-border-radius-base);
				color: var(--el-color-white);
				margin-right: 16px;
			}

			.category-info {
				flex: 1;

				.category-name {
					margin: 0 0 4px 0;
					font-size: 18px;
					font-weight: 600;
					color: var(--el-text-color-primary);
				}

				.category-description {
					margin: 0;
					color: var(--el-text-color-placeholder);
					font-size: 14px;
				}
			}

			.category-arrow {
				color: var(--el-text-color-disabled);
				transition: color var(--el-transition-duration);
			}
		}

		&:hover .category-content .category-arrow {
			color: var(--el-color-primary);
		}
	}
}

// 响应式设计
@media (max-width: 768px) {
	.data-factory-container {
		padding: 10px;

		.page-header-card .page-header {
			flex-direction: column;
			align-items: flex-start;
			gap: 16px;

			.header-right {
				width: 100%;
				justify-content: flex-end;
			}
		}

		.categories-grid {
			grid-template-columns: 1fr;
		}

		.category-card .category-content .category-icon {
			width: 48px;
			height: 48px;
		}
	}
}
</style>