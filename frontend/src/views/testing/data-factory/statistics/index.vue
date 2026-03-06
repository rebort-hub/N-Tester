<template>
	<div class="data-factory-statistics-container">
		<!-- 页面头部 -->
		<el-card shadow="hover" class="page-header-card">
			<div class="page-header">
				<div class="header-left">
					<h2 class="page-title">
						<el-icon><PieChart /></el-icon>
						统计分析
					</h2>
					<p class="page-description">数据工厂使用情况统计和分析</p>
				</div>
				<div class="header-right">
					<el-button @click="refreshStatistics">
						<el-icon><Refresh /></el-icon>
						刷新统计
					</el-button>
					<el-button type="primary" @click="exportReport">
						<el-icon><Download /></el-icon>
						导出报告
					</el-button>
				</div>
			</div>
		</el-card>

		<!-- 统计内容 -->
		<el-card shadow="hover" class="statistics-content-card">
			<StatisticsView />
		</el-card>
	</div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { PieChart, Refresh, Download } from '@element-plus/icons-vue';
import StatisticsView from '/@/views/testing/data-factory/components/StatisticsView.vue';

// 响应式数据
const loading = ref(false);

// 刷新统计
const refreshStatistics = () => {
	// StatisticsView 组件会自动刷新
	ElMessage.success('统计数据已刷新');
};

// 导出报告
const exportReport = () => {
	try {
		// 这里可以调用导出API
		ElMessage.success('统计报告导出功能开发中...');
	} catch (error) {
		console.error('导出报告失败:', error);
		ElMessage.error('导出报告失败');
	}
};
</script>

<style scoped lang="scss">
.data-factory-statistics-container {
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

	.statistics-content-card {
		// StatisticsView组件内部已有样式，这里不需要额外padding
		:deep(.el-card__body) {
			padding: 0;
		}
	}
}

// 响应式设计
@media (max-width: 768px) {
	.data-factory-statistics-container {
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
	}
}
</style>