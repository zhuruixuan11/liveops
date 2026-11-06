<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">🎙️ 主播工作台</div>
        <div class="page-sub">欢迎回来，{{ auth.user?.username }} · 今天也要元气满满地开播</div>
      </div>
      <el-button :icon="Refresh" circle @click="load" />
    </div>

    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :xs="24" :sm="12" :md="6" v-for="k in kpis" :key="k.label">
        <div class="kpi-card">
          <div class="kpi-icon" :style="{ background: k.bg }">{{ k.icon }}</div>
          <div>
            <div class="kpi-value">{{ k.value }}</div>
            <div class="kpi-label">{{ k.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-card v-if="plan" class="rec-card">
      <template #header>
        <div class="rec-head">
          <div>
            <b>✨ 今日推荐内容</b>
            <span class="rec-sub">基于近 14 天成交 + 弹幕意图 + 近期热点</span>
          </div>
          <div class="rec-actions">
            <el-tag type="danger" effect="dark" size="small">主推：{{ plan.focus_product }}</el-tag>
            <el-button size="small" plain round @click="openAssistant">查看完整规划</el-button>
          </div>
        </div>
      </template>
      <div class="rec-grid">
        <div v-for="(r, i) in plan.recommendations" :key="i" class="rec-item">
          <div class="rec-index">{{ i + 1 }}</div>
          <div>
            <div class="rec-title">{{ r.title }}</div>
            <div class="rec-reason">{{ r.reason }}</div>
            <div class="rec-action">→ {{ r.action }}</div>
          </div>
        </div>
      </div>
      <div class="rec-topics">
        <span class="rec-topics-label">近期热点</span>
        <el-tag v-for="t in plan.hot_topics" :key="t.topic" size="small" type="warning" effect="plain">
          {{ t.topic }}
        </el-tag>
      </div>
    </el-card>

    <el-card>
      <template #header><b>我的直播场次</b></template>
      <el-table :data="items" stripe size="small" v-loading="loading">
        <el-table-column prop="session_id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" effect="dark" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="计划开始" width="170" />
        <el-table-column prop="viewer_count" label="在线" width="90" align="center" />
        <el-table-column label="操作" width="330" align="center">
          <template #default="{ row }">
            <el-button v-if="row.status !== 'living'" size="small" type="success" round @click="start(row)">开播</el-button>
            <el-button v-else size="small" type="danger" round @click="end(row)">下播</el-button>
            <router-link :to="`/host/live/${row.session_id}`">
              <el-button size="small" type="primary" plain round>进入直播间</el-button>
            </router-link>
            <router-link :to="`/host/analytics/${row.session_id}`">
              <el-button size="small" plain round>流量复盘</el-button>
            </router-link>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && items.length === 0" description="暂无我的场次" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const items = ref<any[]>([])
const loading = ref(false)
const plan = ref<any>(null)

function statusType(s: string): 'success' | 'info' | 'warning' | 'danger' {
  return { living: 'success', planned: 'warning', ended: 'info', cancelled: 'danger' }[s] as any || 'info'
}
function statusLabel(s: string) {
  return { living: '直播中', planned: '未开始', ended: '已结束', cancelled: '已取消' }[s] || s
}

const kpis = computed(() => {
  const living = items.value.filter((s) => s.status === 'living')
  const planned = items.value.filter((s) => s.status === 'planned')
  const online = living.reduce((t, s) => t + (s.viewer_count || 0), 0)
  const peak = Math.max(0, ...items.value.map((s) => s.peak_viewer || 0))
  return [
    { label: '累计场次', value: items.value.length, icon: '📅', bg: 'rgba(59,110,245,.12)' },
    { label: '直播中', value: living.length, icon: '🔴', bg: 'rgba(244,63,94,.12)' },
    { label: '当前总在线', value: online, icon: '👥', bg: 'rgba(34,197,94,.12)' },
    { label: '历史峰值', value: peak, icon: '📈', bg: 'rgba(245,158,11,.14)' },
    { label: '待开播', value: planned.length, icon: '⏰', bg: 'linear-gradient(135deg,#c2e9fb,#7cb8f7)' },
  ].slice(0, 4)
})

async function load() {
  loading.value = true
  try {
    const hostId = auth.user?.staff_id
    const r: any = await api.listLiveSessions({ host_id: hostId, size: 100 })
    items.value = r?.items || []
  } catch { /* noop */ }
  finally { loading.value = false }
  loadPlan()
}

async function loadPlan() {
  try {
    const living = items.value.find((s: any) => s.status === 'living')
    const planned = items.value.find((s: any) => s.status === 'planned')
    const ref = living || planned
    plan.value = await api.assistantPlan({
      session_id: ref?.session_id,
      host_id: auth.user?.staff_id,
      duration_minutes: 60,
    })
  } catch { /* noop */ }
}

async function start(row: any) {
  try {
    await api.updateSessionStatus(row.session_id, 'living')
    ElMessage.success('已开播，祝直播顺利！')
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '开播失败')
  }
}

async function end(row: any) {
  await ElMessageBox.confirm('确认结束本场直播？')
  try {
    await api.updateSessionStatus(row.session_id, 'ended')
    ElMessage.success('已下播，辛苦啦')
    load()
    try {
      await ElMessageBox.confirm('本场已结束，是否立即查看本场复盘？', '本场复盘', {
        confirmButtonText: '查看复盘', cancelButtonText: '稍后', type: 'success',
      })
      router.push(`/host/analytics/${row.session_id}`)
    } catch { /* 用户选择稍后 */ }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '下播失败')
  }
}

// 打开 App 里的 AI 助手悬浮窗（原 /assistant 页面已下线）
function openAssistant() {
  window.dispatchEvent(new CustomEvent('open-assistant'))
  ElMessage.info('已打开右下角 AI 运营助手，切到「直播规划」查看完整脚本')
}

onMounted(load)
</script>

<style scoped>
/* 今日推荐 */
.rec-card { margin-bottom: 16px; border-left: 4px solid #f59e0b; }
.rec-head { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.rec-sub { font-size: 12px; color: #9aa3b2; margin-left: 10px; }
.rec-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.rec-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.rec-item { display: flex; gap: 10px; background: #fffaf0; border: 1px solid #fde9c8; border-radius: 12px; padding: 12px 14px; }
.rec-index {
  width: 22px; height: 22px; border-radius: 50%; flex-shrink: 0;
  background: linear-gradient(135deg, #f59e0b, #f97316); color: #fff; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.rec-title { font-size: 14px; font-weight: 700; color: #1f2430; }
.rec-reason { font-size: 12px; color: #6b7280; margin-top: 4px; line-height: 1.6; }
.rec-action { font-size: 12px; color: #3b6ef5; margin-top: 4px; }
.rec-topics { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 14px; }
.rec-topics-label { font-size: 12px; color: #9aa3b2; }

@media (max-width: 900px) {
  .rec-grid { grid-template-columns: 1fr; }
}
</style>
