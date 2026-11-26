import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { describe, expect, it, vi } from 'vitest'
import { createMemoryHistory } from 'vue-router'

import { i18n } from '@/app/i18n'
import { createAppRouter } from '@/app/router'
import type { GuestVisit } from '@/api/types'
import {
  GUEST_FILTERS,
  guestActions,
  guestStatusClass,
  guestStatusKey,
  isWindowOrdered,
  toIsoUtc,
} from '@/modules/guests/format'

vi.mock('@/modules/guests/api', () => ({
  guestsApi: {
    list: vi.fn(),
    detail: vi.fn(),
    register: vi.fn(),
    checkIn: vi.fn(),
    checkOut: vi.fn(),
  },
}))

import { guestsApi } from '@/modules/guests/api'
import GuestsView from '@/modules/guests/views/GuestsView.vue'

const visit: GuestVisit = {
  id: 'g1',
  guest_name: 'مریم احمدی',
  host_name: 'سارا محمدی',
  purpose: 'ملاقات خانوادگی',
  status: 'expected',
  allowed_from: '2026-11-26T16:00:00Z',
  allowed_until: '2026-11-26T18:00:00Z',
  checked_in_at: null,
  checked_out_at: null,
  overdue: false,
  created_at: '2026-11-26T15:40:00Z',
  updated_at: '2026-11-26T15:40:00Z',
}

describe('guest presentation helpers', () => {
  it('maps a status to its translation key', () => {
    expect(guestStatusKey('checked_in')).toBe('guests.status.checked_in')
  })

  it('offers check-in then check-out and nothing after', () => {
    expect(guestActions('expected')).toEqual(['check_in'])
    expect(guestActions('checked_in')).toEqual(['check_out'])
    expect(guestActions('checked_out')).toEqual([])
  })

  it('requires the allowed window to end after it starts', () => {
    expect(isWindowOrdered('2026-11-26T16:00', '2026-11-26T18:00')).toBe(true)
    expect(isWindowOrdered('2026-11-26T18:00', '2026-11-26T16:00')).toBe(false)
    expect(isWindowOrdered('', '2026-11-26T16:00')).toBe(false)
  })

  it('sends datetime-local input as UTC ISO', () => {
    const local = '2026-11-26T16:00'
    expect(toIsoUtc(local)).toBe(new Date(local).toISOString())
  })

  it('exposes every desk filter', () => {
    expect(GUEST_FILTERS).toEqual(['all', 'expected', 'checked_in', 'checked_out'])
  })

  it('gives each status a distinct badge class', () => {
    const classes = new Set(
      (['expected', 'checked_in', 'checked_out'] as const).map((status) =>
        guestStatusClass(status),
      ),
    )
    expect(classes.size).toBe(3)
  })
})

describe('GuestsView', () => {
  it('checks a guest in and then out', async () => {
    vi.mocked(guestsApi.list).mockResolvedValue({
      items: [visit],
      meta: { page: 1, per_page: 50, total: 1 },
    })
    vi.mocked(guestsApi.detail).mockResolvedValue(visit)
    vi.mocked(guestsApi.checkIn).mockResolvedValue({
      ...visit,
      status: 'checked_in',
      checked_in_at: '2026-11-26T16:10:00Z',
    })
    vi.mocked(guestsApi.checkOut).mockResolvedValue({
      ...visit,
      status: 'checked_out',
      checked_in_at: '2026-11-26T16:10:00Z',
      checked_out_at: '2026-11-26T17:30:00Z',
    })

    const wrapper = mount(GuestsView, {
      global: { plugins: [i18n, createPinia()], stubs: { RouterLink: true } },
    })
    await flushPromises()

    await wrapper.get('ul button').trigger('click')
    await flushPromises()

    const checkIn = wrapper
      .findAll('article button')
      .find((button) => button.text() === 'ثبت ورود')
    expect(checkIn).toBeDefined()
    await checkIn!.trigger('click')
    await flushPromises()

    expect(guestsApi.checkIn).toHaveBeenCalledWith('g1')
    expect(wrapper.get('article h2').text()).toBe('مریم احمدی')
    expect(wrapper.text()).toContain('ورود مهمان ثبت شد.')

    const checkOut = wrapper
      .findAll('article button')
      .find((button) => button.text() === 'ثبت خروج')
    expect(checkOut).toBeDefined()
    await checkOut!.trigger('click')
    await flushPromises()

    expect(guestsApi.checkOut).toHaveBeenCalledWith('g1')
    expect(wrapper.text()).toContain('خروج مهمان ثبت شد.')
  })

  it('registers a guest and selects the new visit', async () => {
    vi.mocked(guestsApi.list).mockResolvedValue({
      items: [],
      meta: { page: 1, per_page: 50, total: 0 },
    })
    vi.mocked(guestsApi.register).mockResolvedValue(visit)

    const wrapper = mount(GuestsView, {
      global: { plugins: [i18n, createPinia()], stubs: { RouterLink: true } },
    })
    await flushPromises()

    await wrapper.get('#guest-name').setValue('مریم احمدی')
    await wrapper.get('#guest-host').setValue('resident@sara.ir')
    await wrapper.get('#guest-from').setValue('2026-11-26T16:00')
    await wrapper.get('#guest-until').setValue('2026-11-26T18:00')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(guestsApi.register).toHaveBeenCalledWith({
      guest_name: 'مریم احمدی',
      host_email: 'resident@sara.ir',
      purpose: null,
      allowed_from: new Date('2026-11-26T16:00').toISOString(),
      allowed_until: new Date('2026-11-26T18:00').toISOString(),
    })
    expect(wrapper.get('article h2').text()).toBe('مریم احمدی')
  })
})

describe('guests route', () => {
  const router = createAppRouter(createMemoryHistory())

  it('resolves the front desk', () => {
    expect(router.resolve('/guests').name).toBe('guests')
  })

  it('is authenticated and limited to managers and admins', () => {
    const route = router.getRoutes().find((item) => item.name === 'guests')
    expect(route?.meta.requiresAuth).toBe(true)
    expect(route?.meta.roles).toEqual(['manager', 'admin'])
  })
})
