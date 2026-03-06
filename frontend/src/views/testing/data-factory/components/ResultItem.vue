<template>
	<div class="result-item">
		<!-- 字符串结果 -->
		<div v-if="isStringResult" class="string-result">
			<div class="result-content">{{ data }}</div>
			<div class="result-actions">
				<el-button size="small" @click="copyToClipboard(data)">
					<el-icon><DocumentCopy /></el-icon>
					复制
				</el-button>
			</div>
		</div>

		<!-- 数字结果 -->
		<div v-else-if="isNumberResult" class="number-result">
			<div class="result-content">
				<el-statistic :value="data" :precision="getNumberPrecision(data)" />
			</div>
			<div class="result-actions">
				<el-button size="small" @click="copyToClipboard(String(data))">
					<el-icon><DocumentCopy /></el-icon>
					复制
				</el-button>
			</div>
		</div>

		<!-- 布尔结果 -->
		<div v-else-if="isBooleanResult" class="boolean-result">
			<div class="result-content">
				<el-tag :type="data ? 'success' : 'danger'" size="large">
					{{ data ? 'True' : 'False' }}
				</el-tag>
			</div>
		</div>

		<!-- 数组结果 -->
		<div v-else-if="isArrayResult" class="array-result">
			<div class="array-header">
				<span class="array-title">数组结果 ({{ data.length }} 项)</span>
				<el-button size="small" @click="copyToClipboard(JSON.stringify(data, null, 2))">
					<el-icon><DocumentCopy /></el-icon>
					复制全部
				</el-button>
			</div>
			<div class="array-items">
				<div
					v-for="(item, index) in displayItems"
					:key="index"
					class="array-item"
				>
					<div class="item-index">{{ index + 1 }}</div>
					<div class="item-content">
						<ResultItem :data="item" :tool="tool" />
					</div>
				</div>
				<div v-if="data.length > maxDisplayItems" class="more-items">
					<el-button text @click="showAllItems = !showAllItems">
						{{ showAllItems ? '收起' : `还有 ${data.length - maxDisplayItems} 项...` }}
					</el-button>
				</div>
			</div>
		</div>

		<!-- 对象结果 -->
		<div v-else-if="isObjectResult" class="object-result">
			<div class="object-header">
				<span class="object-title">对象结果</span>
				<el-button size="small" @click="copyToClipboard(JSON.stringify(data, null, 2))">
					<el-icon><DocumentCopy /></el-icon>
					复制JSON
				</el-button>
			</div>
			<div class="object-content">
				<!-- 特殊对象类型处理 -->
				<div v-if="isImageResult" class="image-result">
					<div class="image-info">
						<el-descriptions :column="2" size="small">
							<el-descriptions-item label="文件路径">{{ data.file_path }}</el-descriptions-item>
							<el-descriptions-item label="文件大小">{{ data.file_size }}</el-descriptions-item>
							<el-descriptions-item label="图片格式">{{ data.format }}</el-descriptions-item>
							<el-descriptions-item label="图片尺寸">{{ data.width }}x{{ data.height }}</el-descriptions-item>
						</el-descriptions>
					</div>
					<div v-if="data.url" class="image-preview">
						<img :src="data.url" :alt="data.file_path" class="preview-image" />
					</div>
				</div>

				<div v-else-if="isHashResult" class="hash-result">
					<div class="hash-info">
						<el-descriptions :column="1" size="small">
							<el-descriptions-item label="算法">{{ data.algorithm }}</el-descriptions-item>
							<el-descriptions-item label="哈希值">
								<code class="hash-value">{{ data.hash }}</code>
								<el-button size="small" text @click="copyToClipboard(data.hash)">
									复制
								</el-button>
							</el-descriptions-item>
							<el-descriptions-item v-if="data.length" label="长度">{{ data.length }}</el-descriptions-item>
						</el-descriptions>
					</div>
				</div>

				<div v-else-if="isPasswordStrengthResult" class="password-strength-result">
					<div class="strength-info">
						<el-descriptions :column="2" size="small">
							<el-descriptions-item label="强度等级">
								<el-tag :type="getStrengthType(data.strength)">{{ data.strength }}</el-tag>
							</el-descriptions-item>
							<el-descriptions-item label="强度分数">{{ data.score }}/100</el-descriptions-item>
							<el-descriptions-item label="密码长度">{{ data.length }}</el-descriptions-item>
							<el-descriptions-item label="字符类型">{{ data.character_types }}</el-descriptions-item>
						</el-descriptions>
					</div>
					<div v-if="data.suggestions && data.suggestions.length > 0" class="suggestions">
						<h5>改进建议:</h5>
						<ul>
							<li v-for="suggestion in data.suggestions" :key="suggestion">
								{{ suggestion }}
							</li>
						</ul>
					</div>
				</div>

				<div v-else-if="isCrontabResult" class="crontab-result">
					<div class="crontab-info">
						<el-descriptions :column="1" size="small">
							<el-descriptions-item v-if="data.expression" label="表达式">
								<code>{{ data.expression }}</code>
							</el-descriptions-item>
							<el-descriptions-item v-if="data.description" label="描述">
								{{ data.description }}
							</el-descriptions-item>
							<el-descriptions-item v-if="data.next_runs" label="下次执行时间">
								<div class="next-runs">
									<div v-for="(time, index) in data.next_runs" :key="index" class="next-run-item">
										{{ formatDateTime(time) }}
									</div>
								</div>
							</el-descriptions-item>
							<el-descriptions-item v-if="data.is_valid !== undefined" label="表达式有效性">
								<el-tag :type="data.is_valid ? 'success' : 'danger'">
									{{ data.is_valid ? '有效' : '无效' }}
								</el-tag>
							</el-descriptions-item>
						</el-descriptions>
					</div>
				</div>

				<!-- 通用对象显示 -->
				<div v-else class="generic-object">
					<el-descriptions :column="2" size="small">
						<el-descriptions-item
							v-for="(value, key) in displayObjectFields"
							:key="key"
							:label="formatFieldLabel(key)"
						>
							<div v-if="typeof value === 'object'" class="nested-object">
								<ResultItem :data="value" :tool="tool" />
							</div>
							<div v-else class="field-value">
								{{ formatFieldValue(value) }}
								<el-button
									v-if="isCopiableValue(value)"
									size="small"
									text
									@click="copyToClipboard(String(value))"
								>
									复制
								</el-button>
							</div>
						</el-descriptions-item>
					</el-descriptions>
				</div>
			</div>
		</div>

		<!-- 未知类型结果 -->
		<div v-else class="unknown-result">
			<div class="result-content">
				<pre>{{ JSON.stringify(data, null, 2) }}</pre>
			</div>
			<div class="result-actions">
				<el-button size="small" @click="copyToClipboard(JSON.stringify(data, null, 2))">
					<el-icon><DocumentCopy /></el-icon>
					复制JSON
				</el-button>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, ref, defineProps } from 'vue';
