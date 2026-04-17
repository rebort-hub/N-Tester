<template>
	<div class="case-runner-page">
		<!-- 顶部工具栏 -->
		<div class="case-runner-toolbar">
			<div class="toolbar-left">
				<el-select v-model="selectedServiceId" placeholder="请选择服务" clearable filterable style="width:200px" @change="onServiceChange">
					<el-option v-for="s in serviceList" :key="s.id" :label="s.name" :value="s.id" />
				</el-select>
				<el-input v-model="caseKeyword" placeholder="搜索用例" clearable style="width:180px" @keyup.enter="filterCases" />
				<el-button type="primary" icon="Search" @click="filterCases">搜索</el-button>
				<el-button icon="Refresh" @click="resetSearch">重置</el-button>
			</div>
			<div class="toolbar-right">
				<el-button type="success" icon="Plus" :disabled="!selectedSuiteId" @click="openAddCaseDialog">新增用例</el-button>
				<el-button type="primary" :disabled="selectedCaseIds.length === 0" @click="openRunDialog">
					执行选中 ({{ selectedCaseIds.length }})
				</el-button>
			</div>
		</div>

		<!-- 主体：左侧用例集树 + 右侧用例列表 -->
		<div class="case-runner-body">
			<!-- 左侧用例集树 -->
			<div class="suite-panel">
				<div class="suite-panel-header">
					<span class="suite-panel-title">用例集</span>
				</div>
				<div v-if="!selectedServiceId" class="suite-empty">请先选择服务</div>
				<el-tree
					v-else
					:data="suiteTree"
					:props="{ label: 'name', children: 'children' }"
					node-key="id"
					highlight-current
					class="suite-tree"
					@node-click="onSuiteClick"
				>
					<template #default="{ data }">
						<span class="suite-node">
							<el-icon style="color:#f39c12;margin-right:4px"><Folder /></el-icon>
							<span class="suite-node-name">{{ data.name }}</span>
							<el-badge v-if="suiteCaseCount(data.id) > 0" :value="suiteCaseCount(data.id)" type="primary" class="suite-badge" />
						</span>
					</template>
				</el-tree>
			</div>

			<!-- 右侧用例列表 -->
			<div class="case-panel">
				<!-- 统计栏 -->
				<div class="case-stats-bar" v-if="allCases.length">
					<span class="stat-item">全部 <b>{{ allCases.length }}</b></span>
					<span class="stat-sep">·</span>
					<span class="stat-item pass">通过 <b>{{ allCases.filter(c=>c.status===1).length }}</b></span>
					<span class="stat-sep">·</span>
					<span class="stat-item fail">失败 <b>{{ allCases.filter(c=>c.status===2).length }}</b></span>
					<span class="stat-sep">·</span>
					<span class="stat-item">未执行 <b>{{ allCases.filter(c=>c.status===0).length }}</b></span>
				</div>

				<!-- 类型筛选 -->
				<div class="case-type-tabs">
					<span v-for="t in caseTypeTabOptions" :key="t.value" class="case-type-tab" :class="{active: activeCaseType===t.value}" @click="activeCaseType=t.value">
						{{ t.label }} ({{ t.value===0 ? allCases.length : allCases.filter(c=>c.case_type===t.value).length }})
					</span>
				</div>

				<el-table v-loading="loading" :data="filteredCases" border stripe empty-text="请先选择用例集" @selection-change="onSelectionChange" style="width:100%">
					<el-table-column type="selection" width="45" />
					<el-table-column prop="name" label="用例名称" min-width="180" show-overflow-tooltip />
					<el-table-column prop="description" label="描述" min-width="140" show-overflow-tooltip>
						<template #default="{ row }">{{ row.description || '-' }}</template>
					</el-table-column>
					<el-table-column label="类型" width="90" align="center">
						<template #default="{ row }">
							<el-tag :type="caseTypeMeta(row.case_type).color" size="small" effect="plain">{{ caseTypeMeta(row.case_type).label }}</el-tag>
						</template>
					</el-table-column>
					<el-table-column label="状态" width="90" align="center">
						<template #default="{ row }">
							<el-tag :type="caseStatusMeta(row.status).type" size="small">{{ caseStatusMeta(row.status).text }}</el-tag>
						</template>
					</el-table-column>
					<el-table-column label="所属用例集" width="130" show-overflow-tooltip>
						<template #default="{ row }">{{ suiteName(row.suite_id) }}</template>
					</el-table-column>
					<el-table-column label="操作" width="140" align="center" fixed="right">
						<template #default="{ row }">
							<span style="white-space:nowrap;display:inline-flex;gap:4px">
								<el-button type="warning" size="small" @click="openEditCaseDialog(row)">编辑</el-button>
								<el-button type="danger" size="small" @click="deleteCase(row)">删除</el-button>
							</span>
						</template>
					</el-table-column>
				</el-table>

				<div style="margin-top:12px">
					<el-pagination v-show="total > 0" background v-model:current-page="currentPage" v-model:page-size="pageSize" :page-sizes="[20,50,100]" layout="total, sizes, prev, pager, next, jumper" :total="total" @size-change="filterCases" @current-change="filterCases" />
				</div>
			</div>
		</div>

		<!-- 新增/编辑用例弹窗 -->
		<el-dialog v-model="caseDialogVisible" :title="caseDialogTitle" width="520px" destroy-on-close @close="resetCaseForm">
			<el-form ref="caseFormRef" :model="caseForm" label-width="80px">
				<el-form-item label="用例名称" required>
					<el-input v-model="caseForm.name" placeholder="请输入用例名称" />
				</el-form-item>
				<el-form-item label="用例类型">
					<el-radio-group v-model="caseForm.case_type">
						<el-radio-button v-for="t in caseTypeOptions" :key="t.value" :value="t.value">{{ t.label }}</el-radio-button>
					</el-radio-group>
				</el-form-item>
				<el-form-item label="描述">
					<el-input v-model="caseForm.description" type="textarea" :rows="2" placeholder="可选" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="caseDialogVisible=false">取消</el-button>
				<el-button type="primary" :loading="caseSubmitting" @click="submitCaseForm">确定</el-button>
			</template>
		</el-dialog>

		<!-- 执行配置弹窗 -->
		<el-dialog v-model="runDialogRef" title="执行配置" width="420px" destroy-on-close>
			<el-form :model="run_form" label-width="90px">
				<el-form-item label="任务名称" required>
					<el-input v-model="run_form.name" placeholder="请输入任务名称" />
				</el-form-item>
				<el-form-item label="执行环境" required>
					<el-select v-model="run_form.config.env_id" placeholder="请选择环境" style="width:100%">
						<el-option v-for="e in env_list" :key="e.id" :label="e.name" :value="e.id" />
					</el-select>
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="runDialogRef = false">取消</el-button>
				<el-button type="primary" @click="run_confirm">确定</el-button>
			</template>
		</el-dialog>

		<!-- 执行监控抽屉（保持不变）-->
		<el-drawer
			v-model="resultDialogRef"
			direction="rtl"
			size="min(92vw, 1680px)"
			append-to-body
			destroy-on-close
			class="wa-run-monitor-drawer wa-run-monitor-theme"
			:show-close="true"
			:close-on-click-modal="false"
			@closed="stopPolling"
		>
			<template #header>
				<div class="wa-run-monitor-drawer-header">
					<div class="wa-run-monitor-drawer-titleline">
						<span class="wa-run-monitor-drawer-title">{{ run_form.name }} - {{ run_type }}</span>
						<el-tag type="info" effect="plain" size="small" class="wa-run-monitor-drawer-badge">执行监控</el-tag>
					</div>
					<p class="wa-run-monitor-drawer-sub">接口用例步骤与日志，执行结束后可继续查看或关闭抽屉</p>
				</div>
			</template>
			<div class="wa-run-monitor-shell">
				<div class="wa-run-monitor-body api-run-monitor-body--solo">
					<div class="wa-run-monitor-pane api-run-monitor-pane--solo">
						<div class="wa-run-monitor-desc">
							<el-card shadow="never" class="wa-run-monitor-surface wa-run-monitor-summary">
								<el-descriptions :column="4" class="wa-run-monitor-desc-table" size="small">
									<el-descriptions-item label="任务名称">{{ run_form.name }}</el-descriptions-item>
									<el-descriptions-item label="执行人">{{ run_form.username || '—' }}</el-descriptions-item>
									<el-descriptions-item label="开始时间">{{ start_time ? String(start_time).replace('T', ' ') : '—' }}</el-descriptions-item>
									<el-descriptions-item label="结束时间">{{ end_time ? String(end_time).replace('T', ' ') : '—' }}</el-descriptions-item>
									<el-descriptions-item label="执行环境">{{ run_env || '—' }}</el-descriptions-item>
									<el-descriptions-item label="执行总数">{{ run_count }}</el-descriptions-item>
									<el-descriptions-item label="通过数">{{ Math.max(0, run_count - run_fail) }}</el-descriptions-item>
									<el-descriptions-item label="失败数">{{ run_fail }}</el-descriptions-item>
								</el-descriptions>
							</el-card>
						</div>
						<div class="wa-run-monitor-split">
							<el-card shadow="never" class="wa-run-monitor-surface wa-run-monitor-card wa-run-monitor-card--timeline">
								<template #header>
									<span class="wa-run-monitor-card-title">执行步骤</span>
								</template>
								<el-timeline class="wa-run-monitor-timeline">
									<el-timeline-item
										v-for="(res, index) in run_result_list"
										:key="index"
										:timestamp="res.create_time ? '执行时间：' + String(res.create_time).replace('T', ' ') : ''"
										:type="res.status === 1 ? 'success' : 'danger'"
									>
										<div class="api-run-monitor-step">
											<div>
												<div class="api-run-monitor-step-title">
													<span v-if="res.name !== '执行结束'">接口：{{ res.name }}</span>
													<span v-else>{{ res.name }}</span>
												</div>
												<div v-if="res.name !== '执行结束'" class="api-run-monitor-step-meta">
													<span>code：{{ res?.res?.code ?? '-' }}</span>
													<span>size：{{ res?.res?.size ?? 0 }}B</span>
													<span>time：{{ res?.res?.res_time ?? 0 }}ms</span>
												</div>
											</div>
											<div v-if="res.name !== '执行结束'">
												<el-button type="primary" link @click="view_result(res)">查看详情</el-button>
											</div>
										</div>
									</el-timeline-item>
								</el-timeline>
							</el-card>
							<el-card shadow="never" class="wa-run-monitor-surface wa-run-monitor-card wa-run-monitor-card--log">
								<template #header>
									<div class="wa-run-monitor-log-toolbar">
										<span class="wa-run-monitor-log-toolbar-title">
											<el-icon class="wa-run-monitor-log-toolbar-icon"><Monitor /></el-icon>
											接口用例执行过程日志
										</span>
										<el-button size="small" class="wa-run-monitor-btn-ghost" @click="copyApiRunLog">
											<el-icon class="el-icon--left"><DocumentCopy /></el-icon>
											复制
										</el-button>
									</div>
								</template>
								<ul class="wa-run-monitor-log-list">
									<li v-if="run_type !== '执行结束'" class="wa-run-monitor-log-pending">
										<span class="wa-run-monitor-log-dot" aria-hidden="true" />
										执行日志获取中…
									</li>
									<li
										v-for="(log, idx) in run_result_log"
										:key="idx"
										class="wa-run-monitor-log-line"
										:class="logLineClass(log)"
									>
										<template v-for="(seg, si) in parseLogLineForDisplay(log)" :key="`${idx}-${si}`">
											<span :class="seg.cls">{{ seg.text }}</span>
										</template>
									</li>
								</ul>
							</el-card>
						</div>
					</div>
				</div>
				<div class="wa-run-monitor-footer">
					<el-button class="wa-run-monitor-btn-ghost" @click="resultDialogRef = false">关闭</el-button>
				</div>
			</div>
		</el-drawer>

		<!-- 结果详情抽屉 -->
		<el-drawer v-model="detail_drawer" title="请求详情" size="1100px" destroy-on-close>
			<ApiDetail
				v-if="(detail?.res ?? detail?.response ?? detail?.res_info) && (detail?.req ?? detail?.request ?? detail?.req_info)"
				:api-data="buildDetailApiData(detail)"
				:env_list="env_list"
				:tree_list="[]"
				:params_list="[]"
				:local_db_list="[]"
			/>
		</el-drawer>
	</div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { DocumentCopy, Monitor, Folder } from '@element-plus/icons-vue';
