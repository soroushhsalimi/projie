import type { GuestVisit, GuestVisitCreatePayload, GuestVisitPage, GuestStatus } from '@/api/types'
import { apiRequest } from '@/api/client'

export interface GuestListParams {
  status?: GuestStatus
  page?: number
  per_page?: number
}

function toQuery(params: GuestListParams): string {
  const search = new URLSearchParams()
  if (params.status) search.set('status', params.status)
  if (params.page) search.set('page', String(params.page))
  if (params.per_page) search.set('per_page', String(params.per_page))
  const query = search.toString()
  return query ? `?${query}` : ''
}

export const guestsApi = {
  list(params: GuestListParams = {}): Promise<GuestVisitPage> {
    return apiRequest<GuestVisitPage>(`/guests${toQuery(params)}`)
  },

  detail(id: string): Promise<GuestVisit> {
    return apiRequest<GuestVisit>(`/guests/${id}`)
  },

  register(payload: GuestVisitCreatePayload): Promise<GuestVisit> {
    return apiRequest<GuestVisit>('/guests', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  checkIn(id: string): Promise<GuestVisit> {
    return apiRequest<GuestVisit>(`/guests/${id}/check-in`, { method: 'POST' })
  },

  checkOut(id: string): Promise<GuestVisit> {
    return apiRequest<GuestVisit>(`/guests/${id}/check-out`, { method: 'POST' })
  },
}
