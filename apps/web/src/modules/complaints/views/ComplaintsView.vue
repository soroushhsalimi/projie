<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { ApiError } from '@/api/client'
import type { ComplaintDetail, ComplaintSummary } from '@/api/types'
import { formatDate } from '@/app/i18n'
import { complaintsApi } from '@/modules/complaints/api'
import {
  COMPLAINT_FILTERS,
  canRespond,
  complaintActions,
  complaintStatusClass,
  complaintStatusKey,
  type ComplaintAction,
  type ComplaintFilter,
} from '@/modules/complaints/format'
import BrandMark from '@/shared/components/BrandMark.vue'

const { t } = useI18n()

const filter = ref<ComplaintFilter>('submitted')
const items = ref<ComplaintSummary[]>([])
const total = ref(0)
const loading = ref(true)
const error = ref<string | null>(null)

const selected = ref<ComplaintDetail | null>(null)
const detailLoading = ref(false)
const answer = ref('')
const submitting = ref(false)
const actionError = ref<string | null>(null)
const answered = ref(false)

const actions = computed(() => (selected.value ? complaintActions(selected.value.status) : []))
const mayRespond = computed(() => (selected.value ? canRespond(selected.value.status) : false))

function messageFor(err: unknown): string {
  if (!(err instanceof ApiError)) return t('auth.errors.network')
  const key = `complaints.errors.${err.code}`
  const translated = t(key)
  return translated === key ? t('complaints.errors.unknown') : translated
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const page = await complaintsApi.list({
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

async function select(complaint: ComplaintSummary): Promise<void> {
  detailLoading.value = true
  actionError.value = null
  answer.value = ''
  answered.value = false
  try {
    selected.value = await complaintsApi.detail(complaint.id)
  } catch (err) {
    selected.value = null
    actionError.value = messageFor(err)
  } finally {
    detailLoading.value = false
  }
}

async function move(action: ComplaintAction): Promise<void> {
  if (!selected.value) return
  submitting.value = true
  actionError.value = null
  try {
    selected.value = await complaintsApi.startReview(selected.value.id)
    if (filter.value === action) {
      await load()
    } else {
      // Follow the complaint into its new queue so the change is visible immediately.
      keepSelectionOnFilterChange = true
      filter.value = action
    }
  } catch (err) {
    actionError.value = messageFor(err)
  } finally {
    submitting.value = false
  }
}

async function sendAnswer(): Promise<void> {
  if (!selected.value || answer.value.trim().length < 2) return
  submitting.value = true
  actionError.value = null
  try {
    selected.value = await complaintsApi.respond(selected.value.id, answer.value.trim())
    answer.value = ''
    answered.value = true
    await load()
  } catch (err) {
    actionError.value = messageFor(err)
  } finally {
    submitting.value = false
  }
}

let keepSelectionOnFilterChange = false

watch(filter, () => {
  if (keepSelectionOnFilterChange) {
    keepSelectionOnFilterChange = false
  } else {
    selected.value = null
  }
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
          <span class="hidden sm:inline">{{ t('complaints.back') }}</span>
        </RouterLink>
      </div>
    </header>

    <main id="main-content" class="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
      <section class="flex flex-col gap-2">
        <p class="text-[0.65rem] font-bold uppercase tracking-[0.2em] text-teal-700">
          {{ t('complaints.eyebrow') }}
        </p>
        <h1 class="text-2xl font-extrabold tracking-tight text-ink-950 sm:text-3xl">
          {{ t('complaints.title') }}
        </h1>
        <p class="max-w-2xl text-sm leading-7 text-ink-500">{{ t('complaints.subtitle') }}</p>
      </section>

      <div class="mt-6 flex flex-wrap items-center gap-2" role="group" :aria-label="t('complaints.filtersLabel')">
        <button
          v-for="option in COMPLAINT_FILTERS"
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
          {{ t(`complaints.filters.${option}`) }}
        </button>
        <span class="ms-auto text-xs text-ink-400">{{ t('complaints.total', { count: total }) }}</span>
      </div>

      <div class="mt-6 grid gap-6 lg:grid-cols-5">
        <section class="lg:col-span-2" :aria-busy="loading">
          <div v-if="loading" class="space-y-3">
            <div v-for="index in 3" :key="index" class="skeleton h-28 w-full"></div>
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
            <p class="text-sm font-semibold text-ink-700">{{ t('complaints.empty') }}</p>
            <p class="mt-1 text-xs text-ink-400">{{ t('complaints.emptyHint') }}</p>
          </div>

          <ul v-else class="space-y-3">
            <li v-for="complaint in items" :key="complaint.id">
              <button
                type="button"
                class="w-full rounded-2xl border bg-white p-4 text-start shadow-sm transition hover:border-teal-300"
                :class="
                  selected?.id === complaint.id
                    ? 'border-teal-400 ring-2 ring-teal-500/15'
                    : 'border-ink-100'
                "
                :aria-pressed="selected?.id === complaint.id"
                @click="select(complaint)"
              >
                <div class="flex items-start justify-between gap-3">
                  <span class="text-sm font-bold text-ink-900">{{ complaint.subject }}</span>
                  <span
                    class="shrink-0 rounded-full border px-2.5 py-1 text-[0.65rem] font-bold"
                    :class="complaintStatusClass(complaint.status)"
                  >
                    {{ t(complaintStatusKey(complaint.status)) }}
                  </span>
                </div>
                <p class="mt-2 text-xs text-ink-500">
                  {{ complaint.resident_name }} · {{ t(`complaints.category.${complaint.category}`) }}
                </p>
                <p class="mt-1 text-[0.7rem] text-ink-400">{{ formatDate(complaint.created_at) }}</p>
              </button>
            </li>
          </ul>
        </section>

        <section class="lg:col-span-3">
          <div
            v-if="!selected && !detailLoading"
            class="flex h-full min-h-48 items-center justify-center rounded-[1.75rem] border border-dashed border-ink-200 bg-white p-8 text-center"
          >
            <p class="text-sm text-ink-400">{{ t('complaints.selectPrompt') }}</p>
          </div>

          <div v-else-if="detailLoading" class="skeleton h-96 w-full"></div>

          <article
            v-else-if="selected"
            class="rounded-[1.75rem] border border-ink-100 bg-white p-6 shadow-sm"
          >
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 class="text-lg font-extrabold text-ink-950">{{ selected.subject }}</h2>
                <p class="mt-1 text-xs text-ink-500">
                  {{ t('complaints.resident') }}: {{ selected.resident_name }} ·
                  {{ t(`complaints.category.${selected.category}`) }}
                </p>
              </div>
              <span
                class="rounded-full border px-3 py-1.5 text-xs font-bold"
                :class="complaintStatusClass(selected.status)"
              >
                {{ t(complaintStatusKey(selected.status)) }}
              </span>
            </div>

            <p class="mt-4 rounded-2xl bg-sand-50 p-4 text-sm leading-7 text-ink-700">
              {{ selected.description }}
            </p>

            <div v-if="selected.response" class="mt-5 rounded-2xl border border-teal-200 bg-teal-50/60 p-4">
              <h3 class="text-xs font-bold uppercase tracking-wider text-teal-800">
                {{ t('complaints.recordedResponse') }}
              </h3>
              <p class="mt-2 text-sm leading-7 text-ink-800">{{ selected.response.body }}</p>
              <p class="mt-2 text-[0.7rem] text-ink-500">
                {{ selected.response.responder_name }} · {{ formatDate(selected.response.created_at) }}
              </p>
            </div>

            <p v-if="actionError" role="alert" class="mt-4 rounded-xl bg-red-50 p-3 text-xs font-semibold text-red-700">
              {{ actionError }}
            </p>

            <p v-if="answered" role="status" class="mt-4 rounded-xl bg-teal-50 p-3 text-xs font-semibold text-teal-800">
              {{ t('complaints.answered') }}
            </p>

            <form class="mt-5" @submit.prevent="sendAnswer">
              <div class="flex flex-wrap items-center gap-2">
                <button
                  v-for="action in actions"
                  :key="action"
                  type="button"
                  class="rounded-xl border border-ink-200 bg-white px-4 py-2.5 text-xs font-semibold text-ink-700 transition hover:border-teal-300 hover:text-teal-800"
                  :disabled="submitting"
                  @click="move(action)"
                >
                  {{ t(`complaints.actions.${action}`) }}
                </button>
              </div>

              <template v-if="mayRespond">
                <label for="complaint-answer" class="field-label mt-4">
                  {{ t('complaints.answerLabel') }}
                </label>
                <textarea
                  id="complaint-answer"
                  v-model="answer"
                  class="field-input min-h-24"
                  maxlength="2000"
                  :placeholder="t('complaints.answerPlaceholder')"
                ></textarea>
                <button
                  type="submit"
                  class="btn-primary mt-3 w-auto px-5 py-2.5"
                  :disabled="submitting || answer.trim().length < 2"
                >
                  {{ submitting ? t('complaints.sending') : t('complaints.answerSubmit') }}
                </button>
              </template>
            </form>
          </article>
        </section>
      </div>
    </main>
  </div>
</template>
