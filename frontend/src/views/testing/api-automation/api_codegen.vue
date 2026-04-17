<template>
  <div class="codegen-layout">

    <!-- 左侧配置面板 -->
    <div class="codegen-sidebar">
      <div class="sidebar-section">
        <div class="section-title">
          <el-icon><Setting /></el-icon> 框架选择
        </div>
        <div class="framework-grid">
          <div
            v-for="fw in frameworks"
            :key="fw.value"
            class="framework-card"
            :class="{ 'framework-card--active': form.framework === fw.value }"
            @click="form.framework = fw.value"
          >
            <span class="framework-card-dot" :style="{ background: fw.color }"></span>
            <span class="framework-card-name">{{ fw.label }}</span>
            <span class="framework-card-lang">{{ fw.lang }}</span>
          </div>
        </div>
      </div>

      <el-divider />

      <div class="sidebar-section">
        <div class="section-title">
          <el-icon><Connection /></el-icon> 接口来源
        </div>
        <el-select v-model="form.source_type" style="width:100%" @change="onSourceChange">
          <el-option label="Swagger 拉取接口" value="swagger" />
          <el-option label="Apifox 拉取接口" value="apifox" />
          <el-option label="接口用例" value="case" />
          <el-option label="自定义编写" value="custom" />
        </el-select>
      </div>

      <!-- swagger / apifox / case：从接口树选择 -->
      <template v-if="form.source_type !== 'custom'">
        <div class="sidebar-section">
          <div class="section-title">
            <el-icon><List /></el-icon> 选择服务
          </div>
          <el-select
            v-model="form.service_id"
            filterable
            clearable
            placeholder="选择服务"
            style="width:100%"
            @change="onServiceChange"
          >
            <el-option v-for="s in serviceList" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </div>

        <div class="sidebar-section">
          <div class="section-title">
            <el-icon><Files /></el-icon> 选择接口
            <el-tag size="small" type="info" class="ml-4">已选 {{ selectedApiIds.length }}</el-tag>
          </div>
          <el-input
            v-model="apiFilter"
            placeholder="过滤接口名称"
            clearable
            size="small"
            :prefix-icon="Search"
            class="mb-8"
          />
          <el-scrollbar height="280px">
            <el-tree
              ref="apiTreeRef"
              :data="apiTree"
              :props="{ children: 'children', label: 'name' }"
              show-checkbox
              node-key="id"
              :filter-node-method="filterApiNode"
              @check="onTreeCheck"
            >
              <template #default="{ data }">
                <span class="tree-node-item">
                  <el-tag
                    v-if="data.type === 2"
                    size="small"
                    :type="methodTagType(data.method)"
                    class="method-tag"
                  >{{ data.method || 'API' }}</el-tag>
                  <el-icon v-else class="folder-icon"><Folder /></el-icon>
                  <span class="node-name">{{ data.name }}</span>
                </span>
              </template>
            </el-tree>
          </el-scrollbar>
        </div>
      </template>

      <!-- 自定义：手动填写接口 -->
      <template v-else>
        <div class="sidebar-section">
          <div class="section-title">
            <el-icon><EditPen /></el-icon> 自定义接口
            <el-button size="small" type="primary" link :icon="Plus" @click="addCustomApi">添加</el-button>
          </div>
          <el-scrollbar height="380px">
            <div v-for="(a, idx) in form.custom_apis" :key="idx" class="custom-api-item">
              <!-- 接口头部行 -->
              <div class="custom-api-row">
                <el-select v-model="a.method" style="width:82px" size="small">
                  <el-option v-for="m in methods" :key="m" :label="m" :value="m" />
                </el-select>
                <el-input v-model="a.url" placeholder="/api/path" size="small" style="flex:1;min-width:0" />
                <el-button size="small" link :icon="a.expanded ? ArrowUp : ArrowDown" @click="a.expanded = !a.expanded" />
                <el-button size="small" type="danger" link :icon="Delete" @click="removeCustomApi(idx)" />
              </div>
              <el-input v-model="a.name" placeholder="接口名称（可选）" size="small" class="mt-4" />

              <!-- 展开的详细配置 -->
              <div v-if="a.expanded" class="custom-api-detail">
                <el-tabs v-model="a._tab" size="small" class="detail-tabs">
                  <el-tab-pane label="Params" name="params">
                    <div v-for="(p, pi) in a.params" :key="pi" class="kv-row">
                      <el-checkbox v-model="p.enabled" size="small" />
                      <el-input v-model="p.key" placeholder="key" size="small" style="flex:1;min-width:0" />
                      <el-input v-model="p.value" placeholder="value" size="small" style="flex:1;min-width:0" />
                      <el-button size="small" type="danger" link :icon="Delete" @click="a.params.splice(pi,1)" />
                    </div>
                    <el-button size="small" link type="primary" :icon="Plus" @click="a.params.push({key:'',value:'',enabled:true})">添加</el-button>
                  </el-tab-pane>

                  <el-tab-pane label="Headers" name="headers">
                    <div v-for="(h, hi) in a.headers" :key="hi" class="kv-row">
                      <el-checkbox v-model="h.enabled" size="small" />
                      <el-input v-model="h.key" placeholder="key" size="small" style="flex:1;min-width:0" />
                      <el-input v-model="h.value" placeholder="value" size="small" style="flex:1;min-width:0" />
                      <el-button size="small" type="danger" link :icon="Delete" @click="a.headers.splice(hi,1)" />
                    </div>
                    <el-button size="small" link type="primary" :icon="Plus" @click="a.headers.push({key:'',value:'',enabled:true})">添加</el-button>
                  </el-tab-pane>

                  <el-tab-pane label="Body" name="body">
                    <el-radio-group v-model="a.body_type" size="small" class="body-type-group">
                      <el-radio-button value="none">None</el-radio-button>
                      <el-radio-button value="json">JSON</el-radio-button>
                      <el-radio-button value="form">Form</el-radio-button>
                    </el-radio-group>
                    <el-input
                      v-if="a.body_type !== 'none'"
                      v-model="a.body"
                      type="textarea"
                      :rows="4"
                      size="small"
                      class="mt-4"
                      :placeholder="a.body_type === 'json' ? bodyJsonPlaceholder : bodyFormPlaceholder"
                    />
                  </el-tab-pane>
                </el-tabs>
              </div>
            </div>
          </el-scrollbar>
        </div>
      </template>

      <el-divider />

      <div class="sidebar-section">
        <div class="section-title"><el-icon><Link /></el-icon> 基础配置</div>
        <el-form label-width="70px" size="small">
          <el-form-item label="Base URL">
            <el-input v-model="form.base_url" placeholder="https://api.example.com" />
          </el-form-item>
          <el-form-item label="类名">
            <el-input v-model="form.class_name" placeholder="AutoGenerated" />
          </el-form-item>
        </el-form>
      </div>

      <div class="sidebar-actions">
        <el-button type="primary" :loading="generating" :icon="MagicStick" style="width:100%" @click="doGenerate">
          生成代码
        </el-button>
      </div>
    </div>

    <!-- 右侧编辑器区域 -->
    <div class="codegen-editor-area">
      <!-- 工具栏 -->
      <div class="editor-toolbar">
        <div class="toolbar-left">
          <el-tag :type="frameworkTagType" size="small" effect="dark">{{ form.framework }}</el-tag>
          <span class="toolbar-hint">代码可直接编辑</span>
        </div>
        <div class="toolbar-right">
          <el-button size="small" :icon="CopyDocument" @click="copyCode">复制</el-button>
          <el-button size="small" :icon="Download" @click="downloadCode">下载</el-button>
          <el-button
            v-if="canRun"
            size="small"
            type="success"
            :icon="VideoPlay"
            :loading="running"
            @click="runCode"
          >运行</el-button>
        </div>
      </div>

      <!-- Monaco 编辑器 -->
      <div class="editor-wrap">
        <div v-if="!generatedCode" class="editor-placeholder">
          <el-empty :image-size="80" description="配置左侧参数后点击「生成代码」" />
        </div>
        <MonacoEditor
          v-else
          v-model:value="generatedCode"
          :long="editorLanguage"
          theme="vs-dark"
          :options="editorOptions"
          style="height:100%;width:100%"
        />
      </div>

      <!-- 运行输出 -->
      <div v-if="runOutput" class="run-output">
        <div class="run-output-header">
          <span>
            <el-icon><Terminal /></el-icon> 运行输出
          </span>
          <div class="run-output-actions">
            <el-tag :type="runSuccess ? 'success' : 'danger'" size="small">
              {{ runSuccess ? '通过' : '失败' }}
            </el-tag>
            <el-button size="small" link :icon="Close" @click="runOutput = ''" />
          </div>
        </div>
        <pre class="run-output-pre">{{ runOutput }}</pre>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { ElMessage } from 'element-plus';