import { Session } from '/@/utils/storage';
import { logLineClass, parseLogLineForDisplay } from '@/utils/runMonitorLog';
import ApiDetail from './api_detail.vue';
import { useApiAutomationApi } from '/@/api/v1/api_automation';

const {
	api_service,
	api_suite_list,
	api_case_list,
	add_api_case,
	del_api_case,
	api_env,
	run_api_case,
	get_api_script_log,
	get_api_script_result,
} = useApiAutomationApi();

// ---- 服务 & 用例集 ----
const serviceList = ref<any[]>([]);
const selectedServiceId = ref<number | null>(null);
const suiteList = ref<any[]>([]);
const suiteTree = computed(() => suiteList.value); // 树形结构直接用
const suiteOptions = computed(() => flattenSuites(suiteList.value));
const selectedSuiteId = ref<number | null>(null);
const activeCaseType = ref(0);

const caseTypeTabOptions = [
	{ label: '全部', value: 0 },
	{ label: '正向', value: 1 },
	{ label: '负向', value: 2 },
	{ label: '边界值', value: 3 },
	{ label: '安全性', value: 4 },
	{ label: '其他', value: 5 },
];

const flattenSuites = (tree: any[]): any[] => {
	const result: any[] = [];
	const walk = (nodes: any[]) => {
		for (const n of nodes) {
			result.push(n);
			if (n.children?.length) walk(n.children);
		}
	};
	walk(tree);
	return result;
};

