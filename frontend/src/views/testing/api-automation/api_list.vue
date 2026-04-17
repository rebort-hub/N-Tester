<template>
	<div class="api-list-container">
		<el-card shadow="hover" :body-style="{ paddingBottom: '0' }">
			<el-form :inline="true" :model="searchParams">
				<el-form-item label="服务名称">
					<el-input
						v-model="searchParams.name"
						placeholder="请输入服务名称"
						clearable
						style="width: 180px"
						@keyup.enter="loadList"
					/>
				</el-form-item>
				<el-form-item label="业务线">
					<el-select
						v-model="searchParams.business_id"
						placeholder="请选择业务线"
						clearable
						style="width: 160px"
					>
						<el-option
							v-for="b in businessOptions"
							:key="b.id"
							:label="b.name"
							:value="b.id"
						/>
					</el-select>
				</el-form-item>
				<el-form-item label="负责人">
					<el-select
						v-model="searchParams.manager"
						placeholder="请选择负责人"
						clearable
						filterable
						style="width: 160px"
					>
						<el-option
							v-for="u in userOptions"
							:key="u.id"
							:label="u.username"
							:value="u.id"
						/>
					</el-select>
				</el-form-item>
				<el-form-item>
					<el-button type="primary" icon="Search" @click="handleSearch">搜索</el-button>
					<el-button icon="Refresh" @click="resetSearch">重置</el-button>
				</el-form-item>
				<el-form-item style="float: right">
					<el-button type="primary" icon="Plus" @click="openAddDialog">新增</el-button>
				</el-form-item>
			</el-form>
		</el-card>

		<el-card shadow="hover" style="margin-top: 8px">
			<el-table
				ref="tableRef"
				v-loading="loading"
				:data="tableData"
				border
				stripe
				empty-text="暂无数据"
				table-layout="auto"
				style="width: 100%"
				@row-dblclick="onRowDblClick"
			>
				<el-table-column width="40" align="center">
					<template #default>
						<span class="drag-handle" style="cursor: grab; color: #909399; font-size: 16px;">⠿</span>
					</template>
				</el-table-column>
				<el-table-column type="index" label="序号" width="60" align="center" />
				<el-table-column prop="name" label="服务名称" min-width="140" show-overflow-tooltip />
				<el-table-column prop="project_name" label="所属项目" min-width="120" show-overflow-tooltip />
				<el-table-column prop="source_type" label="文档类型" width="110" align="center">
					<template #default="{ row }">
						{{ row.source_type || '-' }}
					</template>
				</el-table-column>
				<el-table-column prop="source_addr" label="接口文档地址" min-width="160" show-overflow-tooltip>
					<template #default="{ row }">
						{{ row.source_addr || '-' }}
					</template>
				</el-table-column>
				<el-table-column label="拉取状态" width="110" align="center">
					<template #default="{ row }">
						<el-tag :type="pullStatusMeta(row.last_pull_status).type">
							{{ pullStatusMeta(row.last_pull_status).text }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="manager_name" label="负责人" width="100" align="center" show-overflow-tooltip>
					<template #default="{ row }">
						{{ row.manager_name || '-' }}
					</template>
				</el-table-column>
				<el-table-column label="操作" width="280" align="center" fixed="right">
					<template #default="{ row }">
						<span class="action-cell">
							<el-button
								v-if="row.source_addr"
								type="primary"
								size="small"
								:loading="pullingIds.has(row.id)"
								@click.stop="pullDoc(row)"
							>拉取</el-button>
							<el-button type="warning" size="small" @click.stop="openEditDialog(row)">修改</el-button>
							<el-button type="success" size="small" @click.stop="openEnvDialog(row)">环境</el-button>
							<el-button type="danger" size="small" @click.stop="deleteService(row)">删除</el-button>
						</span>
					</template>
				</el-table-column>
			</el-table>

			<div style="margin-top: 12px">
				<el-pagination
					v-show="total > 0"
					background
					v-model:current-page="currentPage"
					v-model:page-size="pageSize"
					:page-sizes="[10, 20, 50, 100]"
					layout="total, sizes, prev, pager, next, jumper"
					:total="total"
					@size-change="loadList"
					@current-change="loadList"
				/>
			</div>
		</el-card>

		<!-- 新增/编辑对话框 -->
		<el-dialog
			v-model="dialogVisible"
			:title="isEdit ? '编辑服务' : '新增服务'"
			width="520px"
			@close="resetForm"
		>
			<el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
				<el-form-item label="服务名称" prop="name">
					<el-input v-model="formData.name" placeholder="请输入服务名称" />
				</el-form-item>
				<el-form-item label="所属项目" prop="api_project_id">
					<el-select v-model="formData.api_project_id" placeholder="请选择项目" style="width: 100%">
						<el-option
							v-for="p in projectOptions"
							:key="p.id"
							:label="p.name"
							:value="p.id"
						/>
					</el-select>
				</el-form-item>
				<el-form-item label="文档类型">
					<el-select v-model="formData.source_type" placeholder="请选择文档类型" clearable style="width: 100%">
						<el-option label="swagger" value="swagger" />
						<el-option label="apifox" value="apifox" />
					</el-select>
				</el-form-item>
				<el-form-item label="文档地址">
					<el-input v-model="formData.source_addr" placeholder="请输入文档地址 URL" />
				</el-form-item>
				<el-form-item label="负责人">
					<el-select v-model="formData.manager" placeholder="请选择负责人" clearable filterable style="width: 100%">
						<el-option
							v-for="u in userOptions"
							:key="u.id"
							:label="u.username"
							:value="u.id"
						/>
					</el-select>
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="dialogVisible = false">取消</el-button>
				<el-button type="primary" :loading="submitting" @click="submitForm">确定</el-button>
			</template>
		</el-dialog>
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
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import Sortable from 'sortablejs';
import { useApiAutomationApi } from '/@/api/v1/api_automation';
import { useUserApi } from '/@/api/v1/system/user';
import { useProjectApi } from '/@/api/v1/projects/project';

const emit = defineEmits<{
	(e: 'select-service', service: { id: number; name: string }): void;
}>();

const {
	api_service,
	add_api_service,
	edit_api_service,
	del_api_service,
	pull_api_doc,
	api_env,
	add_env,
	save_env,
	del_env,
	api_service_sort,
} = useApiAutomationApi();

const { getList: getUserList } = useUserApi();
const { getList: getProjectList } = useProjectApi();

// ---- 列表状态 ----
const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);
const searchParams = reactive({ name: '', business_id: null as number | null, manager: null as number | null });

