import api from './index'

/**
 * 用户登录
 */
export const login = (username, password) => {
  const formData = new FormData()
  formData.append('username', username)
  formData.append('password', password)
  
  return api.post('/auth/login', formData)
}

/**
 * 用户注册
 */
export const register = (username, email, password, full_name = '') => {
  const formData = new FormData()
  formData.append('username', username)
  formData.append('email', email)
  formData.append('password', password)
  if (full_name) {
    formData.append('full_name', full_name)
  }
  
  return api.post('/auth/register', formData)
}

/**
 * 用户登出
 */
export const logout = () => {
  return api.post('/auth/logout')
}

/**
 * 获取当前用户信息
 */
export const getCurrentUser = () => {
  return api.get('/auth/me')
}
