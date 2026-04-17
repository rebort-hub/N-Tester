<template>
	<div class="report-page" v-loading="loading" element-loading-text="报告加载中...">

		<!-- 顶部 Header -->
		<div class="report-header">
			<div class="report-header-brand">
				<span class="brand-icon">></span>
				<span class="brand-name">接口测试报告</span>
			</div>
			<div class="report-header-meta">
				<span class="meta-item">
					<span class="meta-label">任务</span>
					<span class="meta-val">{{ result_form.name }}</span>
				</span>
				<span class="meta-sep">|</span>
				<span class="meta-item">
					<span class="meta-label">执行人</span>
					<span class="meta-val">{{ result_form.username || '-' }}</span>
				</span>
				<span class="meta-sep">|</span>
				<span class="meta-item">
					<span class="meta-label">开始</span>
					<span class="meta-val">{{ result_form.start_time ? String(result_form.start_time).replace('T',' ').slice(0,19) : '-' }}</span>
				</span>
				<span class="meta-sep">|</span>
				<span class="meta-item">
					<span class="meta-label">结束</span>
					<span class="meta-val">{{ result_form.end_time ? String(result_form.end_time).replace('T',' ').slice(0,19) : '-' }}</span>
				</span>
			</div>
		</div>

		<!-- 汇总统计 -->
		<div class="report-summary">
			<!-- 环形进度 -->
			<div class="summary-donut">
				<el-progress
					type="circle"
					:percentage="result_form.result?.percent ?? 0"
					:width="120"
					:stroke-width="10"
					:color="(result_form.result?.percent ?? 0) >= 80 ? '#52c41a' : (result_form.result?.percent ?? 0) >= 60 ? '#faad14' : '#ff4d4f'"
				>
					<template #default="{ percentage }">
						<div class="donut-inner">
							<span class="donut-pct">{{ percentage }}%</span>
							<span class="donut-label">通过率</span>
						</div>
					</template>
				</el-progress>
			</div>

			<!-- 统计卡片 -->
			<div class="summary-cards">
				<div class="scard scard-total">
					<div class="scard-icon">></div>
					<div class="scard-body">
						<div class="scard-val">{{ result_form.result?.total ?? 0 }}</div>
						<div class="scard-label">接口总数</div>
					</div>
				</div>
				<div class="scard scard-pass">
					<div class="scard-icon">√</div>
					<div class="scard-body">
						<div class="scard-val">{{ result_form.result?.pass ?? 0 }}</div>
						<div class="scard-label">通过</div>
					</div>
				</div>
				<div class="scard scard-fail">
					<div class="scard-icon">X</div>
					<div class="scard-body">
						<div class="scard-val">{{ result_form.result?.fail ?? 0 }}</div>
						<div class="scard-label">失败</div>
					</div>
				</div>
				<div class="scard scard-skip">
					<div class="scard-icon">></div>
					<div class="scard-body">
						<div class="scard-val">{{ Math.max(0, (result_form.result?.total ?? 0) - (result_form.result?.pass ?? 0) - (result_form.result?.fail ?? 0)) }}</div>
						<div class="scard-label">跳过</div>
					</div>
				</div>
			</div>

			<!-- 进度条 -->
			<div class="summary-bar-wrap">
				<div class="bar-title">执行进度</div>
				<div class="bar-track">
					<div class="bar-pass" :style="{width: passWidth + '%'}"></div>
					<div class="bar-fail" :style="{width: failWidth + '%'}"></div>
				</div>
				<div class="bar-legend">
					<span class="legend-pass">■ 通过 {{ result_form.result?.pass ?? 0 }}</span>
					<span class="legend-fail">■ 失败 {{ result_form.result?.fail ?? 0 }}</span>
				</div>
			</div>
		</div>

		<!-- 主体：左侧用例列表 + 右侧详情 -->
		<div class="report-body">
			<!-- 左侧用例列表 -->
			<div class="case-sidebar">
				<div class="sidebar-header">
					<span class="sidebar-title">用例列表</span>
					<div class="sidebar-tabs">
						<span class="stab" :class="{active: script_active==='all'}" @click="switchTab('all')">全部 {{ res_script_result.length }}</span>
						<span class="stab pass" :class="{active: script_active==='pass'}" @click="switchTab('pass')">通过 {{ res_script_result.filter(s=>s.status===1).length }}</span>
						<span class="stab fail" :class="{active: script_active==='fail'}" @click="switchTab('fail')">失败 {{ res_script_result.filter(s=>s.status===0).length }}</span>
					</div>
				</div>
				<div class="case-list">
					<div
						v-for="(script, index) in script_list"
						:key="index"
						class="case-item"
						:class="{ active: (script.uuid || script.menu_id || script.id) === menu_id, 'case-pass': script.status===1, 'case-fail': script.status===0 }"
						@click="script_click(script, index)"
					>
						<span class="case-status-dot" :class="script.status===1 ? 'dot-pass' : 'dot-fail'"></span>
						<div class="case-info">
							<div class="case-name">{{ script.name }}</div>
							<div class="case-stats">
								<span class="cs-pass">✓ {{ script.pass }}</span>
								<span class="cs-fail">✗ {{ script.fail }}</span>
							</div>
						</div>
						<el-icon class="case-arrow"><ArrowRight /></el-icon>
					</div>
				</div>
			</div>

			<!-- 右侧详情 -->
			<div class="detail-panel">
				<!-- 当前用例信息栏 -->
				<div class="detail-header">
					<div class="detail-title">{{ name || '请选择用例' }}</div>
					<div class="detail-meta">
						<span class="dm-item"><span class="dm-label">环境</span>{{ run_env || '-' }}</span>
						<span class="dm-item"><span class="dm-label">开始</span>{{ start_time ? String(start_time).replace('T',' ').slice(0,19) : '-' }}</span>
						<span class="dm-item"><span class="dm-label">结束</span>{{ end_time ? String(end_time).replace('T',' ').slice(0,19) : '-' }}</span>
						<span class="dm-item"><span class="dm-label">总数</span>{{ run_count }}</span>
						<span class="dm-item pass-text"><span class="dm-label">通过</span>{{ run_count - run_fail }}</span>
						<span class="dm-item fail-text"><span class="dm-label">失败</span>{{ run_fail }}</span>
					</div>
				</div>

				<!-- 步骤 + 日志 -->
				<div class="detail-content">
					<!-- 步骤时间线 -->
					<div class="steps-panel">
						<div class="panel-title">
							<span class="panel-title-icon">⚡</span> 执行步骤
						</div>
						<div class="steps-list">
							<div
								v-for="(res, idx) in run_result_list"
								:key="idx"
								class="step-item"
								:class="res.status===1 ? 'step-pass' : res.name==='执行结束' ? 'step-end' : 'step-fail'"
							>
								<div class="step-connector" v-if="idx < run_result_list.length - 1"></div>
								<div class="step-dot" :class="res.status===1 ? 'dot-s-pass' : res.name==='执行结束' ? 'dot-s-end' : 'dot-s-fail'">
									<span v-if="res.status===1">✓</span>
									<span v-else-if="res.name==='执行结束'">■</span>
									<span v-else>✗</span>
								</div>
								<div class="step-body">
									<div class="step-name-row">
										<span class="step-name">{{ res.name === '执行结束' ? '执行结束' : res.name }}</span>
										<span v-if="res.name !== '执行结束'" class="step-time">{{ res.create_time ? String(res.create_time).replace('T',' ').slice(11,19) : '' }}</span>
									</div>
									<div v-if="res.name !== '执行结束' && res.res" class="step-metrics">
										<span class="metric" :class="res.res.code >= 200 && res.res.code < 300 ? 'metric-ok' : 'metric-err'">{{ res.res.code }}</span>
										<span class="metric">{{ res.res.res_time }}ms</span>
										<span class="metric">{{ res.res.size }}B</span>
									</div>
									<div v-if="res.name !== '执行结束'" class="step-action">
										<el-button size="small" type="primary" plain @click="view_result(res)">查看详情</el-button>
									</div>
								</div>
							</div>
							<div v-if="!run_result_list.length" class="steps-empty">暂无执行步骤</div>
						</div>
					</div>

					<!-- 执行日志 -->
					<div class="log-panel">
						<div class="panel-title">
							<span class="panel-title-icon">📄</span> 执行日志
							<el-button size="small" class="log-copy-btn" @click="copyLog">复制</el-button>
						</div>
						<div class="log-body">
							<div v-if="!run_result_log.length" class="log-empty">暂无日志</div>
							<div
								v-for="(log, idx) in run_result_log"
								:key="idx"
								class="log-line"
								:class="log.includes('失败') || log.includes('ERROR') ? 'log-err' : log.includes('成功') || log.includes('通过') ? 'log-ok' : ''"
							>{{ log }}</div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- 请求详情抽屉 -->
		<el-drawer v-model="detail_drawer" title="请求详情" size="1100px" destroy-on-close>
			<ApiDetail
				v-if="(detail?.res ?? detail?.response ?? detail?.res_info) && (detail?.req ?? detail?.request ?? detail?.req_info)"
				:api-data="buildDetailApiData(detail)"
				:env_list="env_list"
				:tree_list="tree_list"
				:local_db_list="local_db_list"
			/>
		</el-drawer>
	</div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { ArrowRight } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import {
	get_api_script_report_log,
	get_api_script_result_detail,
	get_api_script_result_detail_list,
	get_api_script_result_report_list,
	get_api_script_result_list,
	api_env,
	api_db_list,
	api_tree_list,
} from '/@/api/v1/api_automation';
import ApiDetail from './api_detail.vue';

