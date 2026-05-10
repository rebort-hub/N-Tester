<template>
	<div>
		<el-table
			ref="serverTableRef"
			v-loading="tableIsLoading"
			element-loading-text="正在获取数据"
			:data="tableDataList"
			style="width: 100%"
			:header-cell-style="{ textAlign: 'center' }"
			stripe
			row-key="id"
			:height="tableHeight"
			class="device-table"
			@row-dblclick="rowDblclick"
		>
			<el-table-column label="排序" width="50" align="center">
				<template #header>
					<el-tooltip effect="dark" placement="top-start">
						<template #content>
							<div>可拖拽数据前的图标进行自定义排序</div>
						</template>
						<span class="help-ico"><el-icon><QuestionFilled /></el-icon></span>
					</el-tooltip>
				</template>
				<template #default="scope">
					<el-button
						text
						class="drag-button"
						draggable="true"
						:data-index="scope.$index"
						@dragstart="handleDragStart($event, scope.row, scope.$index)"
						@dragover="handleDragOver($event, scope.$index)"
						@drop="handleDrop($event, scope.$index)"
						@dragend="handleDragEnd"
					>
						<el-icon><Rank /></el-icon>
					</el-button>
				</template>
			</el-table-column>

			<el-table-column label="序号" header-align="center" width="60">
				<template #default="scope">
					<span>{{ (queryItems.currentPage - 1) * queryItems.pageSize + scope.$index + 1 }}</span>
				</template>
			</el-table-column>

			<el-table-column show-overflow-tooltip prop="name" align="center" label="服务器名称" min-width="140">
				<template #default="scope">
					<div class="server-name-cell">
						<el-icon class="server-icon"><Monitor /></el-icon>
						<span class="server-name">{{ scope.row.name }}</span>
					</div>
				</template>
			</el-table-column>

			<el-table-column show-overflow-tooltip align="center" label="服务器系统类型" min-width="120">
				<template #default="scope">
					<el-tag :type="getOsTagType(displayServerOs(scope.row))" size="small">
						{{ displayServerOs(scope.row) }}
					</el-tag>
				</template>
			</el-table-column>

			<el-table-column show-overflow-tooltip prop="ip" align="center" label="服务器ip地址" min-width="140">
				<template #default="scope">
					<div class="ip-cell">
						<code class="ip-code">{{ scope.row.ip }}</code>
						<el-button text size="small" class="copy-btn" title="复制IP地址" @click="copyIp(scope.row.ip)">
							<el-icon><CopyDocument /></el-icon>
						</el-button>
					</div>
				</template>
			</el-table-column>

			<el-table-column show-overflow-tooltip prop="port" align="center" label="服务器端口" width="100">
				<template #default="scope">
					<span>{{ scope.row.port }}</span>
				</template>
			</el-table-column>

			<el-table-column show-overflow-tooltip prop="appium_version" align="center" label="appium版本" min-width="100">
				<template #default="scope">
					<el-tag type="info" size="small">v{{ scope.row.appium_version }}</el-tag>
				</template>
			</el-table-column>

			<el-table-column prop="status" align="center" label="最近一次访问状态" min-width="130">
				<template #default="scope">
					<el-tag size="small" :type="appiumServerRequestStatusMappingTagType[scope.row.status ?? 0]">
						{{ appiumServerRequestStatusMappingContent[scope.row.status ?? 0] }}
					</el-tag>
				</template>
			</el-table-column>

			<el-table-column fixed="right" align="center" label="操作" width="300">
				<template #default="scope">
					<div class="action-buttons">
						<el-button type="success" size="small" @click="runServer(scope.row)">访问</el-button>
						<el-button type="primary" size="small" @click="openEdit(scope.row)">修改</el-button>
						<el-popconfirm width="250px" title="复制此服务器并生成新的服务器?" @confirm="copyData(scope.row)">
							<template #reference>
								<el-button size="small" :loading="scope.row.copyIsLoading">复制</el-button>
							</template>
						</el-popconfirm>
						<el-popconfirm width="250px" :title="`确定删除【${scope.row.name}】?`" @confirm="deleteData(scope.row)">
							<template #reference>
								<el-button type="danger" size="small">删除</el-button>
							</template>
						</el-popconfirm>
					</div>
				</template>
			</el-table-column>
		</el-table>

		<el-pagination
			v-show="tableDataTotal > 0"
			class="device-pagination"
			background
			layout="total, prev, pager, next, sizes"
			:total="tableDataTotal"
			v-model:current-page="queryItems.currentPage"
			v-model:page-size="queryItems.pageSize"
			:page-sizes="[10, 20, 50]"
			@current-change="getTableDataList"
			@size-change="onPageSizeChange"
		/>

		<el-dialog
			v-model="dialog.visible"
			:title="dialog.isEdit ? '修改服务器' : '添加Appium服务器'"
			width="520px"
			destroy-on-close
			:close-on-click-modal="false"
		>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="100px" size="small">
				<el-form-item label="别名" prop="name">
					<el-input v-model="form.name" placeholder="别名" />
				</el-form-item>
				<el-form-item label="系统类型" prop="server_os">
					<el-select v-model="form.server_os" placeholder="请选择appium服务所在电脑的系统类型" style="width: 100%" clearable>
						<el-option label="Windows" value="windows" />
						<el-option label="macOS" value="mac" />
						<el-option label="Linux" value="linux" />
					</el-select>
				</el-form-item>
				<el-form-item label="服务器ip" prop="ip">
					<el-input v-model="form.ip" placeholder="如 192.168.0.1（勿填 http）" style="width: calc(100% - 28px); vertical-align: middle" />
					<el-tooltip placement="top-start">
						<template #content>
							<div>请填写 ip，勿填写 http</div>
							<div>如地址为 http://192.168.0.1，请填：192.168.0.1</div>
						</template>
						<span class="help-ico inline-help"><el-icon><QuestionFilled /></el-icon></span>
					</el-tooltip>
				</el-form-item>
				<el-form-item label="服务器端口" prop="port">
					<el-input v-model="form.port" placeholder="服务器端口" />
				</el-form-item>
				<el-form-item label="appium版本" prop="appium_version">
					<el-select v-model="form.appium_version" placeholder="请选择appium版本" style="width: 100%">
						<el-option v-for="v in appiumVersions" :key="v" :label="v" :value="v" />
					</el-select>
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button size="small" @click="dialog.visible = false">取消</el-button>
				<el-button type="primary" size="small" :loading="saving" @click="submitForm">保存</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import { Monitor, CopyDocument, Rank, QuestionFilled } from '@element-plus/icons-vue';
