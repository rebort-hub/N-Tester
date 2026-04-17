<template>
	<div class="result-list-container">
		<el-card shadow="hover" :body-style="{ paddingBottom: '0' }">
			<el-form :inline="true" :model="searchParams.search">
				<el-form-item label="任务名称">
					<el-input
						v-model="searchParams.search.name"
						placeholder="请输入任务名称"
						clearable
						style="width: 220px"
						@keyup.enter="get_script_result_list"
					/>
				</el-form-item>
				<el-form-item>
					<el-button type="primary" icon="Search" @click="get_script_result_list">搜索</el-button>
					<el-button icon="Refresh" @click="reset_search">重置</el-button>
				</el-form-item>
			</el-form>
		</el-card>

		<el-card shadow="hover" style="margin-top: 8px">
			<el-table
				v-loading="loading"
				:data="table_data"
				border
				stripe
				empty-text="暂无数据"
				:fit="true"
				table-layout="auto"
				style="width: 100%"
			>
				<el-table-column type="index" label="序号" width="60" align="center" />
				<el-table-column prop="name" label="任务名称" min-width="140" show-overflow-tooltip />
				<el-table-column label="任务状态" width="110" align="center">
					<template #default="{ row }">
						<el-tag :type="statusMeta(row.status).tagType">{{ statusMeta(row.status).text }}</el-tag>
					</template>
				</el-table-column>
				<el-table-column label="通过率" width="160" align="center">
					<template #default="{ row }">
						<el-progress :percentage="row.result?.percent ?? 0" :color="customColors" :stroke-width="10" />
					</template>
				</el-table-column>
				<el-table-column label="执行人" prop="username" width="100" align="center" show-overflow-tooltip />
				<el-table-column label="开始时间" width="170" align="center">
					<template #default="{ row }">
						{{ row.start_time ? String(row.start_time).replace('T', ' ') : '-' }}
					</template>
				</el-table-column>
				<el-table-column label="结束时间" width="170" align="center">
					<template #default="{ row }">
						{{ row.end_time ? String(row.end_time).replace('T', ' ') : '-' }}
					</template>
				</el-table-column>
				<el-table-column label="操作" width="340" align="center" fixed="right">
					<template #default="{ row }">
						<span class="action-cell">
							<el-button type="success" size="small" @click="viewDetail(row)">详情</el-button>
							<el-button
								v-if="statusMeta(row.status).isRunning"
								type="danger"
								size="small"
								@click="stop_run(row.result_id)"
							>停止</el-button>

							<el-button
								v-if="statusMeta(row.status).canViewReport"
								type="primary"
								size="small"
								@click="view_report(row.result_id)"
							>查看报告</el-button>

							<el-button
								v-if="statusMeta(row.status).canRerun"
								type="info"
								size="small"
								@click="rerun(row)"
							>重跑</el-button>

							<el-button
								v-else
								type="info"
								size="small"
								disabled
								title="执行中可先停止"
							>重跑</el-button>

							<el-button type="danger" size="small" @click="del_run(row)">删除</el-button>
						</span>
					</template>
				</el-table-column>
			</el-table>

			<div style="margin-top: 12px">
				<el-pagination
					v-show="total > 0"
					background
					v-model:current-page="searchParams.currentPage"
					v-model:page-size="searchParams.pageSize"
					:page-sizes="[10, 25, 50, 100]"
					layout="total, sizes, prev, pager, next, jumper"
					:total="total"
					@size-change="get_script_result_list"
					@current-change="get_script_result_list"
				/>
			</div>
		</el-card>

		<!-- 用例详情抽屉 -->
		<el-drawer
			v-model="detailDrawerVisible"
			direction="rtl"
			size="480px"
			destroy-on-close
			:show-close="false"
		>
			<template #header="{ close }">
				<div class="drawer-header">
					<div class="drawer-header-info">
						<div class="drawer-title">{{ detailRow?.name }}</div>
						<div class="drawer-subtitle">
							<span>{{ detailRow?.start_time ? String(detailRow.start_time).replace('T',' ').slice(0,19) : '' }}</span>
							<span v-if="detailRow?.end_time" style="margin-left:8px">→ {{ String(detailRow.end_time).replace('T',' ').slice(0,19) }}</span>
						</div>
					</div>
					<el-icon class="drawer-close" @click="close"><Close /></el-icon>
				</div>
			</template>

			<!-- 汇总卡片 -->
			<div class="detail-summary-cards">
				<div class="summary-card">
					<div class="sc-val">{{ detailRow?.result?.total ?? (detailRow?.script?.length ?? 0) }}</div>
					<div class="sc-label">总用例</div>
				</div>
				<div class="summary-card pass-card">
					<div class="sc-val">{{ detailRow?.result?.pass ?? 0 }}</div>
					<div class="sc-label">通过</div>
				</div>
				<div class="summary-card fail-card">
					<div class="sc-val">{{ detailRow?.result?.fail ?? 0 }}</div>
					<div class="sc-label">失败</div>
				</div>
				<div class="summary-card rate-card">
					<div class="sc-val">{{ detailRow?.result?.percent ?? 0 }}%</div>
					<div class="sc-label">通过率</div>
				</div>
			</div>

			<!-- 进度条 -->
			<div class="detail-progress">
				<el-progress
					:percentage="detailRow?.result?.percent ?? 0"
					:color="[{color:'#f56c6c',percentage:99.99},{color:'#67c23a',percentage:100}]"
					:stroke-width="8"
					:show-text="false"
				/>
			</div>

			<!-- 用例列表 -->
			<div class="detail-section-title">用例明细</div>
			<div class="detail-case-list">
				<div
					v-for="(step, i) in (detailRow?.script || [])"
					:key="i"
					class="detail-case-item"
					:class="(step.fail ?? 0) > 0 ? 'item-fail' : 'item-pass'"
				>
					<div class="case-status-bar" :class="(step.fail ?? 0) > 0 ? 'bar-fail' : 'bar-pass'" />
					<div class="case-item-body">
						<div class="case-item-top">
							<span class="case-index" :class="(step.fail ?? 0) > 0 ? 'idx-fail' : 'idx-pass'">{{ i + 1 }}</span>
							<span class="case-name">{{ step.name }}</span>
							<el-tag
								:type="(step.fail ?? 0) === 0 ? 'success' : 'danger'"
								size="small"
								effect="dark"
								round
								style="margin-left:auto;flex-shrink:0"
							>{{ (step.fail ?? 0) === 0 ? '✓ 通过' : '✗ 失败' }}</el-tag>
						</div>
						<div v-if="step.pass !== undefined || step.fail !== undefined" class="case-item-stats">
							<span class="stat-pass">通过 {{ step.pass ?? 0 }} 步</span>
							<span class="stat-sep">·</span>
							<span class="stat-fail">失败 {{ step.fail ?? 0 }} 步</span>
						</div>
					</div>
				</div>
				<div v-if="!detailRow?.script?.length" class="detail-empty">
					暂无用例明细
				</div>
			</div>
		</el-drawer>
	</div>
