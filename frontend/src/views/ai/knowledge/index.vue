<template>
	<div class="page-wrap">
		<el-card shadow="hover" class="toolbar">
			<el-form :inline="true">
				<el-form-item label="项目">
					<el-select v-model="projectId" placeholder="选择项目" style="width: 220px" @change="onProjectChange">
						<el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
					</el-select>
				</el-form-item>
				<el-form-item>
					<el-button @click="openGlobal">全局配置</el-button>
					<el-button type="primary" @click="loadBases">刷新</el-button>
					<el-button type="success" @click="openCreateKb">新建知识库</el-button>
				</el-form-item>
			</el-form>
		</el-card>

		<el-card shadow="hover">
			<el-table v-loading="loading" :data="bases" stripe @row-click="onRow">
				<el-table-column prop="name" label="名称" min-width="160" />
				<el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
				<el-table-column label="文档/已处理" width="120">
					<template #default="{ row }"> {{ row.document_count }} / {{ row.processed_count }} </template>
				</el-table-column>
				<el-table-column label="操作" width="200" fixed="right">
					<template #default="{ row }">
						<el-button size="small" type="primary" @click.stop="openDetail(row)">管理</el-button>
						<el-button size="small" type="warning" @click.stop="editKb(row)">编辑</el-button>
						<el-button size="small" type="danger" @click.stop="removeKb(row)">删除</el-button>
					</template>
				</el-table-column>
			</el-table>
			<div class="pager" v-if="total > 0">
				<el-pagination
					v-model:current-page="page"
					v-model:page-size="pageSize"
					:total="total"
					layout="total, prev, pager, next"
					@current-change="loadBases"
				/>
			</div>
		</el-card>

		<el-dialog v-model="kbDlg" :title="editKbId ? '编辑知识库' : '新建知识库'" width="520px" destroy-on-close>
			<el-form :model="kbForm" label-width="100px">
				<el-form-item label="名称" required>
					<el-input v-model="kbForm.name" />
				</el-form-item>
				<el-form-item label="描述">
					<el-input v-model="kbForm.description" type="textarea" rows="2" />
				</el-form-item>
				<el-form-item label="分块大小">
					<el-input-number v-model="kbForm.chunk_size" :min="100" :max="4000" />
				</el-form-item>
				<el-form-item label="重叠">
					<el-input-number v-model="kbForm.chunk_overlap" :min="0" :max="500" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="kbDlg = false">取消</el-button>
				<el-button type="primary" :loading="savingKb" @click="submitKb">保存</el-button>
			</template>
		</el-dialog>

		<el-dialog v-model="gcDlg" title="知识库全局配置（向量/模型）" width="680px">
			<el-form :model="gcForm" label-width="120px">
				<el-form-item label="嵌入提供商">
					<el-select v-model="gcForm.embedding_provider" style="width: 100%">
						<el-option label="openai" value="openai" />
						<el-option label="ollama" value="ollama" />
					</el-select>
				</el-form-item>
				<el-form-item label="嵌入 Base URL">
					<el-input v-model="gcForm.embedding_base_url" placeholder="留空则使用 OpenAI 官方" />
				</el-form-item>
				<el-form-item label="嵌入 API Key">
					<el-input v-model="gcForm.embedding_api_key" type="password" show-password />
				</el-form-item>
				<el-form-item label="嵌入模型">
					<el-input v-model="gcForm.embedding_model" />
				</el-form-item>
				<el-divider content-position="left">向量数据库</el-divider>
				<el-form-item label="启用向量检索">
					<el-switch v-model="gcForm.vector_enabled" />
				</el-form-item>
				<el-form-item label="向量库类型">
					<el-select v-model="gcForm.vector_provider" style="width: 100%">
						<el-option label="qdrant" value="qdrant" />
						<el-option label="chroma" value="chroma" />
					</el-select>
				</el-form-item>
				<el-form-item label="向量库 URL">
					<el-input v-model="gcForm.vector_url" placeholder="如 http://127.0.0.1:6333" />
				</el-form-item>
				<el-form-item label="向量库 API Key">
					<el-input v-model="gcForm.vector_api_key" type="password" show-password />
				</el-form-item>
				<el-form-item label="集合名">
					<el-input v-model="gcForm.vector_collection" />
				</el-form-item>
				<el-form-item label="向量维度">
					<el-input-number v-model="gcForm.vector_dimension" :min="1" :max="8192" />
				</el-form-item>
				<el-form-item label="Top K">
					<el-input-number v-model="gcForm.retrieval_top_k" :min="1" :max="50" />
				</el-form-item>
				<el-form-item>
					<el-button :loading="testingEmb" @click="testEmb">测试嵌入连接</el-button>
					<el-button :loading="testingVector" @click="testVector">测试向量库连接</el-button>
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="gcDlg = false">关闭</el-button>
				<el-button type="primary" @click="saveGc">保存</el-button>
			</template>
		</el-dialog>

		<el-drawer v-model="drawer" :title="detail.title" size="60%" destroy-on-close>
			<div class="drawer-body" v-if="detail.id">
				<el-tabs v-model="tab">
					<el-tab-pane label="文档" name="doc">
						<div class="row-actions">
							<el-upload :show-file-list="false" :http-request="customUpload">
								<el-button type="primary">上传文档</el-button>
							</el-upload>
							<el-button @click="loadDocs">刷新文档</el-button>
						</div>
						<el-table v-loading="docLoading" :data="docs" size="small">
							<el-table-column prop="title" label="标题" min-width="160" />
							<el-table-column prop="document_type" label="类型" width="80" />
							<el-table-column label="状态" width="120">
								<template #default="{ row }">
									<el-tag size="small" :type="statusTagType(row.status)">{{ statusText(row.status) }}</el-tag>
								</template>
							</el-table-column>
							<el-table-column label="操作" width="160">
								<template #default="{ row }">
									<el-button size="small" type="primary" @click="viewChunks(row)">查看</el-button>
									<el-button size="small" type="danger" @click="removeDoc(row)">删除</el-button>
								</template>
							</el-table-column>
						</el-table>
					</el-tab-pane>
					<el-tab-pane label="关键词检索" name="q">
						<el-input v-model="qText" placeholder="输入关键词" @keyup.enter="runQuery" />
						<el-button type="primary" style="margin-top: 8px" @click="runQuery">检索</el-button>
						<el-scrollbar v-if="qResults.length" class="q-scroll">
							<div v-for="(r, i) in qResults" :key="i" class="q-item">
								<div class="meta">{{ r.metadata?.document_title }}</div>
								<pre>{{ r.content }}</pre>
							</div>
						</el-scrollbar>
						<p v-else class="hint">无结果时会自动回退关键词匹配；开启全局向量配置后优先走向量检索。</p>
					</el-tab-pane>
				</el-tabs>
			</div>
		</el-drawer>

		<el-dialog v-model="chunkDlg" width="760px" destroy-on-close>
			<template #header>
				<div>文档分块详情 - {{ chunkDocTitle || '未命名文档' }}</div>
			</template>
			<div class="chunk-meta">
				<span>分块大小：{{ chunkMeta.chunk_size }}</span>
				<span>重叠：{{ chunkMeta.chunk_overlap }}</span>
				<span>总分块数：{{ chunkMeta.total_chunks }}</span>
			</div>
			<el-table v-loading="chunkLoading" :data="chunkList" size="small" max-height="480">
				<el-table-column prop="index" label="序号" width="80" />
				<el-table-column label="内容">
					<template #default="{ row }">
						<pre class="chunk-content">{{ row.content }}</pre>
					</template>
				</el-table-column>
			</el-table>
			<template #footer>
				<el-button @click="chunkDlg = false">关闭</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { UploadRequestOptions } from 'element-plus';
