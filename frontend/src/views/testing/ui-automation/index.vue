<template>
  <div class="ui-automation-container">
    <el-card shadow="hover">
      <el-tabs v-model="activeTab" type="card">
        <!-- UI项目管理 Tab -->
        <el-tab-pane label="UI项目管理" name="projects">
          <!-- 搜索栏 -->
          <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="项目名称">
          <el-input v-model="searchForm.name" placeholder="请输入项目名称" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="关联项目">
          <el-select v-model="searchForm.project_id" placeholder="请选择项目" clearable style="width: 200px" @change="handleProjectChange">
            <el-option v-for="item in projectList" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          <el-button type="success" :icon="Plus" @click="handleCreate">新建UI项目</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="项目名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="base_url" label="基础URL" min-width="200" show-overflow-tooltip />
        <el-table-column prop="browser_type" label="浏览器" width="100">
          <template #default="{ row }">
            <el-tag :type="getBrowserTagType(row.browser_type)">{{ getBrowserName(row.browser_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="viewport_width" label="视口宽度" width="100" />
        <el-table-column prop="viewport_height" label="视口高度" width="100" />
        <el-table-column prop="timeout" label="超时(ms)" width="100" />
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.creation_date) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleManage(row)">管理</el-button>
            <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="primary" size="small" @click="handleGenerateCode(row)">生成代码</el-button>
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
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        style="margin-top: 20px; justify-content: flex-end"
      />
        </el-tab-pane>

        <!-- 浏览器检查 Tab -->
        <el-tab-pane label="浏览器检查" name="browser-check">
          <browser-check />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="120px">
        <el-form-item label="关联项目" prop="project_id">
          <el-select v-model="formData.project_id" placeholder="请选择项目" style="width: 100%">
            <el-option v-for="item in projectList" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="基础URL">
          <el-input v-model="formData.base_url" placeholder="https://example.com" />
        </el-form-item>
        <el-form-item label="浏览器类型" prop="browser_type">
          <el-select v-model="formData.browser_type" placeholder="请选择浏览器" style="width: 100%">
            <el-option label="Chromium" value="chromium" />
            <el-option label="Firefox" value="firefox" />
            <el-option label="WebKit" value="webkit" />
          </el-select>
        </el-form-item>
        <el-form-item label="视口宽度" prop="viewport_width">
          <el-input-number v-model="formData.viewport_width" :min="800" :max="3840" style="width: 100%" />
        </el-form-item>
        <el-form-item label="视口高度" prop="viewport_height">
          <el-input-number v-model="formData.viewport_height" :min="600" :max="2160" style="width: 100%" />
        </el-form-item>
        <el-form-item label="超时时间(ms)" prop="timeout">
          <el-input-number v-model="formData.timeout" :min="1000" :max="300000" :step="1000" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 代码生成对话框 -->
    <el-dialog
      v-model="codeDialogVisible"
      title="生成项目代码"
      width="800px"
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
      title="生成的代码"
      width="900px"
      :close-on-click-modal="false"
    >
      <el-tabs v-model="activeCodeTab">
        <el-tab-pane v-for="file in generatedFiles" :key="file.filename" :label="file.filename" :name="file.filename">
          <div class="code-preview">
            <el-button type="primary" size="small" @click="handleCopyCode(file.content)" style="margin-bottom: 10px">
              复制代码
            </el-button>
            <pre><code>{{ file.content }}</code></pre>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import { useUiAutomationApi } from '/@/api/v1/ui_automation'
import { getProjectList } from '/@/api/v1/project'
import { useRouter } from 'vue-router'
import { formatDateTime } from '/@/utils/formatTime'
import BrowserCheck from './browser-check.vue'

const { uiProjectApi } = useUiAutomationApi()

// 定义组件名称
defineOptions({
  name: 'UIAutomationIndex'
})

const router = useRouter()

// Tab 切换
const activeTab = ref('projects')

// 搜索表单
const searchForm = reactive({
  name: '',
  project_id: null
})

// 表格数据
const tableData = ref([])
const loading = ref(false)

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 项目列表（用于下拉选择）
const projectList = ref([])

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('新建UI项目')
const formRef = ref()
const submitLoading = ref(false)

// 表单数据
const formData = reactive({
  id: null,
  project_id: null,
  name: '',
  description: '',
  base_url: '',
  browser_type: 'chromium',
  viewport_width: 1920,
  viewport_height: 1080,
  timeout: 30000
})

// 表单验证规则
const formRules = {
  project_id: [{ required: true, message: '请选择关联项目', trigger: 'change' }],
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  browser_type: [{ required: true, message: '请选择浏览器类型', trigger: 'change' }],
  viewport_width: [{ required: true, message: '请输入视口宽度', trigger: 'blur' }],
  viewport_height: [{ required: true, message: '请输入视口高度', trigger: 'blur' }],
  timeout: [{ required: true, message: '请输入超时时间', trigger: 'blur' }]
}

// 代码生成
const codeDialogVisible = ref(false)
const codeLoading = ref(false)
const currentProjectId = ref(null)
const codeForm = reactive({
  language: 'javascript',
  framework: 'playwright',
  include_comments: true
})

// 代码预览
const codePreviewVisible = ref(false)
const activeCodeTab = ref('')
const generatedFiles = ref([])

// 获取浏览器标签类型
const getBrowserTagType = (browser: string) => {
  const types: any = {
    chromium: 'success',
    firefox: 'warning',
    webkit: 'info'
  }
  return types[browser] || ''
}

// 获取浏览器名称
const getBrowserName = (browser: string) => {
  const names: any = {
    chromium: 'Chromium',
    firefox: 'Firefox',
    webkit: 'WebKit'
  }
  return names[browser] || browser
}

// 加载项目列表（用于下拉选择）
const loadProjectList = async () => {
  try {
    const res = await getProjectList({ page: 1, page_size: 100 })
    projectList.value = res.data.items || []
    
    // 如果有项目且searchForm.project_id为空，默认选择第一个项目
    if (projectList.value.length > 0 && !searchForm.project_id) {
      searchForm.project_id = projectList.value[0].id
    }
  } catch (error) {
    console.error('加载项目列表失败:', error)
    ElMessage.error('加载项目列表失败')
  }
}

// 加载表格数据
const loadTableData = async () => {
  // 如果没有选择项目，提示用户
  if (!searchForm.project_id) {
    ElMessage.warning('请先选择关联项目')
    return
  }
  
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      project_id: searchForm.project_id,
      name: searchForm.name || undefined
    }
    const res = await uiProjectApi.list(params)
    tableData.value = res.data.items || []
    pagination.total = res.data.total || 0
  } catch (error) {
    ElMessage.error('加载数据失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadTableData()
}

// 项目改变
const handleProjectChange = () => {
  pagination.page = 1
  searchForm.name = ''
  loadTableData()
}

// 重置
const handleReset = () => {
  searchForm.name = ''
  // 不重置project_id，保持当前选择的项目
  pagination.page = 1
  loadTableData()
}

// 新建
const handleCreate = () => {
  dialogTitle.value = '新建UI项目'
  Object.assign(formData, {
    id: null,
    project_id: searchForm.project_id, // 使用当前选择的项目ID
    name: '',
    description: '',
    base_url: '',
    browser_type: 'chromium',
    viewport_width: 1920,
    viewport_height: 1080,
    timeout: 30000
  })
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row: any) => {
  dialogTitle.value = '编辑UI项目'
  Object.assign(formData, row)
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  await formRef.value.validate()
  
  // 检查项目名称是否重复（仅在创建或修改名称时检查）
  const isDuplicate = tableData.value.some(item => 
    item.name === formData.name && item.id !== formData.id
  )
  
  if (isDuplicate) {
    ElMessage.warning('项目名称已存在，请使用其他名称')
    return
  }
  
  submitLoading.value = true
  try {
    if (formData.id) {
      await uiProjectApi.update(formData.id, formData)
      ElMessage.success('更新成功')
    } else {
      await uiProjectApi.create(formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadTableData()
  } catch (error: any) {
    // 处理后端返回的错误信息
    const errorMsg = error?.response?.data?.message || error?.message || '操作失败'
    ElMessage.error(errorMsg)
    console.error(error)
  } finally {
    submitLoading.value = false
  }
}

// 删除
const handleDelete = (row: any) => {
  ElMessageBox.confirm('确定要删除该UI项目吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await uiProjectApi.delete(row.id)
      ElMessage.success('删除成功')
      loadTableData()
    } catch (error) {
      ElMessage.error('删除失败')
      console.error(error)
    }
  })
}

// 管理（跳转到详情页）
const handleManage = (row: any) => {
  router.push({
    path: '/testing/ui-automation/manage',
    query: { id: row.id }
  })
}

// 生成代码
const handleGenerateCode = (row: any) => {
  currentProjectId.value = row.id
  codeDialogVisible.value = true
}

// 提交代码生成
const handleGenerateCodeSubmit = async () => {
  codeLoading.value = true
  try {
    const res = await uiProjectApi.generateCode(currentProjectId.value, codeForm)
    generatedFiles.value = res.data.files || []
    if (generatedFiles.value.length > 0) {
      activeCodeTab.value = generatedFiles.value[0].filename
    }
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
const handleCopyCode = (code: string) => {
  navigator.clipboard.writeText(code).then(() => {
    ElMessage.success('代码已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 分页
const handleSizeChange = () => {
  loadTableData()
}

const handleCurrentChange = () => {
  loadTableData()
}

// 初始化
onMounted(async () => {
  console.log('[UI Automation Index] 组件挂载')
  await loadProjectList()
  // 只有在有项目的情况下才加载数据
  if (searchForm.project_id) {
    loadTableData()
  }
})
</script>

<style scoped lang="scss">
.ui-automation-container {
  padding: 20px;

  .search-form {
    margin-bottom: 20px;
  }

  .code-preview {
    pre {
      background-color: #f5f5f5;
      padding: 15px;
      border-radius: 4px;
      overflow-x: auto;
      max-height: 500px;
      
      code {
        font-family: 'Courier New', Courier, monospace;
        font-size: 13px;
        line-height: 1.5;
      }
    }
  }
}
</style>
