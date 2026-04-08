<template>
  <div class="ai-chat-container">
    <!-- 左侧对话列表 -->
    <div class="conversation-sidebar">
      <div class="sidebar-header">
        <el-button type="primary" :icon="Plus" @click="handleCreateConversation" v-auth="'ai:chat:create'">
          新建对话
        </el-button>
      </div>
      
      <!-- 搜索框 -->
      <div class="search-box">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索对话..."
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
        />
      </div>
      
      <div class="conversation-list">
        <div v-if="filteredConversations.length === 0" class="empty-list">
          <el-empty :description="searchKeyword ? '未找到匹配的对话' : '暂无对话'" :image-size="80" />
        </div>
        <div
          v-for="conv in filteredConversations"
          :key="conv.id"
          :class="['conversation-item', { active: currentConversationId === conv.id }]"
          @click="handleSelectConversation(conv.id)"
        >
          <div class="conversation-content">
            <div class="title">{{ conv.title || '新对话' }}</div>
            <div class="meta">
              <span>{{ conv.message_count || 0 }} 条消息</span>
              <span>{{ formatDate(conv.updation_date) }}</span>
            </div>
          </div>
          <div class="conversation-actions">
            <el-button
              link
              :icon="Edit"
              size="small"
              @click.stop="handleEditTitle(conv)"
              v-auth="'ai:chat:update'"
              title="编辑标题"
            />
            <el-button
              link
              :icon="Download"
              size="small"
              @click.stop="handleExportConversation(conv.id)"
              title="导出对话"
            />
            <el-button
              link
              :icon="Delete"
              size="small"
              type="danger"
              @click.stop="handleDeleteConversation(conv.id)"
              v-auth="'ai:chat:delete'"
              title="删除对话"
            />
          </div>
        </div>
      </div>
    </div>
    
    <!-- 右侧聊天区域 -->
    <div class="chat-main">
      <!-- 顶部导航栏 -->
      <div v-if="currentConversationId" class="chat-navbar">
        <div class="navbar-left">
          <h2>{{ currentConversation?.title || '新对话' }}</h2>
        </div>
        <div class="navbar-right">
          <div class="chat-options">
            <el-select
              v-model="selectedProjectId"
              placeholder="项目"
              size="small"
              style="width: 140px"
              @change="handleProjectChange"
            >
              <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
            <el-switch v-model="useKnowledgeBase" size="small" />
            <el-select
              v-model="selectedKnowledgeBaseId"
              placeholder="知识库来源"
              size="small"
              style="width: 180px"
              :disabled="!useKnowledgeBase"
            >
              <el-option v-for="kb in knowledgeBases" :key="kb.id" :label="kb.name" :value="Number(kb.id)" />
            </el-select>
            <el-switch v-model="useMcp" size="small" />
            <el-select
              v-model="selectedMcpConfigId"
              placeholder="MCP配置"
              size="small"
              style="width: 160px"
              :disabled="!useMcp"
            >
              <el-option v-for="m in mcpConfigs" :key="m.id" :label="m.name" :value="m.id" />
            </el-select>
          </div>
          <div class="connection-status">
            <el-icon :class="['status-icon', isWsConnected ? 'connected' : 'disconnected']">
              <Connection v-if="isWsConnected" />
              <Warning v-else />
            </el-icon>
            <span class="status-text">{{ isWsConnected ? '已连接' : '未连接' }}</span>
          </div>
          <el-button size="small" @click="openMcpRecords">执行记录</el-button>
          <el-tag v-if="messages.length > 0" size="small" type="info">
            {{ messages.length }} 条消息
          </el-tag>
          <el-tag v-if="currentConversation?.total_tokens" size="small" type="warning">
            {{ currentConversation.total_tokens }} Token
          </el-tag>
        </div>
      </div>
      
      <!-- 欢迎界面 -->
      <div v-if="!currentConversationId" class="welcome-screen">
        <div class="welcome-content">
          <div class="ai-logo">
            <el-icon size="64"><ChatDotRound /></el-icon>
          </div>
          <h1>AI 聊天助手</h1>
          <p class="welcome-subtitle">
            智能对话助手，支持实时流式响应
          </p>

          <div class="example-prompts">
            <div class="prompt-card" @click="handleCreateWithPrompt('帮我写一个 Python 快速排序算法')">
              <h4>代码生成</h4>
              <p>帮我写一个 Python 快速排序算法</p>
            </div>
            <div class="prompt-card" @click="handleCreateWithPrompt('解释一下什么是 RESTful API')">
              <h4>技术解答</h4>
              <p>解释一下什么是 RESTful API</p>
            </div>
            <div class="prompt-card" @click="handleCreateWithPrompt('如何优化数据库查询性能？')">
              <h4>最佳实践</h4>
              <p>如何优化数据库查询性能？</p>
            </div>
            <div class="prompt-card" @click="handleCreateWithPrompt('前端性能优化有哪些方法？')">
              <h4>性能优化</h4>
              <p>前端性能优化有哪些方法？</p>
            </div>
          </div>
        </div>
      </div>
      
      <template v-else>
        <!-- 消息列表 -->
        <div ref="messageListRef" class="message-list" @scroll="handleScroll">
          <!-- 加载更多提示 -->
          <div v-if="loadingMessages" class="load-more-tip">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>加载中...</span>
          </div>
          <div v-else-if="!hasMoreMessages && messages.length > 0" class="load-more-tip">
            <span>没有更多消息了</span>
          </div>
          
          <!-- 性能优化提示 -->
          <div v-if="messages.length > maxRenderedMessages" class="performance-tip">
            <el-alert
              type="info"
              :closable="false"
              show-icon
            >
              <template #title>
                为了更好的性能，只显示最近 {{ maxRenderedMessages }} 条消息。
                <el-button link type="primary" size="small" @click="loadMoreMessages">
                  加载更多历史消息
                </el-button>
              </template>
            </el-alert>
          </div>
          
          <div
            v-for="msg in displayMessages"
            :key="msg.id"
            :class="['message-group', msg.role]"
          >
            <div class="message-avatar">
              <div v-if="msg.role === 'user'" class="user-avatar">
                <el-icon><UserFilled /></el-icon>
              </div>
              <div v-else class="ai-avatar">
                <el-icon><ChatDotRound /></el-icon>
              </div>
            </div>
            
            <div class="message-content">
              <div class="message-header">
                <strong class="sender-name">{{ msg.role === 'user' ? '我' : 'AI 助手' }}</strong>
                <span class="time">{{ formatTime(msg.creation_date) }}</span>
              </div>
              
              <div class="message-body">
                <!-- 折叠/展开按钮 -->
                <el-button
                  v-if="msg.content.length > 500"
                  text
                  size="small"
                  :icon="msg.collapsed ? ArrowDown : ArrowUp"
                  class="fold-button"
                  @click="toggleMessageFold(msg)"
                >
                  {{ msg.collapsed ? '展开' : '收起' }}
                </el-button>
                
                <!-- 附件显示 -->
                <div v-if="msg.meta_data?.attachments && msg.meta_data.attachments.length > 0" class="message-attachments">
                  <div
                    v-for="(att, index) in msg.meta_data.attachments"
                    :key="index"
                    class="attachment-preview"
                  >
                    <el-icon class="attachment-icon">
                      <Picture v-if="att.type?.startsWith('image/')" />
                      <Document v-else />
                    </el-icon>
                    <span class="attachment-name">{{ att.name }}</span>
                    <span class="attachment-size">{{ formatFileSize(att.size) }}</span>
                  </div>
                </div>
                
                <div
                  :class="['message-text', { collapsed: msg.collapsed }]"
                  v-html="renderMarkdown(msg.content)"
                ></div>
                
                <!-- 只有内容为空且loading时才显示打字指示器 -->
                <div
                  v-if="msg.role === 'assistant' && msg.loading && !msg.content"
                  class="typing-indicator"
                >
                  <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
              
              <div v-if="!msg.loading" class="message-actions">
                <el-button
                  text
                  size="small"
                  :icon="DocumentCopy"
                  @click="handleCopyMessage(msg.content)"
                  title="复制消息"
                />
                <el-tag v-if="msg.tokens_used" size="small" type="info">Token: {{ msg.tokens_used }}</el-tag>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 输入区域 -->
        <div class="chat-input">
          <div class="input-wrapper">
            <!-- 附件预览 -->
            <div v-if="attachments.length > 0" class="attachments-preview">
              <div
                v-for="attachment in attachments"
                :key="attachment.id"
                class="attachment-item"
              >
                <div class="attachment-icon">
                  <el-icon v-if="attachment.type.startsWith('image/')"><Picture /></el-icon>
                  <el-icon v-else><Document /></el-icon>
                </div>
                <div class="attachment-info">
                  <div class="attachment-name">{{ attachment.name }}</div>
                  <div class="attachment-size">{{ formatFileSize(attachment.size) }}</div>
                  <el-progress
                    v-if="attachment.uploading"
                    :percentage="attachment.uploadProgress || 0"
                    :show-text="false"
                    style="margin-top: 4px"
                  />
                </div>
                <el-button
                  v-if="!attachment.uploading"
                  text
                  circle
                  :icon="Close"
                  size="small"
                  class="remove-btn"
                  @click="handleRemoveAttachment(attachment.id)"
                  title="删除附件"
                />
              </div>
            </div>
            
            <div class="input-container">
              <!-- 上传按钮 -->
              <div class="upload-buttons">
                <el-tooltip content="上传图片" placement="top">
                  <el-button
                    link
                    :icon="Picture"
                    @click="handleSelectImage"
                    :disabled="sending"
                  />
                </el-tooltip>
                <el-tooltip content="上传文件" placement="top">
                  <el-button
                    link
                    :icon="Document"
                    @click="handleSelectFile"
                    :disabled="sending"
                  />
                </el-tooltip>
              </div>
              
              <el-input
                v-model="inputMessage"
                type="textarea"
                :rows="1"
                :autosize="{ minRows: 1, maxRows: 6 }"
                placeholder="向 AI 助手发送消息..."
                :disabled="sending"
                resize="none"
                class="message-input"
                @keydown.enter.exact.prevent="handleSendMessage"
                @keydown.shift.enter.exact="inputMessage += '\n'"
                @keydown.ctrl.k.prevent="handleClearInput"
                @keydown.esc="handleCancelSending"
              />
              <el-button
                :disabled="(!inputMessage.trim() && attachments.length === 0) || sending"
                :loading="sending"
                class="send-button"
                type="primary"
                circle
                @click="handleSendMessage"
              >
                <el-icon><Promotion /></el-icon>
              </el-button>
            </div>
            <div class="input-footer">
              <span class="input-hint">按 Enter 发送消息，Shift + Enter 换行</span>
            </div>
          </div>
          
          <!-- 隐藏的文件输入 -->
          <input
            ref="imageInputRef"
            type="file"
            accept="image/*"
            multiple
            style="display: none"
            @change="handleImageChange"
          />
          <input
            ref="fileInputRef"
            type="file"
            multiple
            style="display: none"
            @change="handleFileChange"
          />
        </div>
      </template>
    </div>
    
    <!-- 编辑标题对话框 -->
    <el-dialog
      v-model="editTitleDialogVisible"
      title="编辑对话标题"
      width="400px"
    >
      <el-input
        v-model="editingTitle"
        placeholder="请输入对话标题"
      />
      <template #footer>
        <el-button @click="editTitleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveTitle">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="mcpRecordDialogVisible"
      title="MCP 执行记录"
      width="860px"
    >
      <el-table v-loading="mcpRecordLoading" :data="mcpRecords" size="small" max-height="520">
        <el-table-column prop="creation_date" label="时间" width="170">
          <template #default="{ row }">{{ formatTime(row.creation_date) }}</template>
        </el-table-column>
        <el-table-column prop="phase" label="阶段" width="100" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : row.status === 'skipped' ? 'info' : 'danger'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="tool_name" label="工具" width="180" show-overflow-tooltip />
        <el-table-column prop="duration_ms" label="耗时(ms)" width="90" />
        <el-table-column label="详情" min-width="260" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.error_message || row.output_summary || '-' }}
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="mcpRecordDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Edit,
  Delete,
  UserFilled,
  Promotion,
  Loading,
  Search,
  DocumentCopy,
  Download,
  ChatDotRound,
  Connection,
  Warning,
  ArrowDown,
  ArrowUp,
  Picture,
  Document,
  Close
} from '@element-plus/icons-vue'
import { useConversationApi } from '/@/api/v1/ai/conversation'
import type { ConversationData, MessageData } from '/@/api/v1/ai/conversation'
import { useFileApi } from '/@/api/v1/common/file'
import { useProjectApi } from '/@/api/v1/projects/project'
import { projectPlatformApi } from '/@/api/v1/projects/platform'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-light.css'

