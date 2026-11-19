import { createI18n } from 'vue-i18n'

import enUS from '@/locales/en-US'
import faIR from '@/locales/fa-IR'

export const SUPPORTED_LOCALES = ['fa-IR', 'en-US'] as const
export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number]

export const DEFAULT_LOCALE: SupportedLocale = 'fa-IR'

export const i18n = createI18n({
  legacy: false,
  locale: DEFAULT_LOCALE,
  fallbackLocale: 'en-US',
  messages: {
    'fa-IR': faIR,
    'en-US': enUS,
  },
})

export function applyDocumentLocale(locale: SupportedLocale): void {
  document.documentElement.lang = locale
  document.documentElement.dir = locale === 'fa-IR' ? 'rtl' : 'ltr'
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat(i18n.global.locale.value).format(value)
}

export function formatDate(value: string | Date): string {
  const date = typeof value === 'string' ? new Date(value) : value
  return new Intl.DateTimeFormat(i18n.global.locale.value, {
    dateStyle: 'medium',
    timeZone: 'UTC',
  }).format(date)
}
