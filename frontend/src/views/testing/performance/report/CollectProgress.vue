<template>
	<!-- 报告收集进度抽屉，通过 SSE 实时展示四步收集流程 -->
	<el-drawer
		v-model="visible"
		title="报告收集进度"
		direction="rtl"
		:size="drawerSize"
		:close-on-click-modal="false"
		:destroy-on-close="false"
		@close="handleClose"
	>
		<div class="collect-drawer-body" v-if="currentReport">
			<!-- 报告基本信息 -->
			<div class="report-info">
				<div class="report-name">{{ currentReport.report_name }}</div>
				<div class="report-scene">场景：{{ currentReport.scenario_name }}</div>
				<div v-if="plan" class="report-plan-row">
					<el-tag size="small" effect="plain" :type="plan === 'a' ? 'primary' : 'success'">
						{{ plan === 'a' ? '方案A · 单机直传（执行机 → Minio）' : '方案B · 平台中转（执行机 → 平台 → Minio）' }}
					</el-tag>
				</div>
			</div>

			<!-- 整体进度条（置顶） -->
			<div class="progress-bar-wrapper">
				<el-progress
					:percentage="currentState.pct || 0"
					:status="progressStatus"
					:stroke-width="8"
					striped
					:striped-flow="currentState.status === 'running'"
					:duration="10"
				/>
			</div>

			<!-- 步骤折叠面板列表（方案A时隐藏Step3） -->
			<div class="steps-wrapper">
				<div
					v-for="s in visibleSteps"
					:key="s.step"
					class="step-panel"
					:class="getStepPanelClass(s.step)"
				>
					<!-- 面板头：图标 + 步骤名 + 百分比 / 展开箭头 -->
					<div
						class="step-header"
						:class="{ 'step-header--clickable': isDoneStep(s.step) && !isRunningStep(s.step) }"
						@click="toggleDone(s.step)"
					>
						<div class="step-icon">
							<el-icon v-if="isRunningStep(s.step)" class="rotating"><ele-Loading /></el-icon>
							<el-icon v-else-if="isDoneStep(s.step)" class="icon-done"><ele-CircleCheckFilled /></el-icon>
							<el-icon v-else-if="isFailedStep(s.step)" class="icon-failed"><ele-CircleCloseFilled /></el-icon>
							<el-icon v-else class="icon-wait"><ele-Clock /></el-icon>
						</div>
						<div class="step-name">
							{{ s.name }}
							<span v-if="s.step === 1 && plan" class="step-plan-label">{{ plan === 'a' ? '执行机直传' : '平台中转' }}</span>
							<span v-else-if="s.step === 2 && plan" class="step-plan-label">{{ plan === 'a' ? '方案A' : '方案B' }}</span>
							<span v-else-if="s.step === 4 && plan" class="step-plan-label">{{ plan === 'a' ? '执行机直传 MinIO' : '平台中转上传' }}</span>
							<span v-else-if="s.planLabel && plan" class="step-plan-label">（{{ s.planLabel }}）</span>
						</div>
						<div class="step-pct" v-if="isRunningStep(s.step)">{{ currentState.pct }}%</div>
						<!-- 已完成步骤显示折叠/展开箭头 -->
						<el-icon
							v-if="isDoneStep(s.step) && !isRunningStep(s.step)"
							class="step-toggle-icon"
							:class="{ 'step-toggle-icon--open': expandedDone.has(s.step) }"
						>
							<ele-ArrowDown />
						</el-icon>
					</div>

					<!-- 面板体（仅展开中/失败步骤显示） -->
					<Transition name="step-expand">
						<div v-if="isExpandedStep(s.step)" class="step-body">
							<!-- 已完成步骤取快照数据；运行中/失败步骤取实时数据 -->
							<template v-if="isDoneStep(s.step) && !isRunningStep(s.step)">
								<!-- 无快照（打开弹窗时收集已结束，SSE 仅下发终态）：降级提示 -->
								<div v-if="!stepSnapshots[s.step]" class="step-no-detail">步骤已完成（打开弹窗时收集已结束，无过程详情）</div>
								<!-- done 展开：用快照 detail -->
								<div
									v-if="stepSnapshots[s.step]?.detail"
									class="step-detail"
								>{{ stepSnapshots[s.step].detail }}</div>

								<!-- Step 1 done：连接列表（快照） -->
								<div v-if="s.step === 1 && stepSnapshots[1]?.sub_items?.connections?.length" class="conn-list">
									<div
										v-for="(c, idx) in stepSnapshots[1].sub_items.connections"
										:key="idx"
										class="conn-item"
										:class="`conn-item--${c.status}`"
									>
										<el-icon v-if="c.status === 'running'" class="rotating w-icon"><ele-Loading /></el-icon>
										<el-icon v-else-if="c.status === 'done'" class="w-icon icon-done"><ele-CircleCheckFilled /></el-icon>
										<el-icon v-else class="w-icon icon-failed"><ele-CircleCloseFilled /></el-icon>
										<span class="w-conn-name">{{ c.name }}</span>
										<span class="w-conn-url">{{ c.url }}</span>
										<el-tooltip v-if="c.status === 'failed' && c.detail" :content="c.detail" placement="top" :show-after="0">
											<span class="w-conn-error">{{ c.detail }}</span>
										</el-tooltip>
									</div>
								</div>

								<!-- Step 2 done：打包子步骤（快照） -->
								<div v-if="s.step === 2 && plan === 'a' && stepSnapshots[2]?.sub_items?.report_zip" class="zip-list">
									<div
										v-for="key in (['report_zip','log_zip','jtl_zip'] as Array<'report_zip'|'log_zip'|'jtl_zip'>)"
										:key="key"
										class="zip-item"
										:class="`zip-item--${stepSnapshots[2].sub_items[key]?.status ?? 'pending'}`"
									>
										<el-icon v-if="stepSnapshots[2].sub_items[key]?.status === 'running'" class="rotating w-icon"><ele-Loading /></el-icon>
										<el-icon v-else-if="stepSnapshots[2].sub_items[key]?.status === 'done'" class="w-icon icon-done"><ele-CircleCheckFilled /></el-icon>
										<el-icon v-else-if="stepSnapshots[2].sub_items[key]?.status === 'skip'" class="w-icon icon-skip"><ele-Remove /></el-icon>
										<el-icon v-else class="w-icon icon-wait"><ele-Clock /></el-icon>
										<span class="w-ip">{{ key === 'report_zip' ? 'HTML报告' : key === 'log_zip' ? 'JMeter日志' : 'JTL结果' }}</span>
										<span v-if="stepSnapshots[2].sub_items[key]?.detail" class="w-detail">{{ stepSnapshots[2].sub_items[key].detail }}</span>
									</div>
								</div>

								<!-- Step 3 done：master/worker（快照） -->
								<div v-if="s.step === 3 && stepSnapshots[3]?.sub_items" class="worker-list">
									<div
										v-if="stepSnapshots[3].sub_items.master"
										class="worker-item"
										:class="`worker-item--${stepSnapshots[3].sub_items.master.status}`"
									>
										<el-icon v-if="stepSnapshots[3].sub_items.master.status==='running'" class="rotating w-icon"><ele-Loading /></el-icon>
										<el-icon v-else-if="stepSnapshots[3].sub_items.master.status==='done'" class="w-icon icon-done"><ele-CircleCheckFilled /></el-icon>
										<el-icon v-else class="w-icon icon-failed"><ele-CircleCloseFilled /></el-icon>
										<span class="w-ip">执行机（主节点）</span>
										<span v-if="stepSnapshots[3].sub_items.master.detail" class="w-detail">{{ stepSnapshots[3].sub_items.master.detail }}</span>
									</div>
									<div
										v-for="(w, idx) in stepSnapshots[3].sub_items.workers"
										:key="idx"
										class="worker-item"
										:class="`worker-item--${w.status}`"
									>
										<el-icon v-if="w.status==='running'" class="rotating w-icon"><ele-Loading /></el-icon>
										<el-icon v-else-if="w.status==='done'" class="w-icon icon-done"><ele-CircleCheckFilled /></el-icon>
										<el-icon v-else-if="w.status==='failed'" class="w-icon icon-failed"><ele-CircleCloseFilled /></el-icon>
										<el-icon v-else class="w-icon icon-wait"><ele-Clock /></el-icon>
										<span class="w-ip">Worker-{{ Number(idx) + 1 }}（{{ w.ip }}）</span>
										<span v-if="w.detail" class="w-detail">{{ w.detail }}</span>
									</div>
								</div>

								<!-- Step 4 done：上传子步骤（快照） -->
								<div v-if="s.step === 4 && stepSnapshots[4]?.sub_items" class="upload-list">
									<div
										v-for="key in (['report','log','jtl'] as Array<'report'|'log'|'jtl'>)"
										:key="key"
										class="upload-item"
										:class="`upload-item--${stepSnapshots[4].sub_items[key]?.status ?? 'pending'}`"
									>
										<el-icon v-if="stepSnapshots[4].sub_items[key]?.status==='running'" class="rotating w-icon"><ele-Loading /></el-icon>
										<el-icon v-else-if="stepSnapshots[4].sub_items[key]?.status==='done'" class="w-icon icon-done"><ele-CircleCheckFilled /></el-icon>
										<el-icon v-else-if="stepSnapshots[4].sub_items[key]?.status==='skip'" class="w-icon icon-skip"><ele-Remove /></el-icon>
										<el-icon v-else class="w-icon icon-wait"><ele-Clock /></el-icon>
										<span class="w-ip">{{ key === 'report' ? 'HTML报告' : key === 'log' ? 'JMeter日志' : 'JTL结果' }}</span>
										<span v-if="stepSnapshots[4].sub_items[key]?.detail" class="w-detail">{{ stepSnapshots[4].sub_items[key].detail }}</span>
									</div>
								</div>
							</template>

							<!-- 运行中 / 失败步骤：实时数据 -->
							<template v-else>
								<!-- 通用 detail 文本 -->
								<div
									v-if="currentState.detail"
									class="step-detail"
									:class="{ 'step-detail--failed': isFailedStep(s.step) }"
								>{{ currentState.detail }}</div>

								<!-- Step 1：连接列表 -->
								<div v-if="s.step === 1 && currentState.sub_items?.connections?.length" class="conn-list">
									<div
										v-for="(c, idx) in currentState.sub_items.connections"
										:key="idx"
										class="conn-item"
										:class="`conn-item--${c.status}`"
									>
										<el-icon v-if="c.status === 'running'" class="rotating w-icon"><ele-Loading /></el-icon>
										<el-icon v-else-if="c.status === 'done'" class="w-icon icon-done"><ele-CircleCheckFilled /></el-icon>
										<el-icon v-else class="w-icon icon-failed"><ele-CircleCloseFilled /></el-icon>
										<span class="w-conn-name">{{ c.name }}</span>
										<span class="w-conn-url">{{ c.url }}</span>
										<el-tooltip v-if="c.status === 'failed' && c.detail" :content="c.detail" placement="top" :show-after="0">
											<span class="w-conn-error">{{ c.detail }}</span>
										</el-tooltip>
									</div>
								</div>

								<!-- Step 2：打包子步骤（方案A显示3个zip，方案B只有detail） -->
								<div v-if="s.step === 2 && plan === 'a' && currentState.sub_items?.report_zip" class="zip-list">
									<div
										v-for="item in step2ZipItems"
										:key="item.key"
										class="zip-item"
										:class="`zip-item--${item.status}`"
									>
										<el-icon v-if="item.status === 'running'" class="rotating w-icon"><ele-Loading /></el-icon>
										<el-icon v-else-if="item.status === 'done'" class="w-icon icon-done"><ele-CircleCheckFilled /></el-icon>
										<el-icon v-else-if="item.status === 'skip'" class="w-icon icon-skip"><ele-Remove /></el-icon>
										<el-icon v-else class="w-icon icon-wait"><ele-Clock /></el-icon>
										<span class="w-ip">{{ item.label }}</span>
										<span v-if="item.status === 'running'" class="w-detail">打包中...</span>
										<span v-else-if="item.detail" class="w-detail">{{ item.detail }}</span>
									</div>
								</div>

								<!-- Step 3：master + worker 子状态 -->
								<div v-if="s.step === 3 && currentState.sub_items" class="worker-list">
									<div
										v-if="currentState.sub_items.master"
										class="worker-item"
										:class="`worker-item--${currentState.sub_items.master.status}`"
									>
										<el-icon v-if="currentState.sub_items.master.status === 'running'" class="rotating w-icon"><ele-Loading /></el-icon>
										<el-icon v-else-if="currentState.sub_items.master.status === 'done'" class="w-icon icon-done"><ele-CircleCheckFilled /></el-icon>
										<el-icon v-else class="w-icon icon-failed"><ele-CircleCloseFilled /></el-icon>
										<span class="w-ip">执行机（主节点）</span>
										<span v-if="currentState.sub_items.master.detail" class="w-detail">{{ currentState.sub_items.master.detail }}</span>
									</div>
									<div
										v-for="(w, idx) in currentState.sub_items.workers"
										:key="idx"
										class="worker-item"
										:class="`worker-item--${w.status}`"
									>
										<el-icon v-if="w.status === 'running'" class="rotating w-icon"><ele-Loading /></el-icon>
										<el-icon v-else-if="w.status === 'done'" class="w-icon icon-done"><ele-CircleCheckFilled /></el-icon>
										<el-icon v-else-if="w.status === 'failed'" class="w-icon icon-failed"><ele-CircleCloseFilled /></el-icon>
										<el-icon v-else class="w-icon icon-wait"><ele-Clock /></el-icon>
										<span class="w-ip">Worker-{{ Number(idx) + 1 }}（{{ w.ip }}）</span>
										<span v-if="w.detail" class="w-detail">{{ w.detail }}</span>
									</div>
								</div>

								<!-- Step 4：report / log / jtl 上传子步骤 -->
								<div v-if="s.step === 4 && currentState.sub_items" class="upload-list">
									<div
										v-for="item in step4UploadItems"
										:key="item.key"
										class="upload-item"
										:class="`upload-item--${item.status}`"
									>
										<el-icon v-if="item.status === 'running'" class="rotating w-icon"><ele-Loading /></el-icon>
										<el-icon v-else-if="item.status === 'done'" class="w-icon icon-done"><ele-CircleCheckFilled /></el-icon>
										<el-icon v-else-if="item.status === 'skip'" class="w-icon icon-skip"><ele-Remove /></el-icon>
										<el-icon v-else class="w-icon icon-wait"><ele-Clock /></el-icon>
										<span class="w-ip">{{ item.label }}</span>
										<span v-if="item.status === 'running' && !item.detail" class="w-detail">上传中...</span>
										<span v-else-if="item.detail" class="w-detail">{{ item.detail }}</span>
									</div>
								</div>
							</template>
						</div>
					</Transition>
				</div>
			</div>

			<!-- 中断/失败时 step=0（步骤行无高亮）需在步骤列表下方单独展示 detail -->
			<div
				v-if="currentState.status === 'interrupted' && currentState.detail"
				class="terminal-notice terminal-notice--interrupted"
			>
				{{ currentState.detail }}
			</div>
			<div
				v-else-if="currentState.status === 'failed' && currentState.step === 0 && currentState.detail"
				class="terminal-notice terminal-notice--failed"
			>
				{{ currentState.detail }}
			</div>
		</div>

		<div v-else class="collect-empty">请从报告列表选择一条收集中的记录</div>

		<template #footer>
			<el-button @click="close">关闭</el-button>
		</template>
	</el-drawer>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { usePerformanceApi } from '/@/api/v1/performance';

