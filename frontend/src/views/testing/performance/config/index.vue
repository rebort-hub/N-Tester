<template>
	<div class="perf-config-container">
		<el-card shadow="hover">
			<el-tabs v-model="activeTab" class="config-tabs">
				<!-- ========== Tab1：压力机配置 ========== -->
				<el-tab-pane label="压力机配置" name="worker">
					<!-- 工具栏 -->
					<div class="toolbar">
						<div class="toolbar-left">
							<el-input
								v-model="workerQuery.name"
								placeholder="搜索名称"
								clearable
								style="width: 300px"
								@keyup.enter="handleWorkerQuery"
							@clear="handleWorkerQuery"
							>
								<template #prefix><el-icon><ele-Search /></el-icon></template>
							</el-input>
							<el-select v-model="workerQuery.status" placeholder="状态" clearable style="width: 160px" @change="handleWorkerQuery">
								<el-option v-for="opt in statusOptions" :key="opt.value" :value="opt.value" :label="opt.label" />
							</el-select>
							<el-button type="primary" @click="handleWorkerQuery">
								<el-icon><ele-Search /></el-icon>搜索
							</el-button>
							<el-button @click="resetWorkerQuery">
								<el-icon><ele-Refresh /></el-icon>重置
							</el-button>
						</div>
						<div class="toolbar-right">
							<el-button type="primary" @click="handleWorkerAdd">
								<el-icon><ele-Plus /></el-icon>新增
							</el-button>
						</div>
					</div>

					<!-- 表格 -->
					<el-table v-loading="workerLoading" :data="workerList" border stripe style="width: 100%">
						<el-table-column prop="name" min-width="150" align="center" show-overflow-tooltip>
							<template #header>
								<span>压力机名称</span>
								<el-tooltip content="压力机节点的显示名称，用于标识区分，如 jmeter-worker-1、jmeter-master等" placement="top">
									<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
								</el-tooltip>
							</template>
						</el-table-column>
						<el-table-column prop="type" min-width="105" align="center">
							<template #header>
								<span>压力机类型</span>
								<el-tooltip content="单机：单机压测；Master：分布式控制机；Slave：分布式执行机" placement="top">
									<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
								</el-tooltip>
							</template>
							<template #default="{ row }">
								<el-tag
									:type="row.type === 'master' ? 'warning' : row.type === 'slave' ? 'success' : 'primary'"
									size="small"
								>
									{{ row.type === 'master' ? 'Master' : row.type === 'slave' ? 'Slave' : '单机' }}
								</el-tag>
							</template>
						</el-table-column>
						<el-table-column prop="status" min-width="95" align="center">
							<template #header><span>状态</span></template>
							<template #default="{ row }">
								<el-switch
									v-model="row.status"
									:active-value="1"
									:inactive-value="0"
									active-text="启用"
									inactive-text="禁用"
									inline-prompt
									size="default"
									@change="handleWorkerStatusChange(row)"
								/>
							</template>
						</el-table-column>
						<el-table-column prop="ip" min-width="140" align="center" show-overflow-tooltip>
							<template #header>
								<span>机器IP</span>
								<el-tooltip content="机器IP或DNS域名；物理机/云主机填IP，K8S Pod填Headless Service DNS" placement="top">
									<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
								</el-tooltip>
							</template>
							<template #default="{ row }">
								<span style="white-space: nowrap">{{ row.ip }}</span>
							</template>
						</el-table-column>
						<el-table-column prop="ssh_port" min-width="100" align="center">
							<template #header>
								<span>SSH 端口</span>
								<el-tooltip content="SSH 连接端口，用于文件分发和远程命令执行，默认 22" placement="top">
									<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
								</el-tooltip>
							</template>
						</el-table-column>
						<el-table-column prop="rmi_port" min-width="100" align="center">
							<template #header>
								<span>RMI 端口</span>
								<el-tooltip content="Worker 上 jmeter-server 监听的 RMI 端口，默认 1099" placement="top">
									<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
								</el-tooltip>
							</template>
						</el-table-column>
						<el-table-column prop="monitor_port" min-width="100" align="center">
							<template #header>
								<span>Monitor</span>
								<el-tooltip content="Prometheus 监控端口，用于采集压力机性能指标，默认 9270" placement="top">
									<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
								</el-tooltip>
							</template>
						</el-table-column>
						<el-table-column prop="max_concurrency" min-width="110" align="center">
							<template #header>
								<span>最大并发数</span>
								<el-tooltip content="该节点物理支持的最大并发用户数，超出此值可能导致机器过载" placement="top">
									<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
								</el-tooltip>
							</template>
						</el-table-column>
						<el-table-column prop="updated_at" label="最后操作时间" min-width="160" align="center">
							<template #default="{ row }"><span style="white-space: nowrap">{{ formatDateTime(row.updated_at) }}</span></template>
						</el-table-column>
						<el-table-column prop="operator_name" label="操作人" min-width="90" align="center">
							<template #default="{ row }">{{ row.operator_name || "-" }}</template>
						</el-table-column>
						<el-table-column prop="remark" label="备注" min-width="180" show-overflow-tooltip />
						<el-table-column label="操作" width="210" fixed="right" align="center" class-name="operation-col">
							<template #default="{ row }">
								<div class="action-btns">
									<el-button type="primary" size="small" text @click="handleWorkerEdit(row)">
										<el-icon><ele-Edit /></el-icon>修改
									</el-button>
									<el-button type="success" size="small" text @click="handleWorkerCopy(row)">
										<el-icon><ele-CopyDocument /></el-icon>复制
									</el-button>
									<el-button type="danger" size="small" text @click="handleWorkerDelete(row)">
										<el-icon><ele-Delete /></el-icon>删除
									</el-button>
								</div>
							</template>
						</el-table-column>
					</el-table>

					<!-- 分页 -->
					<el-pagination
						v-show="workerTotal > 0"
						v-model:current-page="workerQuery.page"
						v-model:page-size="workerQuery.page_size"
						:page-sizes="[10, 20, 50]"
						:total="workerTotal"
						layout="total, sizes, prev, pager, next, jumper"
						class="pagination"
						@size-change="handleWorkerQuery"
						@current-change="handleWorkerQuery"
					/>
				</el-tab-pane>

				<!-- ========== Tab2：参数配置 ========== -->
				<el-tab-pane label="参数配置" name="param">
					<!-- 工具栏 -->
					<div class="toolbar">
						<div class="toolbar-left">
							<el-input
								v-model="paramQuery.name"
								placeholder="搜索参数名称/参数名"
								clearable
								style="width: 300px"
								@keyup.enter="handleParamQuery"
							@clear="handleParamQuery"
							>
								<template #prefix><el-icon><ele-Search /></el-icon></template>
							</el-input>
							<el-select v-model="paramQuery.status" placeholder="状态" clearable style="width: 160px" @change="handleParamQuery">
								<el-option v-for="opt in statusOptions" :key="opt.value" :value="opt.value" :label="opt.label" />
							</el-select>
							<el-button type="primary" @click="handleParamQuery">
								<el-icon><ele-Search /></el-icon>搜索
							</el-button>
							<el-button @click="resetParamQuery">
								<el-icon><ele-Refresh /></el-icon>重置
							</el-button>
						</div>
						<div class="toolbar-right">
							<el-button type="primary" @click="handleParamAdd">
								<el-icon><ele-Plus /></el-icon>新增
							</el-button>
						</div>
					</div>

					<!-- 表格 -->
					<el-table v-loading="paramLoading" :data="paramList" border stripe style="width: 100%">
						<el-table-column type="index" label="编号" width="50" align="center" />
						<el-table-column prop="label" min-width="130" show-overflow-tooltip>
							<template #header>
								<span>参数名称</span>
								<el-tooltip content="参数的中文说明，如「远程 Worker 上的目标目录」" placement="top">
									<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
								</el-tooltip>
							</template>
						</el-table-column>
						<el-table-column prop="key" min-width="140" show-overflow-tooltip>
							<template #header>
								<span>参数名</span>
								<el-tooltip content="参数的英文标识，通常为全大写，如 REMOTE_PATH" placement="top">
									<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
								</el-tooltip>
							</template>
							<template #default="{ row }">
								<span class="key-badge">{{ row.key }}</span>
							</template>
						</el-table-column>
						<el-table-column prop="value" min-width="130" show-overflow-tooltip>
							<template #header>
								<span>参数值</span>
								<el-tooltip content="参数的实际值，如 /data/jmeter/" placement="top">
									<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
								</el-tooltip>
							</template>
						</el-table-column>
						<el-table-column prop="status" label="状态" width="80" align="center">
							<template #default="{ row }">
								<el-switch
									v-model="row.status"
									:active-value="1"
									:inactive-value="0"
									active-text="启用"
									inactive-text="禁用"
									inline-prompt
									size="default"
									:disabled="!!row.is_system"
									@change="handleParamStatusChange(row)"
								/>
							</template>
						</el-table-column>
						<el-table-column prop="updated_at" label="最后操作时间" min-width="130" align="center">
							<template #default="{ row }"><span style="white-space: nowrap">{{ formatDateTime(row.updated_at) }}</span></template>
						</el-table-column>
						<el-table-column prop="operator_name" label="操作人" min-width="60" align="center">
							<template #default="{ row }">{{ row.operator_name || "-" }}</template>
						</el-table-column>
						<el-table-column prop="remark" label="备注" min-width="130" show-overflow-tooltip />
						<el-table-column label="操作" width="170" fixed="right" align="center" class-name="operation-col">
							<template #default="{ row }">
								<div class="action-btns">
									<el-button type="primary" size="small" text @click="handleParamEdit(row)">
										<el-icon><ele-Edit /></el-icon>修改
									</el-button>
									<el-button v-if="!row.is_system" type="danger" size="small" text @click="handleParamDelete(row)">
										<el-icon><ele-Delete /></el-icon>删除
									</el-button>
									<el-tag v-if="row.is_system" type="warning" size="small" effect="plain" style="margin-left: 4px">系统参数</el-tag>
								</div>
							</template>
						</el-table-column>
					</el-table>

					<!-- 分页 -->
					<el-pagination
						v-show="paramTotal > 0"
						v-model:current-page="paramQuery.page"
						v-model:page-size="paramQuery.page_size"
						:page-sizes="[10, 20, 50]"
						:total="paramTotal"
						layout="total, sizes, prev, pager, next, jumper"
						class="pagination"
						@size-change="handleParamQuery"
						@current-change="handleParamQuery"
					/>
				</el-tab-pane>
			</el-tabs>
		</el-card>

		<!-- ========== 压力机 新增/编辑 对话框 ========== -->
		<el-dialog
			v-model="workerDialogVisible"
			:title="workerDialogTitle"
			width="620px"
			top="6vh"
			:close-on-click-modal="false"
			@close="resetWorkerForm"
		>
			<el-form ref="workerFormRef" :model="workerForm" :rules="workerRules" size="default" label-width="115px" hide-required-asterisk class="worker-form">
					<el-form-item prop="name">
					<template #label>
						<span class="label-txt"><span class="label-star">*</span>压力机名称</span>
						<el-tooltip content="压力机节点的显示名称，用于标识区分，如 jmeter-worker-1、jmeter-master等" placement="top">
							<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<el-input v-model="workerForm.name" placeholder="如 jmeter-worker-1" maxlength="100" show-word-limit />
				</el-form-item>
				<el-form-item prop="type">
					<template #label>
						<span class="label-txt"><span class="label-star">*</span>压力机类型</span>
						<el-tooltip content="单机：单节点独立压测；Master：分布式主控节点，负责调度；Slave：分布式执行节点，接受 Master 调度" placement="top">
							<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<el-radio-group v-model="workerForm.type" @change="workerFormRef?.validateField('name')">
						<el-radio value="standalone">单机</el-radio>
						<el-radio value="master">Master</el-radio>
						<el-radio value="slave">Slave</el-radio>
					</el-radio-group>
				</el-form-item>
				<el-form-item prop="status">
					<template #label>
						<span class="label-txt"><span class="label-star">*</span>状态</span>
						<span class="label-tip-placeholder" />
					</template>
					<el-radio-group v-model="workerForm.status">
						<el-radio :value="1">启用</el-radio>
						<el-radio :value="0">禁用</el-radio>
					</el-radio-group>
				</el-form-item>
				<el-form-item prop="ip">
					<template #label>
						<span class="label-txt"><span class="label-star">*</span>机器IP</span>
						<el-tooltip content="机器IP或DNS域名；物理机/云主机填IP，K8S Pod填Headless Service DNS" placement="top">
							<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<el-input v-model="workerForm.ip" placeholder="如 192.168.1.100 或 DNS 域名" />
				</el-form-item>
				<el-form-item prop="ssh_port">
					<template #label>
						<span class="label-txt"><span class="label-star">*</span>SSH 端口</span>
						<el-tooltip content="SSH 连接端口，用于文件分发和远程命令执行，默认 22" placement="top">
							<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<el-input-number v-model="workerForm.ssh_port" :min="1" :max="65535" placeholder="默认 22" style="width: 100%" controls-position="right" />
				</el-form-item>
				<el-form-item prop="rmi_port">
					<template #label>
						<span class="label-txt"><span class="label-star">*</span>RMI 端口</span>
						<el-tooltip content="Worker 上 jmeter-server 监听的 RMI 端口，默认 1099" placement="top">
							<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<el-input-number v-model="workerForm.rmi_port" :min="1" :max="65535" placeholder="默认 1099" style="width: 100%" controls-position="right" />
				</el-form-item>
				<el-form-item prop="monitor_port">
					<template #label>
						<span class="label-txt">Monitor</span>
						<el-tooltip content="Prometheus 监控端口，默认 9270" placement="top">
							<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<el-input-number v-model="workerForm.monitor_port" :min="1" :max="65535" placeholder="输入Prometheus的监控端口，1~65535" style="width: 100%" controls-position="right" />
				</el-form-item>
				<el-form-item prop="max_concurrency">
					<template #label>
						<span class="label-txt">最大并发数</span>
						<el-tooltip content="该节点物理支持的最大并发用户数" placement="top">
							<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<el-input-number v-model="workerForm.max_concurrency" :min="1" placeholder="正整数，如 500" style="width: 100%" controls-position="right" />
				</el-form-item>
				<el-form-item prop="ssh_user">
					<template #label>
						<span class="label-txt">SSH 用户名</span>
						<el-tooltip content="SSH 登录用户名，默认用户root；" placement="top">
							<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<el-input v-model="workerForm.ssh_user" placeholder="输入SSH登录用户名，默认 root" maxlength="100" />
				</el-form-item>
				<el-form-item prop="ssh_password">
					<template #label>
						<span class="label-txt">SSH 密码</span>
						<el-tooltip content="SSH 登录密码，密钥认证失败时兜底。已通过Fernet加密。" placement="top">
							<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<el-input
						v-model="workerForm.ssh_password"
						type="password"
						show-password
						placeholder="输入SSH登录密码"
						maxlength="500"
						autocomplete="new-password"
					/>
				</el-form-item>
				<el-form-item prop="remark">
					<template #label>
						<span class="label-txt">备注</span>
						<span class="label-tip-placeholder" />
					</template>
					<el-input v-model="workerForm.remark" type="textarea" :rows="4" placeholder="选填，描述该压力机用途或所属环境" maxlength="500" show-word-limit />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button size="default" @click="workerDialogVisible = false">取 消</el-button>
				<el-button size="default" type="primary" :loading="workerSubmitLoading" @click="handleWorkerSubmit">确 定</el-button>
			</template>
		</el-dialog>

		<!-- ========== 参数 新增/编辑 对话框 ========== -->
		<el-dialog
			v-model="paramDialogVisible"
			:title="paramDialogTitle"
			width="520px"
			:close-on-click-modal="false"
			@close="resetParamForm"
		>
			<el-form ref="paramFormRef" :model="paramForm" :rules="paramRules" size="default" label-width="105px" hide-required-asterisk class="param-form">
				<el-form-item prop="label">
					<template #label>
						<span class="label-txt"><span class="label-star">*</span>参数名称</span>
						<el-tooltip content="参数的中文说明，如「远程 Worker 上的目标目录」" placement="top">
							<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<el-input v-model="paramForm.label" placeholder="如远程 Worker 上的目标目录" maxlength="100" show-word-limit />
				</el-form-item>
				<el-form-item prop="key">
					<template #label>
						<span class="label-txt"><span class="label-star">*</span>参数名</span>
						<el-tooltip content="参数英文标识，通常全大写，如 REMOTE_PATH；创建后不可修改" placement="top">
							<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<el-input v-model="paramForm.key" :disabled="!!currentParamId" placeholder="如REMOTE_PATH" maxlength="100" show-word-limit />
				</el-form-item>
				<el-form-item prop="value">
					<template #label>
						<span class="label-txt"><span class="label-star">*</span>参数值</span>
						<span class="label-tip-placeholder" />
					</template>
					<el-input v-model="paramForm.value" placeholder="如/data/jmeter/" maxlength="500" show-word-limit />
				</el-form-item>
				<el-form-item prop="status">
					<template #label>
						<span class="label-txt">状态</span>
						<span class="label-tip-placeholder" />
					</template>
					<el-radio-group v-model="paramForm.status" :disabled="isEditingSystemParam">
						<el-radio :value="1" :disabled="isEditingSystemParam">启用</el-radio>
						<el-radio :value="0" :disabled="isEditingSystemParam">禁用</el-radio>
					</el-radio-group>
				</el-form-item>
				<el-form-item v-if="!currentParamId" prop="is_system">
					<template #label>
						<span class="label-txt">系统参数</span>
						<el-tooltip content="系统参数可修改参数名称、参数值、备注，但参数名和状态不可修改，且不允许删除" placement="top">
							<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<div style="width: 100%">
						<el-radio-group v-model="paramForm.is_system">
							<el-radio :value="0">否</el-radio>
							<el-radio :value="1">是</el-radio>
						</el-radio-group>
						<el-alert
							v-if="paramForm.is_system === 1"
							type="warning"
							:closable="false"
							show-icon
							title="系统参数参数名和状态不可修改，且不允许删除"
							style="margin-top: 8px"
						/>
					</div>
				</el-form-item>
				<el-form-item prop="remark">
					<template #label>
						<span class="label-txt">备注</span>
						<span class="label-tip-placeholder" />
					</template>
					<el-input v-model="paramForm.remark" type="textarea" :rows="4" placeholder="请输入备注信息" maxlength="500" show-word-limit />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button size="default" @click="paramDialogVisible = false">取 消</el-button>
				<el-button size="default" type="primary" :loading="paramSubmitLoading" @click="handleParamSubmit">确 定</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts" name="PerformanceConfig">
