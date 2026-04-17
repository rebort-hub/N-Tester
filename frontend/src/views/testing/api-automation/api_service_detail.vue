<template>
	<div class="service-detail-container">
		<!-- 顶部操作栏 -->
		<div class="service-detail-header">
			<el-button type="primary" plain size="small" icon="ArrowLeft" @click="emit('back')">
				返回接口列表
			</el-button>
			<span class="service-name">{{ serviceName }}</span>
			<div class="header-right">
				<el-select
					v-model="selectedEnvId"
					placeholder="请选择环境"
					clearable
					style="width: 180px; margin-right: 8px"
				>
					<el-option
						v-for="env in envList"
						:key="env.id"
						:label="env.name"
						:value="env.id"
					/>
				</el-select>
				<el-button size="small" @click="openEnvDialog">环境管理</el-button>
			</div>
		</div>

		<!-- Tab 区域 -->
		<el-tabs v-model="activeTab" type="border-card" class="service-detail-tabs">
			<el-tab-pane label="接口管理" name="manage">
				<ApiManagePanel :serviceId="currentServiceId" :envId="selectedEnvId" :envList="envList" />
			</el-tab-pane>
			<el-tab-pane label="用例管理" name="case">
				<ApiCaseManagement :serviceId="currentServiceId" :envId="selectedEnvId" />
			</el-tab-pane>
			<el-tab-pane label="执行结果" name="result">
				<ApiResultList :serviceId="currentServiceId" />
			</el-tab-pane>
			<el-tab-pane label="代码生成" name="codegen">
				<ApiCodegen />
			</el-tab-pane>
		</el-tabs>

		<!-- 环境管理对话框 -->
		<el-dialog v-model="envDialogVisible" title="环境管理" width="560px" @close="closeEnvDialog">
			<div style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px">
				<el-input v-model="envSearchName" placeholder="输入环境名称" clearable style="width: 260px" />
				<el-button type="primary" @click="openEnvFormDialog(null)">新增</el-button>
			</div>
			<el-table v-loading="envLoading" :data="filteredEnvList" border stripe empty-text="暂无环境">
				<el-table-column prop="name" label="环境名称" min-width="160" show-overflow-tooltip />
				<el-table-column label="操作" width="140" align="center">
					<template #default="{ row }">
						<el-button type="warning" size="small" @click="openEnvFormDialog(row)">编辑</el-button>
						<el-button type="danger" size="small" @click="deleteEnv(row)">删除</el-button>
					</template>
				</el-table-column>
			</el-table>
		</el-dialog>

		<!-- 新增/编辑环境表单对话框 -->
		<el-dialog
			v-model="envFormVisible"
			:title="envForm.id ? '编辑环境' : '新增环境'"
			width="680px"
			@close="resetEnvForm"
		>
			<el-form :model="envForm" label-width="80px">
				<el-form-item label="* 环境名称">
					<el-input v-model="envForm.name" placeholder="请输入环境名称" />
				</el-form-item>
				<el-form-item label="配置项">
					<div style="width: 100%">
						<div
							v-for="(item, idx) in envForm.config"
							:key="idx"
							style="display: flex; gap: 8px; margin-bottom: 6px"
						>
							<el-input v-model="item.name" placeholder="配置项名（如 {{base_url}}）" style="flex: 1" />
							<el-input v-model="item.value" placeholder="配置项值" style="flex: 1" />
							<el-button type="danger" size="small" @click="envForm.config.splice(idx, 1)">删除</el-button>
						</div>
						<el-button size="small" @click="envForm.config.push({ name: '', value: '' })">添加配置项</el-button>
					</div>
				</el-form-item>
				<el-form-item label="环境变量">
					<div style="width: 100%">
						<div
							v-for="(item, idx) in envForm.variable"
							:key="idx"
							style="display: flex; gap: 8px; margin-bottom: 6px"
						>
							<el-input v-model="item.name" placeholder="变量名（如 {{token}}）" style="flex: 1" />
							<el-input v-model="item.value" placeholder="变量值" style="flex: 1" />
							<el-button type="danger" size="small" @click="envForm.variable.splice(idx, 1)">删除</el-button>
						</div>
						<el-button size="small" @click="envForm.variable.push({ name: '', value: '' })">添加变量</el-button>
					</div>
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="envFormVisible = false">取消</el-button>
				<el-button type="primary" :loading="envSaving" @click="submitEnvForm">保存</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useApiAutomationApi } from '/@/api/v1/api_automation';
import ApiManagePanel from './ApiManagePanel.vue';
import ApiResultList from './api_result_list.vue';
import ApiCodegen from './api_codegen.vue';

