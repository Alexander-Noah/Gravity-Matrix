import { createRouter, createWebHistory } from 'vue-router'
import { appRoutes, defaultRoute } from './routes'

const RouteShell = { template: '<div />' }

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: defaultRoute.path },
    ...appRoutes.map((route) => ({
      path: route.path,
      name: route.id,
      component: RouteShell,
    })),
    { path: '/:pathMatch(.*)*', redirect: defaultRoute.path },
  ],
})

export default router
