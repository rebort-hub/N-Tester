<template>
	<div class="apm-layout">
		<!-- 左侧模块树 -->
		<div class="apm-sidebar">
			<div class="sidebar-header">
				<span class="sidebar-title">
					<el-icon class="sidebar-title-icon"><Grid /></el-icon>
					模块树
				</span>
				<div class="sidebar-actions">
					<el-tooltip content="新增根模块" placement="top">
						<el-button type="primary" size="small" :icon="Plus" circle @click="openAddRootModule" />
					</el-tooltip>
					<el-tooltip content="刷新" placement="top">
						<el-button size="small" :icon="Refresh" circle @click="loadMenuTree" />
					</el-tooltip>
				</div>
			</div>
			<el-input
				v-model="filterText"
				clearable
				placeholder="过滤模块名称"
				size="small"
				class="sidebar-filter"
				:prefix-icon="Search"
			/>
			<el-scrollbar :height="treeScrollHeight" class="sidebar-tree-wrap">
				<el-tree
					ref="treeRef"
					:data="treeData"
					:props="treeProps"
					node-key="id"
					default-expand-all
					highlight-current
					:filter-node-method="filterNode"
					@node-click="onTreeClick"
				>
					<template #default="{ data }">
						<span class="tree-node">
							<span class="tree-node-label">
								<el-icon v-if="data.type === 0" class="tree-ico root"><HomeFilled /></el-icon>
								<el-icon v-else-if="data.type === 1" class="tree-ico folder"><Folder /></el-icon>
								<el-icon v-else class="tree-ico leaf"><Document /></el-icon>
								<span class="tree-node-name">{{ data.name }}</span>
							</span>
							<span class="tree-node-ops" @click.stop>
								<el-dropdown trigger="click" placement="bottom-end" @command="(cmd: string) => onTreeNodeCmd(cmd, data)">
									<el-icon class="tree-more"><MoreFilled /></el-icon>
									<template #dropdown>
										<el-dropdown-menu>
											<el-dropdown-item v-if="data.type === 0 || data.type === 1" command="addChild" :icon="FolderAdd">
												新增子模块
											</el-dropdown-item>
											<el-dropdown-item v-if="data.type !== 0" command="rename" :icon="Edit">
												重命名
											</el-dropdown-item>
											<el-dropdown-item v-if="data.type !== 0" command="delete" :icon="Delete" class="danger-item">
												删除
											</el-dropdown-item>
										</el-dropdown-menu>
									</template>
								</el-dropdown>
							</span>
						</span>
					</template>
				</el-tree>
			</el-scrollbar>
		</div>

		<!-- 右侧内容区 -->
		<div class="apm-content">
			<!-- 工具栏 -->
			<div class="content-toolbar">
				<div class="toolbar-left">
					<template v-if="selectedModuleId">
						<el-icon class="toolbar-module-icon"><Folder /></el-icon>
						<span class="toolbar-module-name">{{ selectedModuleName }}</span>
						<el-tag size="small" type="info" class="toolbar-module-id">ID: {{ selectedModuleId }}</el-tag>
					</template>
					<span v-else class="toolbar-placeholder">请从左侧选择模块</span>
				</div>
				<el-button type="primary" size="small" :icon="Plus" :disabled="!selectedModuleId" @click="openPageDialog('add')">
					新增页面
				</el-button>
			</div>

			<!-- 空状态 -->
			<div v-if="!selectedModuleId" class="content-empty">
				<el-empty description="请先从左侧选择一个模块" :image-size="80" />
			</div>

			<!-- 表格 -->
			<template v-else>
				<el-table
					v-loading="tableLoading"
					element-loading-text="正在获取数据"
					:data="pageRows"
					stripe
					row-key="id"
					:height="tableHeight"
					class="page-table"
					@row-dblclick="onRowDblclick"
				>
					<el-table-column label="排序" width="52" align="center">
						<template #header>
							<el-tooltip content="拖拽图标可排序" placement="top">
								<el-icon class="help-ico"><QuestionFilled /></el-icon>
							</el-tooltip>
						</template>
						<template #default="scope">
							<el-button text class="drag-btn" draggable="true"
								@dragstart="onDragStart($event, scope.row, scope.$index)"
								@dragover="onDragOver($event)"
								@drop="onDrop($event, scope.$index)"
								@dragend="onDragEnd($event)">
								<el-icon><Rank /></el-icon>
							</el-button>
						</template>
					</el-table-column>
					<el-table-column label="序号" width="56" align="center">
						<template #default="scope">
							{{ (pageQuery.currentPage - 1) * pageQuery.pageSize + scope.$index + 1 }}
						</template>
					</el-table-column>
					<el-table-column prop="name" label="页面名称" min-width="130" show-overflow-tooltip />
					<el-table-column prop="activity" label="Activity / 标识" min-width="150" show-overflow-tooltip />
					<el-table-column prop="package_name" label="包名" min-width="130" show-overflow-tooltip />
					<el-table-column prop="remark" label="备注" min-width="100" show-overflow-tooltip />
					<el-table-column label="操作" width="240" align="center" fixed="right">
						<template #default="{ row }">
							<el-button type="primary" size="small" @click="openPageDialog('edit', row)">修改</el-button>
							<el-button type="success" size="small" @click="openElementDialog(row)">元素列表</el-button>
							<el-popconfirm title="复制此页面并生成新页面？" @confirm="copyPage(row)">
								<template #reference>
									<el-button type="warning" size="small">复制</el-button>
								</template>
							</el-popconfirm>
							<el-popconfirm :title="`确定删除「${row.name}」？`" @confirm="deletePage(row)">
								<template #reference>
									<el-button type="danger" size="small">删除</el-button>
								</template>
							</el-popconfirm>
						</template>
					</el-table-column>
				</el-table>

				<el-pagination
					v-show="pageTotal > 0"
					class="page-pager"
					background
					layout="total, prev, pager, next, sizes"
					:total="pageTotal"
					v-model:current-page="pageQuery.currentPage"
					v-model:page-size="pageQuery.pageSize"
					:page-sizes="[10, 20, 50]"
					@current-change="loadPageList"
					@size-change="onPageSizeChange"
				/>
			</template>
		</div>

		<!-- 新增/编辑模块 dialog -->
		<el-dialog v-model="moduleDlg.visible" :title="moduleDlg.title" width="420px" destroy-on-close>
			<el-form ref="moduleFormRef" :model="moduleForm" :rules="moduleRules" label-width="90px">
				<el-form-item label="模块名称" prop="name">
					<el-input v-model="moduleForm.name" placeholder="请输入模块名称" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="moduleDlg.visible = false">取消</el-button>
				<el-button type="primary" :loading="moduleSaving" @click="submitModule">确定</el-button>
			</template>
		</el-dialog>

		<!-- 页面新增/编辑 dialog -->
		<el-dialog v-model="pageDlg.visible" :title="pageDlg.mode === 'add' ? '新增页面' : '修改页面'" width="520px" destroy-on-close>
			<el-form ref="pageFormRef" :model="pageForm" :rules="pageRules" label-width="100px">
				<el-form-item label="页面名称" prop="name">
					<el-input v-model="pageForm.name" placeholder="页面名称" />
				</el-form-item>
				<el-form-item label="Activity">
					<el-input v-model="pageForm.activity" placeholder="可选，如 .MainActivity" />
				</el-form-item>
				<el-form-item label="包名">
					<el-input v-model="pageForm.package_name" placeholder="可选" />
				</el-form-item>
				<el-form-item label="备注">
					<el-input v-model="pageForm.remark" type="textarea" :rows="2" placeholder="可选" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="pageDlg.visible = false">取消</el-button>
				<el-button type="primary" :loading="pageSaving" @click="submitPage">保存</el-button>
			</template>
		</el-dialog>

		<!-- 元素列表 dialog -->
		<el-dialog v-model="elementDlg.visible" :title="`元素列表 — ${elementDlg.pageName}`" width="800px" destroy-on-close @opened="loadElements">
			<div class="element-toolbar">
				<el-button type="primary" size="small" :icon="Plus" @click="openElementForm('add')">新增元素</el-button>
				<el-button type="success" size="small" :icon="Upload" @click="importDlg.visible = true">导入元素</el-button>
				<el-button size="small" :icon="Download" @click="downloadElementTemplate">下载 JSON 模板</el-button>
			</div>
			<el-table v-loading="elementLoading" :data="elementRows" size="small" max-height="400" stripe row-key="id">
				<el-table-column label="排序" width="48" align="center">
					<template #header>
						<el-tooltip content="拖拽排序" placement="top">
							<el-icon class="help-ico"><QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<template #default="scope">
						<el-button text class="drag-btn" draggable="true"
							@dragstart="onElementDragStart($event, scope.row, scope.$index)"
							@dragover="onElementDragOver($event)"
							@drop="onElementDrop($event, scope.$index)"
							@dragend="onElementDragEnd($event)">
							<el-icon><Rank /></el-icon>
						</el-button>
					</template>
				</el-table-column>
				<el-table-column type="index" label="序号" width="56" align="center" />
				<el-table-column prop="name" label="名称" min-width="110" />
				<el-table-column prop="locate_type" label="定位类型" width="120" />
				<el-table-column prop="locate_value" label="定位值" min-width="180" show-overflow-tooltip />
				<el-table-column label="操作" width="120" align="center">
					<template #default="{ row }">
						<el-button type="primary" link size="small" @click="openElementForm('edit', row)">修改</el-button>
						<el-popconfirm title="删除该元素？" @confirm="deleteElement(row)">
							<template #reference>
								<el-button type="danger" link size="small">删除</el-button>
							</template>
						</el-popconfirm>
					</template>
				</el-table-column>
			</el-table>
		</el-dialog>

		<!-- 导入元素 dialog -->
		<el-dialog v-model="importDlg.visible" title="导入元素（JSON）" width="560px" destroy-on-close append-to-body>
			<el-alert type="info" :closable="false" style="margin-bottom: 12px">
				支持 JSON 数组，每项含 <code>name</code>、<code>locate_type</code>（默认 id）、<code>locate_value</code>。
			</el-alert>
			<input ref="importFileRef" type="file" accept=".json,application/json" class="hidden-file" @change="onImportFile" />
			<el-button size="small" :icon="Upload" @click="triggerImportFile">选择文件</el-button>
			<el-input v-model="importJsonText" type="textarea" :rows="10" class="import-textarea"
				placeholder='[{"name":"登录按钮","locate_type":"id","locate_value":"com.app:id/btn_login"}]' />
			<template #footer>
				<el-button @click="importDlg.visible = false">取消</el-button>
				<el-button type="primary" :loading="importSubmitting" @click="submitElementImport">导入</el-button>
			</template>
		</el-dialog>

		<!-- 元素新增/编辑 dialog -->
		<el-dialog v-model="elementForm.visible" :title="elementForm.mode === 'add' ? '新增元素' : '修改元素'" width="480px" destroy-on-close append-to-body>
			<el-form ref="elementFormRef" :model="elementForm" :rules="elementRules" label-width="100px">
				<el-form-item label="名称" prop="name">
					<el-input v-model="elementForm.name" />
				</el-form-item>
				<el-form-item label="定位类型" prop="locate_type">
					<el-select v-model="elementForm.locate_type" style="width: 100%">
						<el-option label="id" value="id" />
						<el-option label="xpath" value="xpath" />
						<el-option label="accessibility_id" value="accessibility_id" />
						<el-option label="class_name" value="class_name" />
						<el-option label="其它" value="other" />
					</el-select>
				</el-form-item>
				<el-form-item label="定位值" prop="locate_value">
					<el-input v-model="elementForm.locate_value" type="textarea" :rows="3" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="elementForm.visible = false">取消</el-button>
				<el-button type="primary" :loading="elementSaving" @click="submitElement">保存</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { ElTree, FormInstance, FormRules } from 'element-plus';
