import axios from 'axios'
import router from '@/router'

const client = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

client.interceptors.request.use((cfg) => {
  const t = localStorage.getItem('liveops_token')
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})

client.interceptors.response.use(
  (r) => r.data,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('liveops_token')
      localStorage.removeItem('liveops_user')
      router.push({ name: 'login' })
    }
    return Promise.reject(err)
  },
)

export default client
