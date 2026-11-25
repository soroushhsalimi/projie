import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { describe, expect, it, vi } from 'vitest'
import { createMemoryHistory } from 'vue-router'

import { ApiError } from '@/api/client'
import { i18n } from '@/app/i18n'
import { createAppRouter } from '@/app/router'
import type { RequestSummary } from '@/api/types'
import {
  REQUEST_FILTERS,
  requestActions,
  requestStatusClass,
  requestStatusKey,
} from '@/modules/requests/format'

vi.mock('@/modules/requests/api', () => ({
  requestsApi: {
    list: vi.fn(),
    create: vi.fn(),
    withdraw: vi.fn(),
    listQueue: vi.fn(),
    updateStatus: vi.fn(),
  },
}))

import { requestsApi } from '@/modules/requests/api'
import RequestQueueView from '@/modules/requests/views/RequestQueueView.vue'

describe('request review helpers', () => {
  it('maps a review status to its translation key', () => {
    expect(requestStatusKey('under_review')).toBe('requests.status.under_review')
  })

  it('offers only the legal review actions', () => {
    expect(requestActions('submitted')).toEqual(['under_review', 'approved', 'rejected'])
    expect(requestActions('under_review')).toEqual(['approved', 'rejected'])
    expect(requestActions('approved')).toEqual([])
    expect(requestActions('rejected')).toEqual([])
    expect(requestActions('withdrawn')).toEqual([])
  })

  it('exposes every queue filter', () => {
    expect(REQUEST_FILTERS).toEqual([
      'all',
      'submitted',
      'under_review',
      'approved',
      'rejected',
    ])
  })

  it('gives each status a distinct badge class', () => {
    const classes = new Set(
      (
        ['submitted', 'under_review', 'approved', 'rejected', 'withdrawn'] as const
      ).map((status) => requestStatusClass(status)),
    )
    expect(classes.size).toBe(5)
  })
})

describe('request review route', () => {
  const router = createAppRouter(createMemoryHistory())

  it('resolves the manager queue', () => {
    expect(router.resolve('/requests/review').name).toBe('request-review')
  })

  it('is authenticated and limited to managers and admins', () => {
    const route = router.getRoutes().find((item) => item.name === 'request-review')
    expect(route?.meta.requiresAuth).toBe(true)
    expect(route?.meta.roles).toEqual(['manager', 'admin'])
  })
})

const pending: RequestSummary = {
  id: 'r1',
  applicant_name: 'سارا محمدی',
  dormitory_name: 'خوابگاه الزهرا',
  room_type: 'double',
  desired_move_in: '2027-02-01',
  duration_months: 6,
  note: 'اتاق نزدیک پنجره',
  status: 'submitted',
  created_at: '2026-11-25T10:00:00Z',
  updated_at: '2026-11-25T10:00:00Z',
}

describe('RequestQueueView', () => {
  it('shows submitted requests with the applicant name', async () => {
    vi.mocked(requestsApi.listQueue).mockResolvedValue({
      items: [pending],
      meta: { page: 1, per_page: 50, total: 1 },
    })

    const wrapper = mount(RequestQueueView, {
      global: { plugins: [i18n, createPinia()], stubs: { RouterLink: true } },
    })
    await flushPromises()

    expect(requestsApi.listQueue).toHaveBeenCalledWith({ status: 'submitted', per_page: 50 })
    expect(wrapper.text()).toContain('سارا محمدی')
    expect(wrapper.text()).toContain('خوابگاه الزهرا')
    expect(wrapper.text()).toContain('ثبت‌شده')
  })

  it('follows a reviewed request into its new status filter', async () => {
    vi.mocked(requestsApi.listQueue).mockResolvedValue({
      items: [pending],
      meta: { page: 1, per_page: 50, total: 1 },
    })
    vi.mocked(requestsApi.updateStatus).mockResolvedValue({ ...pending, status: 'approved' })

    const wrapper = mount(RequestQueueView, {
      global: { plugins: [i18n, createPinia()], stubs: { RouterLink: true } },
    })
    await flushPromises()

    const approve = wrapper.findAll('button').find((button) => button.text() === 'تأیید')
    expect(approve).toBeDefined()
    await approve!.trigger('click')
    await flushPromises()

    expect(requestsApi.updateStatus).toHaveBeenCalledWith('r1', 'approved')
    expect(requestsApi.listQueue).toHaveBeenLastCalledWith({ status: 'approved', per_page: 50 })
    expect(wrapper.get('[role="group"] [aria-pressed="true"]').text()).toBe('تأییدشده')
    expect(wrapper.text()).toContain('وضعیت درخواست به «تأییدشده» تغییر کرد.')
  })

  it('reports a stale transition as a conflict', async () => {
    vi.mocked(requestsApi.listQueue).mockResolvedValue({
      items: [pending],
      meta: { page: 1, per_page: 50, total: 1 },
    })
    vi.mocked(requestsApi.updateStatus).mockRejectedValue(
      new ApiError(409, 'request_transition_not_allowed', 'nope'),
    )

    const wrapper = mount(RequestQueueView, {
      global: { plugins: [i18n, createPinia()], stubs: { RouterLink: true } },
    })
    await flushPromises()

    const start = wrapper.findAll('button').find((button) => button.text() === 'شروع بررسی')
    await start!.trigger('click')
    await flushPromises()

    expect(wrapper.find('[role="alert"]').text()).toContain('این تغییر وضعیت مجاز نیست')
  })
})
