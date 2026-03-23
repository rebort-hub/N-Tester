<template>
  <div v-loading="loading" style="padding: 10px">
    <!-- 上半部分：统计信息 -->
    <el-card shadow="hover">
      <div style="display: flex; gap: 10px; width: 100%">
        <div style="width: 34%">
          <el-card shadow="never">
            <el-descriptions border :column="2">
              <el-descriptions-item label="任务名称">{{ res_form.task_name }}</el-descriptions-item>
              <el-descriptions-item label="执行人">{{ res_form.username }}</el-descriptions-item>
              <el-descriptions-item label="开始时间">{{ formatTime(res_form.start_time) }}</el-descriptions-item>
              <el-descriptions-item label="结束时间">{{ formatTime(res_form.end_time) }}</el-descriptions-item>
              <el-descriptions-item label="执行总数">{{ res_form.total }}</el-descriptions-item>
              <el-descriptions-item label="通过率">
                <el-tag type="success">{{ res_form.percent }}%</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </div>
        <div style="flex: 1; display: flex; gap: 10px; align-items: stretch">
          <div class="stat-card stat-card--blue">
            <div class="stat-label">脚本总数</div>
            <div class="stat-value">{{ res_form.total }}</div>
          </div>
          <div class="stat-card stat-card--green">
            <div class="stat-label">通过率</div>
            <div class="stat-value">{{ res_form.percent }}%</div>
          </div>
          <div class="stat-card stat-card--teal">
            <div class="stat-label">通过数</div>
            <div class="stat-value">{{ res_form.total - res_form.total_fail }}</div>
          </div>
          <div class="stat-card stat-card--red">
            <div class="stat-label">失败数</div>
            <div class="stat-value">{{ res_form.total_fail }}</div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 下半部分：脚本列表 + 详情 -->
    <el-card shadow="hover" style="margin-top: 10px">
      <div style="display: flex; gap: 10px; width: 100%">
        <!-- 左侧脚本列表 -->
        <div style="width: 180px; flex-shrink: 0">
          <el-card shadow="never" style="height: 750px; overflow-y: auto">
            <el-tabs v-model="script_active" @tab-click="handleTabClick">
              <el-tab-pane label="全部" name="all">
                <div v-for="(script, index) in script_list" :key="script.id" style="padding-bottom: 8px">
                  <div :style="get_card_style(script.status)" :class="{ highlight: selectedIndex === index }" class="script-item">
                    <el-button class="script-btn" link
                      :icon="script.status === 0 ? 'CircleClose' : 'CircleCheck'"
                      :style="{ color: script.status === 0 ? '#f3050d' : '#0bbd87' }"
                      @click="script_click(script, index)">{{ script.name }}</el-button>
                  </div>
                </div>
              </el-tab-pane>
              <el-tab-pane label="通过" name="pass">
                <div v-for="(script, index) in script_list" :key="script.id" style="padding-bottom: 8px">
                  <div v-if="script.status === 1" :style="get_card_style(script.status)" :class="{ highlight: selectedIndex === index }" class="script-item">
                    <el-button class="script-btn" link icon="CircleCheck" :style="{ color: '#0bbd87' }" @click="script_click(script, index)">{{ script.name }}</el-button>
                  </div>
                </div>
              </el-tab-pane>
              <el-tab-pane label="失败" name="fail">
                <div v-for="(script, index) in script_list" :key="script.id" style="padding-bottom: 8px">
                  <div v-if="script.status === 0" :style="get_card_style(script.status)" :class="{ highlight: selectedIndex === index }" class="script-item">
                    <el-button class="script-btn" link icon="CircleClose" :style="{ color: '#f3050d' }" @click="script_click(script, index)">{{ script.name }}</el-button>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </div>

        <!-- 右侧浏览器 + 详情 -->
        <div style="flex: 1; min-width: 0">
          <el-card shadow="never" style="height: 750px; overflow-y: auto">
            <el-tabs tab-position="left" v-model="browser_active" class="demo-tabs" @tab-click="change_browser">
              <el-tab-pane v-for="(item, index) in browser_list" :key="index" :name="item.value">
                <template #label><span>{{ item.name }}</span></template>
                <div style="width: 100%">
                  <!-- 执行信息栏 -->
                  <div class="info-bar">
                    <span class="info-item"><span class="info-label">执行状态</span><el-tag type="danger" size="small">执行结束</el-tag></span>
                    <span class="info-item"><span class="info-label">浏览器</span>{{ item.name }}</span>
                    <span class="info-item"><span class="info-label">执行人</span>{{ res_form.username }}</span>
                    <span class="info-item"><span class="info-label">开始时间</span>{{ start_time }}</span>
                    <span class="info-item"><span class="info-label">结束时间</span>{{ end_time }}</span>
                    <span class="info-item"><span class="info-label">总数</span>{{ run_total }}</span>
                    <span class="info-item"><span class="info-label">通过</span><span style="color:#0bbd87;font-weight:600">{{ run_pass }}</span></span>
                    <span class="info-item"><span class="info-label">失败</span><span style="color:#f3050d;font-weight:600">{{ run_fail }}</span></span>
                    <span class="info-item" v-if="trace">
                      <el-button type="primary" size="small" plain @click="download_report">⬇ trace.zip</el-button>
                      <el-button type="warning" size="small" @click="view_trace" style="margin-left:4px">🔍 分析页面</el-button>
                    </span>
                    <span class="info-item" v-if="pre_video">
                      <el-button type="success" size="small" @click="view_video">▶ 查看视频</el-button>
                    </span>
                  </div>

                  <!-- 步骤 + 日志 -->
                  <div style="display: flex; gap: 10px; margin-top: 10px">
                    <!-- 步骤时间线 -->
                    <div class="panel-box" style="width: 340px; flex-shrink: 0; height: 600px; overflow-y: auto">
                      <div v-if="!web_result.length" style="color: #999; padding: 8px 0">暂无执行过程</div>
                      <el-timeline>
                        <el-timeline-item
                          v-for="(res, index) in web_result" :key="index"
                          center :icon="getIcon(res.status)" type="primary"
                          :color="colors(res.status)" size="large"
                          :timestamp="'执行时间：' + res.create_time" placement="top"
                        >
                          <div :class="res.status === 1 ? 'step-card step-card--pass' : 'step-card step-card--fail'">
                            <div class="step-name">{{ res.name }}</div>
                            <div class="step-log">{{ res.log }}</div>
                            <div class="step-actions">
                              <el-popover v-if="Object.keys(res.assert_result || {}).length" placement="right" :width="500" trigger="click">
                                <template #reference>
                                  <el-button class="action-btn action-btn--purple" size="small" icon="Search">断言详情</el-button>
                                </template>
                                <div v-for="(item, i) in res.assert_result" :key="i">
                                  <span :style="get_log_style(item.result)">{{ '断言结果：' + item.result }}</span>
                                  <el-button v-if="item.img" icon="Picture" link style="float:right" @click="pre_view(item.img)">查看详情</el-button>
                                </div>
                              </el-popover>
                              <el-button v-if="res.before_img" class="action-btn action-btn--blue" size="small" icon="Picture" @click="pre_view(res.before_img)">执行前</el-button>
                              <el-button v-if="res.after_img" class="action-btn action-btn--orange" size="small" icon="Picture" @click="pre_view(res.after_img)">执行后</el-button>
                            </div>
                          </div>
                        </el-timeline-item>
                      </el-timeline>
                      <el-image-viewer v-if="img_show" :url-list="pre_img" @close="close_img" />
                    </div>

                    <!-- 日志 -->
                    <div class="panel-box" style="flex: 1; height: 600px; overflow-y: auto">
                      <div v-if="!web_result_log.length" style="color: #999">暂无执行日志</div>
                      <div v-for="(log, index) in web_result_log" :key="index" class="log-line" :style="get_log_style(log)">{{ log }}</div>
                    </div>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { get_web_result_report, get_web_result_detail } from '/@/api/v1/web_management'
