<template>
	<div class="perf-report-container">
		<el-card shadow="never">
			<!-- 查询区 -->
			<div class="toolbar">
				<div class="toolbar-left">
					<el-input
						v-model="query.report_name"
						placeholder="报告文件名称"
						clearable
						style="width: 220px"
						@keyup.enter="handleQuery"
						@clear="handleQuery"
					>
						<template #prefix><el-icon><ele-Search /></el-icon></template>
					</el-input>
					<el-input
						v-model="query.scenario_code"
						placeholder="场景编号"
						clearable
						style="width: 150px"
						@keyup.enter="handleQuery"
						@clear="handleQuery"
					/>
					<el-input
						v-model="query.creator"
						placeholder="报告人"
						clearable
						style="width: 130px"
						@keyup.enter="handleQuery"
						@clear="handleQuery"
					/>
					<el-date-picker
						v-model="query.timeRange"
						type="datetimerange"
						range-separator="~"
						start-placeholder="开始时间"
						end-placeholder="结束时间"
						value-format="YYYY-MM-DD HH:mm:ss"
						style="width: 250px"
						@change="handleQuery"
					/>
					<el-button type="primary" @click="handleQuery">
						<el-icon><ele-Search /></el-icon>查询
					</el-button>
					<el-button @click="resetQuery">
						<el-icon><ele-RefreshRight /></el-icon>重置
					</el-button>
				</div>
				<div class="toolbar-right">
					<el-button type="primary" @click="openDownloadDrawer">
						<el-icon><ele-Download /></el-icon>下载报告
					</el-button>
					<el-button @click="handleQuickCollect">
						<el-icon><ele-Document /></el-icon>收集日志
					</el-button>
				</div>
			</div>

			<!-- 数据表格 -->
			<el-table
				:data="tableData"
				v-loading="loading"
				stripe
				border
				style="width: 100%"
			>
				<el-table-column label="编号" prop="id" width="75" align="center" />
				<el-table-column prop="report_code" width="195" align="center" show-overflow-tooltip>
					<template #header>
						<span>报告ID</span>
						<el-tooltip content="报告唯一标识，格式：RPT + 年月日时分秒 + 随机数" placement="top">
							<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
				</el-table-column>
				<el-table-column label="场景编号" prop="scenario_code" width="130" align="center" show-overflow-tooltip />
				<el-table-column label="压测场景" prop="scenario_name" min-width="130" show-overflow-tooltip />
				<el-table-column label="报告文件名称" prop="report_name" min-width="210" show-overflow-tooltip />
				<el-table-column prop="file_size" width="100" align="center">
					<template #header>
						<span>文件大小</span>
						<el-tooltip content="收集并打包的报告 zip 文件大小（含 HTML 报告、jtl 结果文件及 JMeter 日志）" placement="top">
							<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<template #default="{ row }">{{ formatFileSize(row.file_size) }}</template>
				</el-table-column>
				<el-table-column width="80" align="center">
					<template #header>
						<span>状态</span>
						<el-tooltip content="收集中：正在从压力机收集报告；完成：收集成功；中断：已强制停止，可恢复；失败：收集出错" placement="top">
							<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<template #default="{ row }">
						<el-tag :type="statusTagType(row.report_status)" size="small">
							{{ statusLabel(row.report_status) }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column width="90" align="center">
					<template #header>
						<span>触发方式</span>
						<el-tooltip content="手动触发：用户主动启动压测；定时任务：由调度器自动触发" placement="top">
							<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<template #default="{ row }">
						<el-tag :type="row.trigger_type === 2 ? 'warning' : 'info'" size="small">
							{{ row.trigger_type === 2 ? '定时任务' : '手动触发' }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column label="报告人" prop="creator" width="100" align="center" show-overflow-tooltip />
				<el-table-column label="生成时间" prop="generated_at" width="160" align="center">
					<template #default="{ row }">{{ formatDateTime(row.generated_at) }}</template>
				</el-table-column>
				<el-table-column prop="remark" min-width="130" show-overflow-tooltip>
					<template #header>
						<span>备注</span>
						<el-tooltip content="仅收集失败时显示错误原因，可辅助排查问题" placement="top">
							<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<template #default="{ row }">
						<span v-if="row.remark" style="color: var(--el-color-danger); font-size: 12px">{{ row.remark }}</span>
						<span v-else style="color: var(--el-color-info)">--</span>
					</template>
				</el-table-column>
				<el-table-column label="操作" width="280" fixed="right" align="center" class-name="operation-col">
					<template #default="{ row }">
						<div class="action-btns">
							<!-- 收集中：查看进度 + 强制停止 -->
							<template v-if="row.report_status === 1">
								<el-button type="primary" size="small" text @click="handleViewProgress(row)">
									<el-icon><ele-View /></el-icon>查看进度
								</el-button>
								<el-button type="warning" size="small" text @click="handleForceStop(row)">
									<el-icon><ele-VideoPause /></el-icon>强制停止
								</el-button>
							</template>
							<!-- 已完成：在线报告 + 在线日志（hover 文件列表） -->
							<template v-else-if="row.report_status === 2">
								<el-button type="success" size="small" text @click="handlePreview(row)">
									<el-icon><ele-Monitor /></el-icon>在线报告
								</el-button>
								<el-popover
									trigger="hover"
									placement="bottom-start"
									:width="200"
									:show-after="80"
									:hide-after="200"
									@show="loadLogFiles(row)"
								>
									<template #reference>
										<el-button type="info" size="small" text>
											<el-icon><ele-Document /></el-icon>在线日志
										</el-button>
									</template>
									<div v-if="logFilesLoading[row.id]" class="log-popover-loading">
										<el-icon class="is-loading"><ele-Loading /></el-icon>
										<span>加载中…</span>
									</div>
									<div v-else class="log-popover-list">
										<div
											v-for="f in (logFilesCache[row.id] ?? [])"
											:key="f"
											class="log-popover-item"
											@click="openLogByFile(row, f)"
										>
											<el-icon><ele-Document /></el-icon>
											<span>{{ f }}</span>
										</div>
										<div v-if="!logFilesCache[row.id]?.length && !logFilesLoading[row.id]" class="log-popover-empty">
											暂无日志文件
										</div>
									</div>
								</el-popover>
							</template>
							<!-- 中断/失败：查看进度 + 恢复收集 -->
							<template v-else-if="row.report_status === 3 || row.report_status === 4">
								<el-button type="primary" size="small" text @click="handleViewProgress(row)">
									<el-icon><ele-View /></el-icon>查看进度
								</el-button>
								<el-button type="success" size="small" text @click="handleResume(row)">
									<el-icon><ele-VideoPlay /></el-icon>恢复收集
								</el-button>
							</template>
							<el-button type="danger" size="small" text @click="handleDelete(row)">
								<el-icon><ele-Delete /></el-icon>删除
							</el-button>
						</div>
					</template>
				</el-table-column>
			</el-table>

			<!-- 分页 -->
			<el-pagination
				v-model:current-page="pagination.page"
				v-model:page-size="pagination.page_size"
				:total="pagination.total"
				:page-sizes="[10, 20, 50, 100]"
				layout="total, sizes, prev, pager, next, jumper"
				class="pagination"
				@size-change="handleQuery"
				@current-change="handleQuery"
			/>
		</el-card>

		<!-- 在线日志抽屉（右侧，宽度自适应屏幕 1/2） -->
		<el-drawer
			v-model="logDrawer.visible"
			:title="logDrawer.title"
			direction="rtl"
			:size="logDrawerSize"
			:close-on-click-modal="true"
			destroy-on-close
			class="log-drawer"
		>
			<div class="log-console" v-loading="logDrawer.loading">
				<pre v-if="logDrawer.content">{{ logDrawer.content }}</pre>
				<div v-else-if="!logDrawer.loading" class="log-empty">暂无日志内容</div>
			</div>
		</el-drawer>

		<!-- 下载报告抽屉 -->
		<el-drawer
			v-model="downloadDrawer.visible"
			title="下载压测报告"
			direction="rtl"
			:size="downloadDrawerSize"
			:close-on-click-modal="false"
			destroy-on-close
			class="download-drawer"
		>
			<el-form label-width="90px" class="download-form">
				<el-form-item label="报告 ID" required>
					<el-select
						v-model="downloadForm.reportId"
						placeholder="请选择已完成的报告"
						style="width: 100%"
						filterable
					>
						<el-option
							v-for="r in completedReports"
							:key="r.id"
							:value="r.id"
							:label="r.report_code"
						/>
					</el-select>
				</el-form-item>
				<el-form-item label="下载内容" required>
					<el-checkbox-group v-model="downloadForm.types" class="download-checks">
						<el-checkbox label="report">HTML 报告</el-checkbox>
						<el-checkbox label="log">JMeter 运行日志</el-checkbox>
						<el-checkbox label="jtl">JTL 结果文件</el-checkbox>
					</el-checkbox-group>
				</el-form-item>
				<div class="download-hint">
					<el-icon><ele-InfoFilled /></el-icon>
					每个文件将在新标签页中独立下载
				</div>
			</el-form>
			<template #footer>
				<el-button @click="downloadDrawer.visible = false">取消</el-button>
				<el-button
					type="primary"
					:disabled="!downloadForm.reportId || !downloadForm.types.length"
					:loading="downloadDrawer.loading"
					@click="confirmDownload"
				>
					确定
				</el-button>
			</template>
		</el-drawer>

		<!-- 收集进度抽屉 -->
		<CollectProgressDrawer ref="progressDrawerRef" @collected="onCollected" @closed="onProgressClosed" />
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onActivated } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useRoute } from 'vue-router';
import { usePerformanceApi } from '/@/api/v1/performance';
import { formatDateTime } from '/@/utils/formatTime';
import CollectProgressDrawer from './CollectProgress.vue';

