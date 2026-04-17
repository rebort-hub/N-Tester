<template>
	<div>
		<!-- 项目表格页面 -->
		<div v-if="show_type === 'project'">
			<el-card class="box-card">
				<div class="project-topbar">
					<div class="project-topbar-left">
						<el-input 
							v-model="project_searchParams.search.name" 
							placeholder="搜索项目名称" 
							clearable 
							style="width: 300px;"
							@keyup.enter="searchProject"
						>
							<template #append>
								<el-button @click="searchProject">搜索</el-button>
							</template>
						</el-input>
						<el-button @click="resetSearch">重置</el-button>
					</div>
					<div class="project-topbar-right">
						<el-tooltip content="在「项目管理」中创建项目" placement="top">
							<el-button type="info" plain size="small">项目来源：全局项目管理</el-button>
						</el-tooltip>
					</div>
				</div>
			</el-card>

			<el-card class="box-card mt-10px">
				<el-table :data="project_list" stripe>
					<el-table-column prop="id" label="ID" width="80" />
					<el-table-column prop="name" label="项目名称" />
					<el-table-column prop="description" label="描述" />
					<el-table-column label="状态" width="100">
						<template #default="{ row }">
							<el-tag :type="row.status==='active'?'success':row.status==='paused'?'warning':'info'" size="small">
								{{ row.status==='active'?'活跃':row.status==='paused'?'暂停':row.status==='completed'?'已完成':'已归档' }}
							</el-tag>
						</template>
					</el-table-column>
					<el-table-column label="服务" width="200">
						<template #default="{ row }">
							<el-dropdown @command="(command) => handleServiceCommand(command, row)">
								<el-button type="primary" size="small">
									服务管理 <el-icon class="el-icon--right"><MoreFilled /></el-icon>
								</el-button>
								<template #dropdown>
									<el-dropdown-menu>
										<el-dropdown-item command="add_service" :icon="Connection">新增服务</el-dropdown-item>
										<el-dropdown-item command="service_detail" :icon="View">服务详情</el-dropdown-item>
										<el-dropdown-item command="scene_manage" :icon="Setting">场景管理</el-dropdown-item>
										<el-dropdown-item command="result_list" :icon="List">结果列表</el-dropdown-item>
									</el-dropdown-menu>
								</template>
							</el-dropdown>
						</template>
					</el-table-column>
				</el-table>
				
				<div class="pagination-wrapper">
					<el-pagination
						v-model:current-page="project_searchParams.currentPage"
						v-model:page-size="project_searchParams.pageSize"
						:page-sizes="[10, 20, 50, 100]"
						:total="project_total"
						layout="total, sizes, prev, pager, next, jumper"
						@size-change="getProjectList"
						@current-change="getProjectList"
					/>
				</div>
			</el-card>
		</div>


		<div v-else-if="show_type === 'service_detail'" class="service-detail-page">
			<el-card class="box-card service-toolbar-card">
				<div class="service-topbar">
					<div class="service-topbar-left">
						<span class="service-title">{{ current_service?.name || current_project?.name }}</span>
					</div>
					<div class="service-topbar-right">
						<div class="doc-import-row">
							<el-select v-model="doc_source_type" placeholder="文档来源" class="doc-source-select">
								<el-option label="Swagger" value="swagger" />
								<el-option label="Apifox" value="apifox" />
							</el-select>
							<el-input
								v-model="doc_source_url"
								:placeholder="doc_source_type === 'apifox' ? '输入 Apifox 文档URL（必填）' : '输入 Swagger 文档URL（JSON）'"
								clearable
								class="doc-url-input"
							/>
							<el-input
								v-if="doc_source_type === 'apifox'"
								v-model="doc_source_cookies"
								placeholder="Apifox Cookies（必填）"
								clearable
								class="doc-cookie-input"
							/>
							<el-button type="primary" :loading="pulling_doc" size="small" @click="handlePullApiDoc">
								拉取并解析
							</el-button>
						</div>
						<div class="service-tools-row">
							<el-select v-model="env_id" placeholder="选择环境" style="width: 150px;">
								<el-option v-for="env in env_list" :key="env.id" :label="env.name" :value="env.id" />
							</el-select>
							<el-popover placement="bottom" :width="900" trigger="click">
								<template #reference>
									<el-button type="info" size="small" style="margin-left: 8px">直连数据库</el-button>
								</template>
								<ApiDbPopover />
							</el-popover>
							<el-popover placement="bottom" :width="800" trigger="click">
								<template #reference>
									<el-button type="primary" size="small" style="margin-left: 8px">全局变量</el-button>
								</template>
								<ApiVarPopover />
							</el-popover>
						</div>
					</div>
				</div>
			</el-card>

			<div class="service-main">
				<div class="service-left">
					<el-card class="box-card api-tree-card">
						<div class="tree-container">
							<div class="tree-title">
								<span class="font-bold">接口树</span>
							</div>
							<div class="tree-service-bar">
								<el-select
									v-model="selected_service_id"
									placeholder="选择服务"
									style="flex: 1; margin-right: 10px;"
									@change="onServiceChange"
								>
									<el-option v-for="svc in service_list" :key="svc.id" :label="svc.name" :value="svc.id" />
								</el-select>
								<el-button type="primary" size="small" @click="openAddService(current_project)">新增服务</el-button>
								<el-button type="danger" size="small" @click="deleteCurrentService" style="margin-left: 8px">删除服务</el-button>
							</div>
							<div class="tree-actions-bar">
								<el-input v-model="api_tree_filter" placeholder="搜索接口" clearable style="flex: 1; margin-right: 10px;" />
								<el-dropdown @command="handleAddApiCommand">
									<el-button type="primary" size="small">
										添加 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
									</el-button>
									<template #dropdown>
										<el-dropdown-menu>
											<el-dropdown-item command="add_folder">添加目录</el-dropdown-item>
											<el-dropdown-item command="add_api">添加接口</el-dropdown-item>
										</el-dropdown-menu>
									</template>
								</el-dropdown>
							</div>
							<div class="tree-content">
								<el-tree
									ref="api_tree_ref"
									:data="api_tree_data"
									:props="{ children: 'children', label: 'name' }"
									node-key="id"
									:filter-node-method="filterNode"
									@node-click="onTreeNodeClick"
								>
									<template #default="{ data }">
										<div class="custom-tree-node">
											<div class="node-content">
												<el-icon v-if="data.type === 1" class="node-icon icon-folder">
													<FolderOpened />
												</el-icon>
												<el-icon v-else-if="data.type === 3" class="node-icon icon-case">
													<Link />
												</el-icon>
												<span
													v-if="data.type === 2 || data.type === 3"
													class="method-badge"
													:style="{ backgroundColor: getMethodColor(data.method) }"
												>
													{{ getMethodLabel(data.method) }}
												</span>
												<span class="node-title">{{ data.name }}</span>
											</div>
											<div class="node-actions" v-if="data.type === 1 || data.type === 2 || data.type === 3">
												<el-dropdown @command="(command) => handleNodeCommand(command, data)" trigger="click">
													<el-button type="text" size="small">
														<el-icon><MoreFilled /></el-icon>
													</el-button>
													<template #dropdown>
														<el-dropdown-menu>
															<el-dropdown-item v-if="data.type === 1" command="add_folder">添加子目录</el-dropdown-item>
															<el-dropdown-item v-if="data.type === 1" command="add_api">添加接口</el-dropdown-item>
															<el-dropdown-item v-if="data.type === 2" command="copy">复制接口</el-dropdown-item>
															<el-dropdown-item command="edit">编辑</el-dropdown-item>
															<el-dropdown-item command="delete" divided>删除</el-dropdown-item>
														</el-dropdown-menu>
													</template>
												</el-dropdown>
											</div>
										</div>
									</template>
								</el-tree>
							</div>
						</div>
					</el-card>
				</div>
				
				<div class="service-right">
					<el-card class="box-card api-detail-card">
						<template #header>
							<span class="font-bold">接口详情</span>
						</template>
						<div v-if="api_tabs.length === 0" class="api-empty">
							<span>请选择接口查看详情</span>
						</div>
						<div v-else class="api-detail-content">
							<el-tabs v-model="api_active_tab" type="card" closable @tab-remove="closeApiTab">
								<el-tab-pane v-for="tab in api_tabs" :key="tab.name" :label="tab.title" :name="tab.name">
									<ApiDetail 
										:api-data="tab.data" 
										:env-id="env_id"
										:env_list="env_list"
										:tree_list="api_tree_data"
										:params_list="params_list"
										:local_db_list="local_db_list"
										:service-id="current_service?.id"
										@caseSaved="loadServiceDetail"
										@apiSaved="loadServiceDetail"
									/>
								</el-tab-pane>
							</el-tabs>
						</div>
					</el-card>
				</div>
			</div>
		</div>


		<div v-else-if="show_type === 'scene_manage'">
			<el-card class="box-card">
				<div class="scene-topbar">
					<div class="scene-topbar-left">
						<el-button :icon="Back" @click="goBack">返回项目</el-button>
						<span class="scene-title">{{ current_project?.name }} - 场景管理</span>
					</div>
				</div>
			</el-card>
			<ApiScript />
		</div>

	
		<div v-else-if="show_type === 'result_list'">
			<el-card class="box-card">
				<div class="result-topbar">
					<div class="result-topbar-left">
						<el-button :icon="Back" @click="goBack">返回项目</el-button>
						<span class="result-title">测试结果列表</span>
					</div>
				</div>
			</el-card>
			<ApiResultList />
		</div>

		<!-- 对话框 -->
		<el-dialog v-model="envManageDialogVisible" title="环境管理" width="900px" destroy-on-close>
			<div style="display: flex; justify-content: flex-end; margin-bottom: 12px;">
				<el-button type="primary" @click="newEnv">新增环境</el-button>
			</div>
			<el-table :data="env_list" stripe>
				<el-table-column prop="id" label="ID" width="80" />
				<el-table-column prop="name" label="环境名称" min-width="200" />
				<el-table-column label="变量数量" width="120">
					<template #default="{ row }">
						{{ Array.isArray(row.variable) ? row.variable.length : 0 }}
					</template>
				</el-table-column>
				<el-table-column label="操作" width="220">
					<template #default="{ row }">
						<el-button type="primary" size="small" @click="editEnv(row)">编辑</el-button>
						<el-button type="danger" size="small" @click="removeEnv(row)">删除</el-button>
					</template>
				</el-table-column>
			</el-table>
			<template #footer>
				<el-button @click="envManageDialogVisible = false">关闭</el-button>
			</template>
		</el-dialog>

		<el-dialog v-model="envEditDialogVisible" :title="envForm.id ? '编辑环境' : '新增环境'" width="900px" destroy-on-close append-to-body>
			<el-form ref="envFormRef" :model="envForm" label-width="90px">
				<el-form-item label="环境名称" required>
					<el-input v-model="envForm.name" placeholder="请输入环境名称" />
				</el-form-item>
				<el-form-item label="配置项">
					<div style="width: 100%;">
						<div style="max-height: 260px; overflow-y: auto; border: 1px solid #e4e7ed; padding: 10px; border-radius: 6px;">
							<div v-for="(c, idx) in envForm.config" :key="idx" style="display:flex; gap:10px; align-items:center; margin-bottom: 8px;">
								<el-input v-model="c.name" placeholder="配置项名（如 {{base_url}}）" style="width: 260px" />
								<el-input v-model="c.value" placeholder="配置项值" style="flex: 1" />
								<el-button type="danger" size="small" @click="removeEnvConfigRow(idx)">删除</el-button>
							</div>
							<el-empty v-if="!envForm.config || envForm.config.length === 0" description="暂无配置项，点击下方添加" />
						</div>
						<el-button type="primary" plain size="small" style="margin-top: 10px" @click="addEnvConfigRow">
							添加配置项
						</el-button>
					</div>
				</el-form-item>
				<el-form-item label="环境变量">
					<div style="width: 100%;">
						<div style="max-height: 320px; overflow-y: auto; border: 1px solid #e4e7ed; padding: 10px; border-radius: 6px;">
							<div v-for="(v, idx) in envForm.variable" :key="idx" style="display:flex; gap:10px; align-items:center; margin-bottom: 8px;">
								<el-input v-model="v.name" placeholder="变量名（如 {{token}}）" style="width: 260px" />
								<el-input v-model="v.value" placeholder="变量值" style="flex: 1" />
								<el-button type="danger" size="small" @click="removeEnvVarRow(idx)">删除</el-button>
							</div>
							<el-empty v-if="!envForm.variable || envForm.variable.length === 0" description="暂无变量，点击下方添加" />
						</div>
						<el-button type="primary" plain size="small" style="margin-top: 10px" @click="addEnvVarRow">
							添加变量
						</el-button>
					</div>
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="envEditDialogVisible = false">取消</el-button>
				<el-button type="primary" :loading="envSaving" @click="saveEnvForm">保存</el-button>
			</template>
		</el-dialog>

		<!-- 新增服务 -->
		<el-dialog v-model="addServiceDialogVisible" title="新增服务" width="520px" destroy-on-close>
			<el-form :model="service_form" label-width="90px">
				<el-form-item label="所属项目">
					<el-input :model-value="current_project?.name || '-'" disabled />
				</el-form-item>
				<el-form-item label="服务名称" required>
					<el-input v-model="service_form.name" placeholder="请输入服务名称" />
				</el-form-item>
				<el-form-item label="描述">
					<el-input v-model="service_form.description" type="textarea" placeholder="请输入描述（可选）" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="addServiceDialogVisible = false">取消</el-button>
				<el-button type="primary" :loading="addingService" @click="confirmAddService">确定</el-button>
			</template>
		</el-dialog>

		<!-- 菜单对话框 -->
		<el-dialog v-model="menuDialogRef" :title="dialogTitle" width="500px" destroy-on-close>
			<el-form :model="menu_form" label-width="90px">
				<el-form-item label="名称" required><el-input v-model="menu_form.name" /></el-form-item>
				<el-form-item label="类型">
					<el-select v-model="menu_form.type" disabled>
						<el-option label="目录" :value="1" />
						<el-option label="接口" :value="2" />
					</el-select>
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="menuDialogRef = false">取消</el-button>
				<el-button type="primary" @click="confirmMenu">确定</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { ElMessage, ElMessageBox, ElTree } from 'element-plus';