import { useProjectApi } from '/@/api/v1/projects/project';
import { projectPlatformApi } from '/@/api/v1/projects/platform';
import { aiKnowledgeConfigApi } from '/@/api/v1/ai/knowledge-config';

const projectApi = useProjectApi();
const projectId = ref<number | null>(null);
const projects = ref<{ id: number; name: string }[]>([]);

const loading = ref(false);
const bases = ref<any[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);

const kbDlg = ref(false);
const savingKb = ref(false);
const editKbId = ref<string | null>(null);
const kbForm = reactive({
	name: '',
	description: '',
	chunk_size: 1000,
	chunk_overlap: 200,
});

const gcDlg = ref(false);
const gcForm = reactive({
	embedding_provider: 'openai',
	embedding_base_url: '',
	embedding_api_key: '',
	embedding_model: 'text-embedding-3-small',
	vector_enabled: false,
	vector_provider: 'qdrant',
	vector_url: '',
	vector_api_key: '',
	vector_collection: 'knowledge_default',
	vector_dimension: 1536,
	retrieval_top_k: 5,
	chunk_size: 1000,
	chunk_overlap: 200,
	distance_metric: 'Cosine',
	remark: '',
});

const drawer = ref(false);
const detail = reactive<{ id: string | null; title: string }>({ id: null, title: '' });
const tab = ref('doc');
const docs = ref<any[]>([]);
const docLoading = ref(false);
const qText = ref('');
const qResults = ref<any[]>([]);
const chunkDlg = ref(false);
const chunkLoading = ref(false);
const chunkDocTitle = ref('');
const chunkList = ref<Array<{ index: number; content: string }>>([]);
const chunkMeta = reactive({
	chunk_size: 0,
	chunk_overlap: 0,
	total_chunks: 0,
});

