<template>
	<div class="case-mgmt-container">
		<!-- 左侧用例集树 -->
		<div class="suite-panel">
			<div class="suite-panel-header">
				<el-input
					v-model="suiteKeyword"
					placeholder="搜索用例集"
					clearable
					size="small"
					prefix-icon="Search"
					style="flex: 1; margin-right: 6px"
				/>
				<el-button type="primary" size="small" icon="Plus" @click="openAddSuiteDialog(null)">新增</el-button>
			</div>

			<el-tree
				ref="suiteTreeRef"
				:data="suiteTree"
				:props="{ label: 'name', children: 'children' }"
				:filter-node-method="filterSuiteNode"
				node-key="id"
				highlight-current
				draggable
				:allow-drop="allowDrop"
				@node-drop="onSuiteDrop"
				@node-click="onSuiteNodeClick"
				class="suite-tree"
			>
				<template #default="{ node, data }">
					<span class="suite-tree-node">
						<span class="node-label" :title="data.name">{{ data.name }}</span>
						<span class="node-actions" @click.stop>
							<el-tooltip content="新增子用例集" placement="top">
								<el-icon class="node-action-icon" @click="openAddSuiteDialog(data)"><Plus /></el-icon>
							</el-tooltip>
							<el-tooltip content="编辑" placement="top">
								<el-icon class="node-action-icon" @click="openEditSuiteDialog(data)"><Edit /></el-icon>
							</el-tooltip>
							<el-tooltip content="删除" placement="top">
								<el-icon class="node-action-icon danger" @click="deleteSuite(data)"><Delete /></el-icon>
							</el-tooltip>
						</span>
					</span>
				</template>
			</el-tree>
		</div>

		<!-- 右侧用例列表 -->
		<div class="case-panel">
			<div class="case-panel-header">
				<span class="selected-suite-name">{{ selectedSuite ? selectedSuite.name : '请选择用例集' }}</span>
				<div class="case-panel-actions">
					<el-button
						type="success"
						size="small"
						icon="VideoPlay"
						:disabled="selectedCaseIds.length === 0"
						@click="openRunDialog"
					>
						执行 {{ selectedCaseIds.length > 0 ? `(${selectedCaseIds.length})` : '' }}
					</el-button>
					<el-button
						type="primary"
						size="small"
						icon="Plus"
						:disabled="!selectedSuite"
						@click="openAddCaseDialog"
					>
						新增用例
					</el-button>
				</div>
			</div>

			<!-- 执行结果摘要 -->
			<div v-if="runResult" class="run-result-bar">
				<el-alert :closable="false" type="info" style="padding: 6px 12px">
					<template #default>
						<span>
							执行完成：共 <b>{{ runResult.total }}</b> 条，
							通过 <b style="color: #67c23a">{{ runResult.pass }}</b>，
							失败 <b style="color: #f56c6c">{{ runResult.fail }}</b>
						</span>
						<el-button
							type="primary"
							link
							size="small"
							style="margin-left: 12px"
							@click="viewResultDetail"
						>查看详情</el-button>
						<el-button link size="small" @click="runResult = null">关闭</el-button>
					</template>
				</el-alert>
			</div>

			<!-- 用例类型筛选 -->
			<div class="case-type-tabs">
				<span
					v-for="t in caseTypeTabOptions"
					:key="t.value"
					class="case-type-tab"
					:class="{ active: activeCaseType === t.value }"
					@click="activeCaseType = t.value"
				>
					{{ t.label }} ({{ t.value === 0 ? caseList.length : caseList.filter(c => c.case_type === t.value).length }})
				</span>
			</div>

			<el-table
				v-loading="caseLoading"
				:data="filteredCaseList"
				border
				stripe
				empty-text="暂无用例，请先选择用例集"
				style="width: 100%"
				@selection-change="onSelectionChange"
			>
				<el-table-column type="selection" width="45" />
				<el-table-column prop="name" label="用例名称" min-width="160" show-overflow-tooltip />
				<el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip>
					<template #default="{ row }">{{ row.description || '-' }}</template>
				</el-table-column>
				<el-table-column label="类型" width="90" align="center">
					<template #default="{ row }">
						<el-tag :type="caseTypeMeta(row.case_type).color" size="small" effect="plain">
							{{ caseTypeMeta(row.case_type).label }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column label="状态" width="90" align="center">
					<template #default="{ row }">
						<el-tag :type="caseStatusMeta(row.status).type" size="small">
							{{ caseStatusMeta(row.status).text }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column label="操作" width="140" align="center" fixed="right">
					<template #default="{ row }">
						<el-button type="warning" size="small" @click="openEditCaseDialog(row)">编辑</el-button>
						<el-button type="danger" size="small" @click="deleteCase(row)">删除</el-button>
					</template>
				</el-table-column>
			</el-table>
		</div>

		<!-- 新增/编辑用例集对话框 -->
		<el-dialog
			v-model="suiteDialogVisible"
			:title="suiteDialogTitle"
			width="400px"
			@close="resetSuiteForm"
		>
			<el-form ref="suiteFormRef" :model="suiteForm" :rules="suiteFormRules" label-width="80px">
				<el-form-item label="名称" prop="name">
					<el-input v-model="suiteForm.name" placeholder="请输入用例集名称" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="suiteDialogVisible = false">取消</el-button>
				<el-button type="primary" :loading="suiteSubmitting" @click="submitSuiteForm">确定</el-button>
			</template>
		</el-dialog>

		<!-- 新增/编辑用例对话框 -->
		<el-dialog
			v-model="caseDialogVisible"
			:title="caseDialogTitle"
			width="520px"
			@close="resetCaseForm"
		>
			<el-form ref="caseFormRef" :model="caseForm" :rules="caseFormRules" label-width="80px">
				<el-form-item label="用例名称" prop="name">
					<el-input v-model="caseForm.name" placeholder="请输入用例名称" />
				</el-form-item>
				<el-form-item label="用例类型">
					<el-radio-group v-model="caseForm.case_type">
						<el-radio-button v-for="t in caseTypeOptions" :key="t.value" :value="t.value">{{ t.label }}</el-radio-button>
					</el-radio-group>
				</el-form-item>
				<el-form-item label="描述">
					<el-input v-model="caseForm.description" type="textarea" :rows="2" placeholder="请输入描述（可选）" />
				</el-form-item>
				<el-form-item label="关联接口">
					<div style="width:100%">
						<div v-if="!apiTreeData.length" style="color:var(--el-text-color-placeholder);font-size:13px;padding:8px 0">
							该服务暂无接口，请先在接口管理中创建
						</div>
						<el-tree
							v-else
							ref="caseApiTreeRef"
							:data="apiTreeData"
							:props="{ label: 'name', children: 'children' }"
							node-key="id"
							show-checkbox
							:default-expand-all="true"
							:check-strictly="false"
							style="border:1px solid var(--el-border-color);border-radius:6px;padding:4px;max-height:200px;overflow-y:auto;font-size:12px"
							@check="onApiTreeCheck"
						>
							<template #default="{ data }">
								<span style="display:flex;align-items:center;gap:4px">
									<el-tag v-if="data.method_name" size="small" :color="data.method_color" style="color:#fff;border:none;font-size:10px;padding:0 4px;height:16px;line-height:16px">{{ data.method_name }}</el-tag>
									<span>{{ data.name }}</span>
								</span>
							</template>
						</el-tree>
						<div v-if="selectedApiNodes.length" style="margin-top:6px;font-size:12px;color:var(--el-text-color-regular)">
							已选 {{ selectedApiNodes.length }} 个接口
						</div>
					</div>
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="caseDialogVisible = false">取消</el-button>
				<el-button type="primary" :loading="caseSubmitting" @click="submitCaseForm">确定</el-button>
			</template>
		</el-dialog>

		<!-- 执行配置弹窗 -->
		<el-dialog v-model="runDialogVisible" title="执行配置" width="380px">
			<el-form label-width="80px">
				<el-form-item label="已选用例">
					<span>{{ selectedCaseIds.length }} 条</span>
				</el-form-item>
				<el-form-item label="执行环境" required>
					<el-select v-model="runForm.env_id" placeholder="请选择环境" style="width: 100%">
						<el-option
							v-for="env in envList"
							:key="env.id"
							:label="env.name"
							:value="env.id"
						/>
					</el-select>
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="runDialogVisible = false">取消</el-button>
				<el-button type="primary" :loading="running" @click="confirmRun">确认执行</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import { Plus, Edit, Delete } from '@element-plus/icons-vue';
import { useApiAutomationApi } from '/@/api/v1/api_automation';

const props = defineProps<{
	serviceId: number;
	envId: number | null;
}>();

const emit = defineEmits<{
	(e: 'view-result', resultId: string): void;
}>();

const {
	api_suite_list,
	add_api_suite,
	edit_api_suite,
	del_api_suite,
	api_suite_sort,
	api_case_list,
	add_api_case,
	edit_api_case,
	del_api_case,
	run_api_case,
	api_env,
	api_params_list,
} = useApiAutomationApi();

// ---- 接口树（用于新增用例关联接口）----
const apiTreeData = ref<any[]>([]);
const loadApiTree = async () => {
	try {
		const { apiAutomationApi } = await import('/@/api/v1/api_automation');
		const r: any = await apiAutomationApi.api_tree({ search: { api_service_id: props.serviceId } });
		apiTreeData.value = Array.isArray(r?.data) ? r.data : [];
	} catch { apiTreeData.value = []; }
};

// ---- 用例集树 ----
const suiteTree = ref<any[]>([]);
const suiteTreeRef = ref<any>(null);
const suiteKeyword = ref('');
const selectedSuite = ref<any>(null);

watch(suiteKeyword, (val) => {
	suiteTreeRef.value?.filter(val);
});

const filterSuiteNode = (value: string, data: any) => {
	if (!value) return true;
	return data.name?.includes(value);
};

const loadSuiteTree = async () => {
	try {
		const res: any = await api_suite_list({ api_service_id: props.serviceId });
		const raw = res?.data;
		suiteTree.value = Array.isArray(raw) ? raw : (Array.isArray(raw?.content) ? raw.content : []);
	} catch {
		suiteTree.value = [];
	}
};

const onSuiteNodeClick = (data: any) => {
	selectedSuite.value = data;
	loadCaseList(data.id);
};

// ---- 拖拽排序 ----
const allowDrop = (draggingNode: any, dropNode: any, type: string) => {
	// 只允许同级排序（prev/next），不允许内部嵌套改变
	if (type === 'inner') return false;
	return draggingNode.data.parent === dropNode.data.parent;
};

const onSuiteDrop = async (draggingNode: any, dropNode: any, dropType: string) => {
	// 找到同级节点，提取排序后的 id 列表
	const parent = draggingNode.parent;
	const siblings: any[] = parent?.childNodes ?? [];
	const ids = siblings.map((n: any) => n.data.id);
	if (ids.length === 0) return;
	try {
		await api_suite_sort({ ids });
	} catch (e: any) {
		ElMessage.error(e?.message || '排序保存失败');
		await loadSuiteTree();
	}
};

// ---- 用例集 CRUD ----
const suiteDialogVisible = ref(false);
const suiteDialogTitle = ref('新增用例集');
const suiteSubmitting = ref(false);
const suiteFormRef = ref<FormInstance>();
const suiteForm = ref({ id: 0, name: '', parent: null as number | null, mode: 'add' as 'add' | 'edit' });
const suiteFormRules: FormRules = {
	name: [{ required: true, message: '请输入用例集名称', trigger: 'blur' }],
};

const openAddSuiteDialog = (parentData: any | null) => {
	suiteForm.value = { id: 0, name: '', parent: parentData?.id ?? null, mode: 'add' };
	suiteDialogTitle.value = parentData ? `新增子用例集（${parentData.name}）` : '新增一级用例集';
	suiteDialogVisible.value = true;
};

const openEditSuiteDialog = (data: any) => {
	suiteForm.value = { id: data.id, name: data.name, parent: data.parent ?? null, mode: 'edit' };
	suiteDialogTitle.value = '编辑用例集';
	suiteDialogVisible.value = true;
};

const resetSuiteForm = () => {
	suiteForm.value = { id: 0, name: '', parent: null, mode: 'add' };
	suiteFormRef.value?.clearValidate();
};

const submitSuiteForm = async () => {
	const valid = await suiteFormRef.value?.validate().catch(() => false);
	if (!valid) return;
	suiteSubmitting.value = true;
	try {
		if (suiteForm.value.mode === 'edit') {
			await edit_api_suite({ id: suiteForm.value.id, name: suiteForm.value.name });
			ElMessage.success('修改成功');
		} else {
			await add_api_suite({
				name: suiteForm.value.name,
				parent: suiteForm.value.parent,
				api_service_id: props.serviceId,
			});
			ElMessage.success('新增成功');
		}
		suiteDialogVisible.value = false;
		await loadSuiteTree();
	} catch (e: any) {
		ElMessage.error(e?.message || '操作失败');
	} finally {
		suiteSubmitting.value = false;
	}
};

const deleteSuite = async (data: any) => {
	try {
		await ElMessageBox.confirm(
			`确认删除用例集「${data.name}」？将级联删除所有子用例集和用例，此操作不可恢复。`,
			'提示',
			{ type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' }
		);
		await del_api_suite({ id: data.id });
		ElMessage.success('删除成功');
		if (selectedSuite.value?.id === data.id) {
			selectedSuite.value = null;
			caseList.value = [];
		}
		await loadSuiteTree();
	} catch (e: any) {
		if (e === 'cancel' || e === 'close') return;
		ElMessage.error(e?.message || '删除失败');
	}
};

// ---- 用例列表 ----
const caseList = ref<any[]>([]);
const caseLoading = ref(false);
const selectedCaseIds = ref<number[]>([]);
const activeCaseType = ref(0); // 0=全部

const caseTypeOptions = [
	{ label: '正向', value: 1, color: 'success' },
	{ label: '负向', value: 2, color: 'danger' },
	{ label: '边界值', value: 3, color: 'warning' },
	{ label: '安全性', value: 4, color: 'info' },
	{ label: '其他', value: 5, color: '' },
] as const;

const caseTypeTabOptions = [
	{ label: '全部', value: 0 },
	...caseTypeOptions,
];

const caseTypeMeta = (type: number) => {
	return caseTypeOptions.find(t => t.value === type) || { label: '其他', value: 5, color: '' };
};

const filteredCaseList = computed(() => {
	if (activeCaseType.value === 0) return caseList.value;
	return caseList.value.filter(c => c.case_type === activeCaseType.value);
});

const caseStatusMeta = (status: number) => {
	switch (status) {
		case 1: return { text: '通过', type: 'success' as const };
		case 2: return { text: '失败', type: 'danger' as const };
		default: return { text: '未执行', type: 'info' as const };
	}
};

const loadCaseList = async (suiteId: number) => {
	caseLoading.value = true;
	try {
		const res: any = await api_case_list({ suite_id: suiteId });
		const raw = res?.data;
		caseList.value = Array.isArray(raw) ? raw : (Array.isArray(raw?.content) ? raw.content : []);
	} catch {
		caseList.value = [];
	} finally {
		caseLoading.value = false;
	}
};

const onSelectionChange = (rows: any[]) => {
	selectedCaseIds.value = rows.map((r) => r.id);
};

// ---- 用例 CRUD ----
const caseDialogVisible = ref(false);
const caseDialogTitle = ref('新增用例');
const caseSubmitting = ref(false);
const caseFormRef = ref<FormInstance>();
const caseApiTreeRef = ref<any>(null);
const caseForm = ref({ id: 0, name: '', description: '', scriptText: '', case_type: 1, mode: 'add' as 'add' | 'edit' });
const selectedApiNodes = ref<any[]>([]); // 接口树已选节点

const onApiTreeCheck = (_: any, state: any) => {
	// 只取叶子节点（type===2 是接口，type===3 是用例）
	selectedApiNodes.value = state.checkedNodes.filter((n: any) => n.type === 2 || n.type === 3 || !n.children?.length);
};
const caseFormRules: FormRules = {
	name: [{ required: true, message: '请输入用例名称', trigger: 'blur' }],
};

const openAddCaseDialog = () => {
	if (!selectedSuite.value) return;
	caseForm.value = { id: 0, name: '', description: '', scriptText: '', case_type: 1, mode: 'add' };
	selectedApiNodes.value = [];
	caseDialogTitle.value = '新增用例';
	caseDialogVisible.value = true;
	loadApiTree();
};

const openEditCaseDialog = (row: any) => {
	caseForm.value = {
		id: row.id,
		name: row.name,
		description: row.description || '',
		scriptText: row.script ? JSON.stringify(row.script, null, 2) : '',
		case_type: row.case_type || 1,
		mode: 'edit',
	};
	selectedApiNodes.value = [];
	caseDialogTitle.value = '编辑用例';
	caseDialogVisible.value = true;
	loadApiTree();
};

const resetCaseForm = () => {
	caseForm.value = { id: 0, name: '', description: '', scriptText: '', case_type: 1, mode: 'add' };
	selectedApiNodes.value = [];
	caseFormRef.value?.clearValidate();
};

const parseScript = (text: string): any[] => {
	if (!text.trim()) return [];
	try {
		const parsed = JSON.parse(text);
		return Array.isArray(parsed) ? parsed : [];
	} catch {
		return [];
	}
};

const submitCaseForm = async () => {
	const valid = await caseFormRef.value?.validate().catch(() => false);
	if (!valid) return;
	caseSubmitting.value = true;
	try {
		const script = selectedApiNodes.value.length
			? selectedApiNodes.value.map((n: any) => ({ api_id: n.api_id || n.id, name: n.name, step: n.step || 1 }))
			: parseScript(caseForm.value.scriptText);
		if (caseForm.value.mode === 'edit') {
			await edit_api_case({
				id: caseForm.value.id,
				name: caseForm.value.name,
				description: caseForm.value.description,
				script,
				case_type: caseForm.value.case_type,
			});
			ElMessage.success('修改成功');
		} else {
			await add_api_case({
				name: caseForm.value.name,
				description: caseForm.value.description,
				suite_id: selectedSuite.value!.id,
				script,
				case_type: caseForm.value.case_type,
			});
			ElMessage.success('新增成功');
		}
		caseDialogVisible.value = false;
		await loadCaseList(selectedSuite.value!.id);
	} catch (e: any) {
		ElMessage.error(e?.message || '操作失败');
	} finally {
		caseSubmitting.value = false;
	}
};

const deleteCase = async (row: any) => {
	try {
		await ElMessageBox.confirm(`确认删除用例「${row.name}」？`, '提示', {
			type: 'warning',
			confirmButtonText: '确定',
			cancelButtonText: '取消',
		});
		await del_api_case({ id: row.id });
		ElMessage.success('删除成功');
		await loadCaseList(selectedSuite.value!.id);
	} catch (e: any) {
		if (e === 'cancel' || e === 'close') return;
		ElMessage.error(e?.message || '删除失败');
	}
};

// ---- 执行 ----
const runDialogVisible = ref(false);
const running = ref(false);
const runForm = ref({ env_id: null as number | null });
const envList = ref<any[]>([]);
const paramsList = ref<any[]>([]);
const runResult = ref<{ total: number; pass: number; fail: number; resultId: string } | null>(null);

const loadEnvList = async () => {
	try {
		const res: any = await api_env();
		const raw = res?.data;
		envList.value = Array.isArray(raw) ? raw : (Array.isArray(raw?.content) ? raw.content : []);
	} catch {
		envList.value = [];
	}
};

const loadParamsList = async () => {
	try {
		const res: any = await api_params_list();
		const raw = res?.data;
		paramsList.value = Array.isArray(raw) ? raw : (Array.isArray(raw?.content) ? raw.content : []);
	} catch {
		paramsList.value = [];
	}
};

const openRunDialog = async () => {
	runForm.value = { env_id: props.envId ?? null, params_id: null };
	await Promise.all([loadEnvList(), loadParamsList()]);
	runDialogVisible.value = true;
};

const confirmRun = async () => {
	if (!runForm.value.env_id) {
		ElMessage.warning('请选择执行环境');
		return;
	}
	running.value = true;
	try {
		const res: any = await run_api_case({
			case_ids: selectedCaseIds.value,
			env_id: runForm.value.env_id,
		});
		const data = res?.data;
		const resultId = data?.result_id ?? data?.id ?? '';
		const total = selectedCaseIds.value.length;
		const passCount = typeof data?.pass === 'number' ? data.pass : 0;
		const failCount = typeof data?.fail === 'number' ? data.fail : total - passCount;
		runResult.value = { total, pass: passCount, fail: failCount, resultId: String(resultId) };
		runDialogVisible.value = false;
		ElMessage.success('执行完成');
		// 刷新用例状态
		if (selectedSuite.value) {
			await loadCaseList(selectedSuite.value.id);
		}
	} catch (e: any) {
		ElMessage.error(e?.message || '执行失败');
	} finally {
		running.value = false;
	}
};

const viewResultDetail = () => {
	if (runResult.value?.resultId) {
		emit('view-result', runResult.value.resultId);
	}
};

onMounted(() => {
	loadSuiteTree();
});
</script>

<style scoped>
.case-mgmt-container {
	display: flex;
	height: 100%;
	min-height: 0;
	gap: 0;
}

/* 左侧用例集树 */
.suite-panel {
	width: 280px;
	min-width: 220px;
	max-width: 320px;
	border-right: 1px solid #e4e7ed;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.suite-panel-header {
	display: flex;
	align-items: center;
	padding: 8px;
	border-bottom: 1px solid #e4e7ed;
	flex-shrink: 0;
}

.suite-tree {
	flex: 1;
	overflow-y: auto;
	padding: 4px 0;
}

.suite-tree-node {
	display: flex;
	align-items: center;
	width: 100%;
	overflow: hidden;
}

.node-label {
	flex: 1;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
	font-size: 13px;
}

.node-actions {
	display: none;
	align-items: center;
	gap: 4px;
	flex-shrink: 0;
	margin-left: 4px;
}

.suite-tree-node:hover .node-actions {
	display: flex;
}

.node-action-icon {
	font-size: 14px;
	color: #606266;
	cursor: pointer;
	padding: 2px;
	border-radius: 2px;
}

.node-action-icon:hover {
	color: #409eff;
	background: #ecf5ff;
}

.node-action-icon.danger:hover {
	color: #f56c6c;
	background: #fef0f0;
}

/* 右侧用例列表 */
.case-panel {
	flex: 1;
	display: flex;
	flex-direction: column;
	overflow: hidden;
	padding: 8px;
	min-width: 0;
}

.case-panel-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 8px;
	flex-shrink: 0;
}

.selected-suite-name {
	font-size: 14px;
	font-weight: 600;
	color: #303133;
}

.case-panel-actions {
	display: flex;
	gap: 8px;
}

.run-result-bar {
	margin-bottom: 8px;
	flex-shrink: 0;
}

/* 用例类型筛选 tab */
.case-type-tabs {
	display: flex;
	gap: 6px;
	margin-bottom: 10px;
	flex-shrink: 0;
	flex-wrap: wrap;
}

.case-type-tab {
	padding: 4px 14px;
	border-radius: 20px;
	font-size: 12px;
	cursor: pointer;
	border: 1px solid var(--el-border-color);
	color: var(--el-text-color-regular);
	background: var(--el-bg-color);
	transition: all .15s;
	user-select: none;
	white-space: nowrap;
}

.case-type-tab:hover {
	border-color: #409eff;
	color: #409eff;
}

.case-type-tab.active {
	background: #409eff;
	border-color: #409eff;
	color: #fff;
	font-weight: 500;
}

/* 深色适配 */
.suite-panel {
	border-right-color: var(--el-border-color);
}

.suite-panel-header {
	border-bottom-color: var(--el-border-color);
}

.selected-suite-name {
	color: var(--el-text-color-primary);
}

.node-action-icon {
	color: var(--el-text-color-regular);
}

.node-action-icon:hover {
	color: #409eff;
	background: var(--el-color-primary-light-9);
}

.node-action-icon.danger:hover {
	color: #f56c6c;
	background: var(--el-color-danger-light-9);
}
</style>
