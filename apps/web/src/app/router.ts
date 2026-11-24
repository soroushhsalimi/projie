import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
  type Router,
  type RouterHistory,
} from 'vue-router'

import { useAuthStore } from '@/modules/auth/stores/auth'

export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: { name: 'login' },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/modules/auth/views/LoginView.vue'),
    meta: { guestOnly: true, title: 'ورود' },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/modules/auth/views/RegisterView.vue'),
    meta: { guestOnly: true, title: 'ثبت‌نام' },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/modules/dashboard/views/DashboardView.vue'),
    meta: { requiresAuth: true, title: 'داشبورد' },
  },
  {
    path: '/tickets',
    name: 'tickets',
    component: () => import('@/modules/tickets/views/TicketsView.vue'),
    meta: {
      requiresAuth: true,
      roles: ['manager', 'admin'],
      title: 'درخواست‌های تعمیرات',
    },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/shared/views/NotFoundView.vue'),
  },
]

export function createAppRouter(history: RouterHistory = createWebHistory()): Router {
  const router = createRouter({
    history,
    routes,
    scrollBehavior: () => ({ top: 0 }),
  })

  router.beforeEach(async (to) => {
    const auth = useAuthStore()
    await auth.ensureInitialized()

    if (to.meta.requiresAuth && !auth.isAuthenticated) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    if (to.meta.guestOnly && auth.isAuthenticated) {
      return { name: 'dashboard' }
    }
    if (to.meta.roles && (!auth.user || !to.meta.roles.includes(auth.user.role))) {
      return { name: 'dashboard' }
    }
    return true
  })

  return router
}

export const router = createAppRouter()
