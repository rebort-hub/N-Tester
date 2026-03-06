<template>
  <div class="figma-config-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>Figma配置管理</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            添加配置
          </el-button>
        </div>
      </template>

      <!-- 筛选区域 -->
      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="项目">
          <el-select 
            v-model="queryForm.project_id" 
            placeholder="请选择项目" 
            clearable
            style="width: 240px"
          >
            <el-option
              v-for="project in projectList"
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
        <el-table-column prop="file_name" label="文件名称" min-width="180" />
        <el-table-column prop="file_key" label="文件ID" width="130" />
        <el-table-column prop="file_url" label="文件URL" min-width="250" show-overflow-tooltip />
        
        <!-- API配额列 -->
        <el-table-column label="API配额" width="180">
          <template #default="{ row }">
            <div v-if="row.rateLimitStatus" style="padding: 4px 0;">
              <el-progress 
                :percentage="getRateLimitPercentage(row.rateLimitStatus)"
                :status="getRateLimitStatus(row.rateLimitStatus)"
                :stroke-width="12"
              />
              <div style="font-size: 12px; color: #606266; margin-top: 4px;">
                今日剩余: {{ row.rateLimitStatus.remaining_day }}/{{ row.rateLimitStatus.total_day }}
              </div>
            </div>
            <el-button 
              v-else
              type="text" 
              size="small"
              @click="loadRateLimitStatus(row)"
            >
              查看配额
            </el-button>
          </template>
        </el-table-column>
        
        <!-- 缓存状态列 -->
        <el-table-column label="缓存状态" width="140">
          <template #default="{ row }">
            <div v-if="row.cacheInfo">
              <el-tag v-if="row.cacheInfo.is_expired" type="info" size="small">
                已过期
              </el-tag>
              <el-tag v-else type="success" size="small">
                有效 ({{ formatCacheAge(row.cacheInfo.cache_age_hours) }})
              </el-tag>
              <div style="font-size: 12px; color: #909399; margin-top: 4px;">
                命中: {{ row.cacheInfo.hit_count }}次
              </div>
            </div>
            <div v-else-if="row.cacheInfo === null">
              <el-tag type="info" size="small">无缓存</el-tag>
              <div style="font-size: 12px; color: #909399; margin-top: 4px;">
                需要先提取
              </div>
            </div>
            <el-button 
              v-else
              type="text" 
              size="small"
              @click="loadCacheInfo(row)"
            >
              查看缓存
            </el-button>
          </template>
        </el-table-column>
        
        <el-table-column prop="last_sync_time" label="最后同步" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.last_sync_time) }}
          </template>
        </el-table-column>
        
        <el-table-column label="提取状态" width="200">
          <template #default="{ row }">
            <div v-if="row.currentTask">
              <el-progress 
                v-if="row.currentTask.status === 'processing'"
                :percentage="row.currentTask.progress"
                :status="'active'"
              />
              <el-tag v-else-if="row.currentTask.status === 'completed'" type="success">
                提取完成
              </el-tag>
              <el-tag v-else-if="row.currentTask.status === 'failed'" type="danger">
                提取失败
              </el-tag>
              <el-tag v-else type="info">{{ row.currentTask.status }}</el-tag>
              <div v-if="row.currentTask.current_step" style="font-size: 12px; color: #909399; margin-top: 4px;">
                {{ row.currentTask.current_step }}
              </div>
            </div>
            <span v-else style="color: #909399;">-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="480" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small"
              @click="handleExtract(row)"
              :loading="row.extracting"
              :disabled="row.currentTask && row.currentTask.status === 'processing'"
            >
              提取需求
            </el-button>
            <el-button 
              v-if="row.currentTask && row.currentTask.result_document_id"
              type="success" 
              size="small"
              @click="handleViewResult(row.currentTask.result_document_id)"
            >
              查看结果
            </el-button>
            <el-button 
              type="info" 
              size="small"
              @click="handleOfflineView(row)"
              :disabled="!row.cacheInfo || row.cacheInfo.is_expired"
              :title="!row.cacheInfo ? '暂无缓存数据，请先提取' : (row.cacheInfo.is_expired ? '缓存已过期，请重新提取' : '查看缓存数据')"
            >
              离线查看
            </el-button>
            <el-button 
              type="warning" 
              size="small"
              @click="handleCheckUpdates(row)"
            >
              检查更新
            </el-button>
            <el-dropdown trigger="click" style="margin-left: 6px;">
              <el-button size="small">
                更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handlePreview(row)">
                    预览
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleEdit(row)">
                    编辑
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleClearCache(row)" divided>
                    清除缓存
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleDelete(row)" divided>
                    <span style="color: #f56c6c;">删除</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogTitle"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="项目" prop="project_id">
          <el-select 
            v-model="form.project_id" 
            placeholder="请选择项目"
            style="width: 100%"
          >
            <el-option
              v-for="project in projectList"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="Access Token" prop="access_token">
          <el-input 
            v-model="form.access_token" 
            type="password"
            placeholder="原型链接（/proto/）需要填写Token"
            show-password
          />
          <div class="form-tip">
            <strong>⚠️ 重要说明：</strong><br/>
            • <strong>原型链接（/proto/）</strong>：虽然浏览器可以查看，但API访问需要Token<br/>
            • <strong>如何获取Token</strong>：访问 
            <a href="https://www.figma.com/settings" target="_blank" style="color: #409eff">
              Figma设置页面
            </a>
            生成Personal Access Token<br/>
            • <strong>免费账号</strong>：无需付费，注册免费账号即可生成Token
          </div>
        </el-form-item>
        
        <el-form-item label="文件URL" prop="file_url">
          <el-input 
            v-model="form.file_url" 
            placeholder="https://www.figma.com/file/ABC123/MyDesign 或 https://www.figma.com/proto/ABC123/..."
            @blur="extractFileKey"
          />
          <div class="form-tip">
            粘贴Figma文件的完整URL（支持file、proto、design类型链接），系统会自动提取文件ID
          </div>
        </el-form-item>
        
        <el-form-item label="文件ID" prop="file_key">
          <el-input v-model="form.file_key" placeholder="自动提取" readonly />
        </el-form-item>
        
        <el-form-item label="文件名称" prop="file_name">
          <el-input 
            v-model="form.file_name" 
            placeholder="请输入文件名称（可选）"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          确定
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 提取模式选择对话框 -->
    <el-dialog 
      v-model="extractDialogVisible" 
      title="选择提取模式"
      width="520px"
      :close-on-click-modal="false"
    >
      <!-- 智能提示面板 -->
      <el-alert 
        v-if="extractSmartTips"
        :title="extractSmartTips.title"
        :type="extractSmartTips.type"
        :closable="false"
        style="margin-bottom: 20px;"
      >
        <div v-html="extractSmartTips.message"></div>
      </el-alert>
      
      <el-radio-group v-model="extractionMode" style="width: 100%;">
        <div style="margin-bottom: 20px;">
          <el-radio label="simple">
            <span style="font-weight: 600;">快速提取（推荐）</span>
          </el-radio>
          <div style="margin-left: 24px; margin-top: 8px; color: #606266; font-size: 13px; line-height: 1.6;">
            5-10秒完成，基于Frame结构生成需求<br/>
            适合快速预览和大文件<br/>
            不会触发API速率限制
          </div>
        </div>
        
        <div>
          <el-radio label="complete">
            <span style="font-weight: 600;">完整分析</span>
          </el-radio>
          <div style="margin-left: 24px; margin-top: 8px; color: #606266; font-size: 13px; line-height: 1.6;">
            5-10分钟完成，使用AI Vision深度分析<br/>
            需求更详细准确<br/>
            需要配置AI模型
          </div>
        </div>
      </el-radio-group>
      
      <!-- 强制刷新选项 -->
      <el-divider style="margin: 20px 0;" />
      <el-checkbox v-model="forceRefresh">
        <span style="font-weight: 500;">强制刷新</span>
        <span style="color: #909399; font-size: 13px; margin-left: 8px;">
          （忽略缓存，重新调用API）
        </span>
      </el-checkbox>
      <div style="margin-left: 24px; margin-top: 8px; color: #909399; font-size: 12px; line-height: 1.5;">
        💡 提示：如果不勾选，系统会自动检查缓存和更新状态，<br/>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;在设计稿无更新时直接使用缓存（0次API调用，1秒完成）
      </div>
      
      <template #footer>
        <el-button @click="extractDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="startExtraction" :loading="extracting">
          开始提取
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 预览对话框 -->
    <el-dialog 
      v-model="previewDialogVisible" 
      title="Figma文件预览"
      width="700px"
    >
      <div v-loading="previewLoading">
        <el-descriptions :column="2" border v-if="previewData">
          <el-descriptions-item label="文件名称">{{ previewData.file_name }}</el-descriptions-item>
          <el-descriptions-item label="文件ID">{{ previewData.file_key }}</el-descriptions-item>
          <el-descriptions-item label="页面数量">{{ previewData.total_pages }}</el-descriptions-item>
          <el-descriptions-item label="Frame数量">{{ previewData.total_frames }}</el-descriptions-item>
          <el-descriptions-item label="预计需求数" :span="2">
            {{ previewData.estimated_requirements }} 个
          </el-descriptions-item>
        </el-descriptions>
        
        <el-divider>页面详情</el-divider>
        
        <el-collapse v-if="previewData">
          <el-collapse-item 
            v-for="(page, index) in previewData.pages" 
            :key="index"
            :title="`${page.name} (${page.frame_count} 个Frame)`"
          >
            <el-table :data="page.frames" size="small" border>
              <el-table-column prop="name" label="Frame名称" />
              <el-table-column prop="width" label="宽度" width="80" />
              <el-table-column prop="height" label="高度" width="80" />
            </el-table>
            <div v-if="page.frame_count > 10" style="color: #909399; font-size: 12px; margin-top: 8px;">
              * 仅显示前10个Frame
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
      
      <template #footer>
        <el-button @click="previewDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleExtractFromPreview">
          开始提取
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 离线查看对话框 -->
    <el-dialog 
      v-model="offlineViewDialogVisible" 
      title="离线查看（缓存数据）"
      width="700px"
    >
      <div v-loading="offlineViewLoading">
        <el-alert 
          title="提示"
          type="info"
          :closable="false"
          style="margin-bottom: 16px;"
        >
          此数据来自缓存，可能不是最新版本。如需最新数据，请点击"检查更新"后重新提取。
        </el-alert>
        
        <el-descriptions :column="2" border v-if="offlineViewData">
          <el-descriptions-item label="文件名称">{{ offlineViewData.file_name }}</el-descriptions-item>
          <el-descriptions-item label="文件ID">{{ offlineViewData.file_key }}</el-descriptions-item>
          <el-descriptions-item label="页面数量">{{ offlineViewData.total_pages }}</el-descriptions-item>
          <el-descriptions-item label="Frame数量">{{ offlineViewData.total_frames }}</el-descriptions-item>
          <el-descriptions-item label="缓存时间" :span="2">
            {{ formatDateTime(offlineViewData.cache_time) }}
          </el-descriptions-item>
        </el-descriptions>
        
        <el-divider>页面详情</el-divider>
        
        <el-collapse v-if="offlineViewData">
          <el-collapse-item 
            v-for="(page, index) in offlineViewData.pages" 
            :key="index"
            :title="`${page.name} (${page.frame_count} 个Frame)`"
          >
            <el-table :data="page.frames" size="small" border>
              <el-table-column prop="name" label="Frame名称" />
              <el-table-column prop="width" label="宽度" width="80" />
              <el-table-column prop="height" label="高度" width="80" />
            </el-table>
            <div v-if="page.frame_count > 10" style="color: #909399; font-size: 12px; margin-top: 8px;">
              * 仅显示前10个Frame
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
      
      <template #footer>
        <el-button @click="offlineViewDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { Plus, ArrowDown } from '@element-plus/icons-vue'
