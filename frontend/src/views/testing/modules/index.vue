<template>
	<div class="module-tree-container">
		<!-- 顶部工具栏 -->
		<el-card shadow="hover" class="toolbar-card">
			<el-form :inline="true" :model="queryForm" class="toolbar-form">
				<el-form-item label="项目">
					<el-select v-model="queryForm.project_id" placeholder="请选择项目" clearable @change="handleProjectChange" style="width: 250px">
						<el-option v-for="project in projectList" :key="project.id" :label="project.name" :value="project.id" />
					</el-select>
				</el-form-item>
				<el-form-item>
					<el-button type="primary" size="small" @click="handleAddRootModule" :disabled="!queryForm.project_id">
						<el-icon><ele-Plus /></el-icon>
						新增根模块
					</el-button>
					<el-button type="success" size="small" @click="handleExport" :disabled="!queryForm.project_id || moduleTree.length === 0">
						<el-icon><ele-Download /></el-icon>
						导出
					</el-button>
					<el-button type="warning" size="small" @click="handleImport" :disabled="!queryForm.project_id">
						<el-icon><ele-Upload /></el-icon>
						导入
					</el-button>
					<el-button size="small" @click="handleRefresh" :disabled="!queryForm.project_id">
						<el-icon><ele-Refresh /></el-icon>
						刷新
					</el-button>
				</el-form-item>
			</el-form>
		</el-card>

		<!-- 主内容区域：左侧树 + 右侧表格 -->
		<el-card shadow="hover" class="content-card">
			<el-row :gutter="20" class="content-row">
				<!-- 左侧：模块树 -->
				<el-col :span="6" class="tree-col">
					<div class="tree-header">
						<span class="tree-title">模块结构</span>
						<el-input
							v-model="treeFilterText"
							placeholder="搜索模块"
							clearable
							size="small"
							style="width: 150px"
						>
							<template #prefix>
								<el-icon><ele-Search /></el-icon>
							</template>
						</el-input>
					</div>

					<div class="tree-content" v-loading="treeLoading">
						<el-tree
							ref="treeRef"
							:data="moduleTree"
							:props="treeProps"
							:filter-node-method="filterNode"
							:highlight-current="true"
							:expand-on-click-node="false"
							node-key="id"
							default-expand-all
							@node-click="handleNodeClick"
						>
							<template #default="{ node, data }">
								<span class="custom-tree-node">
									<span class="node-label">
										<el-icon><ele-Folder /></el-icon>
										<span>{{ node.label }}</span>
										<el-tag size="small" type="info" class="count-tag">{{ data.testcase_count || 0 }}</el-tag>
									</span>
									<span class="node-actions">
										<el-button type="primary" size="small" text @click.stop="handleAddChild(data)">
											<el-icon><ele-Plus /></el-icon>
										</el-button>
										<el-button type="primary" size="small" text @click.stop="handleEditModule(data)">
											<el-icon><ele-Edit /></el-icon>
										</el-button>
										<el-button type="danger" size="small" text @click.stop="handleDeleteModule(data)">
											<el-icon><ele-Delete /></el-icon>
										</el-button>
									</span>
								</span>
							</template>
						</el-tree>
						<el-empty v-if="!treeLoading && moduleTree.length === 0" description="暂无模块" />
					</div>
				</el-col>

				<!-- 右侧：测试用例列表 -->
				<el-col :span="18" class="table-col">
					<div class="table-header">
						<span class="table-title">
							{{ currentModule ? `${currentModule.name} - 测试用例` : '测试用例列表' }}
						</span>
						<div class="table-actions">
							<el-input
								v-model="testcaseQuery.title"
								placeholder="搜索用例标题"
								clearable
								size="small"
								style="width: 200px; margin-right: 10px"
								@keyup.enter="handleQueryTestcases"
							>
								<template #prefix>
									<el-icon><ele-Search /></el-icon>
								</template>
							</el-input>
							<el-button type="primary" size="small" @click="handleQueryTestcases">查询</el-button>
						</div>
					</div>

					<div class="table-content" v-loading="tableLoading">
						<el-table :data="testcaseList" style="width: 100%" height="calc(100vh - 320px)">
							<el-table-column prop="id" label="ID" width="80" />
							<el-table-column prop="title" label="用例标题" min-width="250" show-overflow-tooltip />
							<el-table-column prop="priority" label="优先级" width="100" align="center">
								<template #default="{ row }">
									<el-tag :type="getPriorityType(row.priority)" size="small">
										{{ getPriorityLabel(row.priority) }}
									</el-tag>
								</template>
							</el-table-column>
							<el-table-column prop="status" label="状态" width="100" align="center">
								<template #default="{ row }">
									<el-tag :type="getStatusType(row.status)" size="small">
										{{ getStatusLabel(row.status) }}
									</el-tag>
								</template>
							</el-table-column>
							<el-table-column prop="test_type" label="类型" width="120" align="center">
								<template #default="{ row }">
									{{ getTestTypeLabel(row.test_type) }}
								</template>
							</el-table-column>
							<el-table-column prop="author_name" label="作者" width="120" show-overflow-tooltip />
							<el-table-column prop="creation_date" label="创建时间" width="180">
								<template #default="{ row }">
									{{ formatDateTime(row.creation_date) }}
								</template>
							</el-table-column>
							<el-table-column label="操作" width="150" fixed="right">
								<template #default="{ row }">
									<el-button type="primary" size="small" @click="handleViewTestcase(row)">查看</el-button>
									<el-button type="success" size="small" @click="handleEditTestcase(row)">编辑</el-button>
								</template>
							</el-table-column>
						</el-table>

						<el-pagination
							v-model:current-page="testcaseQuery.page"
							v-model:page-size="testcaseQuery.page_size"
							:page-sizes="[10, 20, 50, 100]"
							:total="testcaseTotal"
							layout="total, sizes, prev, pager, next, jumper"
							@size-change="handleQueryTestcases"
							@current-change="handleQueryTestcases"
							class="pagination"
						/>
					</div>
				</el-col>
			</el-row>
		</el-card>

		<!-- 模块编辑对话框 -->
		<el-dialog
			v-model="moduleDialogVisible"
			:title="moduleDialogTitle"
			width="600px"
			:close-on-click-modal="false"
			@close="handleModuleDialogClose"
		>
			<el-form :model="moduleForm" :rules="moduleRules" ref="moduleFormRef" label-width="100px">
				<el-form-item label="模块名称" prop="name">
					<el-input v-model="moduleForm.name" placeholder="请输入模块名称" maxlength="100" show-word-limit />
				</el-form-item>
				<el-form-item label="父模块">
					<div style="display: flex; gap: 10px;">
						<el-input
							:model-value="getParentModuleName(selectedParentId)"
							placeholder="根模块"
							readonly
							style="flex: 1;"
						/>
						<el-button type="primary" size="small" @click="handleSelectParent">选择</el-button>
						<el-button type="danger" size="small" @click="selectedParentId = null" v-if="selectedParentId">清除</el-button>
					</div>
				</el-form-item>
				<el-form-item label="排序" prop="sort_order">
					<el-input-number v-model="moduleForm.sort_order" :min="0" :max="9999" style="width: 100%" />
				</el-form-item>
				<el-form-item label="描述" prop="description">
					<el-input
						v-model="moduleForm.description"
						type="textarea"
						:rows="4"
						placeholder="请输入模块描述"
						maxlength="500"
						show-word-limit
					/>
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button size="small" @click="moduleDialogVisible = false">取消</el-button>
				<el-button type="primary" size="small" @click="handleModuleSubmit" :loading="moduleSubmitLoading">确定</el-button>
			</template>
		</el-dialog>

		<!-- 导入对话框 -->
		<el-dialog v-model="importDialogVisible" title="导入模块" width="600px" :close-on-click-modal="false">
			<el-form :model="importForm" label-width="100px">
				<el-form-item label="导入文件">
					<el-upload
						ref="uploadRef"
						:auto-upload="false"
						:limit="1"
						accept=".json"
						:on-change="handleFileChange"
						:file-list="fileList"
					>
						<el-button size="small">选择文件</el-button>
						<template #tip>
							<div class="el-upload__tip">只能上传 JSON 文件</div>
						</template>
					</el-upload>
				</el-form-item>
				<el-form-item label="覆盖模式">
					<el-switch v-model="importForm.override" active-text="覆盖同名模块" inactive-text="跳过同名模块" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button size="small" @click="importDialogVisible = false">取消</el-button>
				<el-button type="primary" size="small" @click="handleImportSubmit" :loading="importLoading">导入</el-button>
			</template>
		</el-dialog>

		<!-- 父模块选择对话框 -->
		<el-dialog v-model="parentSelectDialogVisible" title="选择父模块" width="500px">
			<el-tree
				:data="moduleTree"
				:props="treeProps"
				node-key="id"
				default-expand-all
				@node-click="handleParentSelected"
			>
				<template #default="{ node, data }">
					<span class="parent-select-node">
						<el-icon><ele-Folder /></el-icon>
						<span>{{ node.label }}</span>
					</span>
				</template>
			</el-tree>
			<template #footer>
				<el-button size="small" @click="parentSelectDialogVisible = false">取消</el-button>
			</template>
		</el-dialog>

		<!-- 测试用例表单对话框 -->
		<TestCaseForm
			v-model="testcaseFormVisible"
			:project-id="queryForm.project_id || 0"
			:project-name="currentProjectName"
			:testcase-id="currentTestcaseId"
			@success="handleTestcaseSuccess"
		/>

		<!-- 测试用例详情对话框 -->
		<TestCaseDetail v-model="testcaseDetailVisible" :testcase-id="currentTestcaseId || 0" />
	</div>