const perfApi = usePerformanceApi();

// ======================== 步骤定义 ========================
const STEPS = [
	{ step: 1, name: 'SSH连接' },
	{ step: 2, name: '远端打包' },
	{ step: 3, name: '文件下载', planLabel: '方案B' },
	{ step: 4, name: '打包上传' },
];

// ======================== 状态 ========================
const visible       = ref(false);
const currentReport = ref<any>(null);
// 方案标志：'a'=执行机直传MinIO（单机），'b'=平台中转，null=未知
const plan          = ref<'a' | 'b' | null>(null);

// 用户手动展开的已完成步骤集合（done 面板默认折叠，点击可展开）
const expandedDone = ref<Set<number>>(new Set());
// 每步完成时的状态快照，供折叠后重新展开时显示历史详情
const stepSnapshots = ref<Record<number, { detail: string; sub_items?: any }>>({});

// sessionStorage 持久化：按报告 ID 缓存快照，关闭/重开抽屉后仍可查看过程详情
const SNAPSHOT_KEY = (id: number) => `perf_snapshots_${id}`;
function saveSnapshots(id: number) {
	try { sessionStorage.setItem(SNAPSHOT_KEY(id), JSON.stringify(stepSnapshots.value)); } catch { /* ignore */ }
}
function loadSnapshots(id: number): Record<number, { detail: string; sub_items?: any }> {
	try {
		const raw = sessionStorage.getItem(SNAPSHOT_KEY(id));
		return raw ? JSON.parse(raw) : {};
	} catch { return {}; }
}

