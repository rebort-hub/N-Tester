<template>
	<div class="version-container">
		<el-card shadow="hover" class="search-card">
			<!-- 搜索区域 -->
			<el-form :inline="true" :model="queryForm" class="search-form">
				<el-form-item label="版本名称">
					<el-input v-model="queryForm.name" placeholder="请输入版本名称" clearable @keyup.enter="handleQuery" style="width: 200px" />
				</el-form-item>
				<el-form-item label="主干版本">
					<el-select v-model="queryForm.is_baseline" placeholder="请选择" clearable style="width: 120px">
						<el-option label="是" :value="true" />
						<el-option label="否" :value="false" />
					</el-select>
				</el-form-item>
				<el-form-item>
					<el-button type="primary" @click="handleQuery">
						<el-icon><ele-Search /></el-icon>
						查询
					</el-button>
					<el-button @click="handleReset">
						<el-icon><ele-Refresh /></el-icon>
						重置
					</el-button>
				</el-form-item>
			</el-form>
		</el-card>

		<el-card shadow="hover" class="table-card">
			<!-- 操作按钮 -->
			<div class="table-header">
				<el-button type="primary" @click="handleAdd">
					<el-icon><ele-Plus /></el-icon>
					新增版本
				</el-button>
			</div>

			<!-- 数据表格 -->
			<el-table :data="tableData" style="width: 100%" v-loading="loading" stripe>
				<el-table-column prop="id" label="ID" width="80" />
				<el-table-column prop="name" label="版本名称" min-width="150" />
				<el-table-column prop="description" label="版本描述" min-width="200" show-overflow-tooltip />
				<el-table-column prop="is_baseline" label="主干版本" width="100" align="center">
					<template #default="{ row }">
						<el-tag v-if="row.is_baseline" type="success">是</el-tag>
						<el-tag v-else type="info">否</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="project_count" label="关联项目" width="100" align="center" />
				<el-table-column prop="testcase_count" label="关联用例" width="100" align="center" />
				<el-table-column prop="creation_date" label="创建时间" width="180">
					<template #default="{ row }">
						{{ formatDateTime(row.creation_date) }}
					</template>
				</el-table-column>
				<el-table-column label="操作" width="280" fixed="right">
					<template #default="{ row }">
						<el-button type="primary" size="small" @click="handleAssociate(row)">关联用例</el-button>
						<el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
						<el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
					</template>
				</el-table-column>
			</el-table>

			<!-- 分页 -->
			<el-pagination
				v-model:current-page="queryForm.page"
				v-model:page-size="queryForm.page_size"
				:page-sizes="[10, 20, 50, 100]"
				:total="total"
				layout="total, sizes, prev, pager, next, jumper"
				@size-change="handleQuery"
				@current-change="handleQuery"
				class="pagination"
			/>
		</el-card>

		<!-- 新增/编辑对话框 -->
		<VersionForm v-if="dialogVisible" v-model="dialogVisible" :version-id="currentVersionId" @success="handleQuery" />

		<!-- 关联用例对话框 -->
		<TestCaseAssociation v-if="associateVisible" v-model="associateVisible" :version-id="currentVersionId" />
	</div>
</template>

<script setup lang="ts" name="VersionList">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { getVersionList, deleteVersion } from '/@/api/v1/testcases';
import VersionForm from './components/VersionForm.vue';
import TestCaseAssociation from './components/TestCaseAssociation.vue';

// 查询表单
const queryForm = reactive({
	name: '',
	is_baseline: null as boolean | null,
	page: 1,
	page_size: 20,
});

// 数据
const tableData = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);

// 对话框
const dialogVisible = ref(false);
const associateVisible = ref(false);
const currentVersionId = ref<number | null>(null);

// 查询
const handleQuery = async () => {
	loading.value = true;
	try {
		const params = { ...queryForm };
		// 移除空值
		if (params.is_baseline === null) {
			delete (params as any).is_baseline;
		}

		const res = await getVersionList(params);
		if (res.code === 200) {
			tableData.value = res.data.items || [];
			total.value = res.data.total || 0;
		}
	} catch (error) {
		console.error('查询失败:', error);
		ElMessage.error('查询失败');
	} finally {
		loading.value = false;
	}
};

// 重置
const handleReset = () => {
	queryForm.name = '';
	queryForm.is_baseline = null;
	queryForm.page = 1;
	handleQuery();
};

// 新增
const handleAdd = () => {
	currentVersionId.value = null;
	dialogVisible.value = true;
};

// 编辑
const handleEdit = (row: any) => {
	currentVersionId.value = row.id;
	dialogVisible.value = true;
};

// 关联用例
const handleAssociate = (row: any) => {
	currentVersionId.value = row.id;
	associateVisible.value = true;
};

// 删除
const handleDelete = (row: any) => {
	ElMessageBox.confirm(`确定要删除版本"${row.name}"吗？`, '提示', {
		confirmButtonText: '确定',
		cancelButtonText: '取消',
		type: 'warning',
	})
		.then(async () => {
			try {
				const res = await deleteVersion(row.id);
				if (res.code === 200) {
					ElMessage.success('删除成功');
					handleQuery();
				}
			} catch (error) {
				console.error('删除失败:', error);
				ElMessage.error('删除失败');
			}
		})
		.catch(() => {});
};

// 格式化日期时间
const formatDateTime = (dateTime: string) => {
	if (!dateTime) return '-';
	const date = new Date(dateTime);
	const year = date.getFullYear();
	const month = String(date.getMonth() + 1).padStart(2, '0');
	const day = String(date.getDate()).padStart(2, '0');
	const hours = String(date.getHours()).padStart(2, '0');
	const minutes = String(date.getMinutes()).padStart(2, '0');
	const seconds = String(date.getSeconds()).padStart(2, '0');
	return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
};

// 初始化
onMounted(() => {
	handleQuery();
});
</script>

<style scoped lang="scss">
.version-container {
	padding: 20px;

	.search-card {
		margin-bottom: 20px;
	}

	.table-card {
		.table-header {
			margin-bottom: 20px;
		}

		.pagination {
			margin-top: 20px;
			display: flex;
			justify-content: flex-end;
		}
	}
}
</style>