import { Back, MoreFilled, View, Setting, List, Document, ArrowDown, Folder, Link, Connection, FolderOpened, Switch } from '@element-plus/icons-vue';
import ApiDetail from './api_detail.vue';
import ApiScript from './api_script.vue';
import ApiResultList from './api_result_list.vue';
import ApiCodePopover from './components/ApiCodePopover.vue';
import ApiFunctionPopover from './components/ApiFunctionPopover.vue';
import ApiDbPopover from './components/ApiDbPopover.vue';
import ApiParamsPopover from './components/ApiParamsPopover.vue';
import ApiVarPopover from './components/ApiVarPopover.vue';
import { useProjectApi } from '/@/api/v1/projects/project';
import {
	add_api_service,
	add_env,
	add_menu,
	api_env,
	api_info,
	api_send,
	api_service,
	api_tree,
	api_tree_list,
	copy_menu,
	del_api_service,
	del_env,
	del_menu,
	env_info,
	params_select,
	save_api,
	save_env,
	api_db_list,
	edit_menu,
	pull_api_doc,
} from '/@/api/v1/api_automation';

type ShowType = 'project' | 'service_detail' | 'scene_manage' | 'result_list';

const props = defineProps<{ initialServiceId?: number }>();
const emit = defineEmits<{ (e: 'service-changed', serviceId: number): void }>();

