<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { ApiError } from '@/api/client'
import AlertBanner from '@/modules/auth/components/AlertBanner.vue'
import AuthShell from '@/modules/auth/components/AuthShell.vue'
import FormField from '@/modules/auth/components/FormField.vue'
import PasswordField from '@/modules/auth/components/PasswordField.vue'
import PasswordStrength from '@/modules/auth/components/PasswordStrength.vue'
import { useAuthStore } from '@/modules/auth/stores/auth'
import { fieldErrors, registerSchema } from '@/modules/auth/validation'

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()

const form = reactive({
  full_name: '',
  national_id: '',
  phone: '',
  email: '',
  address: '',
  password: '',
  confirmPassword: '',
  acceptTerms: false,
})

const errors = ref<Record<string, string>>({})
const formError = ref('')
const emailTaken = ref(false)

function focusFirstError(): void {
  const first = Object.keys(errors.value)[0]
  if (first) document.getElementById(first)?.focus()
}

function translateFieldErrors(raw: Record<string, string>): Record<string, string> {
  return Object.fromEntries(Object.entries(raw).map(([field, message]) => [field, t(message)]))
}

function handleApiError(error: unknown): void {
  if (error instanceof ApiError) {
    if (error.code === 'email_already_registered') {
      emailTaken.value = true
      errors.value = { email: t('auth.errors.email_already_registered') }
      formError.value = t('auth.errors.email_already_registered')
      document.getElementById('email')?.focus()
      return
    }
    if (error.code === 'national_id_already_registered') {
      errors.value = {
        national_id: t('auth.errors.national_id_already_registered'),
      }
      formError.value = t('auth.errors.national_id_already_registered')
      document.getElementById('national_id')?.focus()
      return
    }
    if (error.code === 'validation_error') {
      const translated: Record<string, string> = {}
      for (const field of Object.keys(error.fields)) {
        translated[field] = t('validation.server')
      }
      errors.value = translated
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
  emailTaken.value = false

  const parsed = registerSchema.safeParse(form)
  if (!parsed.success) {
    errors.value = translateFieldErrors(fieldErrors(parsed.error))
    focusFirstError()
    return
  }
  errors.value = {}

  try {
    await auth.register({
      full_name: parsed.data.full_name,
      email: parsed.data.email,
      national_id: parsed.data.national_id,
      phone: parsed.data.phone,
      address: parsed.data.address,
      password: parsed.data.password,
    })
    await router.push('/dashboard')
  } catch (error) {
    handleApiError(error)
  }
}
</script>

<template>
  <AuthShell mode="register">
    <div class="auth-card">
      <header class="mb-6">
        <p class="text-[0.65rem] font-bold uppercase tracking-[0.28em] text-teal-700">SARA</p>
        <h1 class="mt-2 text-[1.75rem] font-extrabold tracking-tight text-ink-950">
          {{ t('auth.registerTitle') }}
        </h1>
        <p class="mt-2 text-sm leading-6 text-ink-500">{{ t('auth.registerSubtitle') }}</p>
      </header>

      <AlertBanner v-if="formError" class="mb-5" :message="formError">
        <span>{{ formError }}</span>
        <RouterLink v-if="emailTaken" to="/login" class="ms-1 font-bold underline underline-offset-4">
          {{ t('auth.loginLink') }}
        </RouterLink>
      </AlertBanner>

      <form class="space-y-4" novalidate @submit.prevent="submit">
        <FormField
          id="full_name"
          v-model="form.full_name"
          :label="t('auth.fullName')"
          :placeholder="t('auth.fullNamePlaceholder')"
          :error="errors.full_name"
          autocomplete="name"
          required
        />

        <FormField
          id="email"
          v-model="form.email"
          :label="t('auth.email')"
          :placeholder="t('auth.emailPlaceholder')"
          :error="errors.email"
          type="email"
          inputmode="email"
          autocomplete="email"
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

        <FormField
          id="national_id"
          v-model="form.national_id"
          :label="t('auth.nationalId')"
          :placeholder="t('auth.nationalIdPlaceholder')"
          :error="errors.national_id"
          inputmode="numeric"
          ltr
          required
        />

        <FormField
          id="phone"
          v-model="form.phone"
          :label="t('auth.phone')"
          :placeholder="t('auth.phonePlaceholder')"
          :error="errors.phone"
          type="tel"
          inputmode="tel"
          autocomplete="tel"
          ltr
          required
        />

        <div>
          <label for="address" class="field-label">
            <span>
              {{ t('auth.address') }}
              <span class="text-red-500" aria-hidden="true">*</span>
            </span>
          </label>
          <textarea
            id="address"
            v-model="form.address"
            rows="2"
            maxlength="500"
            required
            class="field-input min-h-20"
            :placeholder="t('auth.addressPlaceholder')"
            :aria-invalid="Boolean(errors.address)"
            :aria-describedby="errors.address ? 'address-error' : undefined"
          ></textarea>
          <p v-if="errors.address" id="address-error" class="field-error" aria-live="polite">
            {{ errors.address }}
          </p>
        </div>

        <div>
          <PasswordField
            id="password"
            v-model="form.password"
            :label="t('auth.password')"
            :placeholder="t('auth.passwordPlaceholder')"
            :error="errors.password"
            autocomplete="new-password"
          />
          <PasswordStrength :password="form.password" :email="form.email" />
        </div>

        <PasswordField
          id="confirmPassword"
          v-model="form.confirmPassword"
          :label="t('auth.confirmPassword')"
          :placeholder="t('auth.confirmPasswordPlaceholder')"
          :error="errors.confirmPassword"
          autocomplete="new-password"
        />

        <div>
          <label class="flex cursor-pointer items-start gap-2.5 text-xs leading-6 text-ink-600">
            <input
              v-model="form.acceptTerms"
              type="checkbox"
              class="mt-1 h-4 w-4 shrink-0 rounded border-ink-300 accent-teal-600"
              :aria-invalid="Boolean(errors.acceptTerms)"
              :aria-describedby="errors.acceptTerms ? 'terms-error' : undefined"
            />
            <span>
              {{ t('auth.terms') }}
              <a href="#" class="font-medium text-teal-700 underline underline-offset-4">
                {{ t('footer.terms') }}
              </a>
            </span>
          </label>
          <p v-if="errors.acceptTerms" id="terms-error" class="field-error" aria-live="polite">
            {{ errors.acceptTerms }}
          </p>
        </div>

        <button type="submit" class="btn-primary !mt-5" :disabled="auth.submitting">
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
          <span>{{ auth.submitting ? t('auth.registering') : t('auth.register') }}</span>
        </button>
      </form>

      <p class="mt-6 text-center text-sm text-ink-500">
        {{ t('auth.haveAccount') }}
        <RouterLink to="/login" class="link">{{ t('auth.loginLink') }}</RouterLink>
      </p>

      <p class="mt-3 flex items-center justify-center gap-1.5 text-[0.68rem] text-ink-400">
        <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <rect x="4" y="10" width="16" height="10" rx="2.5" />
          <path d="M8 10V7a4 4 0 0 1 8 0v3" stroke-linecap="round" />
        </svg>
        {{ t('auth.secureNote') }}
      </p>
    </div>
  </AuthShell>
</template>