defineOptions({
  name: 'AIChatPage'
})

const conversationApi = useConversationApi()
const fileApi = useFileApi()
const projectApi = useProjectApi()

// 配置 marked 使用 highlight.js
marked.setOptions({
  highlight: function(code: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(code, { language: lang, ignoreIllegals: true }).value
      } catch (err) {
        console.error('Highlight error:', err)
      }
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
  gfm: true
})

// 附件相关
interface Attachment {
  id: string
  name: string
  size: number
  type: string
  url?: string
  file?: File
  uploading?: boolean
  uploadProgress?: number
}

const attachments = ref<Attachment[]>([])
const fileInputRef = ref<HTMLInputElement>()
const imageInputRef = ref<HTMLInputElement>()

// 状态
const conversations = ref<ConversationData[]>([])
const messages = ref<MessageData[]>([])
const currentConversationId = ref<number | null>(null)
const inputMessage = ref('')
const sending = ref(false)
const messageListRef = ref<HTMLElement>()
const searchKeyword = ref('')
const loadingMessages = ref(false)
const hasMoreMessages = ref(true)
const currentPage = ref(1)
const pageSize = 20
const streamingMessage = ref<MessageData | null>(null)  // 正在流式接收的消息
const wsConnection = ref<{ ws: WebSocket; send: (payload: any) => void; close: () => void } | null>(null)  // WebSocket 连接
const isWsConnected = ref(false)  // WebSocket 真实连接状态
const projects = ref<Array<{ id: number; name: string }>>([])
const selectedProjectId = ref<number | null>(null)
const useKnowledgeBase = ref(false)
const selectedKnowledgeBaseId = ref<number | null>(null)
const knowledgeBases = ref<any[]>([])
const useMcp = ref(false)
const selectedMcpConfigId = ref<number | null>(null)
const mcpConfigs = ref<any[]>([])
const mcpRecordDialogVisible = ref(false)
const mcpRecordLoading = ref(false)
const mcpRecords = ref<any[]>([])

