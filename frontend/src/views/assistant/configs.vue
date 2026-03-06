<template>
	<div class="assistant-configs-container">
		<!-- 页面头部 -->
		<el-card shadow="hover" class="page-header-card">
			<div class="page-header">
				<div class="header-left">
					<h2 class="page-title">
						<el-icon><Setting /></el-icon>
						助手配置管理
					</h2>
					<p class="page-description">管理AI助手的配置信息，包括API密钥、基础URL等设置</p>
				</div>
				<div class="header-right">
					<el-button type="primary" @click="showCreateDialog">
						<el-icon><Plus /></el-icon>
						新建配置
					</el-button>
					<el-button @click="loadConfigs">
						<el-icon><Refresh /></el-icon>
						刷新
					</el-button>
				</div>
			</div>
		</el-card>

		<!-- 筛选条件 -->
		<el-card shadow="hover" class="filter-card">
			<el-form :model="filters" inline>
				<el-form-item label="状态筛选">
					<el-select v-model="filters.is_active" placeholder="全部状态" clearable @change="loadConfigs" style="width: 120px">
						<el-option label="启用" :value="true" />
						<el-option label="禁用" :value="false" />
					</el-select>
				</el-form-item>
				<el-form-item label="搜索">
					<el-input
						v-model="filters.keyword"
						placeholder="搜索配置名称"
						@keyup.enter="loadConfigs"
						style="width: 200px"
					>
						<template #append>
							<el-button @click="loadConfigs">
								<el-icon><Search /></el-icon>
							</el-button>
						</template>
					</el-input>
				</el-form-item>
			</el-form>
		</el-card>

		<!-- 配置列表 -->
		<el-card shadow="hover" class="table-card">
			<el-table
				v-loading="loading"
				:data="configs"
				stripe
				style="width: 100%"
			>
				<el-table-column prop="name" label="配置名称" min-width="150" show-overflow-tooltip />
				<el-table-column prop="assistant_type" label="助手类型" width="120">
					<template #default="{ row }">
						<el-tag :type="getTypeTagType(row.assistant_type)">
							{{ getTypeText(row.assistant_type) }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="dify_base_url" label="Dify URL" min-width="200" show-overflow-tooltip />
				<el-table-column prop="is_active" label="状态" width="80">
					<template #default="{ row }">
						<el-tag :type="row.is_active ? 'success' : 'danger'">
							{{ row.is_active ? '启用' : '禁用' }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="created_at" label="创建时间" width="160">
					<template #default="{ row }">
						{{ formatDateTime(row.created_at) }}
					</template>
				</el-table-column>
				<el-table-column label="操作" width="200" fixed="right">
					<template #default="{ row }">
						<el-button size="small" @click="viewConfig(row)">查看</el-button>
						<el-button size="small" type="primary" @click="editConfig(row)">编辑</el-button>
						<el-button 
							size="small" 
							type="danger" 
							@click="deleteConfig(row)"
						>
							删除
						</el-button>
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
					@size-change="loadConfigs"
					@current-change="loadConfigs"
				/>
			</div>
		</el-card>

		<!-- 创建/编辑配置对话框 -->
		<el-dialog
			v-model="dialogVisible"
			:title="dialogMode === 'create' ? '新建配置' : '编辑配置'"
			width="600px"
			@close="resetForm"
		>
			<el-form
				ref="formRef"
				:model="formData"
				:rules="formRules"
				label-width="120px"
			>
				<el-form-item label="配置名称" prop="name">
					<el-input v-model="formData.name" placeholder="请输入配置名称" />
				</el-form-item>
				<el-form-item label="助手类型" prop="assistant_type">
					<el-select v-model="formData.assistant_type" placeholder="请选择助手类型">
						<el-option label="聊天机器人" value="chatbot" />
						<el-option label="工作流" value="workflow" />
						<el-option label="智能体" value="agent" />
					</el-select>
				</el-form-item>
				<el-form-item label="Dify API Key" prop="dify_api_key">
					<el-input 
						v-model="formData.dify_api_key" 
						type="password" 
						placeholder="请输入Dify API Key"
						show-password
					/>
				</el-form-item>
				<el-form-item label="Dify Base URL" prop="dify_base_url">
					<el-input v-model="formData.dify_base_url" placeholder="请输入Dify Base URL" />
				</el-form-item>
				<el-form-item label="是否启用" prop="is_active">
					<el-switch v-model="formData.is_active" />
				</el-form-item>
			</el-form>
			<template #footer>
				<span class="dialog-footer">
					<el-button @click="dialogVisible = false">取消</el-button>
					<el-button type="primary" @click="submitForm">确定</el-button>
				</span>
			</template>
		</el-dialog>

		<!-- 查看配置对话框 -->
		<el-dialog
			v-model="viewDialogVisible"
			title="配置详情"
			width="600px"
		>
			<el-descriptions :column="1" border>
				<el-descriptions-item label="配置名称">{{ viewData.name }}</el-descriptions-item>
				<el-descriptions-item label="助手类型">
					<el-tag :type="getTypeTagType(viewData.assistant_type)">
						{{ getTypeText(viewData.assistant_type) }}
					</el-tag>
				</el-descriptions-item>
				<el-descriptions-item label="Dify API Key">
					<span class="masked-key">{{ maskApiKey(viewData.dify_api_key) }}</span>
				</el-descriptions-item>
				<el-descriptions-item label="Dify Base URL">{{ viewData.dify_base_url }}</el-descriptions-item>
				<el-descriptions-item label="状态">
					<el-tag :type="viewData.is_active ? 'success' : 'danger'">
						{{ viewData.is_active ? '启用' : '禁用' }}
					</el-tag>
				</el-descriptions-item>
				<el-descriptions-item label="创建时间">{{ formatDateTime(viewData.created_at) }}</el-descriptions-item>
				<el-descriptions-item label="更新时间">{{ formatDateTime(viewData.updated_at) }}</el-descriptions-item>
			</el-descriptions>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Setting, Plus, Refresh, Search } from '@element-plus/icons-vue';
import { 
	getConfigList, 
	createConfig, 
	updateConfig, 
	deleteConfig as deleteConfigApi,
	type AssistantConfig 
} from '/@/api/v1/assistant';

// 响应式数据
const loading = ref(false);
const configs = ref<AssistantConfig[]>([]);
const dialogVisible = ref(false);
const viewDialogVisible = ref(false);
const dialogMode = ref<'create' | 'edit'>('create');

// 筛选条件
const filters = reactive({
	is_active: undefined as boolean | undefined,
	keyword: '',
});

// 分页数据
const pagination = reactive({
	page: 1,
	pageSize: 20,
	total: 0,
});

// 表单数据
const formRef = ref();
const formData = reactive({
	id: 0,
	name: '',
	assistant_type: 'chatbot',
	dify_api_key: '',
	dify_base_url: '',
	is_active: true,
});

// 查看数据
const viewData = reactive({
	name: '',
	assistant_type: '',
	dify_api_key: '',
	dify_base_url: '',
	is_active: false,
	created_at: '',
	updated_at: '',
});

// 表单验证规则
const formRules = {
	name: [
		{ required: true, message: '请输入配置名称', trigger: 'blur' },
		{ min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
	],
	assistant_type: [
		{ required: true, message: '请选择助手类型', trigger: 'change' }
	],
	dify_api_key: [
		{ required: true, message: '请输入Dify API Key', trigger: 'blur' }
	],
	dify_base_url: [
		{ required: true, message: '请输入Dify Base URL', trigger: 'blur' },
		{ type: 'url', message: '请输入正确的URL格式', trigger: 'blur' }
	],
};

// 加载配置列表
const loadConfigs = async () => {
	loading.value = true;
	try {
		const response = await getConfigList({
			page: pagination.page,
			page_size: pagination.pageSize,
			is_active: filters.is_active,
		});
		
		if (response.code === 200) {
			configs.value = response.data.items || [];
			pagination.total = response.data.total || 0;
		} else {
			ElMessage.error(response.message || '加载配置列表失败');
		}
		
	} catch (error) {
		console.error('加载配置列表失败:', error);
		ElMessage.error('加载配置列表失败');
	} finally {
		loading.value = false;
	}
};

// 显示创建对话框
const showCreateDialog = () => {
	dialogMode.value = 'create';
	resetForm();
	dialogVisible.value = true;
};

// 编辑配置
const editConfig = (config: AssistantConfig) => {
	dialogMode.value = 'edit';
	Object.assign(formData, config);
	dialogVisible.value = true;
};

// 查看配置
const viewConfig = (config: AssistantConfig) => {
	Object.assign(viewData, config);
	viewDialogVisible.value = true;
};

// 删除配置
const deleteConfig = async (config: AssistantConfig) => {
	try {
		await ElMessageBox.confirm(
			`确定要删除配置"${config.name}"吗？此操作不可恢复。`,
			'确认删除',
			{
				confirmButtonText: '删除',
				cancelButtonText: '取消',
				type: 'warning',
			}
		);
		
		const response = await deleteConfigApi(config.id);
		
		if (response.code === 200) {
			ElMessage.success('删除配置成功');
			loadConfigs();
		} else {
			ElMessage.error(response.message || '删除配置失败');
		}
		
	} catch (error) {
		if (error !== 'cancel') {
			console.error('删除配置失败:', error);
			ElMessage.error('删除配置失败');
		}
	}
};

// 提交表单
const submitForm = async () => {
	try {
		await formRef.value.validate();
		
		const apiCall = dialogMode.value === 'create' ? createConfig : updateConfig;
		const params = dialogMode.value === 'create' ? formData : [formData.id, formData];
		
		const response = await apiCall(...(Array.isArray(params) ? params : [params]));
		
		if (response.code === 200) {
			ElMessage.success(`${dialogMode.value === 'create' ? '创建' : '更新'}配置成功`);
			dialogVisible.value = false;
			loadConfigs();
		} else {
			ElMessage.error(response.message || `${dialogMode.value === 'create' ? '创建' : '更新'}配置失败`);
		}
		
	} catch (error) {
		console.error('提交表单失败:', error);
		ElMessage.error('提交表单失败');
	}
};

// 重置表单
const resetForm = () => {
	Object.assign(formData, {
		id: 0,
		name: '',
		assistant_type: 'chatbot',
		dify_api_key: '',
		dify_base_url: '',
		is_active: true,
	});
	formRef.value?.resetFields();
};

// 获取类型标签类型
const getTypeTagType = (type: string) => {
	const types: Record<string, string> = {
		chatbot: 'primary',
		workflow: 'success',
		agent: 'warning',
	};
	return types[type] || 'info';
};

// 获取类型文本
const getTypeText = (type: string) => {
	const texts: Record<string, string> = {
		chatbot: '聊天机器人',
		workflow: '工作流',
		agent: '智能体',
	};
	return texts[type] || type;
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

// 掩码API Key
const maskApiKey = (apiKey: string) => {
	if (!apiKey) return '-';
	if (apiKey.length <= 8) return '*'.repeat(apiKey.length);
	return apiKey.substring(0, 4) + '*'.repeat(apiKey.length - 8) + apiKey.substring(apiKey.length - 4);
};

// 组件挂载时加载数据
onMounted(() => {
	loadConfigs();
});
</script>

<style scoped>
.assistant-configs-container {
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
	color: var(--el-text-color-primary);
}

.page-description {
	margin: 0;
	color: var(--el-text-color-regular);
	font-size: 14px;
}

.header-right {
	display: flex;
	gap: 12px;
}

.filter-card {
	margin-bottom: 20px;
}

.table-card {
	margin-bottom: 20px;
}

.pagination-container {
	display: flex;
	justify-content: center;
	margin-top: 20px;
}

.masked-key {
	font-family: monospace;
	color: var(--el-text-color-regular);
}
</style>