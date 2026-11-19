import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { setAccessToken } from '@/api/client'
import type { LoginPayload, RegisterPayload, TokenResponse, User } from '@/api/types'
import { authApi } from '@/modules/auth/api'

export type AuthPhase = 'idle' | 'restoring' | 'authenticated' | 'guest'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(null)
  const phase = ref<AuthPhase>('idle')
  const submitting = ref(false)
  let initialization: Promise<void> | null = null

  const isAuthenticated = computed(() => phase.value === 'authenticated' && user.value !== null)
  const isRestoring = computed(() => phase.value === 'idle' || phase.value === 'restoring')
  const displayName = computed(() => user.value?.full_name ?? '')

  function adopt(session: TokenResponse): void {
    user.value = session.user
    accessToken.value = session.access_token
    setAccessToken(session.access_token)
    phase.value = 'authenticated'
  }

  function clear(): void {
    user.value = null
    accessToken.value = null
    setAccessToken(null)
    phase.value = 'guest'
  }

  async function ensureInitialized(): Promise<void> {
    if (phase.value !== 'idle') return
    if (!initialization) {
      initialization = (async () => {
        phase.value = 'restoring'
        try {
          const session = await authApi.refresh()
          if (session) adopt(session)
          else clear()
        } catch {
          clear()
        }
      })()
    }
    await initialization
  }

  async function login(payload: LoginPayload): Promise<User> {
    submitting.value = true
    try {
      const session = await authApi.login(payload)
      adopt(session)
      return session.user
    } finally {
      submitting.value = false
    }
  }

  async function register(payload: RegisterPayload): Promise<User> {
    submitting.value = true
    try {
      const session = await authApi.register(payload)
      adopt(session)
      return session.user
    } finally {
      submitting.value = false
    }
  }

  async function logout(): Promise<void> {
    submitting.value = true
    try {
      await authApi.logout()
    } catch {
      // A failed network call must not keep the UI in a signed-in state.
    } finally {
      clear()
      submitting.value = false
    }
  }

  async function loadProfile(): Promise<void> {
    if (!accessToken.value) return
    user.value = await authApi.me()
  }

  return {
    user,
    accessToken,
    phase,
    submitting,
    isAuthenticated,
    isRestoring,
    displayName,
    ensureInitialized,
    login,
    register,
    logout,
    loadProfile,
    clear,
  }
})
