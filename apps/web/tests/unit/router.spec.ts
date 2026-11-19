import { describe, expect, it } from 'vitest'
import { createMemoryHistory } from 'vue-router'

import { createAppRouter } from '@/app/router'

describe('app router', () => {
  const router = createAppRouter(createMemoryHistory())

  it('resolves the auth routes', () => {
    expect(router.resolve('/login').name).toBe('login')
    expect(router.resolve('/register').name).toBe('register')
    expect(router.resolve('/dashboard').name).toBe('dashboard')
  })

  it('resolves unknown routes to not-found', () => {
    const resolved = router.resolve('/this/does/not/exist')
    expect(resolved.name).toBe('not-found')
  })

  it('marks the dashboard as authenticated-only', () => {
    const dashboard = router.getRoutes().find((route) => route.name === 'dashboard')
    expect(dashboard?.meta.requiresAuth).toBe(true)
  })

  it('marks login and register as guest-only', () => {
    for (const name of ['login', 'register']) {
      const route = router.getRoutes().find((item) => item.name === name)
      expect(route?.meta.guestOnly).toBe(true)
    }
  })
})