const perfApi = usePerformanceApi();
const route = useRoute();

// ======================== 已关闭弹窗的报告 ID（sessionStorage 持久化） ========================
const DISMISSED_KEY = 'perf_report_dismissed_ids';

function loadDismissed(): Set<number> {
	try {
		const raw = sessionStorage.getItem(DISMISSED_KEY);
		return new Set(raw ? JSON.parse(raw) : []);
	} catch { return new Set(); }
}

function saveDismissed(ids: Set<number>) {
	sessionStorage.setItem(DISMISSED_KEY, JSON.stringify([...ids]));
}

const dismissedIds = ref<Set<number>>(loadDismissed());

function onProgressClosed(reportId: number) {
	dismissedIds.value.add(reportId);
	saveDismissed(dismissedIds.value);
}

// ======================== 查询参数 ========================
const query = reactive({
	report_name:   '',
	scenario_code: '',
	creator:       '',
	timeRange:     [] as string[],
});

const pagination = reactive({ page: 1, page_size: 20, total: 0 });

// ======================== 表格数据 ========================
const loading   = ref(false);
const tableData = ref<any[]>([]);

async function fetchList(autoOpenProgress = false) {
	loading.value = true;
	try {
		const params: any = {
			page:      pagination.page,
			page_size: pagination.page_size,
		};
		if (query.report_name)          params.report_name   = query.report_name;
		if (query.scenario_code)        params.scenario_code = query.scenario_code;
		if (query.creator)              params.creator       = query.creator;
		if (query.timeRange?.length === 2) {
			params.generated_at_start = query.timeRange[0];
			params.generated_at_end   = query.timeRange[1];
		}
		const res: any = await perfApi.getReportList(params);
		if (res?.code === 200) {
			tableData.value  = res.data?.items ?? [];
			pagination.total = res.data?.total ?? 0;

			if (autoOpenProgress) {
				const collecting = tableData.value.find(
					r => r.report_status === 1 && !dismissedIds.value.has(r.id)
				);
				if (collecting) {
					progressDrawerRef.value?.open(collecting);
				}
			}
		}
	} finally {
		loading.value = false;
	}
}

