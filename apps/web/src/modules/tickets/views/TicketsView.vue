<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { ApiError } from '@/api/client'
import type { TicketDetail, TicketSummary } from '@/api/types'
import { formatDate } from '@/app/i18n'
import { useAuthStore } from '@/modules/auth/stores/auth'
import { ticketsApi } from '@/modules/tickets/api'
import {
  TICKET_FILTERS,
  ticketActions,
  ticketStatusClass,
  ticketStatusKey,
  type TicketAction,
  type TicketFilter,
} from '@/modules/tickets/format'
import BrandMark from '@/shared/components/BrandMark.vue'

const { t } = useI18n()
const auth = useAuthStore()

const filter = ref<TicketFilter>('open')
const items = ref<TicketSummary[]>([])
const total = ref(0)
const loading = ref(true)
const error = ref<string | null>(null)

const selected = ref<TicketDetail | null>(null)
const detailLoading = ref(false)
const reply = ref('')
const submitting = ref(false)
const actionError = ref<string | null>(null)

const actions = computed(() => (selected.value ? ticketActions(selected.value.status) : []))

function messageFor(err: unknown): string {
  if (!(err instanceof ApiError)) return t('auth.errors.network')
  const key = `tickets.errors.${err.code}`
  const translated = t(key)
  return translated === key ? t('tickets.errors.unknown') : translated
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const page = await ticketsApi.list({
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

async function select(ticket: TicketSummary): Promise<void> {
  detailLoading.value = true
  actionError.value = null
  reply.value = ''
  try {
    selected.value = await ticketsApi.detail(ticket.id)
  } catch (err) {
    selected.value = null
    actionError.value = messageFor(err)
  } finally {
    detailLoading.value = false
  }
}

async function sendReply(): Promise<void> {
  if (!selected.value || reply.value.trim().length < 2) return
  submitting.value = true
  actionError.value = null
  try {
    selected.value = await ticketsApi.reply(selected.value.id, reply.value.trim())
    reply.value = ''
    await load()
  } catch (err) {
    actionError.value = messageFor(err)
  } finally {
    submitting.value = false
  }
}

async function move(status: TicketAction): Promise<void> {
  if (!selected.value) return
  submitting.value = true
  actionError.value = null
  try {
    selected.value = await ticketsApi.updateStatus(selected.value.id, status)
    await load()
  } catch (err) {
    actionError.value = messageFor(err)
  } finally {
    submitting.value = false
  }
}

watch(filter, () => {
  selected.value = null
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
          <span class="hidden sm:inline">{{ t('tickets.back') }}</span>
        </RouterLink>
      </div>
    </header>

    <main id="main-content" class="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
      <section class="flex flex-col gap-2">
        <p class="text-[0.65rem] font-bold uppercase tracking-[0.2em] text-teal-700">
          {{ t('tickets.eyebrow') }}
        </p>
        <h1 class="text-2xl font-extrabold tracking-tight text-ink-950 sm:text-3xl">
          {{ t('tickets.title') }}
        </h1>
        <p class="max-w-2xl text-sm leading-7 text-ink-500">{{ t('tickets.subtitle') }}</p>
      </section>

      <div class="mt-6 flex flex-wrap items-center gap-2" role="group" :aria-label="t('tickets.filtersLabel')">
        <button
          v-for="option in TICKET_FILTERS"
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
          {{ t(`tickets.filters.${option}`) }}
        </button>
        <span class="ms-auto text-xs text-ink-400">{{ t('tickets.total', { count: total }) }}</span>
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
            <p class="text-sm font-semibold text-ink-700">{{ t('tickets.empty') }}</p>
            <p class="mt-1 text-xs text-ink-400">{{ t('tickets.emptyHint') }}</p>
          </div>

          <ul v-else class="space-y-3">
            <li v-for="ticket in items" :key="ticket.id">
              <button
                type="button"
                class="w-full rounded-2xl border bg-white p-4 text-start shadow-sm transition hover:border-teal-300"
                :class="
                  selected?.id === ticket.id ? 'border-teal-400 ring-2 ring-teal-500/15' : 'border-ink-100'
                "
                :aria-pressed="selected?.id === ticket.id"
                @click="select(ticket)"
              >
                <div class="flex items-start justify-between gap-3">
                  <span class="text-sm font-bold text-ink-900">{{ ticket.subject }}</span>
                  <span
                    class="shrink-0 rounded-full border px-2.5 py-1 text-[0.65rem] font-bold"
                    :class="ticketStatusClass(ticket.status)"
                  >
                    {{ t(ticketStatusKey(ticket.status)) }}
                  </span>
                </div>
                <p class="mt-2 text-xs text-ink-500">
                  {{ ticket.reporter_name }} · {{ t(`tickets.category.${ticket.category}`) }}
                </p>
                <p class="mt-1 text-[0.7rem] text-ink-400">{{ formatDate(ticket.created_at) }}</p>
              </button>
            </li>
          </ul>
        </section>

        <section class="lg:col-span-3">
          <div
            v-if="!selected && !detailLoading"
            class="flex h-full min-h-48 items-center justify-center rounded-[1.75rem] border border-dashed border-ink-200 bg-white p-8 text-center"
          >
            <p class="text-sm text-ink-400">{{ t('tickets.selectPrompt') }}</p>
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
                  {{ t('tickets.reporter') }}: {{ selected.reporter_name }} ·
                  {{ t(`tickets.category.${selected.category}`) }}
                </p>
              </div>
              <span
                class="rounded-full border px-3 py-1.5 text-xs font-bold"
                :class="ticketStatusClass(selected.status)"
              >
                {{ t(ticketStatusKey(selected.status)) }}
              </span>
            </div>

            <p class="mt-4 rounded-2xl bg-sand-50 p-4 text-sm leading-7 text-ink-700">
              {{ selected.description }}
            </p>

            <div v-if="selected.messages.length" class="mt-5 space-y-3">
              <h3 class="text-xs font-bold uppercase tracking-wider text-ink-400">
                {{ t('tickets.messages') }}
              </h3>
              <div
                v-for="message in selected.messages"
                :key="message.id"
                class="rounded-2xl border border-ink-100 p-3"
                :class="message.author_role === 'user' ? 'bg-white' : 'bg-teal-50/60'"
              >
                <div class="flex items-center justify-between gap-2">
                  <span class="text-xs font-bold text-ink-800">{{ message.author_name }}</span>
                  <span class="text-[0.65rem] text-ink-400">{{ formatDate(message.created_at) }}</span>
                </div>
                <p class="mt-1 text-sm leading-6 text-ink-700">{{ message.body }}</p>
              </div>
            </div>
            <p v-else class="mt-5 text-xs text-ink-400">{{ t('tickets.noMessages') }}</p>

            <p v-if="actionError" role="alert" class="mt-4 rounded-xl bg-red-50 p-3 text-xs font-semibold text-red-700">
              {{ actionError }}
            </p>

            <form class="mt-5" @submit.prevent="sendReply">
              <label for="ticket-reply" class="field-label">{{ t('tickets.replyLabel') }}</label>
              <textarea
                id="ticket-reply"
                v-model="reply"
                class="field-input min-h-24"
                maxlength="2000"
                :placeholder="t('tickets.replyPlaceholder')"
              ></textarea>
              <div class="mt-3 flex flex-wrap items-center gap-2">
                <button
                  type="submit"
                  class="btn-primary w-auto px-5 py-2.5"
                  :disabled="submitting || reply.trim().length < 2"
                >
                  {{ submitting ? t('tickets.sending') : t('tickets.replySubmit') }}
                </button>
                <button
                  v-for="action in actions"
                  :key="action"
                  type="button"
                  class="rounded-xl border border-ink-200 bg-white px-4 py-2.5 text-xs font-semibold text-ink-700 transition hover:border-teal-300 hover:text-teal-800"
                  :disabled="submitting"
                  @click="move(action)"
                >
                  {{ t(`tickets.actions.${action}`) }}
                </button>
              </div>
            </form>
          </article>
        </section>
      </div>
    </main>
  </div>
</template>