import { getBaseApiUrl } from '/@/utils/config'

// 媒体文件：后端挂载了 /media 路由，直接拼接后端地址
const mediaUrl = (path: string) => path ? `${getBaseApiUrl()}${path}` : ''

// 时间格式化：2026-03-14T21:35:24 → 2026-03-14 21:35:24
const formatTime = (t: string) => t ? t.replace('T', ' ') : ''

const loading = ref(false)
const result_id = ref<string>('')
const menu_id = ref<any>(null)
const res_form = ref<any>({})
const script_active = ref('all')
const selectedIndex = ref(0)
const script_list = ref<any[]>([])
const browser_show = ref([
  { name: 'Chrome', value: 1 },
  { name: 'Firefox', value: 2 },
  { name: 'Edge', value: 3 },
  { name: 'Safari', value: 4 },
])
const browser_list = ref<any[]>([])
const browser_active = ref<any>(null)
const web_result_log = ref<any[]>([])
const img_show = ref(false)
const pre_img = ref<string[]>([])
const web_result = ref<any[]>([])
const start_time = ref('')
const end_time = ref('')
const run_pass = ref(0)
const run_fail = ref(0)
const run_total = ref(0)
const pre_video = ref('')
const trace = ref('')

const get_result_report = async () => {
  loading.value = true
  try {
    const route = useRoute()
    result_id.value = String((route.query.result_id || route.query.resultId || '') as any)

    // 没有 result_id 时直接结束，避免一直 loading
    if (!result_id.value) {
      res_form.value = {}
      script_list.value = []
      browser_list.value = []
      browser_active.value = null
      menu_id.value = null
      web_result.value = []
      web_result_log.value = []
      start_time.value = ''
      end_time.value = ''
      run_pass.value = 0
      run_fail.value = 0
      run_total.value = 0
      pre_video.value = ''
      trace.value = ''
      return
    }

    const res: any = await get_web_result_report({ result_id: result_id.value })
    const data = res?.data || {}
    res_form.value = data

    // 后端找不到报告时会返回 {}，这里兜底避免脚本/浏览器索引报错导致页面卡住
    const scripts = Array.isArray(data.script_list) ? data.script_list : []
    const browsers = Array.isArray(data.browser_list) ? data.browser_list : []
    script_list.value = scripts
    await handle_browser(browsers)
    browser_active.value = browsers[0] ?? null
    menu_id.value = scripts[0]?.id ?? null

    if (browser_active.value != null && menu_id.value != null) {
      await get_result_detail()
    } else {
      web_result.value = []
      web_result_log.value = []
      start_time.value = ''
      end_time.value = ''
      run_pass.value = 0
      run_fail.value = 0
      run_total.value = 0
      pre_video.value = ''
      trace.value = ''
    }
  } finally {
    loading.value = false
  }
}

