<template>
	<div class="app-image-library">
		<div class="ail-header">
			<div class="ail-header__titles">
				<h2 class="ail-title">图像库管理</h2>
				<p class="ail-desc">按项目维护 Airtest 图像素材，支持上传、预览与删除</p>
			</div>
			<el-button type="primary" @click="openUploadDialog">
				<el-icon class="ail-icon-gap"><Plus /></el-icon>
				新增图像
			</el-button>
		</div>

		<el-card shadow="never" class="ail-card">
			<el-form :inline="true" class="ail-form" @submit.prevent>
				<el-form-item label="项目">
					<el-select
						v-model="query.search.menu_id"
						placeholder="请选择项目"
						clearable
						filterable
						style="width: 220px"
						:disabled="menuLoading || menuOptions.length === 0"
						@change="onMenuChange"
					>
						<el-option
							v-for="m in menuOptions"
							:key="'m-' + m.id"
							:label="m.name"
							:value="m.id"
						/>
					</el-select>
				</el-form-item>
				<el-form-item label="图像名称">
					<el-input
						v-model="query.search.file_name__icontains"
						placeholder="模糊搜索"
						clearable
						style="width: 200px"
						@keyup.enter="loadList"
					/>
				</el-form-item>
				<el-form-item>
					<el-button type="primary" :loading="listLoading" @click="loadList">搜索</el-button>
					<el-button @click="resetQuery">重置</el-button>
				</el-form-item>
			</el-form>
		</el-card>

		<el-card shadow="never" class="ail-card ail-table-card">
			<el-table
				v-loading="listLoading"
				:data="rows"
				row-key="id"
				stripe
				border
				empty-text="暂无数据"
				style="width: 100%"
			>
				<el-table-column type="index" label="序号" width="64" align="center" />
				<el-table-column prop="file_name" label="图像名称" min-width="160" show-overflow-tooltip />
				<el-table-column label="预览" width="100" align="center">
					<template #default="{ row }">
						<div v-if="row.file_path" class="ail-thumb-wrap">
							<img :src="row.file_path" alt="" class="ail-thumb" @error="onThumbError" />
						</div>
						<span v-else class="ail-muted">—</span>
					</template>
				</el-table-column>
				<el-table-column prop="create_time" label="创建时间" width="180" align="center">
					<template #default="{ row }">
						{{ formatCellTime(row.create_time) }}
					</template>
				</el-table-column>
				<el-table-column label="操作" width="160" align="center" fixed="right">
					<template #default="{ row }">
						<el-button type="danger" link size="small" @click="confirmDelete(row)">删除</el-button>
					</template>
				</el-table-column>
			</el-table>

			<div class="ail-pagination">
				<el-pagination
					v-model:current-page="query.currentPage"
					v-model:page-size="query.pageSize"
					:total="total"
					:page-sizes="[10, 20, 50]"
					layout="total, sizes, prev, pager, next"
					background
					@size-change="loadList"
					@current-change="loadList"
				/>
			</div>
		</el-card>

		<el-dialog
			v-model="uploadDialogVisible"
			title="上传图像"
			width="520px"
			append-to-body
			align-center
			destroy-on-close
			:close-on-click-modal="false"
			@closed="onUploadDialogClosed"
		>
			<p class="ail-dialog-tip">归属项目：<strong>{{ uploadMenuLabel }}</strong>（与列表当前筛选一致）</p>
			<el-upload
				ref="uploadRef"
				drag
				multiple
				:auto-upload="false"
				:limit="9"
				accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
				:on-change="onUploadChange"
				:on-exceed="onUploadExceed"
			>
				<el-icon class="el-icon--upload"><UploadFilled /></el-icon>
				<div class="el-upload__text">将文件拖到此处，或<em>点击选择</em></div>
				<template #tip>
					<div class="el-upload__tip">单张建议不超过 30MB，最多 9 张；选择后点「开始上传」。</div>
				</template>
			</el-upload>
			<template #footer>
				<el-button @click="uploadDialogVisible = false">取消</el-button>
				<el-button type="primary" :loading="uploadSubmitting" :disabled="pendingFiles.length === 0" @click="submitUpload">
					开始上传
				</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { UploadFile, UploadInstance, UploadProps } from 'element-plus';
