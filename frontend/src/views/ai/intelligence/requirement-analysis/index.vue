<template>
  <div class="requirement-analysis-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>需求文档管理</span>
          <el-button type="primary" @click="handleUpload">
            <el-icon><Upload /></el-icon>
            上传文档
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
            :popper-options="{ strategy: 'fixed' }"
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
        <el-table-column prop="title" label="文档标题" min-width="200" />
        <el-table-column prop="document_type" label="文档类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.document_type.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="文件大小" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="has_analysis" label="分析状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.has_analysis ? 'success' : 'info'">
              {{ row.has_analysis ? '已分析' : '未分析' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="creation_date" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.creation_date) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button 
              type="success" 
              size="small" 
              @click="handleAnalyze(row)" 
              :loading="row.analyzing"
              :disabled="row.status === 'analyzing'"
            >
              {{ row.status === 'analyzing' ? '分析中' : '分析' }}
            </el-button>
            <el-button 
              type="info" 
              size="small" 
              @click="handleViewAnalysis(row)"
              :disabled="row.status !== 'analyzed'"
            >
              结果
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传需求文档"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="uploadFormRef"
        :model="uploadForm"
        :rules="uploadRules"
        label-width="100px"
      >
        <el-form-item label="项目" prop="project_id">
          <el-select 
            v-model="uploadForm.project_id" 
            placeholder="请选择项目" 
            style="width: 100%"
            :popper-options="{ strategy: 'fixed' }"
          >
            <el-option
              v-for="project in projectList"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="文档标题" prop="title">
          <el-input v-model="uploadForm.title" placeholder="请输入文档标题" />
        </el-form-item>
        <el-form-item label="文档文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            accept=".pdf,.docx,.txt,.md"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持 PDF、DOCX、TXT、MD 格式，文件大小不超过 10MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitUpload" :loading="uploadLoading">
          上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 查看详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="文档详情"
      width="800px"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="文档标题">{{ currentDoc?.title }}</el-descriptions-item>
        <el-descriptions-item label="文档类型">{{ currentDoc?.document_type }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ getStatusLabel(currentDoc?.status) }}</el-descriptions-item>
        <el-descriptions-item label="文件大小">{{ formatFileSize(currentDoc?.file_size) }}</el-descriptions-item>
        <el-descriptions-item label="上传时间" :span="2">{{ formatDateTime(currentDoc?.creation_date) }}</el-descriptions-item>
      </el-descriptions>
      
      <el-divider>提取的文本内容</el-divider>
      <div class="extracted-text">
        {{ currentDoc?.extracted_text || '暂无提取内容' }}
      </div>
    </el-dialog>

    <!-- 分析结果对话框 -->
    <el-dialog
      v-model="analysisDialogVisible"
      title="需求分析结果"
      width="90%"
      :close-on-click-modal="false"
    >
      <el-tabs v-model="activeTab">
        <!-- 分析概览 -->
        <el-tab-pane label="分析概览" name="summary">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="需求数量">
              <el-tag type="primary" size="large">{{ analysisData.requirements_count || 0 }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="分析耗时">
              {{ analysisData.analysis_time ? analysisData.analysis_time.toFixed(2) + 's' : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="分析时间" :span="2">
              {{ formatDateTime(analysisData.created_at) }}
            </el-descriptions-item>
          </el-descriptions>
          
          <el-divider>分析报告</el-divider>
          <div class="analysis-report">
            {{ analysisData.analysis_report || '暂无分析报告' }}
          </div>
        </el-tab-pane>

        <!-- 需求列表 -->
        <el-tab-pane label="需求列表" name="requirements">
          <el-table 
            :data="requirementList" 
            border
            stripe
            style="width: 100%"
          >
            <el-table-column prop="requirement_id" label="需求编号" width="120" align="center" />
            <el-table-column prop="requirement_name" label="需求名称" min-width="200" show-overflow-tooltip />
            <el-table-column prop="requirement_type" label="类型" width="120" align="center">
              <template #default="{ row }">
                <el-tag>{{ row.requirement_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="module" label="模块" width="150" show-overflow-tooltip />
            <el-table-column prop="requirement_level" label="级别" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="getLevelType(row.requirement_level)">
                  {{ row.requirement_level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
            <el-table-column label="操作" width="100" align="center" fixed="right">
              <template #default="{ row }">
                <el-button 
                  type="primary" 
                  size="small"
                  @click="handleViewRequirementDetail(row)"
                >
                  详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>

    <!-- 需求详情对话框 -->
    <el-dialog
      v-model="requirementDetailDialogVisible"
      title="需求详情"
      width="700px"
    >
      <el-descriptions :column="1" border v-if="currentRequirement">
        <el-descriptions-item label="需求编号">
          <el-tag>{{ currentRequirement.requirement_id }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="需求名称">
          {{ currentRequirement.requirement_name }}
        </el-descriptions-item>
        <el-descriptions-item label="需求类型">
          <el-tag>{{ currentRequirement.requirement_type }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="所属模块">
          {{ currentRequirement.module }}
        </el-descriptions-item>
        <el-descriptions-item label="需求级别">
          <el-tag :type="getLevelType(currentRequirement.requirement_level)">
            {{ currentRequirement.requirement_level }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="需求描述">
          <div class="requirement-description">
            {{ currentRequirement.description }}
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="验收标准">
          <div class="acceptance-criteria">
            {{ currentRequirement.acceptance_criteria }}
          </div>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import { useRoute } from 'vue-router'
import { requirementDocumentApi } from '/@/api/v1/ai_intelligence'
import { getProjectList as fetchProjectList } from '/@/api/v1/project'
import type { RequirementDocument } from '/@/types/ai_intelligence'

// 查询表单
const queryForm = reactive({
  project_id: null as number | null
})

// 项目列表
const projectList = ref<any[]>([])

// 表格数据
const tableData = ref<RequirementDocument[]>([])
const loading = ref(false)

// 上传对话框
const uploadDialogVisible = ref(false)
const uploadFormRef = ref<FormInstance>()
const uploadLoading = ref(false)
const uploadRef = ref()

const uploadForm = reactive({
  project_id: null as number | null,
  title: '',
  file: null as File | null
})

const uploadRules = {
  project_id: [{ required: true, message: '请选择项目', trigger: 'change' }],
  title: [{ required: true, message: '请输入文档标题', trigger: 'blur' }],
  file: [{ required: true, message: '请选择文件', trigger: 'change' }]
}

// 详情对话框
const detailDialogVisible = ref(false)
const currentDoc = ref<RequirementDocument | null>(null)

// 获取项目列表
const getProjectList = async () => {
  try {
    const res = await fetchProjectList({ page: 1, page_size: 100 })
    projectList.value = res.data?.items || []
  } catch (error: any) {
    console.error('获取项目列表失败', error)
    // 如果是参数错误，尝试不带参数调用
    if (error?.response?.status === 422) {
      try {
        const res = await fetchProjectList({})
        projectList.value = res.data?.items || []
      } catch (e) {
        console.error('重试失败', e)
      }
    }
  }
}

// 获取文档列表
const getList = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (queryForm.project_id) params.project_id = queryForm.project_id
    
    const res = await requirementDocumentApi.list(params)
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
  queryForm.project_id = null
  getList()
}

// 上传
const handleUpload = () => {
  uploadForm.project_id = null
  uploadForm.title = ''
  uploadForm.file = null
  uploadDialogVisible.value = true
}

// 文件选择
const handleFileChange = (file: any) => {
  uploadForm.file = file.raw
}

// 文件移除
const handleFileRemove = () => {
  uploadForm.file = null
}

// 提交上传
const handleSubmitUpload = async () => {
  if (!uploadFormRef.value) return
  
  await uploadFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    if (!uploadForm.file) {
      ElMessage.warning('请选择文件')
      return
    }
    
    uploadLoading.value = true
    try {
      const formData = new FormData()
      formData.append('file', uploadForm.file)
      formData.append('project_id', String(uploadForm.project_id))
      formData.append('title', uploadForm.title)
      
      await requirementDocumentApi.upload(formData)
      ElMessage.success('上传成功')
      uploadDialogVisible.value = false
      getList()
    } catch (error) {
      ElMessage.error('上传失败')
    } finally {
      uploadLoading.value = false
    }
  })
}

// 查看详情
const handleView = async (row: RequirementDocument) => {
  try {
    console.log('查看文档详情，ID:', row.id)
    const res = await requirementDocumentApi.get(row.id!)
    console.log('获取到的响应:', res)
    
    if (!res || !res.data) {
      console.error('响应数据为空:', res)
      ElMessage.error('获取详情失败：响应数据为空')
      return
    }
    
    currentDoc.value = res.data
    detailDialogVisible.value = true
  } catch (error: any) {
    console.error('获取详情失败:', error)
    console.error('错误详情:', error.response?.data || error.message)
    ElMessage.error(`获取详情失败: ${error.response?.data?.message || error.message || '未知错误'}`)
  }
}

// 分析文档
const handleAnalyze = async (row: RequirementDocument) => {
  try {
    // 确认分析
    await ElMessageBox.confirm(
      '确定要分析该需求文档吗？分析过程可能需要10-60秒。',
      '确认分析',
      {
        confirmButtonText: '开始分析',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    // 启动分析
    row.analyzing = true
    const res = await requirementDocumentApi.analyze(row.id!)
    
    if (res.code === 200) {
      ElMessage.success('需求分析已启动，请稍后查看结果')
      
      // 开始轮询分析状态
      startPollingAnalysisStatus(row)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('启动分析失败:', error)
      ElMessage.error('启动分析失败')
    }
    row.analyzing = false
  }
}

// 轮询分析状态
let pollingTimer: number | null = null
const startPollingAnalysisStatus = (row: RequirementDocument) => {
  // 清除之前的定时器
  if (pollingTimer) {
    clearInterval(pollingTimer)
  }
  
  pollingTimer = window.setInterval(async () => {
    try {
      // 重新获取文档信息
      const res = await requirementDocumentApi.get(row.id!)
      
      if (res.code === 200 && res.data) {
        const doc = res.data
        
        // 更新表格中的文档状态
        const index = tableData.value.findIndex(d => d.id === row.id)
        if (index !== -1) {
          tableData.value[index].status = doc.status
          tableData.value[index].has_analysis = doc.has_analysis
        }
        
        // 如果分析完成或失败，停止轮询
        if (doc.status === 'analyzed' || doc.status === 'failed') {
          stopPollingAnalysisStatus()
          row.analyzing = false
          
          if (doc.status === 'analyzed') {
            ElMessage.success('需求分析完成')
            // 自动打开分析结果
            handleViewAnalysis(row)
          } else {
            ElMessage.error('需求分析失败')
          }
        }
      }
    } catch (error) {
      console.error('轮询分析状态失败:', error)
    }
  }, 3000) // 每3秒轮询一次
}

// 停止轮询
const stopPollingAnalysisStatus = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

// 查看分析结果
const analysisDialogVisible = ref(false)
const analysisData = ref<any>({})
const requirementList = ref<any[]>([])
const activeTab = ref('summary')

const handleViewAnalysis = async (row: RequirementDocument) => {
  try {
    const res = await requirementDocumentApi.getAnalysis(row.id!)
    
    if (res.code === 200 && res.data) {
      analysisData.value = res.data.analysis
      requirementList.value = res.data.requirements || []
      analysisDialogVisible.value = true
      activeTab.value = 'summary'
    } else {
      ElMessage.error(res.message || '获取分析结果失败')
    }
  } catch (error: any) {
    console.error('获取分析结果失败:', error)
    ElMessage.error('获取分析结果失败')
  }
}

// 查看需求详情
const requirementDetailDialogVisible = ref(false)
const currentRequirement = ref<any>(null)

const handleViewRequirementDetail = (row: any) => {
  currentRequirement.value = row
  requirementDetailDialogVisible.value = true
}

// 获取需求级别标签类型
const getLevelType = (level: string) => {
  const map: Record<string, string> = {
    '高': 'danger',
    '中': 'warning',
    '低': 'info'
  }
  return map[level] || 'info'
}

// 删除
const handleDelete = (row: RequirementDocument) => {
  ElMessageBox.confirm('确定要删除该文档吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await requirementDocumentApi.delete(row.id!)
      ElMessage.success('删除成功')
      getList()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

// 辅助函数
const getStatusLabel = (status?: string) => {
  const map: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status || 'pending'] || status
}

const getStatusTagType = (status?: string) => {
  const map: Record<string, any> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status || 'pending'] || ''
}

const formatFileSize = (size?: number) => {
  if (!size) return '-'
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + ' KB'
  return (size / 1024 / 1024).toFixed(2) + ' MB'
}

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

onMounted(async () => {
  getProjectList()
  await getList()
  
  // 处理从Figma配置页面跳转过来的documentId参数
  const route = useRoute()
  const documentId = route.query.documentId
  
  if (documentId) {
    // 找到对应的文档
    const document = tableData.value.find(doc => doc.id === Number(documentId))
    
    if (document) {
      // 如果文档已分析，直接查看分析结果
      if (document.has_analysis) {
        handleViewAnalysis(document)
      } else {
        // 如果未分析，提示用户
        ElMessage.info('文档尚未分析，请先点击"分析"按钮')
      }
    } else {
      ElMessage.warning('未找到指定的文档')
    }
  }
})
</script>

<style scoped lang="scss">
.requirement-analysis-container {
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

.extracted-text {
  max-height: 400px;
  overflow-y: auto;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-word;
}

.analysis-report {
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  min-height: 100px;
}

.requirement-description,
.acceptance-criteria {
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 300px;
  overflow-y: auto;
}

:deep(.el-table) {
  .el-button + .el-button {
    margin-left: 6px;
  }
}
</style>
