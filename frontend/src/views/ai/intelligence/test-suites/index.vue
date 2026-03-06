<template>
  <div class="ai-test-suites-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>AI测试套件</span>
          <div class="header-actions">
            <el-button type="primary" @click="handleAdd">
              <el-icon><Plus /></el-icon>
              新增套件
            </el-button>
            <el-button @click="handleRefresh">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="项目">
          <el-select 
            v-model="queryForm.project_id" 
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
        
        <el-form-item label="状态">
          <el-select 
            v-model="queryForm.status" 
            placeholder="请选择状态" 
            clearable
            style="width: 150px"
          >
            <el-option label="激活" value="active" />
            <el-option label="归档" value="archived" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table 
        :data="tableData" 
        v-loading="loading" 
        border 
        stripe
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="套件名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="project_name" label="项目" width="150" />
        <el-table-column prop="module_count" label="模块数" width="100" align="center" />
        <el-table-column prop="case_count" label="用例数" width="100" align="center" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '激活' : '归档' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="creation_date" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.creation_date) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleExecute(row)">
              执行
            </el-button>
            <el-button type="success" size="small" @click="handleViewExecutions(row)">
              执行记录
            </el-button>
            <el-button type="warning" size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
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
        @size-change="handleQuery"
        @current-change="handleQuery"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 套件表单对话框 -->
    <SuiteForm
      v-model="formVisible"
      :suite-id="currentSuiteId"
      @success="handleFormSuccess"
    />

    <!-- 执行对话框 -->
    <el-dialog
      v-model="executeDialogVisible"
      title="执行测试套件"
      width="500px"
    >
      <el-form :model="executeForm" label-width="100px">
        <el-form-item label="执行名称">
          <el-input v-model="executeForm.execution_name" placeholder="可选，如：每日回归测试" />
        </el-form-item>
        <el-form-item label="执行模式">
          <el-radio-group v-model="executeForm.execution_mode">
            <el-radio value="headless">无头模式（后台执行）</el-radio>
            <el-radio value="headed">有头模式（显示浏览器）</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="executeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitExecute" :loading="executing">
          开始执行
        </el-button>
      </template>
    </el-dialog>

    <!-- 执行监控对话框 -->
    <ExecutionMonitor
      v-model="monitorVisible"
      :execution-id="currentExecutionId"
    />

    <!-- 执行记录对话框 -->
    <ExecutionReport
      v-model="reportVisible"
      :suite-id="currentSuiteId"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { aiTestSuiteApi } from '/@/api/v1/ai_intelligence'
import { getProjectList } from '/@/api/v1/project'
import SuiteForm from './components/SuiteForm.vue'
import ExecutionMonitor from './components/ExecutionMonitor.vue'
import ExecutionReport from './components/ExecutionReport.vue'

// 查询表单
const queryForm = reactive({
  project_id: null,
  status: null
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 表格数据
const tableData = ref([])
const loading = ref(false)

// 项目列表
const projectList = ref([])

// 表单对话框
const formVisible = ref(false)
const currentSuiteId = ref(null)

// 执行对话框
const executeDialogVisible = ref(false)
const executing = ref(false)
const executeForm = reactive({
  execution_name: '',
  execution_mode: 'headless'
})
const currentExecuteSuite = ref(null)

// 执行监控
const monitorVisible = ref(false)
const currentExecutionId = ref(null)

// 执行记录
const reportVisible = ref(false)

// 加载项目列表
const loadProjects = async () => {
  try {
    console.log('开始获取主项目列表...')
    // 使用主项目API而不是UI项目API
    const res = await getProjectList({ page: 1, page_size: 100 })
    console.log('主项目列表API响应:', res)
    if (res.code === 200) {
      projectList.value = res.data.list || res.data.items || res.data || []
      console.log('主项目列表:', projectList.value)
    }
  } catch (error) {
    console.error('获取主项目列表失败:', error)
  }
}

// 加载套件列表
const loadSuites = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    
    // 只添加非空的筛选参数
    if (queryForm.project_id) {
      params.project_id = queryForm.project_id
    }
    if (queryForm.status) {
      params.status = queryForm.status
    }
    
    const res = await aiTestSuiteApi.list(params)
    if (res.code === 200) {
      // 兼容不同的数据结构
      tableData.value = res.data.items || res.data.list || res.data || []
      pagination.total = res.data.total || 0
      console.log('套件列表加载成功:', tableData.value.length)
    }
  } catch (error) {
    ElMessage.error('加载套件列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 查询
const handleQuery = () => {
  pagination.page = 1
  loadSuites()
}

// 重置
const handleReset = () => {
  queryForm.project_id = null
  queryForm.status = null
  handleQuery()
}

// 刷新
const handleRefresh = () => {
  loadSuites()
}

// 新增
const handleAdd = () => {
  currentSuiteId.value = null
  formVisible.value = true
}

// 编辑
const handleEdit = (row: any) => {
  currentSuiteId.value = row.id
  formVisible.value = true
}

// 删除
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除套件"${row.name}"吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const res = await aiTestSuiteApi.delete(row.id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      loadSuites()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error(error)
    }
  }
}

// 执行
const handleExecute = (row: any) => {
  currentExecuteSuite.value = row
  executeForm.execution_name = `${row.name} - ${new Date().toLocaleString()}`
  executeForm.execution_mode = 'headless'
  executeDialogVisible.value = true
}

// 提交执行
const submitExecute = async () => {
  executing.value = true
  try {
    const res = await aiTestSuiteApi.execute(currentExecuteSuite.value.id, executeForm)
    if (res.code === 200) {
      ElMessage.success('套件执行已启动')
      executeDialogVisible.value = false
      
      // 打开监控对话框
      currentExecutionId.value = res.data.execution_id
      monitorVisible.value = true
    }
  } catch (error) {
    ElMessage.error('启动执行失败')
    console.error(error)
  } finally {
    executing.value = false
  }
}

// 查看执行记录
const handleViewExecutions = (row: any) => {
  currentSuiteId.value = row.id
  reportVisible.value = true
}

// 表单成功回调
const handleFormSuccess = () => {
  loadSuites()
}

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    }).replace(/\//g, '-')
  } catch (e) {
    return dateStr
  }
}

// 初始化
onMounted(() => {
  loadProjects()
  loadSuites()
})
</script>

<style scoped lang="scss">
.ai-test-suites-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.query-form {
  margin-bottom: 20px;
}
</style>