const show_type = ref<ShowType>('project');

const { getList: getGlobalProjectList } = useProjectApi();

// -------------------- 项目表格 --------------------
const project_list = ref<any[]>([]);
const project_total = ref(0);
const project_searchParams = ref({ 
	currentPage: 1, 
	pageSize: 10, 
	search: { name: '' } 
});
const current_project = ref<any>(null);
const current_service = ref<any>(null);

const getProjectList = async () => {
	show_type.value = 'project';
	try {
		const res: any = await getGlobalProjectList({
			page: project_searchParams.value.currentPage,
			page_size: project_searchParams.value.pageSize,
			name: project_searchParams.value.search.name || undefined,
		});
		const raw = res?.data;
		project_list.value = Array.isArray(raw?.items) ? raw.items : (Array.isArray(raw?.content) ? raw.content : []);
		project_total.value = raw?.total || 0;
	} catch {
		project_list.value = [];
		project_total.value = 0;
	}
};

const searchProject = () => {
	project_searchParams.value.currentPage = 1;
	getProjectList();
};

const resetSearch = () => {
	project_searchParams.value.search.name = '';
	project_searchParams.value.currentPage = 1;
	getProjectList();
};

// -------------------- 服务操作 --------------------
const service_list = ref<any[]>([]);

const getServiceList = async (projectId: number) => {
	// 新架构 api_service 入参为 { search: { api_project_id } }
	const res: any = await api_service({
		page: 1,
		pageSize: 100,
		search: { api_project_id: projectId }
	});
	return res.data?.content || [];
};