import {
	HomeFilled, Folder, Document, Rank, QuestionFilled,
	Plus, Refresh, Search, MoreFilled, FolderAdd, Edit, Delete,
	Grid, Upload, Download,
} from '@element-plus/icons-vue';
import { copyText } from '/@/utils';
import { useAppManagementApi } from '/@/api/v1/app_management';

const api = useAppManagementApi();

// ── 树 ──────────────────────────────────────────────────────────────
const treeRef = ref<InstanceType<typeof ElTree>>();
const treeData = ref<any[]>([]);
const filterText = ref('');
const treeProps = { children: 'children', label: 'name' };
const selectedModuleId = ref<number | null>(null);
const selectedModuleName = ref('');

watch(filterText, (v) => treeRef.value?.filter(v));
function filterNode(value: string, data: any) {
	return !value || String(data.name || '').includes(value);
}

async function loadMenuTree() {
	try {
		const res: any = await api.app_menu({});
		const raw = res?.data ?? res;
		treeData.value = Array.isArray(raw) ? raw : raw?.data ?? [];
		await nextTick();
		if (selectedModuleId.value && treeRef.value) {
			treeRef.value.setCurrentKey(selectedModuleId.value);
		}
	} catch {
		treeData.value = [];
		ElMessage.error('加载模块树失败');
	}
}

