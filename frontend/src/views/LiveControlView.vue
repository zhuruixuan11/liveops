<template>
  <div v-if="session" class="live-room">
    <!-- 直播画面 -->
    <div class="live-stage">
      <video
        v-if="streamUrl"
        :src="streamUrl"
        class="stage-media"
        autoplay muted controls playsinline
      />
      <img
        v-else-if="!posterFailed"
        :src="posterUrl"
        class="stage-media"
        @error="posterFailed = true"
      />
      <div v-else class="stage-fallback"></div>

      <div class="stage-mask"></div>

      <div class="stage-tag">
        <span class="live-dot"></span> LIVE
      </div>
      <div class="stage-viewers">👁 {{ viewers }} 人在线</div>

      <div class="stage-bottom">
        <div class="stage-title">{{ session.title }}</div>
        <div class="stage-sub">
          {{ session.store_name || '—' }} · {{ session.host_name || '—' }}
          <span v-if="!streamUrl" class="stage-note">演示画面（未接入真实推流）</span>
        </div>
      </div>
    </div>

    <!-- 场控三栏 -->
    <div class="control-layout" style="height:auto;flex:1;min-height:0">
      <!-- 左栏 -->
      <div class="col col-left">
        <div style="font-weight:600;margin-bottom:6px">{{ session.title }}</div>
        <div style="color:#909399;font-size:12px;margin-bottom:8px">
          {{ session.store_name }} · {{ session.host_name }} ·
          <el-tag :type="session.status==='living'?'success':'info'" size="small">
            {{ statusLabel(session.status) }}
          </el-tag>
        </div>

        <div class="mini-stat">
          <span class="mini-label">当前在线</span>
          <span class="mini-value">{{ viewers }}</span>
        </div>
        <div ref="chartRef" style="height:140px;margin-bottom:12px"></div>

        <div style="font-weight:600;margin:8px 0 4px">主推商品库存水位</div>
        <div v-if="pushProducts.length === 0" style="color:#909399;font-size:12px">暂无主推商品</div>
        <div v-for="p in pushProducts" :key="p.id" style="margin-bottom:8px">
          <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:2px">
            <span>{{ p.name }}<span v-if="p.spec" style="color:#c0c4cc"> / {{ p.spec }}</span></span>
            <span :style="{ color: p.stock < 10 ? '#f56c6c' : '#909399' }">{{ p.stock }}</span>
          </div>
          <el-progress
            :percentage="Math.min(100, Math.round((p.stock / (maxStock || 1)) * 100))"
            :color="p.stock < 10 ? '#f56c6c' : p.stock < 50 ? '#e6a23c' : '#67c23a'"
          />
        </div>
      </div>

      <!-- 中栏 -->
      <div class="col col-center">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
          <span style="font-weight:600">实时弹幕（监控）</span>
          <div>
            <el-tag size="small" type="info" effect="plain">只读</el-tag>
            <el-button size="small" @click="autoScroll=!autoScroll">
              {{ autoScroll ? '暂停滚动' : '自动滚动' }}
            </el-button>
          </div>
        </div>
        <div style="color:#909399;font-size:12px;margin-bottom:6px">
          老板视角只读监控。AI 应答由主播在「主播直播间」触发，处理记录实时同步到右侧「Agent 决策日志」
        </div>
        <div ref="danmakuBoxRef" style="flex:1;overflow-y:auto">
          <DanmakuStream :items="danmakus" />
        </div>
      </div>

      <!-- 右栏 -->
      <div class="col col-right">
        <div style="font-weight:600;margin-bottom:6px">Agent 决策日志</div>
        <AgentActionLog :items="agentLogs" />
        <div style="font-weight:600;margin:12px 0 6px">监控事件</div>
        <MonitorEvent :items="monitorEvents" />
      </div>
    </div>
  </div>
  <el-empty v-else description="加载中…" />
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import api from '@/api'
import { connectWS } from '@/api/stream'
import DanmakuStream from '@/components/DanmakuStream.vue'
import AgentActionLog from '@/components/AgentActionLog.vue'
import MonitorEvent from '@/components/MonitorEvent.vue'

