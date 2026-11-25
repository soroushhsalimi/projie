import type { RequestStatus, ReviewAction, RoomType } from '@/api/types'

export const ROOM_TYPES = ['single', 'double', 'triple', 'quad'] as const

export const REQUEST_FILTERS = [
  'all',
  'submitted',
  'under_review',
  'approved',
  'rejected',
] as const
export type RequestFilter = (typeof REQUEST_FILTERS)[number]

/** Mirrors the server state machine (SPEC-0006 FR-4); the API remains authoritative. */
const LEGAL_ACTIONS: Record<RequestStatus, ReviewAction[]> = {
  submitted: ['under_review', 'approved', 'rejected'],
  under_review: ['approved', 'rejected'],
  approved: [],
  rejected: [],
  withdrawn: [],
}

export function requestStatusKey(status: RequestStatus): string {
  return `requests.status.${status}`
}

export function requestStatusClass(status: RequestStatus): string {
  if (status === 'submitted') return 'border-gold-300 bg-gold-400/15 text-ink-800'
  if (status === 'under_review') return 'border-teal-200 bg-teal-100 text-teal-800'
  if (status === 'approved') return 'border-emerald-200 bg-emerald-50 text-emerald-800'
  if (status === 'rejected') return 'border-red-200 bg-red-50 text-red-700'
  return 'border-ink-200 bg-ink-100 text-ink-600'
}

export function isActiveRequest(status: RequestStatus): boolean {
  return status === 'submitted'
}

export function requestActions(status: RequestStatus): ReviewAction[] {
  return LEGAL_ACTIONS[status]
}

export function roomTypeKey(roomType: RoomType): string {
  return `requests.roomTypes.${roomType}`
}
