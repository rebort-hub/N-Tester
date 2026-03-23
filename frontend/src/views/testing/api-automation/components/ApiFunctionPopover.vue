<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { api_function, add_function, edit_function, del_function } from '/@/api/v1/api_automation';

const searchParams = ref({ currentPage: 1, pageSize: 10, search: { name__contains: '' } });
const function_list = ref<any[]>([]);
const total = ref(0);
const add_form = ref<any>({ name: '', description: '' });
const addDialog = ref(false);
const editDialog = ref(false);
const title = ref('');

const get_function = async () => {
	const res: any = await api_function(searchParams.value);
	const raw = res?.data;
	const list = Array.isArray(raw?.content) ? raw.content : (Array.isArray(raw) ? raw : []);
	function_list.value = list;
	total.value = typeof raw?.total === 'number' ? raw.total : list.length;
};

const reset_search = () => {
	searchParams.value = { currentPage: 1, pageSize: 10, search: { name__contains: '' } };
	get_function();
};

const openAdd = () => {
	add_form.value = { name: '', description: '' };
	title.value = '添加公共函数';
	addDialog.value = true;
};

const add_confirm = async () => {
	await add_function(add_form.value);
	ElMessage.success('添加成功');
	addDialog.value = false;
	await get_function();
};

const openEdit = (row: any) => {
	add_form.value = { ...row };
	title.value = '编辑公共函数';
	editDialog.value = true;
};

const edit_confirm = async () => {
	await edit_function(add_form.value);
	ElMessage.success('保存成功');
	editDialog.value = false;
	await get_function();
};

const Del_function = async (row: any) => {
	await ElMessageBox.confirm('确认删除该函数：' + row.name + '？', '提示', { type: 'warning' });
	await del_function({ id: row.id });
	ElMessage.success('已删除');
	await get_function();
};

onMounted(() => get_function());
</script>

<template>
	<div class="api-function-popover">
		<el-form :inline="true">
			<el-form-item label="名称">
				<el-input v-model="searchParams.search.name__contains" placeholder="请输入名称" clearable style="width: 160px" />
			</el-form-item>
			<el-form-item>
				<el-button type="primary" @click="get_function">搜索</el-button>
				<el-button @click="reset_search">重置</el-button>
				<el-button type="success" @click="openAdd">添加公共函数</el-button>
			</el-form-item>
		</el-form>
		<el-table :data="function_list" border stripe size="small" max-height="320">
			<el-table-column prop="name" label="名称" width="140" />
			<el-table-column prop="description" label="描述" show-overflow-tooltip />
			<el-table-column prop="username" label="最后更新人" width="100" />
			<el-table-column label="操作" width="120" fixed="right">
				<template #default="{ row }">
					<el-button type="primary" link size="small" @click="openEdit(row)">编辑</el-button>
					<el-button type="danger" link size="small" @click="Del_function(row)">删除</el-button>
				</template>
			</el-table-column>
		</el-table>
		<el-pagination
			small
			layout="total, prev, pager, next"
			:total="total"
			:page-size="searchParams.pageSize"
			:current-page="searchParams.currentPage"
			@current-change="(p: number) => { searchParams.currentPage = p; get_function(); }"
		/>
		<el-dialog v-model="addDialog" :title="title" width="400px" destroy-on-close>
			<el-form :model="add_form" label-width="80px">
				<el-form-item label="名称"><el-input v-model="add_form.name" placeholder="请输入名称" /></el-form-item>
				<el-form-item label="描述"><el-input v-model="add_form.description" type="textarea" :rows="3" placeholder="请输入描述" /></el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="addDialog = false">取消</el-button>
				<el-button type="primary" @click="add_confirm">确定</el-button>
			</template>
		</el-dialog>
		<el-dialog v-model="editDialog" :title="title" width="400px" destroy-on-close>
			<el-form :model="add_form" label-width="80px">
				<el-form-item label="名称"><el-input v-model="add_form.name" placeholder="请输入名称" /></el-form-item>
				<el-form-item label="描述"><el-input v-model="add_form.description" type="textarea" :rows="3" placeholder="请输入描述" /></el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="editDialog = false">取消</el-button>
				<el-button type="primary" @click="edit_confirm">确定</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<style scoped>
.api-function-popover { padding: 5px; }
.api-function-popover .el-pagination { margin-top: 8px; }
</style>
