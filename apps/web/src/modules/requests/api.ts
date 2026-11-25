import { apiRequest } from '@/api/client'
import type {
  AccommodationRequest,
  RequestCreatePayload,
  RequestPage,
  RequestQueuePage,
  RequestStatus,
  RequestSummary,
  ReviewAction,
} from '@/api/types'

export interface RequestQueueParams {
  status?: RequestStatus
  page?: number
  per_page?: number
}

function toQuery(params: RequestQueueParams): string {
  const search = new URLSearchParams()
  if (params.status) search.set('status', params.status)
  if (params.page) search.set('page', String(params.page))
  if (params.per_page) search.set('per_page', String(params.per_page))
  const query = search.toString()
  return query ? `?${query}` : ''
}

export const requestsApi = {
  list(): Promise<RequestPage> {
    return apiRequest<RequestPage>('/requests?per_page=50')
  },

  create(payload: RequestCreatePayload): Promise<AccommodationRequest> {
    return apiRequest<AccommodationRequest>('/requests', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  withdraw(id: string): Promise<AccommodationRequest> {
    return apiRequest<AccommodationRequest>(`/requests/${id}/withdraw`, { method: 'POST' })
  },

  listQueue(params: RequestQueueParams = {}): Promise<RequestQueuePage> {
    return apiRequest<RequestQueuePage>(`/requests/queue${toQuery(params)}`)
  },

  updateStatus(id: string, status: ReviewAction): Promise<RequestSummary> {
    return apiRequest<RequestSummary>(`/requests/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    })
  },
}
