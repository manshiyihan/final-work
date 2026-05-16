import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/views/MainLayout.vue'
import Login from '@/views/Login.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Home',
    component: MainLayout,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  // 需要登录的页面
  if (to.meta.requiresAuth) {
    if (!token) {
      next('/login')
    } else {
      next()
    }
  } else {
    // 已登录用户访问登录页，跳转到首页
    if (to.path === '/login' && token) {
      next('/')
    } else {
      next()
    }
  }
})

export default router