</template>

<script setup lang="ts" name="ModuleTreeManagement">
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue';
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus';
import { getModuleList, createModule, updateModule, deleteModule, getModuleTree, exportModules, importModules } from '/@/api/v1/modules';
import { getProjectList } from '/@/api/v1/project';
import { getTestCaseList } from '/@/api/v1/testcases';
import TestCaseForm from '../testcases/components/TestCaseForm.vue';
import TestCaseDetail from '../testcases/components/TestCaseDetail.vue';

// 查询表单
const queryForm = reactive({
	project_id: null as number | null,
});

// 数据
const projectList = ref<any[]>([]);
const moduleTree = ref<any[]>([]);
const treeLoading = ref(false);
const treeFilterText = ref('');
const treeRef = ref();
const currentModule = ref<any>(null);

// 测试用例
const testcaseList = ref<any[]>([]);
const testcaseTotal = ref(0);
const tableLoading = ref(false);
const testcaseQuery = reactive({
	title: '',
	page: 1,
	page_size: 20,
});

// 树形配置
const treeProps = {
	children: 'children',
	label: 'name',
};

// 模块对话框
const moduleDialogVisible = ref(false);
const moduleSubmitLoading = ref(false);
const moduleFormRef = ref<FormInstance>();
const currentModuleId = ref<number | null>(null);
const selectedParentId = ref<number | null>(null); // 手动管理的父模块ID
const moduleDialogTitle = computed(() => {
	return currentModuleId.value ? '编辑模块' : '新增模块';
});

