import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 90000
})

// 请求拦截器 - 添加token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理401错误
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      // 清除token
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      
      // 跳转到登录页
      if (window.location.pathname !== '/login') {
        ElMessage.error('登录已过期，请重新登录')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export const verifyAudio = (formData) => {
  return api.post('/verify', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const registerSpeaker = (formData) => {
  return api.post('/register', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const getRecords = (params) => {
  return api.get('/records/query', { params })
}

export const healthCheck = () => {
  return api.get('/health')
}

export default api
