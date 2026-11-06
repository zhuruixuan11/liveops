import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: () => import('@/views/HomeView.vue'), meta: { title: '首页概览' } },
  { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { public: true, title: '登录' } },
  { path: '/register', name: 'register', component: () => import('@/views/RegisterView.vue'), meta: { public: true, title: '注册' } },
  { path: '/stores', name: 'stores', component: () => import('@/views/StoreListView.vue'), meta: { title: '门店管理' } },
  { path: '/products', name: 'products', component: () => import('@/views/ProductListView.vue'), meta: { title: '商品管理' } },
  { path: '/products/:id', name: 'product-detail', component: () => import('@/views/ProductDetailView.vue'), meta: { title: '商品详情' } },
  { path: '/live-sessions', name: 'live-sessions', component: () => import('@/views/LiveSessionListView.vue'), meta: { title: '直播场次' } },
  { path: '/live/:id', name: 'live-control', component: () => import('@/views/LiveControlView.vue'), meta: { title: '直播监控' } },
  { path: '/dashboard', name: 'dashboard', component: () => import('@/views/SalesDashboardView.vue'), meta: { title: '销售看板' } },
  { path: '/coupons', name: 'coupons', component: () => import('@/views/CouponView.vue'), meta: { title: '优惠券' } },
  { path: '/orders', name: 'orders', component: () => import('@/views/OrdersView.vue'), meta: { title: '订单' } },
  { path: '/orders/:id', name: 'order-detail', component: () => import('@/views/OrderDetailView.vue'), meta: { title: '订单详情' } },

  // 主播端
  { path: '/host', name: 'host', component: () => import('@/views/HostDashboardView.vue'), meta: { title: '主播工作台' } },
  { path: '/host/live/:id', name: 'host-live', component: () => import('@/views/HostLiveRoomView.vue'), meta: { title: '主播直播间' } },
  { path: '/host/analytics/:id', name: 'host-analytics', component: () => import('@/views/HostAnalyticsView.vue'), meta: { title: '流量复盘' } },
  { path: '/host/orders', name: 'host-orders', component: () => import('@/views/HostOrdersView.vue'), meta: { title: '我的订单' } },

  // 管理端
  { path: '/hosts', name: 'hosts', component: () => import('@/views/HostRankView.vue'), meta: { title: '主播绩效' } },

  // 兜底：未知路径（含已下线的 /assistant）回首页
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to) => {
  const token = localStorage.getItem('liveops_token')
  if (!to.meta.public && !token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
