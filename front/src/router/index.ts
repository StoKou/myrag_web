import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Load from '../views/Load.vue'
import About from '../views/About.vue'
import ChunkView from '../views/chunkView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/home'
    },
    {
      path: '/home',
      name: 'home',
      component: Home,
    },
    {
      path: '/load',
      name: 'load',
      component: Load,
    },
    {
      path: '/about',
      name: 'about',
      component: About,
    },
    {
      path: '/chunk',
      name: 'chunk',
      component: ChunkView,
    },
  ],
})

export default router