const suiteName = (suiteId: number) => suiteOptions.value.find((s) => s.id === suiteId)?.name || '-';

// 每个用例集的用例数
const suiteCaseCount = (suiteId: number) => allCases.value.filter((c) => c.suite_id === suiteId).length;

const loadServices = async () => {
	try {
		const res: any = await api_service({ page: 1, pageSize: 200, search: {} });
		const raw = res?.data;
		serviceList.value = Array.isArray(raw?.content) ? raw.content : (Array.isArray(raw) ? raw : []);
	} catch { serviceList.value = []; }
};

const onServiceChange = async (id: number | null) => {
	selectedSuiteId.value = null;
	allCases.value = [];
	suiteList.value = [];
	activeCaseType.value = 0;
	if (!id) return;
	try {
		const r: any = await api_suite_list({ api_service_id: id });
		suiteList.value = Array.isArray(r?.data) ? r.data : [];
	} catch { suiteList.value = []; }
	await loadCases();
};

const onSuiteClick = (data: any) => {
	selectedSuiteId.value = data.id;
	activeCaseType.value = 0;
	currentPage.value = 1;
	loadCases();
};

// ---- 用例列表 ----
const allCases = ref<any[]>([]);
const loading = ref(false);
const caseKeyword = ref('');
const currentPage = ref(1);
const pageSize = ref(20);

