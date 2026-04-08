<template>
  <div class="browser-use-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>AI智能浏览器</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增用例
          </el-button>
        </div>
      </template>

      <!-- 筛选区域 -->
      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="UI项目">
          <el-select 
            v-model="queryForm.ui_project_id" 
            placeholder="请选择" 
            clearable
            style="width: 300px"
          >
            <el-option
              v-for="project in uiProjectList"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="name" label="用例名称" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="task_description" label="任务描述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="creation_date" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.creation_date) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="360" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="success" size="small" @click="handleExecute(row)">执行</el-button>
            <el-button type="warning" size="small" @click="handleViewLogs(row)">日志</el-button>
            <el-button type="info" size="small" @click="handleViewRecords(row)">记录</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="用例名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入用例名称" />
        </el-form-item>
        <el-form-item label="UI项目">
          <el-select v-model="formData.ui_project_id" placeholder="请选择UI项目" clearable style="width: 100%">
            <el-option
              v-for="project in uiProjectList"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述"
          />
        </el-form-item>
        <el-form-item label="任务描述" prop="task_description">
          <el-input
            v-model="formData.task_description"
            type="textarea"
            :rows="6"
            placeholder="请输入AI要执行的任务描述，例如：打开百度首页，搜索'测试'，点击第一个搜索结果"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 执行记录对话框 -->
    <el-dialog
      v-model="recordsDialogVisible"
      title="执行记录"
      width="900px"
    >
      <el-table :data="recordsList" border stripe v-loading="recordsLoading">
        <el-table-column prop="id" label="记录ID" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="90">
          <template #default="{ row }">
            {{ row.steps_completed?.length || 0 }} 步
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时(秒)" width="100">
          <template #default="{ row }">
            {{ row.duration ? row.duration.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" min-width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="end_time" label="结束时间" min-width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.end_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.gif_path"
              type="primary"
              size="small"
              @click="viewRecordGif(row)"
            >
              查看回放
            </el-button>
            <span v-else class="text-gray">无回放</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 执行监控对话框 -->
    <el-dialog
      v-model="monitorDialogVisible"
      title="AI执行监控"
      width="80%"
      :close-on-click-modal="false"
      @close="handleMonitorDialogClose"
    >
      <div class="execution-monitor">
        <!-- 状态信息 -->
        <el-descriptions :column="3" border>
          <el-descriptions-item label="用例名称">
            {{ currentMonitorCase?.name }}
          </el-descriptions-item>
          <el-descriptions-item label="执行状态">
            <el-tag :type="getMonitorStatusType()">
              {{ getMonitorStatusText() }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="执行进度">
            {{ monitorData.progress }} 步
          </el-descriptions-item>
          <el-descriptions-item label="执行耗时">
            {{ monitorData.duration ? monitorData.duration.toFixed(2) : 0 }}s
          </el-descriptions-item>
          <el-descriptions-item label="GIF录制" :span="2">
            <el-button
              v-if="monitorData.gif_path"
              type="primary"
              size="small"
              @click="handleViewGif"
            >
              查看回放
            </el-button>
            <span v-else-if="monitorData.status === 'failed'" class="text-gray">执行失败，无录制</span>
            <span v-else-if="monitorData.status === 'completed'" class="text-gray">执行完成，未生成GIF</span>
            <span v-else class="text-gray">执行完成后生成</span>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 错误信息 -->
        <el-alert
          v-if="monitorData.error_message"
          type="error"
          title="执行失败"
          :description="monitorData.error_message"
          :closable="false"
          show-icon
          style="margin-top: 15px;"
        />

        <!-- 执行日志 -->
        <el-divider>执行日志</el-divider>
        <el-scrollbar height="400px">
          <pre class="execution-logs">{{ monitorData.logs || '等待执行日志...' }}</pre>
        </el-scrollbar>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button 
            v-if="['completed', 'failed'].includes(monitorData.status)" 
            @click="handleMonitorDialogClose"
          >
            关闭
          </el-button>
          <el-button 
            v-else 
            type="warning" 
            @click="handleStopMonitoring"
          >
            停止监控
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- GIF回放对话框 -->
    <el-dialog
      v-model="gifDialogVisible"
      title="执行回放"
      width="70%"
    >
      <div class="gif-player">
        <img
          :src="currentGifUrl"
          alt="执行回放"
          style="width: 100%; border: 1px solid #ddd; border-radius: 4px;"
        />
      </div>
    </el-dialog>

    <!-- 执行日志对话框 - 参考TestHub实现 -->
    <el-dialog
      v-model="logsDialogVisible"
      title="执行日志"
      width="1200px"
      :close-on-click-modal="false"
      @close="stopLogsPolling"
    >
      <div v-loading="logsLoading">
        <!-- 执行记录列表 -->
        <el-table
          :data="executionLogs"
          border
          stripe
          style="width: 100%"
        >
          <el-table-column label="序号" width="80" align="center">
            <template #default="{ $index }">
              {{ $index + 1 }}
            </template>
          </el-table-column>
          <el-table-column prop="case_name" label="用例名称" min-width="200" show-overflow-tooltip />
          <el-table-column label="执行状态" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="耗时(秒)" width="120" align="center">
            <template #default="{ row }">
              {{ row.duration ? row.duration.toFixed(2) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="开始时间" width="180" align="center">
            <template #default="{ row }">
              {{ formatDateTime(row.start_time) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center" fixed="right">
            <template #default="{ row }">
              <el-button
                type="primary"
                size="small"
                @click="handleViewLogDetail(row)"
              >
                查看详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- 执行日志详情对话框 - 完全参考TestHub实现 -->
    <el-dialog
      v-model="logDetailDialogVisible"
      title="执行详情"
      width="900px"
      :close-on-click-modal="false"
    >
      <div v-if="currentLogDetail" class="record-detail">
        <!-- 基本信息 -->
        <div class="detail-item">
          <span class="label">用例名称:</span>
          <span class="value">{{ currentLogDetail.case_name }}</span>
        </div>

        <div class="detail-item">
          <span class="label">执行状态:</span>
          <el-tag :type="getStatusType(currentLogDetail.status)">
            {{ getStatusText(currentLogDetail.status) }}
          </el-tag>
        </div>

        <div class="detail-item">
          <span class="label">开始时间:</span>
          <span>{{ formatDateTime(currentLogDetail.start_time) }}</span>
        </div>

        <div class="detail-item">
          <span class="label">结束时间:</span>
          <span>{{ currentLogDetail.end_time ? formatDateTime(currentLogDetail.end_time) : '-' }}</span>
        </div>

        <div class="detail-item">
          <span class="label">执行耗时:</span>
          <span>{{ currentLogDetail.duration ? currentLogDetail.duration.toFixed(2) + ' 秒' : '未知' }}</span>
        </div>

        <!-- 任务描述 -->
        <div v-if="currentLogDetail.task_description" class="detail-item mt-15">
          <span class="label">任务描述:</span>
        </div>
        <div v-if="currentLogDetail.task_description" class="task-description-container">
          <div class="task-description-content">{{ currentLogDetail.task_description }}</div>
        </div>

        <!-- 错误信息 -->
        <div v-if="currentLogDetail.error_message" class="detail-item mt-15">
          <span class="label">错误信息:</span>
        </div>
        <div v-if="currentLogDetail.error_message" class="error-container">
          <pre class="error-text">{{ currentLogDetail.error_message }}</pre>
        </div>

        <!-- 执行日志 -->
        <div class="detail-item mt-15">
          <span class="label">执行日志:</span>
        </div>
        <div class="log-container">
          <pre>{{ currentLogDetail.logs || '暂无日志' }}</pre>
        </div>

        <!-- GIF回放 -->
        <div v-if="currentLogDetail.gif_path" class="detail-item mt-15">
          <span class="label">执行回放:</span>
        </div>
        <div v-if="currentLogDetail.gif_path" class="gif-container">
          <el-button
            type="primary"
            size="small"
            @click="handleViewGifFromLog(currentLogDetail.gif_path)"
          >
            查看GIF回放
          </el-button>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="logDetailDialogVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { aiCaseApi, aiExecutionRecordApi } from '/@/api/v1/ai_intelligence'
import { useUiAutomationApi } from '/@/api/v1/ui_automation'
import type { AICase, AICaseForm, AIExecutionRecord } from '/@/types/ai_intelligence'

const { uiProjectApi } = useUiAutomationApi()

// 查询表单
const queryForm = reactive({
  ui_project_id: null as number | null
})

// UI项目列表
const uiProjectList = ref<any[]>([])

// 表格数据
const tableData = ref<AICase[]>([])
const loading = ref(false)

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('新增用例')
const formRef = ref<FormInstance>()
const submitLoading = ref(false)

// 表单数据
const formData = reactive<AICaseForm>({
  ui_project_id: undefined,
  name: '',
  description: '',
  task_description: ''
})

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入用例名称', trigger: 'blur' }],
  task_description: [{ required: true, message: '请输入任务描述', trigger: 'blur' }]
}

// 当前编辑的ID
let currentEditId: number | null = null

// 执行记录
const recordsDialogVisible = ref(false)
const recordsList = ref<AIExecutionRecord[]>([])
const recordsLoading = ref(false)

// 时间格式化函数
const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  } catch (error) {
    return dateStr
  }
}

// 获取UI项目列表
const getUIProjectList = async () => {
  try {
    const res = await uiProjectApi.list({ page: 1, page_size: 1000 })
    uiProjectList.value = res.data?.items || []
  } catch (error) {
    console.error('获取UI项目列表失败', error)
  }
}

// 获取列表
const getList = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (queryForm.ui_project_id) params.ui_project_id = queryForm.ui_project_id
    
    const res = await aiCaseApi.list(params)
    tableData.value = res.data || []
  } catch (error) {
    ElMessage.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

// 查询
const handleQuery = () => {
  getList()
}

// 重置
const handleReset = () => {
  queryForm.ui_project_id = null
  getList()
}

// 新增
const handleAdd = () => {
  currentEditId = null
  dialogTitle.value = '新增用例'
  resetForm()
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row: AICase) => {
  currentEditId = row.id!
  dialogTitle.value = '编辑用例'
  Object.assign(formData, {
    ui_project_id: row.ui_project_id,
    name: row.name,
    description: row.description,
    task_description: row.task_description
  })
  dialogVisible.value = true
}

// 执行
const handleExecute = async (row: AICase) => {
  ElMessageBox.confirm(
    '确定要执行该AI用例吗？执行过程中AI将自动操作浏览器完成任务。',
    '执行确认',
    {
      confirmButtonText: '执行',
      cancelButtonText: '取消',
      type: 'info'
    }
  ).then(async () => {
    try {
      const res = await aiCaseApi.execute(row.id!, false) // false表示显示浏览器窗口
      if (res.code === 200) {
        ElMessage.success('AI用例执行已启动')
        // 打开监控对话框
        showExecutionMonitor(row)
      }
    } catch (error: any) {
      ElMessage.error(error.message || '启动执行失败')
    }
  })
}

// 执行监控对话框
const monitorDialogVisible = ref(false)
const currentMonitorCase = ref<AICase | null>(null)
const monitorData = reactive({
  status: 'running',
  progress: 0,
  logs: '',
  duration: 0,
  error_message: '',
  gif_path: ''
})
let monitorTimer: number | null = null

// 显示执行监控
const showExecutionMonitor = (caseData: AICase) => {
  currentMonitorCase.value = caseData
  monitorData.status = 'running'
  monitorData.progress = 0
  monitorData.logs = '正在启动AI执行...\n'
  monitorData.duration = 0
  monitorData.error_message = ''
  monitorData.gif_path = ''
  monitorDialogVisible.value = true
  
  // 开始轮询
  startMonitorPolling()
}

// 开始轮询执行状态
const startMonitorPolling = () => {
  // 用于跟踪是否已经提示过完成/失败消息
  let hasNotified = false
  
  // 先等待2秒，让后台任务启动
  setTimeout(() => {
    monitorTimer = window.setInterval(async () => {
      try {
        // 获取最新的执行记录
        const res = await aiExecutionRecordApi.list({
          ai_case_id: currentMonitorCase.value?.id,
          page: 1,
          page_size: 1
        })
        
        console.log('轮询获取执行记录:', res)
        
        // 兼容不同的API返回格式
        const records = Array.isArray(res.data) ? res.data : (res.data?.results || [])
        
        if (records && records.length > 0) {
          const latestRecord = records[0]
          
          console.log('最新执行记录:', latestRecord)
          console.log('日志内容:', latestRecord.logs)
          console.log('日志类型:', typeof latestRecord.logs)
          console.log('日志长度:', latestRecord.logs ? latestRecord.logs.length : 0)
          
          // 确保日志是字符串类型
          const logContent = latestRecord.logs || '执行中...'
          // 使用 Object.assign 强制触发响应式更新
          Object.assign(monitorData, {
            status: latestRecord.status,
            progress: latestRecord.steps_completed ? latestRecord.steps_completed.length : 0,
            logs: String(logContent),
            duration: latestRecord.duration || 0,
            error_message: latestRecord.error_message || '',
            gif_path: latestRecord.gif_path || ''
          })
          
          console.log('monitorData.logs已更新:', monitorData.logs)
          console.log('monitorData.logs长度:', monitorData.logs.length)
          
          console.log('执行状态更新:', {
            status: latestRecord.status,
            progress: monitorData.progress,
            logsLength: monitorData.logs.length,
            error: latestRecord.error_message
          })
          
          // 如果完成或失败，停止轮询但不关闭对话框
          if (['completed', 'failed'].includes(latestRecord.status)) {
            stopMonitorPolling()
            
            // 只提示一次
            if (!hasNotified) {
              hasNotified = true
              if (latestRecord.status === 'completed') {
                ElMessage.success('AI用例执行完成')
              } else if (latestRecord.status === 'failed') {
                ElMessage.error('AI用例执行失败')
              }
            }
            
            // 刷新列表
            getList()
          }
        } else {
          // 如果没有找到执行记录，可能还在启动中
          console.log('等待执行记录创建...')
        }
      } catch (error: any) {
        console.error('轮询执行状态失败', error)
        // 静默处理错误，继续轮询
      }
    }, 2000) // 每2秒轮询一次
  }, 2000)
}

// 停止轮询
const stopMonitorPolling = () => {
  if (monitorTimer) {
    clearInterval(monitorTimer)
    monitorTimer = null
  }
}

// 关闭监控对话框时停止轮询
const handleMonitorDialogClose = () => {
  stopMonitorPolling()
  monitorDialogVisible.value = false
  currentMonitorCase.value = null
}

// 停止监控（用户主动停止）
const handleStopMonitoring = () => {
  ElMessageBox.confirm(
    '确定要停止监控吗？执行任务将继续在后台运行。',
    '停止监控',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    handleMonitorDialogClose()
    ElMessage.info('已停止监控，任务继续在后台执行')
  }).catch(() => {
    // 用户取消，不做任何操作
    console.log('用户取消停止监控')
  })
}

// 获取状态标签类型
const getMonitorStatusType = () => {
  const map: Record<string, any> = {
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[monitorData.status] || 'info'
}

// 获取状态文本
const getMonitorStatusText = () => {
  const map: Record<string, string> = {
    running: '执行中',
    completed: '已完成',
    failed: '失败'
  }
  return map[monitorData.status] || monitorData.status
}

// 查看GIF回放
const handleViewGif = () => {
  if (!monitorData.gif_path) {
    ElMessage.warning('暂无GIF录制')
    return
  }
  
  // 打开新窗口查看GIF
  const gifUrl = `/api/static/upload/${monitorData.gif_path}`
  window.open(gifUrl, '_blank')
}

// 查看执行记录
const handleViewRecords = async (row: AICase) => {
  recordsLoading.value = true
  try {
    const res = await aiExecutionRecordApi.list({ ai_case_id: row.id })
    console.log('执行记录响应:', res)
    recordsList.value = res.data || []
    recordsDialogVisible.value = true
  } catch (error) {
    console.error('获取执行记录失败:', error)
    ElMessage.error('获取执行记录失败')
  } finally {
    recordsLoading.value = false
  }
}

// 删除
const handleDelete = (row: AICase) => {
  ElMessageBox.confirm('确定要删除该用例吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await aiCaseApi.delete(row.id!)
      ElMessage.success('删除成功')
      getList()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitLoading.value = true
    try {
      if (currentEditId) {
        await aiCaseApi.update(currentEditId, formData)
        ElMessage.success('更新成功')
      } else {
        await aiCaseApi.create(formData)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      getList()
    } catch (error) {
      ElMessage.error(currentEditId ? '更新失败' : '创建失败')
    } finally {
      submitLoading.value = false
    }
  })
}

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    ui_project_id: undefined,
    name: '',
    description: '',
    task_description: ''
  })
  formRef.value?.clearValidate()
}

// 辅助函数
const getStatusLabel = (status?: string) => {
  const map: Record<string, string> = {
    pending: '待执行',
    running: '执行中',
    completed: '已完成',
    success: '成功',
    failed: '失败'
  }
  return map[status || 'pending'] || status
}

const getStatusTagType = (status?: string) => {
  const map: Record<string, any> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    success: 'success',
    failed: 'danger'
  }
  return map[status || 'pending'] || ''
}