const currentState = ref<{
	step: number;
	pct: number;
	step_name: string;
	detail: string;
	status: 'running' | 'done' | 'failed' | 'interrupted';
	plan?: 'a' | 'b';
	sub_items?: {
		connections?: Array<{ name: string; url: string; status: string; detail: string }>;
		report_zip?: { status: string; detail?: string };
		log_zip?:    { status: string; detail?: string };
		jtl_zip?:    { status: string; detail?: string };
		master?:     { status: string; detail?: string };
		workers?:    Array<{ ip: string; status: string; detail: string }>;
		report?:     { status: string; detail?: string };
		log?:        { status: string; detail?: string };
		jtl?:        { status: string; detail?: string };
	};
}>({
	step: 0, pct: 0, step_name: '', detail: '', status: 'running',
});

let abortCtrl: AbortController | null = null;

// ======================== 对外方法 ========================

function open(report: any) {
	currentReport.value = report;
	currentState.value  = { step: 0, pct: 0, step_name: '', detail: '等待收集开始...', status: 'running' };
	plan.value          = null;
	expandedDone.value  = new Set();
	stepSnapshots.value = loadSnapshots(report.id);
	visible.value       = true;
	startSSE(report.id);
}

function close() {
	visible.value = false;
}

defineExpose({ open, close });

