import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export function getSeverityColor(severity: string): string {
  switch (severity.toLowerCase()) {
    case 'critical':
      return 'badge-critical'
    case 'high':
      return 'badge-high'
    case 'medium':
      return 'badge-medium'
    case 'low':
      return 'badge-low'
    default:
      return 'badge'
  }
}

export function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'complete':
      return 'text-compliant'
    case 'failed':
    case 'error':
      return 'text-violation-high'
    case 'in_progress':
    case 'processing':
      return 'text-accent-600'
    default:
      return 'text-secondary-500'
  }
}

export function getComplianceScoreColor(score: number | null): string {
  if (score === null) return 'text-secondary-400'
  if (score >= 80) return 'text-compliant'
  if (score >= 60) return 'text-violation-medium'
  if (score >= 40) return 'text-violation-high'
  return 'text-violation-critical'
}