</template>
<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Close } from '@element-plus/icons-vue';
import { useApiAutomationApi } from '/@/api/v1/api_automation';
import { getExecutionStatusMeta } from '/@/utils/executionStatus';

const props = withDefaults(defineProps<{ serviceId?: number }>(), { serviceId: 0 });

const {
	get_api_script_result_list,
	run_api_script,
	stop_api_script_result,
	del_api_script_result,
} = useApiAutomationApi();

const table_data = ref<any[]>([]);
const loading = ref(false);
const searchParams = ref({
	currentPage: 1,
	pageSize: 10,
	search: {
		name: '',
	},
});
const customColors = ref<any>([
	{ color: '#ea2e2e', percentage: 99.99 },
	{ color: '#81d36f', percentage: 100 },
]);
const total = ref(0);
const statusMeta = (status: number) => getExecutionStatusMeta(status);

const get_script_result_list = async () => {
	loading.value = true;
	try {
		const res: any = await get_api_script_result_list({
			page: searchParams.value.currentPage,
			pageSize: searchParams.value.pageSize,
			search: searchParams.value.search,
			...(props.serviceId ? { api_service_id: props.serviceId } : {}),
		});
		const raw = res?.data;
		const list = Array.isArray(raw?.content) ? raw.content : (Array.isArray(raw) ? raw : []);
		table_data.value = list.map((r: any) => ({
			...r,
			status: r.status ?? (r.end_time ? 1 : 0),
			result: r.result || {},
			script: r.script || [],
		}));
		total.value = typeof raw?.total === 'number' ? raw.total : list.length;
	} finally {
		loading.value = false;
	}
};

const reset_search = () => {
	searchParams.value.currentPage = 1;
	searchParams.value.pageSize = 10;
	searchParams.value.search.name = '';
	get_script_result_list();
};

const view_report = (result_id: any) => {
	window.open(`/api-automation/report?result_id=${result_id}`, '_blank');
};

const stop_run = async (result_id: number) => {
	try {
		await stop_api_script_result({ result_id });
		ElMessage.success('已请求停止');
		await get_script_result_list();
	} catch (e: any) {
		ElMessage.error(e?.message || '停止失败');
	}
};

const rerun = async (row: any) => {
	try {
		const newId = Date.now();
		if (!row?.config?.env_id) {
			ElMessage.warning('无法重跑：缺少环境配置，请从场景页重新执行');
			return;
		}
		await run_api_script({
			result_id: newId,
			name: row.name,
			config: row.config,
			run_list: row.script || [],
		});
		ElMessage.success('已发起重跑');
		await get_script_result_list();
	} catch (e: any) {
		ElMessage.error(e?.message || '重跑失败');
	}
};