import { ElMessage } from 'element-plus';
import { DocumentCopy } from '@element-plus/icons-vue';
import type { Tool } from '/@/api/v1/data_factory';

// 为了支持递归组件，需要定义组件名称
defineOptions({
	name: 'ResultItem'
});

// Props
const props = defineProps<{
	data: any;
	tool: Tool;
}>();

// 响应式数据
const showAllItems = ref(false);
const maxDisplayItems = 5;

// 计算属性 - 判断数据类型
const isStringResult = computed(() => {
	return typeof props.data === 'string';
});

const isNumberResult = computed(() => {
	return typeof props.data === 'number';
});

const isBooleanResult = computed(() => {
	return typeof props.data === 'boolean';
});

const isArrayResult = computed(() => {
	return Array.isArray(props.data);
});

const isObjectResult = computed(() => {
	return props.data && typeof props.data === 'object' && !Array.isArray(props.data);
});

// 特殊对象类型判断
const isImageResult = computed(() => {
	return isObjectResult.value && (
		props.data.file_path || 
		props.data.url || 
		props.data.format ||
		(props.data.width && props.data.height)
	);
});

const isHashResult = computed(() => {
	return isObjectResult.value && (
		props.data.hash || 
		props.data.algorithm ||
		props.tool.name.includes('hash')
	);
});

const isPasswordStrengthResult = computed(() => {
	return isObjectResult.value && (
		props.data.strength || 
		props.data.score !== undefined ||
		props.tool.name === 'password_strength'
	);
});

const isCrontabResult = computed(() => {
	return isObjectResult.value && (
		props.data.expression || 
		props.data.next_runs ||
		props.data.is_valid !== undefined ||
		props.tool.name.includes('crontab') ||
		props.tool.name.includes('expression')
	);
});

// 数组显示项
const displayItems = computed(() => {
	if (!isArrayResult.value) return [];
	return showAllItems.value ? props.data : props.data.slice(0, maxDisplayItems);
});

// 对象字段显示
const displayObjectFields = computed(() => {
	if (!isObjectResult.value) return {};
	
	// 过滤掉一些内部字段
	const filtered: Record<string, any> = {};
	Object.keys(props.data).forEach(key => {
		if (!key.startsWith('_') && key !== 'type' && key !== 'status') {
			filtered[key] = props.data[key];
		}
	});
	
	return filtered;
});

// 获取数字精度
const getNumberPrecision = (num: number): number => {
	if (Number.isInteger(num)) return 0;
	const str = num.toString();
	const decimalIndex = str.indexOf('.');
	return decimalIndex === -1 ? 0 : Math.min(str.length - decimalIndex - 1, 6);
};

// 获取强度类型
const getStrengthType = (strength: string): string => {
	const strengthMap: Record<string, string> = {
		'很弱': 'danger',
		'弱': 'warning',
		'中等': 'info',
		'强': 'success',
		'很强': 'success'
	};
	return strengthMap[strength] || 'info';
};

