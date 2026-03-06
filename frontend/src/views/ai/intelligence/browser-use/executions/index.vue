<template>
  <div class="ai-browser-executions-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>AI执行记录</span>
          <el-button type="primary" @click="handleExport">
            <el-icon><Download /></el-icon>
            导出记录
          </el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="项目">
          <el-select 
            v-model="queryForm.ui_project_id" 
            placeholder="请选择项目" 
            clearable
            style="width: 200px"
          >
            <el-option
              v-for="project in projectList"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="用例ID">
          <el-input 
            v-model="queryForm.case_id" 
            placeholder="请输入用例ID" 
            clearable
            style="width: 150px"
          />
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" placeholder="请选择状态" clearable style="width: 150px">
            <el-option label="待执行" value="pending" />
            <el-option label="执行中" value="running" />
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
            <el-option label="已停止" value="stopped" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 300px"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="tableData" v-loading="loading" border stripe style="width: 100%" :fit="true">
        <el-table-column prop="id" label="执行ID" min-width="80" show-overflow-tooltip />
        <el-table-column prop="ai_case_id" label="用例ID" min-width="80" />
        <el-table-column prop="case_name" label="用例名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="execution_mode" label="执行模式" min-width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ row.execution_mode === 'headless' ? '无头' : '有头' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" min-width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" min-width="150">
          <template #default="{ row }">
            <el-progress 
              :percentage="row.progress" 
              :status="getProgressStatus(row.status)"
              :stroke-width="12"
            />
            <div style="font-size: 12px; color: #909399; margin-top: 4px;">
              {{ row.current_step }}/{{ row.total_steps }} 步骤
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="时长" min-width="100" align="center">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        <el-table-column label="统计" min-width="150">
          <template #default="{ row }">
            <div style="font-size: 12px;">
              <div>通过: <span style="color: #67c23a;">{{ row.steps_passed }}</span></div>
              <div>失败: <span style="color: #f56c6c;">{{ row.steps_failed }}</span></div>
              <div>Token: {{ row.tokens_used || 0 }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="end_time" label="结束时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.end_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleViewDetail(row)">详情</el-button>
            <el-button type="info" size="small" @click="handleViewLog(row)">日志</el-button>
            <el-button type="success" size="small" @click="handleViewScreenshots(row)">截图</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="queryForm.page"
        v-model:page-size="queryForm.page_size"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="getList"
        @current-change="getList"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog 
      v-model="detailDialogVisible" 
      title="执行详情"
      width="900px"
      :close-on-click-modal="false"
    >
      <el-descriptions :column="2" border v-if="currentExecution">
        <el-descriptions-item label="执行ID" :span="2">
          <el-text type="primary" style="font-family: monospace;">{{ currentExecution.id }}</el-text>
        </el-descriptions-item>
        <el-descriptions-item label="用例ID">
          {{ currentExecution.ai_case_id }}
        </el-descriptions-item>
        <el-descriptions-item label="用例名称">
          {{ currentExecution.case_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="执行模式">
          <el-tag size="small">
            {{ currentExecution.execution_mode === 'headless' ? '无头执行' : '有头执行' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentExecution.status)">
            {{ getStatusLabel(currentExecution.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="进度" :span="2">
          <el-progress 
            :percentage="calculateProgress(currentExecution)" 
            :status="getProgressStatus(currentExecution.status)"
          />
        </el-descriptions-item>
        <el-descriptions-item label="开始时间">
          {{ formatDateTime(currentExecution.start_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="结束时间">
          {{ formatDateTime(currentExecution.end_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="执行时长">
          {{ formatDuration(currentExecution.duration) }}
        </el-descriptions-item>
        <el-descriptions-item label="AI模型配置">
          <div v-if="currentExecution.llm_config_name">
            <div>{{ currentExecution.llm_config_name }}</div>
            <div style="font-size: 12px; color: #909399;">{{ currentExecution.llm_model_name || '-' }}</div>
          </div>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="步骤统计" :span="2">
          总步骤: {{ currentExecution.planned_tasks?.length || 0 }} | 
          已完成: {{ currentExecution.steps_completed?.length || 0 }} | 
          通过: <span style="color: #67c23a;">{{ countStepsByStatus(currentExecution, 'success') }}</span> | 
          失败: <span style="color: #f56c6c;">{{ countStepsByStatus(currentExecution, 'failed') }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="API调用次数">
          {{ currentExecution.api_calls || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="Token使用量">
          <div>
            <div>总计: {{ currentExecution.total_tokens || 0 }}</div>
            <div style="font-size: 12px; color: #909399;">
              输入: {{ currentExecution.prompt_tokens || 0 }} | 
              输出: {{ currentExecution.completion_tokens || 0 }}
            </div>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="错误信息" :span="2" v-if="currentExecution.error_message">
          <el-alert type="error" :closable="false">
            {{ currentExecution.error_message }}
          </el-alert>
        </el-descriptions-item>
      </el-descriptions>
      
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleViewLog(currentExecution)">查看日志</el-button>
        <el-button type="success" @click="handleViewScreenshots(currentExecution)">查看截图</el-button>
      </template>
    </el-dialog>

    <!-- 日志对话框 -->
    <el-dialog 
      v-model="logDialogVisible" 
      title="执行日志"
      width="1000px"
      :close-on-click-modal="false"
    >
      <el-tabs v-model="activeLogTab">
        <el-tab-pane label="执行日志" name="execution">
          <div class="terminal-log">
            <pre>{{ executionLog }}</pre>
          </div>
        </el-tab-pane>
        <el-tab-pane label="AI思考过程" name="thinking">
          <div class="terminal-log">
            <pre>{{ thinkingLog }}</pre>
          </div>
        </el-tab-pane>
        <el-tab-pane label="执行动作" name="actions">
          <el-timeline v-if="actionsList.length > 0">
            <el-timeline-item
              v-for="(action, index) in actionsList"
              :key="index"
              :timestamp="action.timestamp"
              placement="top"
            >
              <el-card>
                <h4>{{ action.action_type }}</h4>
                <p>{{ action.description }}</p>
                <el-tag v-if="action.status" :type="action.status === 'success' ? 'success' : 'danger'" size="small">
                  {{ action.status }}
                </el-tag>
              </el-card>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无执行动作" />
        </el-tab-pane>
      </el-tabs>
      
      <template #footer>
        <el-button @click="logDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleDownloadLog">下载日志</el-button>
      </template>
    </el-dialog>

    <!-- 截图对话框 -->
    <el-dialog 
      v-model="screenshotDialogVisible" 
      title="执行截图"
      width="1200px"
      :close-on-click-modal="false"
    >
      <div v-if="screenshotsList.length > 0" class="screenshots-container">
        <el-carousel :interval="0" arrow="always" height="600px">
          <el-carousel-item v-for="(screenshot, index) in screenshotsList" :key="index">
            <div class="screenshot-item">
              <div class="screenshot-info">
                <span>步骤 {{ screenshot.step_num }}: {{ screenshot.description }}</span>
                <span class="screenshot-time">{{ screenshot.timestamp }}</span>
              </div>
              <el-image 
                :src="screenshot.url" 
                fit="contain"
                style="width: 100%; height: 550px;"
                :preview-src-list="screenshotsList.map(s => s.url)"
                :initial-index="index"
              />
            </div>
          </el-carousel-item>
        </el-carousel>
      </div>
      <el-empty v-else description="暂无截图" />
      
      <template #footer>
        <el-button @click="screenshotDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleDownloadScreenshots">下载所有截图</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
// 导入旧的执行记录API
import { aiExecutionRecordApi } from '/@/api/v1/ai_intelligence'
// 导入项目API
import { getProjectList } from '/@/api/v1/project'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const dateRange = ref([])

const projectList = ref([])

const queryForm = reactive({
  ui_project_id: null,
  case_id: null,
  status: null,
  start_date: null,
  end_date: null,
  page: 1,
  page_size: 20
})

// 详情对话框
const detailDialogVisible = ref(false)
const currentExecution = ref<any>(null)

// 日志对话框
const logDialogVisible = ref(false)
const activeLogTab = ref('execution')
const executionLog = ref('')
const thinkingLog = ref('')
const actionsList = ref<any[]>([])

// 截图对话框
const screenshotDialogVisible = ref(false)
const screenshotsList = ref<any[]>([])

const getList = async () => {
  loading.value = true
  try {
    console.log('开始获取执行记录列表...', queryForm)
    
    // 使用旧的执行记录API
    const params: any = {
      page: queryForm.page,
      page_size: queryForm.page_size
    }
    if (queryForm.ui_project_id) params.ui_project_id = queryForm.ui_project_id
    if (queryForm.case_id) params.ai_case_id = queryForm.case_id
    if (queryForm.status) params.status = queryForm.status
    if (queryForm.start_date) {
      // 格式化日期为 YYYY-MM-DD
      const date = new Date(queryForm.start_date)
      params.start_date = date.toISOString().split('T')[0]
    }
    if (queryForm.end_date) {
      // 格式化日期为 YYYY-MM-DD
      const date = new Date(queryForm.end_date)
      params.end_date = date.toISOString().split('T')[0]
    }
    
    console.log('查询参数:', params)
    
    const res = await aiExecutionRecordApi.list(params)
    console.log('执行记录API响应:', res)
    
    if (res.code === 200) {
      // 适配数据格式 - 支持新旧两种格式
      let records = []
      let totalCount = 0
      
      if (res.data.items) {
        // 新格式：{ items: [], total: 0 }
        records = res.data.items
        totalCount = res.data.total
      } else if (Array.isArray(res.data)) {
        // 旧格式：直接是数组
        records = res.data
        totalCount = records.length
      } else if (res.data.results) {
        // 另一种格式：{ results: [] }
        records = res.data.results
        totalCount = records.length
      }
      
      tableData.value = records.map((item: any) => ({
        ...item,
        execution_id: item.id,
        case_id: item.ai_case_id,  // 修正：使用ai_case_id
        // 计算进度和步骤统计
        progress: item.steps_completed ? 
          Math.round((item.steps_completed.length / (item.planned_tasks?.length || 1)) * 100) : 0,
        current_step: item.steps_completed?.length || 0,
        total_steps: item.planned_tasks?.length || 0,
        steps_passed: item.steps_completed?.filter((s: any) => s.status === 'success').length || 0,
        steps_failed: item.steps_completed?.filter((s: any) => s.status === 'failed').length || 0,
        tokens_used: item.total_tokens || 0
      }))
      total.value = totalCount
      
      console.log('处理后的数据:', {
        count: tableData.value.length,
        total: total.value
      })
    }
  } catch (error: any) {
    console.error('获取列表失败:', error)
    ElMessage.error(error.message || '获取列表失败')
  } finally {
    loading.value = false
  }
}

const handleQuery = () => {
  if (dateRange.value && dateRange.value.length === 2) {
    queryForm.start_date = dateRange.value[0]
    queryForm.end_date = dateRange.value[1]
  } else {
    queryForm.start_date = null
    queryForm.end_date = null
  }
  console.log('执行查询，参数:', queryForm)
  queryForm.page = 1
  getList()
}

const handleReset = () => {
  Object.assign(queryForm, {
    ui_project_id: null,
    case_id: null,
    status: null,
    start_date: null,
    end_date: null,
    page: 1,
    page_size: 20
  })
  dateRange.value = []
  getList()
}

const handleViewDetail = async (row: any) => {
  try {
    const res = await aiExecutionRecordApi.get(row.id)
    if (res.code === 200) {
      currentExecution.value = res.data
      detailDialogVisible.value = true
    }
  } catch (error) {
    ElMessage.error('获取详情失败')
  }
}

const handleViewLog = async (row: any) => {
  try {
    const res = await aiExecutionRecordApi.get(row.id)
    if (res.code === 200) {
      executionLog.value = res.data.logs || '暂无执行日志'
      thinkingLog.value = res.data.ai_thinking_log || '暂无AI思考日志'
      
      // 解析执行动作
      if (row.actions_taken && Array.isArray(row.actions_taken)) {
        actionsList.value = row.actions_taken
      } else {
        actionsList.value = []
      }
      
      logDialogVisible.value = true
    }
  } catch (error) {
    ElMessage.error('获取日志失败')
  }
}

const handleViewScreenshots = async (row: any) => {
  try {
    const res = await aiExecutionRecordApi.get(row.id)
    if (res.code === 200) {
      // 旧API中GIF路径存储在gif_path字段
      if (res.data.gif_path) {
        screenshotsList.value = [{
          url: `/api/static/upload/${res.data.gif_path}`,
          step: 'GIF回放',
          description: '执行过程录制',
          timestamp: res.data.end_time
        }]
      } else {
        screenshotsList.value = []
      }
      screenshotDialogVisible.value = true
    }
  } catch (error) {
    ElMessage.error('获取截图失败')
  }
}

const handleDelete = (row: any) => {
  ElMessageBox.confirm('确定要删除该执行记录吗？此操作将永久删除数据，无法恢复！', '警告', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      // 使用正确的API - 直接删除执行记录
      await aiExecutionRecordApi.delete(row.id)
      ElMessage.success('删除成功')
      getList()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

const handleExport = () => {
  ElMessage.info('导出功能开发中')
}

const handleDownloadLog = () => {
  // 下载日志文件
  const logContent = `执行日志:\n${executionLog.value}\n\nAI思考过程:\n${thinkingLog.value}`
  const blob = new Blob([logContent], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `execution_log_${Date.now()}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

const handleDownloadScreenshots = () => {
  ElMessage.info('批量下载截图功能开发中')
}

const getStatusType = (status: string) => {
  const map: any = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger',
    stopped: 'info'
  }
  return map[status] || ''
}

const getStatusLabel = (status: string) => {
  const map: any = {
    pending: '待执行',
    running: '执行中',
    success: '成功',
    failed: '失败',
    stopped: '已停止'
  }
  return map[status] || status
}

const getProgressStatus = (status: string) => {
  if (status === 'success') return 'success'
  if (status === 'failed') return 'exception'
  return undefined
}

const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const formatDuration = (seconds?: number) => {
  if (!seconds) return '-'
  if (seconds < 60) return `${seconds}秒`
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}分${secs}秒`
}

const calculateProgress = (execution: any) => {
  if (!execution) return 0
  const completed = execution.steps_completed?.length || 0
  const total = execution.planned_tasks?.length || 1
  return Math.round((completed / total) * 100)
}

const countStepsByStatus = (execution: any, status: string) => {
  if (!execution || !execution.steps_completed) return 0
  return execution.steps_completed.filter((s: any) => s.status === status).length
}

// 获取项目列表
const getProjects = async () => {
  try {
    const res = await getProjectList({ page: 1, page_size: 100 })
    if (res.code === 200) {
      projectList.value = res.data.list || res.data.items || res.data || []
    }
  } catch (error) {
    console.error('获取项目列表失败:', error)
  }
}

onMounted(() => {
  getProjects()
  getList()
})
</script>

<style scoped lang="scss">
.ai-browser-executions-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.query-form {
  margin-bottom: 20px;
}

.screenshots-container {
  .screenshot-item {
    display: flex;
    flex-direction: column;
    height: 100%;
    
    .screenshot-info {
      display: flex;
      justify-content: space-between;
      padding: 10px;
      background: #f5f7fa;
      border-radius: 4px;
      margin-bottom: 10px;
      
      .screenshot-time {
        color: #909399;
        font-size: 12px;
      }
    }
  }
}

// 黑色终端风格日志
.terminal-log {
  background-color: #1e1e1e;
  border-radius: 4px;
  padding: 16px;
  max-height: 500px;
  overflow-y: auto;
  
  pre {
    margin: 0;
    color: #d4d4d4;
    font-family: 'Courier New', Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
    font-size: 13px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-wrap: break-word;
  }
  
  // 滚动条样式
  &::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: #2d2d2d;
    border-radius: 4px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #555;
    border-radius: 4px;
    
    &:hover {
      background: #666;
    }
  }
}
</style>