import { copyText, parseListPagePayload } from '/@/utils';
import { appManagementDeviceApi } from '/@/api/v1/app_management_device';
import {
	appiumServerRequestStatusMappingContent,
	appiumServerRequestStatusMappingTagType,
} from '/@/utils/ntestMapping';

defineOptions({ name: 'AppiumServerPanel' });

const appiumVersions = ['1.x', '2.x', '3.x'];
const serverTableRef = ref(null);
const tableIsLoading = ref(false);
const saving = ref(false);
const oldIndex = ref<number>();
const dragRow = ref<any>();
const newIdList = ref<number[]>([]);
const tableDataList = ref<any[]>([]);
const tableDataTotal = ref(0);
const tableHeight = ref('480px');
const queryItems = ref({
	currentPage: 1,
	pageSize: 20,
});

const dialog = ref({ visible: false, isEdit: false });
const formRef = ref<FormInstance>();
const form = ref({
	id: 0,
	name: '',
	server_os: 'windows',
	ip: '',
	port: '4723',
	appium_version: '2.x',
});

const rules: FormRules = {
	name: [{ required: true, message: '请输入别名', trigger: 'blur' }],
	server_os: [{ required: true, message: '请选择系统类型', trigger: 'change' }],
	ip: [{ required: true, message: '请输入 IP', trigger: 'blur' }],
	port: [{ required: true, message: '请输入端口', trigger: 'blur' }],
	appium_version: [{ required: true, message: '请选择版本', trigger: 'change' }],
};

/** 表格传入整行；server_os 可能为数字/对象等非字符串，统一 String 再 toLowerCase */
function displayServerOs(row: Record<string, unknown> | null | undefined): string {
	const v = row?.server_os ?? row?.os;
	const s = v == null || v === '' ? '' : String(v);
	const k = s.toLowerCase();
	if (k === 'linux') return 'Linux';
	if (k === 'windows') return 'Windows';
	if (k === 'mac' || k === 'macos') return 'macOS';
	return s || '-';
}

function getOsTagType(os: string): 'success' | 'primary' | 'warning' | 'info' {
	switch (os) {
		case 'Linux':
			return 'success';
		case 'Windows':
			return 'primary';
		case 'macOS':
			return 'warning';
		default:
			return 'info';
	}
}

function setTableHeight() {
	if (typeof window === 'undefined') return;
	tableHeight.value = window.innerHeight < 800 ? `${window.innerHeight * 0.71}px` : `${window.innerHeight * 0.81}px`;
}

function handleResize() {
	setTableHeight();
}

async function copyIp(text: string) {
	try {
		await copyText(text, '已复制到粘贴板');
	} catch {
		/* ElMessage in copyText */
	}
}

const rowDblclick = async (row: any, column: any) => {
	const prop = column?.property;
	if (prop == null || row[prop] == null) return;
	try {
		await copyText(String(row[prop]), '已复制到粘贴板');
	} catch {
		void 0;
	}
};

function onPageSizeChange() {
	queryItems.value.currentPage = 1;
	getTableDataList();
}

const getTableDataList = async () => {
	tableIsLoading.value = true;
	try {
		const res: any = await appManagementDeviceApi.serverList({
			currentPage: queryItems.value.currentPage,
			pageSize: queryItems.value.pageSize,
		});
		const { list, total } = parseListPagePayload(res);
		tableDataList.value = list;
		tableDataTotal.value = total;
	} catch (e: any) {
		tableDataList.value = [];
		tableDataTotal.value = 0;
		ElMessage.error(e?.message || '加载 Appium 服务器列表失败');
	} finally {
		tableIsLoading.value = false;
	}
};

