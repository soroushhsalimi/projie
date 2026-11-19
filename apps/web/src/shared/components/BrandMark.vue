<script setup lang="ts">
withDefaults(defineProps<{ size?: number; decorative?: boolean }>(), {
  size: 44,
  decorative: false,
})
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 48 48"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    :aria-hidden="decorative ? 'true' : undefined"
    role="img"
  >
    <defs>
      <linearGradient id="sara-mark-bg" x1="4" y1="2" x2="44" y2="46" gradientUnits="userSpaceOnUse">
        <stop stop-color="#1AA79C" />
        <stop offset="1" stop-color="#0F6C67" />
      </linearGradient>
      <linearGradient id="sara-mark-gold" x1="12" y1="12" x2="36" y2="36" gradientUnits="userSpaceOnUse">
        <stop stop-color="#F0D8A6" />
        <stop offset="1" stop-color="#D0A04A" />
      </linearGradient>
    </defs>
    <rect x="1" y="1" width="46" height="46" rx="14" fill="url(#sara-mark-bg)" />
    <rect x="1" y="1" width="46" height="46" rx="14" stroke="white" stroke-opacity="0.14" />
    <rect
      x="14"
      y="14"
      width="20"
      height="20"
      rx="3"
      stroke="url(#sara-mark-gold)"
      stroke-width="1.6"
    />
    <rect
      x="14"
      y="14"
      width="20"
      height="20"
      rx="3"
      stroke="url(#sara-mark-gold)"
      stroke-width="1.6"
      transform="rotate(45 24 24)"
    />
    <path
      d="M20 33v-4.2c0-2.2 1.8-4 4-4s4 1.8 4 4V33"
      stroke="white"
      stroke-width="2"
      stroke-linecap="round"
    />
    <circle cx="24" cy="24" r="1.7" fill="#F0D8A6" />
  </svg>
</template>