const loadServiceOptionsForProject = async (projectId: number) => {
	try {
		const services = await getServiceList(projectId);
		service_list.value = services;
		return services;
	} catch (e) {
		console.error('加载服务下拉失败:', e);
		service_list.value = [];
		return [];
	}
};

const handleServiceCommand = async (command: string, project: any) => {
	current_project.value = project;
	current_service.value = null;

	if (command === 'add_service') {
		openAddService(project);
		return;
	}
	
	// 获取项目的第一个服务作为默认服务
	const services = await loadServiceOptionsForProject(project.id);
	if (services.length > 0) {
		current_service.value = services[0];
	}
	
	switch (command) {
		case 'service_detail':
			if (!current_service.value) {
				ElMessage.warning('该项目下暂无服务，请先新增服务');
				return;
			}
			await enterServiceDetail(project, current_service.value);
			break;
		case 'scene_manage':
			if (!current_service.value) {
				ElMessage.warning('该项目下暂无服务，请先新增服务');
				return;
			}
			await enterSceneManage(project, current_service.value);
			break;
		case 'result_list':
			enterResultList();
			break;
	}
};

// -------------------- 新增服务 --------------------
const addServiceDialogVisible = ref(false);
const service_form = ref<{ name: string; description: string }>({ name: '', description: '' });
const addingService = ref(false);

const openAddService = (project: any) => {
	current_project.value = project;
	service_form.value = { name: '', description: '' };
	addServiceDialogVisible.value = true;
};

const confirmAddService = async () => {
	if (!current_project.value?.id) {
		ElMessage.error('未选择项目');
		return;
	}
	if (!service_form.value.name?.trim()) {
		ElMessage.warning('请输入服务名称');
		return;
	}
	addingService.value = true;
	try {
		const res: any = await add_api_service({
			name: service_form.value.name.trim(),
			description: service_form.value.description?.trim?.() || '',
			api_project_id: Number(current_project.value.id),
		});
		if (res?.code === 200) {
			ElMessage.success('新增服务成功');
			addServiceDialogVisible.value = false;
			// 立刻刷新一次该项目的服务列表，便于后续进入详情
			try {
				service_list.value = await getServiceList(Number(current_project.value.id));
			} catch {
				// ignore
			}
		}
	} catch (e) {
		console.error('新增服务失败:', e);
		ElMessage.error('新增服务失败');
	} finally {
		addingService.value = false;
	}
};

const enterServiceDetail = async (project: any, service: any) => {
	current_project.value = project;
	current_service.value = service;
	selected_service_id.value = service?.id != null ? Number(service.id) : null;
	show_type.value = 'service_detail';
	// 切换项目/服务时重置右侧状态，避免沿用上一次详情
	api_tabs.value = [];
	api_active_tab.value = '';
	api_tree_data.value = [];
	api_tree_filter.value = '';
	await loadServiceOptionsForProject(Number(project.id));
	await loadServiceDetail();
	// 通知父组件服务已切换
	if (service?.id != null) emit('service-changed', Number(service.id));
};

const enterSceneManage = async (project: any, service: any) => {
	current_project.value = project;
	current_service.value = service;
	show_type.value = 'scene_manage';
	await loadSceneManage();
};

const enterResultList = () => {
	show_type.value = 'result_list';
	loadResultList();
};

// -------------------- 服务详情页面 --------------------
const api_tree_data = ref<any[]>([]);
const api_tree_ref = ref<InstanceType<typeof ElTree>>();
const api_tree_filter = ref('');
const api_tabs = ref<any[]>([]);
const api_active_tab = ref('');
const env_list = ref<any[]>([]);
const env_id = ref<any>(null);
const params_list = ref<any[]>([{ name: "", id: null }]);
const local_db_list = ref<any[]>([]);
const selected_service_id = ref<number | null>(null);
const doc_source_type = ref<'swagger' | 'apifox'>('swagger');
const doc_source_url = ref('');
const doc_source_cookies = ref('');
const apifox_doc_content = ref<Record<string, any> | null>(null);
const pulling_doc = ref(false);