import { figmaConfigApi } from '/@/api/v1/ai_intelligence'
import { getProjectList as fetchProjectList } from '/@/api/v1/project'
import { useRouter } from 'vue-router'

const router = useRouter()

// 查询表单
const queryForm = reactive({
  project_id: null as number | null
})

// 项目列表
const projectList = ref<any[]>([])

// 表格数据
const tableData = ref<any[]>([])
const loading = ref(false)

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('添加Figma配置')
const formRef = ref<FormInstance>()
const submitLoading = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)

// 提取模式对话框
const extractDialogVisible = ref(false)
const extractionMode = ref('simple')
const forceRefresh = ref(false)
const extracting = ref(false)
const currentExtractConfigId = ref<number | null>(null)
const extractSmartTips = ref<any>(null)

// 预览对话框
const previewDialogVisible = ref(false)
const previewLoading = ref(false)
const previewData = ref<any>(null)
const previewConfigId = ref<number | null>(null)

// 离线查看对话框
const offlineViewDialogVisible = ref(false)
const offlineViewLoading = ref(false)
const offlineViewData = ref<any>(null)

// 轮询定时器
const pollingIntervals = ref<Map<number, any>>(new Map())

const form = reactive({
  project_id: null as number | null,
  access_token: '',
  file_url: '',
  file_key: '',
  file_name: ''
})

