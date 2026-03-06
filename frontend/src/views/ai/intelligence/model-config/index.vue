<template>
  <div class="ai-model-config-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>AI模型配置</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            关联配置
          </el-button>
        </div>
      </template>

      <!-- 筛选区域 -->
      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="角色">
          <el-select v-model="queryForm.role" placeholder="请选择" clearable style="width: 200px">
            <el-option label="Writer (编写)" value="writer" />
            <el-option label="Reviewer (评审)" value="reviewer" />
            <el-option label="Browser-use (浏览器)" value="browser_use_text" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="config_name" label="配置名称" min-width="150" />
        <el-table-column prop="role" label="角色" width="150">
          <template #default="{ row }">
            <el-tag :type="getRoleTagType(row.role)">{{ getRoleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="provider" label="提供商" width="120">
          <template #default="{ row }">
            <el-tag>{{ getProviderLabel(row.provider) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model_name" label="模型名称" min-width="150" />
        <el-table-column prop="base_url" label="Base URL" min-width="200" show-overflow-tooltip />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              @change="handleStatusChange(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleTest(row)">测试</el-button>
            <el-button type="success" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 关联配置对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="选择LLM配置" prop="llm_config_id">
          <el-select
            v-model="formData.llm_config_id"
            placeholder="请选择LLM配置"
            style="width: 100%"
            @change="handleLLMConfigChange"
          >
            <el-option
              v-for="config in llmConfigList"
              :key="config.id"
              :label="`${config.config_name} (${config.name})`"
              :value="config.id"
            />
          </el-select>
          <div class="form-tip">
            从已有的LLM配置中选择，如果没有可用配置，请先到"LLM配置"页面创建
          </div>
        </el-form-item>
        
        <el-form-item label="角色" prop="role">
          <el-select v-model="formData.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="Writer (编写测试用例)" value="writer" />
            <el-option label="Reviewer (评审测试用例)" value="reviewer" />
            <el-option label="Browser-use (智能浏览器)" value="browser_use_text" />
          </el-select>
          <div class="form-tip">
            选择此配置在AI智能化模块中的角色
          </div>
        </el-form-item>

        <!-- 显示选中的配置信息 -->
        <el-divider v-if="selectedLLMConfig">配置详情</el-divider>
        <template v-if="selectedLLMConfig">
          <el-form-item label="配置名称">
            <span>{{ selectedLLMConfig.config_name }}</span>
          </el-form-item>
          <el-form-item label="模型名称">
            <span>{{ selectedLLMConfig.name }}</span>
          </el-form-item>
          <el-form-item label="提供商">
            <el-tag>{{ getProviderLabel(selectedLLMConfig.provider) }}</el-tag>
          </el-form-item>
          <el-form-item label="模型">
            <span>{{ selectedLLMConfig.model_name }}</span>
          </el-form-item>
          <el-form-item label="Base URL">
            <span class="text-small">{{ selectedLLMConfig.base_url || '默认' }}</span>
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 测试对话框 -->
    <el-dialog
      v-model="testDialogVisible"
      title="测试模型连接"
      width="700px"
    >
      <el-form label-width="100px">
        <el-form-item label="测试消息">
          <el-input
            v-model="testMessage"
            type="textarea"
            :rows="3"
            placeholder="输入测试消息"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleRunTest" :loading="testLoading">
            发送测试
          </el-button>
        </el-form-item>
        <el-form-item label="测试结果" v-if="testResult">
          <el-alert
            :title="testResult.success ? '连接成功' : '连接失败'"
            :type="testResult.success ? 'success' : 'error'"
            :closable="false"
          >
            <template v-if="testResult.success">
              <div><strong>响应:</strong></div>
              <div class="test-response">{{ testResult.response }}</div>
              <div class="test-latency">延迟: {{ testResult.latency }}ms</div>
            </template>
            <template v-else>
              <div>{{ testResult.error || testResult.message }}</div>
            </template>
          </el-alert>
        </el-form-item>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { aiModelConfigApi } from '/@/api/v1/ai_intelligence'
import { useLLMConfigApi } from '/@/api/v1/ai/llmConfig'
import type { LLMConfigData } from '/@/api/v1/ai/llmConfig'

const llmConfigApi = useLLMConfigApi()

// 查询表单
const queryForm = reactive({
  role: ''
})

// 表格数据
const tableData = ref<any[]>([])
const loading = ref(false)

// LLM配置列表
const llmConfigList = ref<LLMConfigData[]>([])

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('关联配置')
const formRef = ref<FormInstance>()
const submitLoading = ref(false)

// 表单数据
const formData = reactive({
  llm_config_id: null as number | null,
  role: ''
})

// 表单验证规则
const formRules = {
  llm_config_id: [{ required: true, message: '请选择LLM配置', trigger: 'change' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

// 当前编辑的ID
let currentEditId: number | null = null

// 选中的LLM配置
const selectedLLMConfig = computed(() => {
  if (!formData.llm_config_id) return null
  return llmConfigList.value.find(c => c.id === formData.llm_config_id)
})

// 测试对话框
const testDialogVisible = ref(false)
const testLoading = ref(false)
const testMessage = ref('Hello, this is a test message.')
const testResult = ref<any>(null)
const testingConfig = ref<any>(null)

// 获取LLM配置列表
const getLLMConfigList = async () => {
  try {
    const res = await llmConfigApi.getList({ is_active: true })
    llmConfigList.value = res.data || []
  } catch (error) {
    console.error('获取LLM配置列表失败', error)
  }
}

// 获取列表
const getList = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (queryForm.role) params.role = queryForm.role
    
    const res = await aiModelConfigApi.list(params)
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
  queryForm.role = ''
  getList()
}

// 新增
const handleAdd = () => {
  currentEditId = null
  dialogTitle.value = '关联配置'
  resetForm()
  dialogVisible.value = true
}

// LLM配置变化
const handleLLMConfigChange = (configId: number) => {
  const config = llmConfigList.value.find(c => c.id === configId)
  if (config) {
    console.log('选中的LLM配置:', config)
  }
}

// 编辑
const handleEdit = async (row: any) => {
  currentEditId = row.id!
  dialogTitle.value = '编辑配置'
  
  // 确保LLM配置列表已加载
  if (llmConfigList.value.length === 0) {
    await getLLMConfigList()
  }
  
  // 设置表单数据
  formData.llm_config_id = row.llm_config_id
  formData.role = row.role
  
  dialogVisible.value = true
}

// 删除
const handleDelete = (row: any) => {
  ElMessageBox.confirm('确定要删除该配置吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await aiModelConfigApi.delete(row.id!)
      ElMessage.success('删除成功')
      getList()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

// 状态切换
const handleStatusChange = async (row: any) => {
  try {
    await aiModelConfigApi.update(row.id!, { is_active: row.is_active })
    ElMessage.success('状态更新成功')
  } catch (error) {
    ElMessage.error('状态更新失败')
    row.is_active = !row.is_active
  }
}

// 测试
const handleTest = (row: any) => {
  testingConfig.value = row
  testMessage.value = 'Hello, this is a test message.'
  testResult.value = null
  testDialogVisible.value = true
}

// 执行测试
const handleRunTest = async () => {
  if (!testingConfig.value) return
  
  // 检查是否有llm_config_id
  if (!testingConfig.value.llm_config_id) {
    ElMessage.error('该配置没有关联LLM配置，无法测试')
    return
  }
  
  testLoading.value = true
  testResult.value = null
  
  try {
    const res = await llmConfigApi.test({
      config_id: testingConfig.value.llm_config_id,
      test_message: testMessage.value
    })
    testResult.value = res.data
  } catch (error: any) {
    testResult.value = {
      success: false,
      error: error.response?.data?.message || error.message || '测试失败'
    }
  } finally {
    testLoading.value = false
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    const selectedConfig = selectedLLMConfig.value
    if (!selectedConfig) {
      ElMessage.error('请选择LLM配置')
      return
    }
    
    submitLoading.value = true
    try {
      const submitData = {
        name: selectedConfig.config_name,
        model_type: selectedConfig.provider,
        role: formData.role,
        api_key: selectedConfig.api_key,
        base_url: selectedConfig.base_url || '',
        model_name: selectedConfig.model_name,
        max_tokens: selectedConfig.max_tokens,
        temperature: selectedConfig.temperature,
        top_p: 0.9,
        is_active: selectedConfig.is_active,
        llm_config_id: selectedConfig.id
      }
      
      if (currentEditId) {
        await aiModelConfigApi.update(currentEditId, submitData)
        ElMessage.success('更新成功')
      } else {
        await aiModelConfigApi.create(submitData)
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
  formData.llm_config_id = null
  formData.role = ''
  formRef.value?.clearValidate()
}

// 辅助函数
const getProviderLabel = (provider: string) => {
  const map: Record<string, string> = {
    openai: 'OpenAI',
    azure_openai: 'Azure OpenAI',
    anthropic: 'Anthropic',
    ollama: 'Ollama',
    deepseek: 'DeepSeek',
    qwen: 'Qwen',
    siliconflow: 'SiliconFlow',
    zhipu: 'Zhipu',
    custom: '自定义'
  }
  return map[provider] || provider
}

const getRoleLabel = (role: string) => {
  const map: Record<string, string> = {
    writer: 'Writer',
    reviewer: 'Reviewer',
    browser_use_text: 'Browser-use'
  }
  return map[role] || role
}

const getRoleTagType = (role: string) => {
  const map: Record<string, any> = {
    writer: 'primary',
    reviewer: 'success',
    browser_use_text: 'warning'
  }
  return map[role] || ''
}

onMounted(() => {
  getLLMConfigList()
  getList()
})
</script>

<style scoped lang="scss">
.ai-model-config-container {
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

.text-gray {
  color: #999;
}

.text-small {
  font-size: 12px;
  color: #666;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
  line-height: 1.5;
}

.test-response {
  margin-top: 10px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 300px;
  overflow-y: auto;
}

.test-latency {
  margin-top: 10px;
  font-size: 12px;
  color: #67c23a;
}
</style>