const loadParamsSelect = async () => {
	try {
		const res: any = await params_select({});
		const data = res?.data;
		params_list.value = Array.isArray(data) ? data : (Array.isArray(data?.content) ? data.content : []);
		if (!params_list.value.some((p: any) => p && p.id == null)) {
			params_list.value = [{ name: '', id: null }, ...params_list.value];
		}
	} catch (e) {
		console.error('加载参数依赖下拉失败:', e);
		params_list.value = [{ name: "", id: null }];
	}
};

const loadLocalDbList = async () => {
	try {
		const res: any = await api_db_list({ page: 1, pageSize: 200 });
		const raw = res?.data;
		const list = Array.isArray(raw?.content) ? raw.content : (Array.isArray(raw) ? raw : []);
		local_db_list.value = list.map((row: any) => ({
			id: row.id,
			name: row.name,
			...row,
		}));
	} catch (e) {
		console.error('加载直连数据库列表失败:', e);
		local_db_list.value = [];
	}
};

const getMethodLabel = (methodVal: number | undefined) => {
	const map: Record<number, string> = {
		1: 'GET',
		2: 'POST',
		3: 'PUT',
		4: 'DELETE',
		5: 'PATCH',
		6: 'OPTIONS',
	};
	return map[Number(methodVal) as number] || 'API';
};

const getMethodColor = (methodVal: number | undefined) => {
	const v = Number(methodVal);
	switch (v) {
		case 1: return '#67C23A'; // GET 绿色
		case 2: return '#409EFF'; // POST 蓝色
		case 3: return '#E6A23C'; // PUT 橙色
		case 4: return '#F56C6C'; // DELETE 红色
		case 5: return '#8E44AD'; // PATCH 紫色
		case 6: return '#909399'; // OPTIONS 灰色
		default: return '#409EFF';
	}
};


const envManageDialogVisible = ref(false);
const envEditDialogVisible = ref(false);
const envFormRef = ref();
const envSaving = ref(false);
const envForm = ref<any>({
	id: undefined,
	name: '',
	config: [],
	variable: [],
	description: ''
});

const openEnvManage = async () => {
	envManageDialogVisible.value = true;
	await reloadEnvList();
};

const reloadEnvList = async () => {
	const envRes: any = await api_env({});
	env_list.value = envRes.data || [];
	if (env_list.value.length > 0 && (env_id.value == null || !env_list.value.some((e: any) => e.id === env_id.value))) {
		env_id.value = env_list.value[0].id;
	}
};

const newEnv = () => {
	envForm.value = { id: undefined, name: '', config: [], variable: [], description: '' };
	envEditDialogVisible.value = true;
};

const editEnv = async (row: any) => {
	try {
		const res: any = await env_info({ id: Number(row.id) });
		const d = res.data || row;
		envForm.value = {
			id: d.id,
			name: d.name || '',
			config: Array.isArray(d.config) ? d.config : [],
			variable: Array.isArray(d.variable) ? d.variable : [],
			description: d.description || ''
		};
		envEditDialogVisible.value = true;
	} catch (e) {
		ElMessage.error('加载环境详情失败');
	}
};

const addEnvConfigRow = () => {
	if (!Array.isArray(envForm.value.config)) envForm.value.config = [];
	envForm.value.config.push({ name: '', value: '' });
};

const removeEnvConfigRow = (idx: number) => {
	envForm.value.config.splice(idx, 1);
};

const addEnvVarRow = () => {
	if (!Array.isArray(envForm.value.variable)) envForm.value.variable = [];
	envForm.value.variable.push({ name: '', value: '' });
};

const removeEnvVarRow = (idx: number) => {
	envForm.value.variable.splice(idx, 1);
};

const saveEnvForm = async () => {
	if (!envForm.value?.name) {
		ElMessage.warning('请输入环境名称');
		return;
	}
	envSaving.value = true;
	try {
		const payload = {
			name: String(envForm.value.name).trim(),
			config: (envForm.value.config || []).filter((c: any) => c && String(c.name || '').trim()),
			variable: (envForm.value.variable || []).filter((v: any) => v && String(v.name || '').trim()),
			description: envForm.value.description || ''
		};
		if (envForm.value.id) {
			await save_env({ env_list: [{ id: Number(envForm.value.id), ...payload }] });
			ElMessage.success('保存成功');
		} else {
			await add_env(payload);
			ElMessage.success('新增成功');
		}
		envEditDialogVisible.value = false;
		await reloadEnvList();
	} catch (e) {
		ElMessage.error('保存失败');
	} finally {
		envSaving.value = false;
	}
};

const removeEnv = async (row: any) => {
	try {
		await ElMessageBox.confirm(`确定删除环境 "${row.name}" 吗？`, '提示', {
			confirmButtonText: '确定',
			cancelButtonText: '取消',
			type: 'warning'
		});
		await del_env({ id: Number(row.id) });
		ElMessage.success('删除成功');
		await reloadEnvList();
	} catch (e: any) {
		if (e !== 'cancel') ElMessage.error('删除失败');
	}
};

