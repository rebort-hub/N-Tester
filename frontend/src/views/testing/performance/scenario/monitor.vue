<template>
	<div class="scene-monitor">

		<!-- 压测进度条 -->
		<div class="monitor-progress-section">
			<div v-if="scene" class="monitor-progress-header">
				<span class="monitor-scene-name">{{ currentScene.name }}</span>
				<el-tag
					:type="statusTagType(currentScene.status)"
					size="small"
					:effect="currentScene.status === 'running' ? 'dark' : 'light'"
					style="margin-left: 10px; flex-shrink: 0"
				>{{ statusLabel(currentScene.status) }}</el-tag>
				<el-button
					type="danger"
					size="small"
					plain
					style="margin-left:auto; flex-shrink: 0"
					:disabled="currentScene.status !== 'running'"
					@click="handleForceStop"
				>
					<el-icon><ele-VideoPause /></el-icon>强制停止
				</el-button>
			</div>

			<!-- 进度轨道行（flex，bar + suffix 始终同行对齐） -->
			<div class="monitor-progress-bar-row">
				<!-- 联调/启动阶段进度条 -->
				<template v-if="execState">
					<div class="stage-bar-area">
						<div class="stage-track">
							<div class="stage-fill" :style="{ width: execState.progress + '%' }"></div>
						</div>
						<!-- 所有阶段名均匀分布在进度条轨道上，同时可见 -->
						<div class="stage-bar-seg-labels">
							<span
								v-for="(s, i) in execState.stages"
								:key="i"
								class="stage-seg-label"
								:class="{ 'seg-done': s.done, 'seg-active': s.active, 'seg-wait': !s.done && !s.active }"
								:style="{ left: `calc(${i * 3}% + 4px)` }"
							>{{ s.label }}</span>
						</div>
						<!-- 阶段分割线：N-1 条，悬停显示阶段名称 -->
						<el-tooltip
							v-for="(m, i) in stageMarkers"
							:key="i"
							:content="m.label"
							placement="top"
							:show-after="0"
							:teleported="true"
						>
							<div
								class="stage-pin"
								:class="{ 'pin-done': m.done, 'pin-active': m.active }"
								:style="{ left: m.position + '%' }"
							></div>
						</el-tooltip>
					</div>
					<span class="monitor-progress-suffix">
						<template v-if="execState.progress >= 100">
							<el-icon :size="20" style="color:#67c23a;font-weight:700"><ele-CircleCheck /></el-icon>
						</template>
						<template v-else>
							<span style="color:#409eff;font-weight:700;font-size:15px">{{ execState.progress }}%</span>
						</template>
					</span>
				</template>

				<!-- 正式压测进度条 -->
				<template v-else>
					<el-progress
						:percentage="currentScene.progress ?? 0"
						:color="progressColor(currentScene.status)"
						:stroke-width="14"
						:show-text="false"
						class="monitor-progress-bar"
					/>
					<span class="monitor-progress-suffix">
						<template v-if="currentScene.status === 'running'">
							<span style="color:#409eff;font-weight:700;font-size:15px">{{ currentScene.progress }}%</span>
						</template>
						<template v-else-if="currentScene.status === 'completed'">
							<el-icon :size="20" style="color:#67c23a;font-weight:700"><ele-CircleCheck /></el-icon>
						</template>
						<template v-else-if="currentScene.status === 'failed' || currentScene.status === 'cancelled'">
							<span style="color:#f56c6c;font-weight:700;font-size:15px">{{ currentScene.progress ?? 0 }}%</span>
						</template>
						<template v-else>
							<span style="color:#909399;font-weight:700;font-size:15px">{{ currentScene.progress ?? 0 }}%</span>
						</template>
					</span>
				</template>
			</div>
		</div>

		<!-- 控制台 + 指标看板 -->
		<div class="monitor-body">
			<!-- 左侧：控制台输出 60% -->
			<div class="monitor-console-wrap">
				<PerfConsole
					:logs="consoleLogs"
					title="压测执行日志（实时）"
					empty-text="暂无输出，启动压测后将在此显示实时日志..."
				>
					<template #actions>
						<el-button size="small" @click="consoleLogs = []">
							<el-icon><ele-Delete /></el-icon>清空
						</el-button>
					</template>
				</PerfConsole>
			</div>

			<!-- 右侧：实时指标看板 40% -->
			<div class="monitor-metrics-wrap" :class="{ 'metrics-dark': monitorDark }">
				<div class="metrics-header">
					<span><el-icon><ele-DataLine /></el-icon>实时监控指标</span>
					<el-tooltip :content="monitorDark ? '切换亮色' : '切换深色'" placement="top" :show-after="300">
						<el-button class="theme-toggle-btn" size="small" text circle @click="monitorDark = !monitorDark">
							<el-icon>
								<ele-Sunny v-if="monitorDark" />
								<ele-Moon v-else />
							</el-icon>
						</el-button>
					</el-tooltip>
				</div>
				<draggable
					class="metrics-charts-list"
					v-model="monitorMetrics"
					item-key="title"
					handle=".panel-title-handle"
					:animation="180"
					ghost-class="metric-drag-ghost"
					chosen-class="metric-drag-chosen"
				>
					<template #item="{ element: m }">
						<MetricChart
							:title="m.title"
							:unit="m.unit"
							:series="m.series"
							:time-labels="monitorTimeLabels"
							:dark-mode="monitorDark"
							:chart-height="220"
							@expand="handleChartExpand"
						/>
					</template>
				</draggable>
			</div>
		</div>

		<!-- Top 5 错误统计 -->
		<div class="monitor-errors-wrap" :class="{ 'errors-dark': monitorDark }">
			<div class="errors-header">
				<span class="errors-header-title">Top 5 Errors by Sampler（实时）</span>
				<el-tooltip content="放大查看" placement="top" :show-after="400">
					<el-button class="errors-expand-btn" size="small" text circle @click="openErrorsExpand">
						<el-icon><ele-FullScreen /></el-icon>
					</el-button>
				</el-tooltip>
			</div>
			<div class="errors-table-scroll">
				<el-table ref="errorsSmallTableRef" :data="top5Errors" size="small" class="errors-table" border :show-header="true">
					<el-table-column label="Sample（接口）" prop="sampler" min-width="200" header-align="center">
						<template #default="{ row }">
							<span class="sampler-name">{{ row.sampler }}</span>
						</template>
					</el-table-column>
					<el-table-column label="#Samples" prop="samples" width="80" align="center" header-align="center" />
					<el-table-column label="#Errors" prop="errors" width="70" align="center" header-align="center">
						<template #default="{ row }">
							<span class="total-errors">{{ row.errors }}</span>
						</template>
					</el-table-column>
					<el-table-column label="Error 1" min-width="160" header-align="center">
						<template #default="{ row }">
							<span v-if="row.top[0]" class="error-msg">{{ row.top[0].error }}</span>
						</template>
					</el-table-column>
					<el-table-column label="Count" width="60" align="center" header-align="center">
						<template #default="{ row }">
							<span v-if="row.top[0]" class="error-count">{{ row.top[0].count }}</span>
						</template>
					</el-table-column>
					<el-table-column label="Error 2" min-width="160" header-align="center">
						<template #default="{ row }">
							<span v-if="row.top[1]" class="error-msg">{{ row.top[1].error }}</span>
						</template>
					</el-table-column>
					<el-table-column label="Count" width="60" align="center" header-align="center">
						<template #default="{ row }">
							<span v-if="row.top[1]" class="error-count">{{ row.top[1].count }}</span>
						</template>
					</el-table-column>
					<el-table-column label="Error 3" min-width="160" header-align="center">
						<template #default="{ row }">
							<span v-if="row.top[2]" class="error-msg">{{ row.top[2].error }}</span>
						</template>
					</el-table-column>
					<el-table-column label="Count" width="60" align="center" header-align="center">
						<template #default="{ row }">
							<span v-if="row.top[2]" class="error-count">{{ row.top[2].count }}</span>
						</template>
					</el-table-column>
					<el-table-column label="Error 4" min-width="160" header-align="center">
						<template #default="{ row }">
							<span v-if="row.top[3]" class="error-msg">{{ row.top[3].error }}</span>
						</template>
					</el-table-column>
					<el-table-column label="Count" width="60" align="center" header-align="center">
						<template #default="{ row }">
							<span v-if="row.top[3]" class="error-count">{{ row.top[3].count }}</span>
						</template>
					</el-table-column>
					<el-table-column label="Error 5" min-width="160" header-align="center">
						<template #default="{ row }">
							<span v-if="row.top[4]" class="error-msg">{{ row.top[4].error }}</span>
						</template>
					</el-table-column>
					<el-table-column label="Count" width="60" align="center" header-align="center">
						<template #default="{ row }">
							<span v-if="row.top[4]" class="error-count">{{ row.top[4].count }}</span>
						</template>
					</el-table-column>
				</el-table>
			</div>
		</div>

		<!-- 放大图表 Dialog -->
		<el-dialog
			v-model="expandVisible"
			width="75%"
			destroy-on-close
			class="expand-chart-dialog"
		>
			<MetricChart
				v-if="expandConfig"
				:title="expandConfig!.title"
				:unit="expandConfig!.unit"
				:series="expandConfig!.series"
				:time-labels="expandConfig!.timeLabels"
				:dark-mode="monitorDark"
				:expandable="false"
				:chart-height="480"
			/>
		</el-dialog>

		<!-- Top5 Errors 放大抽屉（从底部滑出） -->
		<el-drawer
			v-model="errorsExpandVisible"
			direction="btt"
			:size="errorsDrawerSizePx"
			destroy-on-close
			class="errors-expand-drawer"
			:class="{ 'errors-expand-dark': monitorDark }"
		>
			<template #header>
				<span class="errors-dialog-header-title">Top 5 Errors by Sampler（详情）</span>
			</template>
			<el-table :data="top5Errors" size="small" class="errors-table-full" border :show-header="true" style="width: 100%">
				<el-table-column label="Sample（接口）" prop="sampler" min-width="180" header-align="center">
					<template #default="{ row }">
						<span class="sampler-name">{{ row.sampler }}</span>
					</template>
				</el-table-column>
				<el-table-column label="#Samples" prop="samples" width="90" align="center" header-align="center" />
				<el-table-column label="#Errors" prop="errors" width="80" align="center" header-align="center">
					<template #default="{ row }">
						<span class="total-errors">{{ row.errors }}</span>
					</template>
				</el-table-column>
				<el-table-column label="Error 1" min-width="130" header-align="center">
					<template #default="{ row }">
						<span v-if="row.top[0]" class="error-msg-full">{{ row.top[0].error }}</span>
					</template>
				</el-table-column>
				<el-table-column label="Count" width="60" align="center" header-align="center">
					<template #default="{ row }">
						<span v-if="row.top[0]" class="error-count">{{ row.top[0].count }}</span>
					</template>
				</el-table-column>
				<el-table-column label="Error 2" min-width="130" header-align="center">
					<template #default="{ row }">
						<span v-if="row.top[1]" class="error-msg-full">{{ row.top[1].error }}</span>
					</template>
				</el-table-column>
				<el-table-column label="Count" width="60" align="center" header-align="center">
					<template #default="{ row }">
						<span v-if="row.top[1]" class="error-count">{{ row.top[1].count }}</span>
					</template>
				</el-table-column>
				<el-table-column label="Error 3" min-width="130" header-align="center">
					<template #default="{ row }">
						<span v-if="row.top[2]" class="error-msg-full">{{ row.top[2].error }}</span>
					</template>
				</el-table-column>
				<el-table-column label="Count" width="60" align="center" header-align="center">
					<template #default="{ row }">
						<span v-if="row.top[2]" class="error-count">{{ row.top[2].count }}</span>
					</template>
				</el-table-column>
				<el-table-column label="Error 4" min-width="130" header-align="center">
					<template #default="{ row }">
						<span v-if="row.top[3]" class="error-msg-full">{{ row.top[3].error }}</span>
					</template>
				</el-table-column>
				<el-table-column label="Count" width="60" align="center" header-align="center">
					<template #default="{ row }">
						<span v-if="row.top[3]" class="error-count">{{ row.top[3].count }}</span>
					</template>
				</el-table-column>
				<el-table-column label="Error 5" min-width="130" header-align="center">
					<template #default="{ row }">
						<span v-if="row.top[4]" class="error-msg-full">{{ row.top[4].error }}</span>
					</template>
				</el-table-column>
				<el-table-column label="Count" width="60" align="center" header-align="center">
					<template #default="{ row }">
						<span v-if="row.top[4]" class="error-count">{{ row.top[4].count }}</span>
					</template>
				</el-table-column>
			</el-table>
		</el-drawer>

	</div>
