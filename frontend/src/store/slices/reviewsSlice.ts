import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import api from '@/lib/api'

export interface Violation {
  id: string
  regulation: string
  regulation_code: string | null
  severity: 'critical' | 'high' | 'medium' | 'low'
  explanation: string
  original_text: string | null
  corrected_text: string | null
  correction_explanation: string | null
  page_number: number | null
  risk_score: number | null
  confidence_score: number | null
  agent_source: string
  citation_valid: boolean | null
  citation_url: string | null
}

export interface BedrockCall {
  id: string
  agent_name: string
  model_id: string
  input_tokens: number
  output_tokens: number
  total_tokens: number
  latency_ms: number
  success: boolean
  timestamp: string
}

export interface AgentProgress {
  name: string
  displayName: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  startTime?: string
  endTime?: string
  error?: string
}

export interface Review {
  review_id: string
  document_id: string
  document_filename: string
  status: 'pending' | 'in_progress' | 'complete' | 'failed'
  compliance_score: number | null
  risk_score: number | null
  summary: string | null
  violations: Violation[]
  corrections: any[]
  created_at: string
  started_at: string | null
  completed_at: string | null
  error_message: string | null
}

export interface ReviewListItem {
  review_id: string
  document_id: string
  document_filename: string
  status: string
  compliance_score: number | null
  risk_score: number | null
  violation_count: number
  created_at: string
  completed_at: string | null
}

interface ReviewsState {
  reviews: ReviewListItem[]
  currentReview: Review | null
  bedrockCalls: BedrockCall[]
  agentProgress: AgentProgress[]
  loading: boolean
  error: string | null
}

// Define all agents in the workflow
const INITIAL_AGENTS: AgentProgress[] = [
  { name: 'document_reviewer', displayName: 'Document Reviewer', status: 'pending' },
  { name: 'finra_specialist', displayName: 'FINRA Specialist', status: 'pending' },
  { name: 'sec_specialist', displayName: 'SEC Specialist', status: 'pending' },
  { name: 'cfpb_specialist', displayName: 'CFPB Specialist', status: 'pending' },
  { name: 'aml_kyc_agent', displayName: 'AML/KYC Agent', status: 'pending' },
  { name: 'data_privacy_agent', displayName: 'Data Privacy Agent', status: 'pending' },
  { name: 'regulatory_expert', displayName: 'Regulatory Expert', status: 'pending' },
  { name: 'risk_assessment', displayName: 'Risk Assessment', status: 'pending' },
  { name: 'legal_writer', displayName: 'Legal Writer', status: 'pending' },
  { name: 'citation_validator', displayName: 'Citation Validator', status: 'pending' },
  { name: 'quality_assurance', displayName: 'Quality Assurance', status: 'pending' },
  { name: 'audit_trail', displayName: 'Audit Trail', status: 'pending' },
]

const initialState: ReviewsState = {
  reviews: [],
  currentReview: null,
  bedrockCalls: [],
  agentProgress: [],
  loading: false,
  error: null,
}

export const fetchReviews = createAsyncThunk(
  'reviews/fetchAll',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/reviews')
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch reviews')
    }
  }
)

export const fetchReview = createAsyncThunk(
  'reviews/fetchOne',
  async (reviewId: string, { rejectWithValue }) => {
    try {
      const response = await api.get(`/reviews/${reviewId}`)
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch review')
    }
  }
)

export const fetchBedrockCalls = createAsyncThunk(
  'reviews/fetchBedrockCalls',
  async (reviewId: string, { rejectWithValue }) => {
    try {
      const response = await api.get(`/reviews/${reviewId}/bedrock-calls`)
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch Bedrock calls')
    }
  }
)

const reviewsSlice = createSlice({
  name: 'reviews',
  initialState,
  reducers: {
    clearCurrentReview: (state) => {
      state.currentReview = null
      state.bedrockCalls = []
      state.agentProgress = []
    },
    resetAgentProgress: (state) => {
      state.agentProgress = INITIAL_AGENTS.map(a => ({ ...a }))
    },
    updateAgentStatus: (state, action) => {
      const { agentName, status, startTime, endTime, error } = action.payload
      const agent = state.agentProgress.find(a => a.name === agentName)
      if (agent) {
        agent.status = status
        if (startTime) agent.startTime = startTime
        if (endTime) agent.endTime = endTime
        if (error) agent.error = error
      }
    },
    updateReviewFromWebSocket: (state, action) => {
      const { review_id, ...updates } = action.payload
      if (state.currentReview?.review_id === review_id) {
        state.currentReview = { ...state.currentReview, ...updates }
      }
      const index = state.reviews.findIndex(r => r.review_id === review_id)
      if (index !== -1) {
        state.reviews[index] = { ...state.reviews[index], ...updates }
      }
    },
    addBedrockCall: (state, action) => {
      state.bedrockCalls.push(action.payload)
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchReviews.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchReviews.fulfilled, (state, action) => {
        state.loading = false
        state.reviews = action.payload
      })
      .addCase(fetchReviews.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
      .addCase(fetchReview.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchReview.fulfilled, (state, action) => {
        state.loading = false
        state.currentReview = action.payload
      })
      .addCase(fetchReview.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
      .addCase(fetchBedrockCalls.fulfilled, (state, action) => {
        state.bedrockCalls = action.payload
      })
  },
})

export const { clearCurrentReview, updateReviewFromWebSocket, addBedrockCall, resetAgentProgress, updateAgentStatus } = reviewsSlice.actions
export default reviewsSlice.reducer