import {
  Setting, Connection, List, Files, Search, Folder, EditPen,
  Plus, Delete, Link, MagicStick, CopyDocument, Download,
  VideoPlay, Close, ArrowUp, ArrowDown,
} from '@element-plus/icons-vue';
import MonacoEditor from '/@/components/monaco/index.vue';
import { useApiAutomationApi } from '/@/api/v1/api_automation';

// 临时图标占位（项目中无 Python 图标时用文字代替）
const Python = Setting;
const Terminal = List;

const api = useApiAutomationApi();

// ── 框架列表 ─────────────────────────────────────────────────────────
const frameworks = [
  { value: 'pytest',    label: 'pytest',    lang: 'Python', color: '#3fb950' },
  { value: 'unittest',  label: 'unittest',  lang: 'Python', color: '#58a6ff' },
  { value: 'testng',    label: 'TestNG',    lang: 'Java',   color: '#e3b341' },
  { value: 'jest',      label: 'Jest',      lang: 'JS/TS',  color: '#f85149' },
];

// ── 表单状态 ──────────────────────────────────────────────────────────
const form = ref({
  framework: 'pytest' as 'pytest' | 'unittest' | 'testng' | 'jest',
  source_type: 'swagger' as 'swagger' | 'apifox' | 'case' | 'custom',
  service_id: undefined as number | undefined,
  base_url: '',
  class_name: 'AutoGenerated',
  custom_apis: [] as {
    method: string;
    url: string;
    name: string;
    expanded: boolean;
    _tab: string;
    headers: { key: string; value: string; enabled: boolean }[];
    params: { key: string; value: string; enabled: boolean }[];
    body_type: 'none' | 'json' | 'form';
    body: string;
  }[],
});

const methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'];

// ── 服务 & 接口树 ─────────────────────────────────────────────────────
const serviceList = ref<any[]>([]);
const apiTree = ref<any[]>([]);
const apiFilter = ref('');
const apiTreeRef = ref<any>(null);
const selectedApiIds = ref<number[]>([]);

async function loadServices() {
  try {
    const res: any = await api.api_service_list({});
    const raw = res?.data ?? res;
    serviceList.value = Array.isArray(raw) ? raw : raw?.data ?? [];
  } catch { serviceList.value = []; }
}

async function onServiceChange(id: number) {
  selectedApiIds.value = [];
  if (!id) { apiTree.value = []; return; }
  try {
    const res: any = await api.api_tree({ search: { api_service_id: id } });
    const raw = res?.data ?? res;
    apiTree.value = Array.isArray(raw) ? raw : raw?.data ?? [];
  } catch { apiTree.value = []; }
}

function onSourceChange() {
  selectedApiIds.value = [];
  apiTree.value = [];
  form.value.service_id = undefined;
}

watch(apiFilter, (v) => apiTreeRef.value?.filter(v));

function filterApiNode(value: string, data: any) {
  return !value || String(data.name || '').includes(value);
}

function onTreeCheck(_: any, state: any) {
  selectedApiIds.value = (state.checkedNodes as any[])
    .filter((n) => n.type === 2 && n.api_id)
    .map((n) => n.api_id);
}