const detailDrawerVisible = ref(false);
const detailRow = ref<any>(null);

const viewDetail = (row: any) => {
	detailRow.value = row;
	detailDrawerVisible.value = true;
};

const del_run = async (row: any) => {
	try {
		await ElMessageBox.confirm(
			'确认删除该执行记录？若正在执行将先请求停止再删除，该操作不可恢复。',
			'提示',
			{
				type: 'warning',
				confirmButtonText: '确定',
				cancelButtonText: '取消',
			},
		);
		await del_api_script_result({ result_id: row.result_id });
		ElMessage.success('删除成功');
		await get_script_result_list();
	} catch (e: any) {
		if (e === 'cancel' || e === 'close') return;
		ElMessage.error(e?.message || '删除失败');
	}
};

onMounted(() => {
	get_script_result_list();
});
</script>

<style scoped>
.result-list-container { padding: 10px; }
.action-cell { white-space: nowrap; }

/* 抽屉头部 */
.drawer-header { display: flex; align-items: flex-start; justify-content: space-between; width: 100%; }
.drawer-header-info { flex: 1; min-width: 0; }
.drawer-title { font-size: 16px; font-weight: 600; color: var(--el-text-color-primary); margin-bottom: 4px; word-break: break-all; }
.drawer-subtitle { font-size: 12px; color: var(--el-text-color-placeholder); }
.drawer-close { font-size: 20px; color: var(--el-text-color-placeholder); cursor: pointer; flex-shrink: 0; margin-left: 12px; }
.drawer-close:hover { color: var(--el-text-color-regular); }

/* 汇总卡片 */
.detail-summary-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 16px; }
.summary-card { background: linear-gradient(135deg, var(--el-fill-color-light), var(--el-bg-color)); border: 1px solid var(--el-border-color-lighter); border-radius: 10px; padding: 16px 12px; text-align: center; transition: all .2s; }
.summary-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,.08); }
.sc-val { font-size: 26px; font-weight: 700; color: var(--el-text-color-primary); margin-bottom: 4px; }
.sc-label { font-size: 12px; color: var(--el-text-color-placeholder); letter-spacing: .5px; }
.pass-card { background: linear-gradient(135deg, #f0f9ff, #e6f7ff); border-color: #b7eb8f; }
.pass-card .sc-val { color: #52c41a; }
.fail-card { background: linear-gradient(135deg, #fff1f0, #ffebe8); border-color: #ffccc7; }
.fail-card .sc-val { color: #ff4d4f; }
.rate-card { background: linear-gradient(135deg, #f9f0ff, #f3e8ff); border-color: #d3adf7; }
.rate-card .sc-val { color: #722ed1; }

/* 进度条 */
.detail-progress { margin-bottom: 20px; }

/* 区块标题 */
.detail-section-title { font-size: 13px; font-weight: 600; color: var(--el-text-color-primary); margin-bottom: 12px; padding-left: 10px; border-left: 3px solid #409eff; }

/* 用例列表 */
.detail-case-list { display: flex; flex-direction: column; gap: 10px; }
.detail-case-item { position: relative; background: var(--el-bg-color); border: 1px solid var(--el-border-color-lighter); border-radius: 8px; overflow: hidden; transition: all .2s; }
.detail-case-item:hover { box-shadow: 0 2px 8px rgba(0,0,0,.06); }
.item-pass { border-left-color: #52c41a; border-left-width: 3px; }
.item-fail { border-left-color: #ff4d4f; border-left-width: 3px; }
.case-status-bar { position: absolute; left: 0; top: 0; bottom: 0; width: 3px; }
.bar-pass { background: linear-gradient(to bottom, #52c41a, #95de64); }
.bar-fail { background: linear-gradient(to bottom, #ff4d4f, #ff7875); }
.case-item-body { padding: 12px 14px 12px 18px; }
.case-item-top { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.case-index { width: 24px; height: 24px; border-radius: 50%; font-size: 12px; font-weight: 600; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.idx-pass { background: #f6ffed; color: #52c41a; border: 1px solid #b7eb8f; }
.idx-fail { background: #fff1f0; color: #ff4d4f; border: 1px solid #ffccc7; }
.case-name { font-size: 13px; color: var(--el-text-color-primary); font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.case-item-stats { display: flex; align-items: center; gap: 6px; font-size: 12px; padding-left: 34px; }
.stat-pass { color: #52c41a; }
.stat-fail { color: #ff4d4f; }
.stat-sep { color: var(--el-text-color-placeholder); }
.detail-empty { text-align: center; color: var(--el-text-color-placeholder); padding: 40px 0; font-size: 13px; }
</style>
