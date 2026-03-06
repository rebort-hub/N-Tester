<template>
  <div class="generation-history-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>AI用例生成历史</span>
          <el-button type="primary" size="small" @click="handleRefresh">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="任务标题">
          <el-input
            v-model="searchForm.title"
            placeholder="请输入任务标题"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="searchForm.status"
            placeholder="请选择状态"
            clearable
            style="width: 150px"
          >
            <el-option label="全部" value="" />
            <el-option label="待处理" value="pending" />
            <el-option label="生成中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 数据表格 -->
      <el-table
        :data="tableData"
        v-loading="loading"
        border
        stripe
        style="width: 100%"
      >
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="title" label="任务标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="requirement_text" label="关联需求" min-width="250" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="test_case_count" label="生成用例数量" width="120" align="center">
          <template #default="{ row }">
            <span v-if="row.status === 'completed'">{{ getTestCaseCount(row) }}</span>
            <span v-else style="color: #909399">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="creation_date" label="生成时间" width="160" align="center">
          <template #default="{ row }">
            {{ formatTime(row.creation_date) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="handleView(row)"
              :disabled="row.status !== 'completed'"
            >
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 查看用例对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      :title="`查看生成用例 - ${currentTask?.title}`"
      width="90%"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div v-if="currentTask" class="case-detail-container">
        <!-- 任务信息 -->
        <el-descriptions :column="2" border style="margin-bottom: 20px">
          <el-descriptions-item label="任务标题">
            {{ currentTask.title }}
          </el-descriptions-item>
          <el-descriptions-item label="生成时间">
            {{ formatTime(currentTask.creation_date) }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(currentTask.status)">
              {{ getStatusLabel(currentTask.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="用例数量">
            {{ getTestCaseCount(currentTask) }}
          </el-descriptions-item>
          <el-descriptions-item label="关联需求" :span="2">
            {{ currentTask.requirement_text }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 用例内容标签页 -->
        <el-tabs v-model="activeTab">
          <!-- Writer生成的用例 -->
          <el-tab-pane label="Writer生成用例" name="writer">
            <div class="case-content">
              <div class="markdown-body" v-if="currentTask.generated_test_cases" v-html="renderMarkdown(currentTask.generated_test_cases)"></div>
              <el-empty v-else description="暂无内容" />
            </div>
          </el-tab-pane>

          <!-- Reviewer评审反馈 -->
          <el-tab-pane label="Reviewer评审" name="review" v-if="currentTask.review_feedback">
            <div class="case-content review-content">
              <div class="markdown-body" v-html="renderMarkdown(currentTask.review_feedback)"></div>
            </div>
          </el-tab-pane>

          <!-- 最终用例 -->
          <el-tab-pane label="最终用例" name="final">
            <div class="case-content">
              <div class="markdown-body" v-if="currentTask.final_test_cases" v-html="renderMarkdown(currentTask.final_test_cases)"></div>
              <el-empty v-else description="暂无内容" />
            </div>
          </el-tab-pane>
        </el-tabs>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button type="primary" @click="handleSaveToRecords">
            <el-icon><FolderAdd /></el-icon>
            保存到用例库
          </el-button>
          <el-button type="primary" @click="handleExport">
            <el-icon><Download /></el-icon>
            导出用例
          </el-button>
          <el-button @click="handleCopyContent">
            <el-icon><DocumentCopy /></el-icon>
            复制内容
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 保存到测试用例对话框 -->
    <el-dialog
      v-model="saveDialogVisible"
      title="保存到测试用例管理"
      width="650px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="saveFormRef"
        :model="saveForm"
        :rules="saveRules"
        label-width="120px"
      >
        <el-form-item label="保存类型" prop="save_type">
          <el-radio-group v-model="saveForm.save_type">
            <el-radio label="main">主项目测试用例</el-radio>
            <el-radio label="sub">子项目测试用例</el-radio>
          </el-radio-group>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            主项目：保存到测试管理模块<br/>
            子项目：保存到UI自动化/API测试/性能测试项目
          </div>
        </el-form-item>
        
        <el-form-item label="主项目" prop="project_id">
          <el-select 
            v-model="saveForm.project_id" 
            placeholder="请选择主项目" 
            style="width: 100%"
            @change="handleProjectChange"
          >
            <el-option
              v-for="project in projectList"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        
        <!-- 主项目时显示模块选择 -->
        <el-form-item label="所属模块" v-if="saveForm.save_type === 'main'">
          <el-select 
            v-model="saveForm.module_id" 
            placeholder="请选择模块（可选）" 
            clearable
            style="width: 100%"
            :disabled="!saveForm.project_id"
          >
            <el-option
              v-for="module in moduleList"
              :key="module.id"
              :label="module.name"
              :value="module.id"
            >
              <span>{{ module.name }}</span>
              <span v-if="module.description" style="color: #8492a6; font-size: 12px; margin-left: 10px;">
                {{ module.description }}
              </span>
            </el-option>
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;" v-if="!saveForm.project_id">
            请先选择主项目
          </div>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;" v-else-if="moduleList.length === 0">
            该项目下暂无模块，用例将不关联模块
          </div>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;" v-else>
            不选择则用例不关联模块
          </div>
        </el-form-item>
        
        <template v-if="saveForm.save_type === 'sub'">
          <el-form-item label="子项目类型" prop="sub_project_type">
            <el-radio-group v-model="saveForm.sub_project_type" @change="handleSubProjectTypeChange">
              <el-radio label="ui">UI自动化</el-radio>
              <el-radio label="api">API测试</el-radio>
              <el-radio label="performance" disabled>性能测试</el-radio>
            </el-radio-group>
            <div style="color: #909399; font-size: 12px; margin-top: 5px;">
              性能测试功能开发中
            </div>
          </el-form-item>
          
          <el-form-item label="子项目" prop="sub_project_id">
            <el-select 
              v-model="saveForm.sub_project_id" 
              placeholder="请先选择主项目" 
              style="width: 100%"
              :disabled="!saveForm.project_id"
            >
              <el-option
                v-for="project in subProjectList"
                :key="project.id"
                :label="project.name"
                :value="project.id"
              >
                <span>{{ project.name }}</span>
                <span style="color: #8492a6; font-size: 12px; margin-left: 10px;">
                  {{ project.description || project.base_url }}
                </span>
              </el-option>
            </el-select>
            <div style="color: #909399; font-size: 12px; margin-top: 5px;" v-if="!saveForm.project_id">
              请先选择主项目
            </div>
            <div style="color: #909399; font-size: 12px; margin-top: 5px;" v-else-if="subProjectList.length === 0">
              该主项目下暂无{{ saveForm.sub_project_type === 'ui' ? 'UI自动化' : saveForm.sub_project_type === 'api' ? 'API测试' : '性能测试' }}项目
            </div>
          </el-form-item>
        </template>
        
        <el-form-item label="用例模板">
          <el-select v-model="saveForm.template_id" placeholder="使用默认模板" clearable style="width: 100%">
            <el-option
              v-for="template in templateList"
              :key="template.id"
              :label="template.name"
              :value="template.id"
            />
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            不选择则使用默认模板
          </div>
        </el-form-item>
        
        <el-form-item label="预计保存数量">
          <el-input :value="estimatedCount" disabled />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitSave" :loading="saveLoading">
          确认保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Search, RefreshLeft, Download, DocumentCopy, FolderAdd } from '@element-plus/icons-vue'
import { generationTaskApi, testcaseTemplateApi, projectApi } from '/@/api/v1/ai_intelligence'
import { getProjectList as fetchProjectList } from '/@/api/v1/project'
import { getModuleList } from '/@/api/v1/modules'
import type { GenerationTask } from '/@/types/ai_intelligence'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

// 配置marked
marked.setOptions({
  gfm: true,
  breaks: false,
  headerIds: false,
  mangle: false
})

// 搜索表单
const searchForm = reactive({
  title: '',
  status: ''
})

// 表格数据
const tableData = ref<GenerationTask[]>([])
const loading = ref(false)

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 查看对话框
const viewDialogVisible = ref(false)
const currentTask = ref<GenerationTask | null>(null)
const activeTab = ref('writer')

// 保存对话框
const saveDialogVisible = ref(false)
const saveFormRef = ref()
const saveLoading = ref(false)
const projectList = ref<any[]>([])
const subProjectList = ref<any[]>([])
const moduleList = ref<any[]>([])
const templateList = ref<any[]>([])
const estimatedCount = ref(0)

const saveForm = reactive({
  task_id: '',
  save_type: 'main' as 'main' | 'sub',
  project_id: undefined as number | undefined,
  module_id: undefined as number | undefined,
  sub_project_type: 'ui' as 'ui' | 'api' | 'performance',
  sub_project_id: undefined as number | undefined,
  template_id: undefined as number | undefined
})

const saveRules = {
  save_type: [{ required: true, message: '请选择保存类型', trigger: 'change' }],
  project_id: [{ required: true, message: '请选择主项目', trigger: 'change' }],
  sub_project_type: [
    { 
      validator: (rule: any, value: any, callback: any) => {
        if (saveForm.save_type === 'sub' && !value) {
          callback(new Error('请选择子项目类型'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  sub_project_id: [
    { 
      validator: (rule: any, value: any, callback: any) => {
        if (saveForm.save_type === 'sub' && !value) {
          callback(new Error('请选择子项目'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

// 获取列表数据
const getList = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    
    if (searchForm.title) {
      params.title = searchForm.title
    }
    if (searchForm.status) {
      params.status = searchForm.status
    }
    
    const res = await generationTaskApi.list(params)
    tableData.value = res.data || []
    
    // 如果API返回了分页信息，更新total
    if (res.total !== undefined) {
      pagination.total = res.total
    } else {
      pagination.total = tableData.value.length
    }
  } catch (error) {
    console.error('获取列表失败', error)
    ElMessage.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  getList()
}

// 重置
const handleReset = () => {
  searchForm.title = ''
  searchForm.status = ''
  pagination.page = 1
  getList()
}

// 刷新
const handleRefresh = () => {
  getList()
}

// 分页变化
const handleSizeChange = (size: number) => {
  pagination.page_size = size
  getList()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  getList()
}

// 查看详情
const handleView = async (row: GenerationTask) => {
  try {
    // 获取完整的任务详情
    const res = await generationTaskApi.get(row.task_id)
    currentTask.value = res.data
    activeTab.value = 'writer'
    viewDialogVisible.value = true
  } catch (error) {
    console.error('获取任务详情失败', error)
    ElMessage.error('获取任务详情失败')
  }
}

// 导出用例
const handleExport = () => {
  if (!currentTask.value?.final_test_cases) {
    ElMessage.warning('没有可导出的内容')
    return
  }
  
  try {
    // 解析Markdown表格
    const content = currentTask.value.final_test_cases
    
    // 移除代码块标记
    let processedContent = content.trim()
    if (processedContent.startsWith('```markdown')) {
      processedContent = processedContent.replace(/^```markdown\s*\n/, '')
      processedContent = processedContent.replace(/\n```\s*$/, '')
    } else if (processedContent.startsWith('```')) {
      processedContent = processedContent.replace(/^```\s*\n/, '')
      processedContent = processedContent.replace(/\n```\s*$/, '')
    }
    
    // 解析表格
    const lines = processedContent.split('\n')
    const tableData: string[][] = []
    
    for (const line of lines) {
      const trimmedLine = line.trim()
      if (trimmedLine.startsWith('|') && !trimmedLine.includes('---')) {
        // 解析表格行
        const cells = trimmedLine
          .split('|')
          .slice(1, -1) // 移除首尾的空字符串
          .map(cell => cell.trim().replace(/<br>/g, '\n')) // 处理换行
        
        if (cells.length > 0 && cells.some(cell => cell)) {
          tableData.push(cells)
        }
      }
    }
    
    if (tableData.length === 0) {
      ElMessage.warning('没有找到表格数据')
      return
    }
    
    // 生成CSV格式（Excel可以打开）
    const csvContent = tableData
      .map(row => 
        row.map(cell => {
          // 处理包含逗号、引号或换行的单元格
          if (cell.includes(',') || cell.includes('"') || cell.includes('\n')) {
            return `"${cell.replace(/"/g, '""')}"`
          }
          return cell
        }).join(',')
      )
      .join('\n')
    
    // 添加BOM以支持中文
    const BOM = '\uFEFF'
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${currentTask.value.title}_测试用例_${new Date().getTime()}.csv`
    link.click()
    URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功，请使用Excel打开CSV文件')
  } catch (error) {
    console.error('导出失败', error)
    ElMessage.error('导出失败')
  }
}

// 复制内容
const handleCopyContent = async () => {
  if (!currentTask.value?.final_test_cases) {
    ElMessage.warning('没有可复制的内容')
    return
  }
  
  try {
    await navigator.clipboard.writeText(currentTask.value.final_test_cases)
    ElMessage.success('复制成功')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

// 监听主项目变化，加载子项目
const handleProjectChange = async () => {
  // 清空模块选择
  saveForm.module_id = undefined
  moduleList.value = []
  
  // 加载模块列表（主项目时）
  if (saveForm.save_type === 'main' && saveForm.project_id) {
    try {
      const res = await getModuleList({
        project_id: saveForm.project_id,
        page: 1,
        page_size: 1000
      })
      moduleList.value = res.data?.items || []
    } catch (error) {
      console.error('加载模块列表失败', error)
      moduleList.value = []
    }
  }
  
  // 加载子项目列表（子项目时）
  if (saveForm.save_type === 'sub' && saveForm.project_id) {
    try {
      const res = await projectApi.getSubProjects(saveForm.project_id, {
        project_type: saveForm.sub_project_type
      })
      if (saveForm.sub_project_type === 'ui') {
        subProjectList.value = res.data.ui_projects || []
      } else if (saveForm.sub_project_type === 'api') {
        subProjectList.value = res.data.api_projects || []
      } else if (saveForm.sub_project_type === 'performance') {
        subProjectList.value = res.data.performance_projects || []
      }
      // 清空子项目选择
      saveForm.sub_project_id = undefined
    } catch (error) {
      console.error('加载子项目失败', error)
      subProjectList.value = []
    }
  } else {
    subProjectList.value = []
    saveForm.sub_project_id = undefined
  }
}

// 监听子项目类型变化
const handleSubProjectTypeChange = () => {
  saveForm.sub_project_id = undefined
  subProjectList.value = []
  if (saveForm.project_id) {
    handleProjectChange()
  }
}

// 保存到用例库
const handleSaveToRecords = async () => {
  if (!currentTask.value?.final_test_cases) {
    ElMessage.warning('没有可保存的测试用例')
    return
  }
  
  // 移除重复保存限制，允许保存到不同的项目/模块
  // if (currentTask.value.is_saved_to_records) {
  //   ElMessage.warning('该任务已保存过，请勿重复保存')
  //   return
  // }
  
  // 重置表单
  saveForm.task_id = currentTask.value.task_id
  saveForm.save_type = 'main'  // 默认保存到主项目
  saveForm.project_id = currentTask.value.project_id
  saveForm.module_id = undefined
  saveForm.sub_project_type = 'ui'
  saveForm.sub_project_id = undefined
  saveForm.template_id = undefined
  subProjectList.value = []
  moduleList.value = []
  
  // 计算预计保存数量
  try {
    const content = currentTask.value.final_test_cases
    let processedContent = content.trim()
    if (processedContent.startsWith('```markdown')) {
      processedContent = processedContent.replace(/^```markdown\s*\n/, '')
      processedContent = processedContent.replace(/\n```\s*$/, '')
    } else if (processedContent.startsWith('```')) {
      processedContent = processedContent.replace(/^```\s*\n/, '')
      processedContent = processedContent.replace(/\n```\s*$/, '')
    }
    
    const lines = processedContent.split('\n')
    let count = 0
    for (const line of lines) {
      const trimmedLine = line.trim()
      if (trimmedLine.startsWith('|') && !trimmedLine.includes('---')) {
        const cells = trimmedLine.split('|').slice(1, -1).map(cell => cell.trim())
        if (cells.length > 0 && cells.some(cell => cell)) {
          count++
        }
      }
    }
    estimatedCount.value = Math.max(0, count - 1) // 减去表头
  } catch (error) {
    estimatedCount.value = 0
  }
  
  // 加载项目列表
  try {
    const projectRes = await fetchProjectList({ page: 1, page_size: 1000 })
    projectList.value = projectRes.data?.items || []
  } catch (error: any) {
    console.error('加载项目列表失败', error)
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
  
  // 加载模板列表
  try {
    const res = await testcaseTemplateApi.list({ template_type: 'ui' })
    templateList.value = res.data || []
  } catch (error) {
    console.error('加载模板列表失败', error)
  }
  
  // 如果有项目ID，加载模块列表
  if (saveForm.project_id) {
    try {
      const res = await getModuleList({
        project_id: saveForm.project_id,
        page: 1,
        page_size: 1000
      })
      moduleList.value = res.data?.items || []
    } catch (error) {
      console.error('加载模块列表失败', error)
      moduleList.value = []
    }
  }
  
  saveDialogVisible.value = true
}

// 提交保存
const handleSubmitSave = async () => {
  if (!saveFormRef.value) return
  
  await saveFormRef.value.validate(async (valid: boolean) => {
    if (!valid) return
    
    saveLoading.value = true
    try {
      // 构建请求数据
      const requestData: any = {
        task_id: saveForm.task_id,
        save_type: saveForm.save_type,
        project_id: saveForm.project_id,
        template_id: saveForm.template_id
      }
      
      // 如果是保存到主项目，添加模块ID
      if (saveForm.save_type === 'main') {
        requestData.module_id = saveForm.module_id
      }
      
      // 如果是保存到子项目，添加子项目相关字段
      if (saveForm.save_type === 'sub') {
        requestData.sub_project_type = saveForm.sub_project_type
        requestData.sub_project_id = saveForm.sub_project_id
      }
      
      const res = await generationTaskApi.saveToTestcases(saveForm.task_id, requestData)
      ElMessage.success(res.message || '保存成功')
      saveDialogVisible.value = false
      
      // 刷新任务详情
      if (currentTask.value) {
        const taskRes = await generationTaskApi.get(currentTask.value.task_id)
        currentTask.value = taskRes.data
      }
    } catch (error: any) {
      console.error('保存失败', error)
      ElMessage.error(error.message || '保存失败')
    } finally {
      saveLoading.value = false
    }
  })
}

// 计算用例数量
const getTestCaseCount = (task: GenerationTask) => {
  if (!task.final_test_cases) return 0
  
  // 统计表格行数（排除表头）
  const lines = task.final_test_cases.split('\n')
  let count = 0
  
  for (const line of lines) {
    // 匹配表格数据行（以|开头，不是分隔符行）
    if (line.trim().startsWith('|') && !line.includes('---')) {
      count++
    }
  }
  
  // 减去表头行
  return Math.max(0, count - 1)
}

// 辅助函数
const getStatusLabel = (status?: string) => {
  const map: Record<string, string> = {
    pending: '待处理',
    running: '生成中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status || 'pending'] || status
}

const getStatusTagType = (status?: string) => {
  const map: Record<string, any> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status || 'pending'] || ''
}

const formatTime = (time?: string) => {
  if (!time) return ''
  return time.substring(0, 16).replace('T', ' ')
}

// Markdown渲染函数
const renderMarkdown = (content?: string) => {
  if (!content) return '<p class="empty-text">暂无内容</p>'
  
  try {
    // 移除markdown代码块标记（如果存在）
    let processedContent = content.trim()
    
    // 检查是否被包裹在```markdown代码块中
    if (processedContent.startsWith('```markdown')) {
      processedContent = processedContent.replace(/^```markdown\s*\n/, '')
      processedContent = processedContent.replace(/\n```\s*$/, '')
    } else if (processedContent.startsWith('```')) {
      processedContent = processedContent.replace(/^```\s*\n/, '')
      processedContent = processedContent.replace(/\n```\s*$/, '')
    }
    
    // 使用marked解析Markdown
    const html = marked.parse(processedContent) as string
    // 使用DOMPurify清理HTML，防止XSS攻击
    return DOMPurify.sanitize(html)
  } catch (error) {
    console.error('Markdown渲染失败:', error)
    return `<pre>${content}</pre>`
  }
}

onMounted(() => {
  getList()
})
</script>

<style scoped lang="scss">
.generation-history-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}

.case-detail-container {
  .case-content {
    padding: 20px;
    background-color: #fff;
    border: 1px solid #e4e7ed;
    border-radius: 4px;
    max-height: 600px;
    overflow-y: auto;
    overflow-x: auto;
    
    &.review-content {
      background-color: #f9fafb;
      padding-left: 22px;
    }
  }
  
  .action-buttons {
    margin-top: 20px;
    text-align: center;
  }
}

// Markdown样式
.markdown-body {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
  
  h1, h2, h3, h4, h5, h6 {
    margin-top: 24px;
    margin-bottom: 16px;
    font-weight: 600;
    line-height: 1.25;
  }
  
  h1 {
    font-size: 2em;
    border-bottom: 1px solid #eaecef;
    padding-bottom: 0.3em;
  }
  
  h2 {
    font-size: 1.5em;
    border-bottom: 1px solid #eaecef;
    padding-bottom: 0.3em;
  }
  
  h3 {
    font-size: 1.25em;
  }
  
  p {
    margin-bottom: 16px;
  }
  
  ul, ol {
    padding-left: 2em;
    margin-bottom: 16px;
  }
  
  li {
    margin-bottom: 4px;
  }
  
  code {
    padding: 0.2em 0.4em;
    margin: 0;
    font-size: 85%;
    background-color: rgba(27, 31, 35, 0.05);
    border-radius: 3px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  }
  
  pre {
    padding: 16px;
    overflow: auto;
    font-size: 85%;
    line-height: 1.45;
    background-color: #f6f8fa;
    border-radius: 6px;
    
    code {
      background-color: transparent;
      padding: 0;
    }
  }
  
  blockquote {
    padding: 0 1em;
    color: #6a737d;
    border-left: 0.25em solid #dfe2e5;
    margin-bottom: 16px;
  }
  
  hr {
    height: 0.25em;
    padding: 0;
    margin: 24px 0;
    background-color: #e1e4e8;
    border: 0;
  }
  
  .empty-text {
    color: #909399;
    text-align: center;
    padding: 20px;
  }
}

// 表格样式
.case-content {
  :deep(table) {
    width: 100%;
    border-collapse: collapse;
    border-spacing: 0;
    margin: 16px 0;
    display: table;
    table-layout: auto;
    font-size: 14px;
    
    thead {
      background-color: #f6f8fa;
      
      tr {
        border-top: 1px solid #c6cbd1;
      }
      
      th {
        font-weight: 600;
        padding: 12px 16px;
        text-align: left;
        border: 1px solid #dfe2e5;
        background-color: #f6f8fa;
        white-space: nowrap;
        min-width: 100px;
      }
    }
    
    tbody {
      tr {
        background-color: #fff;
        border-top: 1px solid #c6cbd1;
        
        &:nth-child(2n) {
          background-color: #f6f8fa;
        }
        
        &:hover {
          background-color: #f0f9ff;
        }
      }
      
      td {
        padding: 12px 16px;
        border: 1px solid #dfe2e5;
        vertical-align: top;
        min-width: 100px;
        word-break: break-word;
        white-space: pre-wrap;
        overflow-wrap: break-word;
      }
    }
  }
}
</style>
