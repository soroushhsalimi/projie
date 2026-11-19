<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import BrandMark from '@/shared/components/BrandMark.vue'
import { useAuthStore } from '@/modules/auth/stores/auth'

const { t } = useI18n()
const auth = useAuthStore()
const home = computed(() => (auth.isAuthenticated ? '/dashboard' : '/login'))
</script>

<template>
  <main id="main-content" class="relative flex min-h-screen items-center justify-center overflow-hidden bg-sand-50 px-6 py-16">
    <div class="pattern-dots pointer-events-none absolute inset-0 opacity-40" aria-hidden="true" />
    <div
      class="pointer-events-none absolute -top-32 start-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-teal-200/30 blur-3xl"
      aria-hidden="true"
    />

    <div class="relative w-full max-w-md text-center">
      <div class="mx-auto flex justify-center">
        <BrandMark :size="56" decorative />
      </div>

      <p class="mt-8 text-[5rem] font-extrabold leading-none tracking-tight text-ink-950/10">
        {{ t('notFound.code') }}
      </p>
      <h1 class="-mt-6 text-2xl font-extrabold tracking-tight text-ink-950">
        {{ t('notFound.title') }}
      </h1>
      <p class="mx-auto mt-3 max-w-sm text-sm leading-7 text-ink-500">
        {{ t('notFound.body') }}
      </p>

      <RouterLink :to="home" class="btn-primary mx-auto mt-8 max-w-xs">
        {{ t('notFound.home') }}
      </RouterLink>

      <p class="mt-10 text-[0.7rem] text-ink-400">{{ t('footer.rights') }}</p>
    </div>
  </main>
</template>