import { Plus, UploadFilled } from '@element-plus/icons-vue';
import request from '/@/utils/request';
import { useAppManagementApi } from '/@/api/v1/app_management';
import { formatDateTime } from '/@/utils/formatTime';

defineOptions({ name: 'AppImageLibrary' });

const { app_menu_select } = useAppManagementApi();

type MenuRow = { id: number; name: string };
type ImageRow = {
	id: number | string;
	file_name: string;
	file_path: string;
	create_time?: string | null;
	menu_id?: number | null;
};

const menuLoading = ref(false);
const listLoading = ref(false);
const menuOptions = ref<MenuRow[]>([]);

const query = ref({
	currentPage: 1,
	pageSize: 10,
	search: {
		file_name__icontains: '',
		menu_id: undefined as number | undefined,
	},
});

const rows = ref<ImageRow[]>([]);
const total = ref(0);

const uploadDialogVisible = ref(false);
const uploadSubmitting = ref(false);
const uploadRef = ref<UploadInstance>();
const pendingFiles = ref<File[]>([]);

const uploadMenuLabel = computed(() => {
	const id = query.value.search.menu_id;
	const m = menuOptions.value.find((x) => x.id === id);
	return m?.name ?? '（未选择）';
});

function formatCellTime(v: string | Date | null | undefined) {
	if (v == null || v === '') return '—';
	try {
		return formatDateTime(v as string);
	} catch {
		return '—';
	}
}

function onThumbError(ev: Event) {
	const el = ev.target as HTMLImageElement;
	if (el) el.style.visibility = 'hidden';
}

function unwrapListPayload(res: unknown): unknown[] {
	if (res == null || typeof res !== 'object') return [];
	const body = res as Record<string, unknown>;
	const data = body.data;
	if (Array.isArray(data)) return data;
	if (data != null && typeof data === 'object') {
		const d = data as Record<string, unknown>;
		const c = d.content ?? d.items ?? d.rows ?? d.data;
		if (Array.isArray(c)) return c;
	}
	return [];
}

function unwrapImgPage(res: unknown): { list: ImageRow[]; total: number } {
	const body = res as Record<string, unknown> | null;
	const data = (body?.data ?? null) as Record<string, unknown> | null;
	if (!data || typeof data !== 'object') {
		return { list: [], total: 0 };
	}
	const raw = data.content ?? data.items ?? data.rows;
	const list: ImageRow[] = [];
	if (Array.isArray(raw)) {
		raw.forEach((item: unknown, i: number) => {
			if (!item || typeof item !== 'object') return;
			const r = item as Record<string, unknown>;
			const id = r.id != null ? (r.id as number | string) : `tmp-${i}`;
			list.push({
				id,
				file_name: String(r.file_name ?? ''),
				file_path: String(r.file_path ?? ''),
				create_time: r.create_time != null ? String(r.create_time) : undefined,
				menu_id: r.menu_id != null ? Number(r.menu_id) : undefined,
			});
		});
	}
	const t = Number(data.total);
	const totalN = Number.isFinite(t) ? Math.max(0, Math.floor(t)) : list.length;
	return { list, total: totalN };
}

async function loadMenus() {
	menuLoading.value = true;
	try {
		const res: unknown = await app_menu_select({});
		const arr = unwrapListPayload(res);
		const next: MenuRow[] = [];
		arr.forEach((x: unknown) => {
			if (!x || typeof x !== 'object') return;
			const o = x as Record<string, unknown>;
			const id = Number(o.id);
			if (!Number.isFinite(id)) return;
			next.push({ id, name: String(o.name ?? '-') });
		});
		menuOptions.value = next;
		if (next.length && query.value.search.menu_id == null) {
			query.value.search.menu_id = next[0].id;
		}
	} catch (e: unknown) {
		menuOptions.value = [];
		ElMessage.error(e instanceof Error ? e.message : '加载项目列表失败');
	} finally {
		menuLoading.value = false;
	}
}

async function loadList() {
	if (query.value.search.menu_id == null) {
		rows.value = [];
		total.value = 0;
		return;
	}
	listLoading.value = true;
	try {
		const res: unknown = await request({
			url: '/v1/app_management/img_list',
			method: 'post',
			data: { ...query.value },
		});
		const { list, total: t } = unwrapImgPage(res);
		rows.value = list;
		total.value = t;
	} catch (e: unknown) {
		rows.value = [];
		total.value = 0;
		ElMessage.error(e instanceof Error ? e.message : '加载图像列表失败');
	} finally {
		listLoading.value = false;
	}
}

