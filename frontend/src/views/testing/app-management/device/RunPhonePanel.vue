<template>
	<div>
		<el-table
			ref="phoneTableRef"
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

			<el-table-column show-overflow-tooltip prop="name" align="center" label="设备名称" min-width="140">
				<template #default="scope">
					<div class="device-name-cell">
						<el-icon class="device-icon"><Iphone /></el-icon>
						<span class="device-name">{{ scope.row.name }}</span>
					</div>
				</template>
			</el-table-column>

			<el-table-column show-overflow-tooltip align="center" label="系统类型" min-width="100">
				<template #default="scope">
					<el-tag :type="phoneOsTagType(scope.row)" size="small">
						{{ displayPhoneOs(scope.row) }}
					</el-tag>
				</template>
			</el-table-column>

			<el-table-column show-overflow-tooltip prop="os_version" align="center" label="系统版本" min-width="100">
				<template #default="scope">
					<span>{{ scope.row.os_version }}</span>
				</template>
			</el-table-column>

			<el-table-column prop="device_id" align="center" min-width="180">
				<template #header>
					<span>设备id</span>
					<el-tooltip effect="dark" placement="top-start" content="使用adb devices查看">
						<span class="help-ico header-help"><el-icon><QuestionFilled /></el-icon></span>
					</el-tooltip>
				</template>
				<template #default="scope">
					<div class="device-id-cell">
						<code class="device-id">{{ scope.row.device_id }}</code>
						<el-button text size="small" class="copy-btn" title="复制设备ID" @click="copyDeviceId(scope.row.device_id)">
							<el-icon><CopyDocument /></el-icon>
						</el-button>
					</div>
				</template>
			</el-table-column>

			<el-table-column show-overflow-tooltip prop="screen" align="center" label="分辨率" min-width="100">
				<template #default="scope">
					<span>{{ scope.row.screen }}</span>
				</template>
			</el-table-column>

			<el-table-column fixed="right" align="center" label="操作" width="220">
				<template #default="scope">
					<div class="action-buttons">
						<el-button type="primary" size="small" @click="openEdit(scope.row)">修改</el-button>
						<el-popconfirm width="250px" title="复制此设备并生成新的设备?" @confirm="copyData(scope.row)">
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
			:title="dialog.isEdit ? '修改设备' : '添加手机设备'"
			width="520px"
			destroy-on-close
			:close-on-click-modal="false"
		>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="100px" size="small">
				<el-form-item label="别名" prop="name">
					<el-input v-model="form.name" placeholder="设备别名" />
				</el-form-item>
				<el-form-item label="系统类型" prop="phone_os">
					<el-select v-model="form.phone_os" placeholder="请选择设备系统" style="width: 100%">
						<el-option label="Android" value="Android" />
						<el-option label="iOS" value="ios" />
					</el-select>
				</el-form-item>
				<el-form-item label="系统版本" prop="os_version">
					<el-input v-model="form.os_version" placeholder="可选" />
				</el-form-item>
				<el-form-item label="设备id" prop="device_id">
					<el-input v-model="form.device_id" placeholder="adb devices / UDID">
						<template #append>
							<el-tooltip content="Android 可使用 adb devices 查看" placement="top">
								<span class="hint-append">?</span>
							</el-tooltip>
						</template>
					</el-input>
				</el-form-item>
				<el-form-item label="分辨率" prop="screen">
					<el-input v-model="form.screen" placeholder="如 1080x2340" />
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
import { Iphone, CopyDocument, Rank, QuestionFilled } from '@element-plus/icons-vue';
import { copyText, parseListPagePayload } from '/@/utils';
import { appManagementDeviceApi } from '/@/api/v1/app_management_device';

defineOptions({ name: 'RunPhonePanel' });

const phoneTableRef = ref(null);
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
	phone_os: 'Android',
	os_version: '',
	device_id: '',
	screen: '',
});

const rules: FormRules = {
	name: [{ required: true, message: '请输入别名', trigger: 'blur' }],
	phone_os: [{ required: true, message: '请选择系统', trigger: 'change' }],
	device_id: [{ required: true, message: '请输入设备 id', trigger: 'blur' }],
};

