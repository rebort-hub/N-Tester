/**
 * 对话管理 API
 */
import request from '/@/utils/request'
import { Session } from '/@/utils/storage'

// ==================== 类型定义 ====================

/**
 * 对话数据
 */
export interface ConversationData {
  id: number
  session_id: string
  title: string | null
  llm_config_id: number | null
  user_id: number
  is_active: boolean
  creation_date: string
  updation_date: string
  message_count?: number
  total_tokens?: number  // 总 token 数
}

/**
 * 消息数据
 */
export interface MessageData {
  id: number
  conversation_id: number
  role: 'system' | 'user' | 'assistant'
  content: string
  message_type: string
  metadata?: Record<string, any>
  meta_data?: Record<string, any>  // 兼容后端字段名
  tokens_used?: number
  creation_date: string
  loading?: boolean  // 是否正在加载（流式响应中）
  collapsed?: boolean  // 是否折叠显示
  total_tokens?: number  // 总 token 数
}

/**
 * 创建对话请求
 */
export interface ConversationCreateRequest {
  title?: string
  llm_config_id?: number
}

/**
 * 更新对话请求
 */
export interface ConversationUpdateRequest {
  title?: string
  llm_config_id?: number
  is_active?: boolean
}

/**
 * 发送消息请求
 */
export interface SendMessageRequest {
  content: string
  stream?: boolean
  attachments?: Array<{
    name: string
    size: number
    type: string
    url: string
  }>
}

/**
 * 发送消息响应
 */
export interface SendMessageResponse {
  user_message: MessageData
  assistant_message: MessageData
  total_tokens?: number
}

/**
 * 对话列表响应
 */
export interface ConversationListResponse {
  conversations: ConversationData[]
  total: number
}

/**
 * 消息列表响应
 */
export interface MessageListResponse {
  messages: MessageData[]
  total: number
}

/**
 * SSE 消息事件
 */
export interface SSEMessageEvent {
  type: 'start' | 'user_message' | 'content' | 'assistant_message' | 'done' | 'error' | 'connected' | 'pong'
  data?: any
  message?: string
  conversation_id?: number
}

/**
 * WebSocket 消息请求
 */
export interface WSMessageRequest {
  type: 'message' | 'ping'
  content?: string
  attachments?: Array<{
    name: string
    size: number
    type: string
    url: string
  }>
  project_id?: number
  use_knowledge_base?: boolean
  knowledge_base_id?: number
  use_mcp?: boolean
  mcp_config_id?: number
}

// ==================== API 函数 ====================

/**
 * 对话管理 API
 */
