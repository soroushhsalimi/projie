<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import BrandMark from '@/shared/components/BrandMark.vue'
import { formatDate } from '@/app/i18n'
import { useAuthStore } from '@/modules/auth/stores/auth'

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()
const signingOut = ref(false)

const initials = computed(() => {
  const name = auth.user?.full_name?.trim() ?? ''
  if (!name) return '—'
  const parts = name.split(/\s+/).slice(0, 2)
  return parts.map((part) => part.charAt(0)).join('')
})

const roleLabel = computed(() => (auth.user ? t(`dashboard.roles.${auth.user.role}`) : ''))
const statusLabel = computed(() =>
  auth.user ? t(`dashboard.statuses.${auth.user.status}`) : '',
)

async function signOut(): Promise<void> {
  signingOut.value = true
  await auth.logout()
  await router.push('/login')
  signingOut.value = false
}
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

        <div class="flex items-center gap-2">
          <div class="hidden items-center gap-2 rounded-full border border-ink-200 bg-white px-3 py-1.5 sm:flex">
            <span class="flex h-6 w-6 items-center justify-center rounded-full bg-teal-100 text-[0.65rem] font-bold text-teal-800">
              {{ initials }}
            </span>
            <span class="text-xs font-medium text-ink-700">{{ auth.displayName }}</span>
          </div>
          <button
            type="button"
            class="btn-ghost"
            :disabled="signingOut"
            @click="signOut"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 17l5-5-5-5M15 12H3" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            <span class="hidden sm:inline">
              {{ signingOut ? t('dashboard.signingOut') : t('dashboard.signOut') }}
            </span>
          </button>
        </div>
      </div>
    </header>

    <main id="main-content" class="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
      <section
        class="relative overflow-hidden rounded-[2rem] bg-ink-950 p-6 text-white shadow-card sm:p-10"
      >
        <div
          class="pointer-events-none absolute -top-24 end-[-4rem] h-72 w-72 rounded-full bg-teal-500/20 blur-3xl"
          aria-hidden="true"
        />
        <div
          class="pointer-events-none absolute inset-0 opacity-40"
          style="
            background-image:
              linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
            background-size: 44px 44px;
          "
          aria-hidden="true"
        />

        <div class="relative flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div class="flex items-center gap-4">
            <div
              class="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl border border-white/15 bg-white/10 text-xl font-extrabold text-teal-100 backdrop-blur"
            >
              {{ initials }}
            </div>
            <div>
              <p class="text-[0.7rem] font-medium tracking-wide text-teal-200/80">
                {{ t('dashboard.account') }}
              </p>
              <h1 class="mt-1 text-2xl font-extrabold tracking-tight sm:text-3xl">
                {{ t('dashboard.welcome', { name: auth.displayName }) }}
              </h1>
              <p class="mt-2 max-w-xl text-sm leading-7 text-ink-200/85">
                {{ t('dashboard.subtitle') }}
              </p>
            </div>
          </div>

          <div class="flex flex-wrap gap-2">
            <span class="rounded-full border border-teal-300/30 bg-teal-400/10 px-3 py-1.5 text-xs font-semibold text-teal-100">
              {{ roleLabel }}
            </span>
            <span class="rounded-full border border-white/15 bg-white/5 px-3 py-1.5 text-xs font-medium text-ink-100">
              {{ statusLabel }}
            </span>
          </div>
        </div>
      </section>

      <div v-if="auth.user" class="mt-6 grid gap-6 lg:grid-cols-3">
        <section class="rounded-[1.75rem] border border-ink-100 bg-white p-6 shadow-sm lg:col-span-2">
          <div class="flex items-center justify-between">
            <h2 class="text-base font-bold text-ink-950">{{ t('dashboard.account') }}</h2>
            <span class="text-[0.65rem] font-medium uppercase tracking-wider text-ink-400">
              {{ t('dashboard.memberSince') }} {{ formatDate(auth.user.created_at) }}
            </span>
          </div>

          <dl class="mt-5 grid gap-4 sm:grid-cols-2">
            <div class="rounded-2xl bg-sand-50 p-4">
              <dt class="text-[0.7rem] text-ink-400">{{ t('auth.fullName') }}</dt>
              <dd class="mt-1 text-sm font-semibold text-ink-900">{{ auth.user.full_name }}</dd>
            </div>
            <div class="rounded-2xl bg-sand-50 p-4">
              <dt class="text-[0.7rem] text-ink-400">{{ t('auth.email') }}</dt>
              <dd class="mt-1 truncate text-sm font-semibold text-ink-900" dir="ltr">
                {{ auth.user.email }}
              </dd>
            </div>
            <div class="rounded-2xl bg-sand-50 p-4">
              <dt class="text-[0.7rem] text-ink-400">{{ t('auth.phone') }}</dt>
              <dd class="mt-1 text-sm font-semibold text-ink-900" dir="ltr">
                {{ auth.user.phone || '—' }}
              </dd>
            </div>
            <div class="rounded-2xl bg-sand-50 p-4">
              <dt class="text-[0.7rem] text-ink-400">{{ t('dashboard.role') }}</dt>
              <dd class="mt-1 text-sm font-semibold text-ink-900">{{ roleLabel }}</dd>
            </div>
          </dl>
        </section>

        <section class="rounded-[1.75rem] border border-ink-100 bg-white p-6 shadow-sm">
          <div class="flex items-center gap-2">
            <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-50 text-teal-700">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M12 3l7 4v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V7l7-4Z" />
                <path d="m9 12 2 2 4-4" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <h2 class="text-sm font-bold text-ink-950">{{ t('dashboard.security') }}</h2>
          </div>
          <p class="mt-3 text-xs leading-6 text-ink-500">{{ t('dashboard.securityBody') }}</p>
        </section>

        <section
          v-if="auth.user.role !== 'user'"
          class="rounded-[1.75rem] border border-ink-100 bg-white p-6 shadow-sm lg:col-span-3"
        >
          <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div class="max-w-2xl">
              <p class="text-[0.65rem] font-bold uppercase tracking-[0.2em] text-teal-700">
                {{ t('dashboard.ticketsEyebrow') }}
              </p>
              <h2 class="mt-2 text-lg font-extrabold text-ink-950">
                {{ t('dashboard.ticketsTitle') }}
              </h2>
              <p class="mt-2 text-sm leading-7 text-ink-500">
                {{ t('dashboard.ticketsBody') }}
              </p>
            </div>
            <RouterLink
              to="/tickets"
              class="inline-flex shrink-0 items-center gap-2 self-start rounded-xl bg-teal-600 px-4 py-2.5 text-xs font-bold text-white transition hover:bg-teal-700"
            >
              {{ t('dashboard.ticketsCta') }}
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 19l-5-7 5-7M5 12h9" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </RouterLink>
          </div>
        </section>

        <section
          v-if="auth.user.role !== 'user'"
          class="rounded-[1.75rem] border border-ink-100 bg-white p-6 shadow-sm lg:col-span-3"
        >
          <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div class="max-w-2xl">
              <p class="text-[0.65rem] font-bold uppercase tracking-[0.2em] text-teal-700">
                {{ t('dashboard.complaintsEyebrow') }}
              </p>
              <h2 class="mt-2 text-lg font-extrabold text-ink-950">
                {{ t('dashboard.complaintsTitle') }}
              </h2>
              <p class="mt-2 text-sm leading-7 text-ink-500">
                {{ t('dashboard.complaintsBody') }}
              </p>
            </div>
            <RouterLink
              to="/complaints"
              class="inline-flex shrink-0 items-center gap-2 self-start rounded-xl bg-teal-600 px-4 py-2.5 text-xs font-bold text-white transition hover:bg-teal-700"
            >
              {{ t('dashboard.complaintsCta') }}
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 19l-5-7 5-7M5 12h9" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </RouterLink>
          </div>
        </section>

        <section
          v-if="auth.user.role !== 'user'"
          class="rounded-[1.75rem] border border-ink-100 bg-white p-6 shadow-sm lg:col-span-3"
        >
          <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div class="max-w-2xl">
              <p class="text-[0.65rem] font-bold uppercase tracking-[0.2em] text-teal-700">
                {{ t('dashboard.guestsEyebrow') }}
              </p>
              <h2 class="mt-2 text-lg font-extrabold text-ink-950">
                {{ t('dashboard.guestsTitle') }}
              </h2>
              <p class="mt-2 text-sm leading-7 text-ink-500">
                {{ t('dashboard.guestsBody') }}
              </p>
            </div>
            <RouterLink
              to="/guests"
              class="inline-flex shrink-0 items-center gap-2 self-start rounded-xl bg-teal-600 px-4 py-2.5 text-xs font-bold text-white transition hover:bg-teal-700"
            >
              {{ t('dashboard.guestsCta') }}
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 19l-5-7 5-7M5 12h9" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </RouterLink>
          </div>
        </section>

        <section
          v-if="auth.user.role !== 'user'"
          class="rounded-[1.75rem] border border-ink-100 bg-white p-6 shadow-sm lg:col-span-3"
        >
          <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div class="max-w-2xl">
              <p class="text-[0.65rem] font-bold uppercase tracking-[0.2em] text-teal-700">
                {{ t('dashboard.requestReviewEyebrow') }}
              </p>
              <h2 class="mt-2 text-lg font-extrabold text-ink-950">
                {{ t('dashboard.requestReviewTitle') }}
              </h2>
              <p class="mt-2 text-sm leading-7 text-ink-500">
                {{ t('dashboard.requestReviewBody') }}
              </p>
            </div>
            <RouterLink
              to="/requests/review"
              class="inline-flex shrink-0 items-center gap-2 self-start rounded-xl bg-teal-600 px-4 py-2.5 text-xs font-bold text-white transition hover:bg-teal-700"
            >
              {{ t('dashboard.requestReviewCta') }}
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 19l-5-7 5-7M5 12h9" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </RouterLink>
          </div>
        </section>

        <section
          v-if="auth.user.role === 'user'"
          class="relative overflow-hidden rounded-[1.75rem] border border-teal-200/70 bg-gradient-to-bl from-teal-50 via-white to-sand-50 p-6 shadow-sm lg:col-span-3"
        >
          <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div class="max-w-2xl">
              <p class="text-[0.65rem] font-bold uppercase tracking-[0.2em] text-teal-700">
                {{ t('dashboard.nextStep') }}
              </p>
              <h2 class="mt-2 text-lg font-extrabold text-ink-950">{{ t('dashboard.nextStepTitle') }}</h2>
              <p class="mt-2 text-sm leading-7 text-ink-500">{{ t('dashboard.nextStepBody') }}</p>
            </div>
            <RouterLink
              to="/requests"
              class="inline-flex shrink-0 items-center gap-2 self-start rounded-xl bg-teal-600 px-4 py-2.5 text-xs font-bold text-white transition hover:bg-teal-700"
            >
              {{ t('dashboard.nextStepCta') }}
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 19l-5-7 5-7M5 12h9" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </RouterLink>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>
