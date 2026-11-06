<template>
  <div v-if="session">
    <!-- 头部横幅 -->
    <div class="hero">
      <div>
        <div class="hero-title">{{ session.title }}</div>
        <div class="hero-sub">
          {{ session.store_name }} · 主播 {{ session.host_name }}
          <el-tag :type="session.status === 'living' ? 'success' : 'info'" size="small" effect="dark" style="margin-left:6px">
            {{ session.status === 'living' ? '直播中' : session.status }}
          </el-tag>
        </div>
      </div>
      <div class="hero-right">
        <div class="viewer-num">{{ session.viewer_count || 0 }}</div>
        <div class="viewer-label">当前在线</div>
        <router-link :to="`/host/analytics/${sessionId}`">
          <el-button size="small" type="primary" plain style="margin-top:8px">流量复盘</el-button>
        </router-link>
      </div>
    </div>

    <!-- 本场规划：开播时置顶，随时能看，不用再去搜 -->
    <el-card v-if="plan" class="plan-card">
      <div class="plan-head">
        <div>
          <b>📌 本场直播规划</b>
          <span class="plan-sub">主推、节奏和福利节点都在这里，直播中不用再翻页面</span>
        </div>
        <div class="plan-tags">
          <el-tag v-if="plan.platform" size="small" type="warning" effect="plain">{{ plan.platform }}规则</el-tag>
          <el-tag type="danger" effect="dark" size="small">主推：{{ plan.focus_product }}</el-tag>
        </div>
      </div>
      <div class="plan-nodes">
        <div
          v-for="n in planNodes" :key="n.index"
          class="plan-node" :class="{ active: n.phase === pacing?.phase?.name }"
        >
          <div class="plan-node-time">第 {{ n.start }} 分钟</div>
          <div class="plan-node-phase">{{ n.phase }}</div>
          <div class="plan-node-action">{{ n.action }}</div>
        </div>
      </div>
    </el-card>

    <!-- 福利节点提醒 -->
    <div v-if="currentWelfare" class="welfare-remind">
      <div class="welfare-remind-icon">🔔</div>
      <div class="welfare-remind-body">
        <div class="welfare-remind-title">到福利节点了：{{ currentWelfare.phase }}</div>
        <div class="welfare-remind-desc">{{ currentWelfare.action }}　现在发福袋 / 优惠券，正好接住这波在线</div>
      </div>
      <el-button type="danger" round size="small" :loading="issuing" @click="issueWelfareCoupon">
        发券 / 福袋
      </el-button>
    </div>

    <!-- 节奏指挥 -->
    <el-card v-if="pacing" class="pacing-card">
      <template #header>
        <div class="pac-head">
          <b>🎯 直播节奏指挥</b>
          <div class="pac-actions">
            <el-select v-model="duration" size="small" style="width:104px" @change="loadPacing">
              <el-option v-for="m in [30, 45, 60, 90, 120]" :key="m" :label="m + ' 分钟'" :value="m" />
            </el-select>
            <el-button size="small" @click="resetPacing">重新计时</el-button>
            <el-button size="small" type="primary" @click="advancePacing">下一阶段</el-button>
          </div>
        </div>
      </template>

      <div class="pac-grid">
        <div class="pac-block">
          <div class="pac-label">当前阶段</div>
          <div class="pac-name">{{ pacing.phase.name }}</div>
          <div class="pac-range">
            {{ pacing.phase.start_min }}–{{ pacing.phase.end_min }} 分钟 · 已播 {{ Math.floor(pacing.elapsed_minutes) }} 分钟
          </div>
        </div>
        <div class="pac-block">
          <div class="pac-label">距下一阶段</div>
          <div class="pac-timer" :class="{ over: pacing.overtime_minutes > 0 }">{{ countdownText }}</div>
          <div class="pac-range" v-if="pacing.next_phase">下一阶段：{{ pacing.next_phase.name }}</div>
          <div class="pac-range" v-else>已是最后一个阶段</div>
        </div>
        <div class="pac-block">
          <div class="pac-label">近 5 分钟热度</div>
          <div class="pac-heat-row">
            <span class="heat-num">{{ pacing.heat.danmaku_5m }}</span>
            <span class="heat-unit">条弹幕</span>
            <el-tag size="small" :type="trendType" effect="plain">{{ trendLabel }}</el-tag>
          </div>
          <div class="pac-range">近 10 分钟成交 {{ pacing.heat.orders_10m }} 单 · ¥{{ pacing.heat.gmv_10m }}</div>
        </div>
        <div class="pac-block">
          <div class="pac-label">本场累计</div>
          <div class="pac-heat-row">
            <span class="heat-num">{{ pacing.heat.paid_orders_total }}</span>
            <span class="heat-unit">单 · ¥{{ pacing.heat.gmv_total }}</span>
          </div>
          <div class="pac-range">主推：{{ pacing.focus_product.name }}<span v-if="pacing.focus_product.stock != null">（库存 {{ pacing.focus_product.stock }}）</span></div>
        </div>
      </div>

      <div class="pac-segments">
        <div v-for="p in pacing.phases" :key="p.index" class="seg" :class="p.status"
          :style="{ flex: Math.max(1, p.end_min - p.start_min) }">
          {{ p.name }}
        </div>
      </div>

      <div class="pac-action">
        <span class="pac-action-label">现在该做</span>
        <div>
          <div v-for="(a, i) in pacing.next_actions" :key="i" class="pac-action-line">{{ a }}</div>
        </div>
      </div>

      <el-alert v-for="(a, i) in pacing.alerts" :key="'al' + i"
        :title="a.title" :description="a.action" :type="alertType(a.level)"
        :closable="false" show-icon style="margin-top:8px" />

      <!-- 实时福利决策 -->
      <div v-if="pacing.welfare" class="welfare-box" :class="{ hot: pacing.welfare.should_send }">
        <div class="welfare-main">
          <div class="welfare-icon">{{ welfareIcon }}</div>
          <div>
            <div class="welfare-title">
              {{ pacing.welfare.title }}
              <el-tag size="small" :type="pacing.welfare.should_send ? 'danger' : 'info'" effect="plain">
                决策分 {{ pacing.welfare.score }}
              </el-tag>
            </div>
            <div class="welfare-reason">{{ pacing.welfare.reason }}</div>
            <div v-if="pacing.welfare.coupon" class="welfare-coupon">
              可用券：{{ pacing.welfare.coupon.label }} · 剩 {{ pacing.welfare.coupon.stock_left }} 张
            </div>
          </div>
        </div>
        <el-button
          type="danger" round :loading="issuing"
          :disabled="!pacing.welfare.should_send || !pacing.welfare.coupon"
          @click="issueWelfareCoupon"
        >{{ pacing.welfare.coupon ? '一键发券' : '先创建本场券' }}</el-button>
      </div>

      <div v-if="pacing.clock_note" class="pac-note">{{ pacing.clock_note }}</div>
    </el-card>

    <!-- KPI -->
    <el-row :gutter="16" style="margin:16px 0">
      <el-col :xs="24" :sm="12" :md="6" v-for="k in kpis" :key="k.label">
        <div class="kpi-card">
          <div class="kpi-icon" :style="{ background: k.bg }">{{ k.icon }}</div>
          <div>
            <div class="kpi-value" :style="{ color: k.color }">{{ k.value }}</div>
            <div class="kpi-label">{{ k.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="14">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <b>💬 实时弹幕</b>
              <div style="display:flex;align-items:center;gap:8px">
                <el-button size="small" type="success" :loading="agentLoading" @click="fireAgent">
                  AI 处理弹幕
                </el-button>
                <el-tag size="small" :type="ingest?.connected ? 'success' : 'info'" effect="plain">
                  {{ ingest?.connected ? '采集器在线' : '采集器离线' }}
                </el-tag>
                <span class="ingest-text">今日采集 {{ ingest?.today_count ?? 0 }} 条</span>
                <el-tag size="small" type="info" effect="plain">共 {{ danmakus.length }} 条</el-tag>
              </div>
            </div>
          </template>
          <div ref="boxRef" class="danmaku-box">
            <DanmakuStream :items="danmakus" actionable @reply="openReply" />
          </div>

          <!-- AI 建议回复：主播可直接照着口播 -->
          <div v-if="aiResults.length" class="ai-reply-panel">
            <div class="ai-reply-head">
              <span>🤖 AI 建议回复（可直接口播）</span>
              <el-button size="small" text @click="aiResults = []">清空</el-button>
            </div>
            <div v-for="r in aiResults" :key="r.msg_id" class="ai-reply-item">
              <div class="ai-reply-q">
                <el-tag size="small" :type="intentType(r.intent)" effect="plain">{{ intentLabel(r.intent) }}</el-tag>
                <span class="ai-nick">{{ r.nickname || '观众' }}</span>
                <span class="ai-content">{{ r.content }}</span>
              </div>
              <div v-if="r.reply" class="ai-reply-a">→ {{ r.reply }}</div>
              <div v-else class="ai-reply-a err">本条处理失败：{{ r.error }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card>
          <template #header><b>📦 主推商品库存水位</b></template>
          <div v-for="p in focusProducts" :key="p.id" class="stock-item">
            <div class="stock-head">
              <span class="stock-name">
                {{ p.product_name }}
                <el-tag v-if="p.is_focus" size="small" type="danger" effect="dark">主推</el-tag>
              </span>
              <span class="stock-num" :style="{ color: (p.stock ?? 99) < 10 ? '#f56c6c' : '#67c23a' }">
                {{ p.stock ?? '-' }} 件
              </span>
            </div>
            <el-progress
              v-if="p.stock != null"
              :percentage="stockPercent(p.stock)"
              :stroke-width="10"
              :color="p.stock < 10 ? '#f56c6c' : p.stock < 50 ? '#e6a23c' : '#67c23a'"
            />
            <div class="stock-meta">{{ p.spec }} · ¥{{ p.price }}</div>
          </div>
          <el-empty v-if="focusProducts.length === 0" description="暂无主推商品" :image-size="80" />
        </el-card>

        <el-card v-if="insights" class="insight-card">
          <template #header>
            <div class="insight-head">
              <b>💡 弹幕洞察 · 近 {{ insights.minutes }} 分钟</b>
              <el-tag size="small" effect="plain">共 {{ insights.total }} 条</el-tag>
            </div>
          </template>

          <div class="insight-summary">{{ insights.summary }}</div>

          <div class="insight-sec-title">观众最关心</div>
          <div v-for="i in insights.by_intent" :key="i.intent" class="intent-row">
            <div class="intent-name">
              {{ i.intent }}
              <el-tag v-if="i.need_human" size="small" type="danger" effect="dark">需人工</el-tag>
            </div>
            <el-progress
              :percentage="Math.min(100, Math.round((i.count / Math.max(1, insights.total)) * 100))"
              :stroke-width="8" :show-text="false"
              :color="i.need_human ? '#f56c6c' : '#409eff'"
              style="flex:1;margin:0 10px"
            />
            <span class="intent-count">{{ i.count }}</span>
            <div v-if="i.samples.length" class="intent-sample">“{{ i.samples[0] }}”</div>
          </div>
          <el-empty v-if="!insights.by_intent.length" description="暂无有效提问" :image-size="50" />

          <div v-if="insights.keywords.length" class="kw-wrap">
            <el-tag v-for="k in insights.keywords" :key="k.word" size="small" effect="plain" class="kw">
              {{ k.word }} <span class="kw-num">{{ k.count }}</span>
            </el-tag>
          </div>

          <el-alert
            v-if="insights.negative.count"
            :title="`⚠️ 负面/售后 ${insights.negative.count} 条，建议优先处理`"
            :description="insights.negative.samples.join(' / ')"
            type="error" :closable="false" show-icon
          />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="replyDialog" title="人工接管弹幕" width="480px" append-to-body>
      <div v-if="replyTarget" class="reply-quote">
        <b>{{ replyTarget.username }}：</b>{{ replyTarget.content }}
      </div>
      <el-input
        v-model="replyText" type="textarea" :rows="3" maxlength="120" show-word-limit
        placeholder="输入主播回复，发送后以「主播」身份出现在弹幕流"
      />
      <template #footer>
        <el-button size="small" @click="replyDialog = false">取消</el-button>
        <el-button size="small" type="primary" :loading="replySending" @click="sendManual">
          发送并转人工
        </el-button>
      </template>
    </el-dialog>
  </div>
  <el-empty v-else description="加载中…" />
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'
import DanmakuStream from '@/components/DanmakuStream.vue'

const route = useRoute()
const sessionId = Number(route.params.id)
const session = ref<any>(null)
const dash = ref<any>(null)
const danmakus = ref<any[]>([])
const boxRef = ref<HTMLElement>()
const pacing = ref<any>(null)
const ingest = ref<any>(null)
const insights = ref<any>(null)
const duration = ref(60)
const issuing = ref(false)
const agentLoading = ref(false)
const aiResults = ref<any[]>([])

const INTENT_LABELS: Record<string, string> = {
  faq_product: '商品咨询', ask_price: '问价格', ask_coupon: '要优惠',
  ask_stock: '问库存', logistics: '问物流', aftersale: '售后',
  complaint: '投诉', spam: '刷屏', general: '其他',
}

function intentLabel(i?: string) {
  return i ? INTENT_LABELS[i] || i : '未识别'
}

function intentType(i?: string): 'success' | 'info' | 'warning' | 'danger' {
  if (i === 'complaint' || i === 'aftersale') return 'danger'
  if (i === 'spam') return 'info'
  if (i === 'ask_stock' || i === 'ask_coupon') return 'warning'
  return 'success'
}

let timer: any = null
let pacingTimer: any = null
let insightTimer: any = null

const countdownText = computed(() => {
  if (!pacing.value) return '-'
  if (pacing.value.overtime_minutes > 0) return '已超时'
  const s = Math.max(0, pacing.value.countdown_seconds || 0)
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
})
const trendType = computed(() => ({ up: 'success', down: 'danger', flat: 'info' } as any)[pacing.value?.heat?.trend] || 'info')
const trendLabel = computed(() => ({ up: '热度上升', down: '热度下滑', flat: '平稳' } as any)[pacing.value?.heat?.trend] || '平稳')
const welfareIcon = computed(() => ({ coupon: '🎫', lucky_bag: '🎁', price: '🔥' } as any)[pacing.value?.welfare?.type] || '🎁')

function alertType(level: string) {
  return ({ error: 'error', warning: 'warning', success: 'success', info: 'info' } as any)[level] || 'info'
}

function stockPercent(stock: number): number {
  return Math.min(100, Math.round((stock / 100) * 100))
}

const kpis = computed(() => [
  { label: '历史峰值在线', value: session.value?.peak_viewer ?? 0, icon: '👥', color: '#3b6ef5', bg: 'rgba(59,110,245,.12)' },
  { label: '本场成交订单', value: dash.value?.orders ?? 0, icon: '🛒', color: '#16a34a', bg: 'rgba(34,197,94,.12)' },
  { label: '本场 GMV', value: '¥' + Number(dash.value?.gmv ?? 0).toFixed(2), icon: '💰', color: '#f43f5e', bg: 'rgba(244,63,94,.12)' },
  { label: '转化率', value: Number(dash.value?.conversion_rate ?? 0).toFixed(2) + '%', icon: '📈', color: '#f59e0b', bg: 'rgba(245,158,11,.14)' },
])

const focusProducts = ref<any[]>([])
const plan = ref<any>(null)

// 规划节点：把脚本按分钟累加，得到每个阶段的起始分钟
const planNodes = computed(() => {
  let acc = 0
  return (plan.value?.script || []).map((s: any, i: number) => {
    const node = { index: i, start: acc, phase: s.phase, action: s.action }
    acc += Number(s.minutes) || 0
    return node
  })
})

// 福利节点：脚本里提到券/福袋/抽奖/红包的阶段
const welfareNodes = computed(() =>
  planNodes.value.filter((n) => /福利|券|福袋|抽奖|红包/.test(`${n.phase}${n.action}`)),
)

// 当前是否走到福利节点（±3 分钟）
const currentWelfare = computed(() => {
  const elapsed = Number(pacing.value?.elapsed_minutes ?? -1)
  if (elapsed < 0) return null
  return welfareNodes.value.find((n) => Math.abs(n.start - elapsed) <= 3) || null
})

async function loadPlan() {
  try {
    plan.value = await api.assistantPlan({ session_id: sessionId, duration_minutes: duration.value })
  } catch { /* noop */ }
}

async function load() {
  try {
    session.value = await api.getLiveSession(sessionId) as any
    focusProducts.value = (session.value?.live_products || []).filter((p: any) => p.is_focus)
  } catch { /* noop */ }
  try {
    dash.value = await api.getSessionDashboard(sessionId) as any
  } catch { /* noop */ }
  loadPlan()
}

async function loadDanmaku() {
  try {
    const list: any = await api.listDanmaku(sessionId, { size: 100 })
    danmakus.value = (list || []).map((d: any) => ({
      msg_id: d.msg_id,
      username: d.nickname || '观众',
      nickname: d.nickname,
      content: d.content,
      intent: d.intent,
      handled_by: d.handled_by,
    })).reverse()
    nextTick(() => {
      if (boxRef.value) boxRef.value.scrollTop = boxRef.value.scrollHeight
    })
  } catch { /* noop */ }
}

const replyDialog = ref(false)
const replyTarget = ref<any>(null)
const replyText = ref('')
const replySending = ref(false)

function openReply(m: any) {
  replyTarget.value = m
  replyText.value = ''
  replyDialog.value = true
}

async function sendManual() {
  const text = replyText.value.trim()
  if (!text || !replyTarget.value) return
  replySending.value = true
  try {
    await api.manualReply(sessionId, replyTarget.value.msg_id, text)
    ElMessage.success('已转人工并发送回复')
    replyDialog.value = false
    await loadDanmaku()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '发送失败')
  } finally {
    replySending.value = false
  }
}

async function loadPacing() {
  try { pacing.value = await api.pacing(sessionId, duration.value) } catch { /* noop */ }
  try { ingest.value = await api.ingestStatus(sessionId) } catch { /* noop */ }
}

async function loadInsights() {
  try { insights.value = await api.danmakuInsights(sessionId, 30) } catch { /* noop */ }
}

async function issueWelfareCoupon() {
  const coupon = pacing.value?.welfare?.coupon
  if (!coupon) { ElMessage.warning('本场还没有可用优惠券'); return }
  issuing.value = true
  try {
    await api.issueCoupon({ coupon_id: coupon.coupon_id, session_id: sessionId })
    ElMessage.success(`已发放「${coupon.label}」，记得口播报券`)
    loadPacing()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '发券失败')
  } finally {
    issuing.value = false
  }
}

async function fireAgent() {
  agentLoading.value = true
  try {
    const r: any = await api.triggerAgent(sessionId)
    aiResults.value = (r?.results || []).slice().reverse()
    const n = r?.processed ?? 0
    ElMessage.success(
      n > 0
        ? `AI 已处理 ${n} 条弹幕${r?.is_replay ? '（回放最近弹幕）' : ''}`
        : '暂无可处理的弹幕',
    )
    loadDanmaku()
    loadInsights()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || 'AI 处理失败')
  } finally {
    agentLoading.value = false
  }
}

