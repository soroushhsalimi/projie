<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { ApiError } from '@/api/client'
import type { GuestVisit } from '@/api/types'
import { guestsApi } from '@/modules/guests/api'
import {
  GUEST_FILTERS,
  formatDateTime,
  guestActions,
  guestStatusClass,
  guestStatusKey,
  isWindowOrdered,
  toIsoUtc,
  type GuestAction,
  type GuestFilter,
} from '@/modules/guests/format'
import BrandMark from '@/shared/components/BrandMark.vue'

const { t } = useI18n()

const filter = ref<GuestFilter>('expected')
const items = ref<GuestVisit[]>([])
const total = ref(0)
const loading = ref(true)
const error = ref<string | null>(null)

const selected = ref<GuestVisit | null>(null)
const detailLoading = ref(false)
const actionError = ref<string | null>(null)
const submitting = ref(false)
const notice = ref<string | null>(null)

const guestName = ref('')
const hostEmail = ref('')
const purpose = ref('')
const allowedFrom = ref('')
const allowedUntil = ref('')
const formError = ref<string | null>(null)
const saving = ref(false)

const actions = computed(() => (selected.value ? guestActions(selected.value.status) : []))
const windowOrdered = computed(() => isWindowOrdered(allowedFrom.value, allowedUntil.value))
const canRegister = computed(
  () => guestName.value.trim().length >= 2 && hostEmail.value.trim().length > 0 && windowOrdered.value,
)