function handleQuery() {
	pagination.page = 1;
	fetchList();
}

function resetQuery() {
	query.report_name   = '';
	query.scenario_code = '';
	query.creator       = '';
	query.timeRange     = [];
	handleQuery();
}

// ======================== 日志文件列表（悬停懒加载，按报告 ID 缓存） ========================
const logFilesCache:   Record<number, string[]> = reactive({});
const logFilesLoading: Record<number, boolean>  = reactive({});

async function loadLogFiles(row: any) {
	if (logFilesCache[row.id] !== undefined) return;
	logFilesLoading[row.id] = true;
	try {
		const res: any = await perfApi.getReportLog(row.id, 'console');
		logFilesCache[row.id] = res?.code === 200 ? (res.data?.files ?? []) : [];
	} catch {
		logFilesCache[row.id] = [];
	} finally {
		logFilesLoading[row.id] = false;
	}
}

// ======================== 在线日志抽屉 ========================
const logDrawer = reactive({
	visible: false,
	loading: false,
	title:   '',
	content: '',
});

const logDrawerSize = computed(() => {
	if (typeof window === 'undefined') return '720px';
	return Math.max(540, Math.floor(window.innerWidth / 2)) + 'px';
});

const downloadDrawerSize = computed(() => {
	if (typeof window === 'undefined') return '480px';
	return Math.max(420, Math.floor(window.innerWidth / 3)) + 'px';
});