const deleteData = async (row: { id: number }) => {
	await appManagementDeviceApi.serverDelete({ id: row.id });
	ElMessage.success('已删除');
	await getTableDataList();
};

function openEdit(row: any) {
	dialog.value.isEdit = true;
	form.value = {
		id: row.id,
		name: row.name,
		server_os: row.server_os || row.os,
		ip: row.ip,
		port: row.port,
		appium_version: row.appium_version,
	};
	dialog.value.visible = true;
}

function openAdd() {
	dialog.value.isEdit = false;
	form.value = {
		id: 0,
		name: '',
		server_os: 'windows',
		ip: '',
		port: '4723',
		appium_version: '2.x',
	};
	dialog.value.visible = true;
}

defineExpose({ openAdd });

async function submitForm() {
	await formRef.value?.validate();
	saving.value = true;
	try {
		if (dialog.value.isEdit) {
			await appManagementDeviceApi.serverUpdate({
				id: form.value.id,
				name: form.value.name,
				server_os: form.value.server_os,
				ip: form.value.ip,
				port: form.value.port,
				appium_version: form.value.appium_version,
			});
			ElMessage.success('已保存');
		} else {
			await appManagementDeviceApi.serverAdd({
				data_list: [
					{
						name: form.value.name,
						server_os: form.value.server_os,
						ip: form.value.ip,
						port: form.value.port,
						appium_version: form.value.appium_version,
					},
				],
			});
			ElMessage.success('已新增');
		}
		dialog.value.visible = false;
		await getTableDataList();
	} finally {
		saving.value = false;
	}
}

const runServer = async (row: { id: number }) => {
	tableIsLoading.value = true;
	try {
		const res: any = await appManagementDeviceApi.serverRun({ id: row.id });
		ElMessage.success(res?.message || '访问完成');
		await getTableDataList();
	} catch {
		await getTableDataList();
	} finally {
		tableIsLoading.value = false;
	}
};

const copyData = async (row: any) => {
	row.copyIsLoading = true;
	try {
		await appManagementDeviceApi.serverCopy({ id: row.id });
		ElMessage.success('已复制');
		await getTableDataList();
	} finally {
		row.copyIsLoading = false;
	}
};

const handleDragStart = (event: DragEvent, row: any, index: number) => {
	oldIndex.value = index;
	dragRow.value = row;
	event.dataTransfer!.effectAllowed = 'move';
	(event.target as HTMLElement).classList.add('drag-dragging');
};

const handleDragOver = (event: DragEvent) => {
	event.preventDefault();
};

const handleDragEnd = (event: DragEvent) => {
	(event.target as HTMLElement).classList.remove('drag-dragging');
};

const handleDrop = (event: DragEvent, newIndex: number) => {
	event.preventDefault();
	if (oldIndex.value === undefined || !dragRow.value) return;
	const updated = [...tableDataList.value];
	updated.splice(oldIndex.value, 1);
	updated.splice(newIndex, 0, dragRow.value);
	(event.target as HTMLElement).classList.remove('drag-dragging');
	newIdList.value = updated.map((item) => item.id);
	sortTable();
};

const sortTable = async () => {
	tableIsLoading.value = true;
	try {
		await appManagementDeviceApi.serverSort({ id_list: newIdList.value });
		await getTableDataList();
	} finally {
		tableIsLoading.value = false;
	}
};

onMounted(() => {
	setTableHeight();
	window.addEventListener('resize', handleResize);
	void (async () => {
		await getTableDataList();
		await nextTick();
		(serverTableRef.value as { doLayout?: () => void } | null)?.doLayout?.();
	})();
});

onBeforeUnmount(() => {
	window.removeEventListener('resize', handleResize);
});
</script>

<style scoped lang="scss">
.help-ico {
	color: #409eff;
	cursor: help;
	vertical-align: middle;
}
.inline-help {
	margin-left: 6px;
	display: inline-flex;
}

.device-pagination {
	margin-top: 12px;
	justify-content: flex-end;
	display: flex;
}

.device-table {
	border-radius: 4px;
	overflow: hidden;

	.server-name-cell {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;

		.server-icon {
			color: #409eff;
			font-size: 16px;
			flex-shrink: 0;
		}

		.server-name {
			font-weight: 500;
		}
	}

	.ip-cell {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;

		.ip-code {
			background: #f5f7fa;
			padding: 2px 6px;
			border-radius: 3px;
			font-size: 12px;
			color: #606266;
			flex: 1;
			max-width: 160px;
			overflow: hidden;
			text-overflow: ellipsis;
		}

		.copy-btn {
			color: #409eff;
			padding: 2px;
			flex-shrink: 0;

			&:hover {
				background-color: #ecf5ff;
			}
		}
	}

	.drag-button {
		cursor: grab;

		&:hover {
			color: #409eff;
		}

		&:active {
			cursor: grabbing;
		}
	}

	.action-buttons {
		display: flex;
		gap: 4px;
		justify-content: center;
		flex-wrap: nowrap;
		align-items: center;

		.el-button {
			flex-shrink: 0;
		}
	}
}

:deep(.drag-dragging) {
	opacity: 0.6;
}
</style>