</template>

<script setup lang="ts" name="SceneMonitor">
import { ref, computed, onUnmounted } from 'vue';
import { ElMessageBox } from 'element-plus';
import PerfConsole from '../components/PerfConsole.vue';
import MetricChart from '../components/MetricChart.vue';
import draggable from 'vuedraggable';
import { usePerformanceApi } from '/@/api/v1/performance';

const perfApi = usePerformanceApi();

// 接收父组件传入的当前监控场景（null 表示无任务，使用占位默认值保持 UI 完整显示）
const props = defineProps<{
	scene: any | null;
	execState?: {
		stages: { label: string; done: boolean; active: boolean }[];
		progress: number;
	} | null;
}>();

const emit = defineEmits<{
	'exec-done': [];
	'force-stop': [sceneId: number];
}>();

// scene 为 null 时兜底，保证所有字段不会 undefined
const currentScene = computed(() => props.scene ?? { name: '--', status: 'pending', progress: 0 });

// ======================== 联调/启动阶段进度条 ========================

// 两个阶段之间的分割线（N 个阶段 → N-1 条线），悬停显示左侧阶段名称
const stageMarkers = computed(() => {
	const state = props.execState;
	if (!state) return [];
	const { stages } = state;
	return stages.slice(0, -1).map((stage, i) => ({
		label: stage.label,
		position: (i + 1) * 3,   // 每段固定 3%，分割线在 3%、6%
		done: stage.done,
		active: stage.active,
	}));
});

