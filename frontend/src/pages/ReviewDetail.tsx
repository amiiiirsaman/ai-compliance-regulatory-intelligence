import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  Download,
  Activity,
  Zap,
  Shield,
  Scale,
  Eye,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Bot,
  Loader2,
  XCircle,
} from 'lucide-react'
import { RootState, AppDispatch } from '@/store'
import { fetchReview, fetchBedrockCalls, AgentProgress } from '@/store/slices/reviewsSlice'
import { useReviewWebSocket } from '@/lib/websocket'
import { formatDate, getSeverityColor, getComplianceScoreColor, cn } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

// Agent Progress Component
function AgentProgressPanel({ agents, isProcessing }: { agents: AgentProgress[], isProcessing: boolean }) {
  if (!isProcessing && agents.every(a => a.status === 'pending')) {
    return null
  }

  const getStatusIcon = (status: AgentProgress['status']) => {
    switch (status) {
      case 'running':
        return <Loader2 className="w-4 h-4 text-accent-600 animate-spin" />
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-compliant" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-violation-high" />
      default:
        return <Clock className="w-4 h-4 text-secondary-300" />
    }
  }

  const getStatusBg = (status: AgentProgress['status']) => {
    switch (status) {
      case 'running':
        return 'bg-accent-50 border-accent-200'
      case 'completed':
        return 'bg-green-50 border-green-200'
      case 'failed':
        return 'bg-red-50 border-red-200'
      default:
        return 'bg-secondary-50 border-secondary-200'
    }
  }

  const completedCount = agents.filter(a => a.status === 'completed').length
  const runningCount = agents.filter(a => a.status === 'running').length
  const failedCount = agents.filter(a => a.status === 'failed').length
  const progress = Math.round((completedCount / agents.length) * 100)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary-50">
            <Bot className="w-5 h-5 text-primary-600" />
          </div>
          <div>
            <h2 className="text-lg font-heading font-semibold text-secondary-900">
              Agent Pipeline
            </h2>
            <p className="text-sm text-secondary-500">
              {completedCount} of {agents.length} agents complete
              {runningCount > 0 && ` • ${runningCount} running`}
              {failedCount > 0 && ` • ${failedCount} failed`}
            </p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold text-primary-600">{progress}%</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="h-2 bg-secondary-100 rounded-full overflow-hidden mb-4">
        <motion.div
          className="h-full bg-gradient-to-r from-primary-500 to-primary-600"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>

      {/* Agent Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {agents.map((agent, index) => (
          <motion.div
            key={agent.name}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
            className={cn(
              'flex items-center gap-2 p-3 rounded-lg border transition-all duration-300',
              getStatusBg(agent.status),
              agent.status === 'running' && 'ring-2 ring-accent-400 ring-opacity-50'
            )}
          >
            {getStatusIcon(agent.status)}
            <div className="flex-1 min-w-0">
              <p className={cn(
                'text-xs font-medium truncate',
                agent.status === 'running' ? 'text-accent-700' :
                agent.status === 'completed' ? 'text-green-700' :
                agent.status === 'failed' ? 'text-red-700' :
                'text-secondary-500'
              )}>
                {agent.displayName}
              </p>
              {agent.status === 'running' && (
                <p className="text-[10px] text-accent-500">Processing...</p>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

export default function ReviewDetail() {
  const { reviewId } = useParams<{ reviewId: string }>()
  const dispatch = useDispatch<AppDispatch>()
  const { currentReview: review, bedrockCalls, agentProgress, loading } = useSelector(
    (state: RootState) => state.reviews
  )
  const [activeTab, setActiveTab] = useState<'violations' | 'corrections' | 'bedrock'>('violations')
  const [expandedViolation, setExpandedViolation] = useState<string | null>(null)

  // Connect WebSocket for real-time updates
  useReviewWebSocket(reviewId)

  useEffect(() => {
    if (reviewId) {
      dispatch(fetchReview(reviewId))
      dispatch(fetchBedrockCalls(reviewId))
    }
  }, [dispatch, reviewId])

  const handleDownloadAuditTrail = async () => {
    try {
      const response = await api.get(`/reports/${reviewId}/audit-trail/download`, {
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `audit_trail_${reviewId}.json`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      toast.success('Audit trail downloaded')
    } catch (error) {
      toast.error('Failed to download audit trail')
    }
  }

  if (loading || !review) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin mx-auto" />
          <p className="text-secondary-600 mt-4">Loading review...</p>
        </div>
      </div>
    )
  }

  const isProcessing = review.status === 'in_progress' || review.status === 'pending'

  // Group violations by severity
  const violationsBySeverity = {
    critical: review.violations.filter((v) => v.severity === 'critical'),
    high: review.violations.filter((v) => v.severity === 'high'),
    medium: review.violations.filter((v) => v.severity === 'medium'),
    low: review.violations.filter((v) => v.severity === 'low'),
  }

  return (
    <div className="space-y-6">
      {/* Back Button & Title */}
      <div className="flex items-center gap-4">
        <Link
          to="/reviews"
          className="p-2 rounded-lg hover:bg-secondary-100 transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-secondary-600" />
        </Link>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-heading font-bold text-secondary-900 truncate">
            {review.document_filename}
          </h1>
          <p className="text-sm text-secondary-500">
            Review ID: {review.review_id.slice(0, 8)}...
          </p>
        </div>
        <button onClick={handleDownloadAuditTrail} className="btn-secondary">
          <Download className="w-4 h-4" />
          Audit Trail
        </button>
      </div>

      {/* Processing Status Banner */}
      {isProcessing && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-accent-50 border border-accent-200 rounded-xl p-4 flex items-center gap-4"
        >
          <div className="w-10 h-10 rounded-full bg-accent-100 flex items-center justify-center">
            <Activity className="w-5 h-5 text-accent-600 animate-pulse" />
          </div>
          <div className="flex-1">
            <p className="font-medium text-accent-800">Review in progress...</p>
            <p className="text-sm text-accent-600">
              AI agents are analyzing your document for compliance issues
            </p>
          </div>
        </motion.div>
      )}

      {/* Agent Progress Panel */}
      <AgentProgressPanel agents={agentProgress} isProcessing={isProcessing} />

      {/* Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Compliance Score */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-6"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-primary-50">
              <Shield className="w-5 h-5 text-primary-600" />
            </div>
            <span className="text-sm text-secondary-600">Compliance Score</span>
          </div>
          <p
            className={cn(
              'text-3xl font-bold',
              getComplianceScoreColor(review.compliance_score)
            )}
          >
            {review.compliance_score !== null ? `${review.compliance_score}%` : '-'}
          </p>
        </motion.div>

        {/* Risk Score */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card p-6"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-violation-high/10">
              <AlertTriangle className="w-5 h-5 text-violation-high" />
            </div>
            <span className="text-sm text-secondary-600">Risk Score</span>
          </div>
          <p className="text-3xl font-bold text-secondary-900">
            {review.risk_score !== null ? review.risk_score : '-'}
          </p>
        </motion.div>

        {/* Violations */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card p-6"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-accent-50">
              <Scale className="w-5 h-5 text-accent-600" />
            </div>
            <span className="text-sm text-secondary-600">Violations</span>
          </div>
          <p className="text-3xl font-bold text-secondary-900">
            {review.violations.length}
          </p>
        </motion.div>

        {/* Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card p-6"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className={cn(
              'p-2 rounded-lg',
              review.status === 'complete' ? 'bg-compliant/10' : 
              review.status === 'failed' ? 'bg-violation-high/10' : 'bg-accent-50'
            )}>
              {review.status === 'complete' ? (
                <CheckCircle className="w-5 h-5 text-compliant" />
              ) : review.status === 'failed' ? (
                <AlertTriangle className="w-5 h-5 text-violation-high" />
              ) : (
                <Clock className="w-5 h-5 text-accent-600" />
              )}
            </div>
            <span className="text-sm text-secondary-600">Status</span>
          </div>
          <p className="text-lg font-semibold capitalize text-secondary-900">
            {review.status.replace('_', ' ')}
          </p>
        </motion.div>
      </div>

      {/* Summary */}
      {review.summary && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-6"
        >
          <h2 className="text-lg font-heading font-semibold text-secondary-900 mb-3">
            Executive Summary
          </h2>
          <p className="text-secondary-700 leading-relaxed">{review.summary}</p>
        </motion.div>
      )}

      {/* Tabs */}
      <div className="card overflow-hidden">
        <div className="flex border-b border-secondary-200">
          <button
            onClick={() => setActiveTab('violations')}
            className={cn(
              'flex-1 px-6 py-4 text-sm font-medium transition-colors',
              activeTab === 'violations'
                ? 'text-primary-600 border-b-2 border-primary-600 bg-primary-50/50'
                : 'text-secondary-600 hover:text-secondary-900 hover:bg-secondary-50'
            )}
          >
            Violations ({review.violations.length})
          </button>
          <button
            onClick={() => setActiveTab('corrections')}
            className={cn(
              'flex-1 px-6 py-4 text-sm font-medium transition-colors',
              activeTab === 'corrections'
                ? 'text-primary-600 border-b-2 border-primary-600 bg-primary-50/50'
                : 'text-secondary-600 hover:text-secondary-900 hover:bg-secondary-50'
            )}
          >
            Corrections ({review.corrections.length})
          </button>
          <button
            onClick={() => setActiveTab('bedrock')}
            className={cn(
              'flex-1 px-6 py-4 text-sm font-medium transition-colors',
              activeTab === 'bedrock'
                ? 'text-primary-600 border-b-2 border-primary-600 bg-primary-50/50'
                : 'text-secondary-600 hover:text-secondary-900 hover:bg-secondary-50'
            )}
          >
            <span className="flex items-center justify-center gap-2">
              <Zap className="w-4 h-4" />
              Bedrock Logs ({bedrockCalls.length})
            </span>
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          <AnimatePresence mode="wait">
            {activeTab === 'violations' && (
              <motion.div
                key="violations"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-4"
              >
                {review.violations.length === 0 ? (
                  <div className="text-center py-12">
                    <CheckCircle className="w-12 h-12 text-compliant mx-auto mb-4" />
                    <p className="text-secondary-600">No violations found</p>
                  </div>
                ) : (
                  Object.entries(violationsBySeverity).map(([severity, violations]) =>
                    violations.length > 0 && (
                      <div key={severity} className="space-y-3">
                        <h3 className="text-sm font-semibold uppercase tracking-wide text-secondary-500">
                          {severity} ({violations.length})
                        </h3>
                        {violations.map((violation) => (
                          <div
                            key={violation.id}
                            className="border border-secondary-200 rounded-lg overflow-hidden"
                          >
                            <button
                              onClick={() =>
                                setExpandedViolation(
                                  expandedViolation === violation.id ? null : violation.id
                                )
                              }
                              className="w-full px-4 py-3 flex items-center gap-4 hover:bg-secondary-50 transition-colors"
                            >
                              <span className={getSeverityColor(violation.severity)}>
                                {violation.severity}
                              </span>
                              <span className="flex-1 text-left font-medium text-secondary-900 truncate">
                                {violation.regulation}
                              </span>
                              <span className="text-xs text-secondary-500">
                                {violation.agent_source}
                              </span>
                              {expandedViolation === violation.id ? (
                                <ChevronUp className="w-5 h-5 text-secondary-400" />
                              ) : (
                                <ChevronDown className="w-5 h-5 text-secondary-400" />
                              )}
                            </button>
                            <AnimatePresence>
                              {expandedViolation === violation.id && (
                                <motion.div
                                  initial={{ height: 0, opacity: 0 }}
                                  animate={{ height: 'auto', opacity: 1 }}
                                  exit={{ height: 0, opacity: 0 }}
                                  className="border-t border-secondary-200 bg-secondary-50/50"
                                >
                                  <div className="p-4 space-y-4">
                                    <div>
                                      <p className="text-xs font-medium text-secondary-500 uppercase mb-1">
                                        Explanation
                                      </p>
                                      <p className="text-secondary-700">
                                        {violation.explanation}
                                      </p>
                                    </div>
                                    {violation.original_text && (
                                      <div>
                                        <p className="text-xs font-medium text-secondary-500 uppercase mb-1">
                                          Problematic Text
                                        </p>
                                        <p className="text-secondary-700 bg-red-50 p-3 rounded border-l-4 border-violation-high font-mono text-sm">
                                          {violation.original_text}
                                        </p>
                                      </div>
                                    )}
                                    {violation.corrected_text && (
                                      <div>
                                        <p className="text-xs font-medium text-secondary-500 uppercase mb-1">
                                          Suggested Correction
                                        </p>
                                        <p className="text-secondary-700 bg-green-50 p-3 rounded border-l-4 border-compliant font-mono text-sm">
                                          {violation.corrected_text}
                                        </p>
                                      </div>
                                    )}
                                    {violation.citation_url && (
                                      <a
                                        href={violation.citation_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700"
                                      >
                                        View regulation
                                        <ExternalLink className="w-3 h-3" />
                                      </a>
                                    )}
                                  </div>
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </div>
                        ))}
                      </div>
                    )
                  )
                )}
              </motion.div>
            )}

            {activeTab === 'corrections' && (
              <motion.div
                key="corrections"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-4"
              >
                {review.corrections.length === 0 ? (
                  <div className="text-center py-12">
                    <FileText className="w-12 h-12 text-secondary-300 mx-auto mb-4" />
                    <p className="text-secondary-600">No corrections generated</p>
                  </div>
                ) : (
                  review.corrections.map((correction, i) => (
                    <div
                      key={i}
                      className="border border-secondary-200 rounded-lg p-4 space-y-3"
                    >
                      <div className="flex items-center gap-2">
                        <span className={getSeverityColor(correction.severity)}>
                          {correction.severity}
                        </span>
                        <span className="text-sm font-medium text-secondary-700">
                          {correction.regulation}
                        </span>
                      </div>
                      <div className="grid md:grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs font-medium text-secondary-500 uppercase mb-1">
                            Original
                          </p>
                          <p className="text-sm text-secondary-700 bg-red-50 p-3 rounded">
                            {correction.original_text}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs font-medium text-secondary-500 uppercase mb-1">
                            Corrected
                          </p>
                          <p className="text-sm text-secondary-700 bg-green-50 p-3 rounded">
                            {correction.corrected_text}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </motion.div>
            )}

            {activeTab === 'bedrock' && (
              <motion.div
                key="bedrock"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                {bedrockCalls.length === 0 ? (
                  <div className="text-center py-12">
                    <Zap className="w-12 h-12 text-secondary-300 mx-auto mb-4" />
                    <p className="text-secondary-600">No Bedrock calls logged yet</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-secondary-200">
                          <th className="px-4 py-3 text-left font-semibold text-secondary-600">
                            Agent
                          </th>
                          <th className="px-4 py-3 text-right font-semibold text-secondary-600">
                            Input
                          </th>
                          <th className="px-4 py-3 text-right font-semibold text-secondary-600">
                            Output
                          </th>
                          <th className="px-4 py-3 text-right font-semibold text-secondary-600">
                            Latency
                          </th>
                          <th className="px-4 py-3 text-center font-semibold text-secondary-600">
                            Status
                          </th>
                          <th className="px-4 py-3 text-left font-semibold text-secondary-600">
                            Time
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-secondary-100">
                        {bedrockCalls.map((call) => (
                          <tr key={call.id} className="hover:bg-secondary-50">
                            <td className="px-4 py-3 font-medium text-secondary-900">
                              {call.agent_name.replace('_', ' ')}
                            </td>
                            <td className="px-4 py-3 text-right text-secondary-600 font-mono">
                              {call.input_tokens.toLocaleString()}
                            </td>
                            <td className="px-4 py-3 text-right text-secondary-600 font-mono">
                              {call.output_tokens.toLocaleString()}
                            </td>
                            <td className="px-4 py-3 text-right text-secondary-600">
                              {call.latency_ms}ms
                            </td>
                            <td className="px-4 py-3 text-center">
                              {call.success ? (
                                <span className="badge-compliant">Success</span>
                              ) : (
                                <span className="badge-critical">Failed</span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-secondary-500 text-xs">
                              {formatDate(call.timestamp)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot className="bg-secondary-50">
                        <tr>
                          <td className="px-4 py-3 font-semibold text-secondary-900">
                            Total
                          </td>
                          <td className="px-4 py-3 text-right font-semibold font-mono">
                            {bedrockCalls.reduce((sum, c) => sum + c.input_tokens, 0).toLocaleString()}
                          </td>
                          <td className="px-4 py-3 text-right font-semibold font-mono">
                            {bedrockCalls.reduce((sum, c) => sum + c.output_tokens, 0).toLocaleString()}
                          </td>
                          <td className="px-4 py-3 text-right font-semibold">
                            {bedrockCalls.reduce((sum, c) => sum + c.latency_ms, 0).toLocaleString()}ms
                          </td>
                          <td colSpan={2}></td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