import { ref, reactive, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus';
import { usePerformanceApi } from '/@/api/v1/performance';
import { useDictDataApi } from '/@/api/v1/system/dict';
import { formatDateTime } from '/@/utils/formatTime';

// 统一使用 API 封装，避免直接操作 axios
const api = usePerformanceApi();
const dictDataApi = useDictDataApi();

// ======================== 公共 ========================

/** 当前激活的 Tab：'worker'=压力机配置 | 'param'=参数配置 */
const activeTab = ref('worker');

/** 状态下拉选项（从字典表 sys_btn_status 动态加载） */
const statusOptions = ref<{ label: string; value: number }[]>([]);

/** 加载状态字典项，页面挂载时调用一次 */
const loadStatusOptions = async () => {
	try {
		const res = await dictDataApi.getByType('sys_btn_status');
		statusOptions.value = (res.data || []).map((item: any) => ({
			label: item.label ?? item.dict_label,
			value: Number(item.value ?? item.dict_value),
		}));
	} catch {
		// 加载失败不影响主流程
	}
};

/** 表单校验规则 */
const workerRules = {
	name: [{ required: true, message: '请输入压力机名称', trigger: 'blur' }],
	type: [{ required: true, message: '请选择类型', trigger: 'change' }],
	status: [{ required: true, message: '请选择状态', trigger: 'change' }],
	ip: [
		{ required: true, message: '请输入机器 IP', trigger: 'blur' },
		{ pattern: /^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?$/, message: 'IP 或域名格式不正确', trigger: 'blur' },
	],
	rmi_port: [{ required: true, message: '请输入 RMI 端口', trigger: 'blur' }],
	ssh_port: [{ required: true, message: '请输入 SSH 端口', trigger: 'blur' }],
};

// ======================== 压力机Tab — 列表 ========================

const workerLoading = ref(false);
const workerList = ref<any[]>([]);
const workerTotal = ref(0);
const workerQuery = reactive({
	name: '',
	status: undefined as number | undefined,
	page: 1,
	page_size: 20,
});
const machineTypeToInt: Record<string, number> = { master: 1, slave: 2, standalone: 3 };

const normalizeMachine = (m: any) => ({
	...m,
	type: m.machine_type === 1 ? 'master' : m.machine_type === 2 ? 'slave' : 'standalone',
	monitor_port: m.monitor,
});

const handleWorkerQuery = async () => {
	workerLoading.value = true;
	try {
		const params: any = { page: workerQuery.page, page_size: workerQuery.page_size };
		if (workerQuery.name) params.name = workerQuery.name;
		if (workerQuery.status !== undefined) params.status = workerQuery.status;
		const res = await api.getMachineList(params);
		workerList.value = (res.data?.rows || []).map(normalizeMachine);
		workerTotal.value = res.data?.rowTotal ?? 0;
	} catch (e: any) {
		ElMessage.error(e.message || '查询失败');
	} finally {
		workerLoading.value = false;
	}
};

const resetWorkerQuery = () => {
	workerQuery.name = '';
	workerQuery.status = undefined;
	workerQuery.page = 1;
	handleWorkerQuery();
};

const handleWorkerStatusChange = async (row: any) => {
	try {
		await api.updateMachine(row.id, { status: row.status });
		ElMessage.success(row.status === 1 ? '已启用' : '已禁用');
	} catch (e: any) {
		row.status = row.status === 1 ? 0 : 1;
		ElMessage.error(e.message || '状态更新失败');
	}
};

// ======================== 压力机Tab — 对话框 ========================

const workerDialogVisible = ref(false);
const workerSubmitLoading = ref(false);
const workerFormRef = ref<FormInstance>();
const currentWorkerId = ref<number | null>(null);
const workerDialogTitle = computed(() => (currentWorkerId.value ? '修改压力机配置' : '新增压力机配置'));
const workerForm = reactive({
	name: '',
	type: 'standalone',
	status: 1,
	ip: '',
	rmi_port: undefined as number | undefined,
	ssh_port: undefined as number | undefined,
	monitor_port: undefined as number | undefined,
	max_concurrency: undefined as number | undefined,
	ssh_user: '',
	ssh_password: '',
	remark: '',
});

/** 打开新增对话框：清空 currentWorkerId 标记为新增模式 */
const handleWorkerAdd = () => {
	currentWorkerId.value = null;
	workerDialogVisible.value = true;
};

/** 打开编辑对话框：将行数据回填到表单 */
const handleWorkerEdit = (row: any) => {
	currentWorkerId.value = row.id;
	Object.assign(workerForm, {
		name: row.name,
		type: row.type,
		status: row.status,
		ip: row.ip || '',
		rmi_port: row.rmi_port,
		ssh_port: row.ssh_port,
		monitor_port: row.monitor_port,
		max_concurrency: row.max_concurrency,
		ssh_user: row.ssh_user || '',
		ssh_password: row.ssh_password || '',
		remark: row.remark || '',
	});
	workerDialogVisible.value = true;
};

/**
 * 复制行数据到新增表单（currentWorkerId 置 null 表示将创建新记录）
 * 自动在名称后追加 '-copy' 提示用户修改
 */
const handleWorkerCopy = (row: any) => {
	currentWorkerId.value = null;
	Object.assign(workerForm, {
		name: `${row.name}-copy`,
		type: row.type,
		status: row.status,
		ip: row.ip || '',
		rmi_port: row.rmi_port,
		ssh_port: row.ssh_port,
		monitor_port: row.monitor_port,
		max_concurrency: row.max_concurrency,
		ssh_user: row.ssh_user || '',
		ssh_password: row.ssh_password || '',
		remark: row.remark || '',
	});
	workerDialogVisible.value = true;
	ElMessage.info('已复制配置，请修改名称后保存');
};

/**
 * 删除压力机（二次确认 → 软删除）
 * DELETE /v1/performance/config/machines/delete/{id}
 * 后端实现软删除（enabled_flag=0），数据不会物理清除
 */
const handleWorkerDelete = (row: any) => {
	ElMessageBox.confirm(`确定要删除压力机「${row.name}」吗？`, '提示', {
		confirmButtonText: '确定',
		cancelButtonText: '取消',
		type: 'warning',
	}).then(async () => {
		try {
			await api.deleteMachine(row.id);
			handleWorkerQuery();
			ElMessage.success('删除成功');
		} catch (e: any) {
			ElMessage.error(e.message || '删除失败');
		}
	}).catch(() => {});
};

/**
 * 前端表单 → 后端请求体字段转换
 * ssh_password：用户填的 Fernet token 原样回传（后端识别 gAAAAA 前缀直接存库）；
 *              用户改为新密码则传明文（后端 Fernet 加密）；留空则传 null（清除密码）
 */
const denormalizeMachine = (form: typeof workerForm) => ({
	name: form.name,
	machine_type: machineTypeToInt[form.type] ?? 3,
	status: form.status,
	ip: form.ip || null,
	rmi_port: form.rmi_port,
	ssh_port: form.ssh_port,
	monitor: form.monitor_port || null,
	max_concurrency: form.max_concurrency || null,
	ssh_user: form.ssh_user || null,
	ssh_password: form.ssh_password || null,
	remark: form.remark || null,
});

/**
 * 对话框提交（新增 / 修改统一入口）
 * 1. 触发 el-form 校验
 * 2. denormalizeMachine 将前端字段转为后端接口所需字段名
 * 3. 根据 currentWorkerId 区分调用 add 或 update 接口
 * 4. 成功后关闭对话框并刷新列表
 */
const handleWorkerSubmit = async () => {
	if (!workerFormRef.value) return;
	await workerFormRef.value.validate(async (valid) => {
		if (!valid) return;
		workerSubmitLoading.value = true;
		try {
			const payload = denormalizeMachine(workerForm);
			if (currentWorkerId.value) {
				// 编辑：PUT /v1/performance/config/machines/update/{id}
				await api.updateMachine(currentWorkerId.value, payload);
				ElMessage.success('修改成功');
			} else {
				// 新增：POST /v1/performance/config/machines/add
				await api.addMachine(payload);
				ElMessage.success('新增成功');
			}
			workerDialogVisible.value = false;
			handleWorkerQuery();
		} catch (e: any) {
			ElMessage.error(e.message || '保存失败');
		} finally {
			workerSubmitLoading.value = false;
		}
	});
};

/**
 * 对话框关闭回调（@close 触发）
 * 重置表单校验状态 + 清空字段 + 清除编辑 id
 */
const resetWorkerForm = () => {
	workerFormRef.value?.resetFields();
	Object.assign(workerForm, { name: '', type: 'standalone', status: 1, ip: '', rmi_port: undefined, ssh_port: undefined, monitor_port: undefined, max_concurrency: undefined, ssh_user: '', ssh_password: '', remark: '' });
	currentWorkerId.value = null;
};

// ================================ 参数配置Tab ====================================

const paramLoading = ref(false);        // 表格加载状态
const paramList = ref<any[]>([]);       // 表格数据
const paramTotal = ref(0);              // 总条数

/** 查询条件，name 字段后端会同时匹配 name 和 param_key 两列 */
const paramQuery = reactive({
	name: '',
	status: undefined as number | undefined,
	page: 1,
	page_size: 20,
});

/**
 * 后端响应 → 前端展示字段转换
 * - name       → label      （参数中文名称）
 * - param_key  → key        （参数英文标识）
 * - param_value → value     （参数值）
 * - create_time → created_at
 * - update_time → updated_at （最后操作时间）
 * - operator_name 后端已联查 sys_user 返回昵称，直接透传
 */
const normalizeParam = (p: any) => ({
	...p,
	label: p.name,
	key: p.param_key,
	value: p.param_value,
	created_at: p.create_time ?? p.creation_date,
	// 有修改时间取修改时间，否则回退到创建时间（新建记录 updation_date 为 null）
	updated_at: p.update_time ?? p.updation_date ?? p.create_time ?? p.creation_date,
});

/**
 * 前端表单 → 后端请求体字段转换
 * - label  → name
 * - key    → param_key
 * - value  → param_value
 */
const denormalizeParam = (form: typeof paramForm) => ({
	name: form.label,
	param_key: form.key,
	param_value: form.value,
	status: form.status,
	is_system: form.is_system,
	remark: form.remark || null,
});

/**
 * 查询参数配置列表
 * GET /v1/performance/config/params/list
 * name 参数在后端会模糊匹配 name 和 param_key 两个字段
 */
const handleParamQuery = async () => {
	paramLoading.value = true;
	try {
		const params: any = { page: paramQuery.page, page_size: paramQuery.page_size };
		if (paramQuery.name) params.name = paramQuery.name;
		if (paramQuery.status !== undefined) params.status = paramQuery.status;
		const res = await api.getParamList(params);
		paramList.value = (res.data?.rows || []).map(normalizeParam);
		paramTotal.value = res.data?.rowTotal ?? 0;
	} catch (e: any) {
		ElMessage.error(e.message || '查询失败');
	} finally {
		paramLoading.value = false;
	}
};

/** 重置查询条件并重新加载第一页 */
const resetParamQuery = () => {
	paramQuery.name = '';
	paramQuery.status = undefined;
	paramQuery.page = 1;
	handleParamQuery();
};

/**
 * el-switch 状态切换（乐观更新，失败回滚）
 * PUT /v1/performance/config/params/update/{id}  body: { status }
 */
const handleParamStatusChange = async (row: any) => {
	try {
		await api.updateParam(row.id, { status: row.status });
		ElMessage.success(`已${row.status === 1 ? '启用' : '禁用'}：${row.key}`);
	} catch (e: any) {
		// 回滚开关状态
		row.status = row.status === 1 ? 0 : 1;
		ElMessage.error(e.message || '状态更新失败');
	}
};

// ---------- 参数 新增/编辑 对话框 ----------

const paramDialogVisible = ref(false);
const paramSubmitLoading = ref(false);
const paramFormRef = ref<FormInstance>();
/** null = 新增模式；有值 = 编辑模式 */
const currentParamId = ref<number | null>(null);
const paramDialogTitle = computed(() => (currentParamId.value ? '编辑参数' : '新增参数'));
const isEditingSystemParam = computed(() => !!currentParamId.value && paramForm.is_system === 1);

/** 参数表单，字段名为前端约定名（label/key/value） */
const paramForm = reactive({
	label: '',
	key: '',
	value: '',
	status: 1,
	is_system: 0,
	remark: '',
});

/**
 * 参数表单校验规则
 * key 需满足全大写+数字+下划线格式（如 REMOTE_PATH），与后端 param_key 规范对应
 * 唯一性校验由后端处理，接口出错时通过 ElMessage 提示
 */
const paramRules = {
	label: [{ required: true, message: '请输入参数名称', trigger: 'blur' }],
	key: [
		{ required: true, message: '请输入参数名', trigger: 'blur' },
		{ pattern: /^[A-Z0-9_]+$/, message: '参数名只能包含大写字母、数字和下划线', trigger: 'blur' },
	],
	value: [{ required: true, message: '请输入参数值', trigger: 'blur' }],
};

/** 打开新增对话框 */
const handleParamAdd = () => {
	currentParamId.value = null;
	paramDialogVisible.value = true;
};

/** 打开编辑对话框：将行数据（已归一化字段）回填到表单 */
const handleParamEdit = (row: any) => {
	currentParamId.value = row.id;
	Object.assign(paramForm, {
		label: row.label,
		key: row.key,
		value: row.value,
		status: row.status,
		is_system: row.is_system ?? 0,
		remark: row.remark || '',
	});
	paramDialogVisible.value = true;
};

/**
 * 删除参数（二次确认 → 软删除）
 * DELETE /v1/performance/config/params/delete/{id}
 */
const handleParamDelete = (row: any) => {
	ElMessageBox.confirm(`确定要删除参数「${row.key}」吗？`, '提示', {
		confirmButtonText: '确定',
		cancelButtonText: '取消',
		type: 'warning',
	}).then(async () => {
		try {
			await api.deleteParam(row.id);
			handleParamQuery();
			ElMessage.success('删除成功');
		} catch (e: any) {
			ElMessage.error(e.message || '删除失败');
		}
	}).catch(() => {});
};

/**
 * 参数对话框提交（新增 / 修改统一入口）
 * 流程同 handleWorkerSubmit：校验 → 字段转换 → 调用接口 → 刷新列表
 */
const handleParamSubmit = async () => {
	if (!paramFormRef.value) return;
	await paramFormRef.value.validate(async (valid) => {
		if (!valid) return;
		paramSubmitLoading.value = true;
		try {
			const payload = denormalizeParam(paramForm);
			if (currentParamId.value) {
				// 编辑：PUT /v1/performance/config/params/update/{id}
				await api.updateParam(currentParamId.value, payload);
				ElMessage.success('修改成功');
			} else {
				// 新增：POST /v1/performance/config/params/add
				await api.addParam(payload);
				ElMessage.success('新增成功');
			}
			paramDialogVisible.value = false;
			handleParamQuery();
		} catch (e: any) {
			ElMessage.error(e.message || '保存失败');
		} finally {
			paramSubmitLoading.value = false;
		}
	});
};

/** 对话框关闭回调：重置表单校验状态 + 清空字段 + 清除编辑 id */
const resetParamForm = () => {
	paramFormRef.value?.resetFields();
	Object.assign(paramForm, { label: '', key: '', value: '', status: 1, is_system: 0, remark: '' });
	currentParamId.value = null;
};

// ======================== 初始化 ========================

/** 页面挂载后立即加载两个 Tab 的数据，避免首次切换 Tab 时出现空列表 */
onMounted(() => {
	loadStatusOptions();
	handleWorkerQuery();
	handleParamQuery();
});
</script>

<style scoped lang="scss">
.perf-config-container {
	padding: 10px 10px 20px 10px;

	:deep(.el-card__body) {
		padding: 10px 10px 20px 10px;
	}

	// ---- 全局控件字体统一 ----
	:deep(.el-button > span) {
		display: inline-flex !important;
		align-items: center !important;
		line-height: 1 !important;
	}

	:deep(.el-input__inner),
	:deep(.el-textarea__inner) {
		font-size: 13.5px;
	}

	// 输入框与下拉框均使用 el-config-provider 全局 size 控制高度，不单独覆盖
	:deep(.el-input-number) {
		.el-input__inner {
			font-size: 13.5px;
		}
	}

	:deep(.el-select__placeholder),
	:deep(.el-select__selected-item) {
		font-size: 13.5px;
	}

	// ---- Tab 标题 ----
	:deep(.el-tabs__item) {
		font-size: 13.5px;
	}

	:deep(.el-tag) {
		font-size: 13px;
		padding: 0 8px;
	}

	// 主键徽章：使用 element 主题色变量，自动适配深色/浅色模式
	.key-badge {
		display: inline-block;
		padding: 1px 8px;
		background: var(--el-color-primary-light-9);
		color: var(--el-color-primary);
		border: 1px solid var(--el-color-primary-light-7);
		border-radius: 4px;
		font-size: 12px;
		font-weight: 600;
	}

	// ---- 表格 ----
	:deep(.el-table) {
		font-size: 13.5px;

		// 表头背景：使用 element 填充色变量，自动适配深色/浅色
		.el-table__header th {
			font-size: 13.5px;
			background-color: var(--el-fill-color-light);
		}

		// 带 ? 图标的表头：禁止折行，文字与图标水平对齐
		.el-table__header th .cell {
			display: inline-flex;
			align-items: center;
			justify-content: center;
			white-space: nowrap;
		}

		.el-table__cell {
			padding: 7px 0;
		}

		// 操作列背景：使用 element fill-color-light 变量，浅色 #f5f7fa 明显灰，深色由 dark.scss 强制为 #303030
		td.operation-col {
			background-color: var(--el-fill-color-light) !important;
		}
	}

	.config-tabs {
		:deep(.el-tabs__header) {
			margin-top: -8px;
			margin-bottom: 16px;
		}
	}

	.toolbar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 16px;

		.toolbar-left {
			display: flex;
			align-items: center;
			gap: 10px;
			flex-wrap: wrap;
		}

		.toolbar-right {
			display: flex;
			align-items: center;
			gap: 10px;
		}
	}

	.tip-icon {
		margin-left: 4px;
		color: var(--el-text-color-secondary);
		cursor: help;
		vertical-align: -2px;
		font-size: 13.5px;

		&:hover {
			color: var(--el-color-primary);
		}
	}

	.worker-form {
		:deep(.el-form-item__label) {
			display: flex !important;
			align-items: center;
			padding-right: 8px !important;
			font-size: 13.5px;

			.label-txt {
				flex: 1;
				text-align: right;

				.label-star {
					color: var(--el-color-danger);
					margin-right: 2px;
				}
			}

			.label-tip-icon,
			.label-tip-placeholder {
				flex-shrink: 0;
				width: 16px;
				margin-left: 4px;
			}

			.el-tooltip__trigger {
				display: inline-flex !important;
				align-items: center;
			}

			.label-tip-icon {
				color: var(--el-text-color-secondary);
				cursor: help;
				font-size: 13.5px;

				&:hover {
					color: var(--el-color-primary);
				}
			}
		}

		:deep(.el-form-item) {
			margin-bottom: 20px;
		}

		:deep(.el-radio__label) {
			font-size: 13.5px;
		}

		:deep(.el-input__placeholder),
		:deep(.el-textarea__placeholder),
		:deep(.el-input-number .el-input__inner::placeholder) {
			font-size: 12px;
		}

		:deep(.el-input__inner::placeholder),
		:deep(.el-textarea__inner::placeholder) {
			font-size: 12px;
		}

		:deep(.el-input-number) {
			// controls-position="right" 时 El-Plus 只重置 wrapper 的 padding-right，
			// padding-left 仍保留为默认模式下给左侧控件按钮留出的大值（约 40px），
			// 导致内容起始位置比普通 el-input 偏右。此处强制还原为标准内边距。
			.el-input__wrapper {
				padding-left: 11px !important;
			}
			.el-input__inner {
				text-align: left;
			}
		}

		:deep(.el-form-item__content) {
			margin-left: 0 !important;  // 防止部分 el-plus 版本自动追加 margin-left 导致偏移
		}
	}

	.param-form {
		:deep(.el-form-item__label) {
			display: flex !important;
			align-items: center;
			padding-right: 8px !important;
			font-size: 13.5px;

			.label-txt {
				flex: 1;
				text-align: right;

				.label-star {
					color: var(--el-color-danger);
					margin-right: 2px;
				}
			}

			.label-tip-icon,
			.label-tip-placeholder {
				flex-shrink: 0;
				width: 16px;
				margin-left: 4px;
			}

			.el-tooltip__trigger {
				display: inline-flex !important;
				align-items: center;
			}

			.label-tip-icon {
				color: var(--el-text-color-secondary);
				cursor: help;
				font-size: 13.5px;

				&:hover {
					color: var(--el-color-primary);
				}
			}
		}

		:deep(.el-form-item) {
			margin-bottom: 20px;
		}

		:deep(.el-radio__label) {
			font-size: 13.5px;
		}

		:deep(.el-input__inner::placeholder),
		:deep(.el-textarea__inner::placeholder) {
			font-size: 12px;
		}
	}

	:deep(.el-switch) {
		--el-switch-width: 52px;
	}

	.action-btns {
		display: flex;
		align-items: center;
		justify-content: center;
		flex-wrap: nowrap;

		:deep(.el-button) {
			padding: 0 4px;
			font-weight: 600;

			.el-icon {
				margin-right: 2px;
			}
		}
	}

	.pagination {
		margin-top: 16px;
		display: flex;
		justify-content: flex-end;
	}
}
</style>

<style lang="scss">
/* 按钮内 slot wrapper span 设为 flex，使图标与文字垂直居中 */
.perf-config-container .el-button > span {
	display: inline-flex !important;
	align-items: center !important;
	line-height: 1 !important;
}
</style>