function onTreeClick(data: any) {
	if (data.type !== 0 && data.type !== 1) {
		ElMessage.warning('请选根目录或文件夹作为模块');
		return;
	}
	selectedModuleId.value = data.id;
	selectedModuleName.value = data.name;
	pageQuery.value.currentPage = 1;
	loadPageList();
}

// ── 模块树节点操作 ────────────────────────────────────────────────────
const moduleDlg = ref({ visible: false, title: '', mode: '' as 'addRoot' | 'addChild' | 'rename', targetData: null as any });
const moduleFormRef = ref<FormInstance>();
const moduleSaving = ref(false);
const moduleForm = ref({ name: '' });
const moduleRules: FormRules = {
	name: [{ required: true, message: '请输入模块名称', trigger: 'blur' }],
};

function openAddRootModule() {
	moduleDlg.value = { visible: true, title: '新增根模块', mode: 'addRoot', targetData: null };
	moduleForm.value = { name: '' };
}

function onTreeNodeCmd(cmd: string, data: any) {
	if (cmd === 'addChild') {
		moduleDlg.value = { visible: true, title: '新增子模块', mode: 'addChild', targetData: data };
		moduleForm.value = { name: '' };
	} else if (cmd === 'rename') {
		moduleDlg.value = { visible: true, title: '重命名', mode: 'rename', targetData: data };
		moduleForm.value = { name: data.name };
	} else if (cmd === 'delete') {
		ElMessageBox.confirm(`确定删除模块「${data.name}」及其下所有内容？`, '删除确认', {
			type: 'warning',
			confirmButtonText: '删除',
			confirmButtonClass: 'el-button--danger',
		}).then(async () => {
			try {
				await api.del_menu({ id: data.id, type: data.type });
				ElMessage.success('已删除');
				if (selectedModuleId.value === data.id) {
					selectedModuleId.value = null;
					selectedModuleName.value = '';
					pageRows.value = [];
				}
				await loadMenuTree();
			} catch {
				ElMessage.error('删除失败');
			}
		}).catch(() => {});
	}
}

