<template>
	<div class="tool-list-container">
		<!-- 工具搜索 -->
		<div class="search-bar">
			<el-input
				v-model="searchKeyword"
				placeholder="搜索工具..."
				clearable
				@input="filterTools"
			>
				<template #prefix>
					<el-icon><Search /></el-icon>
				</template>
			</el-input>
		</div>

		<!-- 工具列表 -->
		<div class="tools-grid">
			<div
				v-for="tool in filteredTools"
				:key="tool.name"
				class="tool-card"
				@click="selectTool(tool)"
			>
				<div class="tool-icon">
					<el-icon :size="24">
						<component :is="getIconComponent(tool.icon)" />
					</el-icon>
				</div>
				<div class="tool-info">
					<h4 class="tool-name">{{ tool.display_name }}</h4>
					<p class="tool-description">{{ tool.description }}</p>
				</div>
				<div class="tool-actions">
					<el-button size="small" type="primary" @click.stop="openToolDialog(tool)">
						使用
					</el-button>
				</div>
			</div>
		</div>

		<!-- 工具执行对话框 -->
		<el-dialog
			v-model="toolDialogVisible"
			:title="selectedTool?.display_name || '工具执行'"
			width="800px"
			:close-on-click-modal="false"
		>
			<ToolExecutor
				v-if="selectedTool"
				:tool="selectedTool"
				:category="category"
				@execute="handleExecute"
				@batch-generate="handleBatchGenerate"
				@close="toolDialogVisible = false"
			/>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { ref, computed, defineProps, defineEmits } from 'vue';
import { Search, User, Edit, Document, Grid, Setting, Lock, Clock } from '@element-plus/icons-vue';
import type { ToolCategory, Tool } from '/@/api/v1/data_factory';
import ToolExecutor from './ToolExecutor.vue';

// Props
const props = defineProps<{
	category: ToolCategory;
}>();

// Emits
const emit = defineEmits<{
	execute: [result: any];
	batchGenerate: [result: any];
}>();

// 响应式数据
const searchKeyword = ref('');
const selectedTool = ref<Tool | null>(null);
const toolDialogVisible = ref(false);

// 图标映射
const iconMap: Record<string, any> = {
	user: User,
	edit: Edit,
	document: Document,
	code: Grid,
	distribute: Setting,
	lock: Lock,
	clock: Clock,
	message: Edit,
	location: Edit,
	ticket: Document,
	'office-building': Document,
	'credit-card': Document,
	list: Document,
	'circle-check': Document,
	'document-copy': Document,
	search: Search,
	grid: Grid,
	share: Grid,
	view: Grid,
	picture: Grid,
	sort: Setting,
	delete: Edit,
};

// 获取图标组件
const getIconComponent = (iconName: string) => {
	return iconMap[iconName] || Document;
};

// 过滤后的工具列表
const filteredTools = computed(() => {
	if (!searchKeyword.value) {
		return props.category.tools;
	}
	return props.category.tools.filter(tool =>
		tool.display_name.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
		tool.description.toLowerCase().includes(searchKeyword.value.toLowerCase())
	);
});

// 过滤工具
const filterTools = () => {
	// 搜索逻辑已在 computed 中处理
};

// 选择工具
const selectTool = (tool: Tool) => {
	selectedTool.value = tool;
	toolDialogVisible.value = true;
};

// 打开工具对话框
const openToolDialog = (tool: Tool) => {
	selectedTool.value = tool;
	toolDialogVisible.value = true;
};

// 处理工具执行
const handleExecute = (result: any) => {
	emit('execute', result);
	toolDialogVisible.value = false;
};

// 处理批量生成
const handleBatchGenerate = (result: any) => {
	emit('batchGenerate', result);
	toolDialogVisible.value = false;
};
</script>

<style scoped lang="scss">
.tool-list-container {
	padding: 0;
}

.search-bar {
	margin-bottom: 20px;
}

.tools-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
	gap: 16px;
}

.tool-card {
	display: flex;
	align-items: center;
	padding: 16px;
	background: var(--el-fill-color-lighter);
	border-radius: var(--el-border-radius-base);
	cursor: pointer;
	transition: all var(--el-transition-duration);
	border: 1px solid var(--el-border-color-light);

	&:hover {
		background: var(--el-color-primary-light-9);
		border-color: var(--el-color-primary);
		transform: translateY(-1px);
	}

	.tool-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		background: var(--el-color-primary);
		border-radius: var(--el-border-radius-base);
		color: var(--el-color-white);
		margin-right: 12px;
		flex-shrink: 0;
	}

	.tool-info {
		flex: 1;
		min-width: 0;

		.tool-name {
			margin: 0 0 4px 0;
			font-size: 14px;
			font-weight: 600;
			color: var(--el-text-color-primary);
			white-space: nowrap;
			overflow: hidden;
			text-overflow: ellipsis;
		}

		.tool-description {
			margin: 0;
			font-size: 12px;
			color: var(--el-text-color-placeholder);
			line-height: 1.4;
			display: -webkit-box;
			-webkit-line-clamp: 2;
			-webkit-box-orient: vertical;
			overflow: hidden;
		}
	}

	.tool-actions {
		margin-left: 12px;
		flex-shrink: 0;
	}
}

// 响应式设计
@media (max-width: 768px) {
	.tools-grid {
		grid-template-columns: 1fr;
	}

	.tool-card {
		padding: 12px;

		.tool-icon {
			width: 36px;
			height: 36px;
		}

		.tool-info {
			.tool-name {
				font-size: 13px;
			}

			.tool-description {
				font-size: 11px;
			}
		}
	}
}
</style>