const loadServiceDetail = async () => {
	if (!current_service.value) return;
	

	const res: any = await api_tree({
		search: { api_service_id: Number(current_service.value.id) }
	});
	api_tree_data.value = res.data || [];
	
	// 加载环境列表
	await reloadEnvList();

	// 加载参数依赖下拉 & 直连数据库下拉
	await Promise.all([loadParamsSelect(), loadLocalDbList()]);
};

const onServiceChange = async (serviceId: number) => {
	const sid = Number(serviceId);
	const svc = service_list.value.find((s: any) => Number(s?.id) === sid);
	if (!svc || !current_project.value) return;
	await enterServiceDetail(current_project.value, svc);
};

const deleteCurrentService = async () => {
	if (!current_project.value?.id) {
		ElMessage.warning('未选择项目');
		return;
	}
	if (!current_service.value?.id) {
		ElMessage.warning('未选择服务');
		return;
	}
	try {
		await ElMessageBox.confirm(`确定删除服务 "${current_service.value.name}" 吗？`, '提示', { type: 'warning' });
		const res: any = await del_api_service({ id: Number(current_service.value.id) });
		if (res?.code === 200) {
			ElMessage.success('删除成功');
			// 刷新服务列表并处理当前服务指针
			const services = await loadServiceOptionsForProject(Number(current_project.value.id));
			if (services.length === 0) {
				goBack();
				return;
			}
			const next = services[0];
			await enterServiceDetail(current_project.value, next);
		}
	} catch (e: any) {
		if (e !== 'cancel') {
			console.error('删除服务失败:', e);
			ElMessage.error('删除服务失败');
		}
	}
};

const handlePullApiDoc = async () => {
	const serviceId = Number(selected_service_id.value || current_service.value?.id || 0);
	if (!serviceId) {
		ElMessage.warning('请先选择服务');
		return;
	}
	if (doc_source_type.value === 'swagger' && !doc_source_url.value.trim()) {
		ElMessage.warning('请输入 Swagger 文档地址');
		return;
	}
	if (doc_source_type.value === 'apifox' && !doc_source_url.value.trim()) {
		ElMessage.warning('Apifox 文档 URL 为必填');
		return;
	}
	if (doc_source_type.value === 'apifox' && !doc_source_cookies.value.trim()) {
		ElMessage.warning('Apifox Cookies 为必填');
		return;
	}
	pulling_doc.value = true;
	try {
		const res: any = await pull_api_doc({
			api_service_id: serviceId,
			source_type: doc_source_type.value,
			doc_url: doc_source_url.value.trim() || undefined,
			cookies: doc_source_type.value === 'apifox' ? (doc_source_cookies.value.trim() || undefined) : undefined,
			doc_content: doc_source_type.value === 'apifox' ? (apifox_doc_content.value || undefined) : undefined,
		});
		if (res?.code === 200) {
			const d = res.data || {};
			const imported = Number(d.imported || 0);
			const updated = Number(d.updated || 0);
			const folders = Number(d.folders || 0);
			if (imported + updated <= 0) {
				ElMessage.warning('解析完成但未识别到可导入接口，请检查导出文件结构或URL/Cookies');
				return;
			}
			ElMessage.success(`解析完成：新增${imported}，更新${updated}，分组${folders}`);
			await loadServiceDetail();
		}
	} finally {
		pulling_doc.value = false;
	}
};

const handleApifoxFileChange = async (uploadFile: any) => {
	const raw = uploadFile?.raw;
	if (!raw) return;
	try {
		const text = await raw.text();
		apifox_doc_content.value = JSON.parse(text);
		ElMessage.success(`已加载文件：${raw.name}`);
	} catch (e: any) {
		apifox_doc_content.value = null;
		ElMessage.error(e?.message || 'Apifox 文件解析失败，请检查 JSON 格式');
	}
};

const onTreeNodeClick = (data: any) => {
	if (data.type === 2 || data.type === 3) {
		openApiTab(data);
	}
};

const openApiTab = async (data: any) => {
	const existingTab = api_tabs.value.find(tab => tab.id === data.id);
	if (existingTab) {
		api_active_tab.value = existingTab.name;
	} else {
		// 加载接口详情
		const res: any = await api_info(data);
		data.api_info = res.data;
		
		const tabName = `api-${data.id}`;
		api_tabs.value.push({
			id: data.id,
			name: tabName,
			title: data.name,
			data: data
		});
		api_active_tab.value = tabName;
	}
};

const closeApiTab = (targetName: string) => {
	const tabs = api_tabs.value;
	let activeName = api_active_tab.value;
	if (activeName === targetName) {
		tabs.forEach((tab, index) => {
			if (tab.name === targetName) {
				const nextTab = tabs[index + 1] || tabs[index - 1];
				if (nextTab) {
					activeName = nextTab.name;
				}
			}
		});
	}
	api_active_tab.value = activeName;
	api_tabs.value = tabs.filter(tab => tab.name !== targetName);
};

const filterNode = (value: string, data: any) => {
	if (!value) return true;
	return data.name.includes(value);
};

watch(api_tree_filter, (val) => {
	api_tree_ref.value?.filter(val);
});

// -------------------- 接口树操作 --------------------
const menuDialogRef = ref(false);
const menu_form = ref({ name: '', type: 1, pid: null });

