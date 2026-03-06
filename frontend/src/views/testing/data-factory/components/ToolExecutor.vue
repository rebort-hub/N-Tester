<template>
	<div class="tool-executor">
		<!-- 工具信息 -->
		<div class="tool-info-section">
			<div class="tool-header">
				<div class="tool-icon">
					<el-icon :size="24">
						<component :is="getIconComponent(tool.icon)" />
					</el-icon>
				</div>
				<div class="tool-details">
					<h3>{{ tool.display_name }}</h3>
					<p>{{ tool.description }}</p>
				</div>
			</div>
		</div>

		<!-- 参数配置 -->
		<div class="params-section">
			<h4>参数配置</h4>
			<el-form :model="formData" label-width="120px" class="params-form">
				<!-- 动态参数表单 -->
				<component
					:is="getParamComponent(tool.name)"
					v-model="formData"
					:tool="tool"
				/>
			</el-form>
		</div>

		<!-- 执行选项 -->
		<div class="options-section">
			<el-row :gutter="20">
				<el-col :span="12">
					<el-form-item label="保存记录">
						<el-switch v-model="options.is_saved" />
					</el-form-item>
				</el-col>
				<el-col :span="12">
					<el-form-item label="批量生成">
						<el-input-number
							v-model="options.batch_count"
							:min="1"
							:max="100"
							:disabled="!options.enable_batch"
						/>
					</el-form-item>
				</el-col>
			</el-row>
			<el-form-item label="标签">
				<el-select
					v-model="options.tags"
					multiple
					filterable
					allow-create
					placeholder="添加标签"
					style="width: 100%"
				>
					<el-option
						v-for="tag in availableTags"
						:key="tag"
						:label="tag"
						:value="tag"
					/>
				</el-select>
			</el-form-item>
		</div>

		<!-- 执行结果 -->
		<div v-if="executeResult" class="result-section">
			<h4>执行结果</h4>
			<div class="result-content">
				<ResultDisplay :result="executeResult" :tool="tool" />
			</div>
		</div>

		<!-- 操作按钮 -->
		<div class="actions-section">
			<el-button @click="$emit('close')">取消</el-button>
			<el-button
				type="primary"
				:loading="executing"
				@click="executeTool"
			>
				{{ options.batch_count > 1 ? `批量生成 (${options.batch_count})` : '执行工具' }}
			</el-button>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, defineProps, defineEmits } from 'vue';
import { ElMessage } from 'element-plus';
import { User, Edit, Document, Grid, Setting, Lock, Clock } from '@element-plus/icons-vue';
import { executeTool as executeToolAPI, batchGenerate, getTagList, type Tool, type ToolCategory } from '/@/api/v1/data_factory';
import ResultDisplay from './ResultDisplay.vue';
// 导入参数组件
import TestDataParams from './params/TestDataParams.vue';
import JsonParams from './params/JsonParams.vue';
import StringParams from './params/StringParams.vue';
import EncodingParams from './params/EncodingParams.vue';
import RandomParams from './params/RandomParams.vue';
import EncryptionParams from './params/EncryptionParams.vue';
import CrontabParams from './params/CrontabParams.vue';

// Props
const props = defineProps<{
	tool: Tool;
	category: ToolCategory;
	initialData?: Record<string, any>;
}>();

// Emits
const emit = defineEmits<{
	execute: [result: any];
	batchGenerate: [result: any];
	close: [];
}>();

// 响应式数据
const formData = ref<Record<string, any>>(props.initialData || {});
const options = reactive({
	is_saved: true,
	batch_count: 1,
	enable_batch: true,
	tags: [] as string[],
});
const executeResult = ref<any>(null);
const executing = ref(false);
const availableTags = ref<string[]>([]);

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

// 获取图标组件
const getIconComponent = (iconName: string) => {
	return iconMap[iconName] || Document;
};

// 获取参数组件
const getParamComponent = (toolName: string) => {
	const category = props.category.category;
	switch (category) {
		case 'test_data':
			return TestDataParams;
		case 'json':
			return JsonParams;
		case 'string':
			return StringParams;
		case 'encoding':
			return EncodingParams;
		case 'random':
			return RandomParams;
		case 'encryption':
			return EncryptionParams;
		case 'crontab':
			return CrontabParams;
		default:
			return 'div';
	}
};

// 执行工具
const executeTool = async () => {
	try {
		executing.value = true;
		executeResult.value = null;

		const requestData = {
			tool_name: props.tool.name,
			tool_category: props.category.category,
			tool_scenario: props.category.scenario,
			input_data: formData.value,
			is_saved: options.is_saved,
			tags: options.tags,
		};

		let response;
		if (options.batch_count > 1) {
			// 批量生成
			response = await batchGenerate({
				...requestData,
				count: options.batch_count,
			});
			console.log('Batch generate response:', response.data);
			// 传递完整的响应数据
			emit('batchGenerate', {
				...response.data,
				count: options.batch_count,
				tool_name: props.tool.display_name
			});
		} else {
			// 单次执行
			response = await executeToolAPI(requestData);
			console.log('Single execute response:', response.data);
			// 传递完整的响应数据
			emit('execute', {
				...response.data,
				tool_name: props.tool.display_name
			});
		}

		executeResult.value = response.data;
		// 移除这里的成功消息，让父组件处理
	} catch (error: any) {
		console.error('工具执行失败:', error);
		ElMessage.error(error.response?.data?.message || '工具执行失败');
	} finally {
		executing.value = false;
	}
};

// 加载标签列表
const loadTags = async () => {
	try {
		const response = await getTagList();
		availableTags.value = response.data?.tags || [];
	} catch (error) {
		console.error('加载标签失败:', error);
	}
};

// 初始化表单数据
const initFormData = () => {
	formData.value = {};
	executeResult.value = null;
};

// 组件挂载时初始化
onMounted(() => {
	initFormData();
	loadTags();
});
</script>

<style scoped lang="scss">
.tool-executor {
	.tool-info-section {
		margin-bottom: 24px;
		padding: 16px;
		background: var(--el-fill-color-lighter);
		border-radius: var(--el-border-radius-base);
		border: 1px solid var(--el-border-color-light);

		.tool-header {
			display: flex;
			align-items: center;

			.tool-icon {
				display: flex;
				align-items: center;
				justify-content: center;
				width: 48px;
				height: 48px;
				background: var(--el-color-primary);
				border-radius: var(--el-border-radius-base);
				color: var(--el-color-white);
				margin-right: 16px;
			}

			.tool-details {
				h3 {
					margin: 0 0 4px 0;
					font-size: 18px;
					color: var(--el-text-color-primary);
				}

				p {
					margin: 0;
					color: var(--el-text-color-regular);
					font-size: 14px;
				}
			}
		}
	}

	.params-section,
	.options-section,
	.result-section {
		margin-bottom: 24px;

		h4 {
			margin: 0 0 16px 0;
			font-size: 16px;
			color: var(--el-text-color-primary);
			border-bottom: 1px solid var(--el-border-color-light);
			padding-bottom: 8px;
		}
	}

	.params-form {
		:deep(.el-form-item) {
			margin-bottom: 18px;
		}
	}

	.result-content {
		padding: 16px;
		background: var(--el-fill-color-lighter);
		border-radius: var(--el-border-radius-base);
		border: 1px solid var(--el-border-color-light);
	}

	.actions-section {
		display: flex;
		justify-content: flex-end;
		gap: 12px;
		padding-top: 16px;
		border-top: 1px solid var(--el-border-color-light);
	}
}
</style>