// ======================== SSE ========================

async function startSSE(reportId: number) {
	stopSSE();
	abortCtrl = new AbortController();

	let resp: Response;
	try {
		resp = await perfApi.collectProcessStream(reportId, abortCtrl.signal);
	} catch {
		return;
	}

	if (!resp.body) return;
	const reader  = resp.body.getReader();
	const decoder = new TextDecoder();
	let   buf     = '';

	while (true) {
		let chunk: ReadableStreamReadResult<Uint8Array>;
		try {
			chunk = await reader.read();
		} catch {
			break;
		}
		if (chunk.done) break;

		buf += decoder.decode(chunk.value, { stream: true });
		const lines = buf.split('\n');
		buf = lines.pop() ?? '';

		for (const line of lines) {
			if (!line.startsWith('data:')) continue;
			try {
				const evt = JSON.parse(line.slice(5).trim());
				if (evt.plan) plan.value = evt.plan as 'a' | 'b';

				const prevStep = currentState.value.step;
				const newStep  = evt.step ?? prevStep;

				// 步骤切换时，快照上一步最终状态供折叠后展开查看
				if (newStep !== prevStep && prevStep > 0) {
					stepSnapshots.value = {
						...stepSnapshots.value,
						[prevStep]: {
							detail:    currentState.value.detail,
							sub_items: currentState.value.sub_items,
						},
					};
					if (currentReport.value?.id) saveSnapshots(currentReport.value.id);
				}

				currentState.value = {
					step:      newStep,
					pct:       evt.pct       ?? currentState.value.pct,
					step_name: evt.step_name ?? currentState.value.step_name,
					detail:    evt.detail    ?? '',
					status:    evt.status    ?? 'running',
					plan:      evt.plan      ?? currentState.value.plan,
					sub_items: evt.sub_items ?? currentState.value.sub_items,
				};

				// 全部完成时将最后一步也存档
				if (evt.status === 'done' && newStep > 0) {
					stepSnapshots.value = {
						...stepSnapshots.value,
						[newStep]: { detail: evt.detail ?? '', sub_items: evt.sub_items ?? currentState.value.sub_items },
					};
					if (currentReport.value?.id) saveSnapshots(currentReport.value.id);
					ElMessage.success(`报告「${currentReport.value?.report_name}」收集完成`);
					emit('collected', currentReport.value);
				} else if (evt.status === 'interrupted') {
					ElMessage.warning(`报告收集已中断：${evt.detail}`);
					emit('collected', currentReport.value);
				} else if (evt.status === 'failed') {
					ElMessage.error(`报告收集失败：${evt.detail}`);
					emit('collected', currentReport.value);
				}
			} catch {
				// JSON 解析失败忽略
			}
		}
	}
}

