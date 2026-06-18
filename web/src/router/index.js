import { createRouter, createWebHistory } from 'vue-router'
import { getAuthSession, hasActiveAuthSession } from '../api/auth'
import { appRoutes, defaultRoute } from './routes'

const RouteShell = { template: '<div />' }

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: defaultRoute.path },
    { path: '/profile', redirect: defaultRoute.path },
    { path: '/projects', redirect: defaultRoute.path },
    { path: '/novel-to-yaml', redirect: '/workbench' },
    ...appRoutes.map((route) => ({
      path: route.path,
      name: route.id,
      component: RouteShell,
    })),
    { path: '/:pathMatch(.*)*', redirect: defaultRoute.path },
  ],
})

router.beforeEach((to) => {
  const canEnterWorkspace = Boolean(getAuthSession().token) && hasActiveAuthSession()

  if (to.name !== 'auth' && !canEnterWorkspace) {
    return { path: '/auth' }
  }

  return true
})

export default router