const handleAddApiCommand = (command: string) => {
	if (command === 'add_folder') {
		openAddMenu(1, null); // 添加根目录
	} else if (command === 'add_api') {
		openAddMenu(2, null); // 添加根接口
	}
};

const handleNodeCommand = (command: string, node: any) => {
	switch (command) {
		case 'add_folder':
			openAddMenu(1, node.id); // 添加子目录
			break;
		case 'add_api':
			openAddMenu(2, node.id); // 添加子接口
			break;
		case 'copy':
			copyApiNode(node);
			break;
		case 'edit':
			editMenu(node);
			break;
		case 'delete':
			deleteMenu(node);
			break;
	}
};

const openAddMenu = (type: number, parentId: number | null) => {
	menu_form.value = { 
		name: '', 
		type: type, 
		pid: parentId || 0 // 根节点的pid为0
	};
	dialogTitle.value = type === 1 ? '添加目录' : '添加接口';
	menuDialogRef.value = true;
};

const editMenu = (node: any) => {
	menu_form.value = { ...node };
	dialogTitle.value = node.type === 1 ? '编辑目录' : '编辑接口';
	menuDialogRef.value = true;
};

const deleteMenu = async (node: any) => {
	await ElMessageBox.confirm(`确定删除 ${node.name} 吗？`, '提示', { type: 'warning' });
	const res: any = await del_menu({ id: node.id });
	if (res.code === 200) {
		ElMessage.success('删除成功');
		await loadServiceDetail();
	}
};

const copyApiNode = async (node: any) => {
	try {
		if (!node?.api_id) {
			ElMessage.warning('仅支持复制接口节点');
			return;
		}
		const res: any = await copy_menu({ id: node.id, api_id: node.api_id });
		if (res.code === 200) {
			ElMessage.success('复制成功');
			await loadServiceDetail();
		}
	} catch (e: any) {
		console.error('复制接口失败:', e);
		ElMessage.error(e?.message || '复制失败');
	}
};

const confirmMenu = async () => {
	if (menu_form.value.id) {
		// 编辑
		const res: any = await edit_menu(menu_form.value);
		if (res.code === 200) {
			ElMessage.success('编辑成功');
			menuDialogRef.value = false;
			await loadServiceDetail();
		}
	} else {
		// 新增
		const menuData = {
			name: menu_form.value.name,
			pid: menu_form.value.pid,
			type: menu_form.value.type,
			api_service_id: current_service.value?.id
		};
		const res: any = await add_menu(menuData);
		if (res.code === 200) {
			ElMessage.success('添加成功');
			menuDialogRef.value = false;
			await loadServiceDetail();
		}
	}
};

// 获取节点图标样式类
const getNodeIconClass = (type: number) => {
	switch (type) {
		case 1: return 'icon-folder';    // 目录 - 蓝色
		case 2: return 'icon-api';       // 接口 - 绿色  
		case 3: return 'icon-case';      // 用例 - 橙色
		default: return '';
	}
};


const loadSceneManage = async () => {

};


const loadResultList = async () => {

};

// -------------------- 返回操作 --------------------
const goBack = () => {
	if (show_type.value === 'project') return;
	
	if (show_type.value === 'service_detail' || show_type.value === 'scene_manage') {
		show_type.value = 'project';
		api_tabs.value = [];
		api_active_tab.value = '';
		api_tree_data.value = [];
		api_tree_filter.value = '';
		current_project.value = null;
		current_service.value = null;
		service_list.value = [];
	} else if (show_type.value === 'result_list') {
		show_type.value = 'project';
	}
};

// -------------------- 生命周期 --------------------
onMounted(async () => {
	if (props.initialServiceId) {
		try {
			const svcRes: any = await api_service({ page: 1, pageSize: 200, search: {} });
			const allServices: any[] = svcRes.data?.content || [];
			const targetSvc = allServices.find((s: any) => Number(s.id) === Number(props.initialServiceId));

			if (targetSvc) {
				// 从全局项目管理查询项目信息
				const projRes: any = await getGlobalProjectList({ page: 1, page_size: 200 });
				const allProjects: any[] = projRes?.data?.items || projRes?.data?.content || [];
				const targetProj = allProjects.find((p: any) => Number(p.id) === Number(targetSvc.api_project_id))
					|| { id: targetSvc.api_project_id, name: '-' };

				current_project.value = targetProj;
				current_service.value = targetSvc;
				selected_service_id.value = Number(props.initialServiceId);
				show_type.value = 'service_detail';
				api_tabs.value = [];
				api_active_tab.value = '';
				api_tree_data.value = [];
				api_tree_filter.value = '';

				await loadServiceOptionsForProject(Number(targetSvc.api_project_id));
				await loadServiceDetail();
			} else {
				await getProjectList();
			}
		} catch {
			await getProjectList();
		}
	} else {
		await getProjectList();
	}
});
</script>


<style scoped>
/* 通用样式 */
.box-card {
	margin-bottom: 10px;
}

.mt-10px {
	margin-top: 10px;
}

/* 项目页面样式 */
.project-topbar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 0;
}

.project-topbar-left {
	display: flex;
	align-items: center;
	gap: 10px;
}

.pagination-wrapper {
	margin-top: 20px;
	display: flex;
	justify-content: center;
}