// 性能优化：限制渲染的消息数量
const maxRenderedMessages = 100 // 最多渲染100条消息
const displayMessages = computed(() => {
  // 如果消息数量少于限制，全部显示
  if (messages.value.length <= maxRenderedMessages) {
    return messages.value
  }
  // 否则只显示最新的消息
  return messages.value.slice(-maxRenderedMessages)
})

// 虚拟滚动优化：只渲染可见区域的消息
const visibleMessages = ref<MessageData[]>([])
const messageRenderBuffer = 10 // 上下各渲染10条额外消息
const isScrolling = ref(false)
let scrollTimer: any = null

// 编辑标题
const editTitleDialogVisible = ref(false)
const editingConversationId = ref<number | null>(null)
const editingTitle = ref('')

// 当前对话
const currentConversation = computed(() => {
  return conversations.value.find(c => c.id === currentConversationId.value)
})

// 过滤后的对话列表
const filteredConversations = computed(() => {
  if (!searchKeyword.value.trim()) {
    return conversations.value
  }
  
  const keyword = searchKeyword.value.toLowerCase()
  return conversations.value.filter(conv => {
    return conv.title?.toLowerCase().includes(keyword)
  })
})

/**
 * 搜索对话
 */
const handleSearch = () => {
  // 搜索逻辑已通过 computed 实现
}

const openMcpRecords = async () => {
  if (!currentConversationId.value) {
    ElMessage.warning('请先选择对话')
    return
  }
  mcpRecordDialogVisible.value = true
  mcpRecordLoading.value = true
  try {
    const res: any = await conversationApi.getMcpRecords(currentConversationId.value, { limit: 100 })
    if (res?.code === 200) {
      mcpRecords.value = res.data?.records || []
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '获取执行记录失败')
  } finally {
    mcpRecordLoading.value = false
  }
}

const loadProjectOptions = async () => {
  try {
    const res: any = await projectApi.getList({ page: 1, page_size: 50 })
    if (res?.code === 200 && res.data?.items) {
      projects.value = res.data.items
      const stored = localStorage.getItem('defaultProjectId')
      if (stored && projects.value.some((p) => p.id === Number(stored))) {
        selectedProjectId.value = Number(stored)
      } else if (projects.value.length) {
        selectedProjectId.value = projects.value[0].id
      }
      await handleProjectChange()
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '加载项目失败')
  }
}

const handleProjectChange = async () => {
  if (!selectedProjectId.value) return
  localStorage.setItem('defaultProjectId', String(selectedProjectId.value))
  try {
    const [kbRes, mcpRes]: any = await Promise.all([
      projectPlatformApi.knowledge.bases.list(selectedProjectId.value, { page: 1, page_size: 200 }),
      projectPlatformApi.mcp.list(selectedProjectId.value, { page: 1, page_size: 200, is_enabled: true })
    ])
    knowledgeBases.value = kbRes?.data?.items || []
    if (!knowledgeBases.value.some((kb: any) => Number(kb.id) === selectedKnowledgeBaseId.value)) {
      selectedKnowledgeBaseId.value = knowledgeBases.value.length ? Number(knowledgeBases.value[0].id) : null
    }
    mcpConfigs.value = mcpRes?.data?.items || []
    if (!mcpConfigs.value.some((m: any) => m.id === selectedMcpConfigId.value)) {
      selectedMcpConfigId.value = mcpConfigs.value.length ? mcpConfigs.value[0].id : null
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '加载知识库/MCP配置失败')
  }
}

/**
 * 复制消息
 */
const handleCopyMessage = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('消息已复制到剪贴板')
  } catch (error) {
    // 降级方案：使用传统方法
    const textarea = document.createElement('textarea')
    textarea.value = content
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    
    try {
      document.execCommand('copy')
      ElMessage.success('消息已复制到剪贴板')
    } catch (err) {
      ElMessage.error('复制失败，请手动复制')
    }
    
    document.body.removeChild(textarea)
  }
}