async function submitModule() {
	await moduleFormRef.value?.validate();
	moduleSaving.value = true;
	try {
		const { mode, targetData } = moduleDlg.value;
		if (mode === 'addRoot') {
			// 根目录下新增子模块（pid = 根节点 id，取树第一个根）
			const rootNode = treeData.value[0];
			if (!rootNode) { ElMessage.error('请先确保存在根目录'); return; }
			await api.add_menu({ name: moduleForm.value.name, type: 1, pid: rootNode.id });
		} else if (mode === 'addChild') {
			await api.add_menu({ name: moduleForm.value.name, type: 1, pid: targetData.id });
		} else if (mode === 'rename') {
			await api.rename_menu({ id: targetData.id, name: moduleForm.value.name });
		}
		ElMessage.success('操作成功');
		moduleDlg.value.visible = false;
		await loadMenuTree();
	} catch {
		ElMessage.error('操作失败');
	} finally {
		moduleSaving.value = false;
	}
}

// ── 页面列表 ──────────────────────────────────────────────────────────
const tableLoading = ref(false);
const pageRows = ref<any[]>([]);
const pageTotal = ref(0);
const pageQuery = ref({ currentPage: 1, pageSize: 20 });

async function loadPageList() {
	if (!selectedModuleId.value) { pageRows.value = []; pageTotal.value = 0; return; }
	tableLoading.value = true;
	try {
		const res: any = await api.pageList({
			module_menu_id: selectedModuleId.value,
			currentPage: pageQuery.value.currentPage,
			pageSize: pageQuery.value.pageSize,
		});
		const payload = res?.data ?? res;
		pageRows.value = payload?.data ?? [];
		pageTotal.value = Number(payload?.total ?? 0);
	} finally {
		tableLoading.value = false;
	}
}

function onPageSizeChange() {
	pageQuery.value.currentPage = 1;
	loadPageList();
}