/* 服务详情页面样式 */
.service-detail-page {
	height: calc(100vh - 110px);
	display: flex;
	flex-direction: column;
	min-height: 0;
	overflow: auto;
	background: var(--el-bg-color-page);
}

.service-toolbar-card {
	flex: 0 0 auto;
	border-radius: 0 !important;
	border-left: none;
	border-right: none;
	border-top: none;
	box-shadow: 0 1px 3px rgba(0,0,0,.08) !important;
}

.service-toolbar-card :deep(.el-card__body) {
	padding: 10px 16px;
	background: var(--el-bg-color);
}

.service-topbar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
}

.service-topbar-left {
	display: flex;
	align-items: center;
	gap: 10px;
}

.service-title {
	font-size: 15px;
	font-weight: 600;
	color: #1a1a2e;
	letter-spacing: .2px;
}

.service-topbar-right {
	display: flex;
	flex-direction: column;
	gap: 6px;
	flex: 1;
	min-width: 0;
}

.doc-import-row {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 8px;
}

.service-tools-row {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 4px;
}

.doc-source-select {
	width: 110px;
}

.doc-url-input {
	width: 300px;
}

.doc-cookie-input {
	width: 300px;
}

.service-main {
	display: flex;
	gap: 8px;
	margin-top: 8px;
	flex: 1 1 auto;
	min-height: 0;
	padding: 0 8px 8px;
}

.service-left {
	width: 280px;
	flex: 0 0 280px;
	min-height: 0;
}

.service-right {
	flex: 1 1 auto;
	min-height: 0;
}

.api-tree-card,
.api-detail-card {
	height: 100%;
	display: flex;
	flex-direction: column;
	min-height: 0;
	border-radius: 8px !important;
	box-shadow: 0 1px 4px rgba(0,0,0,.06) !important;
}

.api-tree-card :deep(.el-card__body),
.api-detail-card :deep(.el-card__body) {
	flex: 1 1 auto;
	min-height: 0;
	display: flex;
	flex-direction: column;
	padding: 0;
}

.tree-container {
	height: 100%;
	display: flex;
	flex-direction: column;
	padding: 12px;
}

.tree-title {
	margin-bottom: 10px;
	font-size: 13px;
	font-weight: 600;
	color: #303133;
}

.tree-actions-bar {
	display: flex;
	align-items: center;
	margin-bottom: 10px;
	gap: 6px;
}

.tree-service-bar {
	display: flex;
	align-items: center;
	margin-bottom: 10px;
	gap: 6px;
}

.tree-content {
	flex: 1;
	overflow: auto;
}

.tree-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	width: 100%;
}

.tree-actions {
	display: flex;
	align-items: center;
}

.api-empty {
	height: calc(100% - 60px);
	display: flex;
	align-items: center;
	justify-content: center;
	border: 1px dashed var(--el-border-color);
	border-radius: 6px;
	color: var(--el-text-color-placeholder);
}

.api-detail-content {
	height: calc(100% - 60px);
}

.custom-tree-node {
	display: flex;
	align-items: center;
	justify-content: space-between;
	width: 100%;
	padding: 2px 0;
	position: relative;
	padding-right: 52px; /* 增大右侧快捷按钮预留空间 */
}

.node-content {
	display: flex;
	align-items: center;
	flex: 1;
	min-width: 0; /* 允许子元素触发省略号，避免覆盖右侧 ... */
}

.node-icon {
	margin-right: 8px;
	font-size: 18px;
}

.method-badge {
	font-size: 11px;
	font-weight: 600;
	padding: 0 4px;
	border-radius: 4px;
	color: #fff;
	min-width: 34px;
	text-align: center;
	margin-right: 3px;
	flex: 0 0 auto;
}

/* 不同类型节点的图标颜色 */
.icon-folder {
	color: #f39c12; /* 橙黄色 - 文件夹的正常颜色 */
}

.icon-api {
	color: #67c23a; /* 绿色 - 接口 */
}

.icon-case {
	color: #e6a23c; /* 橙色 - 用例 */
}

.node-title {
	flex: 1 1 auto;
	min-width: 0;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
	display: block;
	font-size: 12px;
	line-height: 18px;
}

.node-actions {
	position: absolute;
	right: 0;
	top: 50%;
	transform: translateY(-50%);
	opacity: 1; /* 固定显示在右侧 */
}

/* hover 时可加深可见性（保留扩展空间） */
.custom-tree-node:hover .node-actions { opacity: 1; }

/* 场景管理页面样式 */
.scene-topbar {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.scene-topbar-left {
	display: flex;
	align-items: center;
	gap: 10px;
}

.scene-title {
	font-size: 16px;
	font-weight: bold;
	color: var(--el-text-color-primary);
}

/* 结果列表页面样式 */
.result-topbar {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.result-topbar-left {
	display: flex;
	align-items: center;
	gap: 10px;
}

.result-title {
	font-size: 16px;
	font-weight: bold;
	color: var(--el-text-color-primary);
}

.result-stats {
	display: flex;
	flex-direction: column;
	gap: 2px;
}

.result-stats .pass {
	color: var(--el-color-success);
}

.result-stats .fail {
	color: var(--el-color-danger);
}

.result-stats .percent {
	color: var(--el-color-primary);
	font-weight: bold;
}
</style>