function methodTagType(method: string) {
  const m: Record<string, string> = { GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger', PATCH: 'info' };
  return (m[String(method).toUpperCase()] || 'info') as any;
}

// ── 自定义接口 ────────────────────────────────────────────────────────
const bodyJsonPlaceholder = '{"key": "value"}';
const bodyFormPlaceholder = 'key: value\nkey2: value2';

function addCustomApi() {
  form.value.custom_apis.push({
    method: 'GET', url: '', name: '',
    expanded: true,
    _tab: 'params',
    headers: [],
    params: [],
    body_type: 'none',
    body: '',
  });
}
function removeCustomApi(idx: number) {
  form.value.custom_apis.splice(idx, 1);
}

// ── 代码生成 ──────────────────────────────────────────────────────────
const generating = ref(false);
const generatedCode = ref('');

async function doGenerate() {
  if (form.value.source_type !== 'custom' && selectedApiIds.value.length === 0) {
    ElMessage.warning('请先从接口树中勾选至少一个接口');
    return;
  }
  if (form.value.source_type === 'custom' && form.value.custom_apis.length === 0) {
    ElMessage.warning('请先添加至少一个自定义接口');
    return;
  }
  generating.value = true;
  try {
    const payload: any = {
      source_type: form.value.source_type,
      framework: form.value.framework,
      base_url: form.value.base_url,
      class_name: form.value.class_name || 'AutoGenerated',
    };
    if (form.value.source_type !== 'custom') {
      payload.api_ids = selectedApiIds.value;
      payload.service_id = form.value.service_id;
    } else {
      payload.custom_apis = form.value.custom_apis.map((a) => ({
        url: a.url,
        name: a.name || a.url,
        req: {
          method: a.method,
          header: a.headers.filter(h => h.key).map(h => ({ key: h.key, value: h.value, status: h.enabled })),
          params: a.params.filter(p => p.key).map(p => ({ key: p.key, value: p.value, status: p.enabled })),
          body_type: a.body_type === 'none' ? 1 : a.body_type === 'json' ? 2 : 3,
          body: a.body_type === 'json' ? a.body : '',
          form_data: a.body_type === 'form'
            ? a.body.split('\n').filter(Boolean).map(line => {
                const [k, ...rest] = line.split(':');
                return { key: k.trim(), value: rest.join(':').trim(), status: true };
              })
            : [],
        },
      }));
    }
    const res: any = await api.generate_code(payload);
    const data = res?.data ?? res;
    generatedCode.value = data?.code ?? '';
    runOutput.value = '';
    ElMessage.success('代码生成成功');
  } catch (e: any) {
    ElMessage.error(e?.message || '生成失败');
  } finally {
    generating.value = false;
  }
}

// ── 编辑器配置 ────────────────────────────────────────────────────────
const editorLanguage = computed(() => {
  const m: Record<string, string> = { pytest: 'python', unittest: 'python', testng: 'java', jest: 'javascript' };
  return m[form.value.framework] || 'python';
});

const editorOptions = {
  fontSize: 13,
  minimap: { enabled: false },
  scrollBeyondLastLine: false,
  automaticLayout: true,
  tabSize: 4,
};

const frameworkTagType = computed(() => {
  const m: Record<string, string> = { pytest: 'success', unittest: 'primary', testng: 'warning', jest: 'info' };
  return (m[form.value.framework] || 'info') as any;
});

// ── 复制 / 下载 ───────────────────────────────────────────────────────
async function copyCode() {
  if (!generatedCode.value) return;
  try {
    await navigator.clipboard.writeText(generatedCode.value);
    ElMessage.success('已复制到剪贴板');
  } catch {
    ElMessage.error('复制失败，请手动选择复制');
  }
}

function downloadCode() {
  if (!generatedCode.value) return;
  const ext: Record<string, string> = { pytest: 'py', unittest: 'py', testng: 'java', jest: 'js' };
  const filename = `test_${form.value.class_name || 'auto'}.${ext[form.value.framework] || 'txt'}`;
  const blob = new Blob([generatedCode.value], { type: 'text/plain;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

// ── 运行 ──────────────────────────────────────────────────────────────
const canRun = computed(() => ['pytest', 'unittest'].includes(form.value.framework) && !!generatedCode.value);
const running = ref(false);
const runOutput = ref('');
const runSuccess = ref(false);

async function runCode() {
  if (!generatedCode.value) return;
  running.value = true;
  runOutput.value = '';
  try {
    const res: any = await api.run_generated_code({ code: generatedCode.value, framework: form.value.framework });
    const data = res?.data ?? res;
    runOutput.value = data?.output ?? '';
    runSuccess.value = data?.success ?? false;
  } catch (e: any) {
    runOutput.value = e?.message || '运行失败';
    runSuccess.value = false;
  } finally {
    running.value = false;
  }
}

// ── 初始化 ────────────────────────────────────────────────────────────
loadServices();
</script>

<style scoped lang="scss">
.codegen-layout {
  display: flex;
  height: 100%;
  min-height: 0;
  flex: 1;
  gap: 0;
  background: var(--el-bg-color-page);
}

/* ── 左侧配置面板 ── */
.codegen-sidebar {
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-lighter);
  overflow-y: auto;
  padding: 0 0 12px;
}

.sidebar-section {
  padding: 12px 14px 4px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 8px;
}

/* 框架卡片网格 */
.framework-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.framework-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 10px;
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-lighter);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, box-shadow 0.15s;
  user-select: none;

  &:hover {
    border-color: var(--el-color-primary-light-5);
    background: var(--el-fill-color-light);
  }

  &--active {
    border-color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
    box-shadow: 0 0 0 1px var(--el-color-primary-light-5);
  }
}

.framework-card-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.framework-card-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  flex: 1;
}

