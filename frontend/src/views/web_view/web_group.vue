<template>
  <div class="web-group-page">
    <!-- 顶部工具栏 -->
    <div class="group-toolbar">
      <div class="toolbar-left">
        <el-input v-model="searchParams.search.name__icontains" placeholder="搜索脚本名称" clearable style="width:200px" @keyup.enter="group_list" />
        <el-button type="primary" icon="Search" @click="group_list">搜索</el-button>
        <el-button icon="Refresh" @click="reset_search">重置</el-button>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" @click="Add">新增脚本</el-button>
      </div>
    </div>

    <!-- 主体：左侧模块树 + 右侧脚本列表 -->
    <div class="group-body">
      <!-- 左侧模块树 -->
      <div class="module-panel">
        <div class="module-panel-header">
          <span class="module-panel-title">脚本模块</span>
          <span class="module-panel-all" :class="{'module-panel-all--active': !selectedMenuNode}" @click="selectedMenuNode=null">全部</span>
        </div>
        <div class="module-list">
          <template v-for="node in menuTree" :key="node.id">
            <div
              class="mnode"
              :class="{'mnode--active': selectedMenuNode && selectedMenuNode.id === node.id}"
              @click="selectedMenuNode = node"
            >
              <i class="mnode-icon micon-home"></i>
              <span class="mnode-name">{{ node.name }}</span>
            </div>
            <template v-if="node.children && node.children.length">
              <template v-for="child in node.children" :key="child.id">
                <div
                  class="mnode mnode--child"
                  :class="{'mnode--active': selectedMenuNode && selectedMenuNode.id === child.id}"
                  @click="selectedMenuNode = child"
                >
                  <i class="mnode-icon micon-folder"></i>
                  <span class="mnode-name">{{ child.name }}</span>
                </div>
                <template v-if="child.children && child.children.length">
                  <div
                    v-for="leaf in child.children"
                    :key="leaf.id"
                    class="mnode mnode--leaf"
                    :class="{'mnode--active': selectedMenuNode && selectedMenuNode.id === leaf.id}"
                    @click="selectedMenuNode = leaf"
                  >
                    <i class="mnode-icon micon-script"></i>
                    <span class="mnode-name">{{ leaf.name }}</span>
                  </div>
                </template>
              </template>
            </template>
          </template>
        </div>
      </div>

      <!-- 右侧列表 -->
      <div class="scene-panel">
        <el-table :data="filteredTableData" border stripe empty-text="暂无脚本" style="width:100%">
          <el-table-column prop="id" label="ID" width="70" align="center" />
          <el-table-column prop="name" label="脚本名称" min-width="160" show-overflow-tooltip />
          <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">{{ row.description || '-' }}</template>
          </el-table-column>
          <el-table-column label="脚本数" width="80" align="center">
            <template #default="{ row }">
              <span style="display:inline-block;min-width:20px;height:20px;line-height:20px;text-align:center;background:#409eff;color:#fff;border-radius:10px;font-size:11px;padding:0 6px">
                {{ (row.script || []).filter(Boolean).length }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="username" label="更新人" width="90" align="center" show-overflow-tooltip />
          <el-table-column label="创建时间" width="160" align="center">
            <template #default="{ row }">{{ row.create_time ? String(row.create_time).replace('T',' ').slice(0,19) : '-' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="200" align="center" fixed="right">
            <template #default="{ row }">
              <span style="white-space:nowrap;display:inline-flex;gap:4px">
                <el-button type="success" size="small" @click="run_script(row)">运行</el-button>
                <el-button type="warning" size="small" @click="Edit(row)">编辑</el-button>
                <el-button type="danger" size="small" @click="Delete(row)">删除</el-button>
              </span>
            </template>
          </el-table-column>
        </el-table>

        <div style="margin-top:12px">
          <el-pagination v-show="total > 0" background v-model:current-page="searchParams.currentPage" v-model:page-size="searchParams.pageSize" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next, jumper" :total="total" @size-change="group_list" @current-change="group_list" />
        </div>
      </div>
    </div>

      <!-- 新增/编辑脚本弹窗 -->
      <el-dialog
        v-model="scriptDialogVisible"
        :title="title"
        width="860px"
        @close="resetScriptForm"
      >
        <div class="script-dialog-body">
          <!-- 左侧：脚本树选择 -->
          <div class="script-picker">
            <div class="picker-header">
              <span class="picker-title">选择脚本</span>
              <el-input v-model="pickerKeyword" placeholder="搜索脚本" clearable size="small" style="flex:1;margin-left:8px" />
            </div>
            <div class="module-list picker-list">
              <template v-for="node in pickerTreeData" :key="node.id">
                <!-- 顶层是脚本节点，直接可点击 -->
                <div
                  v-if="node.type===2"
                  class="mnode mnode--clickable"
                  :class="{'mnode--added': addedScriptIds.has(Number(node.id))}"
                  style="padding-left:8px"
                  @click="onPickerNodeClick(node)"
                >
                  <i class="mnode-icon micon-script"></i>
                  <span class="mnode-name">{{ node.name }}</span>
                  <span v-if="addedScriptIds.has(Number(node.id))" class="picker-badge picker-badge--added">✓ 已添加</span>
                  <span v-else class="picker-badge picker-badge--add">+ 添加</span>
                </div>
                <!-- 顶层是分组/目录节点 -->
                <template v-else>
                  <div class="mnode" style="padding-left:8px">
                    <i class="mnode-icon" :class="node.type===0?'micon-home':'micon-folder'"></i>
                    <span class="mnode-name">{{ node.name }}</span>
                  </div>
                  <div
                    v-for="leaf in node._flatChildren"
                    :key="leaf.id"
                    class="mnode mnode--clickable"
                    :class="{'mnode--added': addedScriptIds.has(Number(leaf.id))}"
                    :style="'padding-left:' + (8 + leaf._depth * 14) + 'px'"
                    @click="onPickerNodeClick(leaf)"
                  >
                    <i class="mnode-icon micon-script"></i>
                    <span class="mnode-name">{{ leaf.name }}</span>
                    <span v-if="addedScriptIds.has(Number(leaf.id))" class="picker-badge picker-badge--added">✓ 已添加</span>
                    <span v-else class="picker-badge picker-badge--add">+ 添加</span>
                  </div>
                </template>
              </template>
            </div>
          </div>

          <!-- 右侧：已选脚本 + 基本信息 -->
          <div class="script-config">
            <el-form :model="add_form" label-width="70px">
              <el-form-item label="脚本名称" required>
                <el-input v-model="add_form.name" placeholder="请输入脚本名称" />
              </el-form-item>
              <el-form-item label="描述">
                <el-input v-model="add_form.description" placeholder="可选" type="textarea" :rows="2" />
              </el-form-item>
            </el-form>

            <div class="selected-header">
              <span class="selected-title">已选脚本 ({{ add_form.script?.length || 0 }})</span>
              <el-button link size="small" type="danger" @click="add_form.script=[]">清空</el-button>
            </div>
            <div class="selected-list">
              <div v-if="!add_form.script?.length" class="selected-empty">
                <span style="font-size:28px;color:#dcdfe6"></span>
                <p>从左侧点击脚本添加</p>
              </div>
              <div
                v-for="(s, i) in (add_form.script || [])"
                :key="String(s.id ?? i) + '_' + i"
                class="selected-item"
              >
                <span class="selected-index">{{ i + 1 }}</span>
                <span style="color:#67c23a;flex-shrink:0;font-size:13px">●</span>
                <span class="selected-name">{{ s.name }}</span>
                <span class="selected-del" @click.stop="del_web(s)" style="cursor:pointer;color:#c0c4cc;font-size:18px;line-height:1;flex-shrink:0">×</span>
              </div>
            </div>
          </div>
        </div>

        <template #footer>
          <el-button @click="scriptDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitScriptForm">保存</el-button>
        </template>
      </el-dialog>

      <!-- 运行配置弹窗 -->
      <el-dialog v-model="runDialogVisible" title="运行配置" width="420px" destroy-on-close>
        <el-form :model="run_script_form" label-width="90px">
          <el-form-item label="任务名称" required>
            <el-input v-model="run_script_form.task_name" placeholder="请输入任务名称" />
          </el-form-item>
          <el-form-item label="执行模式">
            <el-radio-group v-model="run_script_form.browser_type">
              <el-radio :value="1">有界面</el-radio>
              <el-radio :value="2">无界面</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="分辨率">
            <div style="display:flex;align-items:center;gap:8px">
              <el-input-number v-model="run_script_form.width" controls-position="right" :min="800" style="width:130px" />
              <span style="color:#909399">×</span>
              <el-input-number v-model="run_script_form.height" controls-position="right" :min="600" style="width:130px" />
            </div>
          </el-form-item>
          <el-form-item label="浏览器">
            <el-select v-model="run_script_form.browser" multiple style="width:100%">
              <el-option v-for="item in browser_list" :key="item.value" :label="item.name" :value="item.value" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="runDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="run_script_confirm">确认运行</el-button>
        </template>
      </el-dialog>

      <el-drawer
        v-model="runMonitorDrawerVisible"
        :title="title"
        direction="rtl"
        size="min(92vw, 1680px)"
        append-to-body
        class="wa-run-monitor-drawer wa-run-monitor-theme"
        :show-close="true"
        :close-on-click-modal="false"
        @closed="onRunMonitorDrawerClosed"
      >
        <template #header>
          <div class="wa-run-monitor-drawer-header">
            <div class="wa-run-monitor-drawer-titleline">
              <span class="wa-run-monitor-drawer-title">{{ title }}</span>
              <el-tag type="info" effect="plain" size="small" class="wa-run-monitor-drawer-badge">执行监控</el-tag>
            </div>
            <p class="wa-run-monitor-drawer-sub">步骤与日志，执行结束后可继续查看或关闭抽屉</p>
          </div>
        </template>
        <div class="wa-run-monitor-shell">
          <div class="wa-run-monitor-body">
            <el-tabs
              tab-position="left"
              v-model="run_browser_active"
              class="wa-run-monitor-tabs"
              @tab-click="change_browser"
            >
              <el-tab-pane v-for="(item, index) in run_browsers" :key="index" :name="item.value">
                <template #label>
                  <span class="wa-run-monitor-tab-label">{{ item.name }}</span>
                </template>
                <div class="wa-run-monitor-pane">
                  <div class="wa-run-monitor-desc">
                    <el-card shadow="never" class="wa-run-monitor-surface wa-run-monitor-summary">
                      <el-descriptions :column="3" class="wa-run-monitor-desc-table" size="small">
                        <el-descriptions-item label="执行状态">
                          <span v-if="run_type === '正在执行'" class="wa-run-monitor-pill wa-run-monitor-pill--run">{{
                            run_type
                          }}</span>
                          <span
                            v-else-if="run_type === '执行结束'"
                            class="wa-run-monitor-pill wa-run-monitor-pill--done"
                          >{{ run_type }}</span>
                        </el-descriptions-item>
                        <el-descriptions-item label="浏览器">{{ item.name }}</el-descriptions-item>
                        <el-descriptions-item label="执行人">{{ user?.username || '—' }}</el-descriptions-item>
                        <el-descriptions-item label="开始时间">{{
                          start_time ? fmtDateTime(start_time) : '—'
                        }}</el-descriptions-item>
                        <el-descriptions-item label="结束时间">{{
                          end_time ? fmtDateTime(end_time) : '—'
                        }}</el-descriptions-item>
                        <el-descriptions-item label="已执行">{{ run_count }}</el-descriptions-item>
                        <el-descriptions-item label="通过">{{ run_count - run_fail }}</el-descriptions-item>
                        <el-descriptions-item label="失败">{{ run_fail }}</el-descriptions-item>
                      </el-descriptions>
                    </el-card>
                  </div>
                  <div class="wa-run-monitor-split">
                    <el-card
                      shadow="never"
                      class="wa-run-monitor-surface wa-run-monitor-card wa-run-monitor-card--timeline"
                    >
                      <template #header>
                        <span class="wa-run-monitor-card-title">执行步骤</span>
                      </template>
                      <el-timeline class="wa-run-monitor-timeline">
                        <el-timeline-item
                          v-for="(res, index) in web_result"
                          :key="index"
                          center
                          :icon="getIcon(res.status)"
                          type="primary"
                          :color="colors(res.status)"
                          size="large"
                          :timestamp="'执行时间：' + fmtDateTime(res.create_time)"
                          placement="top"
                        >
                          <el-card
                            shadow="never"
                            class="wa-run-monitor-timeline-node"
                            :class="
                              res.status === 1
                                ? 'wa-run-monitor-timeline-node--ok'
                                : 'wa-run-monitor-timeline-node--fail'
                            "
                            :body-style="{ padding: '8px 12px' }"
                          >
                            <span>{{ res.name }}</span>
                            <span>{{ '结果：' + res.log }}</span>
                          </el-card>
                        </el-timeline-item>
                      </el-timeline>
                    </el-card>
                    <el-card
                      shadow="never"
                      class="wa-run-monitor-surface wa-run-monitor-card wa-run-monitor-card--log"
                    >
                      <template #header>
                        <div class="wa-run-monitor-log-toolbar">
                          <span class="wa-run-monitor-log-toolbar-title">
                            <el-icon class="wa-run-monitor-log-toolbar-icon"><Monitor /></el-icon>
                            执行日志
                          </span>
                          <el-button size="small" class="wa-run-monitor-btn-ghost" @click="copyWebResultLog">
                            <el-icon class="el-icon--left"><DocumentCopy /></el-icon>
                            复制
                          </el-button>
                        </div>
                      </template>
                      <ul class="wa-run-monitor-log-list">
                        <li v-if="run_type !== '执行结束'" class="wa-run-monitor-log-pending">
                          <span class="wa-run-monitor-log-dot" aria-hidden="true" />
                          执行日志获取中…
                        </li>
                        <li
                          v-for="(log, index) in web_result_log"
                          :key="index"
                          class="wa-run-monitor-log-line"
                          :class="logLineClass(log)"
                        >
                          <template v-for="(seg, si) in parseLogLineForDisplay(log)" :key="`${index}-${si}`">
                            <span :class="seg.cls">{{ seg.text }}</span>
                          </template>
                        </li>
                      </ul>
                    </el-card>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
          <div class="wa-run-monitor-footer">
            <el-button class="wa-run-monitor-btn-ghost" @click="runMonitorDrawerVisible = false">关闭</el-button>
          </div>
        </div>
      </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { DocumentCopy, Monitor, HomeFilled, Folder, ChromeFilled, Delete, Check, Close } from '@element-plus/icons-vue'
import { logLineClass, parseLogLineForDisplay } from '@/utils/runMonitorLog'
import { useWebManagementApi } from '/@/api/v1/web_management'
import commonFunction from '/@/utils/commonFunction'
import { formatDateTime } from '/@/utils/formatTime'

const {
  web_group_list,
  web_menu,
  group_add_script,
  add_web_group,
  edit_web_group,
  del_web_group,
  run_web_script,
  get_web_result,
  get_web_result_log,
} = useWebManagementApi()

const { dateFormatYMDHMS } = commonFunction()
const fmtDateTime = (val: any) => formatDateTime(val)

const searchParams = ref({
  search: {
    name__icontains: '',
  },
  currentPage: 1,
  pageSize: 10,
})

const table_data = ref<any[]>([])
const total = ref(0)

// ---- 左侧模块树 ----
const menuTree = ref<any[]>([])
const selectedMenuNode = ref<any>(null)

const loadMenuTree = async () => {
  try {
    const res: any = await web_menu({})
    menuTree.value = ensureId(Array.isArray(res?.data) ? res.data : [])
  } catch { menuTree.value = [] }
}

const onMenuNodeClick = (data: any) => {
  nextTick(() => {
    selectedMenuNode.value = data
  })
}

// 根据选中节点过滤场景
const filteredTableData = computed(() => {
  if (!selectedMenuNode.value || selectedMenuNode.value.id == null) return table_data.value
  const nodeId = Number(selectedMenuNode.value.id)
  return table_data.value.filter((row: any) =>
    (row.script || []).some((s: any) => s != null && Number(s.id) === nodeId)
  )
})

const reset_search = () => {
  searchParams.value = {
    search: {
      name__icontains: '',
    },
    currentPage: 1,
    pageSize: 10,
  }
  group_list()
}

const group_list = async () => {
  const res: any = await web_group_list(searchParams.value)
  const content = res?.data?.content
  // 清洗数据，确保 script 数组里没有 null/undefined 元素
  table_data.value = (Array.isArray(content) ? content : []).map((row: any) => ({
    ...row,
    script: (row.script || []).filter(Boolean),
  }))
  total.value = typeof res?.data?.total === 'number' ? res.data.total : table_data.value.length
}

const element_select_list = ref<any[]>([])
const web_list = ref<any[]>([])

// 确保每个节点都有唯一 id，只保留必要字段，避免响应式属性污染
let _uid = 100000
const ensureId = (nodes: any[]): any[] => {
  return (nodes || []).map((n: any) => {
    const node: any = {
      id: n.id != null ? n.id : (_uid++),
      name: n.name || '',
      type: n.type,
    }
    if (n.children && n.children.length) {
      node.children = ensureId(n.children)
    }
    return node
  })
}

const element_select = async () => {
  const res: any = await web_menu({})
  element_select_list.value = ensureId(Array.isArray(res?.data) ? res.data : [])
}

const add_web = async () => {
  if (!web_list.value.length) {
    return
  }
  const res: any = await group_add_script({
    web_list: web_list.value,
  })
  add_form.value.script = [...(add_form.value.script || []), ...(res.data || [])]
  web_list.value = []
}

const del_web = (data: any) => {
  add_form.value.script = (add_form.value.script || []).filter(
    (item: any) => (item.id != null ? item.id !== data.id : item.name !== data.name)
  )
  addedScriptIds.value = new Set((add_form.value.script || []).map((s: any) => Number(s.id)))
}

// ---- 新增/编辑脚本弹窗 ----
const scriptDialogVisible = ref(false)
const pickerTreeRef = ref<any>(null)
const pickerKeyword = ref('')
const pickedNodes = ref<any[]>([])

watch(pickerKeyword, (v) => pickerTreeRef.value?.filter(v))
const filterPickerNode = (val: string, data: any) => !val || data.name?.includes(val)

// pickerTreeData：静态，不依赖 add_form.script，避免 el-tree 重渲染触发多次 node-click
const pickerTreeData = computed(() => {
  // 递归提取：每个非脚本节点附带其下所有脚本节点（_flatChildren）
  const flatScripts = (nodes: any[], depth = 1): any[] => {
    const result: any[] = []
    for (const n of nodes) {
      if (n.type === 2) {
        result.push({ ...n, _depth: depth })
      } else if (n.children && n.children.length) {
        result.push(...flatScripts(n.children, depth + 1))
      }
    }
    return result
  }
  return element_select_list.value.map((n: any) => ({
    id: n.id,
    name: n.name,
    type: n.type,
    _depth: 0,
    _flatChildren: n.type === 2
      ? [] // 顶层就是脚本，直接在父级处理
      : flatScripts(n.children || [], 1),
    _isSelf: n.type === 2, // 顶层脚本节点
  }))
})

// 用独立的 Set 追踪已添加的脚本 id，不触发 el-tree 重渲染
const addedScriptIds = ref<Set<number>>(new Set())

const onPickerNodeClick = (data: any) => {
  if (data.type !== 2) return
  const id = Number(data.id)
  if (addedScriptIds.value.has(id)) return
  addedScriptIds.value = new Set([...addedScriptIds.value, id])
  add_form.value.script = [
    ...(add_form.value.script || []),
    { id: data.id, name: data.name, type: data.type },
  ]
}

// 判断是否已添加（供 slot 使用，但 slot 里用 addedScriptIds 而不是 add_form.script）
const isScriptAdded = (data: any) => addedScriptIds.value.has(Number(data.id))

const onPickerCheckChange = (data: any, checked: boolean) => {
  if (!checked) {
    pickedNodes.value = pickedNodes.value.filter((n: any) => n.id !== data.id)
    return
  }
  if (data.type === 2 && data.id != null && !pickedNodes.value.find((n: any) => n.id === data.id)) {
    pickedNodes.value.push(data)
  }
}

const addPickedScripts = () => {
  const existing = new Set((add_form.value.script || []).map((s: any) => String(s.id ?? s.name)))
  const toAdd = pickedNodes.value
    .filter((n: any) => !existing.has(String(n.id ?? n.name)))
    .map((n: any) => ({ id: n.id, name: n.name, type: n.type })) // 只保留必要字段，避免 children 等复杂嵌套
  add_form.value.script = [...(add_form.value.script || []), ...toAdd]
  pickedNodes.value = []
  // nodes cleared via onPickerCheckChange
}

const resetScriptForm = () => {
  add_form.value = { name: '', script: [], description: '' }
  pickedNodes.value = []
  pickerKeyword.value = ''
  addedScriptIds.value = new Set()
}

const submitScriptForm = async () => {
  if (!add_form.value.name?.trim()) { ElMessage.warning('请输入脚本名称'); return }
  try {
    if (add_form.value.id) {
      const res: any = await edit_web_group(add_form.value)
      ElMessage.success(res?.message || '修改成功')
    } else {
      const res: any = await add_web_group(add_form.value)
      ElMessage.success(res?.message || '新增成功')
    }
    scriptDialogVisible.value = false
    await group_list()
  } catch (e: any) { ElMessage.error(e?.message || '操作失败') }
}

const add_koiDialogRef = ref<any>(null)
const edit_koiDialogRef = ref<any>(null)

const add_form = ref<any>({
  name: '',
  script: [],
  description: '',
})

const defaultProps = {
  children: 'children',
  label: 'name',
}

const title = ref('')

const Add = async () => {
  await element_select()
  title.value = '新增脚本'
  add_form.value = { name: '', script: [], description: '' }
  addedScriptIds.value = new Set()
  scriptDialogVisible.value = true
}

const add_confirm = async () => {}
const add_cancel = () => {}

const on_menu_allowDrop = (_moveNode: any, inNode: any, type: any) => {
  if (inNode.data.type === 2) return type !== 'inner'
  return type
}

const Edit = async (row: any) => {
  title.value = `编辑脚本：${row.name}`
  const cleanScript = (row.script || []).filter(Boolean).map((s: any) => ({
    id: s.id, name: s.name, type: s.type,
  }))
  add_form.value = { ...row, script: cleanScript }
  addedScriptIds.value = new Set(cleanScript.map((s: any) => Number(s.id)))
  await element_select()
  scriptDialogVisible.value = true
}

const edit_confirm = async () => {}
const edit_cancel = () => {}

const Delete = async (row: any) => {
  try {
    await del_web_group({ id: row.id })
    ElMessage.success('删除成功')
    await group_list()
  } catch (e: any) {
    ElMessage.error(e?.message || '删除失败')
  }
}

// 运行相关
const run_script_form = ref<any>({
  task_name: '',
  browser: [],
  script: [],
  width: 1920,
  height: 1080,
  browser_type: 1,
})

const browser_list = ref([
  { name: 'Chrome', value: 1 },
  { name: 'Firefox', value: 2 },
  { name: 'Edge', value: 3 },
  { name: 'Safari', value: 4 },
])

const run_browsers = ref<any[]>([])
const run_browser_active = ref<any>('')
const runMonitorDrawerVisible = ref(false)
const result_id = ref<string>('')

const onRunMonitorDrawerClosed = () => {
  stopPolling()
}

const user = ref<any>(null)
const web_result = ref<any[]>([])
const web_result_log = ref<any[]>([])
const run_type = ref<string>('')
const run_count = ref<number>(0)
const run_fail = ref<number>(0)
const start_time = ref<string>('')
const end_time = ref<string>('')

const runDialogVisible = ref(false)

const run_script = (row: any) => {
  title.value = `运行：${row.name}`
  run_script_form.value.script = row.script || []
  run_script_form.value.task_name = row.name || ''
  run_script_form.value.browser = [1]
  runDialogVisible.value = true
}

const run_koiDialogRef = ref<any>(null)

const run_script_confirm = async () => {
  if (!run_script_form.value.script.length) {
    ElMessage.error('请选择脚本')
    return
  }
  if (!run_script_form.value.task_name) {
    ElMessage.error('请输入任务名称')
    return
  }
  if (!run_script_form.value.browser.length) {
    ElMessage.error('请选择浏览器')
    return
  }

  run_browsers.value = []
  result_id.value = String(Date.now())
  run_script_form.value.result_id = result_id.value

  run_script_form.value.browser.forEach((b: any) => {
    const found = browser_list.value.find((it) => it.value === b)
    if (found) run_browsers.value.push(found)
  })

  run_browser_active.value = run_script_form.value.browser[0]
  title.value = `正在执行：${run_script_form.value.task_name}`
  runDialogVisible.value = false
  runMonitorDrawerVisible.value = true

  await startPolling()
  await run_web_script(run_script_form.value)
}

const run_script_cancel = () => {}

const interval = ref<any>(null)

const startPolling = async () => {
  if (interval.value) return
  interval.value = setInterval(get_run_result, 2000)
}

const stopPolling = () => {
  if (interval.value) {
    clearInterval(interval.value)
    interval.value = null
  }
}

const get_run_result = async () => {
  run_type.value = '正在执行'
  await get_result()
  await get_result_log()
}

const get_result = async () => {
  const res: any = await get_web_result({
    result_id: result_id.value,
    browser: run_browser_active.value,
  })
  web_result.value = res.data || []
  run_count.value = web_result.value.length
  if (web_result.value.length > 0) {
    start_time.value = web_result.value[web_result.value.length - 1].create_time
  }
  let fail = 0
  web_result.value.forEach((item: any) => {
    if (item.status === 0) {
      fail += 1
    }
    if (item.name === '执行结束') {
      stopPolling()
      run_count.value -= 1
      run_type.value = '执行结束'
      end_time.value = item.create_time
    }
  })
  run_fail.value = fail
}

const get_result_log = async () => {
  const res: any = await get_web_result_log({
    result_id: result_id.value,
    browser: run_browser_active.value,
  })
  web_result_log.value = res.data || []
}

const change_browser = async () => {
  await startPolling()
}

const getIcon = (status: any) => (status === 1 ? Check : Close)
const colors = (status: any) => (status === 1 ? '#0bbd87' : '#d70e0e')

const copyWebResultLog = async () => {
  const lines = web_result_log.value
  const text = Array.isArray(lines) ? lines.join('\n') : ''
  if (!text.trim()) {
    ElMessage.info('暂无日志可复制')
    return
  }
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.warning('复制失败，请手动选择日志文本')
  }
}

