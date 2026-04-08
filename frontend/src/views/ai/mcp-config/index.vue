<template>
	<div class="page-wrap">
		<el-card shadow="hover" class="toolbar">
			<el-form :inline="true">
				<el-form-item label="项目">
					<el-select v-model="projectId" placeholder="选择项目" style="width: 220px" @change="onProjectChange">
						<el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
					</el-select>
				</el-form-item>
				<el-form-item label="搜索">
					<el-input v-model="searchForm.search" clearable placeholder="配置名称" style="width: 200px" @keyup.enter="load" />
				</el-form-item>
				<el-form-item>
					<el-button type="primary" @click="load">刷新</el-button>
					<el-button type="success" @click="openCreate">新建配置</el-button>
				</el-form-item>
			</el-form>
		</el-card>

		<el-card shadow="hover" class="table-card">
			<el-table v-loading="loading" :data="rows" stripe>
				<el-table-column prop="name" label="名称" min-width="140" />
				<el-table-column prop="url" label="URL" min-width="220" show-overflow-tooltip />
				<el-table-column prop="transport" label="协议" width="120" />
				<el-table-column label="启用" width="100">
					<template #default="{ row }">
						<el-switch v-model="row.is_enabled" @change="() => patchRow(row)" />
					</template>
				</el-table-column>
				<el-table-column label="操作" width="300" fixed="right">
					<template #default="{ row }">
						<el-button size="small" type="primary" @click="testRow(row)">测试</el-button>
						<el-button size="small" type="success" @click="openTools(row)">工具</el-button>
						<el-button size="small" type="warning" @click="editRow(row)">编辑</el-button>
						<el-button size="small" type="danger" @click="removeRow(row)">删除</el-button>
					</template>
				</el-table-column>
			</el-table>
			<div class="pager" v-if="total > 0">
				<el-pagination
					v-model:current-page="searchForm.page"
					v-model:page-size="searchForm.page_size"
					:total="total"
					layout="total, prev, pager, next"
					@current-change="load"
				/>
			</div>
		</el-card>

		<el-dialog v-model="dlg" :title="editId ? '编辑 MCP' : '新建 MCP'" width="560px" destroy-on-close @closed="resetForm">
			<el-form :model="form" label-width="100px">
				<el-form-item label="名称" required>
					<el-input v-model="form.name" />
				</el-form-item>
				<el-form-item label="URL" required>
					<el-input v-model="form.url" />
				</el-form-item>
				<el-form-item label="协议">
					<el-select v-model="form.transport" style="width: 100%">
						<el-option label="streamable-http" value="streamable-http" />
						<el-option label="sse" value="sse" />
					</el-select>
				</el-form-item>
				<el-form-item label="启用">
					<el-switch v-model="form.is_enabled" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="dlg = false">取消</el-button>
				<el-button type="primary" :loading="saving" @click="submit">保存</el-button>
			</template>
		</el-dialog>

		<el-dialog v-model="toolsDlg" title="MCP 工具列表" width="780px" destroy-on-close>
			<el-alert
				v-if="toolsErr"
				:title="toolsErr"
				type="error"
				show-icon
				:closable="false"
				style="margin-bottom: 10px"
			/>
			<el-table v-loading="toolsLoading" :data="tools" size="small" max-height="520">
				<el-table-column prop="name" label="名称" min-width="220" />
				<el-table-column prop="description" label="描述" min-width="260" show-overflow-tooltip />
				<el-table-column label="参数" min-width="240">
					<template #default="{ row }">
						<el-text type="info">{{ formatSchema(row.input_schema) }}</el-text>
					</template>
				</el-table-column>
			</el-table>
			<template #footer>
				<el-button @click="toolsDlg = false">关闭</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useProjectApi } from '/@/api/v1/projects/project';
import { projectPlatformApi } from '/@/api/v1/projects/platform';

const projectApi = useProjectApi();
const projectId = ref<number | null>(null);
const projects = ref<{ id: number; name: string }[]>([]);
const loading = ref(false);
const saving = ref(false);
const rows = ref<any[]>([]);
const total = ref(0);
const dlg = ref(false);
const editId = ref<number | null>(null);
const toolsDlg = ref(false);
const toolsLoading = ref(false);
const toolsErr = ref('');
const tools = ref<any[]>([]);

const searchForm = reactive({ search: '', page: 1, page_size: 20 });

const form = reactive({
	name: '',
	url: '',
	transport: 'streamable-http',
	is_enabled: true,
});