const formRules = {
  project_id: [{ required: true, message: '请选择项目', trigger: 'change' }],
  file_url: [{ required: true, message: '请输入文件URL', trigger: 'blur' }],
  file_key: [{ required: true, message: '文件ID不能为空', trigger: 'blur' }]
}

// 获取项目列表
const getProjectList = async () => {
  try {
    const res = await fetchProjectList({ page: 1, page_size: 100 })
    projectList.value = res.data?.items || []
  } catch (error: any) {
    console.error('获取项目列表失败', error)
  }
}

// 获取配置列表
const getList = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (queryForm.project_id) params.project_id = queryForm.project_id
    
    const res = await figmaConfigApi.list(params)
    tableData.value = res.data || []
    
    // 为每个配置获取最新任务状态、速率限制和缓存信息
    for (const config of tableData.value) {
      await loadLatestTask(config.id)
      // 异步加载速率限制和缓存信息（不阻塞）
      loadRateLimitStatus(config)
      loadCacheInfo(config)
    }
  } catch (error) {
    ElMessage.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

// 加载最新任务状态
const loadLatestTask = async (configId: number) => {
  try {
    const res = await figmaConfigApi.getLatestTask(configId)
    const task = res.data
    
    // 找到对应的配置并更新任务状态
    const config = tableData.value.find(c => c.id === configId)
    if (config) {
      config.currentTask = task
      
      // 如果任务正在处理中，启动轮询
      if (task && task.status === 'processing') {
        startPolling(configId, task.task_id)
      }
    }
  } catch (error) {
    console.error('加载任务状态失败', error)
  }
}

// 启动轮询
const startPolling = (configId: number, taskId: string) => {
  // 如果已经有轮询，先清除
  if (pollingIntervals.value.has(configId)) {
    clearInterval(pollingIntervals.value.get(configId))
  }
  
  const interval = setInterval(async () => {
    try {
      const res = await figmaConfigApi.getTaskStatus(taskId)
      const task = res.data
      
      // 更新表格中的任务状态
      const config = tableData.value.find(c => c.id === configId)
      if (config) {
        config.currentTask = task
      }
      
      // 如果任务完成或失败，停止轮询
      if (task.status === 'completed' || task.status === 'failed') {
        clearInterval(interval)
        pollingIntervals.value.delete(configId)
        
        if (task.status === 'completed') {
          ElMessage.success('提取完成！')
          
          // 刷新缓存信息和速率限制状态
          const config = tableData.value.find(c => c.id === configId)
          if (config) {
            await loadCacheInfo(config)
            await loadRateLimitStatus(config)
          }
        } else {
          ElMessage.error(`提取失败: ${task.error_message}`)
        }
      }
    } catch (error) {
      console.error('轮询任务状态失败', error)
      clearInterval(interval)
      pollingIntervals.value.delete(configId)
    }
  }, 2000) // 每2秒查询一次
  
  pollingIntervals.value.set(configId, interval)
}

// 查询
const handleQuery = () => {
  getList()
}

// 重置
const handleReset = () => {
  queryForm.project_id = null
  getList()
}

// 添加
const handleAdd = () => {
  isEdit.value = false
  dialogTitle.value = '添加Figma配置'
  form.project_id = null
  form.access_token = ''
  form.file_url = ''
  form.file_key = ''
  form.file_name = ''
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row: any) => {
  isEdit.value = true
  editId.value = row.id
  dialogTitle.value = '编辑Figma配置'
  form.project_id = row.project_id
  form.access_token = ''  // 不显示原密码
  form.file_url = row.file_url || ''
  form.file_key = row.file_key
  form.file_name = row.file_name || ''
  dialogVisible.value = true
}

// 从URL提取文件ID
const extractFileKey = () => {
  const url = form.file_url
  if (!url) return
  
  // 匹配 /file/, /proto/, /design/ 后面的文件ID
  const match = url.match(/\/(file|proto|design)\/([a-zA-Z0-9]+)/)
  if (match) {
    form.file_key = match[2]
    ElMessage.success('文件ID提取成功')
  } else {
    ElMessage.warning('无法从URL中提取文件ID，请检查URL格式')
  }
}

// 提交
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitLoading.value = true
    try {
      const data = {
        project_id: form.project_id,
        access_token: form.access_token,
        file_key: form.file_key,
        file_url: form.file_url,
        file_name: form.file_name
      }
      
      if (isEdit.value && editId.value) {
        // 编辑时，如果没有输入新密码，则不传access_token
        if (!form.access_token) {
          delete data.access_token
        }
        await figmaConfigApi.update(editId.value, data)
        ElMessage.success('更新成功')
      } else {
        await figmaConfigApi.create(data)
        ElMessage.success('创建成功')
      }
      
      dialogVisible.value = false
      getList()
    } catch (error: any) {
      ElMessage.error(error.response?.data?.message || '操作失败')
    } finally {
      submitLoading.value = false
    }
  })
}

