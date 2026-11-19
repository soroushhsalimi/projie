import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from '@/App.vue'
import { i18n, applyDocumentLocale, DEFAULT_LOCALE } from '@/app/i18n'
import { router } from '@/app/router'
import '@/styles/main.css'

applyDocumentLocale(DEFAULT_LOCALE)

const app = createApp(App)

app.use(createPinia())
app.use(i18n)
app.use(router)
app.mount('#app')
