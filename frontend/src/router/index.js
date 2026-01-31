import { createRouter, createWebHistory } from 'vue-router'
import Portal from '@/views/Portal.vue'
import Home from '@/views/Home.vue'

const routes = [
  {
    path: '/',
    name: 'Portal',
    component: Portal,
    meta: { isPortal: true }
  },
  {
    path: '/ppt',
    name: 'PPT',
    component: Home
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