function displayPhoneOs(row: any) {
	const o = row?.os ?? row?.phone_os;
	const s = o == null || o === '' ? '' : String(o);
	if (s.toLowerCase() === 'ios') return 'iOS';
	if (s === 'Android' || s.toLowerCase() === 'android') return 'Android';
	return s || '-';
}

function phoneOsTagType(row: any): 'success' | 'primary' {
	return displayPhoneOs(row) === 'Android' ? 'success' : 'primary';
}

function setTableHeight() {
	if (typeof window === 'undefined') return;
	tableHeight.value = window.innerHeight < 800 ? `${window.innerHeight * 0.71}px` : `${window.innerHeight * 0.81}px`;
}

function handleResize() {
	setTableHeight();
}

async function copyDeviceId(deviceId: string) {
	try {
		await copyText(deviceId, '设备ID已复制到粘贴板');
	} catch {
		void 0;
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
		const res: any = await appManagementDeviceApi.phoneList({
			currentPage: queryItems.value.currentPage,
			pageSize: queryItems.value.pageSize,
		});
		const { list, total } = parseListPagePayload(res);
		tableDataList.value = list;
		tableDataTotal.value = total;
	} catch (e: any) {
		tableDataList.value = [];
		tableDataTotal.value = 0;
		ElMessage.error(e?.message || '加载运行终端列表失败');
	} finally {
		tableIsLoading.value = false;
	}
};

const deleteData = async (row: { id: number }) => {
	await appManagementDeviceApi.phoneDelete({ id: row.id });
	ElMessage.success('已删除');
	await getTableDataList();
};

function openEdit(row: any) {
	dialog.value.isEdit = true;
	form.value = {
		id: row.id,
		name: row.name,
		phone_os: row.phone_os || row.os,
		os_version: row.os_version || '',
		device_id: row.device_id,
		screen: row.screen || '',
	};
	dialog.value.visible = true;
}

function openAdd() {
	dialog.value.isEdit = false;
	form.value = {
		id: 0,
		name: '',
		phone_os: 'Android',
		os_version: '',
		device_id: '',
		screen: '',
	};
	dialog.value.visible = true;
}

defineExpose({ openAdd });

async function submitForm() {
	await formRef.value?.validate();
	saving.value = true;
	try {
		if (dialog.value.isEdit) {
			await appManagementDeviceApi.phoneUpdate({
				id: form.value.id,
				name: form.value.name,
				phone_os: form.value.phone_os,
				os_version: form.value.os_version,
				device_id: form.value.device_id,
				screen: form.value.screen,
				extends: {},
			});
			ElMessage.success('已保存');
		} else {
			await appManagementDeviceApi.phoneAdd({
				data_list: [
					{
						name: form.value.name,
						phone_os: form.value.phone_os,
						os_version: form.value.os_version,
						device_id: form.value.device_id,
						screen: form.value.screen,
						extends: {},
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

const copyData = async (row: any) => {
	row.copyIsLoading = true;
	try {
		await appManagementDeviceApi.phoneCopy({ id: row.id });
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
		await appManagementDeviceApi.phoneSort({ id_list: newIdList.value });
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
		(phoneTableRef.value as { doLayout?: () => void } | null)?.doLayout?.();
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
.header-help {
	margin-left: 5px;
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

	.device-name-cell {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;

		.device-icon {
			color: #409eff;
			font-size: 16px;
			flex-shrink: 0;
		}

		.device-name {
			font-weight: 500;
		}
	}

	.device-id-cell {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;

		.device-id {
			background: #f5f7fa;
			padding: 2px 6px;
			border-radius: 3px;
			font-size: 12px;
			color: #606266;
			flex: 1;
			max-width: 220px;
			word-break: break-all;
			text-align: left;
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
		flex-wrap: wrap;

		.el-button {
			flex-shrink: 0;
		}
	}
}

.hint-append {
	padding: 0 6px;
	cursor: help;
	color: var(--el-color-info);
}

:deep(.drag-dragging) {
	opacity: 0.6;
}
</style>
