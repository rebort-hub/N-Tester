<template>
  <div class="request-editor">
    <!-- 请求基本信息 -->
    <div class="request-info">
      <el-form :model="localRequest" label-width="80px">
        <el-form-item label="请求名称">
          <el-input v-model="localRequest.name" placeholder="请输入请求名称" />
        </el-form-item>
        
        <el-form-item label="请求URL">
          <el-input v-model="localRequest.url" placeholder="请输入请求URL">
            <template #prepend>
              <el-select v-model="localRequest.method" style="width: 100px">
                <el-option label="GET" value="GET" />
                <el-option label="POST" value="POST" />
                <el-option label="PUT" value="PUT" />
                <el-option label="DELETE" value="DELETE" />
                <el-option label="PATCH" value="PATCH" />
                <el-option label="HEAD" value="HEAD" />
                <el-option label="OPTIONS" value="OPTIONS" />
              </el-select>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input
            v-model="localRequest.description"
            type="textarea"
            :rows="2"
            placeholder="请输入请求描述"
          />
        </el-form-item>
      </el-form>
    </div>

    <!-- 请求详情标签页 -->
    <el-tabs v-model="activeTab" class="request-tabs">
      <!-- 请求参数 -->
      <el-tab-pane label="Params" name="params">
        <KeyValueEditor
          v-model="localRequest.params"
          placeholder-key="参数名"
          placeholder-value="参数值"
          :show-type="true"
          :show-example="true"
        />
      </el-tab-pane>

      <!-- 请求头 -->
      <el-tab-pane label="Headers" name="headers">
        <KeyValueEditor
          v-model="localRequest.headers"
          placeholder-key="Header名"
          placeholder-value="Header值"
          :show-type="true"
        />
      </el-tab-pane>

      <!-- 请求体 -->
      <el-tab-pane label="Body" name="body">
        <div class="body-editor">
          <el-radio-group v-model="bodyType" class="body-type-selector">
            <el-radio-button label="none">none</el-radio-button>
            <el-radio-button label="form-data">form-data</el-radio-button>
            <el-radio-button label="x-www-form-urlencoded">x-www-form-urlencoded</el-radio-button>
            <el-radio-button label="json">json</el-radio-button>
            <el-radio-button label="xml">xml</el-radio-button>
            <el-radio-button label="raw">raw</el-radio-button>
            <el-radio-button label="binary">binary</el-radio-button>
          </el-radio-group>
          
          <!-- none -->
          <div v-if="bodyType === 'none'" class="body-none">
            <el-empty description="此请求没有 Body" :image-size="100" />
          </div>
          
          <!-- form-data -->
          <div v-else-if="bodyType === 'form-data'" class="body-form-data">
            <KeyValueEditor
              v-model="bodyFormData"
              placeholder-key="字段名"
              placeholder-value="字段值"
              :show-type="true"
            />
          </div>
          
          <!-- x-www-form-urlencoded -->
          <div v-else-if="bodyType === 'x-www-form-urlencoded'" class="body-urlencoded">
            <KeyValueEditor
              v-model="bodyUrlencoded"
              placeholder-key="字段名"
              placeholder-value="字段值"
              :show-type="true"
            />
          </div>
          
          <!-- json -->
          <div v-else-if="bodyType === 'json'" class="json-editor">
            <el-input
              v-model="bodyJson"
              type="textarea"
              :rows="15"
              placeholder='{"key": "value"}'
            />
          </div>
          
          <!-- xml -->
          <div v-else-if="bodyType === 'xml'" class="xml-editor">
            <el-input
              v-model="bodyXml"
              type="textarea"
              :rows="15"
              placeholder='<?xml version="1.0" encoding="UTF-8"?>&#10;<root>&#10;  <key>value</key>&#10;</root>'
            />
          </div>
          
          <!-- raw -->
          <div v-else-if="bodyType === 'raw'" class="raw-editor">
            <div class="raw-type-selector">
              <span style="margin-right: 10px;">Raw 类型:</span>
              <el-select v-model="rawType" size="small" style="width: 150px">
                <el-option label="Text" value="text/plain" />
                <el-option label="JSON" value="application/json" />
                <el-option label="XML" value="application/xml" />
                <el-option label="HTML" value="text/html" />
                <el-option label="JavaScript" value="application/javascript" />
              </el-select>
            </div>
            <el-input
              v-model="bodyRaw"
              type="textarea"
              :rows="15"
              placeholder="输入原始文本内容"
            />
          </div>
          
          <!-- binary -->
          <div v-else-if="bodyType === 'binary'" class="binary-editor">
            <el-upload
              :auto-upload="false"
              :show-file-list="true"
              :on-change="handleBinaryFileChange"
              :file-list="binaryFileList"
              :limit="1"
            >
              <el-button type="primary">
                <el-icon><ele-Upload /></el-icon>
                选择文件
              </el-button>
              <template #tip>
                <div class="el-upload__tip">
                  上传二进制文件（如图片、PDF等）
                </div>
              </template>
            </el-upload>
          </div>
        </div>
      </el-tab-pane>

      <!-- Cookies -->
      <el-tab-pane label="Cookies" name="cookies">
        <KeyValueEditor
          v-model="localRequest.cookies"
          placeholder-key="Cookie名"
          placeholder-value="Cookie值"
        />
      </el-tab-pane>

      <!-- 认证 -->
      <el-tab-pane label="Auth" name="auth">
        <div class="auth-editor">
          <el-form label-width="100px">
            <el-form-item label="认证类型">
              <el-select v-model="authType" placeholder="选择认证类型">
                <el-option label="无认证" value="none" />
                <el-option label="Bearer Token" value="bearer" />
                <el-option label="Basic Auth" value="basic" />
                <el-option label="API Key" value="apikey" />
              </el-select>
            </el-form-item>
            
            <template v-if="authType === 'bearer'">
              <el-form-item label="Token">
                <el-input v-model="authData.token" placeholder="请输入Token" />
              </el-form-item>
            </template>
            
            <template v-else-if="authType === 'basic'">
              <el-form-item label="用户名">
                <el-input v-model="authData.username" placeholder="请输入用户名" />
              </el-form-item>
              <el-form-item label="密码">
                <el-input v-model="authData.password" type="password" placeholder="请输入密码" />
              </el-form-item>
            </template>
            
            <template v-else-if="authType === 'apikey'">
              <el-form-item label="Key">
                <el-input v-model="authData.key" placeholder="请输入Key名称" />
              </el-form-item>
              <el-form-item label="Value">
                <el-input v-model="authData.value" placeholder="请输入Key值" />
              </el-form-item>
              <el-form-item label="添加到">
                <el-radio-group v-model="authData.addTo">
                  <el-radio label="header">Header</el-radio>
                  <el-radio label="query">Query Params</el-radio>
                </el-radio-group>
              </el-form-item>
            </template>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- 前置操作 -->
      <el-tab-pane label="前置操作" name="pre-script">
        <OperationListEditor
          v-model="localRequest.pre_request_script"
          title="前置操作"
          :project-id="projectId"
          :api-project-id="apiProjectId"
        />
      </el-tab-pane>

      <!-- 后置操作 -->
      <el-tab-pane label="后置操作" name="post-script">
        <OperationListEditor
          v-model="localRequest.post_request_script"
          title="后置操作"
          :project-id="projectId"
          :api-project-id="apiProjectId"
        />
      </el-tab-pane>

      <!-- 断言 -->
      <el-tab-pane label="断言" name="assertions">
        <AssertionEditor v-model="localRequest.assertions" />
      </el-tab-pane>

      <!-- 设置 -->
      <el-tab-pane label="设置" name="settings">
        <div class="settings-editor">
          <el-form label-width="150px">
            <el-form-item label="SSL 证书验证">
              <el-switch v-model="localRequest.verify_ssl" />
              <span style="margin-left: 10px; color: #909399; font-size: 12px;">
                关闭后将不验证服务器证书
              </span>
            </el-form-item>
            
            <el-form-item label="SSL 证书管理">
              <el-button type="primary" @click="showSSLCertDialog = true">
                <el-icon><ele-Lock /></el-icon>
                管理SSL证书
              </el-button>
              <span style="margin-left: 10px; color: #909399; font-size: 12px;">
                配置CA证书和客户端证书
              </span>
            </el-form-item>
            
            <el-form-item label="自动跟随重定向">
              <el-switch v-model="localRequest.follow_redirects" />
              <span style="margin-left: 10px; color: #909399; font-size: 12px;">
                自动跟随 3xx 重定向响应
              </span>
            </el-form-item>
            
            <el-form-item label="请求超时时间">
              <el-input-number 
                v-model="localRequest.timeout" 
                :min="0" 
                :max="300000"
                :step="1000"
                placeholder="毫秒"
              />
              <span style="margin-left: 10px; color: #909399; font-size: 12px;">
                单位：毫秒（0 表示不限制）
              </span>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- 历史记录 -->
      <el-tab-pane label="历史记录" name="history">
        <div class="history-section">
          <el-button 
            type="primary" 
            size="small" 
            @click="loadHistory"
            :loading="loadingHistory"
            style="margin-bottom: 15px"
          >
            <el-icon><ele-Refresh /></el-icon>
            刷新历史
          </el-button>
          
          <el-table 
            :data="historyList" 
            style="width: 100%"
            v-loading="loadingHistory"
            @row-click="handleHistoryRowClick"
            :row-style="{ cursor: 'pointer' }"
          >
            <el-table-column prop="executed_at" label="执行时间" min-width="160">
              <template #default="{ row }">
                {{ formatDateTime(row.executed_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="status_code" label="状态码" width="90">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status_code)">
                  {{ row.status_code }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="response_time" label="响应时间" width="100">
              <template #default="{ row }">
                {{ row.response_time?.toFixed(2) }}ms
              </template>
            </el-table-column>
            <el-table-column label="断言结果" width="90">
              <template #default="{ row }">
                <el-tag v-if="row.assertions_passed !== null" :type="row.assertions_passed ? 'success' : 'danger'">
                  {{ row.assertions_passed ? '通过' : '失败' }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="environment_name" label="环境" min-width="100" show-overflow-tooltip />
            <el-table-column label="操作" width="90">
              <template #default="{ row }">
                <el-button 
                  type="primary" 
                  size="small" 
                  text
                  @click.stop="viewHistoryDetail(row)"
                >
                  查看详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <el-pagination
            v-if="historyTotal > 0"
            v-model:current-page="historyPage"
            v-model:page-size="historyPageSize"
            :total="historyTotal"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            @current-change="loadHistory"
            @size-change="loadHistory"
            style="margin-top: 15px; justify-content: flex-end"
          />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 响应区域 -->
    <div v-if="response" class="response-section">
      <el-divider>响应结果</el-divider>
      
      <div class="response-info">
        <el-tag :type="getStatusType(response.status_code)">
          状态码: {{ response.status_code }}
        </el-tag>
        <el-tag type="info">
          响应时间: {{ response.response_time?.toFixed(2) }}ms
        </el-tag>
      </div>

      <el-tabs v-model="responseTab" class="response-tabs">
        <el-tab-pane label="Body" name="body">
          <div class="response-body">
            <pre>{{ formatJson(response.response_data?.body) }}</pre>
          </div>
        </el-tab-pane>

        <el-tab-pane label="Headers" name="headers">
          <div class="response-headers">
            <el-descriptions :column="1" border>
              <el-descriptions-item
                v-for="(value, key) in response.response_data?.headers"
                :key="key"
                :label="key"
              >
                {{ value }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-tab-pane>

        <el-tab-pane label="Assertions" name="assertions" v-if="response.assertions_results">
          <div class="assertions-results">
            <el-table :data="response.assertions_results" style="width: 100%">
              <el-table-column prop="type" label="类型" width="150" />
              <el-table-column prop="message" label="描述" />
              <el-table-column prop="passed" label="结果" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.passed ? 'success' : 'danger'">
                    {{ row.passed ? '通过' : '失败' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
  
  <!-- SSL证书管理对话框 -->
  <SSLCertificateDialog
    v-model="showSSLCertDialog"
    :project-id="projectId"
  />
</template>

<script setup lang="ts">
import { ref, watch, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useApiTestingApi } from '/@/api/v1/api_testing'
import KeyValueEditor from './KeyValueEditor.vue'
import AssertionEditor from './AssertionEditor.vue'
import SSLCertificateDialog from './SSLCertificateDialog.vue'
import OperationListEditor from './OperationListEditor.vue'

const { apiRequestApi } = useApiTestingApi()

const props = defineProps<{
  modelValue: any
  environmentId?: number
  response?: any
  executing?: boolean
  projectId?: number
  apiProjectId?: number
}>()

const emit = defineEmits(['update:modelValue', 'execute'])

// SSL证书对话框
const showSSLCertDialog = ref(false)

// 确保所有字段都有默认值
const ensureDefaults = (request: any) => {
  return {
    name: '',
    method: 'GET',
    url: '',
    description: '',
    params: {},
    headers: {},
    body: null,
    cookies: {},
    auth: null,
    pre_request_script: [],
    post_request_script: [],
    assertions: [],
    verify_ssl: true,
    follow_redirects: true,
    timeout: 30000,
    ...request
  }
}

const localRequest = ref(ensureDefaults(props.modelValue || {}))
const activeTab = ref('params')
const responseTab = ref('body')

// Body类型
const bodyType = ref('none')
const bodyJson = ref('')
const bodyFormData = ref({})
const bodyUrlencoded = ref({})
const bodyXml = ref('')
const bodyRaw = ref('')
const rawType = ref('text/plain')
const bodyBinary = ref<any>(null)
const binaryFileList = ref<any[]>([])

// 认证类型
const authType = ref('none')
const authData = ref<any>({})

// 监听props变化 - 只在外部数据变化时更新
watch(() => props.modelValue, (newVal) => {
  if (!newVal) return
  // 使用 JSON 比较避免不必要的更新
  const newData = ensureDefaults(newVal)
  if (JSON.stringify(newData) !== JSON.stringify(localRequest.value)) {
    localRequest.value = newData
    initBodyType()
    initAuthType()
  }
}, { deep: true })

// 监听本地数据变化 - 使用 nextTick 延迟更新
watch(localRequest, (newVal) => {
  nextTick(() => {
    emit('update:modelValue', newVal)
  })
}, { deep: true })

// 初始化Body类型
const initBodyType = () => {
  if (!localRequest.value.body) {
    bodyType.value = 'none'
    bodyJson.value = ''
    bodyFormData.value = {}
    bodyUrlencoded.value = {}
    bodyXml.value = ''
    bodyRaw.value = ''
    bodyBinary.value = null
    binaryFileList.value = []
    return
  }
  
  const body = localRequest.value.body
  
  // 判断body类型
  if (typeof body === 'string') {
    // 尝试解析为JSON
    try {
      JSON.parse(body)
      bodyType.value = 'json'
      bodyJson.value = body
    } catch {
      // 检查是否为XML
      if (body.trim().startsWith('<?xml') || body.trim().startsWith('<')) {
        bodyType.value = 'xml'
        bodyXml.value = body
      } else {
        bodyType.value = 'raw'
        bodyRaw.value = body
      }
    }
  } else if (body && typeof body === 'object') {
    // 检查是否有文件类型字段
    const hasFile = Object.values(body).some((v: any) => v instanceof File)
    if (hasFile) {
      bodyType.value = 'form-data'
      bodyFormData.value = body
    } else {
      bodyType.value = 'x-www-form-urlencoded'
      bodyUrlencoded.value = body
    }
  } else if (body instanceof File) {
    bodyType.value = 'binary'
    bodyBinary.value = body
    binaryFileList.value = [{ name: body.name, raw: body }]
  }
}

// 初始化认证类型
const initAuthType = () => {
  if (!localRequest.value.auth) {
    authType.value = 'none'
    authData.value = {}
  } else {
    authType.value = localRequest.value.auth.type || 'none'
    authData.value = localRequest.value.auth.data || {}
  }
}

// 监听Body类型变化
watch(bodyType, (newType) => {
  if (newType === 'none') {
    localRequest.value.body = null
  } else if (newType === 'json') {
    localRequest.value.body = bodyJson.value
  } else if (newType === 'form-data') {
    localRequest.value.body = bodyFormData.value
  } else if (newType === 'x-www-form-urlencoded') {
    localRequest.value.body = bodyUrlencoded.value
  } else if (newType === 'xml') {
    localRequest.value.body = bodyXml.value
  } else if (newType === 'raw') {
    localRequest.value.body = bodyRaw.value
  } else if (newType === 'binary') {
    localRequest.value.body = bodyBinary.value
  }
})

// 监听Body数据变化
watch(bodyJson, (newVal) => {
  if (bodyType.value === 'json') {
    localRequest.value.body = newVal
  }
})

watch(bodyFormData, (newVal) => {
  if (bodyType.value === 'form-data') {
    localRequest.value.body = newVal
  }
}, { deep: true })

watch(bodyUrlencoded, (newVal) => {
  if (bodyType.value === 'x-www-form-urlencoded') {
    localRequest.value.body = newVal
  }
}, { deep: true })

watch(bodyXml, (newVal) => {
  if (bodyType.value === 'xml') {
    localRequest.value.body = newVal
  }
})

watch(bodyRaw, (newVal) => {
  if (bodyType.value === 'raw') {
    localRequest.value.body = newVal
  }
})

// 监听认证数据变化
watch([authType, authData], ([newType, newData]) => {
  if (newType === 'none') {
    localRequest.value.auth = null
  } else {
    localRequest.value.auth = {
      type: newType,
      data: newData
    }
  }
}, { deep: true })

// 格式化JSON
const formatJson = (data: any) => {
  if (!data) return ''
  if (typeof data === 'string') {
    try {
      return JSON.stringify(JSON.parse(data), null, 2)
    } catch {
      return data
    }
  }
  return JSON.stringify(data, null, 2)
}

// 获取状态码类型
const getStatusType = (status: number) => {
  if (status >= 200 && status < 300) return 'success'
  if (status >= 300 && status < 400) return 'info'
  if (status >= 400 && status < 500) return 'warning'
  return 'danger'
}

// 处理二进制文件上传
const handleBinaryFileChange = (file: any) => {
  bodyBinary.value = file.raw
  binaryFileList.value = [file]
  localRequest.value.body = file.raw
}

// 历史记录相关
const historyList = ref<any[]>([])
const historyTotal = ref(0)
const historyPage = ref(1)
const historyPageSize = ref(10)
const loadingHistory = ref(false)

// 加载历史记录
const loadHistory = async () => {
  if (!localRequest.value?.id) {
    ElMessage.warning('请先保存请求')
    return
  }
  
  loadingHistory.value = true
  try {
    const res = await apiRequestApi.history(localRequest.value.id, {
      page: historyPage.value,
      page_size: historyPageSize.value
    })
    historyList.value = res.data.items || []
    historyTotal.value = res.data.total || 0
  } catch (error) {
    console.error('加载历史记录失败:', error)
    ElMessage.error('加载历史记录失败')
  } finally {
    loadingHistory.value = false
  }
}

// 查看历史详情
const viewHistoryDetail = (row: any) => {
  ElMessageBox.alert(
    `<div style="max-height: 400px; overflow: auto;">
      <h4>请求信息</h4>
      <p><strong>URL:</strong> ${row.request_data?.url || '-'}</p>
      <p><strong>方法:</strong> ${row.request_data?.method || '-'}</p>
      <h4>响应信息</h4>
      <p><strong>状态码:</strong> ${row.status_code}</p>
      <p><strong>响应时间:</strong> ${row.response_time?.toFixed(2)}ms</p>
      <h4>响应Body</h4>
      <pre style="background: #f5f7fa; padding: 10px; border-radius: 4px; max-height: 200px; overflow: auto;">${formatJson(row.response_data?.body)}</pre>
    </div>`,
    '历史记录详情',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '关闭'
    }
  )
}

// 点击历史记录行
const handleHistoryRowClick = (row: any) => {
  // 可以选择加载该历史记录的响应数据到响应区域
  // 这里暂时不实现，避免覆盖当前响应
}

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 监听请求ID变化，自动加载历史
watch(() => localRequest.value?.id, (newId) => {
  if (newId && activeTab.value === 'history') {
    loadHistory()
  }
})

// 监听标签页切换
watch(activeTab, (newTab) => {
  if (newTab === 'history' && localRequest.value?.id) {
    loadHistory()
  }
})

// 初始化
initBodyType()
initAuthType()
</script>

<style scoped lang="scss">
.request-editor {
  display: flex;
  flex-direction: column;
  gap: 20px;
  
  .request-info {
    padding: 10px 0;
  }
  
  .request-tabs,
  .response-tabs {
    :deep(.el-tabs__content) {
      padding: 15px 0;
    }
  }
  
  .body-editor {
    .body-type-selector {
      margin-bottom: 15px;
      
      :deep(.el-radio-button__inner) {
        padding: 8px 15px;
      }
    }
    
    .body-none {
      padding: 40px 0;
      text-align: center;
    }
    
    .json-editor,
    .xml-editor,
    .raw-editor {
      :deep(textarea) {
        font-family: 'Courier New', monospace;
        font-size: 13px;
      }
    }
    
    .raw-type-selector {
      margin-bottom: 10px;
      display: flex;
      align-items: center;
    }
    
    .binary-editor {
      padding: 20px 0;
    }
  }
  
  .auth-editor {
    max-width: 600px;
  }
  
  .settings-editor {
    max-width: 800px;
    padding: 20px 0;
    
    :deep(.el-form-item) {
      margin-bottom: 24px;
    }
  }
  
  .history-section {
    padding: 10px 0;
    
    :deep(.el-table) {
      .el-table__row {
        &:hover {
          background-color: #f5f7fa;
        }
      }
    }
    
    :deep(.el-pagination) {
      display: flex;
    }
  }
  
  .response-section {
    margin-top: 20px;
    
    .response-info {
      display: flex;
      gap: 10px;
      margin-bottom: 15px;
    }
    
    .response-body {
      background: #f5f7fa;
      padding: 15px;
      border-radius: 4px;
      max-height: 400px;
      overflow: auto;
      
      pre {
        margin: 0;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        white-space: pre-wrap;
        word-wrap: break-word;
      }
    }
    
    .response-headers {
      max-height: 400px;
      overflow: auto;
    }
  }
}
</style>
