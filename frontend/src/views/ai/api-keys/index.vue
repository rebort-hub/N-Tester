<template>
	<div class="page-wrap">
		<el-card shadow="hover" class="toolbar">
			<el-form :inline="true">
				<el-form-item label="项目">
					<el-select v-model="projectId" placeholder="选择项目" style="width: 220px" @change="onProjectChange">
						<el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
					</el-select>
				</el-form-item>
				<el-form-item label="服务类型">
					<el-select v-model="searchForm.service_type" clearable placeholder="全部" style="width: 140px" @change="load">
						<el-option label="OpenAI" value="openai" />
						<el-option label="Claude" value="claude" />
						<el-option label="Gemini" value="gemini" />
						<el-option label="通义千问" value="qwen" />
						<el-option label="GitHub" value="github" />
						<el-option label="其他" value="other" />
					</el-select>
				</el-form-item>
				<el-form-item>
					<el-button type="primary" @click="load">刷新</el-button>
					<el-button type="success" @click="openCreate">新建密钥</el-button>
				</el-form-item>
			</el-form>
		</el-card>

		<el-card shadow="hover">
			<el-table v-loading="loading" :data="rows" stripe>
				<el-table-column prop="name" label="名称" min-width="120" />
				<el-table-column prop="service_type" label="类型" width="100" />
				<el-table-column label="密钥" min-width="200">
					<template #default="{ row }">
						<span>{{ row.show ? row.api_key : mask(row.api_key) }}</span>
						<el-button link @click="row.show = !row.show">{{ row.show ? '隐藏' : '显示' }}</el-button>
					</template>
				</el-table-column>
				<el-table-column label="启用" width="90">
					<template #default="{ row }">
						<el-switch v-model="row.is_active" @change="() => quickSave(row)" />
					</template>
				</el-table-column>
				<el-table-column label="操作" width="340" fixed="right">
					<template #default="{ row }">
						<el-button size="small" type="primary" @click="testRow(row)">测试</el-button>
						<el-button size="small" type="warning" @click="editRow(row)">编辑</el-button>
						<el-button size="small" type="success" @click="regenRow(row)">重新生成</el-button>
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

		<el-dialog v-model="dlg" :title="editId ? '编辑密钥' : '新建密钥'" width="520px" destroy-on-close @closed="resetForm">
			<el-form :model="form" label-width="100px">
				<el-form-item label="名称" required>
					<el-input v-model="form.name" />
				</el-form-item>
				<el-form-item label="类型" required>
					<el-select v-model="form.service_type" style="width: 100%">
						<el-option label="openai" value="openai" />
						<el-option label="claude" value="claude" />
						<el-option label="gemini" value="gemini" />
						<el-option label="qwen" value="qwen" />
						<el-option label="github" value="github" />
						<el-option label="other" value="other" />
					</el-select>
				</el-form-item>
				<el-form-item label="密钥" required>
					<el-input v-model="form.api_key" type="password" show-password />
				</el-form-item>
				<el-form-item label="描述">
					<el-input v-model="form.description" type="textarea" rows="2" />
				</el-form-item>
				<el-form-item label="启用">
					<el-switch v-model="form.is_active" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="dlg = false">取消</el-button>
				<el-button type="primary" :loading="saving" @click="submit">保存</el-button>
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

const searchForm = reactive({ service_type: '', page: 1, page_size: 20 });

const form = reactive({
	name: '',
	service_type: 'openai',
	api_key: '',
	description: '',
	is_active: true,
});

function mask(s: string) {
	if (!s) return '';
	if (s.length <= 8) return '****';
	return s.slice(0, 4) + '****' + s.slice(-4);
}

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
		const res: any = await projectPlatformApi.apiKeys.list(projectId.value, {
			service_type: searchForm.service_type || undefined,
			page: searchForm.page,
			page_size: searchForm.page_size,
		});
		if (res?.code === 200 && res.data) {
			rows.value = (res.data.items || []).map((r: any) => ({ ...r, show: false }));
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
	form.service_type = row.service_type;
	form.api_key = row.api_key;
	form.description = row.description || '';
	form.is_active = row.is_active;
	dlg.value = true;
}

function resetForm() {
	form.name = '';
	form.service_type = 'openai';
	form.api_key = '';
	form.description = '';
	form.is_active = true;
}

async function submit() {
	if (!projectId.value) return;
	saving.value = true;
	try {
		if (editId.value) {
			const res: any = await projectPlatformApi.apiKeys.update(projectId.value, editId.value, { ...form });
			if (res?.code === 200) {
				ElMessage.success('已保存');
				dlg.value = false;
				load();
			}
		} else {
			const res: any = await projectPlatformApi.apiKeys.create(projectId.value, { ...form });
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

async function quickSave(row: any) {
	if (!projectId.value) return;
	await projectPlatformApi.apiKeys.update(projectId.value, row.id, {
		is_active: row.is_active,
	});
}

async function testRow(row: any) {
	if (!projectId.value) return;
	const res: any = await projectPlatformApi.apiKeys.test(projectId.value, row.id);
	if (res?.code === 200) {
		ElMessage.success(res.message || '测试完成');
	}
}

async function regenRow(row: any) {
	if (!projectId.value) return;
	await ElMessageBox.confirm('将生成新密钥，旧值将失效。继续？', '提示', { type: 'warning' });
	const res: any = await projectPlatformApi.apiKeys.regenerate(projectId.value, row.id);
	if (res?.code === 200) {
		ElMessage.success('已重新生成');
		load();
	}
}

async function removeRow(row: any) {
	if (!projectId.value) return;
	await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' });
	const res: any = await projectPlatformApi.apiKeys.remove(projectId.value, row.id);
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
.pager {
	margin-top: 12px;
	display: flex;
	justify-content: flex-end;
}
.toolbar {
	margin-bottom: 12px;
}
</style>