// 执行日志对话框使用的状态函数
const getStatusType = (status?: string) => {
  const map: Record<string, any> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    success: 'success',
    failed: 'danger'
  }
  return map[status || 'pending'] || 'info'
}

const getStatusText = (status?: string) => {
  const map: Record<string, string> = {
    pending: '待执行',
    running: '执行中',
    completed: '执行成功',
    success: '执行成功',
    failed: '执行失败'
  }
  return map[status || 'pending'] || status
}

// GIF对话框
const gifDialogVisible = ref(false)
const currentGifUrl = ref('')

// 从执行记录查看GIF
const viewRecordGif = (record: AIExecutionRecord) => {
  if (!record.gif_path) {
    ElMessage.warning('该记录没有GIF录制')
    return
  }
  currentGifUrl.value = `/api/static/upload/${record.gif_path}`
  gifDialogVisible.value = true
}

// 执行日志对话框
const logsDialogVisible = ref(false)
const executionLogs = ref<AIExecutionRecord[]>([])
const logsLoading = ref(false)
let logsPollingTimer: number | null = null
const currentCaseIdForLogs = ref<number | null>(null)

// 执行日志详情对话框
const logDetailDialogVisible = ref(false)
const currentLogDetail = ref<AIExecutionRecord | null>(null)