// api_case_management.vue will be created in task 9 - use async import with fallback
const ApiCaseManagement = defineAsyncComponent({
	loader: () => import('./api_case_management.vue'),
	errorComponent: {
		template: '<div style="padding: 20px; color: #909399;">用例管理组件加载中，请稍后...</div>',
	},
	delay: 200,
	timeout: 5000,
});

const props = defineProps<{
	serviceId: number;
	serviceName: string;
}>();

const emit = defineEmits<{
	(e: 'back'): void;
}>();

const activeTab = ref<'manage' | 'case' | 'result' | 'codegen'>('manage');
const selectedEnvId = ref<number | null>(null);

const currentServiceId = ref<number>(props.serviceId);

const {
	api_env,
	add_env,
	save_env,
	del_env,
} = useApiAutomationApi();

// ---- 环境列表 ----
const envList = ref<any[]>([]);
const envLoading = ref(false);
const envDialogVisible = ref(false);
const envSearchName = ref('');
const filteredEnvList = computed(() =>
	envSearchName.value
		? envList.value.filter((e) => e.name?.includes(envSearchName.value))
		: envList.value
);

// 新增/编辑环境表单
const envFormVisible = ref(false);
const envSaving = ref(false);
const envForm = ref<{ id?: number; name: string; config: any[]; variable: any[] }>({
	name: '', config: [], variable: [],
});

const loadEnvList = async () => {
	envLoading.value = true;
	try {
		const res: any = await api_env();
		const raw = res?.data;
		envList.value = Array.isArray(raw) ? raw : (Array.isArray(raw?.content) ? raw.content : []);
	} catch {
		envList.value = [];
	} finally {
		envLoading.value = false;
	}
};

const openEnvDialog = async () => {
	envDialogVisible.value = true;
	await loadEnvList();
};

const closeEnvDialog = () => {
	envSearchName.value = '';
};

const openEnvFormDialog = (row: any | null) => {
	if (row) {
		envForm.value = {
			id: row.id,
			name: row.name || '',
			config: Array.isArray(row.config) ? row.config.map((c: any) => ({ ...c })) : [],
			variable: Array.isArray(row.variable) ? row.variable.map((v: any) => ({ ...v })) : [],
		};
	} else {
		envForm.value = { name: '', config: [{ name: '', value: '' }], variable: [] };
	}
	envFormVisible.value = true;
};

const resetEnvForm = () => {
	envForm.value = { name: '', config: [], variable: [] };
};

const submitEnvForm = async () => {
	if (!envForm.value.name.trim()) {
		ElMessage.warning('请输入环境名称');
		return;
	}
	envSaving.value = true;
	try {
		const payload = {
			name: envForm.value.name.trim(),
			config: envForm.value.config.filter((c) => String(c.name || '').trim()),
			variable: envForm.value.variable.filter((v) => String(v.name || '').trim()),
		};
		if (envForm.value.id) {
			await save_env({ env_list: [{ id: envForm.value.id, ...payload }] });
			ElMessage.success('保存成功');
		} else {
			await add_env(payload);
			ElMessage.success('新增成功');
		}
		envFormVisible.value = false;
		await loadEnvList();
	} catch (e: any) {
		ElMessage.error(e?.message || '保存失败');
	} finally {
		envSaving.value = false;
	}
};

const deleteEnv = async (row: any) => {
	try {
		await ElMessageBox.confirm(`确认删除环境「${row.name}」？`, '提示', {
			type: 'warning',
			confirmButtonText: '确定',
			cancelButtonText: '取消',
		});
		await del_env({ id: row.id });
		ElMessage.success('删除成功');
		await loadEnvList();
	} catch (e: any) {
		if (e === 'cancel' || e === 'close') return;
		ElMessage.error(e?.message || '删除失败');
	}
};

onMounted(() => {
	loadEnvList();
});
</script>

<style scoped>
.service-detail-container {
	display: flex;
	flex-direction: column;
	height: 100%;
	padding: 10px;
}

.service-detail-header {
	display: flex;
	align-items: center;
	margin-bottom: 8px;
	gap: 12px;
}

.service-name {
	font-size: 16px;
	font-weight: 600;
	color: #303133;
	flex: 1;
}

.header-right {
	display: flex;
	align-items: center;
	margin-left: auto;
}

.service-detail-tabs {
	flex: 1;
	display: flex;
	flex-direction: column;
	min-height: 0;
}

.service-detail-tabs :deep(.el-tabs__content) {
	flex: 1;
	min-height: 0;
	overflow: hidden;
	padding: 0 !important;
}

.service-detail-tabs :deep(.el-tab-pane) {
	height: 100%;
	overflow: hidden;
}

/* 恢复内层 apifox-tabs 的 padding，避免被外层 !important 覆盖 */
.service-detail-tabs :deep(.apifox-tabs .el-tabs__content) {
	padding: 10px 12px !important;
	overflow-y: auto !important;
}
</style>