function stopSSE() {
	if (abortCtrl) {
		abortCtrl.abort();
		abortCtrl = null;
	}
}

function handleClose() {
	stopSSE();
	if (currentReport.value) {
		emit('closed', currentReport.value.id);
	}
}

// ======================== emit ========================
const emit = defineEmits<{
	(e: 'collected', report: any): void;
	// 用户手动关闭抽屉时通知父组件，父组件记录该 id 避免再次自动弹出
	(e: 'closed', reportId: number): void;
}>();

// ======================== 计算属性 ========================

// 抽屉宽度自适应屏幕 1/3，最小 480px
const drawerSize = computed(() => {
	if (typeof window === 'undefined') return '560px';
	return Math.max(480, Math.floor(window.innerWidth / 3)) + 'px';
});

// 方案A（执行机直传）时隐藏 Step3（文件下载），前端不渲染该面板
const visibleSteps = computed(() =>
	STEPS.filter(s => s.step !== 3 || plan.value === 'b')
);

const progressStatus = computed(() => {
	if (currentState.value.status === 'done')        return 'success';
	if (currentState.value.status === 'failed')       return 'exception';
	if (currentState.value.status === 'interrupted')  return 'exception';
	return undefined;
});

// Step 2 打包子条目（方案A显示3个zip）
const step2ZipItems = computed(() => {
	const si = currentState.value.sub_items;
	if (!si) return [];
	return [
		{ key: 'report_zip', label: 'HTML报告',   status: si.report_zip?.status ?? 'pending', detail: si.report_zip?.detail ?? '' },
		{ key: 'log_zip',    label: 'JMeter日志', status: si.log_zip?.status ?? 'pending',    detail: si.log_zip?.detail ?? '' },
		{ key: 'jtl_zip',   label: 'JTL结果',    status: si.jtl_zip?.status ?? 'pending',    detail: si.jtl_zip?.detail ?? '' },
	];
});