const statusLabel = (status: string) => {
	const map: Record<string, string> = {
		debug: '待联调', pending: '待开始', running: '进行中', completed: '已完成', cancelled: '已取消', failed: '失败',
	};
	return map[status] ?? status;
};

const statusTagType = (status: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
	const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
		debug: 'info', pending: 'warning', running: '', completed: 'success', cancelled: 'info', failed: 'danger',
	};
	return map[status] ?? '';
};

const progressColor = (status: string) => {
	const map: Record<string, string> = {
		running: '#409eff', completed: '#67c23a', failed: '#f56c6c', cancelled: '#f56c6c',
	};
	return map[status] ?? '#409eff';
};

// ======================== 控制台日志 ========================

const consoleLogs = ref<{ time: string; text: string; level: string }[]>([]);

// ======================== 实时监控 SSE ========================

let _monitorAbortCtrl: AbortController | null = null;
let _monitorOffset = 0;

const _addLog = (text: string, level?: string) => {
	const now = new Date();
	const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
	// 根据文本内容推断日志级别
	let lv = level;
	if (!lv) {
		const t = (text ?? '').toLowerCase();
		if (/\berror\b/.test(t) || t.includes('exception')) lv = 'error';
		else if (t.includes('warn')) lv = 'warn';
		else lv = 'info';
	}
	consoleLogs.value.push({ time, text, level: lv });
};