// ── 页面新增/编辑 ─────────────────────────────────────────────────────
const pageDlg = ref({ visible: false, mode: 'add' as 'add' | 'edit' });
const pageFormRef = ref<FormInstance>();
const pageSaving = ref(false);
const pageForm = ref({ id: 0, name: '', activity: '', package_name: '', remark: '' });
const pageRules: FormRules = {
	name: [{ required: true, message: '请输入页面名称', trigger: 'blur' }],
};

function openPageDialog(mode: 'add' | 'edit', row?: any) {
	pageDlg.value.mode = mode;
	pageForm.value = mode === 'add'
		? { id: 0, name: '', activity: '', package_name: '', remark: '' }
		: { id: row.id, name: row.name, activity: row.activity || '', package_name: row.package_name || '', remark: row.remark || '' };
	pageDlg.value.visible = true;
}

async function submitPage() {
	await pageFormRef.value?.validate();
	pageSaving.value = true;
	try {
		if (pageDlg.value.mode === 'add') {
			await api.pageAdd({ module_menu_id: selectedModuleId.value, ...pageForm.value });
			ElMessage.success('已新增');
		} else {
			await api.pageUpdate(pageForm.value);
			ElMessage.success('已保存');
		}
		pageDlg.value.visible = false;
		await loadPageList();
	} finally {
		pageSaving.value = false;
	}
}

async function copyPage(row: any) {
	await api.pageCopy({ id: row.id });
	ElMessage.success('已复制');
	await loadPageList();
}

async function deletePage(row: any) {
	await api.pageDelete({ id: row.id });
	ElMessage.success('已删除');
	await loadPageList();
}

// ── 拖拽排序（页面） ──────────────────────────────────────────────────
let dragOldIndex: number | undefined;
let dragRow: any;

function onDragStart(e: DragEvent, row: any, index: number) {
	dragOldIndex = index; dragRow = row;
	e.dataTransfer!.effectAllowed = 'move';
	(e.target as HTMLElement).classList.add('dragging');
}
function onDragOver(e: DragEvent) { e.preventDefault(); }
function onDragEnd(e: DragEvent) { (e.target as HTMLElement).classList.remove('dragging'); }
async function onDrop(e: DragEvent, newIndex: number) {
	e.preventDefault();
	(e.target as HTMLElement).classList.remove('dragging');
	if (dragOldIndex === undefined || !dragRow) return;
	const list = [...pageRows.value];
	list.splice(dragOldIndex, 1);
	list.splice(newIndex, 0, dragRow);
	tableLoading.value = true;
	try {
		await api.pageSort({ id_list: list.map((r) => r.id) });
		await loadPageList();
	} finally { tableLoading.value = false; }
}

async function onRowDblclick(row: any, column: any) {
	const prop = column?.property;
	if (prop && row[prop] != null) {
		try { await copyText(String(row[prop]), '已复制'); } catch { void 0; }
	}
}

// ── 元素列表 ──────────────────────────────────────────────────────────
const elementDlg = ref({ visible: false, pageId: 0, pageName: '' });
const elementRows = ref<any[]>([]);
const elementLoading = ref(false);
const elementForm = ref<any>({ visible: false, mode: 'add', id: 0, name: '', locate_type: 'id', locate_value: '' });
const elementFormRef = ref<FormInstance>();
const elementSaving = ref(false);
const elementRules: FormRules = {
	name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
	locate_value: [{ required: true, message: '请输入定位值', trigger: 'blur' }],
};

function openElementDialog(row: any) {
	elementDlg.value = { visible: true, pageId: row.id, pageName: row.name };
	elementRows.value = [];
}

async function loadElements() {
	if (!elementDlg.value.pageId) return;
	elementLoading.value = true;
	try {
		const res: any = await api.pageElementList({ page_id: elementDlg.value.pageId });
		const raw = res?.data ?? res;
		elementRows.value = Array.isArray(raw) ? raw : [];
	} finally { elementLoading.value = false; }
}

function openElementForm(mode: 'add' | 'edit', row?: any) {
	elementForm.value = mode === 'add'
		? { visible: true, mode: 'add', id: 0, name: '', locate_type: 'id', locate_value: '' }
		: { visible: true, mode: 'edit', id: row.id, name: row.name, locate_type: row.locate_type || 'id', locate_value: row.locate_value || '' };
}