// Step 4 上传子条目（report → log → jtl）
const step4UploadItems = computed(() => {
	const si = currentState.value.sub_items;
	if (!si) return [];
	return [
		{ key: 'report', label: 'HTML报告', status: si.report?.status ?? 'pending', detail: si.report?.detail ?? '' },
		{ key: 'log',    label: 'JMeter日志', status: si.log?.status ?? 'pending',  detail: si.log?.detail ?? '' },
		{ key: 'jtl',    label: 'JTL结果',  status: si.jtl?.status ?? 'pending',    detail: si.jtl?.detail ?? '' },
	];
});

// ======================== 步骤状态判断 ========================

function isRunningStep(step: number): boolean {
	return currentState.value.status === 'running' && currentState.value.step === step;
}

function isDoneStep(step: number): boolean {
	if (currentState.value.status === 'done') return true;
	return step < currentState.value.step;
}

function isFailedStep(step: number): boolean {
	const s = currentState.value.status;
	return (s === 'failed' || s === 'interrupted') && currentState.value.step === step;
}

function isExpandedStep(step: number): boolean {
	if (isRunningStep(step) || isFailedStep(step)) return true;
	// 已完成的步骤：用户手动点击后展开
	if (isDoneStep(step)) return expandedDone.value.has(step);
	return false;
}

