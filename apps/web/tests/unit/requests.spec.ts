import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { describe, expect, it, vi } from 'vitest'
import { createMemoryHistory } from 'vue-router'

import { i18n } from '@/app/i18n'
import { createAppRouter } from '@/app/router'
import type { AccommodationRequest } from '@/api/types'
import {
  ROOM_TYPES,
  isActiveRequest,
  requestStatusKey,
  roomTypeKey,
} from '@/modules/requests/format'

vi.mock('@/modules/requests/api', () => ({
  requestsApi: {
    list: vi.fn(),
    create: vi.fn(),
    withdraw: vi.fn(),
  },
}))

import { requestsApi } from '@/modules/requests/api'
import RequestsView from '@/modules/requests/views/RequestsView.vue'

const submitted: AccommodationRequest = {
  id: 'r1',
  dormitory_name: 'خوابگاه الزهرا',
  room_type: 'double',
  desired_move_in: '2027-02-01',
  duration_months: 6,
  note: null,
  status: 'submitted',
  created_at: '2026-11-25T10:00:00Z',
  updated_at: '2026-11-25T10:00:00Z',
}

describe('accommodation request helpers', () => {
  it('exposes the four room types', () => {
    expect(ROOM_TYPES).toEqual(['single', 'double', 'triple', 'quad'])
  })

  it('maps statuses and room types to translation keys', () => {
    expect(requestStatusKey('submitted')).toBe('requests.status.submitted')
    expect(roomTypeKey('quad')).toBe('requests.roomTypes.quad')
  })

  it('treats only a submitted request as active', () => {
    expect(isActiveRequest('submitted')).toBe(true)
    expect(isActiveRequest('withdrawn')).toBe(false)
  })
})

describe('requests route', () => {
  const router = createAppRouter(createMemoryHistory())

  it('resolves the resident request page', () => {
    expect(router.resolve('/requests').name).toBe('requests')
  })

  it('is authenticated and limited to residents', () => {
    const route = router.getRoutes().find((item) => item.name === 'requests')
    expect(route?.meta.requiresAuth).toBe(true)
    expect(route?.meta.roles).toEqual(['user'])
  })
})

describe('RequestsView', () => {
  it('submits the form and shows the created request', async () => {
    vi.mocked(requestsApi.list)
      .mockResolvedValueOnce({ items: [], meta: { page: 1, per_page: 50, total: 0 } })
      .mockResolvedValue({ items: [submitted], meta: { page: 1, per_page: 50, total: 1 } })
    vi.mocked(requestsApi.create).mockResolvedValue(submitted)

    const wrapper = mount(RequestsView, {
      global: { plugins: [i18n, createPinia()], stubs: { RouterLink: true } },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('هنوز درخواستی ثبت نکرده‌ای.')

    await wrapper.get('#request-dormitory').setValue('خوابگاه الزهرا')
    await wrapper.get('#request-move-in').setValue('2027-02-01')
    await wrapper.get('#request-duration').setValue('6')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(requestsApi.create).toHaveBeenCalledWith({
      dormitory_name: 'خوابگاه الزهرا',
      room_type: 'double',
      desired_move_in: '2027-02-01',
      duration_months: 6,
      note: null,
    })
    expect(wrapper.text()).toContain('درخواستت ثبت شد')
    expect(wrapper.text()).toContain('خوابگاه الزهرا')
    expect(wrapper.text()).toContain('ثبت‌شده')
  })

  it('refuses an empty form without calling the API', async () => {
    vi.mocked(requestsApi.list).mockResolvedValue({
      items: [],
      meta: { page: 1, per_page: 50, total: 0 },
    })

    const wrapper = mount(RequestsView, {
      global: { plugins: [i18n, createPinia()], stubs: { RouterLink: true } },
    })
    await flushPromises()

    await wrapper.get('#request-dormitory').setValue(' ')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(requestsApi.create).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('نام خوابگاه باید حداقل ۲ کاراکتر باشد.')
  })

  it('withdraws an active request and refreshes the list', async () => {
    vi.mocked(requestsApi.list)
      .mockResolvedValueOnce({ items: [submitted], meta: { page: 1, per_page: 50, total: 1 } })
      .mockResolvedValue({
        items: [{ ...submitted, status: 'withdrawn' }],
        meta: { page: 1, per_page: 50, total: 1 },
      })
    vi.mocked(requestsApi.withdraw).mockResolvedValue({ ...submitted, status: 'withdrawn' })

    const wrapper = mount(RequestsView, {
      global: { plugins: [i18n, createPinia()], stubs: { RouterLink: true } },
    })
    await flushPromises()

    const withdraw = wrapper.findAll('button').find((button) => button.text() === 'لغو درخواست')
    expect(withdraw).toBeDefined()
    await withdraw!.trigger('click')
    await flushPromises()

    expect(requestsApi.withdraw).toHaveBeenCalledWith('r1')
    expect(wrapper.text()).toContain('لغوشده')
    expect(wrapper.text()).not.toContain('لغو درخواست')
  })
})
