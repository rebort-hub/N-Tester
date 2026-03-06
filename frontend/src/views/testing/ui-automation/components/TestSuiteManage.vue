<template>
  <div class="test-suite-manage">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索测试套件"
        style="width: 250px"
        clearable
        @clear="loadTestSuiteList"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button type="primary" :icon="Plus" @click="handleCreate">新建测试套件</el-button>
      <el-button type="success" :icon="VideoPlay" @click="handleBatchExecute">批量执行</el-button>
      <el-button type="danger" :icon="Delete" @click="handleBatchDelete" :disabled="selectedTestSuites.length === 0">批量删除</el-button>
      <el-button :icon="Refresh" @click="loadTestSuiteList">刷新</el-button>
    </div>

    <!-- 测试套件列表 -->
    <el-table
      :data="testSuiteList"
      v-loading="loading"
      border
      stripe
      style="margin-top: 15px"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="套件名称" min-width="200" />
      <el-table-column prop="engine_type" label="执行引擎" width="120">
        <template #default="{ row }">
          <el-tag>{{ row.engine_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="browser_type" label="浏览器" width="100">
        <template #default="{ row }">
          <el-tag type="success">{{ row.browser_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="headless" label="无头模式" width="100">
        <template #default="{ row }">
          <el-tag :type="row.headless ? 'info' : 'warning'">
            {{ row.headless ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="parallel" label="并行执行" width="100">
        <template #default="{ row }">
          <el-tag :type="row.parallel ? 'success' : 'info'">
            {{ row.parallel ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="max_workers" label="最大并行数" width="110" />
      <el-table-column prop="test_case_count" label="用例数量" width="100">
        <template #default="{ row }">
          <el-tag type="primary">{{ row.test_case_count || 0 }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="300" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="handleManageCases(row)">管理用例</el-button>
          <el-button type="success" size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button type="warning" size="small" @click="handleExecute(row)">执行</el-button>
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
      @size-change="loadTestSuiteList"
      @current-change="loadTestSuiteList"
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
        <el-form-item label="套件名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入套件名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="执行引擎" prop="engine_type">
          <el-radio-group v-model="formData.engine_type">
            <el-radio label="playwright">Playwright</el-radio>
            <el-radio label="selenium">Selenium</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="浏览器类型" prop="browser_type">
          <el-radio-group v-model="formData.browser_type">
            <el-radio label="chromium">Chromium</el-radio>
            <el-radio label="firefox">Firefox</el-radio>
            <el-radio label="webkit">WebKit</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="无头模式">
          <el-switch v-model="formData.headless" />
          <span style="margin-left: 10px; color: #909399; font-size: 12px">
            无头模式下浏览器不显示界面
          </span>
        </el-form-item>
        <el-form-item label="并行执行">
          <el-switch v-model="formData.parallel" />
          <span style="margin-left: 10px; color: #909399; font-size: 12px">
            并行执行可以提高执行效率
          </span>
        </el-form-item>
        <el-form-item label="最大并行数" v-if="formData.parallel">
          <el-input-number v-model="formData.max_workers" :min="1" :max="10" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 管理用例对话框 -->
    <el-dialog
      v-model="casesDialogVisible"
      :title="`管理测试用例 - ${currentSuiteName}`"
      width="1200px"
      :close-on-click-modal="false"
    >
      <div class="cases-manage-container">
        <!-- 左侧：可用用例列表 -->
        <div class="available-cases">
          <div class="section-header">
            <span>可用测试用例</span>
            <el-input
              v-model="caseSearchKeyword"
              placeholder="搜索用例"
              size="small"
              style="width: 200px"
              clearable
            />
          </div>
          <el-table
            :data="filteredAvailableCases"
            height="400"
            @selection-change="handleAvailableCasesSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="name" label="用例名称" min-width="150" show-overflow-tooltip />
            <el-table-column prop="priority" label="优先级" width="80">
              <template #default="{ row }">
                <el-tag :type="getPriorityTagType(row.priority)" size="small">
                  {{ getPriorityName(row.priority) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="steps_count" label="步骤数" width="80" align="center">
              <template #default="{ row }">
                <el-tag type="info" size="small">{{ row.steps_count || 0 }}</el-tag>
              </template>
            </el-table-column>
            <template #empty>
              <div class="empty-state">
                <el-icon size="48" color="#c0c4cc">
                  <Search />
                </el-icon>
                <p>暂无可用的测试用例</p>
                <p class="empty-tip">请检查项目中是否已创建测试用例</p>
              </div>
            </template>
          </el-table>
          <div class="button-area">
            <el-button type="primary" :icon="Right" @click="handleAddCases" :disabled="selectedAvailableCases.length === 0">
              添加选中用例
            </el-button>
          </div>
        </div>

        <!-- 右侧：已关联用例列表 -->
        <div class="linked-cases">
          <div class="section-header">
            <span>已关联测试用例</span>
            <el-button type="danger" size="small" :icon="Delete" @click="handleRemoveSelectedCases" :disabled="selectedLinkedCases.length === 0">
              移除选中
            </el-button>
          </div>
          <el-table
            :data="linkedCasesList"
            height="400"
            @selection-change="handleLinkedCasesSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="name" label="用例名称" min-width="150" show-overflow-tooltip />
            <el-table-column prop="priority" label="优先级" width="80">
              <template #default="{ row }">
                <el-tag :type="getPriorityTagType(row.priority)" size="small">
                  {{ getPriorityName(row.priority) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="steps_count" label="步骤数" width="80" align="center">
              <template #default="{ row }">
                <el-tag type="info" size="small">{{ row.steps_count || 0 }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row, $index }">
                <el-button link type="danger" size="small" @click="handleRemoveCase($index)">移除</el-button>
              </template>
            </el-table-column>
            <template #empty>
              <div class="empty-state">
                <el-icon size="48" color="#c0c4cc">
                  <Box />
                </el-icon>
                <p>暂无关联的测试用例</p>
                <p class="empty-tip">请从左侧选择用例进行添加</p>
              </div>
            </template>
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="casesDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveCases" :loading="casesSubmitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 执行配置对话框 -->
    <el-dialog
      v-model="executeDialogVisible"
      :title="`执行测试套件 - ${currentSuiteName}`"
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
        <el-form-item label="并行执行">
          <el-switch v-model="executeForm.parallel" />
          <span style="margin-left: 10px; color: #909399; font-size: 12px">
            并行执行可以提高执行效率
          </span>
        </el-form-item>
        <el-form-item label="最大并行数" v-if="executeForm.parallel">
          <el-input-number v-model="executeForm.max_workers" :min="1" :max="10" style="width: 100%" />
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

    <!-- 批量执行配置对话框 -->
    <el-dialog
      v-model="batchExecuteDialogVisible"
      :title="currentSuiteName"
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import { Plus, VideoPlay, Refresh, Search, Right, Delete, Box } from '@element-plus/icons-vue'
import { uiTestSuiteApi, uiTestCaseApi } from '/@/api/v1/ui_automation'
import { formatDateTime } from '/@/utils/formatTime'
import ExecutionMonitor from './ExecutionMonitor.vue'

const props = defineProps<{
  uiProjectId: number
}>()

// 搜索
const searchKeyword = ref('')

// 表格数据
const testSuiteList = ref([])
const loading = ref(false)
const selectedTestSuites = ref([])

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('新建测试套件')
const formRef = ref()
const submitLoading = ref(false)

// 表单数据
const formData = reactive({
  id: null,
  ui_project_id: props.uiProjectId,
  name: '',
  description: '',
  engine_type: 'playwright',
  browser_type: 'chromium',
  headless: true,
  parallel: false,
  max_workers: 1,
  test_case_ids: []
})

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入套件名称', trigger: 'blur' }],
  engine_type: [{ required: true, message: '请选择执行引擎', trigger: 'change' }],
  browser_type: [{ required: true, message: '请选择浏览器类型', trigger: 'change' }]
}

// 用例管理对话框
const casesDialogVisible = ref(false)
const currentSuiteId = ref<number | null>(null)
const currentSuiteName = ref('')
const availableCasesList = ref([])
const linkedCasesList = ref([])
const caseSearchKeyword = ref('')
const selectedAvailableCases = ref([])
const selectedLinkedCases = ref([])
const casesSubmitLoading = ref(false)

// 过滤后的可用用例
const filteredAvailableCases = computed(() => {
  if (!caseSearchKeyword.value) {
    return availableCasesList.value
  }
  return availableCasesList.value.filter((item: any) =>
    item.name.toLowerCase().includes(caseSearchKeyword.value.toLowerCase())
  )
})

// 执行监控
const monitorDialogVisible = ref(false)
const currentExecutionId = ref<number | null>(null)

// 执行配置
const executeDialogVisible = ref(false)
const executeLoading = ref(false)
const currentExecuteSuiteId = ref<number | null>(null)
const executeForm = reactive({
  engine_type: 'playwright',
  browser_type: 'chromium',
  channel: 'chrome',  // 默认使用系统 Chrome
  headless: true,
  parallel: false,
  max_workers: 1,
  timeout: 30000
})

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

// 加载测试套件列表
const loadTestSuiteList = async () => {
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
    const res = await uiTestSuiteApi.list(params)
    testSuiteList.value = res.data.items || []
    pagination.total = res.data.total || 0
  } catch (error) {
    ElMessage.error('加载测试套件列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadTestSuiteList()
}

// 选择变化
const handleSelectionChange = (selection: any[]) => {
  selectedTestSuites.value = selection
}

// 新建
const handleCreate = () => {
  dialogTitle.value = '新建测试套件'
  Object.assign(formData, {
    id: null,
    ui_project_id: props.uiProjectId,
    name: '',
    description: '',
    engine_type: 'playwright',
    browser_type: 'chromium',
    headless: true,
    parallel: false,
    max_workers: 1,
    test_case_ids: []
  })
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row: any) => {
  dialogTitle.value = '编辑测试套件'
  Object.assign(formData, row)
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  await formRef.value.validate()
  submitLoading.value = true
  try {
    if (formData.id) {
      await uiTestSuiteApi.update(formData.id, formData)
      ElMessage.success('更新成功')
    } else {
      await uiTestSuiteApi.create(formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadTestSuiteList()
  } catch (error) {
    ElMessage.error('操作失败')
    console.error(error)
  } finally {
    submitLoading.value = false
  }
}

// 删除
const handleDelete = (row: any) => {
  ElMessageBox.confirm('确定要删除该测试套件吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await uiTestSuiteApi.delete(row.id)
      ElMessage.success('删除成功')
      loadTestSuiteList()
    } catch (error) {
      ElMessage.error('删除失败')
      console.error(error)
    }
  })
}

// 管理用例
const handleManageCases = async (row: any) => {
  currentSuiteId.value = row.id
  currentSuiteName.value = row.name
  casesDialogVisible.value = true
  
  // 加载可用用例列表
  try {
    const res = await uiTestCaseApi.list({
      ui_project_id: props.uiProjectId,
      page: 1,
      page_size: 1000
    })
    availableCasesList.value = res.data.items || []
  } catch (error) {
    ElMessage.error('加载用例列表失败')
    console.error(error)
  }
  
  // 加载已关联用例列表（从详情API获取）
  try {
    const detailRes = await uiTestSuiteApi.get(row.id)
    linkedCasesList.value = detailRes.data.test_cases || []
  } catch (error) {
    ElMessage.error('加载已关联用例失败')
    console.error(error)
    linkedCasesList.value = []
  }
}

// 可用用例选择变化
const handleAvailableCasesSelectionChange = (selection: any[]) => {
  selectedAvailableCases.value = selection
}

// 已关联用例选择变化
const handleLinkedCasesSelectionChange = (selection: any[]) => {
  selectedLinkedCases.value = selection
}

// 添加用例
const handleAddCases = () => {
  selectedAvailableCases.value.forEach((testCase: any) => {
    const exists = linkedCasesList.value.some((item: any) => item.id === testCase.id)
    if (!exists) {
      linkedCasesList.value.push(testCase)
    }
  })
  selectedAvailableCases.value = []
}

// 移除单个用例
const handleRemoveCase = (index: number) => {
  linkedCasesList.value.splice(index, 1)
}

// 移除选中用例
const handleRemoveSelectedCases = () => {
  const selectedIds = selectedLinkedCases.value.map((item: any) => item.id)
  linkedCasesList.value = linkedCasesList.value.filter(
    (item: any) => !selectedIds.includes(item.id)
  )
  selectedLinkedCases.value = []
}

// 保存用例关联
const handleSaveCases = async () => {
  casesSubmitLoading.value = true
  try {
    // 去重：确保没有重复的用例ID
    const test_case_ids = [...new Set(linkedCasesList.value.map((item: any) => item.id))]
    
    console.log('保存用例关联:', {
      suite_id: currentSuiteId.value,
      test_case_ids: test_case_ids,
      count: test_case_ids.length
    })
    
    await uiTestSuiteApi.update(currentSuiteId.value, { test_case_ids })
    ElMessage.success('保存成功')
    casesDialogVisible.value = false
    loadTestSuiteList()
  } catch (error) {
    ElMessage.error('保存失败')
    console.error(error)
  } finally {
    casesSubmitLoading.value = false
  }
}

// 执行测试套件
const handleExecute = (row: any) => {
  currentExecuteSuiteId.value = row.id
  currentSuiteName.value = row.name
  // 使用套件的默认配置
  executeForm.engine_type = row.engine_type || 'playwright'
  executeForm.browser_type = row.browser_type || 'chromium'
  executeForm.headless = row.headless !== undefined ? row.headless : true
  executeForm.parallel = row.parallel !== undefined ? row.parallel : false
  executeForm.max_workers = row.max_workers || 1
  executeDialogVisible.value = true
}

// 提交执行
const handleExecuteSubmit = async () => {
  executeLoading.value = true
  try {
    const res = await uiTestSuiteApi.execute(currentExecuteSuiteId.value, executeForm)
    currentExecutionId.value = res.data.execution_id
    ElMessage.success('测试套件开始执行')
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
  if (selectedTestSuites.value.length === 0) {
    ElMessage.warning('请先选择要执行的测试套件')
    return
  }
  
  // 打开批量执行配置对话框
  currentSuiteName.value = `批量执行 (${selectedTestSuites.value.length} 个套件)`
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
    // 获取选中的测试套件ID
    const suite_ids = selectedTestSuites.value.map((item: any) => item.id)
    
    // 调用批量执行API
    const res = await uiTestSuiteApi.batchExecute({
      suite_ids,
      ...batchExecuteForm
    })
    
    ElMessage.success(`开始批量执行 ${suite_ids.length} 个测试套件`)
    batchExecuteDialogVisible.value = false
    
    // 显示执行结果信息
    ElMessageBox.alert(
      `已提交 ${suite_ids.length} 个测试套件执行任务，请在执行历史记录中查看执行状态`,
      '批量执行已启动',
      {
        confirmButtonText: '确定',
        type: 'success'
      }
    )
    
    // 刷新列表
    loadTestSuiteList()
  } catch (error) {
    ElMessage.error('批量执行失败')
    console.error(error)
  } finally {
    batchExecuteLoading.value = false
  }
}

// 批量删除
const handleBatchDelete = () => {
  if (selectedTestSuites.value.length === 0) {
    ElMessage.warning('请先选择要删除的测试套件')
    return
  }
  
  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedTestSuites.value.length} 个测试套件吗？此操作不可恢复。`,
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
      text: `正在删除 ${selectedTestSuites.value.length} 个测试套件...`,
      background: 'rgba(0, 0, 0, 0.7)'
    })
    
    try {
      let successCount = 0
      let failCount = 0
      const errors: string[] = []
      
      // 逐个删除
      for (const suite of selectedTestSuites.value) {
        try {
          await uiTestSuiteApi.delete(suite.id)
          successCount++
        } catch (error: any) {
          failCount++
          errors.push(`${suite.name}: ${error?.response?.data?.detail || '删除失败'}`)
        }
      }
      
      loading.close()
      
      if (failCount === 0) {
        ElMessage.success(`成功删除 ${successCount} 个测试套件`)
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
      loadTestSuiteList()
      // 清空选择
      selectedTestSuites.value = []
    } catch (error) {
      loading.close()
      ElMessage.error('批量删除失败')
      console.error(error)
    }
  })
}

// 初始化
onMounted(() => {
  loadTestSuiteList()
})

// 暴露方法给父组件
defineExpose({
  handleBatchExecute
})
</script>

<style scoped lang="scss">
.test-suite-manage {
  .toolbar {
    display: flex;
    gap: 10px;
    align-items: center;
  }

  .cases-manage-container {
    display: flex;
    gap: 20px;
    height: 500px;
    overflow: hidden;

    .available-cases,
    .linked-cases {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;

      .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        font-weight: 600;
        font-size: 14px;
        flex-shrink: 0;
        color: var(--el-text-color-primary);
        padding-bottom: 8px;
        border-bottom: 1px solid var(--el-border-color-light);
      }
      
      // 表格容器样式
      :deep(.el-table) {
        flex: 1;
        min-height: 0;
        
        // 当表格为空时的样式
        .el-table__empty-block {
          min-height: 100px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .el-table__empty-text {
          color: var(--el-text-color-placeholder);
          font-size: 14px;
        }
      }
      
      // 按钮区域样式
      .button-area {
        margin-top: 15px;
        text-align: center;
        flex-shrink: 0;
        padding-top: 12px;
        border-top: 1px solid var(--el-border-color-lighter);
      }
    }

    // 左侧可用用例区域特殊样式
    .available-cases {
      .button-area {
        .el-button {
          width: 140px;
        }
      }
    }

    // 右侧已关联用例区域特殊样式
    .linked-cases {
      .section-header {
        .el-button {
          margin-left: 10px;
        }
      }
    }
  }

  // 空状态样式
  .empty-state {
    text-align: center;
    padding: 40px 20px;
    color: var(--el-text-color-placeholder);

    p {
      margin: 10px 0 5px 0;
      font-size: 14px;
      color: var(--el-text-color-regular);
      
      &.empty-tip {
        font-size: 12px;
        color: var(--el-text-color-placeholder);
      }
    }
  }
}
</style>