// 加载速率限制状态
const loadRateLimitStatus = async (row: any) => {
  try {
    const res = await figmaConfigApi.getRateLimitStatus(row.id)
    if (res.code === 200) {
      row.rateLimitStatus = res.data
    }
  } catch (error: any) {
    console.error('加载速率限制状态失败', error)
  }
}

// 加载缓存信息
const loadCacheInfo = async (row: any) => {
  try {
    const res = await figmaConfigApi.getCacheInfo(row.id)
    if (res.code === 200) {
      row.cacheInfo = res.data
    } else if (res.code === 404) {
      // 没有缓存数据
      row.cacheInfo = null
    }
  } catch (error: any) {
    // 404表示没有缓存，这是正常情况
    if (error.response?.status === 404) {
      row.cacheInfo = null
    } else {
      console.error('加载缓存信息失败', error)
    }
  }
}

// 获取速率限制百分比
const getRateLimitPercentage = (status: any) => {
  if (!status) return 0
  return Math.round((status.remaining_day / status.total_day) * 100)
}

// 获取速率限制状态
const getRateLimitStatus = (status: any) => {
  if (!status) return ''
  if (status.warning_level === 'danger') return 'exception'
  if (status.warning_level === 'warning') return 'warning'
  return 'success'
}

// 格式化缓存年龄
const formatCacheAge = (hours: number) => {
  if (hours < 1) return '< 1小时'
  if (hours < 24) return `${Math.round(hours)}小时`
  return `${Math.round(hours / 24)}天`
}