const loadCases = async () => {
	if (!selectedServiceId.value) return;
	loading.value = true;
	try {
		const suites = selectedSuiteId.value
			? [{ id: selectedSuiteId.value }]
			: suiteOptions.value;
		const results: any[] = [];
		for (const suite of suites) {
			const r: any = await api_case_list({ suite_id: suite.id });
			const list = Array.isArray(r?.data) ? r.data : [];
			results.push(...list);
		}
		allCases.value = results;
	} catch { allCases.value = []; }
	finally { loading.value = false; }
};

const filteredCases = computed(() => {
	let list = allCases.value;
	if (activeCaseType.value !== 0) list = list.filter((c) => c.case_type === activeCaseType.value);
	if (caseKeyword.value) list = list.filter((c) => c.name?.includes(caseKeyword.value));
	const start = (currentPage.value - 1) * pageSize.value;
	return list.slice(start, start + pageSize.value);
});

const total = computed(() => {
	let list = allCases.value;
	if (activeCaseType.value !== 0) list = list.filter((c) => c.case_type === activeCaseType.value);
	if (caseKeyword.value) list = list.filter((c) => c.name?.includes(caseKeyword.value));
	return list.length;
});

const filterCases = () => { currentPage.value = 1; };
const resetSearch = () => {
	selectedSuiteId.value = null;
	caseKeyword.value = null as any;
	activeCaseType.value = 0;
	currentPage.value = 1;
	loadCases();
};