export const useConversationApi = () => {
  /**
   * 创建对话
   */
  const createConversation = (data: ConversationCreateRequest) => {
    return request<ConversationData>({
      url: '/v1/ai/conversation',
      method: 'post',
      data
    })
  }

  /**
   * 获取对话列表
   */
  const getConversationList = (params?: { skip?: number; limit?: number }) => {
    return request<ConversationListResponse>({
      url: '/v1/ai/conversation',
      method: 'get',
      params
    })
  }

  /**
   * 获取对话详情
   */
  const getConversation = (id: number) => {
    return request<ConversationData>({
      url: `/v1/ai/conversation/${id}`,
      method: 'get'
    })
  }

  /**
   * 更新对话
   */
  const updateConversation = (id: number, data: ConversationUpdateRequest) => {
    return request<ConversationData>({
      url: `/v1/ai/conversation/${id}`,
      method: 'put',
      data
    })
  }

  /**
   * 删除对话
   */
  const deleteConversation = (id: number) => {
    return request<void>({
      url: `/v1/ai/conversation/${id}`,
      method: 'delete'
    })
  }

  /**
   * 获取消息列表
   */
  const getMessageList = (conversationId: number, params?: { skip?: number; limit?: number }) => {
    return request<MessageListResponse>({
      url: `/v1/ai/conversation/${conversationId}/messages`,
      method: 'get',
      params
    })
  }

  /**
   * 获取 MCP 执行记录
   */
  const getMcpRecords = (conversationId: number, params?: { limit?: number }) => {
    return request<{ records: any[]; total: number }>({
      url: `/v1/ai/conversation/${conversationId}/mcp-records`,
      method: 'get',
      params
    })
  }


  const sendMessage = (conversationId: number, data: SendMessageRequest) => {
    return request<SendMessageResponse>({
      url: `/v1/ai/conversation/${conversationId}/messages`,
      method: 'post',
      data
    })
  }

  /**
   * 发送消息（流式响应 SSE）
   * @param conversationId 对话 ID
   * @param data 消息数据
   * @param onMessage 消息回调
   * @param onError 错误回调
   * @param onComplete 完成回调
   * @returns 取消函数
   */
  const sendMessageStream = (
    conversationId: number,
    data: SendMessageRequest,
    onMessage: (event: SSEMessageEvent) => void,
    onError?: (error: Error) => void,
    onComplete?: () => void
  ): (() => void) => {
    const baseURL = import.meta.env.VITE_API_BASE_URL || ''
    const token = Session.get('token') || ''
    
 
    const url = `${baseURL}/api/v1/ai/conversation/${conversationId}/messages/stream`
    

    let aborted = false
    
    const fetchSSE = async () => {
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(data)
        })
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const reader = response.body?.getReader()
        const decoder = new TextDecoder()
        
        if (!reader) {
          throw new Error('Response body is null')
        }
        
        while (!aborted) {
          const { done, value } = await reader.read()
          
          if (done) {
            if (onComplete) {
              onComplete()
            }
            break
          }
          
          // 解码数据
          const chunk = decoder.decode(value, { stream: true })
          
          // 处理 SSE 数据（可能包含多个事件）
          const lines = chunk.split('\n')
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.substring(6)
              
              try {
                const event = JSON.parse(dataStr)
                onMessage(event)
                
                // 如果收到完成或错误事件，结束
                if (event.type === 'done' || event.type === 'error') {
                  aborted = true
                  if (onComplete) {
                    onComplete()
                  }
                  break
                }
              } catch (e) {
                console.error('Failed to parse SSE data:', e)
              }
            }
          }
        }
      } catch (error) {
        console.error('SSE fetch error:', error)
        if (onError && !aborted) {
          onError(error as Error)
        }
      }
    }
    
    // 启动 SSE 连接
    fetchSSE()
    
    // 返回取消函数
    return () => {
      aborted = true
    }
  }

  /**
   * 发送消息（WebSocket 流式响应）- 简化版本
   * @param conversationId 对话 ID
   * @param onMessage 消息回调
   * @param onError 错误回调
   * @param onClose 关闭回调
   * @param onOpen 连接成功回调
   * @returns WebSocket 实例和发送函数
   */
  const connectWebSocket = (
    conversationId: number,
    onMessage: (event: SSEMessageEvent) => void,
    onError?: (error: Event) => void,
    onClose?: () => void,
    onOpen?: () => void
  ): { ws: WebSocket; send: (payload: Omit<WSMessageRequest, 'type'>) => void; close: () => void } => {
    const token = Session.get('token') || ''
    
    // 构建 WebSocket URL
    let wsUrl: string
    const baseURL = import.meta.env.VITE_API_BASE_URL || ''
    const isDev = import.meta.env.DEV  // Vite 提供的开发环境标识
    
    if (isDev && baseURL) {
      // 开发环境：使用环境变量中的地址（因为前后端端口不同）
      const protocol = baseURL.startsWith('https') ? 'wss:' : 'ws:'
      const host = baseURL.replace(/^https?:\/\//, '').replace(/\/$/, '')
      wsUrl = `${protocol}//${host}/api/v1/ai/conversation/${conversationId}/ws?token=${encodeURIComponent(token)}`
    } else {
      // 生产环境：使用当前页面的 host（前后端同域，通过 Nginx 代理）
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      wsUrl = `${protocol}//${host}/api/v1/ai/conversation/${conversationId}/ws?token=${encodeURIComponent(token)}`
    }
    
    console.log('Connecting to WebSocket:', wsUrl)
    
    // 创建 WebSocket 连接
    const ws = new WebSocket(wsUrl)
    
    // 连接打开
    ws.onopen = () => {
      console.log('WebSocket connected')
      onOpen?.()
    }
    
    // 接收消息
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }
    
    // 连接错误
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      onError?.(error)
    }
    
    // 连接关闭
    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason)
      onClose?.()
    }
    
    // 发送消息函数
    const send = (payload: Omit<WSMessageRequest, 'type'>) => {
      if (ws.readyState === WebSocket.OPEN) {
        const message: WSMessageRequest = {
          type: 'message',
          ...payload
        }
        ws.send(JSON.stringify(message))
      } else {
        console.error('WebSocket is not open, current state:', ws.readyState)
        throw new Error('WebSocket 连接未就绪')
      }
    }
    
    // 关闭连接函数
    const close = () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close()
      }
    }
    
    return { ws, send, close }
  }

  return {
    createConversation,
    getConversationList,
    getConversation,
    updateConversation,
    deleteConversation,
    getMessageList,
    getMcpRecords,
    sendMessage,
    sendMessageStream,
    connectWebSocket
  }
}

/**
 * 默认导出
 */
export default useConversationApi
