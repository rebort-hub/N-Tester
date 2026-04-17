<template>
	<div class="manage-panel">
		<!-- 顶部工具栏 -->
		<div class="manage-toolbar">
			<div class="toolbar-row">
				<div class="toolbar-doc">
					<el-select v-model="doc_source_type" style="width:110px;flex-shrink:0">
						<el-option label="Swagger" value="swagger" />
						<el-option label="Apifox" value="apifox" />
					</el-select>
					<el-input v-model="doc_source_url" placeholder="输入文档 URL" clearable style="flex:1;min-width:180px" />
					<el-input
						v-if="doc_source_type === 'apifox'"
						v-model="doc_source_cookies"
						placeholder="Apifox Cookies（必填）"
						clearable
						style="flex:1;min-width:160px"
					/>
					<el-button type="primary" size="small" :loading="pulling" @click="pullDoc" style="flex-shrink:0">拉取并解析</el-button>
				</div>
				<div class="toolbar-tools">
					<el-popover placement="bottom" :width="900" trigger="click">
						<template #reference>
							<el-button size="small" type="info">直连数据库</el-button>
						</template>
						<ApiDbPopover />
					</el-popover>
					<el-popover placement="bottom" :width="800" trigger="click">
						<template #reference>
							<el-button size="small" type="primary">全局变量</el-button>
						</template>
						<ApiVarPopover />
					</el-popover>
				</div>
			</div>
		</div>

		<!-- 主体：左侧接口树 + 右侧详情 -->
		<div class="manage-body">
			<!-- 左侧接口树 -->
			<div class="tree-panel">
				<div class="tree-actions">
					<el-input v-model="treeFilter" placeholder="搜索接口" clearable size="small" style="flex:1" />
					<el-dropdown @command="handleAddCommand" style="margin-left:6px">
						<el-button type="primary" size="small">添加<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
						<template #dropdown>
							<el-dropdown-menu>
								<el-dropdown-item command="add_folder">添加目录</el-dropdown-item>
								<el-dropdown-item command="add_api">添加接口</el-dropdown-item>
							</el-dropdown-menu>
						</template>
					</el-dropdown>
				</div>
				<el-tree
					ref="treeRef"
					:data="treeData"
					:props="{ children: 'children', label: 'name' }"
					node-key="id"
					:filter-node-method="filterNode"
					class="api-tree"
					@node-click="onNodeClick"
				>
					<template #default="{ data }">
						<div class="tree-node">
							<div class="node-left">
								<el-icon v-if="data.type===1" class="icon-folder"><FolderOpened /></el-icon>
								<el-icon v-else-if="data.type===3" class="icon-case"><Link /></el-icon>
								<span v-if="data.type===2||data.type===3" class="method-badge" :style="{background: methodColor(data.method)}">{{ methodLabel(data.method) }}</span>
								<span class="node-name">{{ data.name }}</span>
							</div>
							<el-dropdown trigger="click" @command="(cmd) => handleNodeCommand(cmd, data)" @click.stop>
								<el-icon class="node-more"><MoreFilled /></el-icon>
								<template #dropdown>
									<el-dropdown-menu>
										<el-dropdown-item v-if="data.type===1" command="add_folder">添加子目录</el-dropdown-item>
										<el-dropdown-item v-if="data.type===1" command="add_api">添加接口</el-dropdown-item>
										<el-dropdown-item v-if="data.type===2" command="copy">复制接口</el-dropdown-item>
										<el-dropdown-item command="rename">重命名</el-dropdown-item>
										<el-dropdown-item command="delete" divided>删除</el-dropdown-item>
									</el-dropdown-menu>
								</template>
							</el-dropdown>
						</div>
					</template>
				</el-tree>
			</div>

			<!-- 右侧接口详情 -->
			<div class="detail-panel">
				<div v-if="!apiTabs.length" class="detail-empty">
					<el-icon style="font-size:40px;color:#dcdfe6"><Document /></el-icon>
					<p>点击左侧接口查看详情</p>
				</div>
				<div v-else class="detail-tabs-wrap">
					<!-- 接口多 Tab（可关闭） -->
					<el-tabs v-model="activeTab" type="card" closable class="api-outer-tabs" @tab-remove="closeTab">
						<el-tab-pane v-for="tab in apiTabs" :key="tab.name" :label="tab.title" :name="tab.name">
							<!-- 接口内部功能 Tab：调试 / 接口文档 / 调试记录 / Mock -->
							<div class="inner-tab-container">
								<el-tabs v-model="tab.innerTab" class="inner-tabs">
									<el-tab-pane label="调试" name="debug" />
									<el-tab-pane label="接口文档" name="doc" />
									<el-tab-pane label="调试记录" name="history" />
									<el-tab-pane label="Mock" name="mock" />
								</el-tabs>
								<div class="inner-tab-content">
									<!-- 调试：始终渲染，用 v-show 控制显隐 -->
									<ApiDetail
										v-show="tab.innerTab==='debug'"
										:api-data="tab.data"
										:env-id="envId"
										:env_list="envList"
										:tree_list="treeData"
										:params_list="paramsList"
										:service-id="serviceId"
										:embedded="true"
										@caseSaved="loadTree"
										@apiSaved="loadTree"
									/>
									<!-- 接口文档 -->
									<div v-if="tab.innerTab==='doc'" class="inner-panel-wrap">
										<ApiDocPanel :api-data="tab.data" />
									</div>
									<!-- 调试记录 -->
									<div v-if="tab.innerTab==='history'" class="inner-panel-wrap">
										<ApiHistoryPanel :api-data="tab.data" />
									</div>
									<!-- Mock -->
									<div v-if="tab.innerTab==='mock'" class="inner-panel-wrap">
										<ApiMockPanel :service-id="serviceId" :api-data="tab.data" />
									</div>
								</div>
							</div>
						</el-tab-pane>
					</el-tabs>
				</div>
			</div>
		</div>

		<!-- 新增目录/接口弹窗 -->
		<el-dialog v-model="menuDialogVisible" :title="menuDialogTitle" width="400px" destroy-on-close>
			<el-form label-width="80px">
				<el-form-item label="名称" required>
					<el-input v-model="menuForm.name" placeholder="请输入名称" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="menuDialogVisible=false">取消</el-button>
				<el-button type="primary" @click="confirmMenu">确定</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { ArrowDown, FolderOpened, Link, MoreFilled, Document } from '@element-plus/icons-vue';