// ---- 拖拽排序 ----
const tableRef = ref<any>(null);
let sortableInstance: Sortable | null = null;

const initSortable = () => {
	if (sortableInstance) {
		sortableInstance.destroy();
		sortableInstance = null;
	}
	const el = tableRef.value?.$el?.querySelector('.el-table__body tbody');
	if (!el) return;
	sortableInstance = Sortable.create(el, {
		handle: '.drag-handle',
		animation: 150,
		onEnd: async ({ newIndex, oldIndex }) => {
			if (newIndex === undefined || oldIndex === undefined || newIndex === oldIndex) return;
			const moved = tableData.value.splice(oldIndex, 1)[0];
			tableData.value.splice(newIndex, 0, moved);
			try {
				await api_service_sort({ ids: tableData.value.map((r: any) => r.id) });
			} catch (e: any) {
				ElMessage.error(e?.message || '排序保存失败');
			}
		},
	});
};

// ---- 筛选选项 ----
const userOptions = ref<any[]>([]);
const businessOptions = ref<any[]>([]);

const loadFilterOptions = async () => {
	try {
		const res: any = await getUserList({ page: 1, page_size: 100 });
		const raw = res?.data;
		userOptions.value = Array.isArray(raw?.items) ? raw.items : (Array.isArray(raw) ? raw : []);
	} catch {
		userOptions.value = [];
	}
	// 业务线暂无独立接口，保持空列表（可后续扩展）
	businessOptions.value = [];
};

// ---- 拉取状态 ----
const pullingIds = ref<Set<number>>(new Set());

const pullStatusMeta = (status: number | null | undefined) => {
	switch (status) {
		case 1: return { text: '成功', type: 'success' as const };
		case 2: return { text: '失败', type: 'danger' as const };
		default: return { text: '未拉取', type: 'info' as const };
	}
};

// ---- 项目选项 ----
const projectOptions = ref<any[]>([]);

const loadProjects = async () => {
	try {
		const res: any = await getProjectList({ page: 1, page_size: 100 });
		const raw = res?.data;
		projectOptions.value = Array.isArray(raw?.items) ? raw.items
			: Array.isArray(raw?.content) ? raw.content
			: Array.isArray(raw) ? raw : [];
	} catch {
		projectOptions.value = [];
	}
};

// ---- 加载列表 ----
const loadList = async () => {
	loading.value = true;
	// 确保用户列表已加载，用于显示负责人名称
	if (!userOptions.value.length) await loadFilterOptions();
	try {
		const res: any = await api_service({
			page: currentPage.value,
			pageSize: pageSize.value,
			search: {
				name: searchParams.name || undefined,
				manager: searchParams.manager ?? undefined,
				business_id: searchParams.business_id ?? undefined,
			},
		});
		const raw = res?.data;
		const list = Array.isArray(raw?.content) ? raw.content : (Array.isArray(raw) ? raw : []);
		// 补充项目名称和负责人名称
		tableData.value = list.map((item: any) => ({
			...item,
			project_name: item.project_name || item.api_project?.name || projectOptions.value.find((p: any) => p.id === item.api_project_id)?.name || '-',
			manager_name: item.manager_name || userOptions.value.find((u: any) => u.id === item.manager)?.username || (item.manager ? String(item.manager) : '-'),
		}));
		total.value = typeof raw?.total === 'number' ? raw.total : list.length;
	} finally {
		loading.value = false;
	}
	await nextTick();
	initSortable();
};

