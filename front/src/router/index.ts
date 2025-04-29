import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Load from '../views/Load.vue'
import About from '../views/About.vue'
import ChunkView from '../views/chunkView.vue'
import VectorStore from '../views/VectorStore.vue'
import Embedding from '../views/Embedding.vue'

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
      path: '/chunk',
      name: 'chunk',
      component: ChunkView,
    },
    {
      path: '/embedding',
      name: 'embedding',
      component: Embedding,
    },
    {
      path: '/vectorstore',
      name: 'vectorstore',
      component: VectorStore,
    },
    {
      path: '/about',
      name: 'about',
      component: About,
    },
  ],
})

export default router
