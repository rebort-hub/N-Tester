<template>
	<div class="report-page" v-loading="loading" element-loading-text="报告加载中...">

		<!-- 顶部 Header -->
		<div class="report-header">
			<div class="report-header-brand">
				<span class="brand-icon">></span>
				<span class="brand-name">UI 测试报告</span>
				<span class="brand-sub">Web 自动化</span>
			</div>
			<div class="report-header-meta">
				<span class="meta-item">
					<span class="meta-label">任务</span>
					<span class="meta-val">{{ res_form.task_name }}</span>
				</span>
				<span class="meta-sep">|</span>
				<span class="meta-item">
					<span class="meta-label">执行人</span>
					<span class="meta-val">{{ res_form.username || '-' }}</span>
				</span>
				<span class="meta-sep">|</span>
				<span class="meta-item">
					<span class="meta-label">开始</span>
					<span class="meta-val">{{ formatTime(res_form.start_time) }}</span>
				</span>
				<span class="meta-sep">|</span>
				<span class="meta-item">
					<span class="meta-label">结束</span>
					<span class="meta-val">{{ formatTime(res_form.end_time) }}</span>
				</span>
			</div>
		</div>

		<!-- 汇总统计 -->
		<div class="report-summary">
			<div class="summary-donut">
				<el-progress
					type="circle"
					:percentage="Number(res_form.percent ?? 0)"
					:width="120"
					:stroke-width="10"
					:color="Number(res_form.percent ?? 0) >= 80 ? '#52c41a' : Number(res_form.percent ?? 0) >= 60 ? '#faad14' : '#ff4d4f'"
				>
					<template #default="{ percentage }">
						<div class="donut-inner">
							<span class="donut-pct">{{ percentage }}%</span>
							<span class="donut-label">通过率</span>
						</div>
					</template>
				</el-progress>
			</div>

			<div class="summary-cards">
				<div class="scard scard-total">
					<div class="scard-icon">></div>
					<div class="scard-body">
						<div class="scard-val">{{ res_form.total ?? 0 }}</div>
						<div class="scard-label">脚本总数</div>
					</div>
				</div>
				<div class="scard scard-pass">
					<div class="scard-icon">√</div>
					<div class="scard-body">
						<div class="scard-val">{{ (res_form.total ?? 0) - (res_form.total_fail ?? 0) }}</div>
						<div class="scard-label">通过</div>
					</div>
				</div>
				<div class="scard scard-fail">
					<div class="scard-icon">X</div>
					<div class="scard-body">
						<div class="scard-val">{{ res_form.total_fail ?? 0 }}</div>
						<div class="scard-label">失败</div>
					</div>
				</div>
				<div class="scard scard-browser">
					<div class="scard-icon">></div>
					<div class="scard-body">
						<div class="scard-val">{{ browser_list.length }}</div>
						<div class="scard-label">浏览器</div>
					</div>
				</div>
			</div>

			<div class="summary-bar-wrap">
				<div class="bar-title">执行进度</div>
				<div class="bar-track">
					<div class="bar-pass" :style="{width: passWidth + '%'}"></div>
					<div class="bar-fail" :style="{width: failWidth + '%'}"></div>
				</div>
				<div class="bar-legend">
					<span class="legend-pass">■ 通过 {{ (res_form.total ?? 0) - (res_form.total_fail ?? 0) }}</span>
					<span class="legend-fail">■ 失败 {{ res_form.total_fail ?? 0 }}</span>
				</div>
			</div>
		</div>

		<!-- 主体 -->
		<div class="report-body">
			<!-- 左侧脚本列表 -->
			<div class="case-sidebar">
				<div class="sidebar-header">
					<span class="sidebar-title">脚本列表</span>
					<div class="sidebar-tabs">
						<span class="stab" :class="{active: script_active==='all'}" @click="switchTab('all')">全部 {{ (res_form.script_list||[]).length }}</span>
						<span class="stab pass" :class="{active: script_active==='pass'}" @click="switchTab('pass')">通过 {{ (res_form.script_list||[]).filter((s:any)=>s.status===1).length }}</span>
						<span class="stab fail" :class="{active: script_active==='fail'}" @click="switchTab('fail')">失败 {{ (res_form.script_list||[]).filter((s:any)=>s.status===0).length }}</span>
					</div>
				</div>
				<div class="case-list">
					<div
						v-for="(script, index) in script_list"
						:key="script.id"
						class="case-item"
						:class="{ active: selectedIndex === index, 'case-pass': script.status===1, 'case-fail': script.status===0 }"
						@click="script_click(script, index)"
					>
						<span class="case-status-dot" :class="script.status===1 ? 'dot-pass' : 'dot-fail'"></span>
						<div class="case-info">
							<div class="case-name">{{ script.name }}</div>
						</div>
						<el-icon class="case-arrow"><ArrowRight /></el-icon>
					</div>
				</div>
			</div>

			<!-- 右侧详情 -->
			<div class="detail-panel">
				<!-- 浏览器切换 Tab -->
				<div class="browser-tabs" v-if="browser_list.length">
					<span
						v-for="b in browser_list"
						:key="b.value"
						class="btab"
						:class="{active: browser_active === b.value}"
						@click="changeBrowser(b.value)"
					>
						{{ b.name }}
					</span>
				</div>

				<!-- 信息栏 -->
				<div class="detail-header">
					<div class="detail-title">{{ script_list[selectedIndex]?.name || '请选择脚本' }}</div>
					<div class="detail-meta">
						<span class="dm-item"><span class="dm-label">开始</span>{{ start_time }}</span>
						<span class="dm-item"><span class="dm-label">结束</span>{{ end_time }}</span>
						<span class="dm-item"><span class="dm-label">总数</span>{{ run_total }}</span>
						<span class="dm-item pass-text"><span class="dm-label">通过</span>{{ run_pass }}</span>
						<span class="dm-item fail-text"><span class="dm-label">失败</span>{{ run_fail }}</span>
	
						<span class="dm-item" v-if="pre_video">
							<el-button size="small" type="success" @click="view_video">▶ 视频</el-button>
						</span>
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
								v-for="(res, idx) in web_result"
								:key="idx"
								class="step-item"
								:class="res.status===1 ? 'step-pass' : 'step-fail'"
							>
								<div class="step-connector" v-if="idx < web_result.length - 1"></div>
								<div class="step-dot" :class="res.status===1 ? 'dot-s-pass' : 'dot-s-fail'">
									<span v-if="res.status===1">✓</span>
									<span v-else>✗</span>
								</div>
								<div class="step-body">
									<div class="step-name-row">
										<span class="step-name">{{ res.name }}</span>
										<span class="step-time">{{ res.create_time ? String(res.create_time).slice(11,19) : '' }}</span>
									</div>
									<div v-if="res.log" class="step-log-text">{{ res.log }}</div>
									<div class="step-action">
										<el-popover v-if="Object.keys(res.assert_result || {}).length" placement="right" :width="500" trigger="click">
											<template #reference>
												<el-button size="small" type="primary" plain>断言详情</el-button>
											</template>
											<div v-for="(item, i) in res.assert_result" :key="i" style="margin-bottom:4px">
												<span :style="item.result?.includes('失败') ? 'color:#ff4d4f' : 'color:#52c41a'">{{ '断言：' + item.result }}</span>
												<el-button v-if="item.img" link size="small" style="float:right" @click="pre_view(item.img)">查看截图</el-button>
											</div>
										</el-popover>
										<el-button v-if="res.before_img" size="small" plain @click="pre_view(res.before_img)">执行前</el-button>
										<el-button v-if="res.after_img" size="small" type="warning" plain @click="pre_view(res.after_img)">执行后</el-button>
									</div>
								</div>
							</div>
							<div v-if="!web_result.length" class="steps-empty">暂无执行步骤</div>
						</div>
						<el-image-viewer v-if="img_show" :url-list="pre_img" @close="close_img" />
					</div>

					<!-- 日志 -->
					<div class="log-panel">
						<div class="panel-title">
							<span class="panel-title-icon">📄</span> 执行日志
						</div>
						<div class="log-body">
							<div v-if="!web_result_log.length" class="log-empty">暂无日志</div>
							<div
								v-for="(log, idx) in web_result_log"
								:key="idx"
								class="log-line"
								:class="log.includes('失败') || log.includes('ERROR') ? 'log-err' : log.includes('成功') || log.includes('通过') ? 'log-ok' : ''"
							>{{ log }}</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { ArrowRight } from '@element-plus/icons-vue';
