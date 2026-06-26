// User types
export interface User {
  id: string
  email: string
  full_name: string | null
  created_at: string
}

// Auth types
export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name?: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

// Document types
export interface Document {
  id: string
  user_id: string
  filename: string
  original_filename: string
  file_type: string
  file_size: number
  s3_key: string | null
  local_path: string | null
  uploaded_at: string
  text_content: string | null
}

export interface DocumentUploadResponse {
  document_id: string
  review_id: string
  filename: string
  upload_url: string | null
  message: string
}

// Review types
export type ReviewStatus = 'pending' | 'in_progress' | 'complete' | 'failed'
export type ViolationSeverity = 'critical' | 'high' | 'medium' | 'low'

export interface Violation {
  id: string
  review_id: string
  regulation: string
  severity: ViolationSeverity
  explanation: string
  original_text: string | null
  corrected_text: string | null
  citation_url: string | null
  agent_source: string
  created_at: string
}

export interface Correction {
  regulation: string
  severity: ViolationSeverity
  original_text: string
  corrected_text: string
  explanation: string
}

export interface ReviewSummary {
  review_id: string
  document_id: string
  document_filename: string
  status: ReviewStatus
  compliance_score: number | null
  risk_score: number | null
  violation_count: number
  created_at: string
  completed_at: string | null
}

export interface ReviewDetail extends ReviewSummary {
  summary: string | null
  violations: Violation[]
  corrections: Correction[]
}

// Bedrock call types
export interface BedrockCall {
  id: string
  review_id: string
  agent_name: string
  model_id: string
  input_tokens: number
  output_tokens: number
  latency_ms: number
  success: boolean
  error_message: string | null
  timestamp: string
}

// WebSocket event types
export type ReviewEventType =
  | 'status_update'
  | 'agent_started'
  | 'agent_completed'
  | 'violation_found'
  | 'review_complete'
  | 'error'

export interface ReviewEvent {
  type: ReviewEventType
  review_id: string
  timestamp: string
  data: Record<string, unknown>
}

// Audit types
export interface AuditLog {
  id: string
  review_id: string
  agent_name: string
  action: string
  details: Record<string, unknown>
  timestamp: string
}

// API response types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ApiError {
  detail: string
  status_code?: number
}
