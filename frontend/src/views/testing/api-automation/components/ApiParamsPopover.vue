<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { api_params, add_params, edit_params, del_params } from '/@/api/v1/api_automation';

const searchParams = ref({ currentPage: 1, pageSize: 10, search: { name__contains: '' } });
const params_list = ref<any[]>([]);
const total = ref(0);
const add_form = ref<any>({ name: '', value: '{}' });
const addDialog = ref(false);
const editDialog = ref(false);
const title = ref('');

const get_params = async () => {
	const res: any = await api_params(searchParams.value);
	const raw = res?.data;
	const list = Array.isArray(raw?.content) ? raw.content : (Array.isArray(raw) ? raw : []);
	params_list.value = list;
	total.value = typeof raw?.total === 'number' ? raw.total : list.length;
};

const reset_search = () => {
	searchParams.value = { currentPage: 1, pageSize: 10, search: { name__contains: '' } };
	get_params();
};

const openAdd = () => {
	add_form.value = { name: '', value: {} };
	title.value = '添加参数依赖';
	addDialog.value = true;
};

const add_confirm = async () => {
	let val: any = {};
	try {
		val = JSON.parse(add_form.value.value || '{}');
	} catch (_) {
		ElMessage.error('值必须是合法 JSON');
		return;
	}
	await add_params({ name: add_form.value.name, value: val });
	ElMessage.success('添加成功');
	addDialog.value = false;
	await get_params();
};

const openEdit = (row: any) => {
	add_form.value = {
		id: row.id,
		name: row.name,
		value: typeof row.value === 'string' ? row.value : JSON.stringify(row.value || {}, null, 2),
	};
	title.value = '编辑参数依赖';
	editDialog.value = true;
};

const edit_confirm = async () => {
	let val: any = {};
	try {
		val = JSON.parse(add_form.value.value || '{}');
	} catch (_) {
		ElMessage.error('值必须是合法 JSON');
		return;
	}
	await edit_params({ id: add_form.value.id, name: add_form.value.name, value: val });
	ElMessage.success('保存成功');
	editDialog.value = false;
	await get_params();
};

const Del_params = async (row: any) => {
	await ElMessageBox.confirm('确认删除该参数依赖：' + row.name + '？', '提示', { type: 'warning' });
	await del_params({ id: row.id });
	ElMessage.success('已删除');
	await get_params();
};

onMounted(() => get_params());
</script>

<template>
	<div class="api-params-popover">
		<el-form :inline="true">
			<el-form-item label="名称">
				<el-input v-model="searchParams.search.name__contains" placeholder="请输入名称" clearable style="width: 160px" />
			</el-form-item>
			<el-form-item>
				<el-button type="primary" @click="get_params">搜索</el-button>
				<el-button @click="reset_search">重置</el-button>
				<el-button type="success" @click="openAdd">添加参数依赖</el-button>
			</el-form-item>
		</el-form>
		<el-table :data="params_list" border stripe size="small" max-height="320">
			<el-table-column prop="name" label="名称" width="140" />
			<el-table-column prop="value" label="值" show-overflow-tooltip />
			<el-table-column label="操作" width="120" fixed="right">
				<template #default="{ row }">
					<el-button type="primary" link size="small" @click="openEdit(row)">编辑</el-button>
					<el-button type="danger" link size="small" @click="Del_params(row)">删除</el-button>
				</template>
			</el-table-column>
		</el-table>
		<el-pagination
			small
			layout="total, prev, pager, next"
			:total="total"
			:page-size="searchParams.pageSize"
			:current-page="searchParams.currentPage"
			@current-change="(p: number) => { searchParams.currentPage = p; get_params(); }"
		/>
		<el-dialog v-model="addDialog" :title="title" width="560px" destroy-on-close>
			<el-form :model="add_form" label-width="80px">
				<el-form-item label="名称"><el-input v-model="add_form.name" placeholder="请输入名称" /></el-form-item>
				<el-form-item label="值(JSON)">
					<el-input v-model="add_form.value" type="textarea" :rows="6" placeholder='{"key":"value"}' />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="addDialog = false">取消</el-button>
				<el-button type="primary" @click="add_confirm">确定</el-button>
			</template>
		</el-dialog>
		<el-dialog v-model="editDialog" :title="title" width="560px" destroy-on-close>
			<el-form :model="add_form" label-width="80px">
				<el-form-item label="名称"><el-input v-model="add_form.name" placeholder="请输入名称" /></el-form-item>
				<el-form-item label="值(JSON)">
					<el-input v-model="add_form.value" type="textarea" :rows="6" placeholder='{"key":"value"}' />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="editDialog = false">取消</el-button>
				<el-button type="primary" @click="edit_confirm">确定</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<style scoped>
.api-params-popover { padding: 5px; }
.api-params-popover .el-pagination { margin-top: 8px; }
</style>