const route = useRoute()
const sessionId = Number(route.params.id)
const session = ref<any>(null)
const viewers = ref(0)
const liveProducts = ref<any[]>([])
const danmakus = ref<any[]>([])
const agentLogs = ref<any[]>([])
const monitorEvents = ref<any[]>([])
const autoScroll = ref(true)
const posterFailed = ref(false)

// 演示画面：未接入真实推流时展示海报；接入后可把 streamUrl 换成 HLS/MP4 地址
const streamUrl = ref('')
const posterUrl =
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=' +
  encodeURIComponent(
    'realistic photo of a chinese e-commerce live streaming studio, female host presenting skincare products to camera, ring light and phone on tripod, bright modern studio background, product shelf behind, warm lighting, high detail',
  ) +
  '&image_size=landscape_16_9'

const pushProducts = computed(() =>
  liveProducts.value.map((p: any) => ({
    id: p.sku_id || p.product_id,
    name: p.product_name || '商品',
    spec: p.spec || '',
    stock: Number(p.stock ?? 0),
    price: p.price,
  })),
)
const maxStock = computed(() => Math.max(1, ...pushProducts.value.map((p) => p.stock)))

let ws: ReturnType<typeof connectWS> | null = null
let chart: echarts.ECharts | null = null
const chartRef = ref<HTMLElement>()
const danmakuBoxRef = ref<HTMLElement>()
const viewerHistory = reactive<number[]>([])

function statusLabel(s: string) {
  return { planned: '未开播', living: '直播中', ended: '已结束', cancelled: '已取消' }[s] || s || '-'
}

// 后端返回的 Agent 动作 / 监控事件字段与展示组件不同，这里统一成展示结构
const TOOL_LABELS: Record<string, string> = {
  intent_classify: '意图识别',
  send_danmaku_reply: '回复弹幕',
  issue_coupon: '发放优惠券',
  query_stock: '查询库存',
  query_product_faq: '商品知识库',
  create_human_ticket: '转人工',
  set_focus_product: '切换主推',
  degraded: '降级处理',
}
const EVENT_META: Record<string, { title: string; level: string }> = {
  viewer_drop: { title: '在线骤降', level: 'WARN' },
  peak_focus: { title: '接近峰值', level: 'INFO' },
  stock_alert: { title: '库存告急', level: 'CRITICAL' },
  low_conversion: { title: '转化偏低', level: 'WARN' },
}

function toAgentLog(a: any) {
  const label = TOOL_LABELS[a.tool_name] || a.tool_name || 'Agent'
  return {
    ts: a.created_at || a.ts,
    action: `${label}${a.tool_result ? '：' + a.tool_result : ''}`,
    reason: a.decision_reason || '',
  }
}

function toMonitorEvent(e: any) {
  const meta = EVENT_META[e.event_type] || { title: e.event_type || '监控事件', level: 'INFO' }
  const parts = [
    e.metric_value != null ? `当前 ${e.metric_value}` : '',
    e.threshold != null ? `阈值 ${e.threshold}` : '',
    e.agent_response || '',
  ].filter(Boolean)
  return { ts: e.created_at || e.ts, type: e.event_type, title: meta.title, level: meta.level, detail: parts.join(' · ') }
}

async function loadLogs() {
  try {
    const actions: any = await api.listAgentActions(sessionId, { size: 20 })
    agentLogs.value = (actions || []).map(toAgentLog)
  } catch { /* noop */ }
  try {
    const events: any = await api.listMonitorEvents(sessionId, { size: 20 })
    monitorEvents.value = (events || []).map(toMonitorEvent)
  } catch { /* noop */ }
}

async function load() {
  try {
    const s: any = await api.getLiveSession(sessionId)
    session.value = s
    liveProducts.value = s?.live_products || []
    viewers.value = Number(s?.viewer_count || 0)
  } catch { /* noop */ }
}