function messageFor(err: unknown): string {
  if (!(err instanceof ApiError)) return t('auth.errors.network')
  const key = `guests.errors.${err.code}`
  const translated = t(key)
  return translated === key ? t('guests.errors.unknown') : translated
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const page = await guestsApi.list({
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

async function select(visit: GuestVisit): Promise<void> {
  detailLoading.value = true
  actionError.value = null
  notice.value = null
  try {
    selected.value = await guestsApi.detail(visit.id)
  } catch (err) {
    selected.value = null
    actionError.value = messageFor(err)
  } finally {
    detailLoading.value = false
  }
}

async function move(action: GuestAction): Promise<void> {
  if (!selected.value) return
  submitting.value = true
  actionError.value = null
  notice.value = null
  try {
    selected.value =
      action === 'check_in'
        ? await guestsApi.checkIn(selected.value.id)
        : await guestsApi.checkOut(selected.value.id)
    notice.value = t(`guests.done.${action}`)
    await load()
  } catch (err) {
    actionError.value = messageFor(err)
  } finally {
    submitting.value = false
  }
}

async function register(): Promise<void> {
  if (!canRegister.value) {
    formError.value = t('guests.form.invalidWindow')
    return
  }
  saving.value = true
  formError.value = null
  try {
    const visit = await guestsApi.register({
      guest_name: guestName.value.trim(),
      host_email: hostEmail.value.trim(),
      purpose: purpose.value.trim() || null,
      allowed_from: toIsoUtc(allowedFrom.value),
      allowed_until: toIsoUtc(allowedUntil.value),
    })
    selected.value = visit
    guestName.value = ''
    hostEmail.value = ''
    purpose.value = ''
    allowedFrom.value = ''
    allowedUntil.value = ''
    notice.value = t('guests.done.registered')
    await load()
  } catch (err) {
    formError.value = messageFor(err)
  } finally {
    saving.value = false
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
          <span class="hidden sm:inline">{{ t('guests.back') }}</span>
        </RouterLink>
      </div>
    </header>

    <main id="main-content" class="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
      <section class="flex flex-col gap-2">
        <p class="text-[0.65rem] font-bold uppercase tracking-[0.2em] text-teal-700">
          {{ t('guests.eyebrow') }}
        </p>
        <h1 class="text-2xl font-extrabold tracking-tight text-ink-950 sm:text-3xl">
          {{ t('guests.title') }}
        </h1>
        <p class="max-w-2xl text-sm leading-7 text-ink-500">{{ t('guests.subtitle') }}</p>
      </section>

      <div class="mt-6 flex flex-wrap items-center gap-2" role="group" :aria-label="t('guests.filtersLabel')">
        <button
          v-for="option in GUEST_FILTERS"
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
          {{ t(`guests.filters.${option}`) }}
        </button>
        <span class="ms-auto text-xs text-ink-400">{{ t('guests.total', { count: total }) }}</span>
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
            <p class="text-sm font-semibold text-ink-700">{{ t('guests.empty') }}</p>
            <p class="mt-1 text-xs text-ink-400">{{ t('guests.emptyHint') }}</p>
          </div>

          <ul v-else class="space-y-3">
            <li v-for="visit in items" :key="visit.id">
              <button
                type="button"
                class="w-full rounded-2xl border bg-white p-4 text-start shadow-sm transition hover:border-teal-300"
                :class="
                  selected?.id === visit.id
                    ? 'border-teal-400 ring-2 ring-teal-500/15'
                    : 'border-ink-100'
                "
                :aria-pressed="selected?.id === visit.id"
                @click="select(visit)"
              >
                <div class="flex items-start justify-between gap-3">
                  <span class="text-sm font-bold text-ink-900">{{ visit.guest_name }}</span>
                  <span
                    class="shrink-0 rounded-full border px-2.5 py-1 text-[0.65rem] font-bold"
                    :class="guestStatusClass(visit.status)"
                  >
                    {{ t(guestStatusKey(visit.status)) }}
                  </span>
                </div>
                <p class="mt-2 text-xs text-ink-500">{{ t('guests.host') }}: {{ visit.host_name }}</p>
                <p class="mt-1 text-[0.7rem] text-ink-400">
                  {{ formatDateTime(visit.allowed_from) }} — {{ formatDateTime(visit.allowed_until) }}
                </p>
                <p
                  v-if="visit.overdue"
                  class="mt-2 inline-block rounded-full border border-red-200 bg-red-50 px-2 py-0.5 text-[0.65rem] font-bold text-red-700"
                >
                  {{ t('guests.overdue') }}
                </p>
              </button>
            </li>
          </ul>
        </section>

        <section class="lg:col-span-3">
          <div
            v-if="!selected && !detailLoading"
            class="flex h-full min-h-40 items-center justify-center rounded-[1.75rem] border border-dashed border-ink-200 bg-white p-8 text-center"
          >
            <p class="text-sm text-ink-400">{{ t('guests.selectPrompt') }}</p>
          </div>

          <div v-else-if="detailLoading" class="skeleton h-72 w-full"></div>

          <article
            v-else-if="selected"
            class="rounded-[1.75rem] border border-ink-100 bg-white p-6 shadow-sm"
          >
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 class="text-lg font-extrabold text-ink-950">{{ selected.guest_name }}</h2>
                <p class="mt-1 text-xs text-ink-500">
                  {{ t('guests.host') }}: {{ selected.host_name }}
                </p>
              </div>
              <div class="flex flex-wrap items-center gap-2">
                <span
                  v-if="selected.overdue"
                  class="rounded-full border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-bold text-red-700"
                >
                  {{ t('guests.overdue') }}
                </span>
                <span
                  class="rounded-full border px-3 py-1.5 text-xs font-bold"
                  :class="guestStatusClass(selected.status)"
                >
                  {{ t(guestStatusKey(selected.status)) }}
                </span>
              </div>
            </div>

            <dl class="mt-4 grid gap-3 sm:grid-cols-2">
              <div class="rounded-2xl bg-sand-50 p-4">
                <dt class="text-[0.7rem] text-ink-400">{{ t('guests.allowedWindow') }}</dt>
                <dd class="mt-1 text-xs font-semibold text-ink-900">
                  {{ formatDateTime(selected.allowed_from) }} —
                  {{ formatDateTime(selected.allowed_until) }}
                </dd>
              </div>
              <div class="rounded-2xl bg-sand-50 p-4">
                <dt class="text-[0.7rem] text-ink-400">{{ t('guests.actualTimes') }}</dt>
                <dd class="mt-1 text-xs font-semibold text-ink-900">
                  {{ selected.checked_in_at ? formatDateTime(selected.checked_in_at) : t('guests.notArrived') }}
                  ·
                  {{ selected.checked_out_at ? formatDateTime(selected.checked_out_at) : t('guests.stillInside') }}
                </dd>
              </div>
            </dl>

            <p v-if="selected.purpose" class="mt-4 rounded-2xl bg-sand-50 p-4 text-sm leading-7 text-ink-700">
              {{ selected.purpose }}
            </p>

            <p v-if="actionError" role="alert" class="mt-4 rounded-xl bg-red-50 p-3 text-xs font-semibold text-red-700">
              {{ actionError }}
            </p>
            <p v-if="notice" role="status" class="mt-4 rounded-xl bg-teal-50 p-3 text-xs font-semibold text-teal-800">
              {{ notice }}
            </p>

            <div class="mt-5 flex flex-wrap items-center gap-2">
              <button
                v-for="action in actions"
                :key="action"
                type="button"
                class="btn-primary w-auto px-5 py-2.5"
                :disabled="submitting"
                @click="move(action)"
              >
                {{ submitting ? t('guests.saving') : t(`guests.actions.${action}`) }}
              </button>
            </div>
          </article>

          <form
            class="mt-6 rounded-[1.75rem] border border-ink-100 bg-white p-6 shadow-sm"
            @submit.prevent="register"
          >
            <h2 class="text-base font-extrabold text-ink-950">{{ t('guests.form.title') }}</h2>
            <p class="mt-1 text-xs text-ink-500">{{ t('guests.form.hint') }}</p>

            <div class="mt-4 grid gap-3 sm:grid-cols-2">
              <div>
                <label for="guest-name" class="field-label">{{ t('guests.form.guestName') }}</label>
                <input id="guest-name" v-model="guestName" class="field-input" maxlength="120" />
              </div>
              <div>
                <label for="guest-host" class="field-label">{{ t('guests.form.hostEmail') }}</label>
                <input
                  id="guest-host"
                  v-model="hostEmail"
                  class="field-input"
                  dir="ltr"
                  type="email"
                  :placeholder="t('guests.form.hostPlaceholder')"
                />
              </div>
              <div class="sm:col-span-2">
                <label for="guest-purpose" class="field-label">{{ t('guests.form.purpose') }}</label>
                <input id="guest-purpose" v-model="purpose" class="field-input" maxlength="200" />
              </div>
              <div>
                <label for="guest-from" class="field-label">{{ t('guests.form.allowedFrom') }}</label>
                <input id="guest-from" v-model="allowedFrom" class="field-input" type="datetime-local" />
              </div>
              <div>
                <label for="guest-until" class="field-label">{{ t('guests.form.allowedUntil') }}</label>
                <input id="guest-until" v-model="allowedUntil" class="field-input" type="datetime-local" />
              </div>
            </div>

            <p v-if="formError" role="alert" class="mt-3 rounded-xl bg-red-50 p-3 text-xs font-semibold text-red-700">
              {{ formError }}
            </p>

            <button type="submit" class="btn-primary mt-4 w-auto px-5 py-2.5" :disabled="saving || !canRegister">
              {{ saving ? t('guests.saving') : t('guests.form.submit') }}
            </button>
          </form>
        </section>
      </div>
    </main>
  </div>
</template>