import { useWebManagementApi } from '/@/api/v1/web_management';
import { getBaseApiUrl } from '/@/utils/config';

const { get_web_result_report, get_web_result_detail } = useWebManagementApi();
const mediaUrl = (path: string) => path ? `${getBaseApiUrl()}${path}` : '';
const formatTime = (t: string) => t ? t.replace('T', ' ').slice(0, 19) : '-';

const loading = ref(false);
const result_id = ref('');
const menu_id = ref<any>(null);
const res_form = ref<any>({});
const script_active = ref('all');
const selectedIndex = ref(0);
const script_list = ref<any[]>([]);
const browser_show = [
	{ name: 'Chrome', value: 1 }, { name: 'Firefox', value: 2 },
	{ name: 'Edge', value: 3 }, { name: 'Safari', value: 4 },
];
const browser_list = ref<any[]>([]);
const browser_active = ref<any>(null);
const web_result_log = ref<any[]>([]);
const img_show = ref(false);
const pre_img = ref<string[]>([]);
const web_result = ref<any[]>([]);
const start_time = ref('');
const end_time = ref('');
const run_pass = ref(0);
const run_fail = ref(0);
const run_total = ref(0);
const pre_video = ref('');
const trace = ref('');

const passWidth = computed(() => {
	const t = res_form.value.total ?? 0;
	if (!t) return 0;
	return Math.round(((t - (res_form.value.total_fail ?? 0)) / t) * 100);
});
const failWidth = computed(() => {
	const t = res_form.value.total ?? 0;
	if (!t) return 0;
	return Math.round(((res_form.value.total_fail ?? 0) / t) * 100);
});