const _handleMonitorEvent = (evt: any) => {
	if (evt.type === 'connected') {
		_addLog(evt.message || '已连接实时监控，等待日志数据...', 'info');
	} else if (evt.type === 'log') {
		_addLog(evt.message ?? '');
	} else if (evt.type === 'progress') {
		// 直接修改父组件传入的 scene 对象（与父组件共享同一响应式引用）
		if (props.scene) props.scene.progress = evt.value ?? 0;
		// 若 execState 仍处于 Stage 最后阶段（JMeter 运行中），将真实进度映射到整体进度
		if (props.execState) {
			const preWeight = Math.max(0, (props.execState.stages.length - 1) * 3);
			props.execState.progress = preWeight + Math.round((evt.value ?? 0) * (100 - preWeight) / 100);
		}
	} else if (evt.type === 'done') {
		if (props.scene) {
			const statusMap: Record<number, string> = { 3: 'completed', 4: 'cancelled', 5: 'failed' };
			props.scene.status = statusMap[evt.status] ?? 'completed';
			if (evt.status === 3) props.scene.progress = 100;
			// 取消(4)和失败(5)保留 progress 事件已更新的当前值，不覆盖
		}
		const logType = evt.status === 3 ? 'success' : (evt.status === 4 ? 'warning' : 'error');
		_addLog(evt.message || '压测已完成', logType);
		// 标记所有阶段完成，进度 100%，通知父组件清除 execState
		if (props.execState) {
			props.execState.stages.forEach(s => { s.done = true; s.active = false; });
			props.execState.progress = 100;
		}
		emit('exec-done');
	} else if (evt.type === 'error') {
		if (props.scene) props.scene.status = 'failed';
		_addLog(evt.message || '压测异常', 'error');
		emit('exec-done');
	} else if (evt.type === 'cancelled' || evt.type === 'stopped') {
		if (props.scene) props.scene.status = 'cancelled';
		_addLog(evt.message || '压测已停止', 'warning');
		emit('exec-done');
	}
	// type === 'ping'：心跳保活，无需处理
};

const handleForceStop = () => {
	if (currentScene.value.status !== 'running') return;
	ElMessageBox.confirm(
		`确认立即停止「${currentScene.value.name}」的压测任务？`,
		'强制停止',
		{ type: 'warning', confirmButtonText: '立即停止', cancelButtonText: '取消', confirmButtonClass: 'el-button--danger' }
	).then(() => {
		emit('force-stop', currentScene.value.id);
	}).catch(() => {});
};