async function loadDanmaku() {
  try {
    const rows: any = await api.listDanmaku(sessionId)
    danmakus.value = (rows || []).slice().reverse().map((d: any) => ({
      username: d.nickname || '观众',
      content: d.content,
      intent: d.intent || '',
    }))
    scrollToBottom()
  } catch { /* noop */ }
}

function renderChart() {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption({
    grid: { top: 10, bottom: 20, left: 30, right: 10 },
    xAxis: { type: 'category', data: viewerHistory.map((_, i) => String(i)), show: false },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{
      type: 'line', smooth: true, symbol: 'none', data: viewerHistory.slice(-30),
      areaStyle: { opacity: 0.2 }, lineStyle: { color: '#409eff', width: 2 },
      itemStyle: { color: '#409eff' },
    }],
  })
}

function scrollToBottom() {
  nextTick(() => {
    if (!autoScroll.value) return
    danmakuBoxRef.value && (danmakuBoxRef.value.scrollTop = danmakuBoxRef.value.scrollHeight)
  })
}

onMounted(async () => {
  await load()
  await loadDanmaku()
  loadLogs()
  renderChart()

  try {
    ws = connectWS(sessionId)
    ws.subscribe('danmaku', (m) => {
      const d: any = m.data || {}
      danmakus.value.push({
        username: d.nickname || d.username || '观众',
        content: d.content,
        intent: d.intent || '',
      })
      if (danmakus.value.length > 200) danmakus.value.splice(0, danmakus.value.length - 200)
      scrollToBottom()
    })
    ws.subscribe('agent_action', (m) => {
      agentLogs.value.unshift(toAgentLog(m.data || {}))
      if (agentLogs.value.length > 100) agentLogs.value.pop()
    })
    ws.subscribe('monitor_event', (m) => {
      monitorEvents.value.unshift(toMonitorEvent(m.data || {}))
      if (monitorEvents.value.length > 100) monitorEvents.value.pop()
    })
    ws.subscribe('viewer_stats', (m) => {
      viewers.value = m.data?.viewers ?? viewers.value
      viewerHistory.push(viewers.value)
      if (viewerHistory.length > 60) viewerHistory.shift()
      renderChart()
    })
  } catch { /* noop */ }

  watch(viewers, (v) => {
    viewerHistory.push(v)
    if (viewerHistory.length > 60) viewerHistory.shift()
    renderChart()
  })
})

onBeforeUnmount(() => { ws?.close(); chart?.dispose() })
</script>

<style scoped>
.live-room {
  height: calc(100vh - 76px);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.live-stage {
  position: relative;
  flex: 0 0 300px;
  border-radius: 8px;
  overflow: hidden;
  background: #10141c;
}
.stage-media {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.stage-fallback {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #1f2b3d, #33507a 60%, #4a7bc8);
}
.stage-mask {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.28), rgba(0, 0, 0, 0) 35%, rgba(0, 0, 0, 0.55));
  pointer-events: none;
}
.stage-tag {
  position: absolute;
  top: 12px;
  left: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(245, 108, 108, 0.92);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 12px;
}
.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #fff;
  animation: pulse 1.2s infinite;
}
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.25; } }
.stage-viewers {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 12px;
}
.stage-bottom {
  position: absolute;
  left: 14px;
  right: 14px;
  bottom: 12px;
  color: #fff;
}
.stage-title { font-size: 16px; font-weight: 700; }
.stage-sub { font-size: 12px; opacity: 0.82; margin-top: 2px; }
.stage-note {
  margin-left: 8px;
  padding: 1px 6px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.18);
}
.mini-stat {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 14px; margin-bottom: 8px;
  border-radius: 12px;
  background: var(--lo-primary-soft);
  border: 1px solid rgba(59, 110, 245, 0.16);
}
.mini-label { font-size: 12px; color: var(--lo-text-sub); }
.mini-value { font-size: 22px; font-weight: 700; color: var(--lo-primary); font-variant-numeric: tabular-nums; line-height: 1; }
</style>