// ---- 新增/编辑/删除用例 ----
const caseDialogVisible = ref(false);
const caseDialogTitle = ref('新增用例');
const caseSubmitting = ref(false);
const caseFormRef = ref<any>(null);
const caseForm = ref({ id: 0, name: '', description: '', case_type: 1, mode: 'add' as 'add' | 'edit' });

const openAddCaseDialog = () => {
	if (!selectedSuiteId.value) { ElMessage.warning('请先选择用例集'); return; }
	caseForm.value = { id: 0, name: '', description: '', case_type: 1, mode: 'add' };
	caseDialogTitle.value = '新增用例';
	caseDialogVisible.value = true;
};

const openEditCaseDialog = (row: any) => {
	caseForm.value = { id: row.id, name: row.name, description: row.description || '', case_type: row.case_type || 1, mode: 'edit' };
	caseDialogTitle.value = '编辑用例';
	caseDialogVisible.value = true;
};

const resetCaseForm = () => {
	caseForm.value = { id: 0, name: '', description: '', case_type: 1, mode: 'add' };
};

const submitCaseForm = async () => {
	if (!caseForm.value.name.trim()) { ElMessage.warning('请输入用例名称'); return; }
	caseSubmitting.value = true;
	try {
		if (caseForm.value.mode === 'edit') {
			await add_api_case({ id: caseForm.value.id, name: caseForm.value.name, description: caseForm.value.description, case_type: caseForm.value.case_type } as any);
			ElMessage.success('修改成功');
		} else {
			await add_api_case({ name: caseForm.value.name, description: caseForm.value.description, suite_id: selectedSuiteId.value!, case_type: caseForm.value.case_type });
			ElMessage.success('新增成功');
		}
		caseDialogVisible.value = false;
		await loadCases();
	} catch (e: any) { ElMessage.error(e?.message || '操作失败'); }
	finally { caseSubmitting.value = false; }
};

const deleteCase = async (row: any) => {
	try {
		await ElMessageBox.confirm(`确认删除用例「${row.name}」？`, '提示', { type: 'warning' });
		await del_api_case({ id: row.id });
		ElMessage.success('删除成功');
		await loadCases();
	} catch (e: any) {
		if (e === 'cancel' || e === 'close') return;
		ElMessage.error(e?.message || '删除失败');
	}
};

