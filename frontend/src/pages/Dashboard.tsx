import { useEffect, useState, useMemo } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  FileSearch,
  Upload,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  ArrowRight,
  Activity,
  Filter,
  X,
  ChevronDown,
} from 'lucide-react'
import { RootState, AppDispatch } from '@/store'
import { fetchReviews } from '@/store/slices/reviewsSlice'
import { fetchCurrentUser } from '@/store/slices/authSlice'
import { formatDate, getComplianceScoreColor, cn } from '@/lib/utils'

// Helper function to get letter grade from compliance score
function getLetterGrade(score: number | null): { grade: string; color: string; bgColor: string } {
  if (score === null) return { grade: '-', color: 'text-secondary-400', bgColor: 'bg-secondary-100' }
  if (score >= 90) return { grade: 'A', color: 'text-green-700', bgColor: 'bg-green-100' }
  if (score >= 80) return { grade: 'B', color: 'text-blue-700', bgColor: 'bg-blue-100' }
  if (score >= 70) return { grade: 'C', color: 'text-yellow-700', bgColor: 'bg-yellow-100' }
  if (score >= 60) return { grade: 'D', color: 'text-orange-700', bgColor: 'bg-orange-100' }
  return { grade: 'F', color: 'text-red-700', bgColor: 'bg-red-100' }
}

// Helper function to get risk level
function getRiskLevel(score: number | null): { level: string; color: string; bgColor: string } {
  if (score === null) return { level: '-', color: 'text-secondary-400', bgColor: 'bg-secondary-100' }
  if (score >= 75) return { level: 'Critical', color: 'text-red-700', bgColor: 'bg-red-100' }
  if (score >= 50) return { level: 'High', color: 'text-orange-700', bgColor: 'bg-orange-100' }
  if (score >= 25) return { level: 'Medium', color: 'text-yellow-700', bgColor: 'bg-yellow-100' }
  return { level: 'Low', color: 'text-green-700', bgColor: 'bg-green-100' }
}

// Helper to calculate processing time
function getProcessingTime(createdAt: string, completedAt: string | null): string {
  if (!completedAt) return '-'
  const start = new Date(createdAt).getTime()
  const end = new Date(completedAt).getTime()
  const diffMs = end - start
  const diffMins = Math.floor(diffMs / 60000)
  const diffSecs = Math.floor((diffMs % 60000) / 1000)
  if (diffMins > 0) {
    return `${diffMins}m ${diffSecs}s`
  }
  return `${diffSecs}s`
}