// 格式化字段标签
const formatFieldLabel = (key: string): string => {
	const labelMap: Record<string, string> = {
		file_path: '文件路径',
		file_size: '文件大小',
		width: '宽度',
		height: '高度',
		format: '格式',
		url: '链接',
		hash: '哈希值',
		algorithm: '算法',
		length: '长度',
		strength: '强度',
		score: '分数',
		character_types: '字符类型',
		suggestions: '建议',
		expression: '表达式',
		description: '描述',
		next_runs: '下次执行',
		is_valid: '有效性',
		result: '结果',
		message: '消息',
		error: '错误',
		success: '成功',
		count: '数量',
		total: '总计',
	};
	return labelMap[key] || key;
};

// 格式化字段值
const formatFieldValue = (value: any): string => {
	if (value === null || value === undefined) return '无';
	if (typeof value === 'boolean') return value ? '是' : '否';
	if (typeof value === 'number') return value.toLocaleString();
	if (typeof value === 'string' && value.length > 100) {
		return value.substring(0, 100) + '...';
	}
	return String(value);
};

// 判断是否可复制的值
const isCopiableValue = (value: any): boolean => {
	return typeof value === 'string' || typeof value === 'number';
};

// 格式化日期时间
const formatDateTime = (dateTime: string): string => {
	if (!dateTime) return '';
	return new Date(dateTime).toLocaleString('zh-CN');
};

// 复制到剪贴板
const copyToClipboard = async (text: string) => {
	try {
		await navigator.clipboard.writeText(text);
		ElMessage.success('已复制到剪贴板');
	} catch (error) {
		console.error('复制失败:', error);
		ElMessage.error('复制失败');
	}
};
</script>

<style scoped lang="scss">
.result-item {
	.string-result,
	.number-result {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 8px 12px;
		background: var(--el-fill-color-lighter);
		border-radius: var(--el-border-radius-small);
		border: 1px solid var(--el-border-color-light);

		.result-content {
			flex: 1;
			font-family: 'Courier New', monospace;
			font-size: 14px;
			color: var(--el-text-color-primary);
			word-break: break-all;
		}

		.result-actions {
			margin-left: 12px;
		}
	}

	.boolean-result {
		padding: 8px 12px;
		text-align: center;

		.result-content {
			display: flex;
			justify-content: center;
		}
	}

	.array-result {
		.array-header {
			display: flex;
			justify-content: space-between;
			align-items: center;
			margin-bottom: 12px;
			padding-bottom: 8px;
			border-bottom: 1px solid var(--el-border-color-light);

			.array-title {
				font-weight: 600;
				color: var(--el-text-color-primary);
			}
		}

		.array-items {
			.array-item {
				display: flex;
				align-items: flex-start;
				margin-bottom: 8px;
				padding: 8px;
				background: var(--el-fill-color-lighter);
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

			.more-items {
				text-align: center;
				padding: 8px;
			}
		}
	}

	.object-result {
		.object-header {
			display: flex;
			justify-content: space-between;
			align-items: center;
			margin-bottom: 12px;
			padding-bottom: 8px;
			border-bottom: 1px solid var(--el-border-color-light);

			.object-title {
				font-weight: 600;
				color: var(--el-text-color-primary);
			}
		}

		.object-content {
			.image-result {
				.image-info {
					margin-bottom: 16px;
				}

				.image-preview {
					text-align: center;

					.preview-image {
						max-width: 100%;
						max-height: 200px;
						border-radius: var(--el-border-radius-small);
						box-shadow: var(--el-box-shadow-light);
					}
				}
			}

			.hash-result {
				.hash-value {
					font-family: 'Courier New', monospace;
					font-size: 12px;
					background: var(--el-fill-color-light);
					padding: 2px 4px;
					border-radius: var(--el-border-radius-small);
					word-break: break-all;
				}
			}

			.password-strength-result {
				.suggestions {
					margin-top: 16px;
					padding-top: 12px;
					border-top: 1px solid var(--el-border-color-light);

					h5 {
						margin: 0 0 8px 0;
						font-size: 14px;
						color: var(--el-text-color-regular);
					}

					ul {
						margin: 0;
						padding-left: 20px;
						color: var(--el-text-color-regular);
						font-size: 13px;

						li {
							margin-bottom: 4px;
						}
					}
				}
			}

			.crontab-result {
				.next-runs {
					.next-run-item {
						padding: 2px 0;
						font-size: 13px;
						color: var(--el-text-color-regular);
					}
				}
			}

			.generic-object {
				.nested-object {
					margin-left: 12px;
					padding-left: 12px;
					border-left: 2px solid var(--el-border-color-light);
				}

				.field-value {
					display: flex;
					justify-content: space-between;
					align-items: center;
					font-family: 'Courier New', monospace;
					font-size: 13px;
					color: var(--el-text-color-regular);
				}
			}
		}
	}

	.unknown-result {
		.result-content {
			margin-bottom: 12px;

			pre {
				background: var(--el-fill-color-lighter);
				padding: 12px;
				border-radius: var(--el-border-radius-small);
				border: 1px solid var(--el-border-color-light);
				font-size: 12px;
				color: var(--el-text-color-regular);
				overflow-x: auto;
				margin: 0;
			}
		}

		.result-actions {
			text-align: right;
		}
	}
}
</style>