<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { ApiError } from '@/api/client'
import AlertBanner from '@/modules/auth/components/AlertBanner.vue'
import AuthShell from '@/modules/auth/components/AuthShell.vue'
import FormField from '@/modules/auth/components/FormField.vue'
import PasswordField from '@/modules/auth/components/PasswordField.vue'
import { useAuthStore } from '@/modules/auth/stores/auth'
import { fieldErrors, loginSchema } from '@/modules/auth/validation'

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({ email: '', password: '' })
const errors = ref<Record<string, string>>({})
const formError = ref('')
const isDev = import.meta.env.DEV

const redirectTarget = computed(() => {  const value = route.query.redirect
  if (typeof value === 'string' && value.startsWith('/') && !value.startsWith('//')) return value
  return '/dashboard'
})

function focusFirstError(): void {
  const first = Object.keys(errors.value)[0]
  if (first) document.getElementById(first)?.focus()
}

function translateFieldErrors(raw: Record<string, string>): Record<string, string> {
  return Object.fromEntries(
    Object.entries(raw).map(([field, message]) => [field, t(message)]),
  )
}

function handleApiError(error: unknown): void {
  if (error instanceof ApiError) {
    if (error.code === 'invalid_credentials') {
      formError.value = t('auth.errors.invalid_credentials')
      return
    }
    if (error.code === 'validation_error') {
      const fields: Record<string, string> = {}
      for (const field of Object.keys(error.fields)) {
        fields[field] = t('validation.server')
      }
      errors.value = fields
      formError.value = t('auth.errors.validation_error')
      focusFirstError()
      return
    }
    formError.value = t('auth.errors.unknown')
    return
  }
  formError.value = t('auth.errors.network')
}

async function submit(): Promise<void> {
  formError.value = ''
  const parsed = loginSchema.safeParse(form)
  if (!parsed.success) {
    errors.value = translateFieldErrors(fieldErrors(parsed.error))
    focusFirstError()
    return
  }
  errors.value = {}

  try {
    await auth.login({ email: form.email.trim(), password: form.password })
    await router.push(redirectTarget.value)
  } catch (error) {
    handleApiError(error)
  }
}
</script>

<template>
  <AuthShell mode="login">
    <div class="auth-card">
      <header class="mb-7">
        <p class="text-[0.65rem] font-bold uppercase tracking-[0.28em] text-teal-700">SARA</p>
        <h1 class="mt-2 text-[1.75rem] font-extrabold tracking-tight text-ink-950">
          {{ t('auth.loginTitle') }}
        </h1>
        <p class="mt-2 text-sm leading-6 text-ink-500">{{ t('auth.loginSubtitle') }}</p>
      </header>

      <AlertBanner v-if="formError" class="mb-5" :message="formError" />

      <form class="space-y-5" novalidate @submit.prevent="submit">
        <FormField
          id="email"
          v-model="form.email"
          :label="t('auth.email')"
          :placeholder="t('auth.emailPlaceholder')"
          :error="errors.email"
          type="email"
          autocomplete="email"
          inputmode="email"
          ltr
          required
        >
          <template #leading>
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
              <rect x="3" y="5" width="18" height="14" rx="3" />
              <path d="m4 7 8 6 8-6" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </template>
        </FormField>

        <PasswordField
          id="password"
          v-model="form.password"
          :label="t('auth.password')"
          :placeholder="t('auth.passwordPlaceholder')"
          :error="errors.password"
          autocomplete="current-password"
        />

        <div class="flex items-center justify-between gap-3">
          <p class="flex items-center gap-1.5 text-[0.7rem] text-ink-400">
            <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <rect x="4" y="10" width="16" height="10" rx="2.5" />
              <path d="M8 10V7a4 4 0 0 1 8 0v3" stroke-linecap="round" />
            </svg>
            {{ t('auth.secureNote') }}
          </p>
          <button
            type="button"
            class="text-[0.7rem] font-medium text-ink-400 transition hover:text-teal-700"
            :title="t('common.soon')"
            aria-disabled="true"
          >
            {{ t('auth.forgot') }}
          </button>
        </div>

        <button type="submit" class="btn-primary" :disabled="auth.submitting">
          <svg
            v-if="auth.submitting"
            class="h-4 w-4 animate-spin"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-opacity="0.25" stroke-width="3" />
            <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" stroke-width="3" stroke-linecap="round" />
          </svg>
          <span>{{ auth.submitting ? t('auth.loggingIn') : t('auth.login') }}</span>
          <svg
            v-if="!auth.submitting"
            class="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            aria-hidden="true"
          >
            <path d="M19 12H5M11 18l-6-6 6-6" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </form>

      <p class="mt-6 text-center text-sm text-ink-500">
        {{ t('auth.noAccount') }}
        <RouterLink to="/register" class="link">{{ t('auth.registerLink') }}</RouterLink>
      </p>

      <div
        v-if="isDev"
        class="mt-6 rounded-2xl border border-dashed border-ink-200 bg-sand-50/70 p-3.5"
      >
        <div class="flex items-center justify-between gap-2">
          <p class="text-[0.7rem] font-semibold text-ink-600">{{ t('auth.demo.title') }}</p>
          <span class="rounded-full bg-ink-100 px-2 py-0.5 text-[0.6rem] text-ink-500">DEV</span>
        </div>
        <p class="mt-1 font-mono text-[0.68rem] leading-5 text-ink-500" dir="ltr">
          {{ t('auth.demo.hint') }}
        </p>
      </div>
    </div>
  </AuthShell>
</template>