import ApiDetail from './api_detail.vue';
import ApiDbPopover from './components/ApiDbPopover.vue';
import ApiVarPopover from './components/ApiVarPopover.vue';
import ApiDocPanel from './components/ApiDocPanel.vue';
import ApiHistoryPanel from './components/ApiHistoryPanel.vue';
import ApiMockPanel from './components/ApiMockPanel.vue';
import {
	api_tree, api_info, add_menu, del_menu, edit_menu, copy_menu,
	pull_api_doc, params_select,
} from '/@/api/v1/api_automation';

const props = defineProps<{
	serviceId: number;
	envId: number | null;
	envList: any[];
}>();

// ---- 接口树 ----
const treeRef = ref<any>(null);
const treeData = ref<any[]>([]);
const treeFilter = ref('');
const paramsList = ref<any[]>([]);

watch(treeFilter, (v) => treeRef.value?.filter(v));
const filterNode = (val: string, data: any) => !val || data.name?.includes(val);

const loadTree = async () => {
	try {
		const r: any = await api_tree({ search: { api_service_id: props.serviceId } });
		treeData.value = r?.data || [];
	} catch { treeData.value = []; }
};

const loadParams = async () => {
	try {
		const r: any = await params_select({});
		paramsList.value = r?.data || [];
	} catch { paramsList.value = []; }
};

// ---- 接口 Tab ----
const apiTabs = ref<any[]>([]);
const activeTab = ref('');

const onNodeClick = async (data: any) => {
	if (data.type !== 2 && data.type !== 3) return;
	const existing = apiTabs.value.find((t) => t.id === data.id);
	if (existing) { activeTab.value = existing.name; return; }
	try {
		const r: any = await api_info(data);
		data.api_info = r.data;
	} catch {}
	const name = `api-${data.id}`;
	apiTabs.value.push({ id: data.id, name, title: data.name, data, innerTab: 'debug' });
	activeTab.value = name;
};

