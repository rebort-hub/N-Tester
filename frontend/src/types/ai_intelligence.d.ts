/**
 * AI智能化模块类型定义
 */

// ==================== 需求文档 ====================
export interface RequirementDocument {
  id?: number
  project_id: number
  title: string
  file_path?: string
  document_type: string
  status?: string
  file_size?: number
  extracted_text?: string
  uploaded_by?: number
  has_analysis?: boolean
  creation_date?: string
  updation_date?: string
}

// ==================== AI模型配置 ====================
export interface AIModelConfig {
  id?: number
  name: string
  model_type: 'deepseek' | 'qwen' | 'siliconflow' | 'zhipu' | 'other'
  role: 'writer' | 'reviewer' | 'browser_use_text'
  api_key?: string
  base_url: string
  model_name: string
  max_tokens?: number
  temperature?: number
  top_p?: number
  is_active?: boolean
  created_by?: number
  creation_date?: string
  updation_date?: string
}

// ==================== 提示词配置 ====================
export interface PromptConfig {
  id?: number
  name: string
  prompt_type: 'writer' | 'reviewer'
  content: string
  is_active?: boolean
  created_by?: number
  creation_date?: string
  updation_date?: string
}

// ==================== 测试用例生成任务 ====================
export interface GenerationTask {
  id?: number
  project_id?: number
  task_id?: string
  title: string
  requirement_text: string
  status?: 'pending' | 'running' | 'completed' | 'failed'
  progress?: number
  output_mode?: 'stream' | 'batch'
  stream_buffer?: string
  stream_position?: number
  last_stream_update?: string
  writer_model_config_id?: number
  reviewer_model_config_id?: number
  writer_prompt_config_id?: number
  reviewer_prompt_config_id?: number
  generated_test_cases?: string
  review_feedback?: string
  final_test_cases?: string
  generation_log?: string
  error_message?: string
  created_by?: number
  completed_at?: string
  is_saved_to_records?: boolean
  saved_at?: string
  creation_date?: string
  updation_date?: string
}

// ==================== AI智能浏览器用例 ====================
export interface AICase {
  id?: number
  ui_project_id?: number
  name: string
  description?: string
  task_description: string
  created_by?: number
  creation_date?: string
  updation_date?: string
}

// ==================== AI执行记录 ====================
export interface AIExecutionRecord {
  id?: number
  ui_project_id?: number
  ai_case_id?: number
  case_name: string
  task_description?: string
  execution_mode?: 'text' | 'vision'
  status?: 'pending' | 'running' | 'success' | 'failed'
  start_time?: string
  end_time?: string
  duration?: number
  executed_by?: number
  creation_date?: string
  updation_date?: string
}

// ==================== 表单数据 ====================
export interface RequirementDocumentForm {
  project_id: number
  title: string
  file: File | null
}

export interface AIModelConfigForm {
  name: string
  model_type: string
  role: string
  api_key?: string
  base_url: string
  model_name: string
  max_tokens?: number
  temperature?: number
  top_p?: number
  is_active?: boolean
}

export interface PromptConfigForm {
  name: string
  prompt_type: string
  content: string
  is_active?: boolean
}

export interface GenerationTaskForm {
  project_id?: number
  title: string
  requirement_text: string
  output_mode?: string
  writer_model_config_id?: number
  reviewer_model_config_id?: number
  writer_prompt_config_id?: number
  reviewer_prompt_config_id?: number
}

export interface AICaseForm {
  ui_project_id?: number
  name: string
  description?: string
  task_description: string
}
