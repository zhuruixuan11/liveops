<template>
  <el-container v-if="auth.isLoggedIn">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <span class="logo-icon">🎬</span>
        <span class="logo-text">
          <span class="logo-name">LiveOps</span>
          <span class="logo-sub">直播运营平台</span>
        </span>
      </div>
      <el-menu
        :default-active="route.path"
        background-color="#0d1524"
        text-color="#9fb0c9"
        active-text-color="#ffffff"
        router
        class="side-menu"
      >
        <template v-for="m in menus" :key="m.index">
          <el-menu-item :index="m.index">
            <el-icon><component :is="m.icon" /></el-icon>
            <span>{{ m.label }}</span>
          </el-menu-item>
        </template>
      </el-menu>
      <div class="side-footer">{{ roleLabel }}工作台</div>
    </el-aside>

    <el-container>
      <el-header class="topbar">
        <div class="topbar-title">
          <span class="topbar-dot"></span>
          <span>{{ route.meta.title || 'LiveOps' }}</span>
        </div>
        <div style="display:flex;align-items:center;gap:12px">
          <el-tag v-if="auth.user" :color="roleColor" effect="dark" size="small" style="border:none">{{ roleLabel }}</el-tag>
          <span v-if="auth.user" class="username">{{ auth.user.username }}</span>
          <el-button size="small" text @click="auth.logout()">退出</el-button>
        </div>
      </el-header>
      <el-main class="main-area">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>

    <!-- 右下角可拖动悬浮按钮 → 聊天窗口 -->
    <div
      class="ai-fab" :style="fabStyle" title="AI 运营助手（可拖动）"
      @pointerdown="onFabDown" @click="onFabClick"
    >
      <span class="ai-fab-icon">🤖</span>
    </div>

    <transition name="ai-pop">
      <div v-if="aiOpen" class="ai-panel">
        <div class="ai-panel-head">
          <span class="ai-panel-title">AI 运营助手</span>
          <el-button text size="small" @click="aiOpen = false">关闭 ✕</el-button>
        </div>
        <div class="ai-panel-body">
          <AssistantView />
        </div>
      </div>
    </transition>
  </el-container>
  <router-view v-else />
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AssistantView from '@/views/AssistantView.vue'

const route = useRoute()
const auth = useAuthStore()
const aiOpen = ref(false)

// 悬浮按钮可拖动：位置记在 localStorage，窗口缩放时自动收回可视区
const FAB_SIZE = 52
const fabPos = ref<{ left: number; top: number } | null>(null)
const fabStyle = computed(() => (fabPos.value
  ? { left: `${fabPos.value.left}px`, top: `${fabPos.value.top}px`, right: 'auto', bottom: 'auto' }
  : {}))

let drag: { startX: number; startY: number; originLeft: number; originTop: number; moved: boolean } | null = null
let suppressClick = false

function clampFab(left: number, top: number) {
  const maxLeft = window.innerWidth - FAB_SIZE - 8
  const maxTop = window.innerHeight - FAB_SIZE - 8
  return { left: Math.min(Math.max(8, left), Math.max(8, maxLeft)), top: Math.min(Math.max(8, top), Math.max(8, maxTop)) }
}

function onFabDown(e: PointerEvent) {
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  drag = { startX: e.clientX, startY: e.clientY, originLeft: rect.left, originTop: rect.top, moved: false }
  ;(e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId)
  window.addEventListener('pointermove', onFabMove)
  window.addEventListener('pointerup', onFabUp, { once: true })
}

function onFabMove(e: PointerEvent) {
  if (!drag) return
  const dx = e.clientX - drag.startX
  const dy = e.clientY - drag.startY
  if (Math.abs(dx) > 4 || Math.abs(dy) > 4) drag.moved = true
  if (!drag.moved) return
  fabPos.value = clampFab(drag.originLeft + dx, drag.originTop + dy)
}

function onFabUp() {
  window.removeEventListener('pointermove', onFabMove)
  if (drag?.moved) {
    try { localStorage.setItem('liveops_fab', JSON.stringify(fabPos.value)) } catch { /* noop */ }
    // 拖完不要触发一次点击把窗口打开
    suppressClick = true
    setTimeout(() => { suppressClick = false }, 80)
  }
  drag = null
}

function onFabClick() {
  if (suppressClick) return
  aiOpen.value = !aiOpen.value
}

function onResize() {
  if (fabPos.value) fabPos.value = clampFab(fabPos.value.left, fabPos.value.top)
}

// 其它页面（如主播工作台）通过事件唤起助手浮窗
function onOpenAssistant() { aiOpen.value = true }

onMounted(() => {
  window.addEventListener('open-assistant', onOpenAssistant)
  window.addEventListener('resize', onResize)
  try {
    const saved = localStorage.getItem('liveops_fab')
    if (saved) {
      const p = JSON.parse(saved)
      fabPos.value = clampFab(Number(p.left) || 0, Number(p.top) || 0)
    }
  } catch { /* noop */ }
})

onBeforeUnmount(() => {
  window.removeEventListener('open-assistant', onOpenAssistant)
  window.removeEventListener('resize', onResize)
  window.removeEventListener('pointermove', onFabMove)
})

const ALL_MENUS = [
  // 老板端只保留结果视角：概览、看板、在播场次、主播绩效
  { index: '/', label: '首页概览', icon: 'Odometer', roles: ['ADMIN'] },
  { index: '/dashboard', label: '销售看板', icon: 'DataAnalysis', roles: ['ADMIN'] },
  { index: '/live-sessions', label: '直播场次', icon: 'VideoCamera', roles: ['ADMIN'] },
  { index: '/hosts', label: '主播绩效', icon: 'Medal', roles: ['ADMIN'] },
  // 主播端：工作台 + 我的订单
  { index: '/host', label: '主播工作台', icon: 'VideoCamera', roles: ['HOST'] },
  { index: '/host/orders', label: '我的订单', icon: 'List', roles: ['HOST'] },
]

