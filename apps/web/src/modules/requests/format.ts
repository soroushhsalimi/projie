import type { RequestStatus, RoomType } from '@/api/types'

export const ROOM_TYPES = ['single', 'double', 'triple', 'quad'] as const

export function requestStatusKey(status: RequestStatus): string {
  return `requests.status.${status}`
}

export function requestStatusClass(status: RequestStatus): string {
  if (status === 'submitted') return 'border-gold-300 bg-gold-400/15 text-ink-800'
  return 'border-ink-200 bg-ink-100 text-ink-600'
}

export function isActiveRequest(status: RequestStatus): boolean {
  return status === 'submitted'
}

export function roomTypeKey(roomType: RoomType): string {
  return `requests.roomTypes.${roomType}`
}
