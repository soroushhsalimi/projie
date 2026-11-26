import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import type { TokenResponse, User } from '@/api/types'

vi.mock('@/api/client', () => ({
  setAccessToken: vi.fn(),
}))

vi.mock('@/modules/auth/api', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    me: vi.fn(),
    refresh: vi.fn(),
  },
}))

import { authApi } from '@/modules/auth/api'
import { useAuthStore } from '@/modules/auth/stores/auth'

const user: User = {
  id: '0190f1b0-0000-7000-8000-000000000001',
  email: 'ali@example.com',
  full_name: 'علی رضایی',
  national_id: '0012345679',
  phone: '09121234567',
  address: 'تهران، خیابان آزادی، پلاک ۱۲',
  role: 'user',
  status: 'active',
  created_at: '2026-11-19T00:00:00Z',
}

const session: TokenResponse = {
  access_token: 'access-token',
  token_type: 'bearer',
  expires_in: 900,
  user,
}

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.mocked(authApi.login).mockReset()
    vi.mocked(authApi.register).mockReset()
    vi.mocked(authApi.logout).mockReset()
    vi.mocked(authApi.refresh).mockReset()
  })

  it('starts in idle and restores a session through refresh', async () => {
    vi.mocked(authApi.refresh).mockResolvedValue(session)
    const store = useAuthStore()

    expect(store.phase).toBe('idle')
    await store.ensureInitialized()

    expect(store.phase).toBe('authenticated')
    expect(store.isAuthenticated).toBe(true)
    expect(store.user?.email).toBe('ali@example.com')
  })

  it('becomes guest when no refresh cookie exists', async () => {
    vi.mocked(authApi.refresh).mockResolvedValue(null)
    const store = useAuthStore()

    await store.ensureInitialized()

    expect(store.phase).toBe('guest')
    expect(store.isAuthenticated).toBe(false)
  })

  it('adopts the session on login', async () => {
    vi.mocked(authApi.login).mockResolvedValue(session)
    const store = useAuthStore()

    await store.login({ email: 'ali@example.com', password: 'CorrectHorseBatteryStaple' })

    expect(store.user).toEqual(user)
    expect(store.accessToken).toBe('access-token')
    expect(store.isAuthenticated).toBe(true)
    expect(store.submitting).toBe(false)
  })

  it('does not authenticate on a failed login and resets submitting', async () => {
    vi.mocked(authApi.login).mockRejectedValue(new Error('invalid_credentials'))
    const store = useAuthStore()

    await expect(
      store.login({ email: 'ali@example.com', password: 'wrong-password' }),
    ).rejects.toThrow()

    expect(store.isAuthenticated).toBe(false)
    expect(store.submitting).toBe(false)
  })

  it('clears the session on logout even when the network fails', async () => {
    vi.mocked(authApi.refresh).mockResolvedValue(session)
    vi.mocked(authApi.logout).mockRejectedValue(new Error('offline'))
    const store = useAuthStore()
    await store.ensureInitialized()

    await store.logout()

    expect(store.phase).toBe('guest')
    expect(store.user).toBeNull()
    expect(store.accessToken).toBeNull()
  })
})