// 查看执行日志
const handleViewLogs = async (row: AICase) => {
  try {
    logsLoading.value = true
    currentCaseIdForLogs.value = row.id
    
    // 获取该用例的所有执行记录
    const res = await aiExecutionRecordApi.list({
      ai_case_id: row.id,
      page: 1,
      page_size: 100
    })
    
    console.log('执行记录API响应:', res)
    
    if (res.code === 200) {
      // 确保数据是数组
      const records = Array.isArray(res.data) ? res.data : (res.data?.results || [])
      executionLogs.value = records
      
      console.log('执行记录列表:', executionLogs.value)
      
      // 检查是否有正在执行的任务
      const runningRecord = executionLogs.value.find(
        record => record.status === 'running' || record.status === 'pending'
      )
      
      if (runningRecord) {
        // 如果有正在执行的任务，显示实时监控
        console.log('发现正在执行的任务，显示实时监控')
        logsLoading.value = false
        showExecutionMonitor(row)
      } else {
        // 否则显示历史记录列表
        console.log('没有正在执行的任务，显示历史记录列表')
        logsDialogVisible.value = true
        logsLoading.value = false
        
        // 开始轮询（如果有running/pending任务）
        startLogsPolling()
      }
    } else {
      ElMessage.error(res.message || '获取执行日志失败')
      logsLoading.value = false
    }
  } catch (error) {
    console.error('获取执行日志失败', error)
    ElMessage.error('获取执行日志失败')
    logsLoading.value = false
  }
}

