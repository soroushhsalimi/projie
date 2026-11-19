import { apiRequest, refreshSession } from '@/api/client'
import type { LoginPayload, RegisterPayload, TokenResponse, User } from '@/api/types'

export const authApi = {
  login(payload: LoginPayload): Promise<TokenResponse> {
    return apiRequest<TokenResponse>(
      '/auth/login',
      { method: 'POST', body: JSON.stringify(payload) },
      { retry: false },
    )
  },

  register(payload: RegisterPayload): Promise<TokenResponse> {
    return apiRequest<TokenResponse>(
      '/auth/register',
      { method: 'POST', body: JSON.stringify(payload) },
      { retry: false },
    )
  },

  logout(): Promise<void> {
    return apiRequest<void>('/auth/logout', { method: 'POST' }, { retry: false })
  },

  me(): Promise<User> {
    return apiRequest<User>('/auth/me')
  },

  refresh(): Promise<TokenResponse | null> {
    return refreshSession()
  },
}
