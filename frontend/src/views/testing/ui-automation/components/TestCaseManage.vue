<template>
  <div class="test-case-manage">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索测试用例"
        style="width: 250px"
        clearable
        @clear="loadTestCaseList"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="searchPriority" placeholder="优先级" clearable style="width: 120px" @change="handleSearch">
        <el-option label="高" value="high" />
        <el-option label="中" value="medium" />
        <el-option label="低" value="low" />
      </el-select>
      <el-button type="primary" :icon="Plus" @click="handleCreate">新建测试用例</el-button>
      <el-button type="success" :icon="VideoPlay" @click="handleBatchExecute">批量执行</el-button>
      <el-button type="danger" :icon="Delete" @click="handleBatchDelete" :disabled="selectedTestCases.length === 0">批量删除</el-button>
      <el-button :icon="Refresh" @click="loadTestCaseList">刷新</el-button>
    </div>

    <!-- 测试用例列表 -->
    <el-table
      :data="testCaseList"
      v-loading="loading"
      border
      stripe
      style="margin-top: 15px"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="用例名称" min-width="200" />
      <el-table-column prop="priority" label="优先级" width="100">
        <template #default="{ row }">
          <el-tag :type="getPriorityTagType(row.priority)">
            {{ getPriorityName(row.priority) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="tags" label="标签" min-width="150">
        <template #default="{ row }">
          <el-tag v-for="tag in row.tags" :key="tag" size="small" style="margin-right: 5px">
            {{ tag }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="steps_count" label="步骤数" width="100" align="center">
        <template #default="{ row }">
          <el-tag type="info" size="small">{{ row.steps_count || 0 }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="400" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="handleEditSteps(row)">编辑步骤</el-button>
          <el-button type="success" size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button type="warning" size="small" @click="handleExecute(row)">执行</el-button>
          <el-button type="info" size="small" @click="handleGenerateCode(row)">生成代码</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.page_size"
      :total="pagination.total"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next"
      @size-change="loadTestCaseList"
      @current-change="loadTestCaseList"
      style="margin-top: 15px; justify-content: flex-end"
    />

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="120px">
        <el-form-item label="用例名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入用例名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-radio-group v-model="formData.priority">
            <el-radio label="high">高</el-radio>
            <el-radio label="medium">中</el-radio>
            <el-radio label="low">低</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="formData.tags"
            multiple
            filterable
            allow-create
            placeholder="请选择或输入标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in commonTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="前置条件">
          <el-input v-model="formData.preconditions" type="textarea" :rows="3" placeholder="请输入前置条件" />
        </el-form-item>
        <el-form-item label="预期结果">
          <el-input v-model="formData.expected_result" type="textarea" :rows="3" placeholder="请输入预期结果" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 步骤编辑器对话框 -->
    <el-dialog
      v-model="stepsDialogVisible"
      :title="`编辑测试步骤 - ${currentTestCaseName}`"
      width="1200px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <TestStepEditor
        v-if="stepsDialogVisible"
        :test-case-id="currentTestCaseId"
        :ui-project-id="uiProjectId"
        @close="stepsDialogVisible = false"
      />
    </el-dialog>

    <!-- 执行配置对话框 -->
    <el-dialog
      v-model="executeDialogVisible"
      title="执行测试用例"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="executeForm" label-width="120px">
        <el-form-item label="执行引擎">
          <el-radio-group v-model="executeForm.engine_type">
            <el-radio label="playwright">Playwright</el-radio>
            <el-radio label="selenium">Selenium</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="浏览器类型">
          <el-radio-group v-model="executeForm.browser_type">
            <el-radio label="chromium">Chromium</el-radio>
            <el-radio label="firefox">Firefox</el-radio>
            <el-radio label="webkit">WebKit</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="浏览器渠道" v-if="executeForm.browser_type === 'chromium'">
          <el-select v-model="executeForm.channel" placeholder="选择浏览器" style="width: 100%" clearable>
            <el-option label="Playwright Chromium（需下载）" :value="null" />
            <el-option label="系统 Chrome" value="chrome" />
            <el-option label="系统 Edge" value="msedge" />
          </el-select>
          <div style="margin-top: 5px; color: #909399; font-size: 12px">
            选择系统浏览器可避免下载 Playwright 浏览器
          </div>
        </el-form-item>
        <el-form-item label="无头模式">
          <el-switch v-model="executeForm.headless" />
          <span style="margin-left: 10px; color: #909399; font-size: 12px">
            无头模式下浏览器不显示界面
          </span>
        </el-form-item>
        <el-form-item label="超时时间(ms)">
          <el-input-number v-model="executeForm.timeout" :min="5000" :max="300000" :step="5000" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="executeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleExecuteSubmit" :loading="executeLoading">开始执行</el-button>
      </template>
    </el-dialog>

    <!-- 批量执行配置对话框 -->
    <el-dialog
      v-model="batchExecuteDialogVisible"
      :title="currentTestCaseName"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="batchExecuteForm" label-width="120px">
        <el-form-item label="执行引擎">
          <el-radio-group v-model="batchExecuteForm.engine_type">
            <el-radio label="playwright">Playwright</el-radio>
            <el-radio label="selenium">Selenium</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="浏览器类型">
          <el-radio-group v-model="batchExecuteForm.browser_type">
            <el-radio label="chromium">Chromium</el-radio>
            <el-radio label="firefox">Firefox</el-radio>
            <el-radio label="webkit">WebKit</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="浏览器渠道" v-if="batchExecuteForm.browser_type === 'chromium'">
          <el-select v-model="batchExecuteForm.channel" placeholder="选择浏览器" style="width: 100%" clearable>
            <el-option label="Playwright Chromium（需下载）" :value="null" />
            <el-option label="系统 Chrome" value="chrome" />
            <el-option label="系统 Edge" value="msedge" />
          </el-select>
          <div style="margin-top: 5px; color: #909399; font-size: 12px">
            选择系统浏览器可避免下载 Playwright 浏览器
          </div>
        </el-form-item>
        <el-form-item label="无头模式">
          <el-switch v-model="batchExecuteForm.headless" />
          <span style="margin-left: 10px; color: #909399; font-size: 12px">
            无头模式下浏览器不显示界面
          </span>
        </el-form-item>
        <el-form-item label="并行执行">
          <el-switch v-model="batchExecuteForm.parallel" />
          <span style="margin-left: 10px; color: #909399; font-size: 12px">
            并行执行可以提高执行效率
          </span>
        </el-form-item>
        <el-form-item label="最大并行数" v-if="batchExecuteForm.parallel">
          <el-input-number v-model="batchExecuteForm.max_workers" :min="1" :max="10" style="width: 100%" />
        </el-form-item>
        <el-form-item label="超时时间(ms)">
          <el-input-number v-model="batchExecuteForm.timeout" :min="5000" :max="300000" :step="5000" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchExecuteDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchExecuteSubmit" :loading="batchExecuteLoading">开始执行</el-button>
      </template>
    </el-dialog>

    <!-- 代码生成对话框 -->
    <el-dialog
      v-model="codeDialogVisible"
      title="生成测试用例代码"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="codeForm" label-width="120px">
        <el-form-item label="编程语言">
          <el-radio-group v-model="codeForm.language">
            <el-radio label="javascript">JavaScript</el-radio>
            <el-radio label="python">Python</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="测试框架">
          <el-radio-group v-model="codeForm.framework">
            <el-radio label="playwright">Playwright</el-radio>
            <el-radio label="selenium">Selenium</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="包含注释">
          <el-switch v-model="codeForm.include_comments" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="codeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleGenerateCodeSubmit" :loading="codeLoading">生成代码</el-button>
      </template>
    </el-dialog>

    <!-- 代码预览对话框 -->
    <el-dialog
      v-model="codePreviewVisible"
      :title="`代码预览 - ${currentTestCaseName}`"
      width="900px"
      :close-on-click-modal="false"
    >
      <div class="code-preview-container">
        <div class="code-actions">
          <el-button type="primary" size="small" :icon="CopyDocument" @click="handleCopyCode">复制代码</el-button>
          <el-button type="success" size="small" :icon="Download" @click="handleDownloadCode">下载代码</el-button>
        </div>
        <div class="code-content">
          <pre><code>{{ generatedCode }}</code></pre>
        </div>
      </div>
    </el-dialog>

    <!-- 执行监控对话框 -->
    <el-dialog
      v-model="monitorDialogVisible"
      title="执行监控"
      width="900px"
      :close-on-click-modal="false"
    >
      <ExecutionMonitor
        v-if="monitorDialogVisible"
        :execution-id="currentExecutionId"
        @close="monitorDialogVisible = false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import { Plus, VideoPlay, Refresh, Search, CopyDocument, Download, Delete } from '@element-plus/icons-vue'
import { uiTestCaseApi, uiTestStepApi } from '/@/api/v1/ui_automation'
import { formatDateTime } from '/@/utils/formatTime'
import TestStepEditor from './TestStepEditor.vue'
import ExecutionMonitor from './ExecutionMonitor.vue'

const props = defineProps<{
  uiProjectId: number
}>()

// 搜索
const searchKeyword = ref('')
const searchPriority = ref('')

// 表格数据
const testCaseList = ref([])
const loading = ref(false)
const selectedTestCases = ref([])

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 常用标签
const commonTags = ref(['冒烟测试', '回归测试', '功能测试', '性能测试', '兼容性测试'])

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('新建测试用例')
const formRef = ref()
const submitLoading = ref(false)

// 表单数据
const formData = reactive({
  id: null,
  ui_project_id: props.uiProjectId,
  name: '',
  description: '',
  priority: 'medium',
  tags: [],
  preconditions: '',
  expected_result: ''
})

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入用例名称', trigger: 'blur' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }]
}

// 步骤编辑器
const stepsDialogVisible = ref(false)
const currentTestCaseId = ref<number | null>(null)
const currentTestCaseName = ref('')

// 执行配置
const executeDialogVisible = ref(false)
const executeLoading = ref(false)
const currentExecuteTestCaseId = ref<number | null>(null)
const executeForm = reactive({
  engine_type: 'playwright',
  browser_type: 'chromium',
  channel: 'chrome',  // 默认使用系统 Chrome
  headless: true,
  timeout: 30000
})

// 代码生成
const codeDialogVisible = ref(false)
const codeLoading = ref(false)
const currentCodeTestCaseId = ref<number | null>(null)
const codeForm = reactive({
  language: 'javascript',
  framework: 'playwright',
  include_comments: true
})

// 代码预览
const codePreviewVisible = ref(false)
const generatedCode = ref('')

// 执行监控
const monitorDialogVisible = ref(false)
const currentExecutionId = ref<number | null>(null)

// 获取优先级标签类型
const getPriorityTagType = (priority: string) => {
  const types: any = {
    high: 'danger',
    medium: 'warning',
    low: 'info'
  }
  return types[priority] || ''
}

// 获取优先级名称
const getPriorityName = (priority: string) => {
  const names: any = {
    high: '高',
    medium: '中',
    low: '低'
  }
  return names[priority] || priority
}

// 加载测试用例列表
const loadTestCaseList = async () => {
  loading.value = true
  try {
    const params: any = {
      ui_project_id: props.uiProjectId,
      page: pagination.page,
      page_size: pagination.page_size
    }
    if (searchKeyword.value) {
      params.name = searchKeyword.value
    }
    if (searchPriority.value) {
      params.priority = searchPriority.value
    }
    const res = await uiTestCaseApi.list(params)
    testCaseList.value = res.data.items || []
    pagination.total = res.data.total || 0
  } catch (error) {
    ElMessage.error('加载测试用例列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadTestCaseList()
}

// 选择变化
const handleSelectionChange = (selection: any[]) => {
  selectedTestCases.value = selection
}

// 新建
const handleCreate = () => {
  dialogTitle.value = '新建测试用例'
  Object.assign(formData, {
    id: null,
    ui_project_id: props.uiProjectId,
    name: '',
    description: '',
    priority: 'medium',
    tags: [],
    preconditions: '',
    expected_result: ''
  })
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row: any) => {
  dialogTitle.value = '编辑测试用例'
  Object.assign(formData, {
    ...row,
    tags: row.tags || []
  })
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  await formRef.value.validate()
  submitLoading.value = true
  try {
    if (formData.id) {
      await uiTestCaseApi.update(formData.id, formData)
      ElMessage.success('更新成功')
    } else {
      await uiTestCaseApi.create(formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadTestCaseList()
  } catch (error) {
    ElMessage.error('操作失败')
    console.error(error)
  } finally {
    submitLoading.value = false
  }
}

// 删除
const handleDelete = (row: any) => {
  ElMessageBox.confirm('确定要删除该测试用例吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await uiTestCaseApi.delete(row.id)
      ElMessage.success('删除成功')
      loadTestCaseList()
    } catch (error) {
      ElMessage.error('删除失败')
      console.error(error)
    }
  })
}

// 编辑步骤
const handleEditSteps = (row: any) => {
  currentTestCaseId.value = row.id
  currentTestCaseName.value = row.name
  stepsDialogVisible.value = true
}

// 执行测试用例
const handleExecute = async (row: any) => {
  // 检查测试用例是否有步骤
  try {
    const stepsRes = await uiTestStepApi.listByCase(row.id)
    const steps = stepsRes.data || []
    
    if (steps.length === 0) {
      ElMessageBox.confirm(
        '该测试用例还没有添加测试步骤，是否先去编辑步骤？',
        '提示',
        {
          confirmButtonText: '编辑步骤',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        // 跳转到编辑步骤
        handleEditSteps(row)
      }).catch(() => {
        // 用户取消
      })
      return
    }
  } catch (error) {
    console.error('检查测试步骤失败:', error)
  }
  
  currentExecuteTestCaseId.value = row.id
  currentTestCaseName.value = row.name
  executeDialogVisible.value = true
}

// 提交执行
const handleExecuteSubmit = async () => {
  executeLoading.value = true
  try {
    const res = await uiTestCaseApi.execute(currentExecuteTestCaseId.value, executeForm)
    currentExecutionId.value = res.data.execution_id
    ElMessage.success('测试用例开始执行')
    executeDialogVisible.value = false
    monitorDialogVisible.value = true
  } catch (error) {
    ElMessage.error('执行失败')
    console.error(error)
  } finally {
    executeLoading.value = false
  }
}

// 批量执行
const handleBatchExecute = () => {
  if (selectedTestCases.value.length === 0) {
    ElMessage.warning('请先选择要执行的测试用例')
    return
  }
  
  // 打开批量执行配置对话框
  currentTestCaseName.value = `批量执行 (${selectedTestCases.value.length} 个用例)`
  batchExecuteDialogVisible.value = true
}

// 批量执行配置对话框
const batchExecuteDialogVisible = ref(false)
const batchExecuteLoading = ref(false)
const batchExecuteForm = reactive({
  engine_type: 'playwright',
  browser_type: 'chromium',
  channel: 'chrome',
  headless: true,
  parallel: false,
  max_workers: 1,
  timeout: 30000
})

// 提交批量执行
const handleBatchExecuteSubmit = async () => {
  batchExecuteLoading.value = true
  try {
    // 获取选中的测试用例ID
    const test_case_ids = selectedTestCases.value.map((item: any) => item.id)
    
    // 调用批量执行API
    const res = await uiTestCaseApi.batchExecute({
      ui_project_id: props.uiProjectId,
      test_case_ids,
      ...batchExecuteForm
    })
    
    currentExecutionId.value = res.data.execution_id
    ElMessage.success(`开始批量执行 ${test_case_ids.length} 个测试用例`)
    batchExecuteDialogVisible.value = false
    monitorDialogVisible.value = true
  } catch (error) {
    ElMessage.error('批量执行失败')
    console.error(error)
  } finally {
    batchExecuteLoading.value = false
  }
}

// 批量删除
const handleBatchDelete = () => {
  if (selectedTestCases.value.length === 0) {
    ElMessage.warning('请先选择要删除的测试用例')
    return
  }
  
  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedTestCases.value.length} 个测试用例吗？此操作不可恢复。`,
    '批量删除确认',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
      dangerouslyUseHTMLString: true
    }
  ).then(async () => {
    const loading = ElLoading.service({
      lock: true,
      text: `正在删除 ${selectedTestCases.value.length} 个测试用例...`,
      background: 'rgba(0, 0, 0, 0.7)'
    })
    
    try {
      let successCount = 0
      let failCount = 0
      const errors: string[] = []
      
      // 逐个删除
      for (const testCase of selectedTestCases.value) {
        try {
          await uiTestCaseApi.delete(testCase.id)
          successCount++
        } catch (error: any) {
          failCount++
          errors.push(`${testCase.name}: ${error?.response?.data?.detail || '删除失败'}`)
        }
      }
      
      loading.close()
      
      if (failCount === 0) {
        ElMessage.success(`成功删除 ${successCount} 个测试用例`)
      } else {
        const errorMsg = errors.length > 0 ? `\n失败详情：\n${errors.join('\n')}` : ''
        ElMessageBox.alert(
          `删除完成：成功 ${successCount} 个，失败 ${failCount} 个${errorMsg}`,
          '批量删除结果',
          {
            confirmButtonText: '确定',
            type: failCount > 0 ? 'warning' : 'success'
          }
        )
      }
      
      // 刷新列表
      loadTestCaseList()
      // 清空选择
      selectedTestCases.value = []
    } catch (error) {
      loading.close()
      ElMessage.error('批量删除失败')
      console.error(error)
    }
  })
}

// 生成代码
const handleGenerateCode = (row: any) => {
  currentCodeTestCaseId.value = row.id
  currentTestCaseName.value = row.name
  codeDialogVisible.value = true
}

// 提交代码生成
const handleGenerateCodeSubmit = async () => {
  codeLoading.value = true
  try {
    const res = await uiTestCaseApi.generateCode(currentCodeTestCaseId.value, codeForm)
    generatedCode.value = res.data.code || ''
    codeDialogVisible.value = false
    codePreviewVisible.value = true
    ElMessage.success('代码生成成功')
  } catch (error) {
    ElMessage.error('代码生成失败')
    console.error(error)
  } finally {
    codeLoading.value = false
  }
}

// 复制代码
const handleCopyCode = () => {
  navigator.clipboard.writeText(generatedCode.value).then(() => {
    ElMessage.success('代码已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 下载代码
const handleDownloadCode = () => {
  const blob = new Blob([generatedCode.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const ext = codeForm.language === 'javascript' ? 'js' : 'py'
  a.download = `${currentTestCaseName.value}.${ext}`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('代码已下载')
}

// 初始化
onMounted(() => {
  loadTestCaseList()
})
</script>

<style scoped lang="scss">
.test-case-manage {
  .toolbar {
    display: flex;
    gap: 10px;
    align-items: center;
  }

  .code-preview-container {
    .code-actions {
      margin-bottom: 15px;
      display: flex;
      gap: 10px;
    }

    .code-content {
      pre {
        background-color: #f5f5f5;
        padding: 15px;
        border-radius: 4px;
        overflow-x: auto;
        max-height: 500px;
        margin: 0;

        code {
          font-family: 'Courier New', Courier, monospace;
          font-size: 13px;
          line-height: 1.5;
          color: #333;
        }
      }
    }
  }
}
</style>
