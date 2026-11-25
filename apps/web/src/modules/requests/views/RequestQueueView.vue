<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { ApiError } from '@/api/client'
import type { RequestSummary, ReviewAction } from '@/api/types'
import { formatDate } from '@/app/i18n'
import { requestsApi } from '@/modules/requests/api'
import {
  REQUEST_FILTERS,
  requestActions,
  requestStatusClass,
  requestStatusKey,
  roomTypeKey,
  type RequestFilter,
} from '@/modules/requests/format'
import BrandMark from '@/shared/components/BrandMark.vue'

const { t } = useI18n()

const filter = ref<RequestFilter>('submitted')
const items = ref<RequestSummary[]>([])
const total = ref(0)
const loading = ref(true)
const error = ref<string | null>(null)

const submittingId = ref<string | null>(null)
const actionError = ref<string | null>(null)
const success = ref<string | null>(null)

function messageFor(err: unknown): string {
  if (!(err instanceof ApiError)) return t('auth.errors.network')
  const key = `requests.errors.${err.code}`
  const translated = t(key)
  return translated === key ? t('requests.errors.unknown') : translated
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const page = await requestsApi.listQueue({
      status: filter.value === 'all' ? undefined : filter.value,
      per_page: 50,
    })
    items.value = page.items
    total.value = page.meta.total
  } catch (err) {
    items.value = []
    total.value = 0
    error.value = messageFor(err)
  } finally {
    loading.value = false
  }
}

async function review(item: RequestSummary, status: ReviewAction): Promise<void> {
  if (submittingId.value) return
  submittingId.value = item.id
  actionError.value = null
  success.value = null
  try {
    const updated = await requestsApi.updateStatus(item.id, status)
    success.value = t('requests.review.changed', {
      status: t(requestStatusKey(updated.status)),
    })
    if (filter.value === status) {
      await load()
    } else {
      // Follow the request into its new queue so the change is visible immediately.
      filter.value = status
    }
  } catch (err) {
    actionError.value = messageFor(err)
  } finally {
    submittingId.value = null
  }
}

watch(filter, () => {
  void load()
})

onMounted(load)
</script>

<template>
  <div class="min-h-screen bg-sand-50">
    <header class="sticky top-0 z-30 border-b border-ink-100/80 bg-sand-50/85 backdrop-blur">
      <div class="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <RouterLink to="/dashboard" class="flex items-center gap-2.5">
          <BrandMark :size="36" decorative />
          <div class="leading-tight">
            <span class="text-base font-extrabold text-ink-950">{{ t('app.name') }}</span>
            <span class="ms-2 hidden text-[0.65rem] tracking-[0.25em] text-ink-400 sm:inline">
              {{ t('app.latin') }}
            </span>
          </div>
        </RouterLink>
        <RouterLink to="/dashboard" class="btn-ghost">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <path d="M9 4 2 12l7 8M2 12h20" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <span class="hidden sm:inline">{{ t('requests.review.back') }}</span>
        </RouterLink>
      </div>
    </header>

    <main id="main-content" class="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
      <section class="flex flex-col gap-2">
        <p class="text-[0.65rem] font-bold uppercase tracking-[0.2em] text-teal-700">
          {{ t('requests.review.eyebrow') }}
        </p>
        <h1 class="text-2xl font-extrabold tracking-tight text-ink-950 sm:text-3xl">
          {{ t('requests.review.title') }}
        </h1>
        <p class="max-w-2xl text-sm leading-7 text-ink-500">{{ t('requests.review.subtitle') }}</p>
      </section>

      <p
        v-if="success"
        role="status"
        class="mt-5 rounded-2xl border border-teal-200 bg-teal-50 p-4 text-sm font-semibold text-teal-900"
      >
        {{ success }}
      </p>
      <p
        v-if="actionError"
        role="alert"
        class="mt-5 rounded-2xl border border-red-200 bg-red-50/70 p-4 text-sm font-semibold text-red-700"
      >
        {{ actionError }}
      </p>

      <div
        class="mt-6 flex flex-wrap items-center gap-2"
        role="group"
        :aria-label="t('requests.review.filtersLabel')"
      >
        <button
          v-for="option in REQUEST_FILTERS"
          :key="option"
          type="button"
          class="rounded-full border px-4 py-2 text-xs font-semibold transition"
          :class="
            filter === option
              ? 'border-teal-600 bg-teal-600 text-white'
              : 'border-ink-200 bg-white text-ink-600 hover:border-ink-300'
          "
          :aria-pressed="filter === option"
          @click="filter = option"
        >
          {{ t(`requests.review.filters.${option}`) }}
        </button>
        <span class="ms-auto text-xs text-ink-400">
          {{ t('requests.review.total', { count: total }) }}
        </span>
      </div>

      <section class="mt-6" :aria-busy="loading">
        <div v-if="loading" class="space-y-3">
          <div v-for="index in 3" :key="index" class="skeleton h-36 w-full"></div>
        </div>

        <div v-else-if="error" class="rounded-2xl border border-red-200 bg-red-50/60 p-5">
          <p class="text-sm font-semibold text-red-700">{{ error }}</p>
          <button type="button" class="btn-primary mt-4" @click="load">
            {{ t('common.retry') }}
          </button>
        </div>

        <div
          v-else-if="items.length === 0"
          class="rounded-2xl border border-dashed border-ink-200 bg-white p-8 text-center"
        >
          <p class="text-sm font-semibold text-ink-700">{{ t('requests.review.empty') }}</p>
          <p class="mt-1 text-xs text-ink-400">{{ t('requests.review.emptyHint') }}</p>
        </div>

        <ul v-else class="space-y-3">
          <li
            v-for="item in items"
            :key="item.id"
            class="rounded-2xl border border-ink-100 bg-white p-5 shadow-sm"
          >
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p class="text-sm font-bold text-ink-900">{{ item.applicant_name }}</p>
                <p class="mt-1 text-xs text-ink-500">
                  {{ item.dormitory_name }} · {{ t(roomTypeKey(item.room_type)) }} ·
                  {{ t('requests.list.months', { count: item.duration_months }) }} ·
                  {{ formatDate(item.desired_move_in) }}
                </p>
              </div>
              <span
                class="rounded-full border px-2.5 py-1 text-[0.65rem] font-bold"
                :class="requestStatusClass(item.status)"
              >
                {{ t(requestStatusKey(item.status)) }}
              </span>
            </div>

            <p v-if="item.note" class="mt-3 rounded-xl bg-sand-50 p-3 text-xs leading-6 text-ink-600">
              {{ item.note }}
            </p>

            <div class="mt-4 flex flex-wrap items-center justify-between gap-3">
              <span class="text-[0.7rem] text-ink-400">
                {{ t('requests.list.submittedOn', { date: formatDate(item.created_at) }) }}
              </span>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="action in requestActions(item.status)"
                  :key="action"
                  type="button"
                  class="rounded-xl border border-ink-200 bg-white px-3 py-2 text-xs font-semibold text-ink-700 transition hover:border-teal-300 hover:text-teal-800"
                  :disabled="submittingId === item.id"
                  @click="review(item, action)"
                >
                  {{ t(`requests.review.actions.${action}`) }}
                </button>
              </div>
            </div>
          </li>
        </ul>
      </section>
    </main>
  </div>
</template>
