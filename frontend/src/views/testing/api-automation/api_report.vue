<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { CircleCheck, CircleClose, View } from '@element-plus/icons-vue';
import {
	get_api_script_report_log,
	get_api_script_result_detail,
	get_api_script_result_detail_list,
	get_api_script_result_report_list,
	api_env,
	api_db_list,
	api_tree_list,
} from '/@/api/v1/api_automation';
import ApiDetail from './api_detail.vue';

const route = useRoute();
const result_id = ref<any>('');
const result_form = ref<any>({
	result: { percent: 0, pass: 0, fail: 0 },
});
const loading = ref(false);
const script_active = ref('all');
const script_list = ref<any[]>([]);
const menu_id = ref<any>('');
const selectedIndex = ref(0);
const script_result_list = ref<any[]>([]);
const res_script_result = ref<any[]>([]);
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

const buildDetailApiData = (d: any) => {
	// ApiDetail 组件依赖 api_id/id 触发初始化；这里给一个稳定的兜底值即可
	const stableId = d?.api_id ?? d?.id ?? d?.uuid ?? d?.menu_id ?? `${result_id.value ?? ''}-${d?.name ?? ''}`;
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
		await get_script_result_detail_list();
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

const get_script_result_detail_list = async () => {
	if (!menu_id.value || !result_id.value) return;
	const res: any = await get_api_script_result_detail_list({
		menu_id: String(menu_id.value),
		result_id: Number(result_id.value),
	});
	script_result_list.value = res?.data ?? [];
};

const get_api_tree_list = async () => {
	const res: any = await api_tree_list({});
	tree_list.value = res?.data ?? [];
};

const handleTabClick = (tab: any) => {
	const name = tab?.props?.name;
	if (name === 'all') script_list.value = [...res_script_result.value];
	else if (name === 'pass') script_list.value = res_script_result.value.filter((i: any) => i.status === 1);
	else if (name === 'fail') script_list.value = res_script_result.value.filter((i: any) => i.status === 0);
};

const script_click = async (script: any, index: number) => {
	selectedIndex.value = index;
	menu_id.value = script.uuid ?? script.menu_id ?? script.id;
	name.value = script.name ?? '';
	await get_script_result_detail_list();
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
	run_count.value = data.length;
	run_fail.value = data.filter((i: any) => i.status === 0).length;
	if (data.length > 0) {
		start_time.value = data[data.length - 1].create_time ?? '';
		end_time.value = data[0].create_time ?? '';
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

const getIcon = (status: number) => (status === 1 ? CircleCheck : CircleClose);
const colors = (status: number) => (status === 1 ? '#0bbd87' : '#d70e0e');
const get_card_style = (status: number) =>
	status === 0
		? 'border-radius: 10px; border-color: #f3050d; text-align: left;'
		: 'border-radius: 10px; border-color: #67c23ae0; text-align: left;';
const get_colors = (status: number) => (status === 1 ? 'color: #0bbd87' : 'color: #d70e0e');
const get_log_style = (msg: string) => (msg && msg.includes('失败') ? 'color: #d70e0e' : '');

onMounted(() => {
	get_env_list();
	get_api_tree_list();
	get_script_result();
});
</script>

<template>
	<div class="api-report-page" v-loading="loading" element-loading-text="加载中...">
		<el-card shadow="hover" class="report-card">
			<div class="report-summary">
				<div class="summary-block">
					<el-descriptions border :column="1" size="small">
						<el-descriptions-item label="任务名称">{{ result_form.name }}</el-descriptions-item>
						<el-descriptions-item label="执行人">{{ result_form.username }}</el-descriptions-item>
						<el-descriptions-item label="开始时间">
							{{ result_form.start_time ? String(result_form.start_time).replace('T', ' ') : '-' }}
						</el-descriptions-item>
						<el-descriptions-item label="结束时间">
							{{ result_form.end_time ? String(result_form.end_time).replace('T', ' ') : '-' }}
						</el-descriptions-item>
					</el-descriptions>
				</div>
				<div class="summary-block stats">
					<div class="stat-card stat-card--blue">
						<div class="stat-label">接口总数</div>
						<div class="stat-value">{{ result_form.result?.total ?? 0 }}</div>
					</div>
					<div class="stat-card stat-card--green">
						<div class="stat-label">通过率</div>
						<div class="stat-value">{{ (result_form.result?.percent ?? 0) + '%' }}</div>
					</div>
					<div class="stat-card stat-card--teal">
						<div class="stat-label">通过数</div>
						<div class="stat-value">{{ result_form.result?.pass ?? 0 }}</div>
					</div>
					<div class="stat-card stat-card--red">
						<div class="stat-label">失败数</div>
						<div class="stat-value">{{ result_form.result?.fail ?? 0 }}</div>
					</div>
				</div>
				<div class="summary-block progress-block">
					<el-progress type="dashboard" :percentage="result_form.result?.percent ?? 0" status="success">
						<template #default="{ percentage }">
							<span class="percentage-value">{{ percentage }}%</span>
							<span class="percentage-label">通过率</span>
						</template>
					</el-progress>
				</div>
			</div>
		</el-card>

		<el-card shadow="hover" class="report-body">
			<div class="report-layout">
				<div class="script-sidebar">
					<el-tabs v-model="script_active" @tab-click="handleTabClick">
						<el-tab-pane label="全部" name="all">
							<div v-for="(script, index) in script_list" :key="index" class="script-item">
								<div
									:style="get_card_style(script.status)"
									:class="{ highlight: (script.uuid || script.menu_id || script.id) === menu_id }"
									class="script-card"
								>
									<el-button
										v-if="script.status === 0"
										text
										:icon="CircleClose"
										class="script-btn fail"
										@click="script_click(script, index)"
									>
										{{ script.name + '(通过数' + script.pass + '，失败数' + script.fail + ')' }}
									</el-button>
									<el-button
										v-else
										text
										:icon="CircleCheck"
										class="script-btn pass"
										@click="script_click(script, index)"
									>
										{{ script.name + '(通过数' + script.pass + '，失败数' + script.fail + ')' }}
									</el-button>
								</div>
							</div>
						</el-tab-pane>
						<el-tab-pane label="通过" name="pass">
							<div v-for="(script, index) in script_list" :key="index" class="script-item">
								<div
									v-if="script.status === 1"
									:style="get_card_style(1)"
									:class="{ highlight: (script.uuid || script.menu_id || script.id) === menu_id }"
									class="script-card"
								>
									<el-button text :icon="CircleCheck" class="script-btn pass" @click="script_click(script, index)">
										{{ script.name + '(通过数' + script.pass + '，失败数' + script.fail + ')' }}
									</el-button>
								</div>
							</div>
						</el-tab-pane>
						<el-tab-pane label="失败" name="fail">
							<div v-for="(script, index) in script_list" :key="index" class="script-item">
								<div
									v-if="script.status === 0"
									:style="get_card_style(0)"
									:class="{ highlight: (script.uuid || script.menu_id || script.id) === menu_id }"
									class="script-card"
								>
									<el-button text :icon="CircleClose" class="script-btn fail" @click="script_click(script, index)">
										{{ script.name + '(通过数' + script.pass + '，失败数' + script.fail + ')' }}
									</el-button>
								</div>
							</div>
						</el-tab-pane>
					</el-tabs>
				</div>
				<div class="report-main">
					<!-- 执行信息栏（与 web_report 同风格） -->
					<div class="info-bar" style="margin-bottom: 10px">
						<span class="info-item"><span class="info-label">任务名称</span>{{ name }}</span>
						<span class="info-item"><span class="info-label">执行环境</span>{{ run_env }}</span>
						<span class="info-item"><span class="info-label">开始时间</span>{{ start_time ? String(start_time).replace('T', ' ') : '-' }}</span>
						<span class="info-item"><span class="info-label">结束时间</span>{{ end_time ? String(end_time).replace('T', ' ') : '-' }}</span>
						<span class="info-item"><span class="info-label">总数</span>{{ run_count }}</span>
						<span class="info-item"><span class="info-label">通过</span><span style="color:#0bbd87;font-weight:600">{{ run_count - run_fail }}</span></span>
						<span class="info-item"><span class="info-label">失败</span><span style="color:#f3050d;font-weight:600">{{ run_fail }}</span></span>
					</div>
					<el-card shadow="hover" class="timeline-log-card">
						<div class="timeline-log-layout">
							<div class="panel-box timeline-col">
								<el-timeline>
									<el-timeline-item
										v-for="(res, idx) in run_result_list"
										:key="idx"
										:icon="getIcon(res.status)"
										:color="colors(res.status)"
										:timestamp="res.create_time ? '执行时间：' + String(res.create_time).replace('T', ' ') : ''"
										placement="top"
									>
										<div :class="res.status === 1 ? 'step-card step-card--pass' : 'step-card step-card--fail'">
											<div class="step-name">
												<span v-if="res.name !== '执行结束'">接口：{{ res.name }}</span>
												<span v-else>{{ res.name }}</span>
											</div>
											<div class="step-log" v-if="res.name !== '执行结束' && res.res">
												<span class="mr">code：{{ res.res.code }}</span>
												<span class="mr">size：{{ res.res.size }}B</span>
												<span>time：{{ res.res.res_time }}ms</span>
											</div>
											<div class="step-actions">
												<el-button
													v-if="res.name !== '执行结束'"
													class="action-btn action-btn--purple"
													size="small"
													:icon="View"
													@click="view_result(res)"
												>
													查看详情
												</el-button>
											</div>
										</div>
									</el-timeline-item>
								</el-timeline>
							</div>
							<div class="panel-box log-col">
								<div v-if="!run_result_log.length" style="color: #999">暂无执行日志</div>
								<div v-for="(log, idx) in run_result_log" :key="idx" class="log-line" :style="get_log_style(log)">{{ log }}</div>
							</div>
						</div>
					</el-card>
				</div>
			</div>
		</el-card>

		<el-drawer v-model="detail_drawer" title="请求详情" size="1100" destroy-on-close>
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

<style scoped lang="scss">
.api-report-page {
	padding: 10px;
}
.report-card {
	margin-bottom: 10px;
}
.report-summary {
	display: flex;
	flex-wrap: wrap;
	gap: 10px;
	padding: 10px 0;
}
.summary-block {
	flex: 0 0 auto;
}
.summary-block.stats {
	flex: 1;
	display: flex;
	gap: 10px;
	align-items: stretch;
	min-width: 0;
}
.progress-block {
	display: flex;
	justify-content: center;
	align-items: center;
	padding-left: 20px;
}
.percentage-value {
	display: block;
	font-size: 24px;
}
.percentage-label {
	font-size: 12px;
	color: #909399;
}
.report-body {
	margin-top: 10px;
}
.report-layout {
	display: flex;
	gap: 10px;
}
.script-sidebar {
	width: 180px;
	flex-shrink: 0;
	max-height: 750px;
	overflow: auto;
}
.script-item {
	margin-bottom: 10px;
}
.script-btn {
	padding: 0;
	width: 100%;
	justify-content: flex-start;
	white-space: normal;
	height: auto;
	line-height: 1.4;
}
.script-btn.pass { color: #0bbd87; }
.script-btn.fail { color: #f3050d; }
.report-main {
	flex: 1;
	min-width: 0;
}
.timeline-log-card {
	min-height: 520px;
}
.timeline-log-layout {
	display: flex;
	gap: 10px;
}
.timeline-col {
	width: 340px;
	flex-shrink: 0;
	height: 600px;
	overflow-y: auto;
}
.mr { margin-right: 10px; }
.log-col {
	flex: 1;
	height: 600px;
	overflow-y: auto;
}

/* 统计卡片 — 与 web_report 同风格 */
.stat-card {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  border-radius: 8px; padding: 16px 10px; min-width: 0;
  .stat-label { font-size: 13px; color: rgba(255,255,255,0.85); margin-bottom: 8px; white-space: nowrap }
  .stat-value { font-size: 32px; font-weight: 700; color: #fff; line-height: 1 }
}
.stat-card--blue  { background: linear-gradient(135deg, #4096ff, #1677ff) }
.stat-card--green { background: linear-gradient(135deg, #52c41a, #389e0d) }
.stat-card--teal  { background: linear-gradient(135deg, #13c2c2, #08979c) }
.stat-card--red   { background: linear-gradient(135deg, #ff4d4f, #cf1322) }

/* 执行信息栏 */
.info-bar {
  display: flex; flex-wrap: wrap; gap: 6px 16px;
  align-items: center; padding: 10px 12px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
}
.info-item { display: flex; align-items: center; gap: 4px; white-space: nowrap; font-size: 13px; color: var(--el-text-color-primary) }
.info-label { color: var(--el-text-color-secondary); font-size: 12px; margin-right: 2px }

/* 步骤卡片 */
.step-card {
  border-radius: 6px; padding: 8px 10px; border-left: 3px solid;
  background: var(--el-bg-color);
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.step-card--pass { border-left-color: #0bbd87 }
.step-card--fail { border-left-color: #f3050d }
.step-name { font-size: 13px; font-weight: 600; margin-bottom: 4px; color: var(--el-text-color-primary) }
.step-log  { font-size: 12px; color: var(--el-text-color-secondary); margin-bottom: 6px; word-break: break-all }
.step-actions { display: flex; flex-wrap: wrap; gap: 4px }

/* 操作按钮 */
.action-btn { border-radius: 4px !important }
.action-btn--purple { color: #722ed1 !important; border-color: #722ed1 !important }

/* 面板容器 */
.panel-box {
  border: 1px solid var(--el-border-color);
  border-radius: 6px; padding: 10px;
  background: var(--el-bg-color);
}

/* 脚本列表项 */
.script-card { border: 1px solid var(--el-border-color); padding: 4px 6px; border-radius: 6px }
.highlight { background-color: rgba(182, 230, 239, 0.25) }

/* 日志行 */
.log-line { font-size: 12px; line-height: 1.8; padding: 1px 0; color: var(--el-text-color-primary) }
</style>
