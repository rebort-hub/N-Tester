<template>
  <div class="llm-config-page">
    <!-- 搜索栏 -->
    <el-card shadow="hover" class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="提供商">
          <el-select
            v-model="searchForm.provider"
            placeholder="全部"
            clearable
            style="width: 150px"
          >
            <el-option label="OpenAI" value="openai" />
            <el-option label="Azure OpenAI" value="azure_openai" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="Ollama" value="ollama" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select
            v-model="searchForm.is_active"
            placeholder="全部"
            clearable
            style="width: 120px"
          >
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch" v-auth="'ai:llm:list'">
            搜索
          </el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          <el-button type="primary" :icon="Plus" @click="handleAdd" v-auth="'ai:llm:create'">
            新增配置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 配置列表 -->
    <el-card shadow="hover" class="table-card">
      <el-table
        v-loading="loading"
        :data="configList"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="config_name" label="配置名称" min-width="150" />
        
        <el-table-column label="提供商" width="120">
          <template #default="{ row }">
            <el-tag :type="getProviderTagType(row.provider)">
              {{ getProviderLabel(row.provider) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="name" label="模型名称" min-width="150" />
        
        <el-table-column label="API Key" min-width="200">
          <template #default="{ row }">
            <span class="api-key">{{ maskApiKey(row.api_key) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="参数" width="180">
          <template #default="{ row }">
            <div class="params-cell">
              <div>温度: {{ row.temperature }}</div>
              <div>最大令牌: {{ row.max_tokens }}</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="默认" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success" size="small">
              是
            </el-tag>
            <el-tag v-else type="info" size="small">
              否
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              @change="handleStatusChange(row)"
            />
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="300" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :icon="Connection"
              @click="handleTest(row)"
              v-auth="'ai:llm:test'"
            >
              测试
            </el-button>
            <el-button
              v-if="!row.is_default"
              type="success"
              size="small"
              :icon="Star"
              @click="handleSetDefault(row)"
              v-auth="'ai:llm:setdefault'"
            >
              设为默认
            </el-button>
            <el-button
              type="primary"
              size="small"
              :icon="Edit"
              @click="handleEdit(row)"
              v-auth="'ai:llm:update'"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              :icon="Delete"
              @click="handleDelete(row)"
              v-auth="'ai:llm:delete'"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 配置表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
      >
        <el-form-item label="配置名称" prop="config_name">
          <el-input
            v-model="form.config_name"
            placeholder="请输入配置名称，如：生产环境OpenAI"
          />
        </el-form-item>
        
        <el-form-item label="提供商" prop="provider">
          <el-select
            v-model="form.provider"
            placeholder="请选择提供商"
            style="width: 100%"
            @change="handleProviderChange"
          >
            <el-option label="OpenAI" value="openai" />
            <el-option label="Azure OpenAI" value="azure_openai" />
            <el-option label="Anthropic (Claude)" value="anthropic" />
            <el-option label="Ollama (本地)" value="ollama" />
            <el-option label="自定义 API" value="custom" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="模型名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="如：gpt-4, claude-3-sonnet, qwen-plus"
          />
          <div class="form-tip">
            常用模型：GPT-4, GPT-3.5-turbo, Claude-3-sonnet, Qwen-plus
          </div>
        </el-form-item>
        
        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="form.api_key"
            type="password"
            show-password
            placeholder="请输入 API Key（本地模型如 Ollama 可留空）"
          />
          <div class="form-tip">
            本地模型（如 Ollama）不需要 API Key，可以留空
          </div>
        </el-form-item>
        
        <el-form-item label="API 基础URL" prop="base_url">
          <el-input
            v-model="form.base_url"
            placeholder="如：https://api.openai.com/v1"
          />
          <div class="form-tip">
            OpenAI: https://api.openai.com/v1<br>
            Ollama: http://localhost:11434<br>
            自定义: 填写您的 API 地址
          </div>
        </el-form-item>
        
        <el-form-item label="系统提示词">
          <el-input
            v-model="form.system_prompt"
            type="textarea"
            :rows="3"
            placeholder="可选：指导 LLM 行为的系统级提示词"
          />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="温度参数" prop="temperature">
              <el-slider
                v-model="form.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                show-input
              />
              <div class="form-tip">控制输出的随机性，0-2之间</div>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="最大令牌数" prop="max_tokens">
              <el-input-number
                v-model="form.max_tokens"
                :min="100"
                :max="100000"
                :step="100"
                style="width: 100%"
              />
              <div class="form-tip">单次响应的最大长度</div>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="上下文限制" prop="context_limit">
              <el-input-number
                v-model="form.context_limit"
                :min="1000"
                :max="2000000"
                :step="1000"
                style="width: 100%"
              />
              <div class="form-tip">模型支持的最大上下文Token数</div>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="多模态支持">
              <el-switch v-model="form.supports_vision" />
              <div class="form-tip">是否支持图片输入</div>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="设为默认">
              <el-switch v-model="form.is_default" />
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="启用状态">
              <el-switch v-model="form.is_active" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 测试对话框 -->
    <el-dialog
      v-model="testDialogVisible"
      title="测试 LLM 配置"
      width="600px"
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
        
        <el-form-item label="测试结果">
          <el-alert
            v-if="testResult"
            :title="testResult.message"
            :type="testResult.success ? 'success' : 'error'"
            :closable="false"
          >
            <template v-if="testResult.success">
              <div class="test-result">
                <p><strong>响应内容：</strong></p>
                <p class="response-content">{{ testResult.response }}</p>
                <p><strong>响应时间：</strong>{{ testResult.latency }}秒</p>
              </div>
            </template>
            <template v-else>
              <p><strong>错误信息：</strong>{{ testResult.error }}</p>
            </template>
          </el-alert>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="testDialogVisible = false">关闭</el-button>
        <el-button
          type="primary"
          :loading="testing"
          @click="handleRunTest"
        >
          开始测试
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import {
  Search,
  Refresh,
  Plus,
  Edit,
  Delete,
  Connection,
  Star
} from '@element-plus/icons-vue'
import { useLLMConfigApi } from '/@/api/v1/ai/llmConfig'
import type {
  LLMConfigData,
  LLMConfigCreateData,
  LLMConfigUpdateData,
  LLMProvider
} from '/@/api/v1/ai/llmConfig'

defineOptions({
  name: 'LLMConfigPage'
})

const llmConfigApi = useLLMConfigApi()

// 搜索表单
const searchForm = reactive({
  provider: '',
  is_active: undefined as boolean | undefined
})

// 配置列表
const configList = ref<LLMConfigData[]>([])
const loading = ref(false)

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref<FormInstance>()
const submitting = ref(false)
const editingId = ref<number | null>(null)

// 表单数据
const form = reactive<LLMConfigCreateData>({
  config_name: '',
  name: '',
  provider: 'openai',
  model_name: '',
  api_key: '',
  base_url: '',
  system_prompt: '',
  temperature: 0.7,
  max_tokens: 2000,
  supports_vision: false,
  context_limit: 128000,
  is_default: false,
  is_active: true
})

// 表单验证规则
const rules: FormRules = {
  config_name: [
    { required: true, message: '请输入配置名称', trigger: 'blur' }
  ],
  provider: [
    { required: true, message: '请选择提供商', trigger: 'change' }
  ],
  name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ]
  // api_key 改为可选，支持本地模型（如 Ollama）
}

// 测试对话框
const testDialogVisible = ref(false)
const testing = ref(false)
const testMessage = ref('Hello, this is a test message.')
const testResult = ref<any>(null)
const testingConfig = ref<LLMConfigData | null>(null)

/**
 * 加载配置列表
 */
const loadConfigList = async () => {
  loading.value = true
  try {
    const response = await llmConfigApi.getList({
      provider: searchForm.provider || undefined,
      is_active: searchForm.is_active
    })
    
    if (response.code === 200) {
      configList.value = response.data
    }
  } catch (error: any) {
    ElMessage.error(error.message || '加载配置列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 搜索
 */
const handleSearch = () => {
  loadConfigList()
}

/**
 * 重置
 */
const handleReset = () => {
  searchForm.provider = ''
  searchForm.is_active = undefined
  loadConfigList()
}

/**
 * 新增
 */
const handleAdd = () => {
  dialogTitle.value = '新增 LLM 配置'
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

/**
 * 编辑
 */
const handleEdit = (row: LLMConfigData) => {
  dialogTitle.value = '编辑 LLM 配置'
  editingId.value = row.id
  
  // 填充表单
  Object.assign(form, {
    config_name: row.config_name,
    name: row.name,
    provider: row.provider,
    model_name: row.model_name,
    api_key: row.api_key,
    base_url: row.base_url,
    system_prompt: row.system_prompt,
    temperature: row.temperature,
    max_tokens: row.max_tokens,
    supports_vision: row.supports_vision,
    context_limit: row.context_limit,
    is_default: row.is_default,
    is_active: row.is_active
  })
  
  dialogVisible.value = true
}

/**
 * 删除
 */
const handleDelete = async (row: LLMConfigData) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除配置"${row.config_name}"吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await llmConfigApi.delete(row.id)
    
    if (response.code === 200) {
      ElMessage.success('删除成功')
      loadConfigList()
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      // 显示后端返回的具体错误信息
      const errorMessage = error.response?.data?.message || error.message || '删除失败'
      
      // 如果是关联错误，使用警告类型的消息框
      if (errorMessage.includes('无法删除') || errorMessage.includes('正在使用')) {
        ElMessageBox.alert(errorMessage, '无法删除', {
          confirmButtonText: '我知道了',
          type: 'warning'
        })
      } else {
        ElMessage.error(errorMessage)
      }
    }
  }
}

/**
 * 设置为默认
 */
const handleSetDefault = async (row: LLMConfigData) => {
  try {
    const response = await llmConfigApi.setDefault(row.id)
    
    if (response.code === 200) {
      // 立即更新本地数据，提供即时反馈
      configList.value.forEach(config => {
        config.is_default = config.id === row.id
      })
      
      ElMessage.success('设置成功')
      
      // 然后从服务器重新加载，确保数据一致
      await loadConfigList()
    }
  } catch (error: any) {
    ElMessage.error(error.message || '设置失败')
  }
}

/**
 * 状态切换
 */
const handleStatusChange = async (row: LLMConfigData) => {
  try {
    const response = await llmConfigApi.update(row.id, {
      is_active: row.is_active
    })
    
    if (response.code === 200) {
      ElMessage.success('状态更新成功')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '状态更新失败')
    // 恢复原状态
    row.is_active = !row.is_active
  }
}

/**
 * 测试配置
 */
const handleTest = (row: LLMConfigData) => {
  testingConfig.value = row
  testMessage.value = 'Hello, this is a test message.'
  testResult.value = null
  testDialogVisible.value = true
}

/**
 * 执行测试
 */
const handleRunTest = async () => {
  if (!testingConfig.value) return
  
  testing.value = true
  testResult.value = null
  
  try {
    const response = await llmConfigApi.test({
      config_id: testingConfig.value.id,
      test_message: testMessage.value
    })
    
    testResult.value = response.data
  } catch (error: any) {
    testResult.value = {
      success: false,
      message: '测试失败',
      error: error.message || '未知错误'
    }
  } finally {
    testing.value = false
  }
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    
    try {
      // 设置 model_name 与 name 相同
      form.model_name = form.name
      
      let response
      if (editingId.value) {
        response = await llmConfigApi.update(editingId.value, form)
      } else {
        response = await llmConfigApi.create(form)
      }
      
      if (response.code === 200) {
        ElMessage.success(editingId.value ? '更新成功' : '创建成功')
        dialogVisible.value = false
        loadConfigList()
      }
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

/**
 * 重置表单
 */
const resetForm = () => {
  Object.assign(form, {
    config_name: '',
    name: '',
    provider: 'openai',
    model_name: '',
    api_key: '',
    base_url: 'https://api.openai.com/v1',
    system_prompt: '',
    temperature: 0.7,
    max_tokens: 2000,
    supports_vision: false,
    context_limit: 128000,
    is_default: false,
    is_active: true
  })
  
  formRef.value?.clearValidate()
}

/**
 * 提供商变更
 */
const handleProviderChange = (provider: LLMProvider) => {
  // 根据提供商设置默认值
  switch (provider) {
    case 'openai':
      form.base_url = 'https://api.openai.com/v1'
      form.context_limit = 128000
      break
    case 'anthropic':
      form.base_url = 'https://api.anthropic.com/v1'
      form.context_limit = 200000
      break
    case 'ollama':
      form.base_url = 'http://localhost:11434'
      form.context_limit = 8000
      break
    default:
      form.base_url = ''
      form.context_limit = 128000
  }
}

/**
 * 获取提供商标签类型
 */
const getProviderTagType = (provider: string) => {
  const types: Record<string, any> = {
    openai: 'success',
    azure_openai: 'primary',
    anthropic: 'warning',
    ollama: 'info',
    custom: ''
  }
  return types[provider] || ''
}

/**
 * 获取提供商标签
 */
const getProviderLabel = (provider: string) => {
  const labels: Record<string, string> = {
    openai: 'OpenAI',
    azure_openai: 'Azure',
    anthropic: 'Anthropic',
    ollama: 'Ollama',
    custom: '自定义'
  }
  return labels[provider] || provider
}

/**
 * 遮罩 API Key
 */
const maskApiKey = (apiKey: string) => {
  if (!apiKey) return ''
  if (apiKey.length <= 8) return '***'
  return apiKey.substring(0, 8) + '...' + apiKey.substring(apiKey.length - 4)
}

onMounted(() => {
  loadConfigList()
})
</script>

<style scoped lang="scss">
.llm-config-page {
  padding: 20px;

  .search-card {
    margin-bottom: 20px;

    .search-form {
      margin-bottom: 0;
    }
  }

  .table-card {
    .api-key {
      font-family: 'Courier New', monospace;
      font-size: 13px;
      color: #606266;
    }

    .params-cell {
      font-size: 13px;
      line-height: 1.6;
      color: #606266;
    }
    
    // 操作按钮间距
    :deep(.el-table__body) {
      .el-button {
        margin: 2px;
      }
    }
  }

  .form-tip {
    margin-top: 4px;
    font-size: 12px;
    color: #909399;
    line-height: 1.5;
  }

  .test-result {
    .response-content {
      margin: 8px 0;
      padding: 12px;
      background-color: #f5f7fa;
      border-radius: 4px;
      font-family: 'Courier New', monospace;
      font-size: 13px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
    }
  }
}
</style>
