<script setup lang="ts">
import { computed, useSlots } from 'vue'

const props = withDefaults(
  defineProps<{
    id: string
    label: string
    type?: string
    placeholder?: string
    autocomplete?: string
    error?: string
    hint?: string
    required?: boolean
    disabled?: boolean
    ltr?: boolean
    inputmode?: 'text' | 'email' | 'tel' | 'numeric'
  }>(),
  {
    type: 'text',
    placeholder: '',
    autocomplete: 'off',
    error: '',
    hint: '',
    required: false,
    disabled: false,
    ltr: false,
    inputmode: 'text',
  },
)

const model = defineModel<string>({ required: true })
const slots = useSlots()

const hasLeading = computed(() => Boolean(slots.leading))
const hasTrailing = computed(() => Boolean(slots.trailing))
const describedBy = computed(() => {
  if (props.error) return `${props.id}-error`
  if (props.hint) return `${props.id}-hint`
  return undefined
})
</script>

<template>
  <div>
    <label :for="id" class="field-label">
      <span>
        {{ label }}
        <span v-if="required" class="text-red-500" aria-hidden="true">*</span>
      </span>
      <slot name="labelAction" />
    </label>

    <div class="relative">
      <span
        v-if="hasLeading"
        class="pointer-events-none absolute inset-y-0 start-3.5 flex items-center text-ink-300"
        aria-hidden="true"
      >
        <slot name="leading" />
      </span>

      <input
        :id="id"
        v-model="model"
        :type="type"
        :placeholder="placeholder"
        :autocomplete="autocomplete"
        :disabled="disabled"
        :required="required"
        :inputmode="inputmode"
        :dir="ltr ? 'ltr' : undefined"
        :aria-invalid="Boolean(error)"
        :aria-describedby="describedBy"
        class="field-input"
        :class="{
          'field-input-error': Boolean(error),
          'ps-11': hasLeading,
          'pe-11': hasTrailing,
          'text-left': ltr,
        }"
      />

      <span
        v-if="hasTrailing"
        class="absolute inset-y-0 end-2 flex items-center text-ink-400"
      >
        <slot name="trailing" />
      </span>
    </div>

    <p v-if="error" :id="`${id}-error`" class="field-error" aria-live="polite">
      <svg class="mt-0.5 h-3.5 w-3.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 8v5M12 16h.01" stroke-linecap="round" />
      </svg>
      <span>{{ error }}</span>
    </p>
    <p v-else-if="hint" :id="`${id}-hint`" class="field-hint">{{ hint }}</p>
  </div>
</template>