.framework-card-lang {
  font-size: 10px;
  color: var(--el-text-color-placeholder);
  flex-shrink: 0;
}

.sidebar-actions {
  padding: 12px 14px 0;
  margin-top: auto;
}

/* 接口树节点 */
.tree-node-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.method-tag {
  font-size: 10px;
  padding: 0 4px;
  height: 16px;
  line-height: 16px;
  flex-shrink: 0;
}

.folder-icon {
  color: var(--el-color-warning);
  font-size: 13px;
}

.node-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

/* 自定义接口 */
.custom-api-item {
  padding: 8px;
  margin-bottom: 8px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  background: var(--el-fill-color-lighter);
}

.custom-api-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.custom-api-detail {
  margin-top: 8px;
  border-top: 1px solid var(--el-border-color-lighter);
  padding-top: 6px;
}

.detail-tabs {
  :deep(.el-tabs__header) { margin-bottom: 6px; }
  :deep(.el-tabs__item) { font-size: 11px; padding: 0 8px; height: 28px; line-height: 28px; }
  :deep(.el-tabs__nav-wrap::after) { height: 1px; }
}

.kv-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
}

.body-type-group {
  :deep(.el-radio-button__inner) { padding: 3px 8px; font-size: 11px; }
}

/* ── 右侧编辑器区域 ── */
.codegen-editor-area {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #1e1e1e;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 14px;
  background: #252526;
  border-bottom: 1px solid #3c3c3c;
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-hint {
  font-size: 12px;
  color: #6e7681;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.editor-wrap {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  position: relative;
}

.editor-placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1e1e1e;

  :deep(.el-empty__description p) {
    color: #6e7681;
  }
}

/* 运行输出 */
.run-output {
  flex-shrink: 0;
  max-height: 220px;
  display: flex;
  flex-direction: column;
  border-top: 1px solid #3c3c3c;
  background: #0d1117;
}

.run-output-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: #161b22;
  color: #8b949e;
  font-size: 12px;
  flex-shrink: 0;
}

.run-output-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.run-output-pre {
  flex: 1;
  overflow-y: auto;
  margin: 0;
  padding: 10px 14px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #e6edf3;
  white-space: pre-wrap;
  word-break: break-all;
}

/* 工具类 */
.ml-4 { margin-left: 4px; }
.mb-8 { margin-bottom: 8px; }
.mt-4 { margin-top: 4px; }
</style>