onMounted(() => {
  group_list()
  loadMenuTree()
  try {
    const raw = window.localStorage.getItem('user')
    if (raw) user.value = JSON.parse(raw)
  } catch {
    user.value = null
  }
})
</script>

<style lang="scss" scoped>
.web-group-page { height: calc(100vh - 120px); display: flex; flex-direction: column; padding: 10px; gap: 8px; overflow: hidden; }
.group-toolbar { display: flex; align-items: center; justify-content: space-between; background: var(--el-bg-color); border: 1px solid var(--el-border-color); border-radius: 8px; padding: 10px 14px; flex-shrink: 0; }
.toolbar-left { display: flex; align-items: center; gap: 8px; }
.toolbar-right { display: flex; align-items: center; gap: 8px; }
.group-body { flex: 1; min-height: 0; display: flex; gap: 8px; overflow: hidden; }
.module-panel { width: 220px; flex-shrink: 0; background: var(--el-bg-color); border: 1px solid var(--el-border-color); border-radius: 8px; display: flex; flex-direction: column; overflow: hidden; }
.module-panel-header { padding: 10px 14px; border-bottom: 1px solid var(--el-border-color); flex-shrink: 0; display: flex; align-items: center; justify-content: space-between; }
.module-panel-title { font-size: 13px; font-weight: 600; color: var(--el-text-color-primary); }
.module-panel-all { font-size: 12px; color: #409eff; cursor: pointer; padding: 2px 8px; border-radius: 10px; border: 1px solid #409eff; }
.module-panel-all--active { background: #409eff; color: #fff; }
.module-list { flex: 1; overflow-y: auto; padding: 4px 0; }
.picker-list { border: 1px solid var(--el-border-color); border-radius: 6px; padding: 4px; }
.mnode { display: flex; align-items: center; gap: 6px; padding: 6px 12px; cursor: pointer; border-radius: 4px; transition: background .15s; font-size: 12px; color: var(--el-text-color-primary); }
.mnode:hover { background: var(--el-fill-color-light); }
.mnode--active { background: var(--el-color-primary-light-9); color: #409eff; font-weight: 500; }
.mnode--child { padding-left: 24px; }
.mnode--leaf { padding-left: 36px; }
.mnode--clickable { cursor: pointer; }
.mnode--added { color: #67c23a; }
.mnode-icon { font-style: normal; font-size: 11px; flex-shrink: 0; width: 14px; text-align: center; }
.mnode-icon.micon-home::before { content: '⊙'; color: #409eff; }
.mnode-icon.micon-folder::before { content: '▶'; color: #f39c12; }
.mnode-icon.micon-script::before { content: '●'; color: #67c23a; }
.mnode-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.scene-panel { flex: 1; min-width: 0; background: var(--el-bg-color); border: 1px solid var(--el-border-color); border-radius: 8px; padding: 12px; overflow: auto; }

/* 新增/编辑弹窗 */
.script-dialog-body { display: flex; gap: 0; height: 480px; }
.script-picker { width: 260px; flex-shrink: 0; border-right: 1px solid var(--el-border-color); display: flex; flex-direction: column; overflow: hidden; padding-right: 12px; }
.picker-header { display: flex; align-items: center; margin-bottom: 10px; flex-shrink: 0; }
.picker-title { font-size: 13px; font-weight: 600; color: var(--el-text-color-primary); white-space: nowrap; }
.picker-tree { flex: 1; overflow-y: auto; border: 1px solid var(--el-border-color); border-radius: 6px; padding: 4px; }
.picker-node { display: flex; align-items: center; gap: 4px; width: 100%; padding-right: 4px; }
.picker-node-name { font-size: 12px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.picker-badge { flex-shrink: 0; font-size: 10px; border-radius: 3px; padding: 0 5px; line-height: 16px; font-weight: 600; }
.picker-badge--added { color: #67c23a; border: 1px solid #67c23a; }
.picker-badge--add { color: #409eff; border: 1px solid #409eff; cursor: pointer; }
.picker-icon { font-style: normal; font-size: 13px; flex-shrink: 0; }
.picker-icon.icon-home::before { content: '⊙'; color: #409eff; }
.picker-icon.icon-folder::before { content: '▶'; color: #f39c12; font-size: 10px; }
.picker-icon.icon-script::before { content: '●'; color: #67c23a; font-size: 10px; }
.script-arrow { width: 60px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
.script-config { flex: 1; min-width: 0; display: flex; flex-direction: column; padding-left: 12px; overflow: hidden; }
.selected-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; flex-shrink: 0; }
.selected-title { font-size: 13px; font-weight: 600; color: var(--el-text-color-primary); }
.selected-list { flex: 1; min-height: 0; overflow-y: auto; border: 1px solid var(--el-border-color); border-radius: 6px; padding: 6px; }
.selected-empty { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--el-text-color-placeholder); gap: 6px; font-size: 13px; }
.selected-item { display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: 6px; margin-bottom: 4px; background: var(--el-fill-color-light); border: 1px solid var(--el-border-color-lighter); transition: all .15s; }
.selected-item:hover { background: var(--el-color-primary-light-9); border-color: #409eff; }
.selected-index { width: 20px; height: 20px; border-radius: 50%; background: var(--el-color-primary-light-9); color: #409eff; font-size: 11px; font-weight: 600; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.selected-name { font-size: 12px; color: var(--el-text-color-primary); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.selected-del { font-size: 14px; color: var(--el-text-color-placeholder); cursor: pointer; flex-shrink: 0; }
.selected-del:hover { color: #ff4d4f; }
</style>

<style lang="scss">
@import '@/theme/modules/web-run-monitor.scss';
</style>