function onMenuChange() {
	query.value.currentPage = 1;
	void loadList();
}

function resetQuery() {
	const first = menuOptions.value[0]?.id;
	query.value = {
		currentPage: 1,
		pageSize: 10,
		search: {
			file_name__icontains: '',
			menu_id: first,
		},
	};
	void loadList();
}

function openUploadDialog() {
	if (query.value.search.menu_id == null) {
		ElMessage.warning('请先选择项目');
		return;
	}
	pendingFiles.value = [];
	uploadDialogVisible.value = true;
}

function onUploadDialogClosed() {
	pendingFiles.value = [];
	uploadRef.value?.clearFiles();
}

const onUploadChange: UploadProps['onChange'] = (_file, fileList) => {
	const files: File[] = [];
	fileList.forEach((uf: UploadFile) => {
		const raw = uf.raw;
		if (raw instanceof File) files.push(raw);
	});
	pendingFiles.value = files;
};

const onUploadExceed: UploadProps['onExceed'] = () => {
	ElMessage.warning('最多选择 9 张图片');
};

async function submitUpload() {
	const menuId = query.value.search.menu_id;
	if (menuId == null) {
		ElMessage.error('未选择项目');
		return;
	}
	const files = pendingFiles.value;
	if (!files.length) {
		ElMessage.warning('请先选择图片');
		return;
	}
	uploadSubmitting.value = true;
	try {
		for (const raw of files) {
			const form = new FormData();
			form.append('file', raw);
			form.append('menu_id', String(menuId));
			await request({
				url: '/v1/app_management/add_img',
				method: 'post',
				data: form,
				headers: { 'Content-Type': 'multipart/form-data' },
			});
		}
		ElMessage.success('上传成功');
		uploadDialogVisible.value = false;
		await loadList();
	} catch (e: unknown) {
		ElMessage.error(e instanceof Error ? e.message : '上传失败');
	} finally {
		uploadSubmitting.value = false;
	}
}

function confirmDelete(row: ImageRow) {
	void ElMessageBox.confirm(`确定删除「${row.file_name}」？`, '提示', {
		type: 'warning',
		confirmButtonText: '删除',
		cancelButtonText: '取消',
	})
		.then(async () => {
			const id = Number(row.id);
			if (!Number.isFinite(id)) {
				ElMessage.error('无效的记录 id');
				return;
			}
			try {
				const res: unknown = await request({
					url: '/v1/app_management/delete_img',
					method: 'post',
					data: { id },
				});
				const msg =
					typeof res === 'object' && res != null && 'message' in res
						? String((res as { message?: string }).message ?? '')
						: '';
				ElMessage.success(msg || '已删除');
				await loadList();
			} catch (e: unknown) {
				ElMessage.error(e instanceof Error ? e.message : '删除失败');
			}
		})
		.catch(() => void 0);
}

onMounted(async () => {
	await loadMenus();
	await loadList();
});
</script>

<style scoped lang="scss">
.app-image-library {
	padding: 0 4px 16px;
}

.ail-header {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	gap: 16px;
	margin-bottom: 16px;
}

.ail-title {
	margin: 0 0 6px;
	font-size: 18px;
	font-weight: 600;
	color: var(--el-text-color-primary);
}

.ail-desc {
	margin: 0;
	font-size: 13px;
	color: var(--el-text-color-secondary);
}

.ail-icon-gap {
	margin-right: 6px;
	vertical-align: middle;
}

.ail-card {
	margin-bottom: 12px;
	border-radius: 8px;
}

.ail-table-card {
	overflow: hidden;
}

.ail-form {
	margin-bottom: 0;
}

.ail-thumb-wrap {
	display: flex;
	align-items: center;
	justify-content: center;
	min-height: 48px;
}

.ail-thumb {
	max-width: 72px;
	max-height: 48px;
	object-fit: cover;
	border-radius: 4px;
	border: 1px solid var(--el-border-color-lighter);
}

.ail-muted {
	color: var(--el-text-color-placeholder);
	font-size: 13px;
}

.ail-pagination {
	display: flex;
	justify-content: flex-end;
	margin-top: 16px;
}

.ail-dialog-tip {
	margin: 0 0 12px;
	font-size: 13px;
	color: var(--el-text-color-regular);
}
</style>
