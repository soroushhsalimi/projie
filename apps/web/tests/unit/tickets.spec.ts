import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { describe, expect, it, vi } from 'vitest'
import { createMemoryHistory } from 'vue-router'

import { i18n } from '@/app/i18n'
import { createAppRouter } from '@/app/router'
import type { TicketDetail, TicketSummary } from '@/api/types'
import {
  TICKET_FILTERS,
  ticketActions,
  ticketStatusClass,
  ticketStatusKey,
} from '@/modules/tickets/format'

vi.mock('@/modules/tickets/api', () => ({
  ticketsApi: {
    list: vi.fn(),
    detail: vi.fn(),
    reply: vi.fn(),
    updateStatus: vi.fn(),
  },
}))

import { ticketsApi } from '@/modules/tickets/api'
import TicketsView from '@/modules/tickets/views/TicketsView.vue'

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

const summary: TicketSummary = {
  id: 't1',
  subject: 'نشتی شیر آب حمام',
  category: 'plumbing',
  status: 'open',
  reporter_name: 'سارا محمدی',
  created_at: '2026-11-24T10:00:00Z',
  updated_at: '2026-11-24T10:00:00Z',
}

const detail: TicketDetail = { ...summary, description: 'شیر آب چکه می‌کند.', messages: [] }

describe('TicketsView', () => {
  it('follows the ticket into its new status filter and keeps its detail open', async () => {
    vi.mocked(ticketsApi.list).mockResolvedValue({
      items: [summary],
      meta: { page: 1, per_page: 50, total: 1 },
    })
    vi.mocked(ticketsApi.detail).mockResolvedValue(detail)
    vi.mocked(ticketsApi.updateStatus).mockResolvedValue({ ...detail, status: 'resolved' })

    const wrapper = mount(TicketsView, {
      global: { plugins: [i18n, createPinia()], stubs: { RouterLink: true } },
    })
    await flushPromises()

    await wrapper.get('ul button').trigger('click')
    await flushPromises()

    const resolveAction = wrapper
      .findAll('form button')
      .find((button) => button.text() === 'انجام شد')
    expect(resolveAction).toBeDefined()
    await resolveAction!.trigger('click')
    await flushPromises()

    expect(ticketsApi.updateStatus).toHaveBeenCalledWith('t1', 'resolved')
    expect(ticketsApi.list).toHaveBeenLastCalledWith({ status: 'resolved', per_page: 50 })
    expect(wrapper.get('[role="group"] [aria-pressed="true"]').text()).toBe('انجام شد')
    expect(wrapper.get('article h2').text()).toBe(summary.subject)
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