// ---- 用例类型/状态 ----
const caseTypeOptions = [
	{ label: '正向', value: 1, color: 'success' },
	{ label: '负向', value: 2, color: 'danger' },
	{ label: '边界值', value: 3, color: 'warning' },
	{ label: '安全性', value: 4, color: 'info' },
	{ label: '其他', value: 5, color: '' },
] as const;
const caseTypeMeta = (t: number) => caseTypeOptions.find((o) => o.value === t) || { label: '其他', value: 5, color: '' };
const caseStatusMeta = (s: number) => {
	if (s === 1) return { text: '通过', type: 'success' as const };
	if (s === 2) return { text: '失败', type: 'danger' as const };
	return { text: '未执行', type: 'info' as const };
};

// ---- 勾选 ----
const selectedCaseIds = ref<number[]>([]);
const onSelectionChange = (rows: any[]) => { selectedCaseIds.value = rows.map((r) => r.id); };

// ---- 执行 ----
const env_list = ref<any[]>([]);
const runDialogRef = ref(false);
const resultDialogRef = ref(false);
const run_form = ref<any>({ name: '', config: { env_id: null }, run_list: [], username: '' });

const openRunDialog = async () => {
	if (!selectedCaseIds.value.length) { ElMessage.warning('请先勾选用例'); return; }
	try {
		const r: any = await api_env({});
		env_list.value = r?.data || [];
	} catch { env_list.value = []; }
	run_form.value = { name: `用例执行_${Date.now()}`, config: { env_id: null }, run_list: [], username: '' };
	runDialogRef.value = true;
};

const run_confirm = async () => {
	if (!run_form.value.name || !run_form.value.config.env_id) {
		ElMessage.error('请填写任务名称并选择环境');
		return;
	}
	try {
		const userInfo = Session.get('userInfo');
		if (userInfo?.username) run_form.value.username = userInfo.username;
	} catch (_) {}
	env_list.value.forEach((e: any) => {
		if (e.id === run_form.value.config.env_id) run_env.value = e.name;
	});
	run_result_log.value = [];
	run_result_list.value = [];
	run_count.value = 0;
	run_fail.value = 0;
	start_time.value = '';
	end_time.value = '';
	run_type.value = '正在执行';
	result_id.value = Date.now();
	runDialogRef.value = false;
	resultDialogRef.value = true;
	await startPolling();
	try {
		await run_api_case({
			case_ids: selectedCaseIds.value,
			env_id: run_form.value.config.env_id,
			name: run_form.value.name,
			result_id: result_id.value,
		} as any);
		ElMessage.success('执行完成');
	} catch (e: any) {
		ElMessage.error(e?.message || '执行失败');
	}
};

// ---- 执行监控（保持不变）----
const result_id = ref<number | null>(null);
const run_type = ref('准备执行');
const run_env = ref('');
const run_result_log = ref<any[]>([]);
const run_result_list = ref<any[]>([]);
const run_count = ref(0);
const run_fail = ref(0);
const start_time = ref('');
const end_time = ref('');
const interval = ref<any>(null);

const startPolling = async () => {
	if (interval.value) return;
	interval.value = setInterval(async () => { await get_result(); }, 1500);
};
const stopPolling = () => {
	if (interval.value) clearInterval(interval.value);
	interval.value = null;
};

const get_result = async () => {
	await Promise.all([get_script_log(), get_script_result_data()]);
};

const get_script_log = async () => {
	if (!result_id.value) return;
	const res: any = await get_api_script_log({ result_id: result_id.value });
	run_result_log.value = res.data || [];
};

const get_script_result_data = async () => {
	if (!result_id.value) return;
	const res: any = await get_api_script_result({ result_id: result_id.value });
	run_result_list.value = res.data || [];
	const list = run_result_list.value;
	run_count.value = list.length;
	run_fail.value = 0;
	if (list.length > 0) start_time.value = String(list[list.length - 1]?.create_time ?? '');
	end_time.value = '';
	for (const item of list) {
		if (item?.status === 0) run_fail.value += 1;
		if (item?.name === '执行结束') {
			run_type.value = '执行结束';
			run_count.value = Math.max(0, run_count.value - 1);
			end_time.value = String(item?.create_time ?? '');
			stopPolling();
			break;
		}
	}
};