const get_result_report = async () => {
	loading.value = true;
	try {
		const route = useRoute();
		result_id.value = String((route.query.result_id || route.query.resultId || '') as any);
		if (!result_id.value) return;
		const res: any = await get_web_result_report({ result_id: result_id.value });
		const data = res?.data || {};
		res_form.value = data;
		const scripts = Array.isArray(data.script_list) ? data.script_list : [];
		const browsers = Array.isArray(data.browser_list) ? data.browser_list : [];
		script_list.value = scripts;
		browser_list.value = browsers.map((b: any) => browser_show.find((x) => x.value === b)).filter(Boolean) as any[];
		browser_active.value = browsers[0] ?? null;
		menu_id.value = scripts[0]?.id ?? null;
		if (browser_active.value != null && menu_id.value != null) await get_result_detail();
	} finally {
		loading.value = false;
	}
};

const get_result_detail = async () => {
	const res: any = await get_web_result_detail({ result_id: result_id.value, browser: browser_active.value, menu_id: menu_id.value });
	web_result.value = res.data.content;
	web_result_log.value = res.data.log;
	if (res.data.content.length) {
		start_time.value = formatTime(res.data.content[res.data.content.length - 1].create_time);
		end_time.value = formatTime(res.data.content[0].create_time);
	}
	run_pass.value = res.data.content.filter((i: any) => i.status === 1).length;
	run_fail.value = res.data.content.filter((i: any) => i.status === 0).length;
	run_total.value = run_pass.value + run_fail.value;
	trace.value = res.data.trace;
	pre_video.value = res.data.video;
};

const script_click = async (script: any, index: number) => {
	selectedIndex.value = index;
	menu_id.value = script.id;
	await get_result_detail();
};

const switchTab = (tab: string) => {
	script_active.value = tab;
	const all = res_form.value.script_list || [];
	if (tab === 'all') script_list.value = [...all];
	else if (tab === 'pass') script_list.value = all.filter((i: any) => i.status === 1);
	else script_list.value = all.filter((i: any) => i.status === 0);
};

const changeBrowser = async (val: any) => {
	browser_active.value = val;
	await get_result_detail();
};

const view_video = () => { if (pre_video.value) window.open(mediaUrl(pre_video.value)); };
const pre_view = (img: string) => { pre_img.value = [mediaUrl(img)]; img_show.value = true; };
const close_img = () => { img_show.value = false; };
const download_report = () => { if (trace.value) window.open(mediaUrl(trace.value)); };
const view_trace = () => { window.open('https://trace.playwright.dev/'); };

onMounted(() => { get_result_report(); });
</script>

