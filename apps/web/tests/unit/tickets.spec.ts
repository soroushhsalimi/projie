import { describe, expect, it } from 'vitest'
import { createMemoryHistory } from 'vue-router'

import { createAppRouter } from '@/app/router'
import {
  TICKET_FILTERS,
  ticketActions,
  ticketStatusClass,
  ticketStatusKey,
} from '@/modules/tickets/format'

describe('ticket presentation helpers', () => {
  it('maps a status to its translation key', () => {
    expect(ticketStatusKey('under_review')).toBe('tickets.status.under_review')
  })

  it('offers only the legal next actions', () => {
    expect(ticketActions('open')).toEqual(['under_review', 'resolved'])
    expect(ticketActions('under_review')).toEqual(['resolved'])
    expect(ticketActions('resolved')).toEqual([])
  })

  it('exposes every queue filter', () => {
    expect(TICKET_FILTERS).toEqual(['all', 'open', 'under_review', 'resolved'])
  })

  it('gives each status a distinct badge class', () => {
    const classes = new Set(
      (['open', 'under_review', 'resolved'] as const).map((status) => ticketStatusClass(status)),
    )
    expect(classes.size).toBe(3)
  })
})

describe('tickets route', () => {
  const router = createAppRouter(createMemoryHistory())

  it('resolves the manager queue', () => {
    expect(router.resolve('/tickets').name).toBe('tickets')
  })

  it('is authenticated and limited to managers and admins', () => {
    const route = router.getRoutes().find((item) => item.name === 'tickets')
    expect(route?.meta.requiresAuth).toBe(true)
    expect(route?.meta.roles).toEqual(['manager', 'admin'])
  })
})