function statusText(status?: string): string {
	const map: Record<string, string> = {
		completed: '已完成',
		processing: '处理中',
		pending: '等待中',
		failed: '失败',
	};
	return map[status || ''] || status || '-';
}

function statusTagType(status?: string): 'success' | 'warning' | 'danger' | 'info' {
	const map: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
		completed: 'success',
		processing: 'warning',
		pending: 'info',
		failed: 'danger',
	};
	return map[status || ''] || 'info';
}

async function loadProjects() {
	try {
		const res: any = await projectApi.getList({ page: 1, page_size: 50 });
		if (res?.code === 200 && res.data?.items) {
			projects.value = res.data.items;
			const stored = localStorage.getItem('defaultProjectId');
			if (stored && projects.value.some((p) => p.id === Number(stored))) {
				projectId.value = Number(stored);
			} else if (projects.value.length) {
				projectId.value = projects.value[0].id;
				localStorage.setItem('defaultProjectId', String(projectId.value));
			}
		}
	} catch (e: any) {
		ElMessage.error(e?.message || '获取项目列表失败');
	}
}

function onProjectChange() {
	if (projectId.value) localStorage.setItem('defaultProjectId', String(projectId.value));
	loadBases();
}

async function loadBases() {
	if (!projectId.value) return;
	loading.value = true;
	try {
		const res: any = await projectPlatformApi.knowledge.bases.list(projectId.value, {
			page: page.value,
			page_size: pageSize.value,
		});
		if (res?.code === 200 && res.data) {
			bases.value = res.data.items || [];
			total.value = res.data.total || 0;
		}
	} finally {
		loading.value = false;
	}
}

function openCreateKb() {
	editKbId.value = null;
	kbForm.name = '';
	kbForm.description = '';
	kbForm.chunk_size = 1000;
	kbForm.chunk_overlap = 200;
	kbDlg.value = true;
}

function editKb(row: any) {
	editKbId.value = String(row.id);
	kbForm.name = row.name;
	kbForm.description = row.description || '';
	kbForm.chunk_size = row.chunk_size;
	kbForm.chunk_overlap = row.chunk_overlap;
	kbDlg.value = true;
}

async function submitKb() {
	if (!projectId.value) return;
	savingKb.value = true;
	try {
		if (editKbId.value) {
			const res: any = await projectPlatformApi.knowledge.bases.update(projectId.value, editKbId.value, kbForm);
			if (res?.code === 200) {
				ElMessage.success('已保存');
				kbDlg.value = false;
				loadBases();
			}
		} else {
			const res: any = await projectPlatformApi.knowledge.bases.create(projectId.value, kbForm);
			if (res?.code === 200) {
				ElMessage.success('已创建');
				kbDlg.value = false;
				loadBases();
			}
		}
	} finally {
		savingKb.value = false;
	}
}

async function removeKb(row: any) {
	if (!projectId.value) return;
	await ElMessageBox.confirm('将删除该知识库及文档，确定？', '提示', { type: 'warning' });
	const res: any = await projectPlatformApi.knowledge.bases.remove(projectId.value, row.id);
	if (res?.code === 200) {
		ElMessage.success('已删除');
		loadBases();
	}
}

function onRow(row: any) {
	openDetail(row);
}

function openDetail(row: any) {
	detail.id = String(row.id);
	detail.title = row.name;
	drawer.value = true;
	tab.value = 'doc';
	qResults.value = [];
	loadDocs();
}

async function loadDocs() {
	if (!projectId.value || !detail.id) return;
	docLoading.value = true;
	try {
		const res: any = await projectPlatformApi.knowledge.documents.list(projectId.value, detail.id, {
			page: 1,
			page_size: 100,
		});
		if (res?.code === 200 && res.data) {
			docs.value = res.data.items || [];
		}
	} finally {
		docLoading.value = false;
	}
}

async function customUpload(opt: UploadRequestOptions) {
	if (!projectId.value || !detail.id) return;
	const file = opt.file as File;
	const res: any = await projectPlatformApi.knowledge.documents.upload(projectId.value, detail.id, file);
	if (res?.code === 200) {
		ElMessage.success('上传成功');
		loadDocs();
		loadBases();
	}
}

async function removeDoc(row: any) {
	if (!projectId.value || !detail.id) return;
	await ElMessageBox.confirm('删除该文档？', '提示', { type: 'warning' });
	const res: any = await projectPlatformApi.knowledge.documents.remove(projectId.value, detail.id, row.id);
	if (res?.code === 200) {
		ElMessage.success('已删除');
		loadDocs();
		loadBases();
	}
}

