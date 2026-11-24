import { apiRequest } from '@/api/client'
import type { TicketDetail, TicketPage, TicketStatus } from '@/api/types'

export interface TicketListParams {
  status?: Exclude<TicketStatus, never>
  page?: number
  per_page?: number
}

function toQuery(params: TicketListParams): string {
  const search = new URLSearchParams()
  if (params.status) search.set('status', params.status)
  if (params.page) search.set('page', String(params.page))
  if (params.per_page) search.set('per_page', String(params.per_page))
  const query = search.toString()
  return query ? `?${query}` : ''
}

export const ticketsApi = {
  list(params: TicketListParams = {}): Promise<TicketPage> {
    return apiRequest<TicketPage>(`/tickets${toQuery(params)}`)
  },

  detail(id: string): Promise<TicketDetail> {
    return apiRequest<TicketDetail>(`/tickets/${id}`)
  },

  reply(id: string, body: string): Promise<TicketDetail> {
    return apiRequest<TicketDetail>(`/tickets/${id}/messages`, {
      method: 'POST',
      body: JSON.stringify({ body }),
    })
  },

  updateStatus(id: string, status: 'under_review' | 'resolved'): Promise<TicketDetail> {
    return apiRequest<TicketDetail>(`/tickets/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    })
  },
}