/**
 * 启动实时监控 SSE 连接（由父组件 index.vue 通过 ref 调用）。
 * @param scenarioId 压测场景 ID
 * @param initOffset 断线续传起点（默认从 0 开始）
 * consoleLogs 不会自动清空，只能通过"清空"按钮手动清除。
 */
const startMonitor = async (scenarioId: number, initOffset = 0) => {
	stopMonitor();
	_monitorOffset = initOffset;
	_monitorAbortCtrl = new AbortController();

	try {
		const resp = await perfApi.monitorScenarioStream(scenarioId, initOffset, _monitorAbortCtrl.signal);
		if (!resp.ok || !resp.body) {
			_addLog(`连接失败（HTTP ${resp.status}）`, 'error');
			return;
		}
		const reader = resp.body.getReader();
		const decoder = new TextDecoder();
		let buffer = '';

		while (true) {
			const { done, value } = await reader.read();
			if (done) break;
			buffer += decoder.decode(value, { stream: true });
			const lines = buffer.split('\n');
			buffer = lines.pop() ?? '';
			for (const line of lines) {
				if (!line.startsWith('data: ')) continue;
				try { _handleMonitorEvent(JSON.parse(line.slice(6))); } catch { /* 忽略单行 JSON 解析异常 */ }
			}
		}
	} catch (e: any) {
		if (e?.name === 'AbortError') return;
		_addLog(`连接异常：${e?.message ?? String(e)}`, 'error');
	}
};

/** 停止实时监控 SSE 连接。*/
const stopMonitor = () => {
	_monitorAbortCtrl?.abort();
	_monitorAbortCtrl = null;
};

onUnmounted(() => { stopMonitor(); });

// ======================== 实时监控指标看板 ========================

const monitorDark = ref(true);
const expandVisible = ref(false);
const expandConfig = ref<{ title: string; unit: string; series: any[]; timeLabels: string[] } | null>(null);
const errorsExpandVisible = ref(false);
const errorsSmallTableRef = ref<any>(null);
const errorsDrawerSizePx = ref('300px');

const openErrorsExpand = () => {
	const smallEl = errorsSmallTableRef.value?.$el as HTMLElement | undefined;
	if (smallEl) {
		const tableH = smallEl.offsetHeight;
		const drawerHeaderH = 56;
		const t = drawerHeaderH + tableH;
		const maxH = Math.round(window.innerHeight * 0.9);
		errorsDrawerSizePx.value = Math.min(t, maxH) + 'px';
	}
	errorsExpandVisible.value = true;
};

const handleChartExpand = (cfg: { title: string; unit: string; series: any[]; timeLabels: string[] }) => {
	expandConfig.value = cfg;
	expandVisible.value = true;
};

// 时间轴（16 个时间点，代表最近 15 分钟）
const _now = new Date();
const monitorTimeLabels = Array.from({ length: 16 }, (_, i) => {
	const t = new Date(_now.getTime() - (15 - i) * 60000);
	return `${t.getHours().toString().padStart(2, '0')}:${t.getMinutes().toString().padStart(2, '0')}`;
});

// 指标占位数据（当前版本 monitor SSE 仅推送日志行，实时指标图待后续扩展）
const monitorMetrics = ref([
	{ title: 'QPS', unit: '次/秒', series: [
		{ name: 'jmeter-slave-1', data: [235, 248, 261, 243, 278, 312, 328, 341, 319, 302, 287, 295, 315, 338, 351, 344] },
		{ name: 'jmeter-slave-2', data: [198, 212, 225, 207, 241, 275, 289, 298, 281, 264, 249, 258, 277, 301, 314, 308] },
	]},
	{ title: '平均响应时间（RT）', unit: 'ms', series: [
		{ name: 'jmeter-slave-1', data: [42, 45, 48, 44, 52, 68, 74, 79, 72, 65, 58, 61, 71, 78, 83, 81] },
		{ name: 'jmeter-slave-2', data: [38, 41, 44, 40, 47, 62, 68, 72, 66, 59, 53, 56, 64, 71, 76, 74] },
	]},
	{ title: '并发线程数', unit: '个', series: [
		{ name: 'jmeter-slave-1', data: [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100] },
		{ name: 'jmeter-slave-2', data: [80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80] },
	]},
	{ title: '错误率', unit: '%', series: [
		{ name: 'jmeter-slave-1', data: [0, 0, 0.1, 0, 0.2, 1.8, 2.1, 2.4, 2.0, 1.5, 0.9, 1.1, 1.8, 2.2, 2.5, 2.3] },
		{ name: 'jmeter-slave-2', data: [0, 0, 0, 0, 0.1, 1.5, 1.8, 2.1, 1.7, 1.2, 0.7, 0.9, 1.5, 1.9, 2.2, 2.0] },
	]},
]);

