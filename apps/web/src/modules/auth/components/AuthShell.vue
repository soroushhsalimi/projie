<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import BrandMark from '@/shared/components/BrandMark.vue'

defineProps<{ mode: 'login' | 'register' }>()

const { t } = useI18n()

const features = [
  { key: 'request', icon: 'calendar' },
  { key: 'track', icon: 'pulse' },
  { key: 'manage', icon: 'bed' },
] as const
</script>

<template>
  <div class="auth-shell">
    <section class="brand-panel" aria-label="SARA">
      <div class="brand-arch" aria-hidden="true" />
      <div class="relative z-10 flex min-h-screen flex-col p-10 xl:p-14">
        <header class="flex items-center gap-3">
          <BrandMark :size="46" decorative />
          <div class="leading-tight">
            <div class="text-xl font-extrabold tracking-tight text-white">{{ t('app.name') }}</div>
            <div class="text-[0.65rem] font-medium tracking-[0.35em] text-teal-200/80">
              {{ t('app.latin') }}
            </div>
          </div>
        </header>

        <div class="my-auto max-w-lg py-12">
          <p class="eyebrow">
            <span class="h-1.5 w-1.5 rounded-full bg-teal-300" aria-hidden="true" />
            {{ t('brand.eyebrow') }}
          </p>

          <h1 class="mt-7 text-balance text-4xl font-extrabold leading-[1.25] tracking-tight text-white xl:text-[2.9rem]">
            {{ t('brand.title') }}
          </h1>
          <p class="mt-5 max-w-md text-[0.95rem] leading-8 text-ink-200/90">
            {{ t('brand.subtitle') }}
          </p>

          <ul class="mt-9 space-y-4" role="list">
            <li v-for="feature in features" :key="feature.key" class="feature-row">
              <span class="feature-icon" aria-hidden="true">
                <svg
                  v-if="feature.icon === 'calendar'"
                  class="h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                >
                  <rect x="3" y="5" width="18" height="16" rx="3" />
                  <path d="M8 3v4M16 3v4M3 10h18" stroke-linecap="round" />
                  <path d="m9 15 2 2 4-4" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
                <svg
                  v-else-if="feature.icon === 'pulse'"
                  class="h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                >
                  <path d="M3 12h4l2-6 4 12 2-6h6" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
                <svg
                  v-else
                  class="h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                >
                  <path d="M3 18v-6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v6M3 18h18M6 10V7a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v3" stroke-linecap="round" />
                  <path d="M7 18v2M17 18v2" stroke-linecap="round" />
                </svg>
              </span>
              <span>{{ t(`brand.features.${feature.key}`) }}</span>
            </li>
          </ul>

          <dl class="mt-10 grid grid-cols-3 gap-4 border-t border-white/10 pt-7">
            <div>
              <dt class="sr-only">{{ t('brand.stats.residents') }}</dt>
              <dd class="metric-value">{{ t('brand.stats.residentsValue') }}</dd>
              <dd class="metric-label">{{ t('brand.stats.residents') }}</dd>
            </div>
            <div>
              <dt class="sr-only">{{ t('brand.stats.satisfaction') }}</dt>
              <dd class="metric-value">{{ t('brand.stats.satisfactionValue') }}</dd>
              <dd class="metric-label">{{ t('brand.stats.satisfaction') }}</dd>
            </div>
            <div>
              <dt class="sr-only">{{ t('brand.stats.support') }}</dt>
              <dd class="metric-value">{{ t('brand.stats.supportValue') }}</dd>
              <dd class="metric-label">{{ t('brand.stats.support') }}</dd>
            </div>
          </dl>

          <figure class="mt-10 hidden border-s-2 border-gold-400/60 ps-4 xl:block">
            <blockquote class="text-sm leading-7 text-ink-200/80">{{ t('brand.quote') }}</blockquote>
            <figcaption class="mt-2 text-xs text-ink-400">{{ t('brand.quoteAuthor') }}</figcaption>
          </figure>
        </div>

        <footer class="flex items-center justify-between gap-4 text-[0.7rem] text-ink-400">
          <span>{{ t('footer.rights') }}</span>
          <span class="flex items-center gap-1.5">
            <span class="h-1.5 w-1.5 rounded-full bg-teal-400" aria-hidden="true" />
            {{ t('auth.secureNote') }}
          </span>
        </footer>
      </div>
    </section>

    <main
      id="main-content"
      class="relative flex min-h-screen w-full min-w-0 items-center justify-center overflow-hidden px-4 py-10 sm:px-6 lg:px-10"
    >
      <div class="pattern-dots pointer-events-none absolute inset-0 opacity-40" aria-hidden="true" />
      <div
        class="pointer-events-none absolute -top-24 end-[-6rem] h-72 w-72 rounded-full bg-teal-200/30 blur-3xl"
        aria-hidden="true"
      />
      <div class="relative w-full max-w-[29rem] animate-fade-up">
        <div class="mb-6 flex items-center justify-between lg:hidden">
          <div class="flex items-center gap-2.5">
            <BrandMark :size="40" decorative />
            <div class="leading-tight">
              <div class="text-lg font-extrabold text-ink-950">{{ t('app.name') }}</div>
              <div class="text-[0.6rem] tracking-[0.3em] text-ink-400">{{ t('app.latin') }}</div>
            </div>
          </div>
          <RouterLink :to="mode === 'login' ? '/register' : '/login'" class="text-xs font-medium text-ink-400">
            {{ mode === 'login' ? t('auth.registerLink') : t('auth.loginLink') }}
          </RouterLink>
        </div>

        <slot />

        <footer class="mt-8 flex items-center justify-between px-1 text-[0.7rem] text-ink-400">
          <span>{{ t('footer.rights') }}</span>
          <div class="flex items-center gap-3">
            <a href="#" class="transition hover:text-ink-700">{{ t('footer.privacy') }}</a>
            <a href="#" class="transition hover:text-ink-700">{{ t('footer.terms') }}</a>
          </div>
        </footer>
      </div>
    </main>
  </div>
</template>