// 生成智能提示
const generateSmartTips = async (configId: number) => {
  try {
    // 加载速率限制和缓存信息
    const [rateLimitRes, cacheRes, updateRes] = await Promise.all([
      figmaConfigApi.getRateLimitStatus(configId),
      figmaConfigApi.getCacheInfo(configId),
      figmaConfigApi.checkUpdates(configId)
    ])
    
    const rateLimit = rateLimitRes.data
    const cache = cacheRes.data
    const update = updateRes.data
    
    // 根据情况生成提示
    if (!rateLimit.can_call) {
      return {
        type: 'error',
        title: '⚠️ API配额不足',
        message: `需要等待 ${rateLimit.wait_seconds} 秒后才能调用API。<br/>建议：使用"离线查看"功能查看缓存数据。`
      }
    }
    
    if (rateLimit.warning_level === 'danger') {
      return {
        type: 'warning',
        title: '⚠️ API配额即将用尽',
        message: `今日剩余配额：${rateLimit.remaining_day}/${rateLimit.total_day}<br/>建议：优先使用"快速提取"模式，或使用"离线查看"。`
      }
    }
    
    // 如果没有缓存
    if (!update.cache_exists) {
      return {
        type: 'info',
        title: '🆕 首次提取',
        message: `这是首次提取，暂无缓存数据。<br/>提取成功后会自动创建缓存，后续可使用"离线查看"功能。`
      }
    }
    
    // 有缓存且无更新
    if (cache && !cache.is_expired && !update.has_updates) {
      return {
        type: 'info',
        title: '💡 提示',
        message: `设计稿无更新，缓存仍然有效（${formatCacheAge(cache.cache_age_hours)}）。<br/>建议：使用"离线查看"功能，无需重新提取。`
      }
    }
    
    // 有更新
    if (update.has_updates && update.cache_exists) {
      return {
        type: 'warning',
        title: '🔄 设计稿已更新',
        message: `检测到设计稿有更新。<br/>建议：重新提取以获取最新需求。`
      }
    }
    
    return {
      type: 'success',
      title: '✅ 一切正常',
      message: `API配额充足（剩余 ${rateLimit.remaining_day}/${rateLimit.total_day}），可以开始提取。`
    }
  } catch (error) {
    console.error('生成智能提示失败', error)
    return null
  }
}

