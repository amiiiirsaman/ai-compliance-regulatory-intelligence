import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Upload as UploadIcon,
  FileText,
  X,
  CheckCircle,
  Loader2,
  AlertCircle,
} from 'lucide-react'
import { RootState, AppDispatch } from '@/store'
import { uploadDocument, resetUpload } from '@/store/slices/documentsSlice'
import { formatFileSize, cn } from '@/lib/utils'
import toast from 'react-hot-toast'

const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
}

export default function Upload() {
  const [file, setFile] = useState<File | null>(null)
  const dispatch = useDispatch<AppDispatch>()
  const navigate = useNavigate()
  const { uploading, uploadProgress, error } = useSelector(
    (state: RootState) => state.documents
  )

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024, // 50MB
  })

  const handleUpload = async () => {
    if (!file) return

    const result = await dispatch(uploadDocument(file))
    
    if (uploadDocument.fulfilled.match(result)) {
      toast.success('Document uploaded! Starting compliance review...')
      setTimeout(() => {
        navigate(`/reviews/${result.payload.review_id}`)
      }, 1000)
    } else {
      toast.error('Upload failed. Please try again.')
    }
  }

  const handleRemoveFile = () => {
    setFile(null)
    dispatch(resetUpload())
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-heading font-bold text-secondary-900">
          Upload Document
        </h1>
        <p className="text-secondary-600 mt-1">
          Upload a document for AI-powered compliance review
        </p>
      </div>

      {/* Dropzone */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card"
      >
        <div
          {...getRootProps()}
          className={cn(
            'border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all',
            isDragActive && !isDragReject && 'border-primary-500 bg-primary-50',
            isDragReject && 'border-violation-high bg-red-50',
            !isDragActive && !file && 'border-secondary-300 hover:border-primary-400 hover:bg-secondary-50',
            file && 'border-compliant bg-green-50'
          )}
        >
          <input {...getInputProps()} />
          
          <AnimatePresence mode="wait">
            {file ? (
              <motion.div
                key="file"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="flex flex-col items-center"
              >
                <div className="w-16 h-16 rounded-2xl bg-compliant/10 flex items-center justify-center mb-4">
                  <FileText className="w-8 h-8 text-compliant" />
                </div>
                <p className="font-medium text-secondary-900">{file.name}</p>
                <p className="text-sm text-secondary-500 mt-1">
                  {formatFileSize(file.size)}
                </p>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleRemoveFile()
                  }}
                  className="mt-4 text-sm text-secondary-600 hover:text-violation-high flex items-center gap-1"
                >
                  <X className="w-4 h-4" />
                  Remove file
                </button>
              </motion.div>
            ) : isDragReject ? (
              <motion.div
                key="reject"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center"
              >
                <div className="w-16 h-16 rounded-2xl bg-violation-high/10 flex items-center justify-center mb-4">
                  <AlertCircle className="w-8 h-8 text-violation-high" />
                </div>
                <p className="font-medium text-violation-high">
                  Unsupported file type
                </p>
                <p className="text-sm text-secondary-500 mt-1">
                  Please upload PDF, DOCX, or TXT files only
                </p>
              </motion.div>
            ) : (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center"
              >
                <div className={cn(
                  'w-16 h-16 rounded-2xl flex items-center justify-center mb-4 transition-colors',
                  isDragActive ? 'bg-primary-100' : 'bg-secondary-100'
                )}>
                  <UploadIcon className={cn(
                    'w-8 h-8 transition-colors',
                    isDragActive ? 'text-primary-600' : 'text-secondary-400'
                  )} />
                </div>
                <p className="font-medium text-secondary-900">
                  {isDragActive ? 'Drop your file here' : 'Drag & drop your file here'}
                </p>
                <p className="text-sm text-secondary-500 mt-1">
                  or click to browse
                </p>
                <p className="text-xs text-secondary-400 mt-4">
                  Supports PDF, DOCX, TXT • Max 50MB
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Upload Progress */}
        {uploading && (
          <div className="mt-6 px-6 pb-6">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-secondary-600">Uploading...</span>
              <span className="text-secondary-900 font-medium">{uploadProgress}%</span>
            </div>
            <div className="h-2 bg-secondary-100 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-primary-600 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${uploadProgress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>
        )}

        {/* Upload Button */}
        {file && !uploading && (
          <div className="px-6 pb-6">
            <button
              onClick={handleUpload}
              className="btn-primary w-full py-3 mt-4"
            >
              <CheckCircle className="w-5 h-5" />
              Start Compliance Review
            </button>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mx-6 mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-violation-high flex-shrink-0" />
            <p className="text-sm text-violation-high">{error}</p>
          </div>
        )}
      </motion.div>

      {/* Info */}
      <div className="mt-8 p-6 bg-primary-50 rounded-xl">
        <h3 className="font-medium text-primary-900 mb-3">
          What happens next?
        </h3>
        <ul className="space-y-2 text-sm text-primary-700">
          <li className="flex items-start gap-2">
            <span className="w-5 h-5 rounded-full bg-primary-200 text-primary-700 flex items-center justify-center flex-shrink-0 text-xs font-medium mt-0.5">1</span>
            Your document is securely uploaded and processed
          </li>
          <li className="flex items-start gap-2">
            <span className="w-5 h-5 rounded-full bg-primary-200 text-primary-700 flex items-center justify-center flex-shrink-0 text-xs font-medium mt-0.5">2</span>
            12 AI agents analyze for FINRA, SEC, CFPB, AML, and privacy compliance
          </li>
          <li className="flex items-start gap-2">
            <span className="w-5 h-5 rounded-full bg-primary-200 text-primary-700 flex items-center justify-center flex-shrink-0 text-xs font-medium mt-0.5">3</span>
            Receive detailed findings with corrections and risk scores
          </li>
        </ul>
      </div>
    </div>
  )
}
