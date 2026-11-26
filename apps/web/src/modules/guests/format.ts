import type { GuestStatus } from '@/api/types'
import { i18n } from '@/app/i18n'

export const GUEST_FILTERS = ['all', 'expected', 'checked_in', 'checked_out'] as const
export type GuestFilter = (typeof GUEST_FILTERS)[number]

export type GuestAction = 'check_in' | 'check_out'

export function guestStatusKey(status: GuestStatus): string {
  return `guests.status.${status}`
}

export function guestStatusClass(status: GuestStatus): string {
  if (status === 'expected') return 'border-gold-300 bg-gold-400/15 text-ink-800'
  if (status === 'checked_in') return 'border-teal-200 bg-teal-100 text-teal-800'
  return 'border-ink-200 bg-ink-100 text-ink-600'
}

/** Mirrors the server state machine (SPEC-0008 FR-4, FR-5); the API stays authoritative. */
export function guestActions(status: GuestStatus): GuestAction[] {
  if (status === 'expected') return ['check_in']
  if (status === 'checked_in') return ['check_out']
  return []
}

/** The window must end after it starts (SPEC-0008 FR-3). */
export function isWindowOrdered(from: string, until: string): boolean {
  if (!from || !until) return false
  return new Date(until).getTime() > new Date(from).getTime()
}

export function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat(i18n.global.locale.value, {
    dateStyle: 'short',
    timeStyle: 'short',
    timeZone: 'UTC',
  }).format(new Date(value))
}

/** `<input type="datetime-local">` holds a local wall-clock value; the API takes UTC ISO. */
export function toIsoUtc(value: string): string {
  return new Date(value).toISOString()
}
