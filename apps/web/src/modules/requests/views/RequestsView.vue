<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { ApiError } from '@/api/client'
import type { AccommodationRequest, RequestCreatePayload, RoomType } from '@/api/types'
import { formatDate } from '@/app/i18n'
import { requestsApi } from '@/modules/requests/api'
import {
  ROOM_TYPES,
  isActiveRequest,
  requestStatusClass,
  requestStatusKey,
  roomTypeKey,
} from '@/modules/requests/format'
import BrandMark from '@/shared/components/BrandMark.vue'

const { t } = useI18n()

const items = ref<AccommodationRequest[]>([])
const total = ref(0)
const loading = ref(true)
const error = ref<string | null>(null)
const success = ref<string | null>(null)

const submitting = ref(false)
const withdrawingId = ref<string | null>(null)
const actionError = ref<string | null>(null)

const dormitory = ref('')
const roomType = ref<RoomType>('double')
const moveIn = ref('')
const duration = ref(6)
const note = ref('')
const fieldErrors = ref<Record<string, string>>({})

const hasActiveRequest = computed(() => items.value.some((item) => isActiveRequest(item.status)))

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
    const page = await requestsApi.list()
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

function validate(): boolean {
  const errors: Record<string, string> = {}
  if (dormitory.value.trim().length < 2) errors.dormitory = t('requests.fields.dormitoryError')
  if (!moveIn.value) errors.moveIn = t('requests.fields.moveInError')
  const months = Number(duration.value)
  if (!Number.isInteger(months) || months < 1 || months > 24) {
    errors.duration = t('requests.fields.durationError')
  }
  if (note.value.length > 1000) errors.note = t('requests.fields.noteError')
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

function resetForm(): void {
  dormitory.value = ''
  roomType.value = 'double'
  moveIn.value = ''
  duration.value = 6
  note.value = ''
  fieldErrors.value = {}
}

async function submit(): Promise<void> {
  success.value = null
  actionError.value = null
  if (!validate()) return
  submitting.value = true
  const payload: RequestCreatePayload = {
    dormitory_name: dormitory.value.trim(),
    room_type: roomType.value,
    desired_move_in: moveIn.value,
    duration_months: Number(duration.value),
    note: note.value.trim() || null,
  }
  try {
    await requestsApi.create(payload)
    resetForm()
    success.value = t('requests.form.success')
    await load()
  } catch (err) {
    if (err instanceof ApiError) {
      for (const [field, message] of Object.entries(err.fields)) {
        fieldErrors.value[field] = message
      }
    }
    actionError.value = messageFor(err)
  } finally {
    submitting.value = false
  }
}

async function withdraw(request: AccommodationRequest): Promise<void> {
  actionError.value = null
  success.value = null
  withdrawingId.value = request.id
  try {
    await requestsApi.withdraw(request.id)
    success.value = t('requests.form.withdrawn')
    await load()
  } catch (err) {
    actionError.value = messageFor(err)
  } finally {
    withdrawingId.value = null
  }
}

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
          <span class="hidden sm:inline">{{ t('requests.back') }}</span>
        </RouterLink>
      </div>
    </header>

    <main id="main-content" class="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
      <section class="flex flex-col gap-2">
        <p class="text-[0.65rem] font-bold uppercase tracking-[0.2em] text-teal-700">
          {{ t('requests.eyebrow') }}
        </p>
        <h1 class="text-2xl font-extrabold tracking-tight text-ink-950 sm:text-3xl">
          {{ t('requests.title') }}
        </h1>
        <p class="max-w-2xl text-sm leading-7 text-ink-500">{{ t('requests.subtitle') }}</p>
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

      <div class="mt-6 grid gap-6 lg:grid-cols-5">
        <section class="rounded-[1.75rem] border border-ink-100 bg-white p-6 shadow-sm lg:col-span-2">
          <h2 class="text-base font-bold text-ink-950">{{ t('requests.form.title') }}</h2>
          <p class="mt-2 text-xs leading-6 text-ink-500">{{ t('requests.form.hint') }}</p>

          <p
            v-if="hasActiveRequest"
            class="mt-4 rounded-xl bg-gold-400/15 p-3 text-xs font-semibold text-ink-700"
          >
            {{ t('requests.form.activeNotice') }}
          </p>

          <form class="mt-5 space-y-4" novalidate @submit.prevent="submit">
            <div>
              <label for="request-dormitory" class="field-label">
                {{ t('requests.form.dormitory') }}
              </label>
              <input
                id="request-dormitory"
                v-model="dormitory"
                type="text"
                maxlength="120"
                class="field-input"
                :aria-invalid="Boolean(fieldErrors.dormitory)"
                :placeholder="t('requests.form.dormitoryPlaceholder')"
              />
              <p v-if="fieldErrors.dormitory" class="mt-1 text-xs font-medium text-red-600">
                {{ fieldErrors.dormitory }}
              </p>
            </div>

            <div>
              <label for="request-room-type" class="field-label">
                {{ t('requests.form.roomType') }}
              </label>
              <select id="request-room-type" v-model="roomType" class="field-input">
                <option v-for="option in ROOM_TYPES" :key="option" :value="option">
                  {{ t(roomTypeKey(option)) }}
                </option>
              </select>
            </div>

            <div class="grid gap-4 sm:grid-cols-2">
              <div>
                <label for="request-move-in" class="field-label">
                  {{ t('requests.form.moveIn') }}
                </label>
                <input
                  id="request-move-in"
                  v-model="moveIn"
                  type="date"
                  class="field-input"
                  :aria-invalid="Boolean(fieldErrors.moveIn)"
                />
                <p v-if="fieldErrors.moveIn" class="mt-1 text-xs font-medium text-red-600">
                  {{ fieldErrors.moveIn }}
                </p>
              </div>
              <div>
                <label for="request-duration" class="field-label">
                  {{ t('requests.form.duration') }}
                </label>
                <input
                  id="request-duration"
                  v-model.number="duration"
                  type="number"
                  min="1"
                  max="24"
                  class="field-input"
                  :aria-invalid="Boolean(fieldErrors.duration)"
                />
                <p v-if="fieldErrors.duration" class="mt-1 text-xs font-medium text-red-600">
                  {{ fieldErrors.duration }}
                </p>
              </div>
            </div>

            <div>
              <label for="request-note" class="field-label">
                {{ t('requests.form.note') }}
              </label>
              <textarea
                id="request-note"
                v-model="note"
                maxlength="1000"
                class="field-input min-h-24"
                :placeholder="t('requests.form.notePlaceholder')"
              ></textarea>
              <p v-if="fieldErrors.note" class="mt-1 text-xs font-medium text-red-600">
                {{ fieldErrors.note }}
              </p>
            </div>

            <button type="submit" class="btn-primary" :disabled="submitting">
              {{ submitting ? t('requests.form.submitting') : t('requests.form.submit') }}
            </button>
          </form>
        </section>

        <section class="lg:col-span-3" :aria-busy="loading">
          <div class="flex items-center justify-between">
            <h2 class="text-base font-bold text-ink-950">{{ t('requests.list.title') }}</h2>
            <span class="text-xs text-ink-400">{{ t('requests.list.total', { count: total }) }}</span>
          </div>

          <div v-if="loading" class="mt-4 space-y-3">
            <div v-for="index in 2" :key="index" class="skeleton h-24 w-full"></div>
          </div>

          <div v-else-if="error" class="mt-4 rounded-2xl border border-red-200 bg-red-50/60 p-5">
            <p class="text-sm font-semibold text-red-700">{{ error }}</p>
            <button type="button" class="btn-primary mt-4" @click="load">
              {{ t('common.retry') }}
            </button>
          </div>

          <div
            v-else-if="items.length === 0"
            class="mt-4 rounded-2xl border border-dashed border-ink-200 bg-white p-8 text-center"
          >
            <p class="text-sm font-semibold text-ink-700">{{ t('requests.list.empty') }}</p>
            <p class="mt-1 text-xs text-ink-400">{{ t('requests.list.emptyHint') }}</p>
          </div>

          <ul v-else class="mt-4 space-y-3">
            <li
              v-for="request in items"
              :key="request.id"
              class="rounded-2xl border border-ink-100 bg-white p-5 shadow-sm"
            >
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p class="text-sm font-bold text-ink-900">{{ request.dormitory_name }}</p>
                  <p class="mt-1 text-xs text-ink-500">
                    {{ t(roomTypeKey(request.room_type)) }} ·
                    {{ t('requests.list.months', { count: request.duration_months }) }} ·
                    {{ formatDate(request.desired_move_in) }}
                  </p>
                </div>
                <span
                  class="rounded-full border px-2.5 py-1 text-[0.65rem] font-bold"
                  :class="requestStatusClass(request.status)"
                >
                  {{ t(requestStatusKey(request.status)) }}
                </span>
              </div>

              <p v-if="request.note" class="mt-3 text-xs leading-6 text-ink-600">
                {{ request.note }}
              </p>

              <div class="mt-4 flex items-center justify-between gap-3">
                <span class="text-[0.7rem] text-ink-400">
                  {{ t('requests.list.submittedOn', { date: formatDate(request.created_at) }) }}
                </span>
                <button
                  v-if="isActiveRequest(request.status)"
                  type="button"
                  class="rounded-xl border border-ink-200 bg-white px-3 py-2 text-xs font-semibold text-ink-700 transition hover:border-red-300 hover:text-red-700"
                  :disabled="withdrawingId === request.id"
                  @click="withdraw(request)"
                >
                  {{ withdrawingId === request.id ? t('requests.list.withdrawing') : t('requests.list.withdraw') }}
                </button>
              </div>
            </li>
          </ul>
        </section>
      </div>
    </main>
  </div>
</template>