const route = useRoute();
const result_id = ref<any>('');
const result_form = ref<any>({ result: { percent: 0, pass: 0, fail: 0, total: 0 } });
const loading = ref(false);
const script_active = ref('all');
const script_list = ref<any[]>([]);
const res_script_result = ref<any[]>([]);
const menu_id = ref<any>('');
const selectedIndex = ref(0);
const env_list = ref<any[]>([]);
const tree_list = ref<any[]>([]);
const run_result_list = ref<any[]>([]);
const run_count = ref(0);
const run_fail = ref(0);
const start_time = ref('');
const end_time = ref('');
const run_env = ref('');
const name = ref('');
const run_result_log = ref<any[]>([]);
const detail_drawer = ref(false);
const detail = ref<any>({});
const local_db_list = ref<any[]>([]);

const passWidth = computed(() => {
	const t = result_form.value.result?.total ?? 0;
	if (!t) return 0;
	return Math.round(((result_form.value.result?.pass ?? 0) / t) * 100);
});
const failWidth = computed(() => {
	const t = result_form.value.result?.total ?? 0;
	if (!t) return 0;
	return Math.round(((result_form.value.result?.fail ?? 0) / t) * 100);
});

const buildDetailApiData = (d: any) => {
	const stableId = d?.api_id ?? d?.id ?? d?.uuid ?? d?.menu_id ?? `${result_id.value ?? ''}-${d?.name ?? ''}`;
	return {
		api_id: stableId,
		api_info: { id: stableId, name: d?.name, req: d?.req ?? d?.request ?? d?.req_info, res: d?.res ?? d?.response ?? d?.res_info },
	};
};

