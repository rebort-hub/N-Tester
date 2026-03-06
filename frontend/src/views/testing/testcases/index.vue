<template>
	<div class="testcase-container">
		<el-card shadow="hover" class="search-card">
			<!-- 搜索区域 -->
			<el-form :inline="true" :model="queryForm" class="search-form">
				<el-form-item label="项目">
					<el-select v-model="queryForm.project_id" placeholder="请选择项目" clearable @change="handleProjectChange" style="width: 200px">
						<el-option v-for="project in projectList" :key="project.id" :label="project.name" :value="project.id" />
					</el-select>
				</el-form-item>
				<el-form-item label="模块" v-if="queryForm.project_id">
					<el-select 
						v-model="queryForm.module_id" 
						placeholder="请选择模块" 
						clearable 
						@change="handleQuery" 
						style="width: 200px"
						:key="`module-select-${queryForm.project_id}`"
					>
						<el-option v-for="module in moduleList" :key="module.id" :label="module.name" :value="module.id" />
					</el-select>
				</el-form-item>
				<el-form-item label="标题">
					<el-input v-model="queryForm.title" placeholder="请输入用例标题" clearable @keyup.enter="handleQuery" style="width: 200px" />
				</el-form-item>
				<el-form-item label="状态">
					<el-select v-model="queryForm.status" placeholder="请选择状态" clearable style="width: 120px">
						<el-option label="草稿" value="draft" />
						<el-option label="激活" value="active" />
						<el-option label="已废弃" value="deprecated" />
					</el-select>
				</el-form-item>
				<el-form-item label="优先级">
					<el-select v-model="queryForm.priority" placeholder="请选择优先级" clearable style="width: 120px">
						<el-option label="低" value="low" />
						<el-option label="中" value="medium" />
						<el-option label="高" value="high" />
						<el-option label="紧急" value="critical" />
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
				<el-button type="primary" @click="handleAdd" :disabled="!queryForm.project_id">
					<el-icon><ele-Plus /></el-icon>
					新增用例
				</el-button>
				<el-button type="success" @click="handleImportExcel" :disabled="!queryForm.project_id">
					<el-icon><ele-Upload /></el-icon>
					导入Excel
				</el-button>
				<el-button type="warning" @click="handleExportExcel" :disabled="!queryForm.project_id">
					<el-icon><ele-Download /></el-icon>
					导出Excel
				</el-button>
			</div>

			<!-- 数据表格 -->
			<el-table :data="tableData" style="width: 100%" v-loading="loading">
				<el-table-column prop="id" label="ID" width="80" />
				<el-table-column prop="title" label="用例标题" min-width="200" show-overflow-tooltip />
				<el-table-column prop="module_name" label="所属模块" width="150" show-overflow-tooltip>
					<template #default="{ row }">
						<el-tag v-if="row.module_name" type="info" size="small">{{ row.module_name }}</el-tag>
						<span v-else style="color: #999">-</span>
					</template>
				</el-table-column>
				<el-table-column prop="priority" label="优先级" width="100">
					<template #default="{ row }">
						<el-tag v-if="row.priority === 'critical'" type="danger">紧急</el-tag>
						<el-tag v-else-if="row.priority === 'high'" type="warning">高</el-tag>
						<el-tag v-else-if="row.priority === 'medium'" type="info">中</el-tag>
						<el-tag v-else type="success">低</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="status" label="状态" width="100">
					<template #default="{ row }">
						<el-tag v-if="row.status === 'active'" type="success">激活</el-tag>
						<el-tag v-else-if="row.status === 'draft'" type="info">草稿</el-tag>
						<el-tag v-else type="danger">已废弃</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="test_type" label="类型" width="120">
					<template #default="{ row }">
						{{ getTestTypeLabel(row.test_type) }}
					</template>
				</el-table-column>
				<el-table-column prop="author_name" label="作者" width="120" />
				<el-table-column prop="assignee_name" label="指派人" width="120" />
				<el-table-column prop="creation_date" label="创建时间" width="180">
					<template #default="{ row }">
						{{ formatDateTime(row.creation_date) }}
					</template>
				</el-table-column>
				<el-table-column label="操作" width="240" fixed="right">
					<template #default="{ row }">
						<el-button type="primary" size="small" @click="handleView(row)">查看</el-button>
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
		<TestCaseForm
			v-model="dialogVisible"
			:project-id="queryForm.project_id || 0"
			:project-name="currentProjectName"
			:testcase-id="currentTestCaseId"
			@success="handleQuery"
		/>

		<!-- 详情对话框 -->
		<TestCaseDetail v-model="detailVisible" :testcase-id="currentTestCaseId || 0" />

		<!-- Excel导入对话框 -->
		<el-dialog 
			v-model="excelImportDialogVisible" 
			title="从Excel导入测试用例"
			width="600px"
			:close-on-click-modal="false"
		>
			<el-form label-width="100px">
				<el-form-item label="选择项目" required>
					<el-select 
						v-model="excelProjectId" 
						placeholder="请选择项目" 
						clearable
						style="width: 100%"
					>
						<el-option
							v-for="project in projectList"
							:key="project.id"
							:label="project.name"
							:value="project.id"
						/>
					</el-select>
				</el-form-item>
				
				<el-form-item label="选择模块">
					<el-select 
						v-model="excelModuleId" 
						:key="`excel-module-${excelProjectId || 'none'}`"
						placeholder="不选择则按Sheet名称匹配模块" 
						clearable
						style="width: 100%"
						:disabled="!excelProjectId"
						:loading="excelModuleLoading"
					>
						<el-option
							v-for="module in excelModuleList"
							:key="module.id"
							:label="module.name"
							:value="module.id"
						/>
					</el-select>
					<div style="color: #909399; font-size: 12px; margin-top: 5px;">
						<div>• 指定模块：所有Sheet的用例导入到该模块</div>
						<div>• 不指定模块：每个Sheet名称对应一个模块名称</div>
					</div>
				</el-form-item>
				
				<el-form-item label="选择文件">
					<el-upload
						:auto-upload="false"
						:on-change="handleExcelFileChange"
						:limit="1"
						accept=".xlsx,.xls"
						drag
					>
						<el-icon class="el-icon--upload"><ele-UploadFilled /></el-icon>
						<div class="el-upload__text">
							将Excel文件拖到此处，或<em>点击上传</em>
						</div>
						<template #tip>
							<div class="el-upload__tip">
								只支持 .xlsx 和 .xls 格式的Excel文件
							</div>
						</template>
					</el-upload>
				</el-form-item>
				
				<el-form-item>
					<el-alert
						type="info"
						:closable="false"
						show-icon
					>
						<template #title>
							<div>
								<div style="font-weight: bold; margin-bottom: 8px;">Excel文件格式要求：</div>
								<ul style="margin: 5px 0; padding-left: 20px;">
									<li>必需列：用例标题</li>
									<li>可选列：用例描述、优先级、前置条件、测试步骤、预期结果</li>
								</ul>
								<div style="font-weight: bold; margin: 10px 0 5px 0;">多模块导入：</div>
								<ul style="margin: 5px 0; padding-left: 20px;">
									<li>创建多个Sheet，每个Sheet名称对应一个模块名称</li>
									<li>系统会自动将用例导入到对应的模块中</li>
								</ul>
								<a 
									href="/static/templates/AI_TestCase_Template.xlsx"
									download="TestCase_Template.xlsx"
									style="color: #409eff; text-decoration: none; margin-top: 5px; display: inline-block;"
									target="_blank"
								>
									📥 下载Excel模板
								</a>
							</div>
						</template>
					</el-alert>
				</el-form-item>
			</el-form>
			
			<template #footer>
				<el-button @click="excelImportDialogVisible = false">取消</el-button>
				<el-button 
					type="primary" 
					@click="submitExcelImport"
					:loading="excelImportLoading"
					:disabled="!excelProjectId || !excelFile"
				>
					开始导入
				</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts" name="TestCaseList">