const ROLE_META: Record<string, { label: string; color: string }> = {
  ADMIN: { label: '老板/管理员', color: '#f56c6c' },
  HOST: { label: '主播', color: '#67c23a' },
}

const role = computed(() => auth.user?.role || 'ADMIN')
const roleLabel = computed(() => ROLE_META[role.value]?.label || role.value)
const roleColor = computed(() => ROLE_META[role.value]?.color || '#909399')

const menus = computed(() => ALL_MENUS.filter((m) => m.roles.includes(role.value)))
</script>

<style>
body { margin: 0; font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #f4f6fb; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* 侧边栏 */
.sidebar {
  display: flex; flex-direction: column;
  background: linear-gradient(180deg, #0d1524 0%, #0a101c 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.04);
}
.logo {
  color: #fff; padding: 20px 16px; font-weight: 700; font-size: 17px;
  display: flex; align-items: center; gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}
.logo-icon { font-size: 22px; }
.logo-text { display: flex; flex-direction: column; line-height: 1.25; }
.logo-name { font-size: 17px; letter-spacing: 0.3px; }
.logo-sub { font-size: 11px; font-weight: 400; color: rgba(255, 255, 255, 0.42); letter-spacing: 0.5px; }
.side-menu { border-right: none; flex: 1; padding: 8px; }
.side-menu .el-menu-item {
  height: 44px; line-height: 44px; border-radius: 9px; margin-bottom: 4px;
  position: relative; transition: background 0.18s ease, color 0.18s ease;
}
.side-menu .el-menu-item:hover { background: rgba(255, 255, 255, 0.06) !important; color: #fff !important; }
.side-menu .el-menu-item.is-active {
  background: linear-gradient(90deg, rgba(59, 110, 245, 0.22), rgba(124, 92, 255, 0.12)) !important;
  font-weight: 600;
}
.side-menu .el-menu-item.is-active::before {
  content: ''; position: absolute; left: 0; top: 50%; transform: translateY(-50%);
  width: 3px; height: 18px; border-radius: 0 3px 3px 0;
  background: linear-gradient(180deg, #3b6ef5, #7c5cff);
}
.side-footer {
  color: rgba(255, 255, 255, 0.32); font-size: 12px;
  text-align: center; padding: 12px 0; border-top: 1px solid rgba(255, 255, 255, 0.07);
}

/* 顶栏 */
.topbar {
  background: #fff; display: flex; align-items: center; justify-content: space-between;
  box-shadow: 0 1px 0 rgba(24, 39, 75, 0.06); z-index: 5; height: 60px;
}
.topbar-title { display: flex; align-items: center; gap: 9px; font-weight: 600; font-size: 15px; color: #1f2430; }
.topbar-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: linear-gradient(135deg, #3b6ef5, #7c5cff);
  box-shadow: 0 0 0 3px rgba(59, 110, 245, 0.12);
}
.username { color: #303133; font-size: 14px; }
.main-area { background: #f4f6fb; padding: 20px; }

/* 悬浮 AI 按钮（可拖动） */
.ai-fab {
  position: fixed;
  right: 26px;
  bottom: 30px;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff, #2b6fd0);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  z-index: 2000;
  box-shadow: 0 6px 18px rgba(64, 158, 255, 0.45);
  transition: box-shadow 0.15s ease;
  user-select: none;
  touch-action: none;
}
.ai-fab:hover {
  box-shadow: 0 10px 24px rgba(64, 158, 255, 0.55);
}
.ai-fab:active { cursor: grabbing; }
.ai-fab-icon { font-size: 22px; line-height: 1; pointer-events: none; }

/* AI 聊天窗口：随屏幕自适应 */
.ai-panel {
  position: fixed;
  right: 26px;
  bottom: 92px;
  width: min(520px, calc(100vw - 32px));
  height: min(720px, calc(100vh - 120px));
  background: #fff;
  border-radius: 14px;
  z-index: 2001;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 12px 40px rgba(0, 21, 41, 0.22);
}
.ai-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 1px solid #ebeef5;
  flex-shrink: 0;
}
.ai-panel-title { font-weight: 700; font-size: 15px; color: #303133; }
.ai-panel-body { flex: 1; min-height: 0; overflow-y: auto; padding: 12px 16px; }

@media (max-width: 720px) {
  .ai-panel {
    right: 8px;
    left: 8px;
    bottom: 76px;
    width: auto;
    height: calc(100vh - 96px);
  }
  .ai-fab { right: 14px; bottom: 16px; width: 44px; height: 44px; }
  .ai-fab-icon { font-size: 18px; }
}

.ai-pop-enter-active, .ai-pop-leave-active { transition: opacity 0.18s ease, transform 0.18s ease; }
.ai-pop-enter-from, .ai-pop-leave-to { opacity: 0; transform: translateY(12px) scale(0.98); }

/* 小屏：侧栏收成图标条，给内容让位 */
@media (max-width: 900px) {
  .sidebar { width: 72px !important; }
  .logo { justify-content: center; padding: 18px 0; }
  .logo-text, .side-footer { display: none; }
  .side-menu { padding: 8px 6px; }
  .side-menu .el-menu-item { justify-content: center; padding: 0 !important; }
  .side-menu .el-menu-item span { display: none; }
  .topbar { padding: 0 12px !important; }
  .username { display: none; }
  .main-area { padding: 14px !important; }
}
</style>
