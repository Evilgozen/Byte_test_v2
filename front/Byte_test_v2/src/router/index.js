import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/videos',
      name: 'videos',
      component: () => import('../views/VideoListView.vue'),
    },
    {
      path: '/videos/:id',
      name: 'video-detail',
      component: () => import('../views/VideoDetailView.vue'),
      props: true
    },
    {
      path: '/videos/:id/frames',
      name: 'video-frames',
      component: () => import('../views/VideoFramesView.vue'),
      props: true
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
  ],
})

export default router
