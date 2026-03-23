<template>
  <div style="padding: 10px">
    <!-- 列表顶部栏：对齐 api_script 列表风格 -->
    <el-card class="box-card">
      <div class="script-topbar">
        <div class="script-topbar-left">
          <span class="script-title">Web 自动化 - 场景管理</span>
        </div>
        <div class="script-topbar-right">
          <el-input
            v-model="searchParams.search.name__icontains"
            placeholder="模糊搜索"
            clearable
            style="width: 300px; margin-right: 10px"
            @keyup.enter="group_list"
          >
            <template #append>
              <el-button @click="group_list">搜索</el-button>
            </template>
          </el-input>
          <el-button type="danger" @click="reset_search">重置</el-button>
          <el-button type="primary" @click="Add">新增测试场景</el-button>
        </div>
      </div>
    </el-card>

    <el-card class="box-card mt-10px">
      <el-table :data="table_data" stripe>
        <el-table-column prop="id" label="ID" width="90" />
        <el-table-column prop="name" label="名称" />
        <el-table-column label="用例集">
          <template #default="{ row }">
            <el-popover placement="top" :width="300" trigger="hover">
              <div>
                <el-steps direction="vertical" :active="99">
                  <el-step v-for="step in row.script" :key="step.id" :title="step.name" />
                </el-steps>
              </div>
              <template #reference>
                <el-button type="primary" link>用例详情</el-button>
              </template>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" :show-overflow-tooltip="true" />
        <el-table-column prop="username" label="最后更新人" />
        <el-table-column prop="create_time" label="创建时间" :formatter="dateFormatYMDHMS" />
        <el-table-column prop="update_time" label="更新时间" :formatter="dateFormatYMDHMS" />
        <el-table-column label="操作" width="280">
          <template #default="{ row }">
            <el-button type="success" size="small" @click="run_script(row)">立即运行</el-button>
            <el-button type="warning" size="small" @click="Edit(row)">编辑</el-button>
            <el-button type="danger" size="small" @click="Delete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="searchParams.currentPage"
          v-model:page-size="searchParams.pageSize"
          v-show="total > 0"
          :page-sizes="[10, 20, 50]"
          :background="true"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="group_list"
          @current-change="group_list"
        />
      </div>
    </el-card>

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

      <!-- 运行配置弹窗（旧结构迁移过来，之前缺失导致“立即运行”无反应） -->
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

      <!-- 运行结果弹窗：沿用旧结构，简化为只展示时间线和日志 -->
      <KoiDialog
        ref="res_koiDialogRef"
        :title="title"
        :height="680"
        :width="1600"
        :footer-hidden="true"
      >
        <template #content>
          <div style="width: 100%">
            <el-tabs
              tab-position="left"
              v-model="run_browser_active"
              class="demo-tabs"
              @tab-click="change_browser"
            >
              <el-tab-pane v-for="(item, index) in run_browsers" :key="index" :name="item.value">
                <template #label>
                  <span>{{ item.name }}</span>
                </template>
                <div style="width: 100%">
                  <div style="width: 100%; padding-block-end: 10px">
                    <KoiCard style="height: 80px">
                      <div>
                        <el-descriptions :column="5">
                          <el-descriptions-item label="执行状态：">
                            <el-tag type="success" v-if="run_type === '正在执行'">{{ run_type }}</el-tag>
                            <el-tag type="danger" v-else-if="run_type === '执行结束'">{{ run_type }}</el-tag>
                          </el-descriptions-item>
                          <el-descriptions-item label="浏览器：">{{ item.name }}</el-descriptions-item>
                          <el-descriptions-item label="执行人：">{{ user?.username }}</el-descriptions-item>
                          <el-descriptions-item label="开始时间：">{{ fmtDateTime(start_time) }}</el-descriptions-item>
                          <el-descriptions-item label="结束时间：">{{ fmtDateTime(end_time) }}</el-descriptions-item>
                          <el-descriptions-item label="已执行：">{{ run_count }}</el-descriptions-item>
                          <el-descriptions-item label="通过：">{{ run_count - run_fail }}</el-descriptions-item>
                          <el-descriptions-item label="失败：">{{ run_fail }}</el-descriptions-item>
                        </el-descriptions>
                      </div>
                    </KoiCard>
                  </div>
                  <div style="width: 100%">
                    <KoiCard style="width: 30%; float: left; height: 560px; overflow-y: auto">
                      <div>
                        <el-timeline style="width: 80%">
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
                            <KoiCard :style="get_colors(res.status)">
                              <span>{{ res.name }}</span>
                              <span>{{ '结果：' + res.log }}</span>
                            </KoiCard>
                          </el-timeline-item>
                        </el-timeline>
                      </div>
                    </KoiCard>
                    <KoiCard style="width: 66%; float: right; height: 560px; overflow-y: auto">
                      <div>
                        <li
                          v-if="run_type !== '执行结束'"
                          style="margin-bottom: 7px; color: #0bbd87"
                        >
                          执行日志获取中...
                        </li>
                        <li
                          v-for="(log, index) in web_result_log"
                          :key="index"
                          :style="get_log_style(log)"
                        >
                          {{ log }}
                        </li>
                      </div>
                    </KoiCard>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </template>
      </KoiDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import KoiCard from '/@/components/koi/KoiCard.vue'
import KoiDialog from '/@/components/koi/KoiDialog.vue'
import {
  web_group_list,
  web_menu,
  group_add_script,
  add_web_group,
  edit_web_group,
  del_web_group,
  run_web_script,
  get_web_result,
  get_web_result_log,
} from '/@/api/v1/web_management'
import commonFunction from '/@/utils/commonFunction'
import { formatDateTime } from '/@/utils/formatTime'

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
  // 后端返回：{ code, message, data: { content: [], total: number } }
  // 与旧架构 l-vue-ui 保持一致的解包方式
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
const res_koiDialogRef = ref<InstanceType<typeof KoiDialog> | null>(null)

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
const result_id = ref<string>('')

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
  res_koiDialogRef.value?.koiOpen()

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
const get_colors = (status: any) => (status === 1 ? 'color: #0bbd87' : 'color: #d70e0e')
const get_log_style = (data: string) => (data.includes('失败') ? 'color: #d70e0e' : '')

onMounted(() => {
  group_list()
  try {
    const raw = window.localStorage.getItem('user')
    if (raw) user.value = JSON.parse(raw)
  } catch {
    user.value = null
  }
})
</script>

<style lang="scss" scoped>
.box-card {
  margin-bottom: 10px;
}

.mt-10px {
  margin-top: 10px;
}

.script-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.script-topbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.script-topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.script-title {
  font-size: 16px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  padding-right: 2px;
}

.el-tree-node__content {
  margin-bottom: 5px;
  height: 28px;
}
</style>