import { ref, reactive, onMounted, computed, nextTick, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { getTestCaseList, deleteTestCase, importTestCasesFromExcel, exportTestCasesToExcel } from '/@/api/v1/testcases';
import { getProjectList } from '/@/api/v1/project';
import { getModuleList } from '/@/api/v1/modules';
import TestCaseForm from './components/TestCaseForm.vue';
import TestCaseDetail from './components/TestCaseDetail.vue';

// 查询表单
const queryForm = reactive({
	project_id: null as number | null,
	module_id: null as number | null,
	title: '',
	status: '',
	priority: '',
	page: 1,
	page_size: 20,
});

// 数据
const tableData = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);
const projectList = ref<any[]>([]);
const moduleList = ref<any[]>([]);

// 对话框
const dialogVisible = ref(false);
const detailVisible = ref(false);
const currentTestCaseId = ref<number | null>(null);
const currentProjectName = computed(() => {
	const project = projectList.value.find((p) => p.id === queryForm.project_id);
	return project ? project.name : '';
});

// 获取项目列表
const getProjects = async () => {
	try {
		const res = await getProjectList({ page: 1, page_size: 100 });
		if (res.code === 200) {
			projectList.value = res.data.rows || [];
			// 如果有项目，自动选中第一个
			if (projectList.value.length > 0 && !queryForm.project_id) {
				queryForm.project_id = projectList.value[0].id;
				await getModules();
				handleQuery();
			}
		}
	} catch (error) {
		console.error('获取项目列表失败:', error);
	}
};