const moduleForm = reactive({
	name: '',
	description: '',
	sort_order: 0,
});

const moduleRules = {
	name: [{ required: true, message: '请输入模块名称', trigger: 'blur' }],
};

// 用于选择的扁平化模块列表
const flatModuleList = computed(() => {
	const flatten = (nodes: any[], level = 0): any[] => {
		const result: any[] = [];
		for (const node of nodes) {
			const prefix = '　'.repeat(level);
			result.push({
				id: node.id,
				label: `${prefix}${node.name}`,
				level: level,
			});
			if (node.children && node.children.length > 0) {
				result.push(...flatten(node.children, level + 1));
			}
		}
		return result;
	};
	return flatten(moduleTree.value);
});

// 导入导出
const importDialogVisible = ref(false);
const importLoading = ref(false);
const uploadRef = ref();
const fileList = ref<any[]>([]);
const importForm = reactive({
	override: false,
});

// 父模块选择对话框
const parentSelectDialogVisible = ref(false);

// 测试用例对话框
const testcaseFormVisible = ref(false);
const testcaseDetailVisible = ref(false);
const currentTestcaseId = ref<number | null>(null);

// 当前项目名称
const currentProjectName = computed(() => {
	const project = projectList.value.find((p) => p.id === queryForm.project_id);
	return project ? project.name : '';
});

// 获取父模块名称
const getParentModuleName = (parentId: number | null) => {
	if (!parentId) return '';
	
	// 递归查找模块名称
	const findModuleName = (nodes: any[], targetId: number): string => {
		for (const node of nodes) {
			if (node.id === targetId) {
				return node.name;
			}
			if (node.children && node.children.length > 0) {
				const found = findModuleName(node.children, targetId);
				if (found) return found;
			}
		}
		return '';
	};
	
	return findModuleName(moduleTree.value, parentId);
};

