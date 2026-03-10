<template>
  <div class="case-generation-container">
    <el-row :gutter="20">
      <!-- 左侧：任务列表 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>生成任务</span>
              <div class="header-actions">
                <el-button 
                  v-if="selectedTaskIds.length > 0" 
                  type="danger" 
                  size="small" 
                  @click="handleBatchDelete"
                >
                  <el-icon><Delete /></el-icon>
                  批量删除 ({{ selectedTaskIds.length }})
                </el-button>
                <el-button type="primary" size="small" @click="handleCreateTask">
                  <el-icon><Plus /></el-icon>
                  新建
                </el-button>
              </div>
            </div>
          </template>

          <el-input
            v-model="searchKeyword"
            placeholder="搜索任务"
            clearable
            style="margin-bottom: 15px"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <el-scrollbar height="calc(100vh - 280px)">
            <div class="task-list-header">
              <el-checkbox 
                v-model="selectAll" 
                @change="handleSelectAll"
                :indeterminate="isIndeterminate"
              >
                全选
              </el-checkbox>
            </div>
            <div
              v-for="task in filteredTasks"
              :key="task.task_id"
              class="task-item"
              :class="{ active: currentTask?.task_id === task.task_id }"
            >
              <div class="task-checkbox">
                <el-checkbox 
                  v-model="selectedTaskIds" 
                  :value="task.task_id"
                  @click.stop
                />
              </div>
              <div class="task-content" @click="handleSelectTask(task)">
                <div class="task-title">{{ task.title }}</div>
                <div class="task-meta">
                  <el-tag :type="getStatusTagType(task.status)" size="small">
                    {{ getStatusLabel(task.status) }}
                  </el-tag>
                  <span class="task-time">{{ formatTime(task.creation_date) }}</span>
                </div>
                <el-progress
                  v-if="task.status === 'running'"
                  :percentage="task.progress || 0"
                  :show-text="false"
                  style="margin-top: 5px"
                />
              </div>
              <div class="task-actions">
                <el-button 
                  type="danger" 
                  size="small" 
                  text
                  @click.stop="handleDeleteTask(task)"
                  title="删除"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <el-empty v-if="filteredTasks.length === 0" description="暂无任务" />
          </el-scrollbar>
        </el-card>
      </el-col>

      <!-- 右侧：任务详情 -->
      <el-col :span="16">
        <el-card shadow="hover" v-if="currentTask">
          <template #header>
            <div class="card-header">
              <span>{{ currentTask.title }}</span>
              <div>
                <el-tag :type="getStatusTagType(currentTask.status)">
                  {{ getStatusLabel(currentTask.status) }}
                </el-tag>
              </div>
            </div>
          </template>

          <el-tabs v-model="activeTab">
            <!-- 需求描述 -->
            <el-tab-pane label="需求描述" name="requirement">
              <div class="requirement-text">
                {{ currentTask.requirement_text }}
              </div>
            </el-tab-pane>

            <!-- 生成结果 -->
            <el-tab-pane label="生成结果" name="result">
              <div v-if="currentTask.status === 'running'" class="generating-status">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>AI正在生成测试用例...</span>
                <el-progress :percentage="currentTask.progress || 0" style="margin-top: 10px" />
                
                <!-- 实时流式输出 -->
                <div v-if="currentTask.output_mode === 'stream' && streamContent" class="stream-output">
                  <el-divider content-position="left">实时输出</el-divider>
                  <div class="stream-content" ref="streamContentRef">
                    {{ streamContent }}
                  </div>
                </div>
              </div>

              <div v-else-if="currentTask.status === 'completed'" class="result-content">
                <el-alert
                  title="生成完成"
                  type="success"
                  :closable="false"
                  style="margin-bottom: 15px"
                />
                
                <div class="section-title writer-title">Writer生成的测试用例</div>
                <div class="generated-content markdown-body" v-if="currentTask.generated_test_cases" v-html="renderMarkdown(currentTask.generated_test_cases)"></div>
                <div class="empty-content" v-else>暂无内容</div>

                <template v-if="currentTask.review_feedback">
                  <div class="section-title reviewer-title">Reviewer评审反馈</div>
                  <div class="review-content" v-html="renderMarkdown(currentTask.review_feedback)"></div>
                </template>

                <div class="section-title final-title">最终测试用例</div>
                <div class="final-content markdown-body" v-if="currentTask.final_test_cases" v-html="renderMarkdown(currentTask.final_test_cases)"></div>
                <div class="empty-content" v-else>暂无内容</div>

                <div class="action-buttons">
                  <el-button type="primary" @click="handleSaveToRecords">
                    保存到用例库
                  </el-button>
                  <el-button @click="handleExport">导出</el-button>
                  <el-button @click="handleCopyContent">复制内容</el-button>
                </div>
              </div>

              <div v-else-if="currentTask.status === 'failed'" class="error-status">
                <el-alert
                  title="生成失败"
                  :description="currentTask.error_message"
                  type="error"
                  :closable="false"
                />
              </div>

              <el-empty v-else description="等待生成" />
            </el-tab-pane>

            <!-- 生成日志 -->
            <el-tab-pane label="生成日志" name="log">
              <div class="log-content">
                {{ currentTask.generation_log || '暂无日志' }}
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>

        <el-empty v-else description="请选择一个任务" />
      </el-col>
    </el-row>

    <!-- 创建任务对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建生成任务"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="140px"
      >
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="createForm.title" placeholder="请输入任务标题" />
        </el-form-item>
        <el-form-item label="项目">
          <el-select 
            v-model="createForm.project_id" 
            placeholder="请选择项目" 
            clearable 
            style="width: 100%"
            @change="handleCreateProjectChange"
          >
            <el-option
              v-for="project in projectList"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="需求文档">
          <el-select 
            v-model="selectedDocumentId" 
            placeholder="请选择需求文档（可选）" 
            clearable 
            style="width: 100%"
            :disabled="!createForm.project_id"
            @change="handleDocumentChange"
          >
            <el-option
              v-for="doc in requirementDocuments"
              :key="doc.id"
              :label="doc.title"
              :value="doc.id"
            >
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>{{ doc.title }}</span>
                <el-tag size="small" type="info" style="margin-left: 10px;">
                  {{ formatTime(doc.upload_date) }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;" v-if="!createForm.project_id">
            请先选择项目
          </div>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;" v-else-if="requirementDocuments.length === 0">
            该项目下暂无需求文档，请手动输入需求描述
          </div>
          <div style="color: #67c23a; font-size: 12px; margin-top: 5px;" v-else-if="selectedDocumentId">
            已选择文档，需求描述将自动填充
          </div>
        </el-form-item>
        <el-form-item label="需求描述" prop="requirement_text">
          <el-input
            v-model="createForm.requirement_text"
            type="textarea"
            :rows="8"
            placeholder="请输入需求描述"
          />
        </el-form-item>
        <el-form-item label="输出模式">
          <el-radio-group v-model="createForm.output_mode">
            <el-radio label="stream">流式输出</el-radio>
            <el-radio label="batch">批量输出</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="Writer模型配置" prop="writer_model_config_id">
          <el-select v-model="createForm.writer_model_config_id" placeholder="请选择" style="width: 100%">
            <el-option
              v-for="config in writerModelConfigs"
              :key="config.id"
              :label="config.name"
              :value="config.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Reviewer模型配置" prop="reviewer_model_config_id">
          <el-select v-model="createForm.reviewer_model_config_id" placeholder="请选择" style="width: 100%">
            <el-option
              v-for="config in reviewerModelConfigs"
              :key="config.id"
              :label="config.name"
              :value="config.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Writer提示词" prop="writer_prompt_config_id">
          <el-select v-model="createForm.writer_prompt_config_id" placeholder="请选择" style="width: 100%">
            <el-option
              v-for="config in writerPromptConfigs"
              :key="config.id"
              :label="config.name"
              :value="config.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Reviewer提示词" prop="reviewer_prompt_config_id">
          <el-select v-model="createForm.reviewer_prompt_config_id" placeholder="请选择" style="width: 100%">
            <el-option
              v-for="config in reviewerPromptConfigs"
              :key="config.id"
              :label="config.name"
              :value="config.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitCreate" :loading="createLoading">
          创建并开始生成
        </el-button>
      </template>
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
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { Plus, Search, Loading, Delete } from '@element-plus/icons-vue'
import { generationTaskApi, aiModelConfigApi, promptConfigApi, testcaseTemplateApi, projectApi, requirementDocumentApi } from '/@/api/v1/ai_intelligence'
import { getProjectList as fetchProjectList } from '/@/api/v1/project'
import { getModuleList } from '/@/api/v1/modules'
import type { GenerationTask, GenerationTaskForm, AIModelConfig, PromptConfig, RequirementDocument } from '/@/types/ai_intelligence'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

// 配置marked
marked.setOptions({
  gfm: true, // 启用GitHub风格的Markdown
  breaks: false, // 不自动转换换行
  headerIds: false,
  mangle: false
})

// 任务列表
const taskList = ref<GenerationTask[]>([])
const searchKeyword = ref('')
const currentTask = ref<GenerationTask | null>(null)
const activeTab = ref('requirement')

// 筛选后的任务列表
const filteredTasks = computed(() => {
  if (!searchKeyword.value) return taskList.value
  return taskList.value.filter(task =>
    task.title.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
})

// 项目列表
const projectList = ref<any[]>([])

// 模型配置
const writerModelConfigs = ref<AIModelConfig[]>([])
const reviewerModelConfigs = ref<AIModelConfig[]>([])

// 提示词配置
const writerPromptConfigs = ref<PromptConfig[]>([])
const reviewerPromptConfigs = ref<PromptConfig[]>([])

// 需求文档列表
const requirementDocuments = ref<RequirementDocument[]>([])
const selectedDocumentId = ref<number | undefined>(undefined)

// 批量选择
const selectedTaskIds = ref<string[]>([])
const selectAll = ref(false)
const isIndeterminate = computed(() => {
  const count = selectedTaskIds.value.length
  return count > 0 && count < filteredTasks.value.length
})

// 保存对话框
const saveDialogVisible = ref(false)
const saveFormRef = ref<FormInstance>()
const saveLoading = ref(false)
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

// 创建对话框
const createDialogVisible = ref(false)
const createFormRef = ref<FormInstance>()
const createLoading = ref(false)

const createForm = reactive<GenerationTaskForm>({
  project_id: undefined,
  title: '',
  requirement_text: '',
  output_mode: 'stream',
  writer_model_config_id: undefined,
  reviewer_model_config_id: undefined,
  writer_prompt_config_id: undefined,
  reviewer_prompt_config_id: undefined
})

const createRules = {
  title: [{ required: true, message: '请输入任务标题', trigger: 'blur' }],
  requirement_text: [{ required: true, message: '请输入需求描述', trigger: 'blur' }],
  writer_model_config_id: [{ required: true, message: '请选择Writer模型配置', trigger: 'change' }],
  reviewer_model_config_id: [{ required: true, message: '请选择Reviewer模型配置', trigger: 'change' }],
  writer_prompt_config_id: [{ required: true, message: '请选择Writer提示词', trigger: 'change' }],
  reviewer_prompt_config_id: [{ required: true, message: '请选择Reviewer提示词', trigger: 'change' }]
}

// 轮询定时器
let pollingTimer: number | null = null

// 流式输出内容
const streamContent = ref('')
const streamContentRef = ref<HTMLElement>()

// 获取任务列表
const getTaskList = async () => {
  try {
    const res = await generationTaskApi.list()
    taskList.value = res.data || []
    
    // 如果当前任务正在运行，更新其状态和流式内容
    if (currentTask.value && currentTask.value.status === 'running') {
      const updatedTask = taskList.value.find(t => t.task_id === currentTask.value?.task_id)
      if (updatedTask) {
        currentTask.value = updatedTask
        
        // 更新流式内容
        if (updatedTask.output_mode === 'stream' && updatedTask.stream_buffer) {
          streamContent.value = updatedTask.stream_buffer
          
          // 自动滚动到底部
          setTimeout(() => {
            if (streamContentRef.value) {
              streamContentRef.value.scrollTop = streamContentRef.value.scrollHeight
            }
          }, 100)
        }
      }
    }
  } catch (error) {
    console.error('获取任务列表失败', error)
  }
}

// 获取项目列表
const getProjectList = async () => {
  try {
    const res = await fetchProjectList({ page: 1, page_size: 1000 })
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

// 获取模型配置
const getModelConfigs = async () => {
  try {
    const writerRes = await aiModelConfigApi.list({ role: 'writer' })
    writerModelConfigs.value = writerRes.data || []
    
    const reviewerRes = await aiModelConfigApi.list({ role: 'reviewer' })
    reviewerModelConfigs.value = reviewerRes.data || []
  } catch (error) {
    console.error('获取模型配置失败', error)
  }
}

// 获取提示词配置
const getPromptConfigs = async () => {
  try {
    const writerRes = await promptConfigApi.list({ prompt_type: 'writer' })
    writerPromptConfigs.value = writerRes.data || []
    
    const reviewerRes = await promptConfigApi.list({ prompt_type: 'reviewer' })
    reviewerPromptConfigs.value = reviewerRes.data || []
  } catch (error) {
    console.error('获取提示词配置失败', error)
  }
}

// 选择任务
const handleSelectTask = (task: GenerationTask) => {
  currentTask.value = task
  activeTab.value = 'requirement'
  
  // 如果任务正在运行且是流式模式，获取流式内容
  if (task.status === 'running' && task.output_mode === 'stream') {
    streamContent.value = task.stream_buffer || ''
  } else {
    streamContent.value = ''
  }
}

// 删除单个任务
const handleDeleteTask = (task: GenerationTask) => {
  console.log('[删除任务] 点击删除按钮', task.task_id, task.title)
  
  ElMessageBox.confirm(`确定要删除任务"${task.title}"吗？此操作不可恢复！`, '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      console.log('[删除任务] 用户确认删除')
      try {
        console.log('[删除任务] 调用API删除', task.task_id)
        const res = await generationTaskApi.delete(task.task_id!)
        console.log('[删除任务] API响应', res)
        ElMessage.success('删除成功')
        
        // 如果删除的是当前任务，清空当前任务
        if (currentTask.value?.task_id === task.task_id) {
          currentTask.value = null
        }
        
        // 从选中列表中移除
        const index = selectedTaskIds.value.indexOf(task.task_id!)
        if (index > -1) {
          selectedTaskIds.value.splice(index, 1)
        }
        
        // 刷新列表
        await getTaskList()
      } catch (error) {
        console.error('[删除任务] 删除失败', error)
        ElMessage.error('删除失败')
      }
    })
    .catch(() => {
      console.log('[删除任务] 用户取消删除')
    })
}

// 全选/取消全选
const handleSelectAll = (checked: boolean) => {
  if (checked) {
    selectedTaskIds.value = filteredTasks.value.map(task => task.task_id!)
  } else {
    selectedTaskIds.value = []
  }
}

// 批量删除
const handleBatchDelete = () => {
  if (selectedTaskIds.value.length === 0) {
    ElMessage.warning('请选择要删除的任务')
    return
  }
  
  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedTaskIds.value.length} 个任务吗？此操作不可恢复！`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        const res = await generationTaskApi.batchDelete(selectedTaskIds.value)
        ElMessage.success(res.message || '批量删除成功')
        
        // 如果当前任务在删除列表中，清空当前任务
        if (currentTask.value && selectedTaskIds.value.includes(currentTask.value.task_id!)) {
          currentTask.value = null
        }
        
        // 清空选中列表
        selectedTaskIds.value = []
        selectAll.value = false
        
        // 刷新列表
        await getTaskList()
      } catch (error) {
        console.error('批量删除失败', error)
        ElMessage.error('批量删除失败')
      }
    })
    .catch(() => {})
}

// 创建任务
const handleCreateTask = async () => {
  Object.assign(createForm, {
    project_id: undefined,
    title: '',
    requirement_text: '',
    output_mode: 'stream',
    writer_model_config_id: undefined,
    reviewer_model_config_id: undefined,
    writer_prompt_config_id: undefined,
    reviewer_prompt_config_id: undefined
  })
  
  // 清空需求文档选择
  selectedDocumentId.value = undefined
  requirementDocuments.value = []
  
  // 打开对话框前重新加载配置
  await Promise.all([
    getModelConfigs(),
    getPromptConfigs()
  ])
  
  console.log('Writer模型配置:', writerModelConfigs.value)
  console.log('Reviewer模型配置:', reviewerModelConfigs.value)
  console.log('Writer提示词配置:', writerPromptConfigs.value)
  console.log('Reviewer提示词配置:', reviewerPromptConfigs.value)
  
  createDialogVisible.value = true
}

// 创建任务时项目变化
const handleCreateProjectChange = async () => {
  // 清空需求文档选择
  selectedDocumentId.value = undefined
  requirementDocuments.value = []
  
  // 加载该项目的需求文档列表
  if (createForm.project_id) {
    try {
      const res = await requirementDocumentApi.list({ project_id: createForm.project_id })
      requirementDocuments.value = res.data || []
      console.log('加载需求文档列表:', requirementDocuments.value)
    } catch (error) {
      console.error('加载需求文档失败:', error)
      requirementDocuments.value = []
    }
  }
}

// 需求文档变化
const handleDocumentChange = async () => {
  if (!selectedDocumentId.value) {
    return
  }
  
  try {
    // 获取文档详情
    const res = await requirementDocumentApi.get(selectedDocumentId.value)
    const doc = res.data
    
    // 自动填充任务标题和需求描述
    if (!createForm.title) {
      createForm.title = `${doc.title} - 测试用例生成`
    }
    
    // 填充需求描述
    if (doc.extracted_text) {
      createForm.requirement_text = `文档标题: ${doc.title}\n\n文档内容:\n${doc.extracted_text}`
      ElMessage.success('已自动填充需求描述')
    } else {
      ElMessage.warning('该文档暂无提取的文本内容')
    }
  } catch (error) {
    console.error('获取文档详情失败:', error)
    ElMessage.error('获取文档详情失败')
  }
}

// 提交创建
const handleSubmitCreate = async () => {
  if (!createFormRef.value) return
  
  await createFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    createLoading.value = true
    try {
      const res = await generationTaskApi.create(createForm)
      ElMessage.success('任务创建成功，开始生成')
      createDialogVisible.value = false
      await getTaskList()
      
      // 选中新创建的任务
      const newTask = taskList.value.find(t => t.task_id === res.data.task_id)
      if (newTask) {
        currentTask.value = newTask
      }
      
      // 开始轮询
      startPolling()
    } catch (error) {
      ElMessage.error('创建任务失败')
    } finally {
      createLoading.value = false
    }
  })
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
  
  await saveFormRef.value.validate(async (valid) => {
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

// 导出
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

// 开始轮询
const startPolling = () => {
  if (pollingTimer) return
  
  pollingTimer = window.setInterval(() => {
    getTaskList()
  }, 3000)
}

// 停止轮询
const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
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
  getTaskList()
  getProjectList()
  getModelConfigs()
  getPromptConfigs()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped lang="scss">
.case-generation-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .header-actions {
    display: flex;
    gap: 10px;
  }
}

.task-list-header {
  padding: 10px 12px;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 10px;
}

.task-item {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  margin-bottom: 10px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  transition: all 0.3s;

  &:hover {
    border-color: #409eff;
    background-color: #f0f9ff;
    
    .task-actions {
      opacity: 1;
    }
  }

  &.active {
    border-color: #409eff;
    background-color: #ecf5ff;
  }
  
  .task-checkbox {
    flex-shrink: 0;
    margin-right: 10px;
    padding-top: 2px;
  }
  
  .task-content {
    flex: 1;
    min-width: 0;
    cursor: pointer;
  }

  .task-title {
    font-weight: 500;
    margin-bottom: 8px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    padding-right: 5px;
  }

  .task-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    color: #909399;

    .task-time {
      margin-left: 10px;
    }
  }
  
  .task-actions {
    flex-shrink: 0;
    margin-left: 10px;
    opacity: 0;
    transition: opacity 0.3s;
  }
}

.requirement-text,
.log-content,
.stream-content {
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 500px;
  overflow-y: auto;
}

.generated-content,
.final-content {
  padding: 20px;
  background-color: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  max-height: 600px;
  overflow-y: auto;
  overflow-x: auto;
}

.review-content {
  padding: 20px;
  padding-left: 22px;
  background-color: #f9fafb;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  max-height: 400px;
  overflow-y: auto;
  overflow-x: hidden;
  font-size: 14px;
  line-height: 1.8;
  color: #333;
  word-wrap: break-word;
  word-break: break-word;
}

.empty-content {
  padding: 40px;
  text-align: center;
  color: #909399;
  font-size: 14px;
}

.stream-output {
  margin-top: 20px;
  
  .stream-content {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.6;
  }
}

.generating-status,
.error-status {
  text-align: center;
  padding: 40px 20px;

  .el-icon {
    font-size: 48px;
    margin-bottom: 15px;
  }

  span {
    display: block;
    font-size: 16px;
    color: #606266;
  }
}

.action-buttons {
  margin-top: 20px;
  text-align: center;
}

// 区块标题样式
.section-title {
  font-size: 16px;
  font-weight: bold;
  padding: 12px 16px;
  margin: 20px 0 15px 0;
  border-radius: 4px;
  border-left: 4px solid;
  background-color: #f5f7fa;
}

.writer-title {
  color: #409eff;
  border-left-color: #409eff;
  background-color: #ecf5ff;
}

.reviewer-title {
  color: #e6a23c;
  border-left-color: #e6a23c;
  background-color: #fdf6ec;
}

.final-title {
  color: #67c23a;
  border-left-color: #67c23a;
  background-color: #f0f9ff;
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

// 表格样式 - 独立出来确保优先级
.generated-content,
.final-content {
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
        
        // 处理长文本
        word-break: break-word;
        white-space: pre-wrap;
        overflow-wrap: break-word;
      }
    }
  }
}
</style>
