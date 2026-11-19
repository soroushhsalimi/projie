<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import FormField from '@/modules/auth/components/FormField.vue'

defineProps<{
  id: string
  label: string
  error?: string
  hint?: string
  autocomplete?: string
  placeholder?: string
}>()

const model = defineModel<string>({ required: true })
const { t } = useI18n()
const visible = ref(false)
</script>

<template>
  <FormField
    :id="id"
    :label="label"
    :type="visible ? 'text' : 'password'"
    :placeholder="placeholder"
    :autocomplete="autocomplete ?? 'current-password'"
    :error="error"
    :hint="hint"
    ltr
    required
    :model-value="model"
    @update:model-value="model = $event"
  >
    <template #labelAction>
      <slot name="labelAction" />
    </template>
    <template #trailing>
      <button
        type="button"
        class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-ink-400 transition hover:bg-ink-100 hover:text-ink-700"
        :aria-label="visible ? t('auth.hidePassword') : t('auth.showPassword')"
        :aria-pressed="visible"
        @click="visible = !visible"
      >
        <svg v-if="visible" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
          <path d="M3 3l18 18" stroke-linecap="round" />
          <path d="M10.6 10.6a2 2 0 0 0 2.8 2.8M9.9 5.2A10.6 10.6 0 0 1 12 5c5 0 9 4.5 9 7 0 .8-.5 1.9-1.4 3M6.1 6.7C4.2 8.1 3 10.1 3 12c0 2.5 4 7 9 7 1.5 0 2.9-.4 4.1-1" stroke-linecap="round" />
        </svg>
        <svg v-else class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
          <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z" />
          <circle cx="12" cy="12" r="2.6" />
        </svg>
      </button>
    </template>
  </FormField>
</template>