const get_script_result = async () => {
	loading.value = true;
	result_id.value = route.query.result_id as string;
	try {
		const res: any = await get_api_script_result_detail({ result_id: Number(result_id.value) });
		const data = res?.data || res;
		result_form.value = data;
		const script0 = data.script?.[0];
		if (script0) {
			menu_id.value = script0.uuid ?? script0.menu_id ?? script0.id;
			name.value = script0.name ?? '';
		}
		script_list.value = data.script ?? [];
		res_script_result.value = data.script ?? [];
		run_env.value = env_list.value.find((e: any) => e.id === data.config?.env_id)?.name ?? '';
		await get_script_result_report_list();
		await get_script_log();
	} finally {
		loading.value = false;
	}
};

const get_env_list = async () => {
	const res: any = await api_env({});
	env_list.value = Array.isArray(res?.data) ? res.data : res?.data?.content ?? [];
};

const get_api_tree_list = async () => {
	const res: any = await api_tree_list({});
	tree_list.value = res?.data ?? [];
};

const switchTab = (tab: string) => {
	script_active.value = tab;
	if (tab === 'all') script_list.value = [...res_script_result.value];
	else if (tab === 'pass') script_list.value = res_script_result.value.filter((i: any) => i.status === 1);
	else script_list.value = res_script_result.value.filter((i: any) => i.status === 0);
};

const script_click = async (script: any, index: number) => {
	selectedIndex.value = index;
	menu_id.value = script.uuid ?? script.menu_id ?? script.id;
	name.value = script.name ?? '';
	await get_script_result_report_list();
	await get_script_log();
};

const get_script_result_report_list = async () => {
	if (!result_id.value || !menu_id.value) return;
	const res: any = await get_api_script_result_report_list({
		result_id: Number(result_id.value),
		menu_id: String(menu_id.value),
	});
	const data = res?.data ?? [];
	run_result_list.value = data;
	run_count.value = data.filter((i: any) => i.name !== '执行结束').length;
	run_fail.value = data.filter((i: any) => i.status === 0 && i.name !== '执行结束').length;
	if (data.length > 0) {
		start_time.value = data[data.length - 1]?.create_time ?? '';
		end_time.value = data[0]?.create_time ?? '';
	}
};

const get_script_log = async () => {
	if (!result_id.value || !menu_id.value) return;
	const res: any = await get_api_script_report_log({
		result_id: String(result_id.value),
		menu_id: String(menu_id.value),
	});
	run_result_log.value = res?.data ?? [];
};

