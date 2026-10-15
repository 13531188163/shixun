import { createRouter, createWebHistory } from 'vue-router'

import Dashboard from '../views/Dashboard.vue'
import Temperature from '../views/Temperature.vue'
import Rainfall from '../views/Rainfall.vue'
import Wind from '../views/Wind.vue'
import AirQuality from '../views/AirQuality.vue'
import Comparison from '../views/Comparison.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard,
    },
    {
      path: '/dashboard',
      name: 'dashboard-build',
      component: Dashboard,
    },
    {
      path: '/temperature',
      name: 'temperature',
      component: Temperature,
    },
    {
      path: '/rainfall',
      name: 'rainfall',
      component: Rainfall,
    },
    {
      path: '/wind',
      name: 'wind',
      component: Wind,
    },
    {
      path: '/air-quality',
      name: 'air-quality',
      component: AirQuality,
    },
    {
      path: '/comparison',
      name: 'comparison',
      component: Comparison,
    },
  ],
})

export default router