// 打开父模块选择对话框
const handleSelectParent = () => {
	parentSelectDialogVisible.value = true;
};

// 选择父模块
const handleParentSelected = (moduleId: number) => {
	selectedParentId.value = moduleId;
	parentSelectDialogVisible.value = false;
};

// 获取项目列表
const getProjects = async () => {
	try {
		console.log('[模块管理] 开始加载项目列表...');
		const res = await getProjectList({ page: 1, page_size: 100 });
		if (res.code === 200) {
			projectList.value = res.data.items || [];
			console.log('[模块管理] 加载了', projectList.value.length, '个项目');
			if (projectList.value.length > 0 && !queryForm.project_id) {
				queryForm.project_id = projectList.value[0].id;
				await loadModuleTree();
			}
		}
	} catch (error) {
		console.error('[模块管理] 获取项目列表失败:', error);
		ElMessage.error('获取项目列表失败');
	}
};

// 项目变化
const handleProjectChange = async () => {
	currentModule.value = null;
	testcaseList.value = [];
	testcaseTotal.value = 0;
	await loadModuleTree();
};

// 加载模块树
const loadModuleTree = async () => {
	if (!queryForm.project_id) {
		moduleTree.value = [];
		return;
	}

	treeLoading.value = true;
	try {
		console.log('[模块管理] 加载模块树，项目ID:', queryForm.project_id);
		const res = await getModuleTree(queryForm.project_id);
		console.log('[模块管理] 模块树响应:', res);
		if (res.code === 200) {
			moduleTree.value = res.data || [];
			console.log('[模块管理] 加载了', moduleTree.value.length, '个根模块');
		}
	} catch (error) {
		console.error('[模块管理] 加载模块树失败:', error);
		ElMessage.error('加载模块树失败');
		moduleTree.value = [];
	} finally {
		treeLoading.value = false;
	}
};

// 刷新
const handleRefresh = () => {
	loadModuleTree();
	if (currentModule.value) {
		handleQueryTestcases();
	}
};

// 树节点点击
const handleNodeClick = (data: any) => {
	currentModule.value = data;
	testcaseQuery.page = 1;
	handleQueryTestcases();
};

// 过滤树节点
const filterNode = (value: string, data: any) => {
	if (!value) return true;
	return data.name.includes(value);
};

// 监听搜索文本变化
watch(treeFilterText, (val) => {
	treeRef.value?.filter(val);
});

// 查询测试用例
const handleQueryTestcases = async () => {
	if (!queryForm.project_id) return;

	tableLoading.value = true;
	try {
		const params: any = {
			project_id: queryForm.project_id,
			page: testcaseQuery.page,
			page_size: testcaseQuery.page_size,
		};

		if (testcaseQuery.title) params.title = testcaseQuery.title;
		if (currentModule.value) params.module_id = currentModule.value.id;

		const res = await getTestCaseList(params);
		if (res.code === 200) {
			testcaseList.value = res.data.items || [];
			testcaseTotal.value = res.data.total || 0;
		}
	} catch (error) {
		console.error('查询测试用例失败:', error);
		ElMessage.error('查询测试用例失败');
	} finally {
		tableLoading.value = false;
	}
};

// 新增根模块
const handleAddRootModule = () => {
	currentModuleId.value = null;
	moduleForm.name = '';
	moduleForm.description = '';
	moduleForm.sort_order = 0;
	selectedParentId.value = null;
	moduleDialogVisible.value = true;
};

// 新增子模块
const handleAddChild = (data: any) => {
	currentModuleId.value = null;
	moduleForm.name = '';
	moduleForm.description = '';
	moduleForm.sort_order = 0;
	selectedParentId.value = data.id;
	moduleDialogVisible.value = true;
};

// 编辑模块
const handleEditModule = (data: any) => {
	currentModuleId.value = data.id;
	moduleForm.name = data.name;
	moduleForm.description = data.description || '';
	moduleForm.sort_order = data.sort_order || 0;
	selectedParentId.value = data.parent_id;
	moduleDialogVisible.value = true;
};

