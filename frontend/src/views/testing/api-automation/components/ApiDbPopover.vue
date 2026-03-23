<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { api_db_list, add_api_db, edit_api_db, del_api_db, test_db_conn } from '/@/api/v1/api_automation';

const searchParams = ref({ currentPage: 1, pageSize: 10, search: { name__contains: '' } });
const db_list = ref<any[]>([]);
const total = ref(0);
const add_form = ref<any>({
	name: '',
	config: { host: '', port: '', database: '', user: '', password: '' },
});
const addDialog = ref(false);
const editDialog = ref(false);
const title = ref('');

const get_db = async () => {
	const res: any = await api_db_list(searchParams.value);
	const raw = res?.data;
	const list = Array.isArray(raw?.content) ? raw.content : (Array.isArray(raw) ? raw : []);
	db_list.value = list;
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
	get_db();
};

const openAdd = () => {
	add_form.value = { name: '', config: { host: '', port: '', database: '', user: '', password: '' } };
	title.value = '添加数据库';
	addDialog.value = true;
};

const add_confirm = async () => {
	await add_api_db(add_form.value);
	ElMessage.success('添加成功');
	addDialog.value = false;
	await get_db();
};

const openEdit = (row: any) => {
	add_form.value = { id: row.id, name: row.name, config: { ...row.config } };
	title.value = '编辑数据库';
	editDialog.value = true;
};

const edit_confirm = async () => {
	await edit_api_db(add_form.value);
	ElMessage.success('保存成功');
	editDialog.value = false;
	await get_db();
};

const Del_db = async (row: any) => {
	await ElMessageBox.confirm('确认删除该数据库：' + row.name + '？', '提示', { type: 'warning' });
	await del_api_db({ id: row.id });
	ElMessage.success('已删除');
	await get_db();
};

const Test_conn = async (row: any) => {
	try {
		const res: any = await test_db_conn({ id: row.id });
		const ok = res?.data?.success;
		const msg = res?.data?.message || (ok ? '连接成功' : '连接失败');
		if (ok) ElMessage.success(msg);
		else ElMessage.error(msg);
	} catch (e: any) {
		ElMessage.error(e?.message || '连接失败');
	}
};

onMounted(() => get_db());
</script>

<template>
	<div class="api-db-popover">
		<el-form :inline="true">
			<el-form-item label="名称">
				<el-input v-model="searchParams.search.name__contains" placeholder="请输入名称" clearable style="width: 160px" />
			</el-form-item>
			<el-form-item>
				<el-button type="primary" @click="get_db">搜索</el-button>
				<el-button @click="reset_search">重置</el-button>
				<el-button type="success" @click="openAdd">添加数据库</el-button>
			</el-form-item>
		</el-form>
		<el-table :data="db_list" border stripe size="small" max-height="320">
			<el-table-column prop="name" label="名称" width="100" />
			<el-table-column label="地址" width="100">
				<template #default="{ row }">{{ row.config?.host ?? '-' }}</template>
			</el-table-column>
			<el-table-column label="端口" width="80">
				<template #default="{ row }">{{ row.config?.port ?? '-' }}</template>
			</el-table-column>
			<el-table-column label="数据库" width="90">
				<template #default="{ row }">{{ row.config?.database ?? '-' }}</template>
			</el-table-column>
			<el-table-column label="用户" width="90">
				<template #default="{ row }">{{ row.config?.user ?? '-' }}</template>
			</el-table-column>
			<el-table-column label="更新时间" width="160">
				<template #default="{ row }">{{ formatTime(row.update_time || row.creation_date || row.created_at) }}</template>
			</el-table-column>
			<el-table-column label="操作" width="180" fixed="right">
				<template #default="{ row }">
					<el-button type="success" link size="small" @click="Test_conn(row)">测试连接</el-button>
					<el-button type="primary" link size="small" @click="openEdit(row)">编辑</el-button>
					<el-button type="danger" link size="small" @click="Del_db(row)">删除</el-button>
				</template>
			</el-table-column>
		</el-table>
		<el-pagination
			small
			layout="total, prev, pager, next"
			:total="total"
			:page-size="searchParams.pageSize"
			:current-page="searchParams.currentPage"
			@current-change="(p: number) => { searchParams.currentPage = p; get_db(); }"
		/>
		<el-dialog v-model="addDialog" :title="title" width="480px" destroy-on-close>
			<el-form :model="add_form" label-width="100px">
				<el-form-item label="名称"><el-input v-model="add_form.name" placeholder="请输入名称" /></el-form-item>
				<el-form-item label="数据库地址"><el-input v-model="add_form.config.host" placeholder="请输入数据库地址" /></el-form-item>
				<el-form-item label="数据库端口"><el-input v-model="add_form.config.port" placeholder="端口" /></el-form-item>
				<el-form-item label="数据库名称"><el-input v-model="add_form.config.database" placeholder="请输入数据库名称" /></el-form-item>
				<el-form-item label="数据库用户"><el-input v-model="add_form.config.user" placeholder="请输入用户" /></el-form-item>
				<el-form-item label="数据库密码"><el-input v-model="add_form.config.password" type="password" placeholder="请输入密码" show-password /></el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="addDialog = false">取消</el-button>
				<el-button type="primary" @click="add_confirm">确定</el-button>
			</template>
		</el-dialog>
		<el-dialog v-model="editDialog" :title="title" width="480px" destroy-on-close>
			<el-form :model="add_form" label-width="100px">
				<el-form-item label="名称"><el-input v-model="add_form.name" placeholder="请输入名称" /></el-form-item>
				<el-form-item label="数据库地址"><el-input v-model="add_form.config.host" placeholder="请输入数据库地址" /></el-form-item>
				<el-form-item label="数据库端口"><el-input v-model="add_form.config.port" placeholder="端口" /></el-form-item>
				<el-form-item label="数据库名称"><el-input v-model="add_form.config.database" placeholder="请输入数据库名称" /></el-form-item>
				<el-form-item label="数据库用户"><el-input v-model="add_form.config.user" placeholder="请输入用户" /></el-form-item>
				<el-form-item label="数据库密码"><el-input v-model="add_form.config.password" type="password" placeholder="留空则不修改" show-password /></el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="editDialog = false">取消</el-button>
				<el-button type="primary" @click="edit_confirm">确定</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<style scoped>
.api-db-popover { padding: 5px; }
.api-db-popover .el-pagination { margin-top: 8px; }
</style>
