import client from './client'

export const api = {
  // auth
  login: (username: string, password: string) =>
    client.post<{ token: string; user: any }>('/auth/login', { username, password }),
  register: (payload: any) => client.post('/auth/register', payload),
  me: () => client.get('/auth/me'),

  // stores
  listStores: (params?: any) => client.get('/stores', { params }),
  getStore: (id: number) => client.get(`/stores/${id}`),
  createStore: (payload: any) => client.post('/stores', payload),

  // products
  listProducts: (params?: any) => client.get('/products', { params }),
  getProduct: (id: number) => client.get(`/products/${id}`),
  storeCoverage: () => client.get('/products/store-coverage'),
  listCategories: () => client.get('/products/categories'),

  // live sessions
  listLiveSessions: (params?: any) => client.get('/live-sessions', { params }),
  getLiveSession: (id: number) => client.get(`/live-sessions/${id}`),
  getSessionDashboard: (id: number) => client.get(`/live-sessions/${id}/dashboard`),
  startLive: (id: number) => client.post(`/live-sessions/${id}/start`),
  endLive: (id: number) => client.post(`/live-sessions/${id}/end`),
  updateSessionStatus: (id: number, status: string) => client.put(`/live-sessions/${id}/status`, { status }),

  // danmaku
  sendDanmaku: (sessionId: number, content: string, nickname?: string) =>
    client.post(`/live/${sessionId}/danmaku`, { content, nickname }),
  listDanmaku: (sessionId: number, params?: any) =>
    client.get(`/live/${sessionId}/danmaku`, { params }),
  manualReply: (sessionId: number, msgId: number, content: string) =>
    client.post(`/live/${sessionId}/danmaku/${msgId}/manual-reply`, { content }),
  listAgentActions: (sessionId: number, params?: any) =>
    client.get(`/live/${sessionId}/agent-actions`, { params }),
  listMonitorEvents: (sessionId: number, params?: any) =>
    client.get(`/live/${sessionId}/monitor-events`, { params }),

  // agent
  triggerAgent: (sessionId: number) => client.post(`/live/${sessionId}/agent/trigger`),

  // coupons
  listCoupons: (params?: any) => client.get('/coupons', { params }),
  couponStats: () => client.get('/coupons/stats'),
  createCoupon: (payload: any) => client.post('/coupons', payload),
  issueCoupon: (payload: any) => client.post('/coupons/issue', payload),

  // orders
  listOrders: (params?: any) => client.get('/orders', { params }),
  getOrder: (id: string | number) => client.get(`/orders/${id}`),
  createOrder: (payload: any) => client.post('/orders/', payload),
  payOrder: (id: string | number) => client.post(`/orders/${id}/pay`),

  // dashboard
  homeStats: () => client.get('/dashboard/home'),
  intradaySales: () => client.get('/dashboard/intraday'),
  salesOverview: (params?: any) => client.get('/dashboard/sales', { params }),
  storeRank: (params?: any) => client.get('/dashboard/store-rank', { params }),
  anomalies: () => client.get('/dashboard/anomalies'),

  // 分析
  sessionTraffic: (id: number) => client.get(`/analytics/sessions/${id}/traffic`),
  sessionReview: (id: number) => client.get(`/analytics/sessions/${id}/review`),
  hostRank: (params?: any) => client.get('/analytics/hosts/rank', { params }),

  // 智能助手
  assistantQuery: (payload: { question: string; days?: number }) => client.post('/assistant/query', payload),
  assistantPlan: (payload: any) => client.post('/assistant/plan', payload),
  assistantReplies: (sessionId: number, size = 20) =>
    client.get('/assistant/replies', { params: { session_id: sessionId, size } }),
  danmakuInsights: (sessionId: number, minutes = 30) =>
    client.get('/assistant/danmaku-insights', { params: { session_id: sessionId, minutes } }),

  // 直播节奏
  pacing: (sessionId: number, duration = 60) =>
    client.get(`/pacing/${sessionId}`, { params: { duration } }),
  pacingAdvance: (sessionId: number, duration = 60) =>
    client.post(`/pacing/${sessionId}/advance`, null, { params: { duration } }),
  pacingReset: (sessionId: number) => client.post(`/pacing/${sessionId}/reset`),

  // 弹幕采集
  ingestStatus: (sessionId: number) => client.get('/ingest/status', { params: { session_id: sessionId } }),
}

export default api
