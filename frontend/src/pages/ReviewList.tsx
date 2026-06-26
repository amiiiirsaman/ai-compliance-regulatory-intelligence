import { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  FileSearch,
  CheckCircle,
  AlertTriangle,
  Clock,
  ArrowRight,
  Filter,
} from 'lucide-react'
import { RootState, AppDispatch } from '@/store'
import { fetchReviews } from '@/store/slices/reviewsSlice'
import { formatDate, getComplianceScoreColor, cn } from '@/lib/utils'

export default function ReviewList() {
  const dispatch = useDispatch<AppDispatch>()
  const { reviews, loading } = useSelector((state: RootState) => state.reviews)

  useEffect(() => {
    dispatch(fetchReviews())
  }, [dispatch])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'complete':
        return <CheckCircle className="w-5 h-5 text-compliant" />
      case 'failed':
        return <AlertTriangle className="w-5 h-5 text-violation-high" />
      default:
        return <Clock className="w-5 h-5 text-accent-600 animate-pulse" />
    }
  }

  const getStatusBadge = (status: string) => {
    const statusClasses = {
      complete: 'bg-compliant/10 text-compliant',
      failed: 'bg-violation-high/10 text-violation-high',
      in_progress: 'bg-accent-100 text-accent-700',
      pending: 'bg-secondary-100 text-secondary-600',
    }
    return cn(
      'px-2.5 py-1 rounded-full text-xs font-medium capitalize',
      statusClasses[status as keyof typeof statusClasses] || statusClasses.pending
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-heading font-bold text-secondary-900">
            Compliance Reviews
          </h1>
          <p className="text-secondary-600 mt-1">
            {reviews.length} total review{reviews.length !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button className="btn-secondary">
            <Filter className="w-4 h-4" />
            Filter
          </button>
          <Link to="/upload" className="btn-primary">
            New Review
          </Link>
        </div>
      </div>

      {/* Reviews List */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="text-center">
              <div className="w-12 h-12 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin mx-auto" />
              <p className="text-secondary-600 mt-4">Loading reviews...</p>
            </div>
          </div>
        ) : reviews.length === 0 ? (
          <div className="text-center py-16">
            <FileSearch className="w-16 h-16 text-secondary-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-secondary-900">No reviews yet</h3>
            <p className="text-secondary-600 mt-1 mb-6">
              Upload a document to start your first compliance review
            </p>
            <Link to="/upload" className="btn-primary">
              Upload Document
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-secondary-50 border-b border-secondary-200">
                  <th className="px-6 py-4 text-left text-xs font-semibold text-secondary-600 uppercase tracking-wider">
                    Document
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-secondary-600 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-4 text-center text-xs font-semibold text-secondary-600 uppercase tracking-wider">
                    Compliance
                  </th>
                  <th className="px-6 py-4 text-center text-xs font-semibold text-secondary-600 uppercase tracking-wider">
                    Violations
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-secondary-600 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-4"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-secondary-100">
                {reviews.map((review, i) => (
                  <motion.tr
                    key={review.review_id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.03 }}
                    className="hover:bg-secondary-50 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(review.status)}
                        <div className="min-w-0">
                          <p className="font-medium text-secondary-900 truncate max-w-xs">
                            {review.document_filename}
                          </p>
                          <p className="text-xs text-secondary-500 font-mono">
                            {review.review_id.slice(0, 8)}...
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={getStatusBadge(review.status)}>
                        {review.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      {review.compliance_score !== null ? (
                        <span
                          className={cn(
                            'text-lg font-bold',
                            getComplianceScoreColor(review.compliance_score)
                          )}
                        >
                          {review.compliance_score}%
                        </span>
                      ) : (
                        <span className="text-secondary-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-center">
                      {review.violation_count > 0 ? (
                        <span className="inline-flex items-center justify-center min-w-[2rem] px-2 py-1 rounded-full bg-violation-high/10 text-violation-high text-sm font-medium">
                          {review.violation_count}
                        </span>
                      ) : review.status === 'complete' ? (
                        <span className="text-compliant text-sm font-medium">Clean</span>
                      ) : (
                        <span className="text-secondary-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-secondary-600 text-sm">
                      {formatDate(review.created_at)}
                    </td>
                    <td className="px-6 py-4">
                      <Link
                        to={`/reviews/${review.review_id}`}
                        className="btn-ghost p-2"
                      >
                        <ArrowRight className="w-5 h-5" />
                      </Link>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