// 开始轮询执行日志列表 - 参考TestHub实现
const startLogsPolling = () => {
  // 清除之前的定时器
  if (logsPollingTimer) {
    clearInterval(logsPollingTimer)
  }
  
  logsPollingTimer = window.setInterval(async () => {
    // 只有当对话框打开且有running/pending任务时才轮询
    if (logsDialogVisible.value && currentCaseIdForLogs.value) {
      const hasActiveTasks = executionLogs.value.some(
        r => r.status === 'running' || r.status === 'pending'
      )
      
      if (hasActiveTasks) {
        // 静默刷新，不显示loading
        try {
          const res = await aiExecutionRecordApi.list({
            ai_case_id: currentCaseIdForLogs.value,
            page: 1,
            page_size: 100
          })
          
          if (res.code === 200) {
            const records = Array.isArray(res.data) ? res.data : (res.data?.results || [])
            executionLogs.value = records
            console.log('轮询更新执行记录:', records.length, '条')
          }
        } catch (error) {
          console.error('轮询执行日志失败', error)
        }
      } else {
        // 没有活动任务，停止轮询
        stopLogsPolling()
      }
    }
  }, 5000) // 每5秒轮询一次，参考TestHub
}

// 停止轮询
const stopLogsPolling = () => {
  if (logsPollingTimer) {
    clearInterval(logsPollingTimer)
    logsPollingTimer = null
    console.log('停止轮询执行日志')
  }
}