/**
 * 清空输入框
 */
const handleClearInput = () => {
  inputMessage.value = ''
  ElMessage.info('输入已清空')
}

/**
 * 取消发送
 */
const handleCancelSending = () => {
  if (sending.value && wsConnection.value) {
    // 关闭 WebSocket 连接会中断流式响应
    wsConnection.value.close()
    
    // 移除流式消息
    if (streamingMessage.value) {
      const index = messages.value.findIndex(m => m.id === streamingMessage.value!.id)
      if (index > -1) {
        messages.value.splice(index, 1)
      }
    }
    
    streamingMessage.value = null
    sending.value = false
    ElMessage.info('已取消发送')
    
    // 重新连接 WebSocket
    if (currentConversationId.value) {
      connectToWebSocket(currentConversationId.value)
    }
  }
}

/**
 * 加载对话列表
 */
const loadConversations = async () => {
  try {
    // 加载更多对话（最多100个）
    const response = await conversationApi.getConversationList({ limit: 100 })
    if (response.code === 200) {
      conversations.value = response.data.conversations
    }
  } catch (error: any) {
    ElMessage.error(error.message || '加载对话列表失败')
  }
}

/**
 * 加载消息列表
 */
const loadMessages = async (conversationId: number, append: boolean = false) => {
  if (loadingMessages.value) return
  
  try {
    loadingMessages.value = true
    const response = await conversationApi.getMessageList(conversationId, { 
      limit: pageSize,
      offset: append ? messages.value.length : 0
    })
    
    if (response.code === 200) {
      if (append) {
        // 追加消息（加载更多）
        messages.value = [...response.data.messages, ...messages.value]
      } else {
        // 替换消息（首次加载或刷新）
        messages.value = response.data.messages
        currentPage.value = 1
      }
      
      // 检查是否还有更多消息
      hasMoreMessages.value = response.data.messages.length === pageSize
      
      await nextTick()
      if (!append) {
        scrollToBottom()
      }
    }
  } catch (error: any) {
    ElMessage.error(error.message || '加载消息列表失败')
  } finally {
    loadingMessages.value = false
  }
}

/**
 * 加载更多消息
 */
const loadMoreMessages = async () => {
  if (!currentConversationId.value || !hasMoreMessages.value || loadingMessages.value) {
    return
  }
  
  const scrollTop = messageListRef.value?.scrollTop || 0
  await loadMessages(currentConversationId.value, true)
  
  // 保持滚动位置
  await nextTick()
  if (messageListRef.value) {
    messageListRef.value.scrollTop = scrollTop + 100
  }
}

/**
 * 监听滚动事件（防抖优化）
 */
let scrollDebounceTimer: any = null
const handleScroll = () => {
  if (!messageListRef.value) return
  
  // 清除之前的定时器
  if (scrollDebounceTimer) {
    clearTimeout(scrollDebounceTimer)
  }
  
  // 使用防抖，减少滚动事件处理频率
  scrollDebounceTimer = setTimeout(() => {
    if (!messageListRef.value) return
    
    // 当滚动到顶部时加载更多
    if (messageListRef.value.scrollTop < 100 && hasMoreMessages.value && !loadingMessages.value) {
      loadMoreMessages()
    }
  }, 150) // 150ms 防抖延迟
}

/**
 * 创建对话
 */
const handleCreateConversation = async () => {
  try {
    const response = await conversationApi.createConversation({
      title: '新对话'
    })
    
    if (response.code === 200) {
      await loadConversations()
      handleSelectConversation(response.data.id)
      ElMessage.success('对话创建成功')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '创建对话失败')
  }
}

/**
 * 选择对话
 */
const handleSelectConversation = async (conversationId: number) => {
  // 关闭之前的 WebSocket 连接
  if (wsConnection.value) {
    wsConnection.value.close()
    wsConnection.value = null
  }
  
  currentConversationId.value = conversationId
  await loadMessages(conversationId)
  
  // 建立新的 WebSocket 连接
  connectToWebSocket(conversationId)
}

/**
 * 连接 WebSocket
 */
const connectToWebSocket = (conversationId: number) => {
  try {
    wsConnection.value = conversationApi.connectWebSocket(
      conversationId,
      // onMessage 回调
      (event) => {
        handleWebSocketMessage(event)
      },
      // onError 回调
      (error) => {
        console.error('WebSocket 连接错误:', error)
        isWsConnected.value = false
      },
      // onClose 回调
      () => {
        console.log('WebSocket 连接已关闭')
        isWsConnected.value = false
        wsConnection.value = null
      },
      // onOpen 回调
      () => {
        console.log('WebSocket 连接成功')
        isWsConnected.value = true
        ElMessage.success('连接成功')
      }
    )
  } catch (error: any) {
    console.error('WebSocket 连接失败:', error)
    isWsConnected.value = false
    ElMessage.error(error.message || 'WebSocket 连接失败')
  }
}

/**
 * 处理 WebSocket 消息
 */
const handleWebSocketMessage = (event: any) => {
  if (event.type === 'connected') {
    console.log('WebSocket 连接成功:', event.message)
  } else if (event.type === 'start') {
    console.log('开始接收流式响应')
  } else if (event.type === 'user_message') {
    // 更新用户消息的真实 ID
    if (event.data && messages.value.length > 0) {
      const lastUserMsg = [...messages.value].reverse().find(m => m.role === 'user')
      if (lastUserMsg && lastUserMsg.id > Date.now() - 10000) {
        lastUserMsg.id = event.data.id
      }
    }
  } else if (event.type === 'content') {
    // 追加内容到流式消息
    if (streamingMessage.value && event.data) {
      streamingMessage.value.content += event.data.content
      // 自动滚动到底部
      nextTick(() => scrollToBottom())
    }
  } else if (event.type === 'assistant_message') {
    // 更新 AI 消息的真实 ID 和完整信息
    if (streamingMessage.value && event.data) {
      streamingMessage.value.id = event.data.id
      streamingMessage.value.tokens_used = event.data.tokens_used
      streamingMessage.value.creation_date = event.data.creation_date
    }
  } else if (event.type === 'done') {
    console.log('流式响应完成')
    if (streamingMessage.value) {
      streamingMessage.value.loading = false
      streamingMessage.value.collapsed = streamingMessage.value.content.length > 500
    }
    streamingMessage.value = null
    sending.value = false
    // 刷新对话列表
    loadConversations()
  } else if (event.type === 'error') {
    ElMessage.error(event.message || '发送消息失败')
    // 移除临时消息
    if (streamingMessage.value) {
      const index = messages.value.findIndex(m => m.id === streamingMessage.value!.id)
      if (index > -1) {
        messages.value.splice(index, 1)
      }
    }
    streamingMessage.value = null
    sending.value = false
  } else if (event.type === 'pong') {
    // 心跳响应
    console.log('收到心跳响应')
  }
}