// 切换已完成步骤的展开/折叠（仅 done 状态可触发）
function toggleDone(step: number) {
	if (!isDoneStep(step) || isRunningStep(step)) return;
	if (expandedDone.value.has(step)) {
		expandedDone.value.delete(step);
	} else {
		expandedDone.value.add(step);
	}
	// 触发响应式更新
	expandedDone.value = new Set(expandedDone.value);
}

function getStepPanelClass(step: number): string {
	if (isRunningStep(step)) return 'step-panel--running';
	if (isDoneStep(step))    return 'step-panel--done';
	if (isFailedStep(step))  return 'step-panel--failed';
	return 'step-panel--wait';
}
</script>

<style scoped lang="scss">
.collect-drawer-body {
	padding: 0 4px;
}

.report-info {
	margin-bottom: 16px;
	padding: 12px 14px;
	background: var(--el-fill-color-light);
	border-radius: 6px;

	.report-name {
		font-size: 14px;
		font-weight: 600;
		color: var(--el-text-color-primary);
		margin-bottom: 4px;
		word-break: break-all;
	}

	.report-scene {
		font-size: 12.5px;
		color: var(--el-text-color-secondary);
	}

	.report-plan-row {
		margin-top: 8px;
	}
}

.progress-bar-wrapper {
	padding: 0 2px;
	margin-bottom: 20px;
}

// ── 步骤面板 ──────────────────────────────────────────────────────────────

.steps-wrapper {
	display: flex;
	flex-direction: column;
	gap: 6px;
}

.step-panel {
	border-radius: 6px;
	overflow: hidden;
	border: 1px solid transparent;
	transition: background 0.2s, border-color 0.2s;

	&--running {
		background: var(--el-color-primary-light-9);
		border-color: var(--el-color-primary-light-7);
	}

	&--done {
			background: var(--el-color-success-light-9);
			border-color: var(--el-color-success-light-7);

			.step-header--clickable:hover { background: var(--el-color-success-light-8); border-radius: 4px; }
		}
	&--failed { background: var(--el-color-danger-light-9); border-color: var(--el-color-danger-light-7); }
	&--wait   { background: var(--el-fill-color-lighter); border-color: var(--el-border-color-lighter); }
}

.step-header {
	display: flex;
	align-items: center;
	gap: 10px;
	padding: 10px 12px;

	&--clickable {
		cursor: pointer;
		user-select: none;
		&:hover { background: var(--el-fill-color-light); border-radius: 4px; }
	}
}

.step-icon {
	font-size: 18px;
	flex-shrink: 0;

	.rotating    { color: var(--el-color-primary); animation: spin 1s linear infinite; }
	.icon-done   { color: var(--el-color-success); }
	.icon-failed { color: var(--el-color-danger); }
	.icon-wait   { color: var(--el-text-color-secondary); font-size: 16px; }
}

.step-name {
	flex: 1;
	font-size: 13.5px;
	font-weight: 500;

	.step-panel--done   & { color: var(--el-color-success); }
	.step-panel--failed & { color: var(--el-color-danger); }
	.step-panel--wait   & { color: var(--el-text-color-secondary); }
}

.step-pct {
	font-size: 13px;
	font-weight: 600;
	color: var(--el-color-primary);
	flex-shrink: 0;
}

