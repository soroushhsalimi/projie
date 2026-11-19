<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { useAuthStore } from '@/modules/auth/stores/auth'
import BrandMark from '@/shared/components/BrandMark.vue'

const { t } = useI18n()
const auth = useAuthStore()
</script>

<template>
  <a
    href="#main-content"
    class="sr-only z-50 rounded-lg bg-ink-950 px-4 py-2 text-sm font-semibold text-white focus:not-sr-only focus:fixed focus:start-4 focus:top-4"
  >
    {{ t('common.skipToContent') }}
  </a>

  <div
    v-if="auth.isRestoring"
    class="fixed inset-0 z-40 flex flex-col items-center justify-center gap-4 bg-sand-50"
    role="status"
    aria-live="polite"
  >
    <div class="animate-float">
      <BrandMark :size="56" decorative />
    </div>
    <p class="text-xs font-medium text-ink-400">{{ t('common.loading') }}</p>
  </div>

  <RouterView />
</template>