// 删除模块
const handleDeleteModule = (data: any) => {
	if (data.testcase_count > 0) {
		ElMessage.warning(`该模块下还有 ${data.testcase_count} 个测试用例，无法删除`);
		return;
	}

	if (data.children && data.children.length > 0) {
		ElMessage.warning('该模块下还有子模块，无法删除');
		return;
	}

	ElMessageBox.confirm(`确定要删除模块"${data.name}"吗？`, '提示', {
		confirmButtonText: '确定',
		cancelButtonText: '取消',
		type: 'warning',
	})
		.then(async () => {
			try {
				const res = await deleteModule(data.id);
				if (res.code === 200) {
					ElMessage.success('删除成功');
					await loadModuleTree();
					if (currentModule.value?.id === data.id) {
						currentModule.value = null;
						testcaseList.value = [];
					}
				}
			} catch (error: any) {
				console.error('删除失败:', error);
				ElMessage.error(error.message || '删除失败');
			}
		})
		.catch(() => {});
};

// 提交模块
const handleModuleSubmit = async () => {
	if (!moduleFormRef.value) return;

	await moduleFormRef.value.validate(async (valid) => {
		if (!valid) return;

		moduleSubmitLoading.value = true;
		try {
			let res;
			if (currentModuleId.value) {
				// 编辑模块
				const updateData = {
					name: moduleForm.name,
					description: moduleForm.description,
					parent_id: selectedParentId.value,
					sort_order: moduleForm.sort_order,
				};
				console.log('[模块管理] 更新模块数据:', updateData);
				res = await updateModule(currentModuleId.value, updateData);
			} else {
				// 新增模块
				const createData = {
					name: moduleForm.name,
					description: moduleForm.description,
					parent_id: selectedParentId.value,
					sort_order: moduleForm.sort_order,
					project_id: queryForm.project_id,
				};
				console.log('[模块管理] 创建模块数据:', createData);
				res = await createModule(createData);
			}

			console.log('[模块管理] API 响应:', res);
			if (res.code === 200) {
				ElMessage.success(currentModuleId.value ? '编辑成功' : '新增成功');
				moduleDialogVisible.value = false;
				
				// 重新加载模块树，并等待加载完成
				await loadModuleTree();
				
				// 确保树已经渲染完成
				await nextTick();
				
				// 如果是新增，尝试展开父节点
				if (!currentModuleId.value && selectedParentId.value) {
					const parentNode = treeRef.value?.getNode(selectedParentId.value);
					if (parentNode) {
						parentNode.expanded = true;
					}
				}
			}
		} catch (error: any) {
			console.error('[模块管理] 提交失败:', error);
			console.error('[模块管理] 错误详情:', error.response?.data);
			ElMessage.error(error.response?.data?.detail || error.message || '操作失败');
		} finally {
			moduleSubmitLoading.value = false;
		}
	});
};

// 对话框关闭
const handleModuleDialogClose = () => {
	moduleFormRef.value?.resetFields();
	currentModuleId.value = null;
};

// 导入
const handleImport = () => {
	fileList.value = [];
	importForm.override = false;
	importDialogVisible.value = true;
};

// 文件变化
const handleFileChange = (file: any) => {
	fileList.value = [file];
};

// 导入提交
const handleImportSubmit = async () => {
	if (fileList.value.length === 0) {
		ElMessage.warning('请选择要导入的文件');
		return;
	}

	const file = fileList.value[0].raw;
	const reader = new FileReader();

	reader.onload = async (e) => {
		try {
			const content = e.target?.result as string;
			const data = JSON.parse(content);

			importLoading.value = true;
			const res = await importModules({
				project_id: queryForm.project_id,
				modules: data.modules || [],
				override: importForm.override,
			});

			if (res.code === 200) {
				const result = res.data;
				ElMessage.success(
					`导入完成：成功 ${result.imported_count} 个，跳过 ${result.skipped_count} 个，失败 ${result.error_count} 个`
				);
				importDialogVisible.value = false;
				await loadModuleTree();
			}
		} catch (error: any) {
			console.error('导入失败:', error);
			ElMessage.error(error.message || '导入失败');
		} finally {
			importLoading.value = false;
		}
	};

	reader.readAsText(file);
};

