import { apiRequest } from '@/api/client'
import type { AccommodationRequest, RequestCreatePayload, RequestPage } from '@/api/types'

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
}