async function openLogByFile(row: any, filename: string) {
	logDrawer.title   = `${row.report_code} - ${filename}`;
	logDrawer.content = '';
	logDrawer.visible = true;
	logDrawer.loading = true;
	try {
		const res: any = await perfApi.getReportLog(row.id, 'console', filename);
		logDrawer.content = res?.code === 200 ? (res.data?.content || '暂无内容') : '加载失败';
	} catch {
		logDrawer.content = '加载日志失败，请重试';
	} finally {
		logDrawer.loading = false;
	}
}

// ======================== 下载报告抽屉 ========================
const downloadDrawer = reactive({ visible: false, loading: false });

const downloadForm = reactive({
	reportId: null as number | null,
	types:    ['report', 'log', 'jtl'] as string[],
});

// 从已加载的表格数据中取已完成报告，避免额外请求
const completedReports = computed(() =>
	tableData.value.filter((r: any) => r.report_status === 2)
);

function openDownloadDrawer() {
	downloadForm.reportId = null;
	downloadForm.types    = ['report', 'log', 'jtl'];
	downloadDrawer.visible = true;
}

const TYPE_LABELS: Record<string, string> = {
	report: 'HTML 报告',
	log:    'JMeter 运行日志',
	jtl:    'JTL 结果文件',
};

async function confirmDownload() {
	if (!downloadForm.reportId || !downloadForm.types.length) return;
	downloadDrawer.loading = true;
	try {
		const res: any = await perfApi.getReportDownloadUrl(downloadForm.reportId, downloadForm.types);
		if (res?.code === 200) {
			const urls = res.data ?? {};
			let opened = 0;
			for (const t of downloadForm.types) {
				if (urls[t]) {
					window.open(urls[t], '_blank');
					opened++;
				} else {
					ElMessage.warning(`${TYPE_LABELS[t] ?? t} 文件不存在，已跳过`);
				}
			}
			if (opened > 0) downloadDrawer.visible = false;
		}
	} catch {
		ElMessage.error('获取下载链接失败');
	} finally {
		downloadDrawer.loading = false;
	}
}

// ======================== 操作按钮 ========================
const progressDrawerRef = ref<InstanceType<typeof CollectProgressDrawer>>();

function handleViewProgress(row: any) {
	progressDrawerRef.value?.open(row);
}

function onCollected(_report: any) {
	fetchList();
}

async function handleForceStop(row: any) {
	try {
		await ElMessageBox.confirm(
			`确认强制停止报告「${row.report_name}」的收集？可在停止后选择恢复收集。`,
			'强制停止确认',
			{ type: 'warning', confirmButtonText: '确认停止', cancelButtonText: '取消' }
		);
	} catch {
		return;
	}
	try {
		const res: any = await perfApi.stopReport(row.id);
		if (res?.code === 200) {
			ElMessage.success('已强制停止，状态变更为"中断"');
			fetchList();
		}
	} catch {
		ElMessage.error('操作失败，请重试');
	}
}

