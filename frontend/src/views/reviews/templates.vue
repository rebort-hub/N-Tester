<template>
	<div class="templates-container">
		<!-- 页面头部 -->
		<el-card shadow="hover" class="page-header-card">
			<div class="page-header">
				<div class="header-left">
					<h2 class="page-title">
						<el-icon><Setting /></el-icon>
						评审模板管理
					</h2>
					<p class="page-description">管理评审模板，提高评审效率</p>
				</div>
				<div class="header-right">
					<el-button @click="$router.push('/reviews/index')">
						<el-icon><ArrowLeft /></el-icon>
						返回评审列表
					</el-button>
					<el-button type="primary" @click="showCreateDialog = true">
						<el-icon><Plus /></el-icon>
						创建模板
					</el-button>
				</div>
			</div>
		</el-card>

		<!-- 模板列表 -->
		<el-card shadow="hover" class="table-card">
			<el-table
				v-loading="loading"
				:data="templates"
				stripe
				style="width: 100%"
			>
				<el-table-column prop="name" label="模板名称" min-width="200" />
				<el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
				<el-table-column prop="is_active" label="状态" width="100">
					<template #default="{ row }">
						<el-tag :type="row.is_active ? 'success' : 'info'">
							{{ row.is_active ? '启用' : '禁用' }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="creator_name" label="创建人" width="100" />
				<el-table-column prop="creation_date" label="创建时间" width="160">
					<template #default="{ row }">
						{{ formatDateTime(row.creation_date) }}
					</template>
				</el-table-column>
				<el-table-column label="操作" width="200" fixed="right">
					<template #default="{ row }">
						<el-button size="small" @click="viewTemplate(row)">查看</el-button>
						<el-button size="small" type="primary" @click="editTemplate(row)">编辑</el-button>
						<el-button size="small" type="danger" @click="deleteTemplate(row)">删除</el-button>
					</template>
				</el-table-column>
			</el-table>

			<!-- 分页 -->
			<div class="pagination-container">
				<el-pagination
					v-model:current-page="pagination.page"
					v-model:page-size="pagination.pageSize"
					:total="pagination.total"
					:page-sizes="[10, 20, 50, 100]"
					layout="total, sizes, prev, pager, next, jumper"
					@size-change="loadTemplates"
					@current-change="loadTemplates"
				/>
			</div>
		</el-card>

		<!-- 创建/编辑模板对话框 -->
		<TemplateDialog
			v-model="showCreateDialog"
			:template="currentTemplate"
			@success="loadTemplates"
		/>

		<!-- 查看模板详情对话框 -->
		<el-dialog
			v-model="showViewDialog"
			title="模板详情"
			width="600px"
		>
			<div v-if="viewTemplateData" class="template-detail">
				<el-descriptions :column="2" border>
					<el-descriptions-item label="模板名称" :span="2">
						<span class="template-name">{{ viewTemplateData.name }}</span>
					</el-descriptions-item>
					<el-descriptions-item label="状态">
						<el-tag :type="viewTemplateData.is_active ? 'success' : 'info'">
							{{ viewTemplateData.is_active ? '启用' : '禁用' }}
						</el-tag>
					</el-descriptions-item>
					<el-descriptions-item label="创建人">
						{{ viewTemplateData.creator_name || '未知用户' }}
					</el-descriptions-item>
					<el-descriptions-item label="创建时间">
						{{ formatDateTime(viewTemplateData.creation_date) }}
					</el-descriptions-item>
					<el-descriptions-item label="更新时间">
						{{ formatDateTime(viewTemplateData.updation_date) }}
					</el-descriptions-item>
					<el-descriptions-item label="描述" :span="2">
						<div class="template-description">
							{{ viewTemplateData.description || '暂无描述' }}
						</div>
					</el-descriptions-item>
					<el-descriptions-item label="检查清单" :span="2">
						<div class="checklist-content">
							<pre>{{ JSON.stringify(viewTemplateData.checklist, null, 2) }}</pre>
						</div>
					</el-descriptions-item>
				</el-descriptions>
			</div>

			<template #footer>
				<div class="dialog-footer">
					<el-button @click="showViewDialog = false">关闭</el-button>
					<el-button type="primary" @click="editCurrentTemplate">编辑</el-button>
				</div>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Setting, ArrowLeft, Plus } from '@element-plus/icons-vue';