const handleSearch = () => {
	currentPage.value = 1;
	loadList();
};

const resetSearch = () => {
	searchParams.name = '';
	searchParams.business_id = null;
	searchParams.manager = null;
	currentPage.value = 1;
	loadList();
};

// ---- 双击行进入详情 ----
const onRowDblClick = (row: any) => {
	emit('select-service', { id: row.id, name: row.name });
};

// ---- 拉取文档 ----
const pullDoc = async (row: any) => {
	pullingIds.value.add(row.id);
	try {
		await pull_api_doc({
			api_service_id: row.id,
			source_type: row.source_type || 'swagger',
			doc_url: row.source_addr,
		});
		ElMessage.success('拉取成功');
		await loadList();
	} catch (e: any) {
		ElMessage.error(e?.message || '拉取失败');
		await loadList();
	} finally {
		pullingIds.value.delete(row.id);
	}
};

// ---- 删除服务 ----
const deleteService = async (row: any) => {
	try {
		await ElMessageBox.confirm(`确认删除服务「${row.name}」？该操作不可恢复。`, '提示', {
			type: 'warning',
			confirmButtonText: '确定',
			cancelButtonText: '取消',
		});
		await del_api_service({ id: row.id });
		ElMessage.success('删除成功');
		await loadList();
	} catch (e: any) {
		if (e === 'cancel' || e === 'close') return;
		ElMessage.error(e?.message || '删除失败');
	}
};

// ---- 新增/编辑对话框 ----
const dialogVisible = ref(false);
const isEdit = ref(false);
const submitting = ref(false);
const formRef = ref<FormInstance>();

const formData = reactive({
	id: 0,
	name: '',
	api_project_id: null as number | null,
	source_type: '',
	source_addr: '',
	manager: null as number | null,
});

const formRules: FormRules = {
	name: [{ required: true, message: '请输入服务名称', trigger: 'blur' }],
	api_project_id: [{ required: true, message: '请选择所属项目', trigger: 'change' }],
};

const openAddDialog = async () => {
	isEdit.value = false;
	formData.id = 0;
	formData.name = '';
	formData.api_project_id = null;
	formData.source_type = '';
	formData.source_addr = '';
	formData.manager = null;
	dialogVisible.value = true;
	if (!projectOptions.value.length) await loadProjects();
};

const openEditDialog = async (row: any) => {
	isEdit.value = true;
	formData.id = row.id;
	formData.name = row.name;
	formData.api_project_id = row.api_project_id;
	formData.source_type = row.source_type || '';
	formData.source_addr = row.source_addr || '';
	formData.manager = row.manager ?? null;
	dialogVisible.value = true;
	if (!projectOptions.value.length) await loadProjects();
};

const resetForm = () => {
	formData.id = 0;
	formData.name = '';
	formData.api_project_id = null;
	formData.source_type = '';
	formData.source_addr = '';
	formData.manager = null;
	formRef.value?.clearValidate();
};

const submitForm = async () => {
	const valid = await formRef.value?.validate().catch(() => false);
	if (!valid) return;
	submitting.value = true;
	try {
		if (isEdit.value) {
			await edit_api_service({
				id: formData.id,
				name: formData.name,
				api_project_id: formData.api_project_id!,
				source_type: formData.source_type || undefined,
				source_addr: formData.source_addr || undefined,
				manager: formData.manager ?? undefined,
			} as any);
			ElMessage.success('修改成功');
		} else {
			await add_api_service({
				name: formData.name,
				api_project_id: formData.api_project_id!,
				source_type: formData.source_type || undefined,
				source_addr: formData.source_addr || undefined,
				manager: formData.manager ?? undefined,
			} as any);
			ElMessage.success('新增成功');
		}
		dialogVisible.value = false;
		await loadList();
	} catch (e: any) {
		ElMessage.error(e?.message || '操作失败');
	} finally {
		submitting.value = false;
	}
};

// ---- 环境管理对话框 ----
const envDialogVisible = ref(false);
const envLoading = ref(false);
const envList = ref<any[]>([]);
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

const openEnvDialog = async (_row: any) => {
	envDialogVisible.value = true;
	await loadEnvList();
};

const closeEnvDialog = () => {
	envSearchName.value = '';
	envList.value = [];
};

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

onMounted(async () => {
	await Promise.all([loadProjects(), loadFilterOptions()]);
	await loadList();
});

onUnmounted(() => {
	if (sortableInstance) {
		sortableInstance.destroy();
		sortableInstance = null;
	}
});
</script>

<style scoped>
.api-list-container {
	padding: 10px;
}

.action-cell {
	white-space: nowrap;
}
</style>
