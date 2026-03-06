<template>
	<div class="result-display">
		<!-- 结果头部 -->
		<div class="result-header">
			<div class="result-info">
				<el-icon class="success-icon"><CircleCheck /></el-icon>
				<span class="result-title">执行成功</span>
				<el-tag v-if="recordId" type="info" size="small">
					记录ID: {{ recordId }}
				</el-tag>
			</div>
			<div class="result-actions">
				<el-button size="small" @click="copyResult">
					<el-icon><DocumentCopy /></el-icon>
					复制结果
				</el-button>
				<el-button size="small" @click="exportResult">
					<el-icon><Download /></el-icon>
					导出
				</el-button>
			</div>
		</div>

		<!-- 结果内容 -->
		<div class="result-content">
			<!-- 批量结果 -->
			<div v-if="isBatchResult" class="batch-result">
				<div class="batch-summary">
					<el-statistic title="生成数量" :value="result.count" />
					<el-statistic v-if="result.success_count" title="成功数量" :value="result.success_count" />
					<el-statistic v-if="result.failed_count" title="失败数量" :value="result.failed_count" />
				</div>
				<div class="batch-items">
					<h5>生成结果:</h5>
					<div class="result-list">
						<div
							v-for="(item, index) in result.results"
							:key="index"
							class="result-item"
						>
							<div class="item-index">{{ index + 1 }}</div>
							<div class="item-content">
								<ResultItem :data="item" :tool="tool" />
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- 单个结果 -->
			<div v-else class="single-result">
				<ResultItem :data="result.result" :tool="tool" />
			</div>
		</div>

		<!-- 结果统计 -->
		<div v-if="resultStats" class="result-stats">
			<el-descriptions title="结果统计" :column="3" size="small">
				<el-descriptions-item
					v-for="(value, key) in resultStats"
					:key="key"
					:label="formatStatLabel(key)"
				>
					{{ formatStatValue(value) }}
				</el-descriptions-item>
			</el-descriptions>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, defineProps } from 'vue';
import { ElMessage } from 'element-plus';
import { CircleCheck, DocumentCopy, Download } from '@element-plus/icons-vue';
import type { Tool } from '/@/api/v1/data_factory';
import ResultItem from './ResultItem.vue';

// Props
const props = defineProps<{
	result: any;
	tool: Tool;
}>();

// 计算属性
const isBatchResult = computed(() => {
	return props.result && Array.isArray(props.result.results);
});

const recordId = computed(() => {
	return props.result?.record_id;
});

const resultStats = computed(() => {
	const data = props.result?.result;
	if (!data || typeof data !== 'object') return null;

	// 提取统计信息
	const stats: Record<string, any> = {};
	Object.keys(data).forEach(key => {
		if (key.includes('length') || key.includes('count') || key.includes('size')) {
			stats[key] = data[key];
		}
	});

	return Object.keys(stats).length > 0 ? stats : null;
});

// 复制结果
const copyResult = async () => {
	try {
		let textToCopy = '';
		
		if (isBatchResult.value) {
			// 批量结果
			textToCopy = props.result.results
				.map((item: any, index: number) => `${index + 1}. ${formatResultForCopy(item)}`)
				.join('\n');
		} else {
			// 单个结果
			textToCopy = formatResultForCopy(props.result.result);
		}

		await navigator.clipboard.writeText(textToCopy);
		ElMessage.success('结果已复制到剪贴板');
	} catch (error) {
		console.error('复制失败:', error);
		ElMessage.error('复制失败');
	}
};

// 导出结果
const exportResult = () => {
	try {
		let dataToExport = '';
		
		if (isBatchResult.value) {
			// 批量结果
			dataToExport = JSON.stringify(props.result.results, null, 2);
		} else {
			// 单个结果
			dataToExport = JSON.stringify(props.result.result, null, 2);
		}

		// 创建下载链接
		const blob = new Blob([dataToExport], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = url;
		link.download = `${props.tool.name}_result_${new Date().getTime()}.json`;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		URL.revokeObjectURL(url);

		ElMessage.success('结果已导出');
	} catch (error) {
		console.error('导出失败:', error);
		ElMessage.error('导出失败');
	}
};

// 格式化结果用于复制
const formatResultForCopy = (data: any): string => {
	if (typeof data === 'string') {
		return data;
	}
	if (typeof data === 'object' && data !== null) {
		// 如果有 result 字段，优先使用
		if (data.result !== undefined) {
			return String(data.result);
		}
		// 否则转为 JSON
		return JSON.stringify(data, null, 2);
	}
	return String(data);
};

// 格式化统计标签
const formatStatLabel = (key: string): string => {
	const labelMap: Record<string, string> = {
		length: '长度',
		count: '数量',
		size: '大小',
		original_length: '原始长度',
		new_length: '新长度',
		encoded_length: '编码长度',
		decoded_length: '解码长度',
		total_length: '总长度',
		match_count: '匹配数量',
		replacements: '替换次数',
	};
	return labelMap[key] || key;
};

// 格式化统计值
const formatStatValue = (value: any): string => {
	if (typeof value === 'number') {
		return value.toLocaleString();
	}
	return String(value);
};
</script>

<style scoped lang="scss">
.result-display {
	.result-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 16px;
		padding-bottom: 12px;
		border-bottom: 1px solid var(--el-border-color-light);

		.result-info {
			display: flex;
			align-items: center;
			gap: 8px;

			.success-icon {
				color: var(--el-color-success);
				font-size: 18px;
			}

			.result-title {
				font-weight: 600;
				color: var(--el-text-color-primary);
			}
		}

		.result-actions {
			display: flex;
			gap: 8px;
		}
	}

	.result-content {
		margin-bottom: 16px;
	}

	.batch-result {
		.batch-summary {
			display: flex;
			gap: 24px;
			margin-bottom: 16px;
			padding: 16px;
			background: var(--el-color-primary-light-9);
			border-radius: var(--el-border-radius-small);
		}

		.batch-items {
			h5 {
				margin: 0 0 12px 0;
				font-size: 14px;
				color: var(--el-text-color-regular);
			}

			.result-list {
				max-height: 300px;
				overflow-y: auto;
			}

			.result-item {
				display: flex;
				align-items: flex-start;
				margin-bottom: 8px;
				padding: 8px;
				background: var(--el-bg-color);
				border-radius: var(--el-border-radius-small);
				border: 1px solid var(--el-border-color-light);

				.item-index {
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
					flex-shrink: 0;
				}

				.item-content {
					flex: 1;
					min-width: 0;
				}
			}
		}
	}

	.single-result {
		padding: 16px;
		background: var(--el-bg-color);
		border-radius: var(--el-border-radius-small);
		border: 1px solid var(--el-border-color-light);
	}

	.result-stats {
		margin-top: 16px;
		padding-top: 16px;
		border-top: 1px solid var(--el-border-color-light);
	}
}
</style>