<script setup lang="ts">
withDefaults(
  defineProps<{
    tone?: 'error' | 'success' | 'info'
    title?: string
    message: string
  }>(),
  { tone: 'error', title: '' },
)
</script>

<template>
  <div
    class="flex items-start gap-3 rounded-2xl border px-4 py-3 text-sm"
    :class="{
      'border-red-200 bg-red-50 text-red-800': tone === 'error',
      'border-teal-200 bg-teal-50 text-teal-900': tone === 'success',
      'border-gold-300/60 bg-sand-100 text-sand-900': tone === 'info',
    }"
    :role="tone === 'error' ? 'alert' : 'status'"
  >
    <span
      class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full"
      :class="{
        'bg-red-100 text-red-600': tone === 'error',
        'bg-teal-100 text-teal-700': tone === 'success',
        'bg-sand-200 text-sand-800': tone === 'info',
      }"
      aria-hidden="true"
    >
      <svg v-if="tone === 'error'" class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
        <path d="M12 8v5M12 16h.01" stroke-linecap="round" />
        <circle cx="12" cy="12" r="9" />
      </svg>
      <svg v-else-if="tone === 'success'" class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4">
        <path d="m5 12 4 4L19 6" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
      <svg v-else class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 11v5M12 8h.01" stroke-linecap="round" />
      </svg>
    </span>
    <div class="min-w-0">
      <p v-if="title" class="font-semibold">{{ title }}</p>
      <div class="leading-6">
        <slot>{{ message }}</slot>
      </div>
    </div>
  </div>
</template>