async function advancePacing() {
  try {
    await api.pacingAdvance(sessionId, duration.value)
    ElMessage.success('已切换到下一阶段')
    loadPacing()
  } catch {
    ElMessage.error('切换失败，请稍后重试')
  }
}

async function resetPacing() {
  try {
    await api.pacingReset(sessionId)
    ElMessage.success('节奏计时已重置')
    loadPacing()
  } catch {
    ElMessage.error('重置失败，请稍后重试')
  }
}

onMounted(async () => {
  await load()
  loadDanmaku()
  loadPacing()
  loadInsights()
  timer = setInterval(() => { loadDanmaku(); load() }, 3000)
  pacingTimer = setInterval(loadPacing, 5000)
  insightTimer = setInterval(loadInsights, 15000)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  if (pacingTimer) clearInterval(pacingTimer)
  if (insightTimer) clearInterval(insightTimer)
})
</script>

<style scoped>
.hero {
  background: linear-gradient(120deg, #134e5e 0%, #1e3c72 60%, #2a5298 120%);
  border-radius: 12px; padding: 20px 24px; color: #fff;
  display: flex; justify-content: space-between; align-items: center;
  box-shadow: 0 4px 16px rgba(0,21,41,0.18);
}
.hero-title { font-size: 20px; font-weight: 700; }
.hero-sub { font-size: 13px; opacity: 0.8; margin-top: 6px; }
.hero-right { text-align: center; }
.viewer-num { font-size: 32px; font-weight: 800; color: #5eead4; line-height: 1.1; }
.viewer-label { font-size: 12px; opacity: 0.75; margin-top: 2px; }

.reply-quote {
  padding: 10px 12px; margin-bottom: 12px; border-radius: 10px;
  background: var(--lo-primary-soft); color: var(--lo-text);
  font-size: 13px; line-height: 1.6;
}
.danmaku-box { height: 400px; overflow-y: auto; }

.stock-item { margin-bottom: 16px; }
.stock-item:last-child { margin-bottom: 0; }
.stock-head { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }
.stock-name { font-weight: 600; color: #303133; }
.stock-num { font-weight: 700; }
.stock-meta { color: #909399; font-size: 12px; margin-top: 2px; }
.ingest-text { font-size: 12px; color: #909399; }

/* 节奏指挥 */
.pacing-card { margin-top: 16px; }
.pac-head { display: flex; justify-content: space-between; align-items: center; }
.pac-actions { display: flex; align-items: center; gap: 8px; }
.pac-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.pac-block { background: #f7f9fc; border-radius: 8px; padding: 12px 14px; }
.pac-label { font-size: 12px; color: #909399; }
.pac-name { font-size: 20px; font-weight: 700; color: #1e3c72; margin-top: 4px; }
.pac-range { font-size: 12px; color: #909399; margin-top: 4px; }
.pac-timer { font-size: 26px; font-weight: 800; color: #409eff; line-height: 1.2; margin-top: 2px; font-variant-numeric: tabular-nums; }
.pac-timer.over { color: #f56c6c; font-size: 20px; }
.pac-heat-row { display: flex; align-items: baseline; gap: 6px; margin-top: 2px; }
.heat-num { font-size: 24px; font-weight: 800; color: #67c23a; }
.heat-unit { font-size: 12px; color: #909399; }

.pac-segments { display: flex; gap: 4px; margin: 16px 0 12px; }
.seg {
  flex: 1; text-align: center; font-size: 12px; padding: 6px 4px;
  border-radius: 6px; background: #f0f2f5; color: #909399; white-space: nowrap; overflow: hidden;
}
.seg.done { background: #ecf5ff; color: #409eff; }
.seg.current { background: #409eff; color: #fff; font-weight: 700; box-shadow: 0 2px 8px rgba(64, 158, 255, 0.35); }

.pac-action { display: flex; gap: 12px; background: #f0f9eb; border-radius: 8px; padding: 12px 14px; }
.pac-action-label { font-size: 12px; font-weight: 700; color: #67c23a; white-space: nowrap; }
.pac-action-line { font-size: 13px; color: #4b5563; line-height: 1.8; }
.pac-note { font-size: 12px; color: #909399; margin-top: 8px; }

/* 福利决策 */
.welfare-box {
  display: flex; justify-content: space-between; align-items: center; gap: 16px;
  margin-top: 12px; padding: 12px 16px; border-radius: 8px;
  background: #f4f4f5; border-left: 4px solid #c0c4cc;
}
.welfare-box.hot { background: #fef0f0; border-left-color: #f56c6c; }
.welfare-main { display: flex; gap: 12px; align-items: flex-start; }
.welfare-icon { font-size: 26px; line-height: 1.2; }
.welfare-title { font-size: 14px; font-weight: 700; color: #303133; display: flex; align-items: center; gap: 8px; }
.welfare-reason { font-size: 12px; color: #606266; margin-top: 4px; line-height: 1.6; }
.welfare-coupon { font-size: 12px; color: #f56c6c; font-weight: 600; margin-top: 4px; }

/* 弹幕洞察 */
.insight-card { margin-top: 16px; }
.insight-head { display: flex; justify-content: space-between; align-items: center; }
.insight-summary { font-size: 13px; color: #303133; line-height: 1.7; background: #f7fbff; border-radius: 8px; padding: 10px 12px; }
.insight-sec-title { font-size: 12px; font-weight: 700; color: #909399; margin: 14px 0 8px; }
.intent-row { display: flex; align-items: center; flex-wrap: wrap; margin-bottom: 10px; }
.intent-name { font-size: 13px; color: #303133; display: flex; align-items: center; gap: 4px; width: 116px; flex-shrink: 0; }
.intent-count { font-size: 13px; font-weight: 700; color: #409eff; width: 32px; text-align: right; }
.intent-sample { flex-basis: 100%; font-size: 12px; color: #909399; margin-top: 2px; padding-left: 116px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.kw-wrap { display: flex; flex-wrap: wrap; gap: 6px; margin: 12px 0; }
.kw-num { color: #f56c6c; font-weight: 700; margin-left: 2px; }

/* AI 建议回复 */
.ai-reply-panel {
  margin-top: 12px; padding-top: 10px;
  border-top: 1px dashed #e4e7ed;
  max-height: 230px; overflow-y: auto;
}
.ai-reply-head {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 13px; font-weight: 700; color: #303133; margin-bottom: 8px;
}
.ai-reply-item {
  background: #f7fbff; border-left: 3px solid #409eff;
  border-radius: 6px; padding: 8px 10px; margin-bottom: 8px;
}
.ai-reply-q { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; font-size: 12px; color: #606266; }
.ai-nick { font-weight: 600; color: #303133; }
.ai-content { color: #909399; }
.ai-reply-a { margin-top: 6px; font-size: 13px; color: #1e3c72; line-height: 1.6; }
.ai-reply-a.err { color: #f56c6c; }

/* 置顶的直播规划 */
.plan-card { margin-bottom: 12px; border-left: 4px solid #409eff; }
.plan-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; gap: 10px; flex-wrap: wrap; }
.plan-sub { font-size: 12px; color: #909399; margin-left: 10px; }
.plan-tags { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.plan-nodes { display: flex; gap: 10px; overflow-x: auto; padding-bottom: 4px; }
.plan-node {
  flex: 1 0 170px; background: #f7f9fc; border-radius: 8px;
  padding: 8px 10px; border: 1px solid transparent;
}
.plan-node.active { background: #eef6ff; border-color: #409eff; box-shadow: 0 0 0 2px rgba(64,158,255,.12); }
.plan-node-time { font-size: 11px; color: #909399; }
.plan-node-phase { font-size: 13px; font-weight: 700; color: #303133; margin-top: 2px; }
.plan-node-action { font-size: 12px; color: #606266; margin-top: 4px; line-height: 1.5; }

/* 福利节点提醒 */
.welfare-remind {
  display: flex; align-items: center; gap: 12px;
  background: linear-gradient(135deg, #fff3e0, #ffe9e9);
  border: 1px solid #f5c2c0; border-radius: 10px;
  padding: 12px 16px; margin-bottom: 12px;
  box-shadow: 0 4px 14px rgba(245,108,108,.12);
}
.welfare-remind-icon { font-size: 26px; }
.welfare-remind-body { flex: 1; }
.welfare-remind-title { font-size: 15px; font-weight: 700; color: #b93a3a; }
.welfare-remind-desc { font-size: 12px; color: #7a5b5b; margin-top: 3px; }

/* 小屏（手机/平板竖屏）适配 */
@media (max-width: 960px) {
  .hero { flex-direction: column; align-items: flex-start; gap: 12px; }
  .hero-right { text-align: left; display: flex; align-items: baseline; gap: 8px; }
  .viewer-num { font-size: 26px; }
  .pac-head { flex-wrap: wrap; gap: 8px; }
  .pac-actions { flex-wrap: wrap; }
  .pac-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .pac-segments { flex-wrap: wrap; overflow-x: visible; }
  .seg { flex: 1 1 28%; min-width: 72px; white-space: normal; }
  .plan-nodes { flex-wrap: wrap; overflow-x: visible; }
  .plan-node { flex: 1 1 100%; }
  .welfare-remind { flex-wrap: wrap; }
  .welfare-remind > .el-button { margin-left: 38px; }
  .welfare-box { flex-direction: column; align-items: flex-start; }
  .danmaku-box { height: 300px; }
}
</style>