const closeTab = (name: string) => {
	const idx = apiTabs.value.findIndex((t) => t.name === name);
	apiTabs.value.splice(idx, 1);
	if (activeTab.value === name) {
		activeTab.value = apiTabs.value[Math.max(0, idx - 1)]?.name || '';
	}
};

// ---- 方法颜色 ----
const METHOD_MAP: Record<number, { label: string; color: string }> = {
	1: { label: 'GET', color: '#67C23A' }, 2: { label: 'POST', color: '#409EFF' },
	3: { label: 'PUT', color: '#E6A23C' }, 4: { label: 'DELETE', color: '#F56C6C' },
	5: { label: 'PATCH', color: '#8E44AD' }, 6: { label: 'OPTIONS', color: '#909399' },
};
const methodLabel = (m: number) => METHOD_MAP[m]?.label || 'GET';
const methodColor = (m: number) => METHOD_MAP[m]?.color || '#409EFF';

// ---- 拉取文档 ----
const doc_source_type = ref('swagger');
const doc_source_url = ref('');
const doc_source_cookies = ref('');
const pulling = ref(false);

const pullDoc = async () => {
	if (!doc_source_url.value.trim()) { ElMessage.warning('请输入文档地址'); return; }
	if (doc_source_type.value === 'apifox' && !doc_source_cookies.value.trim()) {
		ElMessage.warning('Apifox 需要填写 Cookies'); return;
	}
	pulling.value = true;
	try {
		await pull_api_doc({
			api_service_id: props.serviceId,
			source_type: doc_source_type.value,
			doc_url: doc_source_url.value.trim(),
			...(doc_source_type.value === 'apifox' ? { cookies: doc_source_cookies.value.trim() } : {}),
		});
		ElMessage.success('拉取成功');
		await loadTree();
	} catch (e: any) { ElMessage.error(e?.message || '拉取失败'); }
	finally { pulling.value = false; }
};

// ---- 菜单操作 ----
const menuDialogVisible = ref(false);
const menuDialogTitle = ref('');
const menuForm = ref({ name: '', type: 1, pid: 0, editId: 0, mode: 'add' as 'add' | 'edit' });

const handleAddCommand = (cmd: string) => {
	menuForm.value = { name: '', type: cmd === 'add_folder' ? 1 : 2, pid: 0, editId: 0, mode: 'add' };
	menuDialogTitle.value = cmd === 'add_folder' ? '添加目录' : '添加接口';
	menuDialogVisible.value = true;
};

const handleNodeCommand = (cmd: string, data: any) => {
	if (cmd === 'add_folder') {
		menuForm.value = { name: '', type: 1, pid: data.id, editId: 0, mode: 'add' };
		menuDialogTitle.value = '添加子目录';
		menuDialogVisible.value = true;
	} else if (cmd === 'add_api') {
		menuForm.value = { name: '', type: 2, pid: data.id, editId: 0, mode: 'add' };
		menuDialogTitle.value = '添加接口';
		menuDialogVisible.value = true;
	} else if (cmd === 'rename') {
		menuForm.value = { name: data.name, type: data.type, pid: data.pid || 0, editId: data.id, mode: 'edit' };
		menuDialogTitle.value = '重命名';
		menuDialogVisible.value = true;
	} else if (cmd === 'copy') {
		copyApi(data);
	} else if (cmd === 'delete') {
		deleteNode(data);
	}
};

const confirmMenu = async () => {
	if (!menuForm.value.name.trim()) { ElMessage.warning('请输入名称'); return; }
	try {
		if (menuForm.value.mode === 'edit') {
			await edit_menu({ id: menuForm.value.editId, name: menuForm.value.name.trim() });
		} else {
			await add_menu({ name: menuForm.value.name.trim(), pid: menuForm.value.pid, type: menuForm.value.type, api_service_id: props.serviceId });
		}
		menuDialogVisible.value = false;
		await loadTree();
	} catch (e: any) { ElMessage.error(e?.message || '操作失败'); }
};

