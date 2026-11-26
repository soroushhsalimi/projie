import { apiRequest } from '@/api/client'
import type { ComplaintDetail, ComplaintPage, ComplaintStatus } from '@/api/types'

export interface ComplaintListParams {
  status?: ComplaintStatus
  page?: number
  per_page?: number
}

function toQuery(params: ComplaintListParams): string {
  const search = new URLSearchParams()
  if (params.status) search.set('status', params.status)
  if (params.page) search.set('page', String(params.page))
  if (params.per_page) search.set('per_page', String(params.per_page))
  const query = search.toString()
  return query ? `?${query}` : ''
}

export const complaintsApi = {
  list(params: ComplaintListParams = {}): Promise<ComplaintPage> {
    return apiRequest<ComplaintPage>(`/complaints${toQuery(params)}`)
  },

  detail(id: string): Promise<ComplaintDetail> {
    return apiRequest<ComplaintDetail>(`/complaints/${id}`)
  },

  startReview(id: string): Promise<ComplaintDetail> {
    return apiRequest<ComplaintDetail>(`/complaints/${id}/status`, {
      method: 'POST',
      body: JSON.stringify({ status: 'in_review' }),
    })
  },

  respond(id: string, body: string): Promise<ComplaintDetail> {
    return apiRequest<ComplaintDetail>(`/complaints/${id}/response`, {
      method: 'POST',
      body: JSON.stringify({ body }),
    })
  },
}