async function loadProjects() {
	try {
		const res: any = await projectApi.getList({ page: 1, page_size: 50 });
		if (res?.code === 200 && res.data?.items) {
			projects.value = res.data.items;
			const stored = localStorage.getItem('defaultProjectId');
			if (stored && projects.value.some((p) => p.id === Number(stored))) {
				projectId.value = Number(stored);
			} else if (projects.value.length) {
				projectId.value = projects.value[0].id;
				localStorage.setItem('defaultProjectId', String(projectId.value));
			}
		}
	} catch (e: any) {
		ElMessage.error(e?.message || '获取项目列表失败');
	}
}

function onProjectChange() {
	if (projectId.value) localStorage.setItem('defaultProjectId', String(projectId.value));
	load();
}

async function load() {
	if (!projectId.value) return;
	loading.value = true;
	try {
		const res: any = await projectPlatformApi.mcp.list(projectId.value, {
			search: searchForm.search,
			page: searchForm.page,
			page_size: searchForm.page_size,
		});
		if (res?.code === 200 && res.data) {
			rows.value = res.data.items || [];
			total.value = res.data.total || 0;
		}
	} finally {
		loading.value = false;
	}
}

function openCreate() {
	editId.value = null;
	resetForm();
	dlg.value = true;
}

function editRow(row: any) {
	editId.value = row.id;
	form.name = row.name;
	form.url = row.url;
	form.transport = row.transport || 'streamable-http';
	form.is_enabled = row.is_enabled;
	dlg.value = true;
}

function resetForm() {
	form.name = '';
	form.url = '';
	form.transport = 'streamable-http';
	form.is_enabled = true;
}

async function submit() {
	if (!projectId.value) return;
	saving.value = true;
	try {
		if (editId.value) {
			const res: any = await projectPlatformApi.mcp.update(projectId.value, editId.value, { ...form });
			if (res?.code === 200) {
				ElMessage.success('已保存');
				dlg.value = false;
				load();
			}
		} else {
			const res: any = await projectPlatformApi.mcp.create(projectId.value, { ...form });
			if (res?.code === 200) {
				ElMessage.success('已创建');
				dlg.value = false;
				load();
			}
		}
	} finally {
		saving.value = false;
	}
}

async function patchRow(row: any) {
	if (!projectId.value) return;
	await projectPlatformApi.mcp.update(projectId.value, row.id, {
		name: row.name,
		url: row.url,
		transport: row.transport,
		headers: row.headers || {},
		is_enabled: row.is_enabled,
	});
}

async function testRow(row: any) {
	if (!projectId.value) return;
	try {
		const res: any = await projectPlatformApi.mcp.test(projectId.value, row.id);
		if (res?.code === 200) {
			const ok = res.data?.ok;
			const status = res.data?.status_code;
			if (ok) {
				ElMessage.success(res.message || '连接成功');
			} else {
				const msg = res.message || (status ? `连接失败（HTTP ${status}）` : '连接失败');
				ElMessage.error(msg);
			}
		}
	} catch (e: any) {
		ElMessage.error(e?.message || '测试失败');
	}
}

function formatSchema(schema: any): string {
	if (!schema) return '-';
	try {
		const props = schema.properties || schema?.json_schema?.properties;
		if (!props || typeof props !== 'object') return JSON.stringify(schema).slice(0, 120);
		const keys = Object.keys(props);
		return keys.length ? keys.join(', ') : '-';
	} catch {
		return '-';
	}
}

async function openTools(row: any) {
	if (!projectId.value) return;
	toolsDlg.value = true;
	toolsLoading.value = true;
	toolsErr.value = '';
	tools.value = [];
	try {
		const res: any = await projectPlatformApi.mcp.tools(projectId.value, row.id);
		if (res?.code === 200 && res.data?.tools) {
			tools.value = res.data.tools;
		}
	} catch (e: any) {
		toolsErr.value = e?.message || '获取工具列表失败';
	} finally {
		toolsLoading.value = false;
	}
}

async function removeRow(row: any) {
	if (!projectId.value) return;
	await ElMessageBox.confirm('确定删除该配置？', '提示', { type: 'warning' });
	const res: any = await projectPlatformApi.mcp.remove(projectId.value, row.id);
	if (res?.code === 200) {
		ElMessage.success('已删除');
		load();
	}
}

onMounted(async () => {
	await loadProjects();
	await load();
});
</script>

<style scoped>
.page-wrap {
	padding: 12px;
}
.toolbar {
	margin-bottom: 12px;
}
.pager {
	margin-top: 12px;
	display: flex;
	justify-content: flex-end;
}
</style>