/**
 * 发送消息（WebSocket 流式响应）
 */
const handleSendMessage = async () => {
  const content = inputMessage.value.trim()
  
  // 验证：必须有消息内容或附件
  if (!content && attachments.value.length === 0) {
    ElMessage.warning('请输入消息内容或上传附件')
    return
  }
  
  if (!currentConversationId.value) {
    ElMessage.warning('请先选择或创建一个对话')
    return
  }
  
  if (!wsConnection.value) {
    ElMessage.error('WebSocket 未连接，请刷新页面重试')
    return
  }
  
  // 检查连接状态
  if (!isWsConnected.value) {
    ElMessage.warning('正在连接中，请稍候...')
    return
  }
  
  // 检查是否有正在上传的附件
  const uploadingAttachments = attachments.value.filter(a => a.uploading)
  if (uploadingAttachments.length > 0) {
    ElMessage.warning('请等待附件上传完成')
    return
  }
  
  inputMessage.value = ''
  sending.value = true
  
  try {
    // 准备附件数据
    const attachmentData = attachments.value.map(att => ({
      name: att.name,
      size: att.size,
      type: att.type,
      url: att.url
    }))
    
    // 构建完整的消息内容
    let fullContent = content
    
    // 如果有附件，将附件信息添加到消息中
    if (attachmentData.length > 0) {
      fullContent += '\n\n[附件]:\n'
      attachmentData.forEach((att, index) => {
        if (att.type.startsWith('image/')) {
          fullContent += `${index + 1}. 图片: ${att.name}\n`
        } else {
          fullContent += `${index + 1}. 文件: ${att.name} (${formatFileSize(att.size)})\n`
        }
      })
    }
    
    // 创建临时的用户消息（立即显示）
    const tempUserMessage: MessageData = {
      id: Date.now(),  // 临时 ID
      conversation_id: currentConversationId.value,
      role: 'user',
      content: fullContent,
      message_type: 'text',
      creation_date: new Date().toISOString(),
      collapsed: fullContent.length > 500,
      meta_data: attachmentData.length > 0 ? { attachments: attachmentData } : undefined
    }
    messages.value.push(tempUserMessage)
    
    // 创建临时的 AI 消息（用于流式显示）
    streamingMessage.value = {
      id: Date.now() + 1,  // 临时 ID
      conversation_id: currentConversationId.value,
      role: 'assistant',
      content: '',  // 内容将逐步填充
      message_type: 'text',
      creation_date: new Date().toISOString(),
      loading: true,
      collapsed: false
    }
    messages.value.push(streamingMessage.value)
    
    // 清空附件列表
    attachments.value = []
    
    // 滚动到底部
    await nextTick()
    scrollToBottom()
    
    // 通过 WebSocket 发送消息，同时携带知识库/MCP选项
    wsConnection.value.send({
      content: content || '[发送了附件]',
      attachments: attachmentData,
      project_id: selectedProjectId.value || undefined,
      use_knowledge_base: useKnowledgeBase.value && !!selectedKnowledgeBaseId.value,
      knowledge_base_id: selectedKnowledgeBaseId.value || undefined,
      use_mcp: useMcp.value && !!selectedMcpConfigId.value,
      mcp_config_id: selectedMcpConfigId.value || undefined
    })
  } catch (error: any) {
    ElMessage.error(error.message || '发送消息失败')
    // 移除临时消息
    if (streamingMessage.value) {
      const index = messages.value.findIndex(m => m.id === streamingMessage.value!.id)
      if (index > -1) {
        messages.value.splice(index, 1)
      }
    }
    streamingMessage.value = null
    sending.value = false
    // 恢复输入内容
    inputMessage.value = content
  }
}

/**
 * 编辑标题
 */
const handleEditTitle = (conversation: ConversationData) => {
  editingConversationId.value = conversation.id
  editingTitle.value = conversation.title || ''
  editTitleDialogVisible.value = true
}

/**
 * 保存标题
 */
const handleSaveTitle = async () => {
  if (!editingConversationId.value) return
  
  try {
    const response = await conversationApi.updateConversation(
      editingConversationId.value,
      { title: editingTitle.value }
    )
    
    if (response.code === 200) {
      await loadConversations()
      editTitleDialogVisible.value = false
      ElMessage.success('标题更新成功')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '更新标题失败')
  }
}

/**
 * 导出对话
 */
