<template>
  <div class="notification-configs">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>通知配置管理</span>
          <el-button 
            type="primary" 
            @click="handleAdd"
            v-auth="'notifications:config:add'"
          >
            <el-icon><ele-Plus /></el-icon>
            新增配置
          </el-button>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :model="queryParams" ref="queryRef" :inline="true" class="search-form">
        <el-form-item label="配置名称" prop="name">
          <el-input
            v-model="queryParams.name"
            placeholder="请输入配置名称"
            clearable
            style="width: 200px"
            @keyup.enter="handleQuery"
          />
        </el-form-item>
        <el-form-item label="通知类型" prop="config_type">
          <el-select
            v-model="queryParams.config_type"
            placeholder="请选择通知类型"
            clearable
            style="width: 200px"
          >
            <el-option label="飞书机器人" value="webhook_feishu" />
            <el-option label="企业微信机器人" value="webhook_wechat" />
            <el-option label="钉钉机器人" value="webhook_dingtalk" />
            <el-option label="Telegram机器人" value="telegram" />
            <el-option label="邮件推送" value="email" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-select
            v-model="queryParams.is_active"
            placeholder="请选择状态"
            clearable
            style="width: 120px"
          >
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">
            <el-icon><ele-Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetQuery">
            <el-icon><ele-Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 批量操作按钮 -->
      <div class="table-header" style="margin-bottom: 16px;">
        <el-button 
          type="danger" 
          :disabled="multiple"
          @click="handleBatchDelete"
          v-auth="'notifications:config:remove'"
        >
          <el-icon><ele-Delete /></el-icon>
          批量删除
        </el-button>
      </div>

      <!-- 数据表格 -->
      <el-table
        v-loading="loading"
        :data="configList"
        row-key="id"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column label="配置名称" prop="name" min-width="150" />
        <el-table-column label="通知类型" prop="config_type" width="120" align="center">
          <template #default="scope">
            <el-tag
              :type="getTypeTagType(scope.row.config_type)"
              size="small"
            >
              {{ getTypeLabel(scope.row.config_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="配置信息" prop="notification_config" min-width="200">
          <template #default="scope">
            <div class="config-info">
              <template v-if="scope.row.config_type === 'telegram'">
                <div>Chat ID: {{ scope.row.notification_config?.chat_id || '-' }}</div>
              </template>
              <template v-else-if="scope.row.config_type === 'email'">
                <div>SMTP: {{ scope.row.notification_config?.smtp_server || '-' }}</div>
                <div>收件人: {{ Array.isArray(scope.row.notification_config?.to_emails) ? scope.row.notification_config.to_emails.join(', ') : (scope.row.notification_config?.to_emails || '-') }}</div>
              </template>
              <template v-else>
                <span class="webhook-url">
                  {{ scope.row.notification_config?.webhook_url || '-' }}
                </span>
              </template>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="默认配置" prop="is_default" width="100" align="center">
          <template #default="scope">
            <el-tag
              :type="scope.row.is_default ? 'success' : 'info'"
              size="small"
            >
              {{ scope.row.is_default ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" prop="is_active" width="80" align="center">
          <template #default="scope">
            <el-switch
              v-model="scope.row.is_active"
              @change="handleStatusChange(scope.row)"
              v-auth="'notifications:config:edit'"
            />
          </template>
        </el-table-column>
        <el-table-column label="创建时间" prop="creation_date" width="160" align="center">
          <template #default="scope">
            <span>{{ scope.row.creation_date ? formatDateTime(scope.row.creation_date) : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" align="center" width="280" class-name="small-padding fixed-width">
          <template #default="scope">
            <div class="button-group">
              <el-button
                type="primary"
                size="small"
                @click="handleTest(scope.row)"
                v-auth="'notifications:config:test'"
              >
                测试
              </el-button>
              <el-button
                type="success"
                size="small"
                @click="handleSetDefault(scope.row)"
                v-auth="'notifications:config:default'"
                v-if="!scope.row.is_default"
              >
                设为默认
              </el-button>
              <el-button
                type="primary"
                size="small"
                @click="handleUpdate(scope.row)"
                v-auth="'notifications:config:edit'"
              >
                编辑
              </el-button>
              <el-button
                type="danger"
                size="small"
                @click="handleDelete(scope.row)"
                v-auth="'notifications:config:remove'"
              >
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-show="total > 0"
        :total="total"
        v-model:current-page="queryParams.pageNum"
        v-model:page-size="queryParams.pageSize"
        @size-change="getList"
        @current-change="getList"
        layout="total, sizes, prev, pager, next, jumper"
        :page-sizes="[10, 20, 50, 100]"
      />
    </el-card>

    <!-- 添加或修改配置对话框 -->
    <el-dialog :title="title" v-model="open" width="600px" append-to-body>
      <el-form ref="configRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入配置名称" />
        </el-form-item>
        <el-form-item label="通知类型" prop="config_type">
          <el-select
            v-model="form.config_type"
            placeholder="请选择通知类型"
            style="width: 100%"
            @change="handleTypeChange"
          >
            <el-option label="飞书机器人" value="webhook_feishu" />
            <el-option label="企业微信机器人" value="webhook_wechat" />
            <el-option label="钉钉机器人" value="webhook_dingtalk" />
            <el-option label="Telegram机器人" value="telegram" />
            <el-option label="邮件推送" value="email" />
          </el-select>
        </el-form-item>
        
        <!-- 飞书机器人配置 -->
        <template v-if="form.config_type === 'webhook_feishu'">
          <el-form-item label="Webhook URL" prop="notification_config.webhook_url">
            <el-input
              v-model="form.notification_config.webhook_url"
              placeholder="请输入飞书机器人Webhook URL"
              type="textarea"
              :rows="2"
            />
          </el-form-item>
          <el-form-item label="签名密钥">
            <el-input
              v-model="form.notification_config.secret"
              placeholder="请输入签名密钥（可选）"
              show-password
            />
          </el-form-item>
          <el-form-item label="关键词">
            <el-input
              v-model="keywordsInput"
              placeholder="请输入关键词，多个用逗号分隔"
              @blur="updateKeywords"
            />
            <div class="form-tip">机器人只会响应包含关键词的消息</div>
          </el-form-item>
        </template>

        <!-- 企业微信机器人配置 -->
        <template v-if="form.config_type === 'webhook_wechat'">
          <el-form-item label="Webhook URL" prop="notification_config.webhook_url">
            <el-input
              v-model="form.notification_config.webhook_url"
              placeholder="请输入企业微信机器人Webhook URL"
              type="textarea"
              :rows="2"
            />
          </el-form-item>
          <el-form-item label="提醒成员">
            <el-input
              v-model="mentionedInput"
              placeholder="请输入要@的成员，多个用逗号分隔，@all表示所有人"
              @blur="updateMentioned"
            />
          </el-form-item>
          <el-form-item label="提醒手机号">
            <el-input
              v-model="mentionedMobileInput"
              placeholder="请输入要@的手机号，多个用逗号分隔"
              @blur="updateMentionedMobile"
            />
          </el-form-item>
        </template>

        <!-- 钉钉机器人配置 -->
        <template v-if="form.config_type === 'webhook_dingtalk'">
          <el-form-item label="Webhook URL" prop="notification_config.webhook_url">
            <el-input
              v-model="form.notification_config.webhook_url"
              placeholder="请输入钉钉机器人Webhook URL"
              type="textarea"
              :rows="2"
            />
          </el-form-item>
          <el-form-item label="签名密钥">
            <el-input
              v-model="form.notification_config.secret"
              placeholder="请输入签名密钥（可选）"
              show-password
            />
          </el-form-item>
          <el-form-item label="@手机号">
            <el-input
              v-model="atMobilesInput"
              placeholder="请输入要@的手机号，多个用逗号分隔"
              @blur="updateAtMobiles"
            />
          </el-form-item>
          <el-form-item label="@用户ID">
            <el-input
              v-model="atUserIdsInput"
              placeholder="请输入要@的用户ID，多个用逗号分隔"
              @blur="updateAtUserIds"
            />
          </el-form-item>
          <el-form-item>
            <el-checkbox v-model="form.notification_config.is_at_all">@所有人</el-checkbox>
          </el-form-item>
        </template>

        <!-- Telegram机器人配置 -->
        <template v-if="form.config_type === 'telegram'">
          <el-form-item label="Bot Token" prop="notification_config.bot_token">
            <el-input
              v-model="form.notification_config.bot_token"
              placeholder="请输入Telegram Bot Token"
              show-password
            />
            <div class="form-tip">从 @BotFather 获取的机器人令牌</div>
          </el-form-item>
          <el-form-item label="Chat ID" prop="notification_config.chat_id">
            <el-input
              v-model="form.notification_config.chat_id"
              placeholder="请输入Chat ID"
            />
            <div class="form-tip">可以是用户ID、群组ID或频道ID</div>
          </el-form-item>
          <el-form-item label="解析模式">
            <el-select
              v-model="form.notification_config.parse_mode"
              placeholder="请选择解析模式"
              style="width: 100%"
              clearable
            >
              <el-option label="HTML" value="HTML" />
              <el-option label="Markdown" value="Markdown" />
              <el-option label="MarkdownV2" value="MarkdownV2" />
            </el-select>
            <div class="form-tip">消息格式解析模式，默认为HTML</div>
          </el-form-item>
          <el-form-item>
            <el-checkbox v-model="form.notification_config.disable_web_page_preview">禁用网页预览</el-checkbox>
          </el-form-item>
        </template>

        <!-- 邮件推送配置 -->
        <template v-if="form.config_type === 'email'">
          <el-form-item label="SMTP服务器" prop="notification_config.smtp_server">
            <el-input
              v-model="form.notification_config.smtp_server"
              placeholder="请输入SMTP服务器地址，如：smtp.gmail.com"
            />
          </el-form-item>
          <el-form-item label="SMTP端口" prop="notification_config.smtp_port">
            <el-input-number
              v-model="form.notification_config.smtp_port"
              placeholder="请输入SMTP端口"
              :min="1"
              :max="65535"
              style="width: 100%"
            />
            <div class="form-tip">常用端口：587(TLS)、465(SSL)、25(无加密)</div>
          </el-form-item>
          <el-form-item label="用户名" prop="notification_config.username">
            <el-input
              v-model="form.notification_config.username"
              placeholder="请输入SMTP用户名"
            />
          </el-form-item>
          <el-form-item label="密码" prop="notification_config.password">
            <el-input
              v-model="form.notification_config.password"
              placeholder="请输入SMTP密码"
              show-password
            />
          </el-form-item>
          <el-form-item label="发件人邮箱" prop="notification_config.from_email">
            <el-input
              v-model="form.notification_config.from_email"
              placeholder="请输入发件人邮箱地址"
              type="email"
            />
          </el-form-item>
          <el-form-item label="收件人邮箱" prop="notification_config.to_emails">
            <el-input
              v-model="toEmailsInput"
              placeholder="请输入收件人邮箱，多个用逗号分隔"
              @blur="updateToEmails"
            />
            <div class="form-tip">支持多个收件人，用逗号分隔</div>
          </el-form-item>
          <el-form-item>
            <el-checkbox v-model="form.notification_config.use_tls">使用TLS加密</el-checkbox>
          </el-form-item>
          <el-form-item>
            <el-checkbox v-model="form.notification_config.use_ssl">使用SSL加密</el-checkbox>
          </el-form-item>
        </template>

        <el-form-item>
          <el-checkbox v-model="form.is_default">设为默认配置</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.is_active">启用配置</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { notificationConfigApi, type NotificationConfig, type NotificationConfigCreate } from '/@/api/v1/notifications'
import { formatDateTime } from '/@/utils/formatTime'

// 响应式数据
const loading = ref(true)
const ids = ref<number[]>([])
const single = ref(true)
const multiple = ref(true)
const showSearch = ref(true)
const total = ref(0)
const configList = ref<NotificationConfig[]>([])
const title = ref('')
const open = ref(false)
const configRef = ref<FormInstance>()

// 查询参数
const queryParams = reactive({
  pageNum: 1,
  pageSize: 10,
  name: '',
  config_type: '',
  is_active: undefined as boolean | undefined
})

// 表单数据
const form = ref<NotificationConfigCreate & { id?: number }>({
  name: '',
  config_type: 'webhook_feishu',
  notification_config: {},
  is_default: false,
  is_active: true
})

// 辅助输入字段
const keywordsInput = ref('')
const mentionedInput = ref('')
const mentionedMobileInput = ref('')
const atMobilesInput = ref('')
const atUserIdsInput = ref('')
const toEmailsInput = ref('')

// 表单验证规则
const rules = computed(() => {
  const baseRules = {
    name: [
      { required: true, message: '配置名称不能为空', trigger: 'blur' }
    ],
    config_type: [
      { required: true, message: '通知类型不能为空', trigger: 'change' }
    ]
  }

  // 根据通知类型添加特定验证规则
  if (form.value.config_type === 'webhook_feishu' || 
      form.value.config_type === 'webhook_wechat' || 
      form.value.config_type === 'webhook_dingtalk') {
    baseRules['notification_config.webhook_url'] = [
      { required: true, message: 'Webhook URL不能为空', trigger: 'blur' }
    ]
  } else if (form.value.config_type === 'telegram') {
    baseRules['notification_config.bot_token'] = [
      { required: true, message: 'Bot Token不能为空', trigger: 'blur' }
    ]
    baseRules['notification_config.chat_id'] = [
      { required: true, message: 'Chat ID不能为空', trigger: 'blur' }
    ]
  } else if (form.value.config_type === 'email') {
    baseRules['notification_config.smtp_server'] = [
      { required: true, message: 'SMTP服务器不能为空', trigger: 'blur' }
    ]
    baseRules['notification_config.smtp_port'] = [
      { required: true, message: 'SMTP端口不能为空', trigger: 'blur' }
    ]
    baseRules['notification_config.username'] = [
      { required: true, message: '用户名不能为空', trigger: 'blur' }
    ]
    baseRules['notification_config.password'] = [
      { required: true, message: '密码不能为空', trigger: 'blur' }
    ]
    baseRules['notification_config.from_email'] = [
      { required: true, message: '发件人邮箱不能为空', trigger: 'blur' },
      { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
    ]
    baseRules['notification_config.to_emails'] = [
      { required: true, message: '收件人邮箱不能为空', trigger: 'blur' }
    ]
  }

  return baseRules
})

// 获取配置列表
const getList = async () => {
  loading.value = true
  try {
    const params = {
      ...queryParams,
      skip: (queryParams.pageNum - 1) * queryParams.pageSize,
      limit: queryParams.pageSize
    }
    const response = await notificationConfigApi.getConfigs(params)
    configList.value = response.data.items || []
    total.value = response.data.total || 0
  } catch (error) {
    console.error('获取配置列表失败:', error)
    ElMessage.error('获取配置列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleQuery = () => {
  queryParams.pageNum = 1
  getList()
}

// 重置搜索
const resetQuery = () => {
  queryParams.pageNum = 1
  queryParams.pageSize = 10
  queryParams.name = ''
  queryParams.config_type = ''
  queryParams.is_active = undefined
  getList()
}

// 多选框选中数据
const handleSelectionChange = (selection: NotificationConfig[]) => {
  ids.value = selection.map(item => item.id!)
  single.value = selection.length !== 1
  multiple.value = !selection.length
}

// 获取类型标签类型
const getTypeTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    webhook_feishu: 'primary',
    webhook_wechat: 'success',
    webhook_dingtalk: 'info',
    telegram: 'warning',
    email: 'danger'
  }
  return typeMap[type] || 'info'
}

// 获取类型标签文本
const getTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    webhook_feishu: '飞书',
    webhook_wechat: '企业微信',
    webhook_dingtalk: '钉钉',
    telegram: 'Telegram',
    email: '邮件'
  }
  return typeMap[type] || type
}

// 状态修改
const handleStatusChange = async (row: NotificationConfig) => {
  const text = row.is_active ? '启用' : '停用'
  try {
    await ElMessageBox.confirm(`确认要${text}"${row.name}"配置吗？`)
    await notificationConfigApi.updateConfig(row.id!, { is_active: row.is_active })
    ElMessage.success(`${text}成功`)
  } catch (error: any) {
    row.is_active = !row.is_active
    console.error(`${text}配置失败:`, error)
    if (error?.message) {
      ElMessage.error(error.message)
    } else {
      ElMessage.error(`${text}失败`)
    }
  }
}

// 新增按钮操作
const handleAdd = () => {
  reset()
  open.value = true
  title.value = '添加通知配置'
}

// 修改按钮操作
const handleUpdate = async (row: NotificationConfig) => {
  reset()
  const id = row.id!
  try {
    const response = await notificationConfigApi.getConfig(id)
    form.value = { ...response.data }
    
    // 设置辅助输入字段
    if (form.value.notification_config) {
      if (form.value.config_type === 'webhook_feishu' && form.value.notification_config.keywords) {
        keywordsInput.value = form.value.notification_config.keywords.join(',')
      }
      if (form.value.config_type === 'webhook_wechat') {
        if (form.value.notification_config.mentioned_list) {
          mentionedInput.value = form.value.notification_config.mentioned_list.join(',')
        }
        if (form.value.notification_config.mentioned_mobile_list) {
          mentionedMobileInput.value = form.value.notification_config.mentioned_mobile_list.join(',')
        }
      }
      if (form.value.config_type === 'webhook_dingtalk') {
        if (form.value.notification_config.at_mobiles) {
          atMobilesInput.value = form.value.notification_config.at_mobiles.join(',')
        }
        if (form.value.notification_config.at_user_ids) {
          atUserIdsInput.value = form.value.notification_config.at_user_ids.join(',')
        }
      }
      if (form.value.config_type === 'email' && form.value.notification_config.to_emails) {
        toEmailsInput.value = Array.isArray(form.value.notification_config.to_emails) 
          ? form.value.notification_config.to_emails.join(',')
          : form.value.notification_config.to_emails
      }
    }
    
    open.value = true
    title.value = '修改通知配置'
  } catch (error) {
    console.error('获取配置详情失败:', error)
    ElMessage.error('获取配置详情失败')
  }
}

// 删除按钮操作
const handleDelete = async (row: NotificationConfig) => {
  try {
    await ElMessageBox.confirm(`是否确认删除配置"${row.name}"？`)
    
    try {
      await notificationConfigApi.deleteConfig(row.id!)
      ElMessage.success('删除成功')
      await getList()
    } catch (error: any) {
      console.error('删除配置失败:', error)
      if (error?.message) {
        ElMessage.error(error.message)
      } else {
        ElMessage.error('删除失败')
      }
    }
  } catch (error) {
    // 用户取消确认对话框，不显示错误信息
    console.log('用户取消删除操作')
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (ids.value.length === 0) {
    ElMessage.warning('请选择要删除的配置')
    return
  }
  
  try {
    await ElMessageBox.confirm(`是否确认删除选中的 ${ids.value.length} 个配置？`)
    
    try {
      await notificationConfigApi.batchDeleteConfigs(ids.value)
      ElMessage.success(`成功删除 ${ids.value.length} 个配置`)
      await getList()
    } catch (error: any) {
      console.error('批量删除失败:', error)
      if (error?.message) {
        ElMessage.error(error.message)
      } else {
        ElMessage.error('批量删除失败')
      }
    }
  } catch (error) {
    // 用户取消确认对话框，不显示错误信息
    console.log('用户取消删除操作')
  }
}

// 设置默认配置
const handleSetDefault = async (row: NotificationConfig) => {
  try {
    await ElMessageBox.confirm(`确认要将"${row.name}"设为默认配置吗？`)
    
    try {
      await notificationConfigApi.setDefaultConfig(row.id!)
      ElMessage.success('设置成功')
      await getList()
    } catch (error: any) {
      console.error('设置默认配置失败:', error)
      if (error?.message) {
        ElMessage.error(error.message)
      } else {
        ElMessage.error('设置失败')
      }
    }
  } catch (error) {
    // 用户取消确认对话框，不显示错误信息
    console.log('用户取消设置操作')
  }
}

// 测试配置
const handleTest = async (row: NotificationConfig) => {
  try {
    await notificationConfigApi.testConfig(row.id!)
    ElMessage.success('测试消息发送成功')
  } catch (error) {
    console.error('测试配置失败:', error)
    ElMessage.error('测试消息发送失败')
  }
}

// 通知类型变化
const handleTypeChange = () => {
  form.value.notification_config = {}
  keywordsInput.value = ''
  mentionedInput.value = ''
  mentionedMobileInput.value = ''
  atMobilesInput.value = ''
  atUserIdsInput.value = ''
  toEmailsInput.value = ''
  
  // 设置默认值
  if (form.value.config_type === 'telegram') {
    form.value.notification_config.parse_mode = 'HTML'
    form.value.notification_config.disable_web_page_preview = false
  } else if (form.value.config_type === 'email') {
    form.value.notification_config.smtp_port = 587
    form.value.notification_config.use_tls = true
    form.value.notification_config.use_ssl = false
  }
}

// 更新关键词
const updateKeywords = () => {
  if (keywordsInput.value) {
    form.value.notification_config.keywords = keywordsInput.value.split(',').map(k => k.trim()).filter(k => k)
  } else {
    delete form.value.notification_config.keywords
  }
}

// 更新提醒成员
const updateMentioned = () => {
  if (mentionedInput.value) {
    form.value.notification_config.mentioned_list = mentionedInput.value.split(',').map(m => m.trim()).filter(m => m)
  } else {
    delete form.value.notification_config.mentioned_list
  }
}

// 更新提醒手机号
const updateMentionedMobile = () => {
  if (mentionedMobileInput.value) {
    form.value.notification_config.mentioned_mobile_list = mentionedMobileInput.value.split(',').map(m => m.trim()).filter(m => m)
  } else {
    delete form.value.notification_config.mentioned_mobile_list
  }
}

// 更新@手机号
const updateAtMobiles = () => {
  if (atMobilesInput.value) {
    form.value.notification_config.at_mobiles = atMobilesInput.value.split(',').map(m => m.trim()).filter(m => m)
  } else {
    delete form.value.notification_config.at_mobiles
  }
}

// 更新@用户ID
const updateAtUserIds = () => {
  if (atUserIdsInput.value) {
    form.value.notification_config.at_user_ids = atUserIdsInput.value.split(',').map(u => u.trim()).filter(u => u)
  } else {
    delete form.value.notification_config.at_user_ids
  }
}

// 更新收件人邮箱
const updateToEmails = () => {
  if (toEmailsInput.value) {
    form.value.notification_config.to_emails = toEmailsInput.value.split(',').map(e => e.trim()).filter(e => e)
  } else {
    delete form.value.notification_config.to_emails
  }
}

// 提交表单
const submitForm = async () => {
  if (!configRef.value) return
  
  try {
    // 先进行表单验证
    await configRef.value.validate()
    
    // 更新webhook_bots中的数据
    updateKeywords()
    updateMentioned()
    updateMentionedMobile()
    updateAtMobiles()
    updateAtUserIds()
    updateToEmails()

    if (form.value.id) {
      await notificationConfigApi.updateConfig(form.value.id, form.value)
      ElMessage.success('修改成功')
    } else {
      await notificationConfigApi.createConfig(form.value)
      ElMessage.success('新增成功')
    }
    open.value = false
    await getList()
  } catch (error: any) {
    console.error('提交表单失败:', error)
    if (error?.message) {
      ElMessage.error(error.message)
    } else {
      ElMessage.error('操作失败')
    }
  }
}

// 取消按钮
const cancel = () => {
  open.value = false
  reset()
}

// 表单重置
const reset = () => {
  form.value = {
    name: '',
    config_type: 'webhook_feishu',
    notification_config: {},
    is_default: false,
    is_active: true
  }
  keywordsInput.value = ''
  mentionedInput.value = ''
  mentionedMobileInput.value = ''
  atMobilesInput.value = ''
  atUserIdsInput.value = ''
  toEmailsInput.value = ''
  
  // 清除表单验证状态
  if (configRef.value) {
    configRef.value.clearValidate()
  }
}

// 初始化
onMounted(() => {
  getList()
})
</script>

<style scoped>
.notification-configs {
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

.webhook-url {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.dialog-footer {
  text-align: right;
}

/* 修复表单验证样式 */
:deep(.el-form-item.is-required .el-form-item__label:before) {
  content: '*';
  color: #f56c6c;
  margin-right: 4px;
  position: static;
  display: inline;
  font-weight: normal;
}

:deep(.el-form-item__label) {
  position: relative;
  display: inline-block;
}

:deep(.el-form-item__error) {
  position: absolute;
  top: 100%;
  left: 0;
  font-size: 12px;
  color: #f56c6c;
  line-height: 1;
  padding-top: 4px;
  z-index: 1;
}

/* 确保表单项有足够的底部间距来显示错误信息 */
:deep(.el-form-item) {
  margin-bottom: 22px;
}
</style>

<style scoped>
.button-group {
  display: flex;
  gap: 4px;
  justify-content: center;
  align-items: center;
  white-space: nowrap;
}

.button-group .el-button {
  margin: 0;
}

.webhook-url {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

.config-info {
  font-size: 12px;
  line-height: 1.4;
}

.config-info > div {
  margin-bottom: 2px;
}

.config-info > div:last-child {
  margin-bottom: 0;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 16px;
}

.dialog-footer {
  text-align: right;
}
</style>