// 获取模块列表
const getModules = async () => {
	if (!queryForm.project_id) {
		moduleList.value = [];
		return;
	}
	
	try {
		const res = await getModuleList({ project_id: queryForm.project_id, page: 1, page_size: 100 });
		if (res.code === 200) {
			moduleList.value = res.data.items || [];
		}
	} catch (error) {
		console.error('获取模块列表失败:', error);
	}
};

// 项目变更
const handleProjectChange = async () => {
	// 清空数据
	tableData.value = [];
	moduleList.value = [];
	queryForm.module_id = null;
	
	// 加载新项目的模块列表
	if (queryForm.project_id) {
		await getModules();
		handleQuery();
	}
};

// 查询
const handleQuery = async () => {
	if (!queryForm.project_id) {
		ElMessage.warning('请先选择项目');
		return;
	}

	loading.value = true;
	try {
		// 过滤掉空值参数
		const params: any = {
			project_id: queryForm.project_id,
			page: queryForm.page,
			page_size: queryForm.page_size,
		};
		
		if (queryForm.module_id) params.module_id = queryForm.module_id;
		if (queryForm.title) params.title = queryForm.title;
		if (queryForm.status) params.status = queryForm.status;
		if (queryForm.priority) params.priority = queryForm.priority;
		
		const res = await getTestCaseList(params);
		if (res.code === 200) {
			const items = res.data.items || res.data.rows || [];
			const totalCount = res.data.total || res.data.rowTotal || 0;
			
			tableData.value = items;
			total.value = totalCount;
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
	queryForm.module_id = null;
	queryForm.title = '';
	queryForm.status = '';
	queryForm.priority = '';
	queryForm.page = 1;
	if (queryForm.project_id) {
		handleQuery();
	}
};

// 新增
const handleAdd = () => {
	currentTestCaseId.value = null;
	dialogVisible.value = true;
};

// 编辑
const handleEdit = (row: any) => {
	currentTestCaseId.value = row.id;
	dialogVisible.value = true;
};

// 查看
const handleView = (row: any) => {
	currentTestCaseId.value = row.id;
	detailVisible.value = true;
};

// 删除
const handleDelete = (row: any) => {
	ElMessageBox.confirm(`确定要删除测试用例"${row.title}"吗？`, '提示', {
		confirmButtonText: '确定',
		cancelButtonText: '取消',
		type: 'warning',
	})
		.then(async () => {
			try {
				const res = await deleteTestCase(row.id);
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

// 获取测试类型标签
const getTestTypeLabel = (type: string) => {
	const typeMap: Record<string, string> = {
		functional: '功能测试',
		integration: '集成测试',
		api: 'API测试',
		ui: 'UI测试',
		performance: '性能测试',
		security: '安全测试',
	};
	return typeMap[type] || type;
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

// ========== Excel导入相关 ==========

// Excel导入状态
const excelImportDialogVisible = ref(false);
const excelImportLoading = ref(false);
const excelFile = ref<File | null>(null);
const excelProjectId = ref<number | null>(null);
const excelModuleId = ref<number | null>(null);
const excelModuleList = ref([]);
const excelModuleLoading = ref(false);

// 打开导入对话框
const handleImportExcel = () => {
	excelProjectId.value = queryForm.project_id;
	excelModuleId.value = null;
	excelModuleList.value = [];
	excelFile.value = null;
	excelModuleLoading.value = false;
	
	excelImportDialogVisible.value = true;
	
	// 如果已选择项目，加载模块列表
	if (excelProjectId.value) {
		loadExcelModules(excelProjectId.value);
	}
};

// 监听Excel项目变化
watch(() => excelProjectId.value, async (projectId) => {
	excelModuleId.value = null;
	excelModuleList.value = [];
	
	if (!projectId) {
		excelModuleLoading.value = false;
		return;
	}
	
	await loadExcelModules(projectId);
});

// 加载模块列表
const loadExcelModules = async (projectId: number) => {
	excelModuleLoading.value = true;
	try {
		const res = await getModuleList({ project_id: projectId, page: 1, page_size: 1000 });
		if (res.code === 200) {
			excelModuleList.value = res.data.items || [];
		}
	} catch (error) {
		console.error('获取模块列表失败:', error);
		ElMessage.error('获取模块列表失败');
	} finally {
		excelModuleLoading.value = false;
	}
};

// 选择Excel文件
const handleExcelFileChange = (file: any) => {
	excelFile.value = file.raw;
	return false;
};

// 提交Excel导入
const submitExcelImport = async () => {
	if (!excelFile.value) {
		ElMessage.warning('请选择Excel文件');
		return;
	}
	
	if (!excelProjectId.value) {
		ElMessage.warning('请选择项目');
		return;
	}
	
	excelImportLoading.value = true;
	try {
		const res = await importTestCasesFromExcel(
			excelFile.value, 
			excelProjectId.value, 
			excelModuleId.value || undefined
		);
		
		if (res.code === 200) {
			const data = res.data || {};
			const imported = data.imported_count || 0;
			const skipped = data.skipped_count || 0;
			const errors = data.error_count || 0;
			const mode = data.mode;
			
			let message = `成功导入 ${imported} 个用例`;
			if (skipped > 0) {
				message += `，跳过 ${skipped} 个已存在的用例`;
			}
			if (errors > 0) {
				message += `，${errors} 个失败`;
			}
			
			ElMessage.success(message);
			
			// 如果是多模块模式，显示详细结果
			if (mode === 'multi_module' && data.sheet_results) {
				console.log('多模块导入结果:', data.sheet_results);
				
				const failedSheets = data.sheet_results.filter((r: any) => r.status !== 'success');
				if (failedSheets.length > 0) {
					const failedNames = failedSheets.map((r: any) => r.sheet).join(', ');
					ElMessage.warning(`以下Sheet导入失败或跳过: ${failedNames}`);
				}
			}
			
			excelImportDialogVisible.value = false;
			excelFile.value = null;
			excelProjectId.value = null;
			excelModuleId.value = null;
			excelModuleList.value = [];
			
			// 刷新列表
			handleQuery();
		}
	} catch (error: any) {
		console.error('Excel导入失败:', error);
		ElMessage.error(error.message || 'Excel导入失败');
	} finally {
		excelImportLoading.value = false;
	}
};

// ========== Excel导出相关 ==========

// 导出Excel
const handleExportExcel = async () => {
	if (!queryForm.project_id) {
		ElMessage.warning('请先选择项目');
		return;
	}
	
	try {
		ElMessage.info('正在导出，请稍候...');
		
		// 构建导出参数（使用当前筛选条件）
		const params: any = {
			project_id: queryForm.project_id,
		};
		
		if (queryForm.module_id) params.module_id = queryForm.module_id;
		if (queryForm.status) params.status = queryForm.status;
		if (queryForm.priority) params.priority = queryForm.priority;
		
		const res = await exportTestCasesToExcel(params);
		
		// 创建下载链接
		const blob = new Blob([res], { 
			type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
		});
		const url = window.URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = url;
		
		// 生成文件名
		const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
		const projectName = currentProjectName.value || 'testcases';
		link.download = `${projectName}_testcases_${timestamp}.xlsx`;
		
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		window.URL.revokeObjectURL(url);
		
		ElMessage.success('导出成功');
	} catch (error: any) {
		console.error('导出失败:', error);
		ElMessage.error(error.message || '导出失败');
	}
};

// 初始化
onMounted(() => {
	getProjects();
});
</script>

<style scoped lang="scss">
.testcase-container {
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