// 导出
const handleExport = async () => {
	try {
		const res = await exportModules({
			project_id: queryForm.project_id,
			include_testcases: false,
		});

		if (res.code === 200) {
			// 下载JSON文件
			const dataStr = JSON.stringify(res.data, null, 2);
			const blob = new Blob([dataStr], { type: 'application/json' });
			const url = URL.createObjectURL(blob);
			const link = document.createElement('a');
			link.href = url;
			link.download = `modules_${queryForm.project_id}_${new Date().getTime()}.json`;
			link.click();
			URL.revokeObjectURL(url);
			ElMessage.success('导出成功');
		}
	} catch (error) {
		console.error('导出失败:', error);
		ElMessage.error('导出失败');
	}
};

// 查看测试用例
const handleViewTestcase = (row: any) => {
	currentTestcaseId.value = row.id;
	testcaseDetailVisible.value = true;
};

// 编辑测试用例
const handleEditTestcase = (row: any) => {
	currentTestcaseId.value = row.id;
	testcaseFormVisible.value = true;
};

// 测试用例操作成功回调
const handleTestcaseSuccess = () => {
	// 刷新测试用例列表
	handleQueryTestcases();
	// 刷新模块树（更新用例数量）
	loadModuleTree();
};

// 辅助函数
const getPriorityType = (priority: string) => {
	const map: Record<string, any> = {
		critical: 'danger',
		high: 'warning',
		medium: '',
		low: 'info',
	};
	return map[priority] || '';
};

const getPriorityLabel = (priority: string) => {
	const map: Record<string, string> = {
		critical: '紧急',
		high: '高',
		medium: '中',
		low: '低',
	};
	return map[priority] || priority;
};

const getStatusType = (status: string) => {
	const map: Record<string, any> = {
		draft: 'info',
		active: 'success',
		deprecated: 'danger',
	};
	return map[status] || '';
};

const getStatusLabel = (status: string) => {
	const map: Record<string, string> = {
		draft: '草稿',
		active: '激活',
		deprecated: '废弃',
	};
	return map[status] || status;
};

const getTestTypeLabel = (type: string) => {
	const map: Record<string, string> = {
		functional: '功能测试',
		integration: '集成测试',
		api: 'API测试',
		ui: 'UI测试',
		performance: '性能测试',
		security: '安全测试',
	};
	return map[type] || type;
};

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
	console.log('[模块管理] 组件已挂载，开始初始化...');
	getProjects();
});
</script>

<style scoped lang="scss">
.module-tree-container {
	padding: 20px;
	height: calc(100vh - 100px);
	display: flex;
	flex-direction: column;

	.toolbar-card {
		margin-bottom: 20px;
		flex-shrink: 0;

		.toolbar-form {
			margin-bottom: 0;
		}
	}

	.content-card {
		flex: 1;
		overflow: hidden;

		.content-row {
			height: 100%;

			.tree-col,
			.table-col {
				height: 100%;
				display: flex;
				flex-direction: column;
			}

			.tree-col {
				border-right: 1px solid #e4e7ed;
				padding-right: 20px;
			}
		}
	}

	.tree-header,
	.table-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 15px;
		padding-bottom: 10px;
		border-bottom: 1px solid #e4e7ed;

		.tree-title,
		.table-title {
			font-size: 16px;
			font-weight: 600;
			color: #303133;
		}

		.table-actions {
			display: flex;
			align-items: center;
		}
	}

	.tree-content {
		flex: 1;
		overflow-y: auto;
		overflow-x: hidden;

		.custom-tree-node {
			flex: 1;
			display: flex;
			align-items: center;
			justify-content: space-between;
			font-size: 14px;
			padding-right: 8px;
			min-width: 0; // 允许子元素收缩

			.node-label {
				display: flex;
				align-items: center;
				gap: 8px;
				flex: 1;
				min-width: 0; // 允许收缩
				overflow: hidden;

				> span {
					overflow: hidden;
					text-overflow: ellipsis;
					white-space: nowrap;
				}

				.count-tag {
					margin-left: 8px;
					flex-shrink: 0; // 标签不收缩
				}
			}

			.node-actions {
				display: none;
				gap: 4px;
				flex-shrink: 0; // 按钮不收缩
				margin-left: 8px;
			}

			&:hover .node-actions {
				display: flex;
			}
		}
	}

	.table-content {
		flex: 1;
		display: flex;
		flex-direction: column;

		.pagination {
			margin-top: 20px;
			display: flex;
			justify-content: flex-end;
		}
	}
}

.parent-select-node {
	display: flex;
	align-items: center;
	gap: 8px;
	cursor: pointer;
	
	&:hover {
		color: var(--el-color-primary);
	}
}
</style>
