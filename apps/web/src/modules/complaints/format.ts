import type { ComplaintStatus } from '@/api/types'

export const COMPLAINT_FILTERS = ['all', 'submitted', 'in_review', 'answered'] as const
export type ComplaintFilter = (typeof COMPLAINT_FILTERS)[number]

export type ComplaintAction = 'in_review'

export function complaintStatusKey(status: ComplaintStatus): string {
  return `complaints.status.${status}`
}

export function complaintStatusClass(status: ComplaintStatus): string {
  if (status === 'submitted') return 'border-gold-300 bg-gold-400/15 text-ink-800'
  if (status === 'in_review') return 'border-teal-200 bg-teal-100 text-teal-800'
  return 'border-ink-200 bg-ink-100 text-ink-600'
}

/** Mirrors the server state machine (SPEC-0007 FR-3); the API remains authoritative. */
export function complaintActions(status: ComplaintStatus): ComplaintAction[] {
  return status === 'submitted' ? ['in_review'] : []
}

/** A complaint accepts exactly one initial response (SPEC-0007 FR-5). */
export function canRespond(status: ComplaintStatus): boolean {
  return status !== 'answered'
}