async function handleResume(row: any) {
	try {
		await ElMessageBox.confirm(
			`确认恢复报告「${row.report_name}」的收集？系统将校验源文件 MD5 后继续收集一致的文件。`,
			'恢复收集确认',
			{ type: 'info', confirmButtonText: '确认恢复', cancelButtonText: '取消' }
		);
	} catch {
		return;
	}
	progressDrawerRef.value?.open({ ...row, report_status: 1 });
	try {
		const res: any = await perfApi.resumeReport(row.id);
		if (res?.code === 200) {
			ElMessage.success('已重新启动收集任务');
			fetchList();
		}
	} catch (err: any) {
		const detail = err?.response?.data?.detail || err?.message || '操作失败';
		ElMessage.error(detail);
	}
}

function handlePreview(row: any) {
	const url = perfApi.getReportPreviewUrl(row.report_code);
	window.open(url, '_blank');
}

async function handleDelete(row: any) {
	try {
		await ElMessageBox.confirm(
			`确认删除报告「${row.report_name}」？将同步删除 Minio 文件，操作不可恢复。`,
			'删除确认',
			{ type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }
		);
	} catch {
		return;
	}
	try {
		const res: any = await perfApi.deleteReport(row.id);
		if (res?.code === 200) {
			ElMessage.success('删除成功');
			fetchList();
		}
	} catch {
		ElMessage.error('删除失败');
	}
}

/** 一键打开当前列表第一条收集中（status=1）报告的进度抽屉 */
function handleQuickCollect() {
	const collecting = tableData.value.find(r => r.report_status === 1);
	if (!collecting) {
		ElMessage.warning('当前列表暂无收集中的报告，请先启动压测或刷新列表');
		return;
	}
	dismissedIds.value.delete(collecting.id);
	saveDismissed(dismissedIds.value);
	progressDrawerRef.value?.open(collecting);
}

// ======================== 状态标签工具 ========================
function statusLabel(status: number): string {
	const map: Record<number, string> = { 1: '收集中', 2: '完成', 3: '中断', 4: '失败' };
	return map[status] ?? '未知';
}

function statusTagType(status: number): string {
	const map: Record<number, string> = { 1: 'primary', 2: 'success', 3: 'warning', 4: 'danger' };
	return map[status] ?? 'info';
}