async function submitElement() {
	await elementFormRef.value?.validate();
	elementSaving.value = true;
	try {
		if (elementForm.value.mode === 'add') {
			await api.pageElementAdd({ page_id: elementDlg.value.pageId, name: elementForm.value.name, locate_type: elementForm.value.locate_type, locate_value: elementForm.value.locate_value });
			ElMessage.success('已新增');
		} else {
			await api.pageElementUpdate({ id: elementForm.value.id, name: elementForm.value.name, locate_type: elementForm.value.locate_type, locate_value: elementForm.value.locate_value });
			ElMessage.success('已保存');
		}
		elementForm.value.visible = false;
		await loadElements();
	} finally { elementSaving.value = false; }
}

async function deleteElement(row: any) {
	await api.pageElementDelete({ id: row.id });
	ElMessage.success('已删除');
	await loadElements();
}

// ── 拖拽排序（元素） ──────────────────────────────────────────────────
let elementDragOldIndex: number | undefined;
let elementDragRow: any;

function onElementDragStart(e: DragEvent, row: any, index: number) {
	elementDragOldIndex = index; elementDragRow = row;
	e.dataTransfer!.effectAllowed = 'move';
	(e.target as HTMLElement).classList.add('dragging');
}
function onElementDragOver(e: DragEvent) { e.preventDefault(); }
function onElementDragEnd(e: DragEvent) { (e.target as HTMLElement).classList.remove('dragging'); }
async function onElementDrop(e: DragEvent, newIndex: number) {
	e.preventDefault();
	(e.target as HTMLElement).classList.remove('dragging');
	if (elementDragOldIndex === undefined || !elementDragRow) return;
	const list = [...elementRows.value];
	list.splice(elementDragOldIndex, 1);
	list.splice(newIndex, 0, elementDragRow);
	elementLoading.value = true;
	try {
		await api.pageElementSort({ id_list: list.map((r) => r.id) });
		await loadElements();
	} finally { elementLoading.value = false; }
}

// ── 导入元素 ──────────────────────────────────────────────────────────
const importDlg = ref({ visible: false });
const importJsonText = ref('');
const importSubmitting = ref(false);
const importFileRef = ref<HTMLInputElement | null>(null);

function downloadElementTemplate() {
	const sample = [
		{ name: '示例按钮', locate_type: 'id', locate_value: 'com.example:id/login_btn' },
		{ name: '示例输入', locate_type: 'xpath', locate_value: '//android.widget.EditText[1]' },
	];
	const blob = new Blob([JSON.stringify(sample, null, 2)], { type: 'application/json;charset=utf-8' });
	const a = document.createElement('a');
	a.href = URL.createObjectURL(blob);
	a.download = 'app_ui_elements_template.json';
	a.click();
	URL.revokeObjectURL(a.href);
}

function triggerImportFile() { importFileRef.value?.click(); }
function onImportFile(ev: Event) {
	const file = (ev.target as HTMLInputElement).files?.[0];
	if (!file) return;
	const reader = new FileReader();
	reader.onload = () => { importJsonText.value = String(reader.result || ''); };
	reader.readAsText(file, 'UTF-8');
	(ev.target as HTMLInputElement).value = '';
}

async function submitElementImport() {
	if (!elementDlg.value.pageId) return;
	let arr: any[];
	try { arr = JSON.parse(importJsonText.value || '[]'); } catch { ElMessage.error('JSON 格式不正确'); return; }
	if (!Array.isArray(arr) || arr.length === 0) { ElMessage.warning('请填写至少一条元素'); return; }
	const elements = arr.map((x) => ({
		name: String(x.name || '').trim(),
		locate_type: String(x.locate_type || 'id').trim() || 'id',
		locate_value: String(x.locate_value || '').trim(),
	}));
	if (elements.some((e) => !e.name || !e.locate_value)) { ElMessage.warning('每条需包含 name 与 locate_value'); return; }
	importSubmitting.value = true;
	try {
		const res: any = await api.pageElementImport({ page_id: elementDlg.value.pageId, elements });
		ElMessage.success(res?.message || '导入完成');
		importDlg.value.visible = false;
		importJsonText.value = '';
		await loadElements();
	} finally { importSubmitting.value = false; }
}

// ── 计算高度 ──────────────────────────────────────────────────────────
const treeScrollHeight = computed(() => {
	const h = typeof window !== 'undefined' ? window.innerHeight : 800;
	return `${Math.max(300, h - 260)}px`;
});
const tableHeight = computed(() => {
	const h = typeof window !== 'undefined' ? window.innerHeight : 800;
	return `${Math.max(300, h - 240)}px`;
});