// 查看日志详情
const handleViewLogDetail = async (row: AIExecutionRecord) => {
  try {
    console.log('查看日志详情，记录ID:', row.id)
    
    // 获取详细信息
    const res = await aiExecutionRecordApi.get(row.id)
    
    console.log('日志详情API响应:', res)
    
    if (res.code === 200) {
      console.log('日志详情数据:', res.data)
      console.log('日志内容:', res.data.logs)
      console.log('错误信息:', res.data.error_message)
      console.log('任务描述:', res.data.task_description)
      
      currentLogDetail.value = res.data
      logDetailDialogVisible.value = true
    } else {
      ElMessage.error(res.message || '获取日志详情失败')
    }
  } catch (error) {
    console.error('获取日志详情失败', error)
    ElMessage.error('获取日志详情失败')
  }
}

// 从日志详情查看GIF
const handleViewGifFromLog = (gifPath: string) => {
  if (!gifPath) {
    ElMessage.warning('没有GIF录制')
    return
  }
  currentGifUrl.value = `/api/static/upload/${gifPath}`
  gifDialogVisible.value = true
}

onMounted(() => {
  getUIProjectList()
  getList()
})
</script>

<style scoped lang="scss">
.browser-use-container {
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

// 操作列按钮样式
:deep(.el-table) {
  .el-button + .el-button {
    margin-left: 6px;
  }
  
  .el-button--small {
    padding: 5px 10px;
    font-size: 12px;
  }
}

.execution-monitor {
  .execution-logs {
    background-color: #1e1e1e;
    color: #d4d4d4;
    padding: 15px;
    border-radius: 4px;
    font-family: 'Courier New', Consolas, Monaco, monospace;
    font-size: 13px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-wrap: break-word;
    min-height: 100px;
    max-height: 400px;
    overflow-y: auto;
  }
  
  .text-gray {
    color: #909399;
  }
}

.gif-player {
  text-align: center;
  
  img {
    max-width: 100%;
    height: auto;
  }
}

// 执行日志详情样式 - 完全参考TestHub
.record-detail {
  .detail-item {
    margin-bottom: 15px;
    
    .label {
      font-weight: bold;
      margin-right: 10px;
      color: #303133;
    }
    
    .value {
      color: #606266;
    }
  }

  .mt-15 {
    margin-top: 15px;
  }

  // 任务描述容器 - 参考TestHub
  .task-description-container {
    background-color: #f5f7fa;
    border: 1px solid #e4e7ed;
    border-radius: 4px;
    padding: 12px 15px;
    margin-top: 8px;

    .task-description-content {
      color: #606266;
      line-height: 1.6;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
  }

  // 错误信息容器
  .error-container {
    background-color: #fef0f0;
    border: 1px solid #fbc4c4;
    border-radius: 4px;
    padding: 12px 15px;
    margin-top: 8px;

    .error-text {
      margin: 0;
      padding: 0;
      color: #f56c6c;
      font-family: 'Courier New', monospace;
      font-size: 13px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
  }

  // 日志容器 - 完全参考TestHub的黑色终端风格
  .log-container {
    background-color: #1e1e1e;
    color: #fff;
    padding: 15px;
    border-radius: 4px;
    max-height: 400px;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
    margin-top: 8px;

    pre {
      margin: 0;
      white-space: pre-wrap;
      word-wrap: break-word;
      font-size: 13px;
      line-height: 1.6;
    }
  }

  // GIF容器
  .gif-container {
    margin-top: 8px;
  }
}
</style>
