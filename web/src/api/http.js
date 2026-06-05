import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

export const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('gm_auth_token')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

export const getApiErrorMessage = (error) => {
  const detail = error?.response?.data?.detail

  if (typeof detail === 'string') {
    return detail
  }

  if (Array.isArray(detail) && detail[0]?.msg) {
    return detail[0].msg
  }

  if (error?.response?.data?.message) {
    return error.response.data.message
  }

  if (error?.code === 'ECONNABORTED') {
    return '请求超时，请稍后重试。'
  }

  if (!error?.response) {
    return '暂时无法连接服务，请确认后端接口已启动。'
  }

  return '请求失败，请稍后重试。'
}
