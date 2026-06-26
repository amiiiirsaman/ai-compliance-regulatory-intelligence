import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import api from '@/lib/api'

export interface Document {
  id: string
  filename: string
  original_filename: string
  file_size: number
  mime_type: string
  document_type: string | null
  status: 'pending' | 'processing' | 'complete' | 'error'
  uploaded_at: string
}

interface DocumentsState {
  documents: Document[]
  loading: boolean
  uploading: boolean
  uploadProgress: number
  error: string | null
}

const initialState: DocumentsState = {
  documents: [],
  loading: false,
  uploading: false,
  uploadProgress: 0,
  error: null,
}

export const fetchDocuments = createAsyncThunk(
  'documents/fetchAll',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/documents')
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch documents')
    }
  }
)

export const uploadDocument = createAsyncThunk(
  'documents/upload',
  async (file: File, { rejectWithValue, dispatch }) => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const progress = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0
          dispatch(setUploadProgress(progress))
        },
      })
      
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Upload failed')
    }
  }
)

const documentsSlice = createSlice({
  name: 'documents',
  initialState,
  reducers: {
    setUploadProgress: (state, action) => {
      state.uploadProgress = action.payload
    },
    resetUpload: (state) => {
      state.uploading = false
      state.uploadProgress = 0
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDocuments.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchDocuments.fulfilled, (state, action) => {
        state.loading = false
        state.documents = action.payload
      })
      .addCase(fetchDocuments.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
      .addCase(uploadDocument.pending, (state) => {
        state.uploading = true
        state.uploadProgress = 0
        state.error = null
      })
      .addCase(uploadDocument.fulfilled, (state) => {
        state.uploading = false
        state.uploadProgress = 100
      })
      .addCase(uploadDocument.rejected, (state, action) => {
        state.uploading = false
        state.uploadProgress = 0
        state.error = action.payload as string
      })
  },
})

export const { setUploadProgress, resetUpload } = documentsSlice.actions
export default documentsSlice.reducer
