import 'vue-router'

import type { Role } from '@/api/types'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    guestOnly?: boolean
    title?: string
    roles?: Role[]
  }
}
