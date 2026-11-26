import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { describe, expect, it, vi } from 'vitest'
import { createMemoryHistory } from 'vue-router'

import { i18n } from '@/app/i18n'
import { createAppRouter } from '@/app/router'
import type { ComplaintDetail, ComplaintSummary } from '@/api/types'
import {
  COMPLAINT_FILTERS,
  canRespond,
  complaintActions,
  complaintStatusClass,
  complaintStatusKey,
} from '@/modules/complaints/format'

vi.mock('@/modules/complaints/api', () => ({
  complaintsApi: {
    list: vi.fn(),
    detail: vi.fn(),
    startReview: vi.fn(),
    respond: vi.fn(),
  },
}))

import { complaintsApi } from '@/modules/complaints/api'
import ComplaintsView from '@/modules/complaints/views/ComplaintsView.vue'

describe('complaint presentation helpers', () => {
  it('maps a status to its translation key', () => {
    expect(complaintStatusKey('in_review')).toBe('complaints.status.in_review')
  })

  it('offers review only before the complaint is answered', () => {
    expect(complaintActions('submitted')).toEqual(['in_review'])
    expect(complaintActions('in_review')).toEqual([])
    expect(complaintActions('answered')).toEqual([])
  })

  it('accepts a response until the complaint is answered', () => {
    expect(canRespond('submitted')).toBe(true)
    expect(canRespond('in_review')).toBe(true)
    expect(canRespond('answered')).toBe(false)
  })

  it('exposes every queue filter', () => {
    expect(COMPLAINT_FILTERS).toEqual(['all', 'submitted', 'in_review', 'answered'])
  })

  it('gives each status a distinct badge class', () => {
    const classes = new Set(
      (['submitted', 'in_review', 'answered'] as const).map((status) =>
        complaintStatusClass(status),
      ),
    )
    expect(classes.size).toBe(3)
  })
})

const summary: ComplaintSummary = {
  id: 'c1',
  subject: 'سر و صدای شبانه در طبقه سوم',
  category: 'noise',
  status: 'submitted',
  resident_name: 'سارا محمدی',
  created_at: '2026-11-22T20:10:00Z',
  updated_at: '2026-11-22T20:10:00Z',
}

const detail: ComplaintDetail = {
  ...summary,
  description: 'هر شب بعد از ساعت ۱۲ صدای بلند می‌آید.',
  response: null,
}

describe('ComplaintsView', () => {
  it('starts the review and records the initial response', async () => {
    vi.mocked(complaintsApi.list).mockResolvedValue({
      items: [summary],
      meta: { page: 1, per_page: 50, total: 1 },
    })
    vi.mocked(complaintsApi.detail).mockResolvedValue(detail)
    vi.mocked(complaintsApi.startReview).mockResolvedValue({ ...detail, status: 'in_review' })
    vi.mocked(complaintsApi.respond).mockResolvedValue({
      ...detail,
      status: 'answered',
      response: {
        id: 'r1',
        body: 'با ساکنان طبقه سوم صحبت شد.',
        responder_name: 'رضا کریمی',
        created_at: '2026-11-23T08:00:00Z',
      },
    })

    const wrapper = mount(ComplaintsView, {
      global: { plugins: [i18n, createPinia()], stubs: { RouterLink: true } },
    })
    await flushPromises()

    await wrapper.get('ul button').trigger('click')
    await flushPromises()

    const reviewAction = wrapper
      .findAll('form button')
      .find((button) => button.text() === 'شروع بررسی')
    expect(reviewAction).toBeDefined()
    await reviewAction!.trigger('click')
    await flushPromises()

    expect(complaintsApi.startReview).toHaveBeenCalledWith('c1')
    expect(wrapper.get('[role="group"] [aria-pressed="true"]').text()).toBe('در حال بررسی')
    expect(wrapper.get('article h2').text()).toBe(summary.subject)

    await wrapper.get('textarea').setValue('با ساکنان طبقه سوم صحبت شد.')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(complaintsApi.respond).toHaveBeenCalledWith('c1', 'با ساکنان طبقه سوم صحبت شد.')
    expect(wrapper.text()).toContain('پاسخ ثبت‌شده')
    expect(wrapper.find('textarea').exists()).toBe(false)
  })
})

describe('complaints route', () => {
  const router = createAppRouter(createMemoryHistory())

  it('resolves the manager queue', () => {
    expect(router.resolve('/complaints').name).toBe('complaints')
  })

  it('is authenticated and limited to managers and admins', () => {
    const route = router.getRoutes().find((item) => item.name === 'complaints')
    expect(route?.meta.requiresAuth).toBe(true)
    expect(route?.meta.roles).toEqual(['manager', 'admin'])
  })
})
