<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { passwordStrength } from '@/modules/auth/validation'

const props = defineProps<{ password: string; email?: string }>()
const { t } = useI18n()

const COMMON = new Set([
  'password',
  'password1',
  'password123',
  '1234567890',
  'qwertyuiop',
  '1111111111',
  'iloveyou',
  'admin12345',
  'letmein123',
  'welcome123',
])

const strength = computed(() => passwordStrength(props.password))
const score = computed(() => (strength.value === 'strong' ? 3 : strength.value === 'medium' ? 2 : 1))
const label = computed(() => t(`auth.strength.${strength.value}`))

const checks = computed(() => {
  const local = (props.email ?? '').split('@')[0]?.toLowerCase() ?? ''
  return {
    length: props.password.length >= 10,
    uncommon: props.password.length > 0 && !COMMON.has(props.password.toLowerCase()),
    email: local.length < 3 || !props.password.toLowerCase().includes(local),
  }
})
</script>

<template>
  <div v-if="password" class="mt-3 space-y-3">
    <div class="flex items-center gap-3">
      <div class="flex flex-1 gap-1" aria-hidden="true">
        <span
          v-for="segment in 3"
          :key="segment"
          class="h-1.5 flex-1 rounded-full transition-colors duration-300"
          :class="
            segment <= score
              ? strength === 'strong'
                ? 'bg-teal-500'
                : strength === 'medium'
                  ? 'bg-gold-400'
                  : 'bg-red-400'
              : 'bg-ink-100'
          "
        />
      </div>
      <span class="text-[0.7rem] font-medium text-ink-500">
        {{ t('auth.strength.label') }}: {{ label }}
      </span>
    </div>

    <ul class="grid gap-1.5 text-[0.7rem] sm:grid-cols-3" role="list">
      <li
        v-for="(passed, key) in checks"
        :key="key"
        class="flex items-center gap-1.5"
        :class="passed ? 'text-teal-700' : 'text-ink-400'"
      >
        <svg v-if="passed" class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4">
          <path d="m5 12 4 4L19 6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <span v-else class="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />
        {{ t(`auth.hints.${key}`) }}
      </li>
    </ul>
  </div>
</template>