const top5Errors = ref<any[]>([]);

const clearLogs = () => { consoleLogs.value = []; };

defineExpose({ startMonitor, stopMonitor, addExternalLog: _addLog, clearLogs });
</script>

<style scoped lang="scss">
.scene-monitor {

	.monitor-progress-section {
		padding: 4px 0 6px;
		border-bottom: 1px solid var(--el-border-color-light);
		margin-bottom: 8px;

		.monitor-progress-header {
			display: flex;
			align-items: center;
			margin-bottom: 4px;

			.monitor-scene-name {
				font-size: 14px;
				font-weight: 600;
				color: var(--el-text-color-primary);
				white-space: nowrap;
				overflow: hidden;
				text-overflow: ellipsis;
				max-width: 40%;
			}

		}

		.monitor-progress-bar-row {
			display: flex;
			align-items: center;
			gap: 12px;

			.monitor-progress-bar {
				flex: 1;
			}

			.monitor-progress-suffix {
				flex-shrink: 0;
				width: 52px;
				display: flex;
				align-items: center;
				justify-content: center;
			}

			// stage 轨道（flex:1 与 suffix 同行对齐）
			.stage-bar-area {
				flex: 1;
				position: relative;

				.stage-track {
					height: 14px;
					background: var(--el-fill-color-darker, #e4e7ed);
					border-radius: 7px;
					overflow: hidden;

					.stage-fill {
						height: 100%;
						background: var(--el-color-primary);
						border-radius: 7px;
						transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
					}
				}

				// 所有阶段名均匀分布在进度条轨道上
				.stage-bar-seg-labels {
					position: absolute;
					top: 0;
					left: 0;
					right: 0;
					height: 14px;
					pointer-events: none;
					z-index: 2;

					.stage-seg-label {
						position: absolute;
						font-size: 11px;
						font-weight: 600;
						white-space: nowrap;
						line-height: 14px;

						&.seg-done {
							color: rgba(255, 255, 255, 0.92);
							text-shadow: 0 0 4px rgba(0, 0, 0, 0.35);
						}
						&.seg-active {
							color: rgba(0, 0, 0, 0.82);
							text-shadow: 0 0 4px rgba(255, 255, 255, 0.9), 0 0 6px rgba(255, 255, 255, 0.6);
						}
						&.seg-wait {
							color: rgba(0, 0, 0, 0.45);
							text-shadow: 0 0 3px rgba(255, 255, 255, 0.7);
						}
					}
				}

				// 阶段分割线：绝对定位，垂直方向略超出轨道
				.stage-pin {
					position: absolute;
					top: -4px;
					height: 22px;
					width: 18px;
					transform: translateX(-50%);
					cursor: default;
					display: flex;
					justify-content: center;
					align-items: stretch;

					&::after {
						content: '';
						width: 2px;
						background: #c8ccd4;
						transition: background 0.3s;
					}

					&.pin-done::after { background: rgba(255, 255, 255, 0.88); }

					&.pin-active::after {
						background: #f0a020;
						animation: pin-pulse 1.2s ease-in-out infinite;
					}
				}
			}
		}
	}

	.monitor-body {
		display: grid;
		grid-template-columns: 60% 1fr;
		// 高度由右列内容决定：metrics-header(38px) + 4×chart(222px) + 3×gap(10px) = 956px
		height: 956px;
		gap: 14px;

		.monitor-console-wrap {
			min-width: 0;
			height: 100%;
			display: flex;
			flex-direction: column;
			overflow: hidden;
		}

		.monitor-metrics-wrap {
			flex: 1;
			min-width: 0;
			display: flex;
			flex-direction: column;
			gap: 0;

			&.metrics-dark {
				.metrics-header {
					background: #111217;
					color: #7ec8e3;
					border-color: #1e2028;

					.theme-toggle-btn {
						color: #7ec8e3 !important;
						&:hover {
							color: #b0dff0 !important;
							background: rgba(255, 255, 255, 0.08) !important;
						}
					}
				}
			}

			.metrics-header {
				display: flex;
				align-items: center;
				justify-content: space-between;
				padding: 8px 14px;
				font-size: 13.5px;
				font-weight: 600;
				color: var(--el-text-color-primary);
				background: var(--el-fill-color-light);
				border: 1px solid var(--el-border-color);
				border-radius: 6px;
				flex-shrink: 0;

				span {
					display: flex;
					align-items: center;
					gap: 6px;
				}

				.theme-toggle-btn {
					color: var(--el-text-color-secondary);
					:deep(.el-icon) {
						font-size: 17px !important;
					}
				}
			}

			.metrics-charts-list {
				display: flex;
				flex-direction: column;
				gap: 10px;
				overflow-y: auto;
				padding: 0;
			}
		}
	}

	.monitor-errors-wrap {
		margin-top: 14px;
		border: 1px solid var(--e-border-color);
		border-radius: 8px;
		overflow: hidden;
		background: var(--el-fill-color-blank);

		--e-cell-bg: var(--el-fill-color-blank);
		--e-cell-color: var(--el-text-color-primary);
		--e-header-bg: var(--el-fill-color-light);
		--e-header-color: var(--el-text-color-secondary);
		--e-border-color: var(--el-border-color);
		--e-hover-bg: var(--el-fill-color-light);
		--e-row-alt-bg: var(--el-fill-color-lighter);

		&.errors-dark {
			border-color: #32333a;
			background: #181b1f;

			--e-cell-bg: #181b1f;
			--e-cell-color: #d8d9da;
			--e-header-bg: #22252b;
			--e-header-color: #9fa7b3;
			--e-border-color: #32333a;
			--e-hover-bg: rgba(255, 255, 255, 0.06);
			--e-row-alt-bg: rgba(255, 255, 255, 0.04);

			.errors-header {
				background: #111217;
				color: #7ec8e3;
				border-bottom-color: #1e2028;
			}

			.errors-expand-btn {
				color: #7ec8e3 !important;
				&:hover { color: #b0dff0 !important; background: rgba(255,255,255,0.08) !important; }
			}
		}

		.errors-header {
			position: relative;
			display: flex;
			align-items: center;
			justify-content: center;
			padding: 11px 40px 11px 14px;
			font-size: 13.5px;
			font-weight: 600;
			color: var(--el-text-color-primary);
			background: var(--el-fill-color-light);
			border-bottom: 1px solid var(--el-border-color);
		}

		.errors-header-title {
			display: flex;
			align-items: center;
			gap: 6px;
		}

		.errors-expand-btn {
			position: absolute;
			right: 8px;
			top: 50%;
			transform: translateY(-50%);
			color: var(--el-text-color-secondary) !important;
			&:hover { color: var(--el-text-color-primary) !important; background: var(--el-fill-color-dark) !important; }
		}

		.errors-table-scroll {
			overflow-x: auto;
		}

		:deep(.errors-table) {
			--el-table-border-color: var(--e-border-color);
			--el-table-border: 1px solid var(--e-border-color);
			--el-table-row-hover-bg-color: var(--e-hover-bg);
			--el-table-header-bg-color: var(--e-header-bg);
			--el-table-bg-color: var(--e-cell-bg);
			--el-table-tr-bg-color: var(--e-cell-bg);
			--el-table-text-color: var(--e-cell-color);
			--el-table-header-text-color: var(--e-header-color);
		}

		:deep(.errors-table td.el-table__cell) {
			background-color: var(--e-cell-bg) !important;
			color: var(--e-cell-color) !important;
			border-bottom-color: var(--e-border-color) !important;
			border-right-color: var(--e-border-color) !important;
		}

		:deep(.errors-table .el-table__row:nth-child(even) td.el-table__cell) {
			background-color: var(--e-row-alt-bg) !important;
		}

		:deep(.errors-table th.el-table__cell) {
			background-color: var(--e-header-bg) !important;
			color: var(--e-header-color) !important;
			border-bottom-color: var(--e-border-color) !important;
			border-right-color: var(--e-border-color) !important;
			text-align: center !important;
		}

		:deep(.errors-table .hover-row > td.el-table__cell) {
			background-color: var(--e-hover-bg) !important;
		}

		:deep(.errors-table.el-table--border::before),
		:deep(.errors-table.el-table--border::after),
		:deep(.errors-table.el-table--border .el-table__inner-wrapper::after),
		:deep(.errors-table .el-table__inner-wrapper::before),
		:deep(.errors-table .el-table__border-left-patch),
		:deep(.errors-table .el-table__border-right-patch),
		:deep(.errors-table .el-table__border-bottom-patch) {
			background-color: var(--e-border-color) !important;
		}

		:deep(.errors-table) {
			.total-errors { color: #f56c6c; font-weight: 600; }
			.error-count { color: #e6a23c; }
			.sampler-name {
				display: block;
				white-space: normal;
				word-break: break-all;
				max-width: 240px;
				font-size: 12px;
			}
			.error-msg {
				font-size: 12px;
				white-space: normal;
				word-break: break-all;
				max-width: 280px;
				display: block;
			}
		}
	}
}

@keyframes pin-pulse {
	0%, 100% { opacity: 1; }
	50%       { opacity: 0.35; }
}
</style>

<style lang="scss">
/* 图表拖拽排序 */
.metric-drag-ghost { opacity: 0.25; }
.metric-drag-chosen { opacity: 0.9; box-shadow: 0 4px 16px rgba(0,0,0,0.18); }

/* 放大图表弹窗：隐藏头部，仅保留图表内容 */
.expand-chart-dialog {
	.el-dialog__header { display: none; }
	.el-dialog__body { padding: 0 !important; }
}

/* ─── errors-expand-drawer 全局样式（el-drawer 使用 teleport，必须非 scoped） ─── */
.errors-expand-drawer {
  overflow: hidden;

  .el-drawer__header {
    position: relative !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 10px 48px !important;
    margin-bottom: 0 !important;
    border-bottom: 1px solid var(--el-border-color) !important;
    background: var(--el-fill-color-light) !important;
    overflow: hidden !important;
  }

  .el-drawer__header > :first-child {
    text-align: center !important;
  }

  .el-drawer__close-btn {
    position: absolute !important;
    right: 12px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    color: var(--el-text-color-regular) !important;
    font-size: 20px !important;
  }

  .el-drawer__body {
    padding: 0;
    overflow: hidden;
  }

  .errors-dialog-header-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }

  .errors-table-full th.el-table__cell {
    text-align: center !important;
  }
  .errors-table-full .el-table__row:nth-child(even) td.el-table__cell {
    background-color: var(--el-fill-color-lighter) !important;
  }
  .errors-table-full .total-errors { color: #f56c6c; font-weight: 600; }
  .errors-table-full .error-count   { color: #e6a23c; }
  .errors-table-full .sampler-name  {
    display: block; white-space: normal; word-break: break-all; font-size: 12px;
  }
  .errors-table-full .error-msg-full {
    font-size: 12.5px; white-space: normal; word-break: break-all; display: block;
  }
}

.errors-expand-drawer.errors-expand-dark {
  background-color: #181b1f !important;

  .el-drawer__header {
    background: #111217 !important;
    border-bottom-color: #1e2028 !important;
  }

  .el-drawer__close-btn { color: #9fa7b3 !important; }
  .errors-dialog-header-title { color: #d8d9da !important; }

  .el-drawer__body {
    background: #181b1f;
    overflow: hidden;
  }

  .el-drawer__body {
    --el-table-border-color: #32333a;
    --el-table-row-hover-bg-color: rgba(255, 255, 255, 0.06);
  }

  .errors-table-full td.el-table__cell {
    background-color: #181b1f !important;
    color: #d8d9da !important;
    border-bottom-color: #32333a !important;
    border-right-color: #32333a !important;
  }

  .errors-table-full .el-table__row:nth-child(even) td.el-table__cell {
    background-color: #1f2128 !important;
  }

  .errors-table-full th.el-table__cell {
    background-color: #22252b !important;
    color: #9fa7b3 !important;
    border-bottom-color: #32333a !important;
    border-right-color: #32333a !important;
    text-align: center !important;
  }

  .errors-table-full {
    --el-table-bg-color: #181b1f;
    --el-table-tr-bg-color: #181b1f;
    --el-table-header-bg-color: #22252b;
    background-color: #181b1f !important;
  }

  .errors-table-full .el-table__inner-wrapper {
    background-color: #181b1f !important;
  }

  .errors-table-full.el-table--border::before,
  .errors-table-full.el-table--border::after,
  .errors-table-full.el-table--border .el-table__inner-wrapper::after,
  .errors-table-full .el-table__inner-wrapper::before,
  .errors-table-full .el-table__border-left-patch,
  .errors-table-full .el-table__border-right-patch,
  .errors-table-full .el-table__border-bottom-patch {
    background-color: #32333a !important;
  }

  .errors-table-full .hover-row > td.el-table__cell {
    background-color: rgba(255, 255, 255, 0.06) !important;
  }
}
</style>
