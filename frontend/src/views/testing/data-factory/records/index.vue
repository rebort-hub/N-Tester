<template>
	<div class="data-factory-records-container">
		<!-- 页面头部 -->
		<el-card shadow="hover" class="page-header-card">
			<div class="page-header">
				<div class="header-left">
					<h2 class="page-title">
						<el-icon><List /></el-icon>
						使用记录
					</h2>
					<p class="page-description">查看和管理数据工厂工具的使用记录</p>
				</div>
				<div class="header-right">
					<el-button @click="refreshRecords">
						<el-icon><Refresh /></el-icon>
						刷新
					</el-button>
					<el-button type="primary" @click="exportRecords">
						<el-icon><Download /></el-icon>
						导出记录
					</el-button>
				</div>
			</div>
		</el-card>

		<!-- 记录列表 -->
		<el-card shadow="hover" class="records-content-card">
			<HistoryList @execute-again="handleExecuteAgain" />
		</el-card>
	</div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { List, Refresh, Download } from '@element-plus/icons-vue';
import HistoryList from '/@/views/testing/data-factory/components/HistoryList.vue';

// 响应式数据
const loading = ref(false);

// 刷新记录
const refreshRecords = () => {
	// HistoryList 组件会自动刷新
	ElMessage.success('记录已刷新');
};

// 导出记录
const exportRecords = () => {
	try {
		// 这里可以调用导出API
		ElMessage.success('记录导出功能开发中...');
	} catch (error) {
		console.error('导出记录失败:', error);
		ElMessage.error('导出记录失败');
	}
};

// 处理重新执行
const handleExecuteAgain = (record: any) => {
	// 现在重新执行逻辑已经在HistoryList组件内部处理，不需要额外操作
	console.log('重新执行记录:', record);
};
</script>

<style scoped lang="scss">
.data-factory-records-container {
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

	.records-content-card {
		:deep(.el-card__body) {
			padding: 0;
		}
	}
}

// 响应式设计
@media (max-width: 768px) {
	.data-factory-records-container {
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