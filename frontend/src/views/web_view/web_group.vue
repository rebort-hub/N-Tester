<template>
  <div class="web-group-page">
    <!-- 顶部工具栏 -->
    <div class="group-toolbar">
      <div class="toolbar-left">
        <el-input v-model="searchParams.search.name__icontains" placeholder="搜索场景名称" clearable style="width:200px" @keyup.enter="group_list" />
        <el-button type="primary" icon="Search" @click="group_list">搜索</el-button>
        <el-button icon="Refresh" @click="reset_search">重置</el-button>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" @click="Add">新增测试场景</el-button>
      </div>
    </div>

    <!-- 主体：左侧模块树 + 右侧场景列表 -->
    <div class="group-body">
      <!-- 左侧模块树 -->
      <div class="module-panel">
        <div class="module-panel-header">
          <span class="module-panel-title">脚本模块</span>
        </div>
        <el-tree
          :data="menuTree"
          :props="{ label: 'name', children: 'children' }"
          node-key="id"
          highlight-current
          class="module-tree"
          @node-click="onMenuNodeClick"
        >
          <template #default="{ data }">
            <span class="module-node">
              <el-icon v-if="data.type===0" style="color:#409eff;margin-right:4px"><HomeFilled /></el-icon>
              <el-icon v-else-if="data.type===1" style="color:#f39c12;margin-right:4px"><Folder /></el-icon>
              <el-icon v-else style="color:#67c23a;margin-right:4px"><ChromeFilled /></el-icon>
              <span class="module-node-name">{{ data.name }}</span>
            </span>
          </template>
        </el-tree>
      </div>

      <!-- 右侧场景列表 -->
      <div class="scene-panel">
        <el-table :data="filteredTableData" border stripe empty-text="暂无场景" style="width:100%">
          <el-table-column prop="id" label="ID" width="70" align="center" />
          <el-table-column prop="name" label="场景名称" min-width="160" show-overflow-tooltip />
          <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">{{ row.description || '-' }}</template>
          </el-table-column>
          <el-table-column label="脚本数" width="80" align="center">
            <template #default="{ row }">
              <el-badge :value="row.script?.length || 0" type="primary" />
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

      <!-- 新增场景 -->
      <KoiDialog
        ref="add_koiDialogRef"
        :title="title"
        :height="620"
        @koi-confirm="add_confirm"
        @koi-cancel="add_cancel"
      >
        <template #content>
          <el-form :model="add_form" label-width="80px">
            <el-form-item label="名称：">
              <el-input v-model="add_form.name" placeholder="请输入名称" clearable />
            </el-form-item>
            <el-form-item label="用例集：">
              <el-cascader
                v-model="web_list"
                placeholder="请选择脚本"
                style="width: 400px; padding-right: 10px"
                :options="element_select_list"
                filterable
                collapse-tags
                :props="{
                  value: 'id',
                  label: 'name',
                  children: 'children',
                  multiple: true
                }"
              >
                <template #default="{ node, data }">
                  <el-icon v-if="data.type === 0" style="padding-right: 5px">
                    <HomeFilled />
                  </el-icon>
                  <el-icon v-else-if="data.type === 1" style="padding-right: 5px">
                    <Folder />
                  </el-icon>
                  <el-icon v-else-if="data.type === 2" style="padding-right: 5px">
                    <ChromeFilled />
                  </el-icon>
                  <span>{{ data.name }}</span>
                  <span v-if="!node.isLeaf">({{ data.children.length }})</span>
                </template>
              </el-cascader>
              <el-button type="primary" icon="plus" plain @click="add_web">确认添加</el-button>
            </el-form-item>
            <el-form-item>
              <div
                style="border: 1px solid #e4e7ed; width: 400px; height: 400px; overflow-y: auto; padding: 10px"
              >
                <el-tree
                  ref="treeRef"
                  :data="add_form.script"
                  :props="defaultProps"
                  default-expand-all
                  :allow-drop="on_menu_allowDrop"
                  draggable
                >
                  <template #default="{ node, data }">
                    <span class="custom-tree-node" style="width: 100%">
                      <div
                        style="border: 1px solid #3e7be5; border-radius: 5px; width: 93%; color: #3e7be5"
                      >
                        <span>
                          <el-icon style="padding-right: 3px; padding-left: 5px">
                            <ChromeFilled />
                          </el-icon>
                          {{ node.label }}
                          <el-button
                            type="text"
                            style="float: right"
                            plain
                            icon="Delete"
                            @click="del_web(data)"
                          />
                        </span>
                      </div>
                    </span>
                  </template>
                </el-tree>
              </div>
            </el-form-item>
            <el-form-item label="描述：">
              <el-input v-model="add_form.description" placeholder="请输入描述" />
            </el-form-item>
          </el-form>
        </template>
      </KoiDialog>

      <!-- 编辑场景 -->
      <KoiDialog
        ref="edit_koiDialogRef"
        :title="title"
        :height="620"
        @koi-confirm="edit_confirm"
        @koi-cancel="edit_cancel"
      >
        <template #content>
          <el-form :model="add_form" label-width="80px">
            <el-form-item label="名称：">
              <el-input v-model="add_form.name" placeholder="请输入名称" clearable />
            </el-form-item>
            <el-form-item label="用例集：">
              <el-cascader
                v-model="web_list"
                placeholder="请选择脚本"
                style="width: 400px; padding-right: 10px"
                :options="element_select_list"
                filterable
                collapse-tags
                :props="{
                  value: 'id',
                  label: 'name',
                  children: 'children',
                  multiple: true
                }"
              >
                <template #default="{ node, data }">
                  <el-icon v-if="data.type === 0" style="padding-right: 5px">
                    <HomeFilled />
                  </el-icon>
                  <el-icon v-else-if="data.type === 1" style="padding-right: 5px">
                    <Folder />
                  </el-icon>
                  <el-icon v-else-if="data.type === 2" style="padding-right: 5px">
                    <ChromeFilled />
                  </el-icon>
                  <span>{{ data.name }}</span>
                  <span v-if="!node.isLeaf">({{ data.children.length }})</span>
                </template>
              </el-cascader>
              <el-button type="primary" icon="plus" plain @click="add_web">确认添加</el-button>
            </el-form-item>
            <el-form-item>
              <div
                style="border: 1px solid #e4e7ed; width: 400px; height: 400px; overflow-y: auto; padding: 10px"
              >
                <el-tree
                  ref="treeRef"
                  :data="add_form.script"
                  :props="defaultProps"
                  default-expand-all
                  :allow-drop="on_menu_allowDrop"
                  draggable
                >
                  <template #default="{ node, data }">
                    <span class="custom-tree-node" style="width: 100%">
                      <div
                        style="border: 1px solid #3e7be5; border-radius: 5px; width: 93%; color: #3e7be5"
                      >
                        <span>
                          <el-icon style="padding-right: 3px; padding-left: 5px">
                            <ChromeFilled />
                          </el-icon>
                          {{ node.label }}
                          <el-button
                            type="text"
                            style="float: right"
                            plain
                            icon="Delete"
                            @click="del_web(data)"
                          />
                        </span>
                      </div>
                    </span>
                  </template>
                </el-tree>
              </div>
            </el-form-item>
            <el-form-item label="描述：">
              <el-input v-model="add_form.description" placeholder="请输入描述" />
            </el-form-item>
          </el-form>
        </template>
      </KoiDialog>

      <KoiDialog
        ref="run_koiDialogRef"
        :title="title"
        :height="220"
        @koi-confirm="run_script_confirm"
        @koi-cancel="run_script_cancel"
      >
        <template #content>
          <el-form>
            <el-form-item label="名称：">
              <el-input v-model="run_script_form.task_name" placeholder="请输入名称" clearable />
            </el-form-item>
            <el-form-item label="执行模式：">
              <el-radio-group v-model="run_script_form.browser_type">
                <el-radio :value="1">有界面</el-radio>
                <el-radio :value="2">无界面</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="分辨率(宽*高)：">
              <div>
                <el-input-number
                  v-model="run_script_form.width"
                  controls-position="right"
                  min="800"
                  label="宽度"
                />
                <el-input-number
                  v-model="run_script_form.height"
                  style="padding-left: 10px"
                  controls-position="right"
                  min="800"
                  label="高度"
                />
              </div>
            </el-form-item>
            <el-form-item label="选择浏览器：">
              <el-select v-model="run_script_form.browser" multiple style="width: 60%">
                <el-option
                  v-for="item in browser_list"
                  :key="item.value"
                  :label="item.name"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-form>
        </template>
      </KoiDialog>


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
            <p class="wa-run-monitor-drawer-sub">场景步骤与日志，执行结束后可继续查看或关闭抽屉</p>
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
                            场景执行日志
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
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { DocumentCopy, Monitor, HomeFilled, Folder, ChromeFilled } from '@element-plus/icons-vue'
import KoiDialog from '/@/components/koi/KoiDialog.vue'
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
    menuTree.value = Array.isArray(res?.data) ? res.data : []
  } catch { menuTree.value = [] }
}