function formatFileSize(bytes: number): string {
	if (!bytes || bytes <= 0) return '0 B';
	const units = ['B', 'KB', 'MB', 'GB', 'TB'];
	const i = Math.floor(Math.log(bytes) / Math.log(1024));
	return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 2)} ${units[i]}`;
}

onMounted(() => {
	if (route.query.scene_no) {
		query.scenario_code = route.query.scene_no as string;
	}
	const navType = (performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming)?.type;
	fetchList(navType !== 'reload');
});

onActivated(() => {
	fetchList(true);
});
</script>

<style scoped lang="scss">
.perf-report-container {
	padding: 10px 10px 20px 10px;

	:deep(.el-card__body) {
		padding: 10px 10px 20px 10px;
	}

	:deep(.el-button > span) {
		display: inline-flex !important;
		align-items: center !important;
		line-height: 1 !important;
	}

	:deep(.el-input__inner),
	:deep(.el-textarea__inner) {
		font-size: 13.5px;
	}

	:deep(.el-select__placeholder),
	:deep(.el-select__selected-item) {
		font-size: 13.5px;
	}

	:deep(.el-tag) {
		font-size: 13px;
		padding: 0 8px;
	}

	:deep(.el-table) {
		font-size: 13.5px;
		margin-top: 12px;

		.el-table__header th {
			font-size: 13.5px;
			background-color: var(--el-fill-color-light);
			text-align: center;
		}

		.el-table__header th .cell {
			display: flex;
			align-items: center;
			justify-content: center;
			white-space: nowrap;
		}

		.el-table__cell {
			padding: 11px 0;
		}
	}

	.toolbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: 10px;
		margin-bottom: 16px;
	}

	.toolbar-left {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 10px;
		flex: 1 1 auto;
		min-width: 0;
	}

	.toolbar-right {
		display: flex;
		align-items: center;
		gap: 10px;
		flex-shrink: 0;
	}

	.pagination {
		margin-top: 16px;
		display: flex;
		justify-content: flex-end;
	}

	.action-btns {
		display: flex;
		align-items: center;
		justify-content: center;
		flex-wrap: nowrap;

		:deep(.el-button) {
			padding: 0 4px;
			font-weight: 600;
			white-space: nowrap;

			.el-icon {
				margin-right: 2px;
			}
		}
	}

	.tip-icon {
		margin-left: 4px;
		color: var(--el-text-color-secondary);
		cursor: help;
		vertical-align: middle;
		font-size: 13.5px;

		&:hover {
			color: var(--el-color-primary);
		}
	}
}

// ── 日志抽屉内容 ───────────────────────────────────────────────────────────────
.log-console {
	height: 100%;
	background: #1e1e1e;
	border-radius: 4px;
	padding: 12px 16px;
	overflow-y: auto;
	box-sizing: border-box;
}

.log-console pre {
	margin: 0;
	font-family: 'Courier New', Courier, monospace;
	font-size: 12px;
	line-height: 1.65;
	color: #d4d4d4;
	white-space: pre-wrap;
	word-break: break-all;
}

.log-empty {
	color: #6c6c6c;
	text-align: center;
	padding: 50px 0;
	font-size: 14px;
}

// ── 下载表单 ───────────────────────────────────────────────────────────────────
.download-form {
	padding: 8px 0;

	.download-checks {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}
}

.download-opt {
	display: flex;
	flex-direction: column;
	line-height: 1.4;
	padding: 3px 0;

	.download-opt-code {
		font-size: 13px;
		color: var(--el-text-color-primary);
		font-family: 'Menlo', 'Consolas', monospace;
	}

	.download-opt-name {
		font-size: 12px;
		color: var(--el-text-color-secondary);
	}
}

.download-hint {
	display: flex;
	align-items: center;
	gap: 5px;
	font-size: 12px;
	color: var(--el-text-color-secondary);
	padding: 4px 0 0 90px;

	.el-icon { color: var(--el-color-info); }
}
</style>

<!-- 日志悬停弹窗 & 抽屉全局样式 -->
<style lang="scss">
.log-popover-loading {
	display: flex;
	align-items: center;
	gap: 6px;
	padding: 8px 4px;
	font-size: 13px;
	color: var(--el-text-color-secondary);

	.el-icon { font-size: 14px; }
}

.log-popover-list {
	display: flex;
	flex-direction: column;
	gap: 2px;
}

.log-popover-item {
	display: flex;
	align-items: center;
	gap: 6px;
	padding: 6px 8px;
	border-radius: 4px;
	font-size: 13px;
	color: var(--el-text-color-primary);
	cursor: pointer;
	transition: background 0.15s;
	font-family: 'Menlo', 'Consolas', monospace;

	.el-icon {
		font-size: 13px;
		color: var(--el-text-color-secondary);
		flex-shrink: 0;
	}

	&:hover {
		background: var(--el-fill-color);
		color: var(--el-color-primary);

		.el-icon { color: var(--el-color-primary); }
	}
}

.log-popover-empty {
	padding: 8px 4px;
	font-size: 13px;
	color: var(--el-text-color-placeholder);
	text-align: center;
}

// 日志抽屉：body 撑满高度供日志滚动
.log-drawer {
	.el-drawer__body {
		padding: 12px !important;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}
}

// 下载抽屉：footer 右对齐
.download-drawer {
	.el-drawer__footer {
		display: flex;
		justify-content: flex-end;
		gap: 8px;
		padding: 12px 20px !important;
		border-top: 1px solid var(--el-border-color-lighter);
	}
}
</style>