onMounted(() => { loadMenuTree(); });
</script>

<style scoped lang="scss">
.apm-layout {
	display: flex;
	gap: 0;
	height: calc(100vh - 160px);
	min-height: 480px;
	background: var(--el-bg-color-page);
}

/* ── 左侧侧边栏 ── */
.apm-sidebar {
	width: 240px;
	flex-shrink: 0;
	display: flex;
	flex-direction: column;
	background: var(--el-bg-color);
	border-right: 1px solid var(--el-border-color-lighter);
	padding: 12px 10px 10px;
	gap: 8px;
}

.sidebar-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding-bottom: 8px;
	border-bottom: 1px solid var(--el-border-color-lighter);
}

.sidebar-title {
	display: inline-flex;
	align-items: center;
	gap: 6px;
	font-weight: 600;
	font-size: 14px;
	color: var(--el-text-color-primary);
}

.sidebar-title-icon {
	color: var(--el-color-primary);
	font-size: 16px;
}

.sidebar-actions {
	display: flex;
	gap: 4px;
}

.sidebar-filter {
	flex-shrink: 0;
}

.sidebar-tree-wrap {
	flex: 1;
}

.sidebar-tip {
	display: flex;
	align-items: flex-start;
	gap: 4px;
	font-size: 11px;
	color: var(--el-text-color-placeholder);
	line-height: 1.5;
	padding-top: 6px;
	border-top: 1px solid var(--el-border-color-lighter);
}

/* 树节点 */
.tree-node {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: space-between;
	min-width: 0;
	padding-right: 2px;
}

.tree-node-label {
	display: inline-flex;
	align-items: center;
	gap: 5px;
	min-width: 0;
	overflow: hidden;
}

.tree-node-name {
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.tree-node-ops {
	flex-shrink: 0;
	opacity: 0;
	transition: opacity 0.15s;
}

.el-tree-node:hover .tree-node-ops,
.el-tree-node.is-current .tree-node-ops {
	opacity: 1;
}

.tree-more {
	cursor: pointer;
	color: var(--el-text-color-secondary);
	font-size: 16px;
	padding: 2px;
	border-radius: 3px;
	&:hover { color: var(--el-color-primary); background: var(--el-fill-color); }
}

.tree-ico {
	font-size: 14px;
	flex-shrink: 0;
	&.root { color: var(--el-color-primary); }
	&.folder { color: var(--el-color-warning); }
	&.leaf { color: var(--el-text-color-secondary); }
}

:deep(.danger-item) {
	color: var(--el-color-danger) !important;
}

/* ── 右侧内容区 ── */
.apm-content {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	padding: 12px 16px;
	gap: 10px;
	overflow: hidden;
}

.content-toolbar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 8px 12px;
	background: var(--el-bg-color);
	border: 1px solid var(--el-border-color-lighter);
	border-radius: 6px;
	flex-shrink: 0;
}

.toolbar-left {
	display: inline-flex;
	align-items: center;
	gap: 8px;
	min-width: 0;
}

.toolbar-module-icon {
	color: var(--el-color-warning);
	font-size: 16px;
}

.toolbar-module-name {
	font-weight: 600;
	font-size: 14px;
	color: var(--el-text-color-primary);
}

.toolbar-module-id {
	flex-shrink: 0;
}

.toolbar-placeholder {
	font-size: 13px;
	color: var(--el-text-color-placeholder);
}

.content-empty {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	background: var(--el-bg-color);
	border: 1px solid var(--el-border-color-lighter);
	border-radius: 6px;
}

.page-table {
	border-radius: 6px;
	flex: 1;
}

.help-ico {
	color: var(--el-color-primary);
	cursor: help;
}

.drag-btn {
	cursor: grab;
	&:active { cursor: grabbing; }
}

:deep(.dragging) { opacity: 0.5; }

.page-pager {
	display: flex;
	justify-content: flex-end;
	flex-shrink: 0;
}

/* 元素弹窗 */
.element-toolbar {
	margin-bottom: 12px;
	display: flex;
	flex-wrap: wrap;
	gap: 8px;
}

.import-textarea {
	margin-top: 10px;
}

.hidden-file {
	display: none;
}
</style>
