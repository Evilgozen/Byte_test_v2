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
      path: '/videos/:id/analysis',
      name: 'video-analysis',
      component: () => import('../views/VideoAnalysisView.vue'),
      props: true
    },
    {
      path: '/videos/:id/keyframes',
      name: 'video-keyframes',
      component: () => import('../views/VideoKeyframesView.vue'),
      props: true
    },
    {
      path: '/videos/:id/segments',
      name: 'video-segments',
      component: () => import('../views/VideoSegmentsView.vue'),
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
