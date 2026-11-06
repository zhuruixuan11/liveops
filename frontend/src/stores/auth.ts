import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'
import router from '@/router'

interface User {
  user_id: number
  username: string
  role: string
  staff_id?: number
  store_id?: number
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('liveops_token') || '')
  const rawUser = localStorage.getItem('liveops_user')
  let parsedUser: User | null = null
  if (rawUser) {
    try { parsedUser = JSON.parse(rawUser) } catch { parsedUser = null }
  }
  const user = ref<User | null>(parsedUser)

  const isLoggedIn = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const r: any = await api.login(username, password)
    token.value = r.access_token || r.token
    localStorage.setItem('liveops_token', token.value)
    // 拉取用户信息（含 role / staff_id / store_id）
    const me: any = await api.me()
    user.value = me
    localStorage.setItem('liveops_user', JSON.stringify(me))
  }

  async function me() {
    try {
      const r: any = await api.me()
      user.value = r
      localStorage.setItem('liveops_user', JSON.stringify(r))
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('liveops_token')
    localStorage.removeItem('liveops_user')
    router.push({ name: 'login' })
  }

  return { token, user, isLoggedIn, login, me, logout }
})