const get_result_detail = async () => {
  const res: any = await get_web_result_detail({
    result_id: result_id.value,
    browser: browser_active.value,
    menu_id: menu_id.value,
  })
  web_result.value = res.data.content
  web_result_log.value = res.data.log
  if (res.data.content.length) {
    start_time.value = res.data.content[res.data.content.length - 1].create_time
    end_time.value = res.data.content[0].create_time
  }
  run_pass.value = res.data.content.filter((i: any) => i.status === 1).length
  run_fail.value = res.data.content.filter((i: any) => i.status === 0).length
  run_total.value = run_pass.value + run_fail.value
  trace.value = res.data.trace
  pre_video.value = res.data.video
}

const script_click = async (script: any, index: number) => {
  selectedIndex.value = index
  menu_id.value = script.id
  await get_result_detail()
}

const handleTabClick = (tab: any) => {
  if (!res_form.value.script_list) return
  if (tab.props.name === 'all') script_list.value = res_form.value.script_list
  else if (tab.props.name === 'pass') script_list.value = res_form.value.script_list.filter((i: any) => i.status === 1)
  else if (tab.props.name === 'fail') script_list.value = res_form.value.script_list.filter((i: any) => i.status === 0)
}

const handle_browser = async (browsers: any[]) => {
  browser_list.value = []
  browsers.forEach((b: any) => {
    const match = browser_show.value.find((x) => x.value === b)
    if (match) browser_list.value.push(match)
  })
}