// 提取需求 - 打开模式选择对话框
const handleExtract = async (row: any) => {
  currentExtractConfigId.value = row.id
  extractionMode.value = 'simple'
  forceRefresh.value = false  // 重置强制刷新选项
  
  // 生成智能提示
  extractSmartTips.value = await generateSmartTips(row.id)
  
  extractDialogVisible.value = true
}

// 离线查看
const handleOfflineView = async (row: any) => {
  offlineViewDialogVisible.value = true
  offlineViewLoading.value = true
  
  try {
    const res = await figmaConfigApi.getCachedData(row.id)
    if (res.code === 200) {
      offlineViewData.value = res.data
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '加载缓存数据失败')
    offlineViewDialogVisible.value = false
  } finally {
    offlineViewLoading.value = false
  }
}

// 检查更新
const handleCheckUpdates = async (row: any) => {
  try {
    const res = await figmaConfigApi.checkUpdates(row.id)
    if (res.code === 200) {
      const update = res.data
      
      // 如果没有缓存
      if (!update.cache_exists) {
        ElMessageBox.confirm(
          `这是首次提取，暂无缓存数据。<br/><br/>
          <strong>提示：</strong>首次提取后会自动创建缓存，<br/>
          后续查看时可以使用"离线查看"功能。<br/><br/>
          是否立即开始提取？`,
          '首次提取',
          {
            confirmButtonText: '开始提取',
            cancelButtonText: '稍后',
            type: 'info',
            dangerouslyUseHTMLString: true
          }
        ).then(() => {
          handleExtract(row)
        })
        return
      }
      
      // 有缓存，检查是否有更新
      if (update.has_updates) {
        ElMessageBox.confirm(
          `检测到设计稿有更新！<br/><br/>
          <strong>变更摘要：</strong>${update.changes_summary}<br/>
          <strong>最新修改时间：</strong>${formatDateTime(update.last_modified)}<br/>
          <strong>缓存修改时间：</strong>${formatDateTime(update.cached_modified)}<br/><br/>
          是否立即重新提取？`,
          '设计稿已更新',
          {
            confirmButtonText: '立即提取',
            cancelButtonText: '稍后',
            type: 'warning',
            dangerouslyUseHTMLString: true
          }
        ).then(() => {
          handleExtract(row)
        })
      } else {
        ElMessage.success({
          message: '✅ 设计稿无更新，当前缓存仍然有效',
          duration: 3000
        })
      }
      
      // 刷新缓存信息
      await loadCacheInfo(row)
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '检查更新失败')
  }
}