const onMenuNodeClick = (data: any) => {
  selectedMenuNode.value = data
}

// 根据选中节点过滤场景（场景的 script 里包含该节点 id 的）
const filteredTableData = computed(() => {
  if (!selectedMenuNode.value) return table_data.value
  const nodeId = selectedMenuNode.value.id
  return table_data.value.filter((row: any) =>
    (row.script || []).some((s: any) => s.id === nodeId || s.pid === nodeId || s.menu_id === nodeId)
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
  table_data.value = Array.isArray(content) ? content : []
  total.value = typeof res?.data?.total === 'number' ? res.data.total : table_data.value.length
}

const element_select_list = ref<any[]>([])
const web_list = ref<any[]>([])

const element_select = async () => {
  const res: any = await web_menu({})
  element_select_list.value = res.data
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
  add_form.value.script = (add_form.value.script || []).filter((item: any) => item.id !== data.id)
}

const add_koiDialogRef = ref<InstanceType<typeof KoiDialog> | null>(null)
const edit_koiDialogRef = ref<InstanceType<typeof KoiDialog> | null>(null)

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
  title.value = '新增测试场景'
  add_form.value = {
    name: '',
    script: [],
    description: '',
  }
  add_koiDialogRef.value?.koiOpen()
}

const add_confirm = async () => {
  const res: any = await add_web_group(add_form.value)
  await group_list()
  add_koiDialogRef.value?.koiQuickClose(res.message)
}

const add_cancel = () => {
  add_koiDialogRef.value?.koiClose()
}

const on_menu_allowDrop = (_moveNode: any, inNode: any, type: any) => {
  if (inNode.data.type === 2) {
    return type !== 'inner'
  }
  return type
}

const Edit = async (row: any) => {
  title.value = `编辑测试场景：${row.name}`
  add_form.value = { ...row }
  await element_select()
  edit_koiDialogRef.value?.koiOpen()
}

const edit_confirm = async () => {
  const res: any = await edit_web_group(add_form.value)
  await group_list()
  edit_koiDialogRef.value?.koiQuickClose(res.message)
}

const edit_cancel = () => {
  edit_koiDialogRef.value?.koiClose()
}

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

const run_script = (row: any) => {
  title.value = '请配置调试信息'
  run_script_form.value.script = row.script || []
  run_script_form.value.task_name = row.name || ''
  run_script_form.value.browser = [1]
  run_koiDialogRef.value?.koiOpen()
}

const run_koiDialogRef = ref<InstanceType<typeof KoiDialog> | null>(null)

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
    if (found) {
      run_browsers.value.push(found)
    }
  })

  run_browser_active.value = run_script_form.value.browser[0]
  title.value = `正在执行：${run_script_form.value.task_name}`
  run_koiDialogRef.value?.koiQuickClose('')
  runMonitorDrawerVisible.value = true

  await startPolling()
  await run_web_script(run_script_form.value)
}

const run_script_cancel = () => {
  run_koiDialogRef.value?.koiQuickClose('取消调试')
}

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

const getIcon = (status: any) => (status === 1 ? 'Check' : 'Close')
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
.module-panel-header { padding: 10px 14px; border-bottom: 1px solid var(--el-border-color); flex-shrink: 0; }
.module-panel-title { font-size: 13px; font-weight: 600; color: var(--el-text-color-primary); }
.module-tree { flex: 1; overflow-y: auto; padding: 4px 0; }
.module-node { display: flex; align-items: center; min-width: 0; }
.module-node-name { font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.scene-panel { flex: 1; min-width: 0; background: var(--el-bg-color); border: 1px solid var(--el-border-color); border-radius: 8px; padding: 12px; overflow: auto; }
</style>

<style lang="scss">
@import '@/theme/modules/web-run-monitor.scss';
</style>