<style scoped lang="scss">
.report-page { min-height: 100vh; background: #f0f2f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }

.report-header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 16px 24px; display: flex; align-items: center; justify-content: space-between; }
.report-header-brand { display: flex; align-items: center; gap: 10px; }
.brand-icon { font-size: 22px; }
.brand-name { font-size: 18px; font-weight: 700; color: #fff; letter-spacing: 1px; }
.brand-sub { font-size: 12px; color: rgba(255,255,255,.5); background: rgba(255,255,255,.1); padding: 2px 8px; border-radius: 10px; }
.report-header-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.meta-item { display: flex; align-items: center; gap: 4px; font-size: 13px; color: rgba(255,255,255,.85); }
.meta-label { color: rgba(255,255,255,.5); font-size: 11px; }
.meta-val { color: #fff; font-weight: 500; }
.meta-sep { color: rgba(255,255,255,.3); }

.report-summary { display: flex; align-items: center; gap: 20px; padding: 20px 24px; background: #fff; border-bottom: 1px solid #e8eaed; flex-wrap: wrap; }
.summary-donut { flex-shrink: 0; }
.donut-inner { display: flex; flex-direction: column; align-items: center; }
.donut-pct { font-size: 22px; font-weight: 700; color: #1a1a2e; }
.donut-label { font-size: 11px; color: #909399; }
.summary-cards { display: flex; gap: 12px; flex: 1; min-width: 0; flex-wrap: wrap; }
.scard { display: flex; align-items: center; gap: 12px; padding: 14px 18px; border-radius: 10px; flex: 1; min-width: 100px; }
.scard-total   { background: linear-gradient(135deg, #667eea, #764ba2); }
.scard-pass    { background: linear-gradient(135deg, #56ab2f, #a8e063); }
.scard-fail    { background: linear-gradient(135deg, #f7971e, #ffd200); }
.scard-browser { background: linear-gradient(135deg, #4facfe, #00f2fe); }
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

.report-body { display: flex; height: calc(100vh - 220px); min-height: 500px; }

.case-sidebar { width: 240px; flex-shrink: 0; background: #fff; border-right: 1px solid #e8eaed; display: flex; flex-direction: column; overflow: hidden; }
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
.case-item.case-pass.active { border-left-color: #52c41a; background: #f6ffed; }
.case-item.case-fail.active { border-left-color: #ff4d4f; background: #fff1f0; }
.case-status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dot-pass { background: #52c41a; }
.dot-fail { background: #ff4d4f; }
.case-info { flex: 1; min-width: 0; }
.case-name { font-size: 12px; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.case-arrow { font-size: 12px; color: #c0c4cc; flex-shrink: 0; }

.detail-panel { flex: 1; min-width: 0; display: flex; flex-direction: column; overflow: hidden; }
.browser-tabs { display: flex; gap: 0; background: #fff; border-bottom: 1px solid #e8eaed; padding: 0 16px; flex-shrink: 0; }
.btab { padding: 10px 16px; font-size: 13px; cursor: pointer; color: #606266; border-bottom: 2px solid transparent; transition: all .15s; user-select: none; }
.btab:hover { color: #409eff; }
.btab.active { color: #409eff; border-bottom-color: #409eff; font-weight: 600; }
.detail-header { padding: 12px 20px; background: #fff; border-bottom: 1px solid #e8eaed; flex-shrink: 0; }
.detail-title { font-size: 15px; font-weight: 600; color: #1a1a2e; margin-bottom: 6px; }
.detail-meta { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 12px; }
.dm-item { display: flex; align-items: center; gap: 4px; color: #606266; }
.dm-label { color: #909399; }
.pass-text { color: #52c41a; font-weight: 600; }
.fail-text { color: #ff4d4f; font-weight: 600; }
.detail-content { flex: 1; min-height: 0; display: flex; overflow: hidden; }

.steps-panel { width: 380px; flex-shrink: 0; border-right: 1px solid #e8eaed; display: flex; flex-direction: column; overflow: hidden; background: #fff; }
.panel-title { padding: 10px 16px; font-size: 13px; font-weight: 600; color: #1a1a2e; border-bottom: 1px solid #f0f0f0; display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.panel-title-icon { font-size: 14px; }
.steps-list { flex: 1; overflow-y: auto; padding: 12px 16px; }
.step-item { display: flex; gap: 12px; position: relative; padding-bottom: 16px; }
.step-item:last-child { padding-bottom: 0; }
.step-connector { position: absolute; left: 11px; top: 24px; bottom: 0; width: 2px; background: #e8eaed; }
.step-dot { width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; z-index: 1; }
.dot-s-pass { background: #f6ffed; border: 2px solid #52c41a; color: #52c41a; }
.dot-s-fail { background: #fff1f0; border: 2px solid #ff4d4f; color: #ff4d4f; }
.step-body { flex: 1; min-width: 0; }
.step-name-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.step-name { font-size: 13px; font-weight: 500; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.step-time { font-size: 11px; color: #c0c4cc; flex-shrink: 0; margin-left: 8px; }
.step-log-text { font-size: 12px; color: #909399; margin-bottom: 6px; word-break: break-all; }
.step-action { display: flex; flex-wrap: wrap; gap: 4px; }
.steps-empty { text-align: center; color: #c0c4cc; padding: 40px 0; font-size: 13px; }

.log-panel { flex: 1; min-width: 0; display: flex; flex-direction: column; overflow: hidden; background: #1e1e1e; }
.log-body { flex: 1; overflow-y: auto; padding: 10px 14px; font-family: 'Consolas','Monaco',monospace; }
.log-empty { color: #555; font-size: 13px; padding: 20px 0; }
.log-line { font-size: 12px; line-height: 1.7; color: #d4d4d4; white-space: pre-wrap; word-break: break-all; }
.log-ok  { color: #4ec9b0; }
.log-err { color: #f48771; }
.log-panel .panel-title { background: #252526; border-bottom-color: #3c3c3c; color: #d4d4d4; }
</style>