const get_db_list = async () => {
	const res: any = await api_db_list({});
	const raw = res?.data;
	local_db_list.value = Array.isArray(raw?.content) ? raw.content : Array.isArray(raw) ? raw : [];
};

const view_result = async (api: any) => {
	await get_db_list();
	detail.value = api;
	detail_drawer.value = true;
};

const copyLog = async () => {
	const text = run_result_log.value.join('\n');
	if (!text) { ElMessage.info('暂无日志'); return; }
	try { await navigator.clipboard.writeText(text); ElMessage.success('已复制'); } catch { ElMessage.warning('复制失败'); }
};

onMounted(() => {
	get_env_list();
	get_api_tree_list();
	get_script_result();
});
</script>

<style scoped lang="scss">
/* ── 整体 ── */
.report-page { min-height: 100vh; background: #f0f2f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }

/* ── Header ── */
.report-header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 16px 24px; display: flex; align-items: center; justify-content: space-between; }
.report-header-brand { display: flex; align-items: center; gap: 10px; }
.brand-icon { font-size: 22px; }
.brand-name { font-size: 18px; font-weight: 700; color: #fff; letter-spacing: 1px; }
.report-header-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.meta-item { display: flex; align-items: center; gap: 4px; font-size: 13px; color: rgba(255,255,255,.85); }
.meta-label { color: rgba(255,255,255,.5); font-size: 11px; }
.meta-val { color: #fff; font-weight: 500; }
.meta-sep { color: rgba(255,255,255,.3); }

/* ── 汇总 ── */
.report-summary { display: flex; align-items: center; gap: 20px; padding: 20px 24px; background: #fff; border-bottom: 1px solid #e8eaed; flex-wrap: wrap; }
.summary-donut { flex-shrink: 0; }
.donut-inner { display: flex; flex-direction: column; align-items: center; }
.donut-pct { font-size: 22px; font-weight: 700; color: #1a1a2e; }
.donut-label { font-size: 11px; color: #909399; }
.summary-cards { display: flex; gap: 12px; flex: 1; min-width: 0; flex-wrap: wrap; }
.scard { display: flex; align-items: center; gap: 12px; padding: 14px 18px; border-radius: 10px; flex: 1; min-width: 100px; }
.scard-total { background: linear-gradient(135deg, #667eea, #764ba2); }
.scard-pass  { background: linear-gradient(135deg, #56ab2f, #a8e063); }
.scard-fail  { background: linear-gradient(135deg, #f7971e, #ffd200); }
.scard-skip  { background: linear-gradient(135deg, #4facfe, #00f2fe); }
.scard-icon { font-size: 24px; }
.scard-val { font-size: 28px; font-weight: 700; color: #fff; line-height: 1; }
.scard-label { font-size: 12px; color: rgba(255,255,255,.8); margin-top: 2px; }
.summary-bar-wrap { flex: 1; min-width: 200px; }
.bar-title { font-size: 12px; color: #909399; margin-bottom: 8px; }
.bar-track { height: 10px; background: #f0f0f0; border-radius: 5px; overflow: hidden; display: flex; }
.bar-pass { background: #52c41a; transition: width .6s; }
.bar-fail { background: #ff4d4f; transition: width .6s; }
.bar-legend { display: flex; gap: 16px; margin-top: 6px; font-size: 12px; }
.legend-pass { color: #52c41a; }
.legend-fail { color: #ff4d4f; }

/* ── 主体 ── */
.report-body { display: flex; gap: 0; height: calc(100vh - 220px); min-height: 500px; }

/* ── 左侧用例列表 ── */
.case-sidebar { width: 260px; flex-shrink: 0; background: #fff; border-right: 1px solid #e8eaed; display: flex; flex-direction: column; overflow: hidden; }
.sidebar-header { padding: 12px 14px; border-bottom: 1px solid #f0f0f0; flex-shrink: 0; }
.sidebar-title { font-size: 13px; font-weight: 600; color: #1a1a2e; display: block; margin-bottom: 8px; }
.sidebar-tabs { display: flex; gap: 4px; }
.stab { padding: 3px 10px; border-radius: 12px; font-size: 11px; cursor: pointer; border: 1px solid #e8eaed; color: #606266; background: #fafafa; transition: all .15s; user-select: none; }
.stab:hover { border-color: #409eff; color: #409eff; }
.stab.active { background: #409eff; border-color: #409eff; color: #fff; }
.stab.pass.active { background: #52c41a; border-color: #52c41a; }
.stab.fail.active { background: #ff4d4f; border-color: #ff4d4f; }
.case-list { flex: 1; overflow-y: auto; padding: 6px 0; }
.case-item { display: flex; align-items: center; gap: 10px; padding: 10px 14px; cursor: pointer; border-left: 3px solid transparent; transition: all .15s; }
.case-item:hover { background: #f5f7fa; }
.case-item.active { background: #e6f4ff; border-left-color: #409eff; }
.case-item.case-pass { border-left-color: transparent; }
.case-item.case-pass.active { border-left-color: #52c41a; background: #f6ffed; }
.case-item.case-fail.active { border-left-color: #ff4d4f; background: #fff1f0; }
.case-status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dot-pass { background: #52c41a; }
.dot-fail { background: #ff4d4f; }
.case-info { flex: 1; min-width: 0; }
.case-name { font-size: 12px; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: 2px; }
.case-stats { display: flex; gap: 8px; font-size: 11px; }
.cs-pass { color: #52c41a; }
.cs-fail { color: #ff4d4f; }
.case-arrow { font-size: 12px; color: #c0c4cc; flex-shrink: 0; }

/* ── 右侧详情 ── */
.detail-panel { flex: 1; min-width: 0; display: flex; flex-direction: column; overflow: hidden; }
.detail-header { padding: 12px 20px; background: #fff; border-bottom: 1px solid #e8eaed; flex-shrink: 0; }
.detail-title { font-size: 15px; font-weight: 600; color: #1a1a2e; margin-bottom: 6px; }
.detail-meta { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 12px; }
.dm-item { display: flex; align-items: center; gap: 4px; color: #606266; }
.dm-label { color: #909399; }
.pass-text { color: #52c41a; font-weight: 600; }
.fail-text { color: #ff4d4f; font-weight: 600; }
.detail-content { flex: 1; min-height: 0; display: flex; gap: 0; overflow: hidden; }

/* ── 步骤面板 ── */
.steps-panel { width: 380px; flex-shrink: 0; border-right: 1px solid #e8eaed; display: flex; flex-direction: column; overflow: hidden; background: #fff; }
.panel-title { padding: 10px 16px; font-size: 13px; font-weight: 600; color: #1a1a2e; border-bottom: 1px solid #f0f0f0; display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.panel-title-icon { font-size: 14px; }
.log-copy-btn { margin-left: auto; }
.steps-list { flex: 1; overflow-y: auto; padding: 12px 16px; }
.step-item { display: flex; gap: 12px; position: relative; padding-bottom: 16px; }
.step-item:last-child { padding-bottom: 0; }
.step-connector { position: absolute; left: 11px; top: 24px; bottom: 0; width: 2px; background: #e8eaed; }
.step-dot { width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; z-index: 1; }
.dot-s-pass { background: #f6ffed; border: 2px solid #52c41a; color: #52c41a; }
.dot-s-fail { background: #fff1f0; border: 2px solid #ff4d4f; color: #ff4d4f; }
.dot-s-end  { background: #f5f5f5; border: 2px solid #d9d9d9; color: #909399; }
.step-body { flex: 1; min-width: 0; }
.step-name-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.step-name { font-size: 13px; font-weight: 500; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.step-time { font-size: 11px; color: #c0c4cc; flex-shrink: 0; margin-left: 8px; }
.step-metrics { display: flex; gap: 8px; margin-bottom: 6px; }
.metric { font-size: 11px; padding: 1px 6px; border-radius: 3px; background: #f5f5f5; color: #606266; }
.metric-ok { background: #f6ffed; color: #52c41a; }
.metric-err { background: #fff1f0; color: #ff4d4f; }
.step-action { }
.steps-empty { text-align: center; color: #c0c4cc; padding: 40px 0; font-size: 13px; }

/* ── 日志面板 ── */
.log-panel { flex: 1; min-width: 0; display: flex; flex-direction: column; overflow: hidden; background: #1e1e1e; }
.log-body { flex: 1; overflow-y: auto; padding: 10px 14px; font-family: 'Consolas','Monaco',monospace; }
.log-empty { color: #555; font-size: 13px; padding: 20px 0; }
.log-line { font-size: 12px; line-height: 1.7; color: #d4d4d4; white-space: pre-wrap; word-break: break-all; }
.log-ok  { color: #4ec9b0; }
.log-err { color: #f48771; }
.log-panel .panel-title { background: #252526; border-bottom-color: #3c3c3c; color: #d4d4d4; }
.log-panel .panel-title .log-copy-btn { color: #aaa; border-color: #4a4a4a; background: transparent; }
</style>
