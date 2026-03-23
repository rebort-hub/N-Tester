<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { api_code, add_code, edit_code, del_code } from '/@/api/v1/api_automation';

const searchParams = ref({ currentPage: 1, pageSize: 10, search: { name__contains: '', code__contains: '' } });
const code_list = ref<any[]>([]);
const total = ref(0);
const add_form = ref<any>({ name: '', code: '' });
const addDialog = ref(false);
const editDialog = ref(false);
const title = ref('');

const get_code = async () => {
	const res: any = await api_code(searchParams.value);
	const raw = res?.data;
	const list = Array.isArray(raw?.content) ? raw.content : (Array.isArray(raw) ? raw : []);
	code_list.value = list;
	total.value = typeof raw?.total === 'number' ? raw.total : list.length;
};

const reset_search = () => {
	searchParams.value = { currentPage: 1, pageSize: 10, search: { name__contains: '', code__contains: '' } };
	get_code();
};

const openAdd = () => {
	add_form.value = { name: '', code: '' };
	title.value = '添加错误码';
	addDialog.value = true;
};

const add_confirm = async () => {
	await add_code(add_form.value);
	ElMessage.success('添加成功');
	addDialog.value = false;
	await get_code();
};

const openEdit = (row: any) => {
	add_form.value = { ...row };
	title.value = '编辑错误码';
	editDialog.value = true;
};

const edit_confirm = async () => {
	await edit_code(add_form.value);
	ElMessage.success('保存成功');
	editDialog.value = false;
	await get_code();
};

const Del_code = async (row: any) => {
	await ElMessageBox.confirm('确认删除该错误码：' + row.name + '？', '提示', { type: 'warning' });
	await del_code({ id: row.id });
	ElMessage.success('已删除');
	await get_code();
};

onMounted(() => get_code());
</script>

<template>
	<div class="api-code-popover">
		<el-form :inline="true">
			<el-form-item label="名称">
				<el-input v-model="searchParams.search.name__contains" placeholder="名称" clearable style="width: 120px" />
			</el-form-item>
			<el-form-item label="编码">
				<el-input v-model="searchParams.search.code__contains" placeholder="编码" clearable style="width: 120px" />
			</el-form-item>
			<el-form-item>
				<el-button type="primary" @click="get_code">搜索</el-button>
				<el-button @click="reset_search">重置</el-button>
				<el-button type="success" @click="openAdd">添加错误码</el-button>
			</el-form-item>
		</el-form>
		<el-table :data="code_list" border stripe size="small" max-height="280">
			<el-table-column prop="name" label="名称" width="120" />
			<el-table-column prop="code" label="错误码" show-overflow-tooltip />
			<el-table-column label="操作" width="120" fixed="right">
				<template #default="{ row }">
					<el-button type="primary" link size="small" @click="openEdit(row)">编辑</el-button>
					<el-button type="danger" link size="small" @click="Del_code(row)">删除</el-button>
				</template>
			</el-table-column>
		</el-table>
		<el-pagination
			small
			layout="total, prev, pager, next"
			:total="total"
			:page-size="searchParams.pageSize"
			:current-page="searchParams.currentPage"
			@current-change="(p: number) => { searchParams.currentPage = p; get_code(); }"
		/>
		<el-dialog v-model="addDialog" :title="title" width="400px" destroy-on-close>
			<el-form :model="add_form" label-width="80px">
				<el-form-item label="名称"><el-input v-model="add_form.name" placeholder="请输入名称" /></el-form-item>
				<el-form-item label="错误码"><el-input v-model="add_form.code" placeholder="请输入错误码" /></el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="addDialog = false">取消</el-button>
				<el-button type="primary" @click="add_confirm">确定</el-button>
			</template>
		</el-dialog>
		<el-dialog v-model="editDialog" :title="title" width="400px" destroy-on-close>
			<el-form :model="add_form" label-width="80px">
				<el-form-item label="名称"><el-input v-model="add_form.name" placeholder="请输入名称" /></el-form-item>
				<el-form-item label="错误码"><el-input v-model="add_form.code" placeholder="请输入错误码" /></el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="editDialog = false">取消</el-button>
				<el-button type="primary" @click="edit_confirm">确定</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<style scoped>
.api-code-popover { padding: 5px; }
.api-code-popover .el-pagination { margin-top: 8px; }
</style>