const copyApiRunLog = async () => {
	const text = Array.isArray(run_result_log.value) ? run_result_log.value.join('\n') : '';
	if (!text.trim()) { ElMessage.info('暂无日志可复制'); return; }
	try {
		await navigator.clipboard.writeText(text);
		ElMessage.success('已复制到剪贴板');
	} catch { ElMessage.warning('复制失败，请手动选择日志文本'); }
};

// ---- 结果详情 ----
const detail_drawer = ref(false);
const detail = ref<any>({});

const view_result = (row: any) => { detail.value = row; detail_drawer.value = true; };

const buildDetailApiData = (d: any) => {
	const stableId = d?.api_id ?? d?.id ?? d?.uuid ?? d?.menu_id ?? `${d?.result_id ?? ''}-${d?.name ?? ''}`;
	return {
		api_id: stableId,
		api_info: {
			id: stableId,
			name: d?.name,
			req: d?.req ?? d?.request ?? d?.req_info,
			res: d?.res ?? d?.response ?? d?.res_info,
		},
	};
};

onMounted(() => { loadServices(); });
</script>

<style scoped>
.case-runner-page { height: calc(100vh - 120px); display: flex; flex-direction: column; padding: 10px; gap: 8px; overflow: hidden; }
.case-runner-toolbar { display: flex; align-items: center; justify-content: space-between; background: var(--el-bg-color); border: 1px solid var(--el-border-color); border-radius: 8px; padding: 10px 14px; flex-shrink: 0; }
.toolbar-left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.toolbar-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.case-runner-body { flex: 1; min-height: 0; display: flex; gap: 8px; overflow: hidden; }
.suite-panel { width: 220px; flex-shrink: 0; background: var(--el-bg-color); border: 1px solid var(--el-border-color); border-radius: 8px; display: flex; flex-direction: column; overflow: hidden; }
.suite-panel-header { padding: 10px 14px; border-bottom: 1px solid var(--el-border-color); flex-shrink: 0; }
.suite-panel-title { font-size: 13px; font-weight: 600; color: var(--el-text-color-primary); }
.suite-empty { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--el-text-color-placeholder); font-size: 13px; }
.suite-tree { flex: 1; overflow-y: auto; padding: 4px 0; }
.suite-node { display: flex; align-items: center; gap: 4px; width: 100%; min-width: 0; }
.suite-node-name { font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.suite-badge { margin-left: auto; flex-shrink: 0; }
.case-panel { flex: 1; min-width: 0; background: var(--el-bg-color); border: 1px solid var(--el-border-color); border-radius: 8px; display: flex; flex-direction: column; overflow: hidden; padding: 10px; }
.case-stats-bar { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; font-size: 13px; flex-shrink: 0; }
.stat-item { color: var(--el-text-color-regular); }
.stat-item b { font-weight: 600; color: var(--el-text-color-primary); }
.stat-item.pass b { color: #67c23a; }
.stat-item.fail b { color: #f56c6c; }
.stat-sep { color: var(--el-border-color); }
.case-type-tabs { display: flex; gap: 6px; margin-bottom: 10px; flex-shrink: 0; flex-wrap: wrap; }
.case-type-tab { padding: 3px 12px; border-radius: 20px; font-size: 12px; cursor: pointer; border: 1px solid var(--el-border-color); color: var(--el-text-color-regular); background: var(--el-bg-color); transition: all .15s; user-select: none; }
.case-type-tab:hover { border-color: #409eff; color: #409eff; }
.case-type-tab.active { background: #409eff; border-color: #409eff; color: #fff; font-weight: 500; }
</style>

<style lang="scss">
@import '@/theme/modules/web-run-monitor.scss';
</style>
