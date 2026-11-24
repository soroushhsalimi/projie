import type { TicketStatus } from '@/api/types'

export const TICKET_FILTERS = ['all', 'open', 'under_review', 'resolved'] as const
export type TicketFilter = (typeof TICKET_FILTERS)[number]

export type TicketAction = 'under_review' | 'resolved'

/** Mirrors the server state machine (SPEC-0004 FR-4); the API remains authoritative. */
const LEGAL_ACTIONS: Record<TicketStatus, TicketAction[]> = {
  open: ['under_review', 'resolved'],
  under_review: ['resolved'],
  resolved: [],
}

export function ticketStatusKey(status: TicketStatus): string {
  return `tickets.status.${status}`
}

export function ticketStatusClass(status: TicketStatus): string {
  if (status === 'open') return 'border-gold-300 bg-gold-400/15 text-ink-800'
  if (status === 'under_review') return 'border-teal-200 bg-teal-100 text-teal-800'
  return 'border-ink-200 bg-ink-100 text-ink-600'
}

export function ticketActions(status: TicketStatus): TicketAction[] {
  return LEGAL_ACTIONS[status]
}