// 清除缓存
const handleClearCache = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要清除该配置的缓存吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await figmaConfigApi.clearCache(row.id)
    if (res.code === 200) {
      ElMessage.success(res.message || '缓存已清除')
      // 刷新缓存信息
      row.cacheInfo = null
      await loadCacheInfo(row)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '清除缓存失败')
    }
  }
}

// 开始提取
const startExtraction = async () => {
  if (!currentExtractConfigId.value) return
  
  extracting.value = true
  try {
    const res = await figmaConfigApi.extractWithMode(
      currentExtractConfigId.value,
      extractionMode.value as 'simple' | 'complete',
      forceRefresh.value
    )
    
    if (res.code === 200) {
      const taskId = res.data.task_id
      const fromCache = res.data.from_cache
      
      if (fromCache) {
        // 使用了缓存
        ElMessage.success({
          message: res.message || '✨ 设计稿无更新，已使用缓存数据（0次API调用，1秒完成）',
          duration: 5000
        })
        
        extractDialogVisible.value = false
        
        // 刷新列表，显示结果
        await loadLatestTask(currentExtractConfigId.value)
      } else {
        // 正常提取
        ElMessage.success(
          extractionMode.value === 'simple' 
            ? '快速提取已启动，预计5-10秒完成' 
            : '完整分析已启动，预计5-10分钟完成'
        )
        
        extractDialogVisible.value = false
        
        // 启动轮询
        startPolling(currentExtractConfigId.value, taskId)
        
        // 刷新列表
        await loadLatestTask(currentExtractConfigId.value)
      }
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '启动提取失败')
  } finally {
    extracting.value = false
  }
}

// 预览
const handlePreview = async (row: any) => {
  previewConfigId.value = row.id
  previewDialogVisible.value = true
  previewLoading.value = true
  
  try {
    const res = await figmaConfigApi.preview(row.id)
    if (res.code === 200) {
      previewData.value = res.data
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '预览失败')
    previewDialogVisible.value = false
  } finally {
    previewLoading.value = false
  }
}

// 从预览对话框开始提取
const handleExtractFromPreview = () => {
  previewDialogVisible.value = false
  if (previewConfigId.value) {
    const config = tableData.value.find(c => c.id === previewConfigId.value)
    if (config) {
      handleExtract(config)
    }
  }
}

// 查看结果
const handleViewResult = (documentId: number) => {
  // 跳转到需求文档管理页面
  router.push({
    path: '/ai/intelligence/requirement-analysis',
    query: { documentId }
  })
}

// 删除
const handleDelete = (row: any) => {
  ElMessageBox.confirm('确定要删除该配置吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await figmaConfigApi.delete(row.id)
      ElMessage.success('删除成功')
      getList()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

// 格式化时间
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
  } catch (e) {
    return dateStr
  }
}

// 清理所有轮询
const cleanupPolling = () => {
  pollingIntervals.value.forEach(interval => clearInterval(interval))
  pollingIntervals.value.clear()
}

onMounted(() => {
  getProjectList()
  getList()
})

onUnmounted(() => {
  cleanupPolling()
})
</script>

<style scoped lang="scss">
.figma-config-container {
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

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
  line-height: 1.5;
}

:deep(.el-table) {
  .el-button + .el-button {
    margin-left: 6px;
  }
}
</style>