.step-plan-label {
	font-size: 11.5px;
	font-weight: 400;
	color: var(--el-text-color-placeholder);
	margin-left: 3px;
}

.step-toggle-icon {
	font-size: 14px;
	flex-shrink: 0;
	color: var(--el-color-success);
	transition: transform 0.2s ease;
	margin-left: auto;

	&--open { transform: rotate(180deg); }
}

// ── 面板体 ─────────────────────────────────────────────────────────────────

.step-body {
	padding: 0 12px 12px 40px;
}

.step-detail {
	font-size: 12px;
	color: var(--el-text-color-secondary);
	margin-bottom: 8px;
	word-break: break-all;
	line-height: 1.5;

	&--failed { color: var(--el-color-danger); }
}

.step-no-detail {
	font-size: 12px;
	color: var(--el-text-color-placeholder);
	font-style: italic;
	padding: 2px 0 4px;
}

// ── 连接 / Worker / 打包 / 上传 子列表 ────────────────────────────────────

.conn-list,
.worker-list,
.zip-list,
.upload-list {
	display: flex;
	flex-direction: column;
	gap: 4px;
}

.conn-item,
.worker-item,
.zip-item,
.upload-item {
	display: flex;
	align-items: center;
	gap: 6px;
	font-size: 12px;
	padding: 3px 0;

	.w-icon {
		font-size: 14px;
		flex-shrink: 0;

		&.rotating    { color: var(--el-color-primary); animation: spin 1s linear infinite; }
		&.icon-done   { color: var(--el-color-success); }
		&.icon-failed { color: var(--el-color-danger); }
		&.icon-skip   { color: var(--el-text-color-placeholder); }
		&.icon-wait   { color: var(--el-text-color-placeholder); }
	}

	.w-ip {
		color: var(--el-text-color-regular);
		white-space: nowrap;
	}

	.w-detail {
		color: var(--el-text-color-secondary);
		margin-left: 4px;
		word-break: break-all;
	}

	// SSH连接条目专用：名称 + 访问对象 + 失败悬停
	.w-conn-name {
		color: var(--el-text-color-regular);
		font-weight: 500;
		flex-shrink: 0;
	}

	.w-conn-url {
		color: var(--el-text-color-placeholder);
		font-size: 11.5px;
		margin-left: 6px;
		flex-shrink: 0;
	}

	.w-conn-error {
		color: var(--el-color-danger);
		font-size: 11.5px;
		max-width: 160px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		cursor: help;
		margin-left: 6px;
	}

	&--done .w-ip   { color: var(--el-color-success); }
	&--failed .w-ip { color: var(--el-color-danger); }
	&--skip .w-ip   { color: var(--el-text-color-placeholder); }
	&--pending .w-ip { color: var(--el-text-color-placeholder); }
}

// ── Transition ─────────────────────────────────────────────────────────────

.step-expand-enter-active,
.step-expand-leave-active {
	transition: max-height 0.25s ease, opacity 0.2s ease;
	max-height: 300px;
	overflow: hidden;
}

.step-expand-enter-from,
.step-expand-leave-to {
	max-height: 0;
	opacity: 0;
}

// ── 中断/失败终态通知 ───────────────────────────────────────────────────────

.terminal-notice {
	margin-top: 12px;
	padding: 8px 12px;
	border-radius: 4px;
	font-size: 12.5px;
	line-height: 1.5;
	word-break: break-all;

	&--interrupted {
		background: var(--el-color-warning-light-9);
		color: var(--el-color-warning-dark-2);
		border-left: 3px solid var(--el-color-warning);
	}

	&--failed {
		background: var(--el-color-danger-light-9);
		color: var(--el-color-danger);
		border-left: 3px solid var(--el-color-danger);
	}
}

.collect-empty {
	text-align: center;
	padding: 60px 0;
	color: var(--el-text-color-secondary);
	font-size: 14px;
}

@keyframes spin {
	from { transform: rotate(0deg); }
	to   { transform: rotate(360deg); }
}
</style>