import { getTemplateList, deleteTemplate as deleteTemplateApi, type ReviewTemplate } from '/@/api/v1/reviews';
import TemplateDialog from './components/TemplateDialog.vue';

// 响应式数据
const loading = ref(false);
const templates = ref<ReviewTemplate[]>([]);
const showCreateDialog = ref(false);
const showViewDialog = ref(false);
const currentTemplate = ref<ReviewTemplate | null>(null);
const viewTemplateData = ref<ReviewTemplate | null>(null);

// 分页数据
const pagination = reactive({
	page: 1,
	pageSize: 10,
	total: 0,
});

// 加载模板列表
const loadTemplates = async () => {
	loading.value = true;
	try {
		const params = {
			page: pagination.page,
			page_size: pagination.pageSize,
		};
		
		const response = await getTemplateList(params);
		if (response.code === 200) {
			templates.value = response.data.rows || [];
			pagination.total = response.data.rowTotal || 0;
		}
	} catch (error) {
		console.error('加载模板列表失败:', error);
		ElMessage.error('加载模板列表失败');
	} finally {
		loading.value = false;
	}
};

// 查看模板
const viewTemplate = (template: ReviewTemplate) => {
	viewTemplateData.value = template;
	showViewDialog.value = true;
};

// 编辑当前查看的模板
const editCurrentTemplate = () => {
	currentTemplate.value = viewTemplateData.value;
	showViewDialog.value = false;
	showCreateDialog.value = true;
};

// 编辑模板
const editTemplate = (template: ReviewTemplate) => {
	currentTemplate.value = template;
	showCreateDialog.value = true;
};

// 删除模板
const deleteTemplate = async (template: ReviewTemplate) => {
	try {
		await ElMessageBox.confirm(
			`确定要删除模板"${template.name}"吗？`,
			'确认删除',
			{
				confirmButtonText: '确定',
				cancelButtonText: '取消',
				type: 'warning',
			}
		);

		const response = await deleteTemplateApi(template.id);
		if (response.code === 200) {
			ElMessage.success(response.message || '删除成功');
			loadTemplates();
		}
	} catch (error) {
		if (error !== 'cancel') {
			console.error('删除模板失败:', error);
			
			// 处理详细的错误信息
			let errorMessage = '删除模板失败';
			if (error && typeof error === 'object' && error.message) {
				errorMessage = error.message;
			} else if (typeof error === 'string') {
				errorMessage = error;
			}
			
			// 如果错误信息包含换行符，使用MessageBox显示详细信息
			if (errorMessage.includes('\n')) {
				ElMessageBox.alert(errorMessage, '删除失败', {
					confirmButtonText: '确定',
					type: 'error',
					customStyle: {
						width: '500px'
					},
					customClass: 'multiline-message-box'
				});
			} else {
				ElMessage.error(errorMessage);
			}
		}
	}
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

// 组件挂载时加载数据
onMounted(() => {
	loadTemplates();
});
</script>

<style scoped>
.templates-container {
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
	color: #303133;
}

.page-description {
	margin: 0;
	color: #909399;
	font-size: 14px;
}

.header-right {
	display: flex;
	gap: 12px;
}

.table-card {
	margin-bottom: 20px;
}

.pagination-container {
	display: flex;
	justify-content: center;
	margin-top: 20px;
}

.template-detail {
	padding: 10px 0;
}

.template-name {
	font-size: 16px;
	font-weight: 600;
	color: var(--el-text-color-primary);
}

.template-description {
	line-height: 1.6;
	color: var(--el-text-color-regular);
	white-space: pre-wrap;
	word-break: break-word;
}

.checklist-content {
	max-height: 300px;
	overflow-y: auto;
	background: var(--el-bg-color-page);
	border: 1px solid var(--el-border-color-light);
	border-radius: 4px;
	padding: 12px;
}

.checklist-content pre {
	margin: 0;
	font-family: 'Courier New', monospace;
	font-size: 12px;
	line-height: 1.4;
	color: var(--el-text-color-regular);
}

.dialog-footer {
	text-align: right;
}

/* 多行消息框样式 */
:global(.multiline-message-box .el-message-box__message) {
	white-space: pre-line;
	text-align: left;
	line-height: 1.6;
	max-height: 300px;
	overflow-y: auto;
}

:global(.multiline-message-box .el-message-box__content) {
	padding: 20px 24px;
}

:global(.multiline-message-box) {
	max-width: 600px;
}
</style>