const copyApi = async (data: any) => {
	try {
		await copy_menu({ id: data.id, api_id: data.api_id });
		ElMessage.success('复制成功');
		await loadTree();
	} catch (e: any) { ElMessage.error(e?.message || '复制失败'); }
};

const deleteNode = async (data: any) => {
	try {
		await ElMessageBox.confirm(`确认删除「${data.name}」？`, '提示', { type: 'warning' });
		await del_menu({ id: data.id, type: data.type });
		ElMessage.success('删除成功');
		apiTabs.value = apiTabs.value.filter((t) => t.id !== data.id);
		await loadTree();
	} catch (e: any) {
		if (e === 'cancel' || e === 'close') return;
		ElMessage.error(e?.message || '删除失败');
	}
};

onMounted(() => { loadTree(); loadParams(); });
</script>

<style scoped>
.manage-panel { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.manage-toolbar { padding: 8px 12px; background: var(--el-bg-color); border-bottom: 1px solid var(--el-border-color); flex-shrink: 0; }
.toolbar-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.toolbar-doc { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }
.toolbar-tools { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.manage-body { flex: 1; min-height: 0; display: flex; overflow: hidden; }
.tree-panel { width: 260px; flex-shrink: 0; border-right: 1px solid var(--el-border-color); display: flex; flex-direction: column; overflow: hidden; background: var(--el-bg-color); }
.tree-actions { display: flex; align-items: center; padding: 8px; border-bottom: 1px solid var(--el-border-color); flex-shrink: 0; }
.api-tree { flex: 1; overflow-y: auto; padding: 4px 0; }
.tree-node { display: flex; align-items: center; justify-content: space-between; width: 100%; padding-right: 4px; }
.node-left { display: flex; align-items: center; gap: 4px; min-width: 0; flex: 1; overflow: hidden; }
.node-name { font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.node-more { font-size: 14px; color: var(--el-text-color-placeholder); cursor: pointer; flex-shrink: 0; opacity: 0; }
.tree-node:hover .node-more { opacity: 1; }
.icon-folder { color: #f39c12; font-size: 16px; flex-shrink: 0; }
.icon-case { color: #e6a23c; font-size: 16px; flex-shrink: 0; }
.method-badge { font-size: 10px; font-weight: 700; padding: 0 4px; border-radius: 3px; color: #fff; flex-shrink: 0; line-height: 16px; }
.detail-panel { flex: 1; min-width: 0; display: flex; flex-direction: column; overflow: hidden; height: 100%; }
.detail-empty { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--el-text-color-placeholder); gap: 8px; font-size: 13px; }
.detail-tabs-wrap { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.detail-tabs-wrap > :deep(.el-tabs) { height: 100%; display: flex; flex-direction: column; }
.detail-tabs-wrap > :deep(.el-tabs > .el-tabs__header) { flex-shrink: 0; }
.detail-tabs-wrap > :deep(.el-tabs > .el-tabs__content) { flex: 1; min-height: 0; overflow: hidden; padding: 0; }
.detail-tabs-wrap > :deep(.el-tabs > .el-tabs__content > .el-tab-pane) { height: 100%; overflow: hidden; }
.inner-tab-container { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.inner-tabs { flex-shrink: 0; }
.inner-tabs :deep(.el-tabs__header) { margin: 0; background: var(--el-fill-color-light); border-bottom: 1px solid var(--el-border-color); padding: 0 8px; }
.inner-tabs :deep(.el-tabs__nav-wrap::after) { display: none; }
.inner-tabs :deep(.el-tabs__item) { height: 36px; line-height: 36px; font-size: 12px; color: var(--el-text-color-regular); padding: 0 14px; }
.inner-tabs :deep(.el-tabs__item:hover) { color: #409eff; }
.inner-tabs :deep(.el-tabs__item.is-active) { color: #409eff; font-weight: 600; }
.inner-tabs :deep(.el-tabs__active-bar) { height: 2px; background: #409eff; }
.inner-tabs :deep(.el-tabs__content) { display: none; }
.inner-tab-content { flex: 1; min-height: 0; overflow: hidden; display: flex; flex-direction: column; }
.inner-panel-wrap { flex: 1; min-height: 0; overflow: hidden; height: 100%; }
</style>