export default function Dashboard() {
  const dispatch = useDispatch<AppDispatch>()
  const { user } = useSelector((state: RootState) => state.auth)
  const { reviews, loading } = useSelector((state: RootState) => state.reviews)

  // Filter state
  const [showFilters, setShowFilters] = useState(false)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [gradeFilter, setGradeFilter] = useState<string>('all')
  const [dateRange, setDateRange] = useState<string>('all')

  useEffect(() => {
    dispatch(fetchCurrentUser())
    dispatch(fetchReviews())
  }, [dispatch])

  // Apply filters
  const filteredReviews = useMemo(() => {
    let result = [...reviews]
    
    // Status filter
    if (statusFilter !== 'all') {
      result = result.filter(r => r.status === statusFilter)
    }
    
    // Grade filter
    if (gradeFilter !== 'all') {
      result = result.filter(r => {
        const { grade } = getLetterGrade(r.compliance_score)
        return grade === gradeFilter
      })
    }
    
    // Date range filter
    if (dateRange !== 'all') {
      const now = new Date()
      const cutoff = new Date()
      if (dateRange === 'today') {
        cutoff.setHours(0, 0, 0, 0)
      } else if (dateRange === 'week') {
        cutoff.setDate(now.getDate() - 7)
      } else if (dateRange === 'month') {
        cutoff.setMonth(now.getMonth() - 1)
      }
      result = result.filter(r => new Date(r.created_at) >= cutoff)
    }
    
    return result
  }, [reviews, statusFilter, gradeFilter, dateRange])

  // Calculate stats from ALL reviews (not filtered)
  const totalReviews = reviews.length
  const completedReviews = reviews.filter((r) => r.status === 'complete').length
  const pendingReviews = reviews.filter((r) => r.status === 'in_progress' || r.status === 'pending').length
  const totalViolations = reviews.reduce((sum, r) => sum + r.violation_count, 0)
  const avgComplianceScore =
    completedReviews > 0
      ? Math.round(
          reviews
            .filter((r) => r.compliance_score !== null)
            .reduce((sum, r) => sum + (r.compliance_score || 0), 0) / completedReviews
        )
      : null

  const recentReviews = filteredReviews.slice(0, 10)
  const activeFiltersCount = [statusFilter, gradeFilter, dateRange].filter(f => f !== 'all').length

  const stats = [
    {
      label: 'Total Reviews',
      value: totalReviews,
      icon: FileSearch,
      color: 'text-primary-600',
      bg: 'bg-primary-50',
    },
    {
      label: 'Pending',
      value: pendingReviews,
      icon: Clock,
      color: 'text-accent-600',
      bg: 'bg-accent-50',
    },
    {
      label: 'Violations Found',
      value: totalViolations,
      icon: AlertTriangle,
      color: 'text-violation-high',
      bg: 'bg-red-50',
    },
    {
      label: 'Avg. Compliance',
      value: avgComplianceScore !== null ? `${avgComplianceScore}%` : '-',
      subValue: avgComplianceScore !== null ? `Grade ${getLetterGrade(avgComplianceScore).grade}` : '',
      icon: TrendingUp,
      color: avgComplianceScore !== null && avgComplianceScore >= 70 ? 'text-compliant' : 'text-violation-medium',
      bg: avgComplianceScore !== null && avgComplianceScore >= 70 ? 'bg-green-50' : 'bg-amber-50',
    },
  ]

  const clearFilters = () => {
    setStatusFilter('all')
    setGradeFilter('all')
    setDateRange('all')
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-heading font-bold text-secondary-900">
            Welcome back, {user?.full_name?.split(' ')[0] || 'User'}
          </h1>
          <p className="text-secondary-600 mt-1">
            Here's an overview of your compliance reviews
          </p>
        </div>
        <Link to="/upload" className="btn-primary">
          <Upload className="w-5 h-5" />
          Upload Document
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="card p-6"
          >
            <div className="flex items-center gap-4">
              <div className={cn('p-3 rounded-xl', stat.bg)}>
                <stat.icon className={cn('w-6 h-6', stat.color)} />
              </div>
              <div>
                <p className="text-sm text-secondary-500">{stat.label}</p>
                <p className={cn('text-2xl font-bold', stat.color)}>{stat.value}</p>
                {'subValue' in stat && stat.subValue && (
                  <p className="text-xs text-secondary-500">{stat.subValue}</p>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Recent Reviews */}
      <div className="card">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 border-b border-secondary-200">
          <h2 className="text-lg font-heading font-semibold text-secondary-900">
            Recent Reviews
            {activeFiltersCount > 0 && (
              <span className="ml-2 text-sm font-normal text-secondary-500">
                ({filteredReviews.length} of {reviews.length})
              </span>
            )}
          </h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={cn(
                "flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg border transition-colors",
                showFilters || activeFiltersCount > 0
                  ? "bg-primary-50 border-primary-200 text-primary-700"
                  : "border-secondary-200 text-secondary-600 hover:bg-secondary-50"
              )}
            >
              <Filter className="w-4 h-4" />
              Filters
              {activeFiltersCount > 0 && (
                <span className="bg-primary-600 text-white text-xs px-1.5 py-0.5 rounded-full">
                  {activeFiltersCount}
                </span>
              )}
              <ChevronDown className={cn("w-4 h-4 transition-transform", showFilters && "rotate-180")} />
            </button>
            <Link
              to="/reviews"
              className="text-sm font-medium text-primary-600 hover:text-primary-700 flex items-center gap-1"
            >
              View all
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="px-6 py-4 bg-secondary-50 border-b border-secondary-200"
          >
            <div className="flex flex-wrap items-center gap-4">
              <div>
                <label className="block text-xs font-medium text-secondary-500 mb-1">Status</label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-3 py-1.5 text-sm rounded-lg border border-secondary-200 bg-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="all">All Statuses</option>
                  <option value="complete">Complete</option>
                  <option value="in_progress">In Progress</option>
                  <option value="pending">Pending</option>
                  <option value="failed">Failed</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-secondary-500 mb-1">Grade</label>
                <select
                  value={gradeFilter}
                  onChange={(e) => setGradeFilter(e.target.value)}
                  className="px-3 py-1.5 text-sm rounded-lg border border-secondary-200 bg-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="all">All Grades</option>
                  <option value="A">A (90-100%)</option>
                  <option value="B">B (80-89%)</option>
                  <option value="C">C (70-79%)</option>
                  <option value="D">D (60-69%)</option>
                  <option value="F">F (&lt;60%)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-secondary-500 mb-1">Date Range</label>
                <select
                  value={dateRange}
                  onChange={(e) => setDateRange(e.target.value)}
                  className="px-3 py-1.5 text-sm rounded-lg border border-secondary-200 bg-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="all">All Time</option>
                  <option value="today">Today</option>
                  <option value="week">Last 7 Days</option>
                  <option value="month">Last 30 Days</option>
                </select>
              </div>
              {activeFiltersCount > 0 && (
                <button
                  onClick={clearFilters}
                  className="flex items-center gap-1 px-3 py-1.5 text-sm text-secondary-600 hover:text-secondary-800 mt-5"
                >
                  <X className="w-4 h-4" />
                  Clear filters
                </button>
              )}
            </div>
          </motion.div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Activity className="w-8 h-8 text-primary-600 animate-pulse" />
          </div>
        ) : recentReviews.length === 0 ? (
          <div className="text-center py-12">
            <FileSearch className="w-12 h-12 text-secondary-300 mx-auto mb-4" />
            <p className="text-secondary-600">
              {activeFiltersCount > 0 ? 'No reviews match your filters' : 'No reviews yet'}
            </p>
            <p className="text-sm text-secondary-500 mt-1">
              {activeFiltersCount > 0 ? (
                <button onClick={clearFilters} className="text-primary-600 hover:underline">
                  Clear filters
                </button>
              ) : (
                'Upload a document to get started'
              )}
            </p>
          </div>
        ) : (
          <>
            {/* Table Header */}
            <div className="hidden md:grid md:grid-cols-12 gap-4 px-6 py-3 bg-secondary-50 text-xs font-medium text-secondary-500 uppercase tracking-wider border-b border-secondary-200">
              <div className="col-span-1">Status</div>
              <div className="col-span-3">Document</div>
              <div className="col-span-2">Date</div>
              <div className="col-span-2 text-center">Compliance</div>
              <div className="col-span-1 text-center">Risk</div>
              <div className="col-span-1 text-center">Violations</div>
              <div className="col-span-1 text-center">Time</div>
              <div className="col-span-1"></div>
            </div>

            <div className="divide-y divide-secondary-100">
              {recentReviews.map((review, i) => {
                const letterGrade = getLetterGrade(review.compliance_score)
                const riskLevel = getRiskLevel(review.risk_score)
                const processingTime = getProcessingTime(review.created_at, review.completed_at)

                return (
                  <motion.div
                    key={review.review_id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.03 }}
                  >
                    <Link
                      to={`/reviews/${review.review_id}`}
                      className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center p-4 hover:bg-secondary-50 transition-colors"
                    >
                      {/* Status Icon */}
                      <div className="col-span-1 flex items-center gap-3 md:gap-0">
                        {review.status === 'complete' ? (
                          <div className="w-10 h-10 rounded-full bg-compliant/10 flex items-center justify-center">
                            <CheckCircle className="w-5 h-5 text-compliant" />
                          </div>
                        ) : review.status === 'failed' ? (
                          <div className="w-10 h-10 rounded-full bg-violation-high/10 flex items-center justify-center">
                            <AlertTriangle className="w-5 h-5 text-violation-high" />
                          </div>
                        ) : (
                          <div className="w-10 h-10 rounded-full bg-accent-100 flex items-center justify-center">
                            <Clock className="w-5 h-5 text-accent-600 animate-pulse" />
                          </div>
                        )}
                        {/* Mobile: Show document name next to status */}
                        <div className="md:hidden flex-1 min-w-0">
                          <p className="font-medium text-secondary-900 truncate">
                            {review.document_filename}
                          </p>
                          <p className="text-sm text-secondary-500">
                            {formatDate(review.created_at)}
                          </p>
                        </div>
                      </div>

                      {/* Document Name (Desktop) */}
                      <div className="hidden md:block col-span-3">
                        <p className="font-medium text-secondary-900 truncate">
                          {review.document_filename}
                        </p>
                      </div>

                      {/* Date (Desktop) */}
                      <div className="hidden md:block col-span-2 text-sm text-secondary-500">
                        {formatDate(review.created_at)}
                      </div>

                      {/* Compliance Score + Grade */}
                      <div className="col-span-2 flex items-center justify-center gap-2">
                        {review.compliance_score !== null ? (
                          <>
                            <span className={cn('text-lg font-bold', getComplianceScoreColor(review.compliance_score))}>
                              {review.compliance_score}%
                            </span>
                            <span className={cn('text-xs font-bold px-2 py-0.5 rounded', letterGrade.bgColor, letterGrade.color)}>
                              {letterGrade.grade}
                            </span>
                          </>
                        ) : (
                          <span className="text-sm text-secondary-400 capitalize">
                            {review.status.replace('_', ' ')}
                          </span>
                        )}
                      </div>

                      {/* Risk Level */}
                      <div className="col-span-1 flex justify-center">
                        {review.risk_score !== null ? (
                          <span className={cn('text-xs font-medium px-2 py-1 rounded', riskLevel.bgColor, riskLevel.color)}>
                            {riskLevel.level}
                          </span>
                        ) : (
                          <span className="text-sm text-secondary-400">-</span>
                        )}
                      </div>

                      {/* Violations */}
                      <div className="col-span-1 text-center">
                        {review.violation_count > 0 ? (
                          <span className="inline-flex items-center gap-1 text-sm font-medium text-violation-high">
                            <AlertTriangle className="w-3 h-3" />
                            {review.violation_count}
                          </span>
                        ) : review.status === 'complete' ? (
                          <span className="text-sm text-compliant">0</span>
                        ) : (
                          <span className="text-sm text-secondary-400">-</span>
                        )}
                      </div>

                      {/* Processing Time */}
                      <div className="col-span-1 text-center text-sm text-secondary-500">
                        {processingTime}
                      </div>

                      {/* Arrow */}
                      <div className="col-span-1 flex justify-end">
                        <ArrowRight className="w-5 h-5 text-secondary-400" />
                      </div>
                    </Link>
                  </motion.div>
                )
              })}
            </div>
          </>
        )}

        {/* Grade Legend */}
        {recentReviews.length > 0 && (
          <div className="px-6 py-4 bg-secondary-50 border-t border-secondary-200">
            <div className="flex flex-wrap items-center gap-4 text-xs">
              <span className="font-medium text-secondary-600">Compliance Grade:</span>
              <span className="flex items-center gap-1">
                <span className="px-1.5 py-0.5 rounded bg-green-100 text-green-700 font-bold">A</span>
                90-100%
              </span>
              <span className="flex items-center gap-1">
                <span className="px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-bold">B</span>
                80-89%
              </span>
              <span className="flex items-center gap-1">
                <span className="px-1.5 py-0.5 rounded bg-yellow-100 text-yellow-700 font-bold">C</span>
                70-79%
              </span>
              <span className="flex items-center gap-1">
                <span className="px-1.5 py-0.5 rounded bg-orange-100 text-orange-700 font-bold">D</span>
                60-69%
              </span>
              <span className="flex items-center gap-1">
                <span className="px-1.5 py-0.5 rounded bg-red-100 text-red-700 font-bold">F</span>
                &lt;60%
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