async function viewChunks(row: any) {
	if (!projectId.value || !detail.id) return;
	chunkDlg.value = true;
	chunkLoading.value = true;
	chunkDocTitle.value = row?.title || '';
	chunkList.value = [];
	chunkMeta.chunk_size = 0;
	chunkMeta.chunk_overlap = 0;
	chunkMeta.total_chunks = 0;
	try {
		const res: any = await projectPlatformApi.knowledge.documents.chunks(projectId.value, detail.id, row.id);
		if (res?.code === 200 && res.data) {
			chunkList.value = res.data.chunks || [];
			chunkMeta.chunk_size = res.data.chunk_size || 0;
			chunkMeta.chunk_overlap = res.data.chunk_overlap || 0;
			chunkMeta.total_chunks = res.data.total_chunks || 0;
		}
	} catch (e: any) {
		ElMessage.error(e?.message || '获取分块失败');
	}
	finally {
		chunkLoading.value = false;
	}
}

async function runQuery() {
	if (!projectId.value || !detail.id || !qText.value.trim()) return;
	const res: any = await projectPlatformApi.knowledge.query(projectId.value, detail.id, {
		query: qText.value.trim(),
		top_k: 5,
	});
	if (res?.code === 200 && res.data?.results) {
		qResults.value = res.data.results;
	}
}

async function openGlobal() {
	const res: any = await aiKnowledgeConfigApi.getGlobal();
	if (res?.code === 200 && res.data) {
		Object.assign(gcForm, res.data);
	}
	gcDlg.value = true;
}

async function saveGc() {
	const res: any = await aiKnowledgeConfigApi.saveGlobal({ ...gcForm });
	if (res?.code === 200) {
		ElMessage.success('已保存');
	}
}

const testingEmb = ref(false);
const testingVector = ref(false);

function formatRequestError(err: any): string {
	if (err?.message && typeof err.message === 'string') return err.message;
	const d = err?.response?.data;
	if (!d) return '请求失败';
	if (typeof d.detail === 'string') return d.detail;
	if (Array.isArray(d.detail)) {
		const first = d.detail[0];
		if (first?.msg) return `${first.loc?.join?.('.') ?? ''} ${first.msg}`.trim();
	}
	return d.message || d.msg || '请求失败';
}

async function testEmb() {
	testingEmb.value = true;
	try {
		const res: any = await aiKnowledgeConfigApi.testEmbedding({
			embedding_provider: gcForm.embedding_provider,
			embedding_base_url: gcForm.embedding_base_url,
			embedding_api_key: gcForm.embedding_api_key,
			embedding_model: gcForm.embedding_model,
		});
		if (res?.code === 200) {
			ElMessage.success(res.message || '嵌入连接成功');
		} else {
			ElMessage.error(res?.message || '嵌入连接失败');
		}
	} catch (err: any) {
		ElMessage.error(formatRequestError(err));
	} finally {
		testingEmb.value = false;
	}
}

async function testVector() {
	testingVector.value = true;
	try {
		const res: any = await aiKnowledgeConfigApi.testVectorDb({
			vector_provider: gcForm.vector_provider,
			vector_url: gcForm.vector_url,
			vector_api_key: gcForm.vector_api_key,
		});
		if (res?.code === 200) {
			ElMessage.success(res.message || '向量库连接成功');
		} else {
			ElMessage.error(res?.message || '向量库连接失败');
		}
	} catch (err: any) {
		ElMessage.error(formatRequestError(err));
	} finally {
		testingVector.value = false;
	}
}

onMounted(async () => {
	await loadProjects();
	await loadBases();
});
</script>

<style scoped>
.page-wrap {
	padding: 12px;
}
.toolbar {
	margin-bottom: 12px;
}
.pager {
	margin-top: 12px;
	display: flex;
	justify-content: flex-end;
}
.row-actions {
	display: flex;
	gap: 8px;
	margin-bottom: 8px;
}
.q-scroll {
	max-height: 420px;
	margin-top: 8px;
}
.q-item {
	padding: 8px;
	border-bottom: 1px solid var(--el-border-color-lighter);
}
.meta {
	font-size: 12px;
	color: var(--el-text-color-secondary);
}
.hint {
	color: var(--el-text-color-secondary);
	font-size: 13px;
}
.drawer-body {
	padding: 8px 12px 12px;
}
.chunk-meta {
	display: flex;
	gap: 16px;
	margin-bottom: 10px;
	color: var(--el-text-color-secondary);
	font-size: 13px;
}
.chunk-content {
	margin: 0;
	max-height: 160px;
	overflow: auto;
	white-space: pre-wrap;
	word-break: break-word;
}
pre {
	white-space: pre-wrap;
	word-break: break-word;
}
</style>