const handleExportConversation = async (conversationId: number) => {
  try {
    // 获取对话信息
    const conv = conversations.value.find(c => c.id === conversationId)
    if (!conv) return
    
    // 分批获取所有消息（每次最多500条）
    let allMessages: MessageData[] = []
    let offset = 0
    const batchSize = 500
    let hasMore = true
    
    while (hasMore) {
      const response = await conversationApi.getMessageList(conversationId, { 
        limit: batchSize,
        offset: offset 
      })
      
      if (response.code !== 200) {
        ElMessage.error('获取消息失败')
        return
      }
      
      const messages = response.data.messages
      allMessages = [...allMessages, ...messages]
      
      // 如果返回的消息数少于批次大小，说明没有更多了
      hasMore = messages.length === batchSize
      offset += batchSize
    }
    
    // 生成 Markdown 格式的内容
    let content = `# ${conv.title || '对话'}\n\n`
    content += `**创建时间**: ${formatTime(conv.creation_date)}\n`
    content += `**消息数量**: ${allMessages.length}\n`
    content += `**总 Token**: ${conv.total_tokens || 0}\n\n`
    content += `---\n\n`
    
    allMessages.forEach((msg, index) => {
      const role = msg.role === 'user' ? '👤 用户' : '🤖 AI 助手'
      content += `## ${role} (${formatTime(msg.creation_date)})\n\n`
      content += `${msg.content}\n\n`
      
      if (msg.tokens_used) {
        content += `*Token: ${msg.tokens_used}*\n\n`
      }
      
      if (index < allMessages.length - 1) {
        content += `---\n\n`
      }
    })
    
    // 创建下载链接
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${conv.title || '对话'}_${new Date().getTime()}.md`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    ElMessage.success('对话已导出')
  } catch (error: any) {
    ElMessage.error(error.message || '导出对话失败')
  }
}

/**
 * 删除对话
 */
const handleDeleteConversation = async (conversationId: number) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个对话吗？删除后无法恢复。',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await conversationApi.deleteConversation(conversationId)
    
    if (response.code === 200) {
      await loadConversations()
      
      // 如果删除的是当前对话，清空消息列表
      if (currentConversationId.value === conversationId) {
        currentConversationId.value = null
        messages.value = []
      }
      
      ElMessage.success('对话删除成功')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除对话失败')
    }
  }
}

/**
 * 渲染 Markdown
 */
const renderMarkdown = (content: string) => {
  if (!content) return ''
  const html = marked(content)
  return DOMPurify.sanitize(html)
}

/**
 * 折叠/展开消息
 */
const toggleMessageFold = (message: MessageData) => {
  message.collapsed = !message.collapsed
}

/**
 * 创建对话并发送提示词
 */
const handleCreateWithPrompt = async (prompt: string) => {
  try {
    const response = await conversationApi.createConversation({
      title: '新对话'
    })
    
    if (response.code === 200) {
      await loadConversations()
      await handleSelectConversation(response.data.id)
      inputMessage.value = prompt
      // 自动发送
      await nextTick()
      handleSendMessage()
    }
  } catch (error: any) {
    ElMessage.error(error.message || '创建对话失败')
  }
}

/**
 * 选择图片
 */
const handleSelectImage = () => {
  imageInputRef.value?.click()
}

/**
 * 选择文件
 */
const handleSelectFile = () => {
  fileInputRef.value?.click()
}

/**
 * 处理图片选择
 */
const handleImageChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (!files || files.length === 0) return
  
  handleFilesSelected(Array.from(files), true)
  
  // 清空 input，允许重复选择同一文件
  target.value = ''
}

/**
 * 处理文件选择
 */
const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (!files || files.length === 0) return
  
  handleFilesSelected(Array.from(files), false)
  
  // 清空 input，允许重复选择同一文件
  target.value = ''
}

/**
 * 处理选中的文件
 */
const handleFilesSelected = async (files: File[], isImage: boolean) => {
  for (const file of files) {
    // 验证文件
    if (isImage) {
      if (!file.type.startsWith('image/')) {
        ElMessage.warning(`${file.name} 不是图片文件`)
        continue
      }
      // 限制图片大小为 10MB
      if (file.size > 10 * 1024 * 1024) {
        ElMessage.warning(`${file.name} 超过 10MB 限制`)
        continue
      }
    } else {
      // 限制文件大小为 50MB
      if (file.size > 50 * 1024 * 1024) {
        ElMessage.warning(`${file.name} 超过 50MB 限制`)
        continue
      }
    }
    
    // 创建附件对象
    const attachment: Attachment = {
      id: Date.now().toString() + Math.random(),
      name: file.name,
      size: file.size,
      type: file.type,
      file: file,
      uploading: true,
      uploadProgress: 0
    }
    
    attachments.value.push(attachment)
    
    // 上传文件
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fileApi.upload(formData)
      
      if (response.code === 200) {
        // 使用 Vue 的响应式更新
        const index = attachments.value.findIndex(a => a.id === attachment.id)
        if (index > -1) {
          attachments.value[index] = {
            ...attachments.value[index],
            uploading: false,
            url: response.data.file_url || response.data.url || response.data.file_path
          }
        }
        ElMessage.success(`${file.name} 上传成功`)
      } else {
        throw new Error(response.msg || '上传失败')
      }
    } catch (error: any) {
      ElMessage.error(`${file.name} 上传失败: ${error.message}`)
      // 移除上传失败的附件
      const index = attachments.value.findIndex(a => a.id === attachment.id)
      if (index > -1) {
        attachments.value.splice(index, 1)
      }
    }
  }
}

/**
 * 移除附件
 */
const handleRemoveAttachment = (attachmentId: string) => {
  const index = attachments.value.findIndex(a => a.id === attachmentId)
  if (index > -1) {
    attachments.value.splice(index, 1)
  }
}

/**
 * 格式化文件大小
 */
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

/**
 * 滚动到底部
 */
const scrollToBottom = () => {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

/**
 * 格式化日期
 */
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`
  
  return date.toLocaleDateString()
}

/**
 * 格式化时间
 */
const formatTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}

// 初始化
onMounted(() => {
  loadConversations()
  loadProjectOptions()
})

// 组件卸载时关闭 WebSocket
onUnmounted(() => {
  if (wsConnection.value) {
    wsConnection.value.close()
    wsConnection.value = null
  }
  
  // 清理定时器
  if (scrollDebounceTimer) {
    clearTimeout(scrollDebounceTimer)
  }
})
</script>