const change_browser = async (pane: any) => {
  browser_active.value = pane.props.name
  await get_result_detail()
}

const getIcon = (status: any) => (status === 1 ? 'Check' : 'Close')
const colors = (status: any) => (status === 1 ? '#0bbd87' : '#f3050d')
const get_card_style = (type: any) => type === 0 ? 'border-color: #f3050d' : 'border-color: #67c23ae0'
const get_log_style = (data: string) => (data.includes('失败') ? 'color: #f3050d' : '')

const view_video = () => { if (pre_video.value) window.open(mediaUrl(pre_video.value)) }
const pre_view = (img: string) => { pre_img.value = [mediaUrl(img)]; img_show.value = true }
const close_img = () => { img_show.value = false }
const download_report = () => { if (trace.value) window.open(mediaUrl(trace.value)); view_trace() }
const view_trace = () => { window.open('https://trace.playwright.dev/') }

onMounted(() => { get_result_report() })
</script>

<style scoped lang="scss">
/* 统计卡片 — 渐变色，深色模式下同样好看 */
.stat-card {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  border-radius: 8px; padding: 16px 10px; min-width: 0;
  .stat-label { font-size: 13px; color: rgba(255,255,255,0.85); margin-bottom: 8px; white-space: nowrap }
  .stat-value { font-size: 32px; font-weight: 700; color: #fff; line-height: 1 }
}
.stat-card--blue  { background: linear-gradient(135deg, #4096ff, #1677ff) }
.stat-card--green { background: linear-gradient(135deg, #52c41a, #389e0d) }
.stat-card--teal  { background: linear-gradient(135deg, #13c2c2, #08979c) }
.stat-card--red   { background: linear-gradient(135deg, #ff4d4f, #cf1322) }

/* 执行信息栏 — 用 el CSS 变量自动适配深色 */
.info-bar {
  display: flex; flex-wrap: wrap; gap: 6px 16px;
  align-items: center; padding: 10px 12px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
}
.info-item { display: flex; align-items: center; gap: 4px; white-space: nowrap; font-size: 13px; color: var(--el-text-color-primary) }
.info-label { color: var(--el-text-color-secondary); font-size: 12px; margin-right: 2px }

/* 步骤卡片 — 用 el CSS 变量自动适配深色 */
.step-card {
  border-radius: 6px; padding: 8px 10px; border-left: 3px solid;
  background: var(--el-bg-color);
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.step-card--pass { border-left-color: #0bbd87 }
.step-card--fail { border-left-color: #f3050d }
.step-name { font-size: 13px; font-weight: 600; margin-bottom: 4px; color: var(--el-text-color-primary) }
.step-log  { font-size: 12px; color: var(--el-text-color-secondary); margin-bottom: 6px; word-break: break-all }
.step-actions { display: flex; flex-wrap: wrap; gap: 4px }

/* 操作按钮 */
.action-btn { border-radius: 4px !important }
.action-btn--blue   { color: #1677ff !important; border-color: #1677ff !important }
.action-btn--orange { color: #fa8c16 !important; border-color: #fa8c16 !important }
.action-btn--purple { color: #722ed1 !important; border-color: #722ed1 !important }

/* 面板容器 — 用 el CSS 变量自动适配深色 */
.panel-box {
  border: 1px solid var(--el-border-color);
  border-radius: 6px; padding: 10px;
  background: var(--el-bg-color);
}

/* 脚本列表项 */
.script-item { border: 1px solid var(--el-border-color); padding: 4px 6px; border-radius: 6px }
.script-btn  { padding: 0 !important; width: 100%; justify-content: flex-start; white-space: normal; height: auto; line-height: 1.4 }

/* 日志行 */
.log-line { font-size: 12px; line-height: 1.8; padding: 1px 0; color: var(--el-text-color-primary) }

.highlight { background-color: rgba(182, 230, 239, 0.25) }
.demo-tabs :deep(.el-tabs__content) { overflow: visible }
</style>
