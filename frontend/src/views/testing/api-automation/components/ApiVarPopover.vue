<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { api_var_list, add_var, edit_var, del_var } from '/@/api/v1/api_automation';

const searchParams = ref({ currentPage: 1, pageSize: 10, search: { name__contains: '' } });
const var_list = ref<any[]>([]);
const total = ref(0);
const add_form = ref<any>({ name: '', value: '' });
const addDialog = ref(false);
const editDialog = ref(false);
const title = ref('');

const get_var = async () => {
	const res: any = await api_var_list(searchParams.value);
	const raw = res?.data;
	const list = Array.isArray(raw?.content) ? raw.content : (Array.isArray(raw) ? raw : []);
	var_list.value = list;
	total.value = typeof raw?.total === 'number' ? raw.total : list.length;
};

const formatTime = (v: any) => {
	if (!v) return '-';
	const d = new Date(v);
	if (isNaN(d.getTime())) return String(v);
	const pad = (n: number) => (n < 10 ? `0${n}` : `${n}`);
	return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
};

const reset_search = () => {
	searchParams.value = { currentPage: 1, pageSize: 10, search: { name__contains: '' } };
	get_var();
};

const openAdd = () => {
	add_form.value = { name: '', value: '' };
	title.value = '添加全局变量';
	addDialog.value = true;
};

const add_confirm = async () => {
	await add_var(add_form.value);
	ElMessage.success('添加成功');
	addDialog.value = false;
	await get_var();
};

const openEdit = (row: any) => {
	add_form.value = { ...row };
	title.value = '编辑变量';
	editDialog.value = true;
};

const edit_confirm = async () => {
	await edit_var(add_form.value);
	ElMessage.success('保存成功');
	editDialog.value = false;
	await get_var();
};

const Del_var = async (row: any) => {
	await ElMessageBox.confirm('确认删除该变量：' + row.name + '？', '提示', { type: 'warning' });
	await del_var({ id: row.id });
	ElMessage.success('已删除');
	await get_var();
};

onMounted(() => get_var());
</script>

<template>
	<div class="api-var-popover">
		<el-form :inline="true">
			<el-form-item label="名称">
				<el-input v-model="searchParams.search.name__contains" placeholder="请输入名称" clearable style="width: 160px" />
			</el-form-item>
			<el-form-item>
				<el-button type="primary" @click="get_var">搜索</el-button>
				<el-button @click="reset_search">重置</el-button>
				<el-button type="success" @click="openAdd">添加变量</el-button>
			</el-form-item>
		</el-form>
		<el-table :data="var_list" border stripe size="small" max-height="320">
			<el-table-column prop="name" label="变量名" width="120" />
			<el-table-column prop="value" label="变量值" show-overflow-tooltip />
			<el-table-column label="更新时间" width="160">
				<template #default="{ row }">{{ formatTime(row.update_time || row.creation_date || row.created_at) }}</template>
			</el-table-column>
			<el-table-column prop="username" label="最后更新人" width="100" />
			<el-table-column label="操作" width="120" fixed="right">
				<template #default="{ row }">
					<el-button type="primary" link size="small" @click="openEdit(row)">编辑</el-button>
					<el-button type="danger" link size="small" @click="Del_var(row)">删除</el-button>
				</template>
			</el-table-column>
		</el-table>
		<el-pagination
			small
			layout="total, prev, pager, next"
			:total="total"
			:page-size="searchParams.pageSize"
			:current-page="searchParams.currentPage"
			@current-change="(p: number) => { searchParams.currentPage = p; get_var(); }"
		/>
		<el-dialog v-model="addDialog" :title="title" width="400px" destroy-on-close>
			<el-form :model="add_form" label-width="80px">
				<el-form-item label="变量名"><el-input v-model="add_form.name" placeholder="请输入变量名" /></el-form-item>
				<el-form-item label="变量值"><el-input v-model="add_form.value" type="textarea" :rows="3" placeholder="请输入变量值" /></el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="addDialog = false">取消</el-button>
				<el-button type="primary" @click="add_confirm">确定</el-button>
			</template>
		</el-dialog>
		<el-dialog v-model="editDialog" :title="title" width="400px" destroy-on-close>
			<el-form :model="add_form" label-width="80px">
				<el-form-item label="变量名"><el-input v-model="add_form.name" placeholder="请输入变量名" /></el-form-item>
				<el-form-item label="变量值"><el-input v-model="add_form.value" type="textarea" :rows="3" placeholder="请输入变量值" /></el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="editDialog = false">取消</el-button>
				<el-button type="primary" @click="edit_confirm">确定</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<style scoped>
.api-var-popover { padding: 5px; }
.api-var-popover .el-pagination { margin-top: 8px; }
</style>