<style scoped lang="scss">
.ai-chat-container {
  display: flex;
  height: calc(100vh - 120px);
  background-color: var(--el-bg-color);
  border-radius: 8px;
  overflow: hidden;
  
  .conversation-sidebar {
    width: 280px;
    background-color: var(--el-bg-color);
    border-right: 1px solid var(--el-border-color-light);
    display: flex;
    flex-direction: column;
    
    .sidebar-header {
      padding: 16px;
      border-bottom: 1px solid var(--el-border-color-light);
      
      .el-button {
        width: 100%;
      }
    }
    
    .search-box {
      padding: 12px 16px;
      border-bottom: 1px solid var(--el-border-color-light);
    }
    
    .conversation-list {
      flex: 1;
      overflow-y: auto;
      padding: 8px;
      
      .empty-list {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 200px;
      }
      
      .conversation-item {
        display: flex;
        align-items: center;
        padding: 12px;
        margin-bottom: 4px;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.3s;
        
        &:hover {
          background-color: var(--el-fill-color-light);
          
          .conversation-actions {
            opacity: 1;
          }
        }
        
        &.active {
          background-color: var(--el-color-primary-light-9);
          border-left: 3px solid var(--el-color-primary);
        }
        
        .conversation-content {
          flex: 1;
          min-width: 0;
          
          .title {
            font-size: 14px;
            font-weight: 500;
            color: var(--el-text-color-primary);
            margin-bottom: 4px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
          
          .meta {
            font-size: 12px;
            color: var(--el-text-color-secondary);
            display: flex;
            justify-content: space-between;
          }
        }
        
        .conversation-actions {
          opacity: 0;
          transition: opacity 0.3s;
          display: flex;
          gap: 4px;
        }
      }
    }
  }
  
  .chat-main {
    position: relative;
    flex: 1;
    display: flex;
    flex-direction: column;
    background-color: var(--el-bg-color);
    overflow: hidden;
    
    .chat-navbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 24px;
      background: var(--el-bg-color);
      border-bottom: 1px solid var(--el-border-color-light);

      .navbar-left {
        h2 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
      }

      .navbar-right {
        display: flex;
        gap: 16px;
        align-items: center;

        .chat-options {
          display: flex;
          gap: 8px;
          align-items: center;
        }

        .connection-status {
          display: flex;
          gap: 8px;
          align-items: center;
          font-size: 12px;

          .status-icon {
            &.connected {
              color: var(--el-color-success);
            }
            &.disconnected {
              color: var(--el-color-danger);
            }
          }

          .status-text {
            color: var(--el-text-color-secondary);
          }
        }
      }
    }
    
    .welcome-screen {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      padding: 32px;
      text-align: center;

      .welcome-content {
        max-width: 800px;

        .ai-logo {
          margin-bottom: 24px;
          color: var(--el-color-primary);
        }

        h1 {
          margin: 0 0 16px;
          font-size: 32px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }

        .welcome-subtitle {
          margin-bottom: 32px;
          font-size: 16px;
          line-height: 1.5;
          color: var(--el-text-color-secondary);
        }

        .example-prompts {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 16px;
          max-width: 600px;

          .prompt-card {
            padding: 20px;
            text-align: left;
            cursor: pointer;
            background: var(--el-bg-color-page);
            border: 1px solid var(--el-border-color-light);
            border-radius: 12px;
            transition: all 0.2s ease;

            &:hover {
              border-color: var(--el-color-primary);
              box-shadow: var(--el-box-shadow-light);
              transform: translateY(-2px);
            }

            h4 {
              margin: 0 0 8px;
              font-size: 14px;
              font-weight: 600;
              color: var(--el-text-color-primary);
            }

            p {
              margin: 0;
              font-size: 13px;
              line-height: 1.4;
              color: var(--el-text-color-secondary);
            }
          }
        }
      }
    }
    
    .message-list {
      flex: 1;
      overflow-y: auto;
      padding: 24px;
      padding-bottom: 140px;
      width: 100%;
      
      .load-more-tip {
        text-align: center;
        padding: 12px;
        color: var(--el-text-color-secondary);
        font-size: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
      }
      
      .performance-tip {
        margin-bottom: 16px;
        
        :deep(.el-alert) {
          background-color: var(--el-color-info-light-9);
          border: 1px solid var(--el-color-info-light-7);
        }
      }
      
      .message-group {
        display: flex;
        gap: 16px;
        margin-bottom: 32px;
        max-width: 100%;
        
        &.user {
          flex-direction: row-reverse;
          
          .message-content {
            align-items: flex-end;
            
            .message-text {
              background-color: var(--el-color-primary);
              color: white;
            }
          }
        }
        
        .message-avatar {
          flex-shrink: 0;

          .user-avatar {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            font-size: 14px;
            color: white;
            background: var(--el-color-primary);
            border-radius: 50%;
          }

          .ai-avatar {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            font-size: 14px;
            color: white;
            background: var(--el-color-success);
            border-radius: 50%;
          }
        }
        
        .message-content {
          flex: 1;
          min-width: 0;
          max-width: 85%;

          .message-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;

            .sender-name {
              font-size: 14px;
              font-weight: 600;
              color: var(--el-text-color-primary);
            }
            
            .time {
              font-size: 12px;
              color: var(--el-text-color-secondary);
            }
          }
          
          .message-body {
            .fold-button {
              padding: 0;
              margin-bottom: 8px;
              font-size: 12px;
              color: var(--el-text-color-secondary);

              &:hover {
                color: var(--el-color-primary);
              }
            }
            
            .message-attachments {
              display: flex;
              flex-wrap: wrap;
              gap: 8px;
              margin-bottom: 12px;
              
              .attachment-preview {
                display: flex;
                align-items: center;
                gap: 6px;
                padding: 6px 12px;
                background: var(--el-bg-color);
                border: 1px solid var(--el-border-color-light);
                border-radius: 6px;
                font-size: 13px;
                
                .attachment-icon {
                  font-size: 16px;
                  color: var(--el-color-primary);
                }
                
                .attachment-name {
                  color: var(--el-text-color-primary);
                  max-width: 150px;
                  overflow: hidden;
                  text-overflow: ellipsis;
                  white-space: nowrap;
                }
                
                .attachment-size {
                  color: var(--el-text-color-secondary);
                  font-size: 12px;
                }
              }
            }

            .message-text {
              padding: 12px 16px;
              border-radius: 8px;
              background-color: var(--el-fill-color-light);
              font-size: 15px;
              line-height: 1.6;
              color: var(--el-text-color-primary);
              word-wrap: break-word;
              word-break: break-word;
              transition: all 0.3s ease;

              &.collapsed {
                position: relative;
                max-height: 120px;
                overflow: hidden;

                &::after {
                  position: absolute;
                  right: 0;
                  bottom: 0;
                  left: 0;
                  height: 40px;
                  content: "";
                  background: linear-gradient(to bottom, transparent, var(--el-fill-color-light));
                }
              }

              :deep(p) {
                margin: 0 0 12px;

                &:last-child {
                  margin-bottom: 0;
                }
              }

              :deep(code) {
                padding: 2px 6px;
                font-family: "Consolas", "Monaco", "Courier New", monospace;
                font-size: 14px;
                background: rgba(0, 0, 0, 0.06);
                border-radius: 4px;
              }

              :deep(pre) {
                padding: 16px;
                margin: 12px 0;
                overflow-x: auto;
                background: #282c34;
                border-radius: 8px;

                code {
                  padding: 0;
                  color: #abb2bf;
                  background: none;
                }
              }
              
              :deep(ul), :deep(ol) {
                margin: 8px 0;
                padding-left: 24px;
              }
              
              :deep(blockquote) {
                margin: 8px 0;
                padding-left: 12px;
                border-left: 3px solid var(--el-border-color);
                color: var(--el-text-color-secondary);
              }
              
              :deep(table) {
                width: 100%;
                margin: 8px 0;
                border-collapse: collapse;
                
                th, td {
                  padding: 8px;
                  border: 1px solid var(--el-border-color);
                }
                
                th {
                  background: var(--el-fill-color);
                  font-weight: 600;
                }
              }
            }

            .typing-indicator {
              display: flex;
              gap: 8px;
              align-items: center;
              padding: 12px 16px;
              color: var(--el-text-color-secondary);

              .typing-dots {
                display: flex;
                gap: 4px;

                span {
                  width: 8px;
                  height: 8px;
                  background: var(--el-text-color-secondary);
                  border-radius: 50%;
                  animation: typing 1.4s infinite;

                  &:nth-child(2) {
                    animation-delay: 0.2s;
                  }
                  &:nth-child(3) {
                    animation-delay: 0.4s;
                  }
                }
              }
            }
          }
          
          .message-actions {
            display: flex;
            gap: 8px;
            align-items: center;
            margin-top: 8px;
            opacity: 0;
            transition: opacity 0.2s ease;

            .el-button {
              min-height: auto;
              padding: 4px 8px;
            }
          }

          &:hover .message-actions {
            opacity: 1;
          }
        }
        
        // 用户消息的特殊样式
        &.user .message-content .message-text {
          background-color: var(--el-color-primary);
          color: white;
          
          :deep(code) {
            background: rgba(255, 255, 255, 0.2);
            color: white;
          }
          
          &.collapsed::after {
            background: linear-gradient(to bottom, transparent, var(--el-color-primary));
          }
        }
      }
    }
    
    .chat-input {
      position: absolute;
      right: 0;
      bottom: 0;
      left: 0;
      z-index: 10;
      padding: 16px 24px 24px;
      background: var(--el-bg-color);
      border-top: 1px solid var(--el-border-color-light);
      backdrop-filter: blur(10px);

      .input-wrapper {
        width: 100%;
        padding: 0 24px;
        margin: 0 auto;
        
        .attachments-preview {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-bottom: 12px;
          padding: 12px;
          background: var(--el-bg-color-page);
          border-radius: 8px;
          
          .attachment-item {
            position: relative;
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 32px 8px 12px;
            background: var(--el-bg-color);
            border: 1px solid var(--el-border-color);
            border-radius: 6px;
            transition: all 0.2s;
            
            &:hover {
              border-color: var(--el-color-primary);
              box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }
            
            .attachment-icon {
              font-size: 24px;
              color: var(--el-color-primary);
            }
            
            .attachment-info {
              flex: 1;
              min-width: 0;
              
              .attachment-name {
                font-size: 13px;
                color: var(--el-text-color-primary);
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                max-width: 200px;
              }
              
              .attachment-size {
                font-size: 12px;
                color: var(--el-text-color-secondary);
                margin-top: 2px;
              }
            }
            
            .remove-btn {
              position: absolute;
              top: 4px;
              right: 4px;
              color: var(--el-color-info);
              transition: all 0.2s;
              
              &:hover {
                color: var(--el-color-danger);
                transform: scale(1.1);
              }
            }
          }
        }

        .input-container {
          position: relative;
          display: flex;
          align-items: flex-end;
          gap: 8px;
          background: var(--el-bg-color-page);
          border: 1px solid var(--el-border-color);
          border-radius: 12px;
          box-shadow: var(--el-box-shadow-light);
          transition: border-color 0.2s ease;

          &:focus-within {
            border-color: var(--el-color-primary);
            box-shadow: var(--el-box-shadow);
          }
          
          .upload-buttons {
            display: flex;
            gap: 4px;
            padding: 12px 0 12px 12px;
            
            .el-button {
              font-size: 20px;
              color: var(--el-text-color-secondary);
              
              &:hover {
                color: var(--el-color-primary);
              }
            }
          }

          .message-input {
            flex: 1;
            
            :deep(.el-textarea__inner) {
              min-height: 52px;
              padding: 18px 70px 18px 8px;
              font-size: 15px;
              line-height: 1.6;
              resize: none;
              background: transparent;
              border: none;
              box-shadow: none;

              &:focus {
                border: none;
                box-shadow: none;
              }
            }
          }

          .send-button {
            position: absolute;
            right: 10px;
            bottom: 10px;
            width: 40px;
            height: 40px;
            min-height: 40px;
            padding: 0;
            border-radius: 50%;
            box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
            transition: all 0.2s ease;

            &:hover:not(:disabled) {
              box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
              transform: translateY(-2px);
            }
          }
        }

        .input-footer {
          display: flex;
          justify-content: center;
          margin-top: 12px;

          .input-hint {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
      }
    }
  }
}

@keyframes typing {
  0%,
  20% {
    opacity: 0.4;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1);
  }
  80%,
  100% {
    opacity: 0.4;
    transform: scale(0.8);
  }
}

// 滚动条样式
.message-list::-webkit-scrollbar {
  width: 6px;
}

.message-list::-webkit-scrollbar-track {
  background: transparent;
}

.message-list::-webkit-scrollbar-thumb {
  background: var(--el-fill-color);
  border-radius: 3px;

  &:hover {
    background: var(--el-fill-color-dark);
  }
}

.conversation-list::-webkit-scrollbar {
  width: 6px;
}

.conversation-list::-webkit-scrollbar-track {
  background: transparent;
}

.conversation-list::-webkit-scrollbar-thumb {
  background: var(--el-fill-color);
  border-radius: 3px;

  &:hover {
    background: var(--el-fill-color-dark);
  }
}
</style>
