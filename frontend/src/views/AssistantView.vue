<template>
  <div class="assistant">
    <div class="hero">
      <div>
        <div class="hero-title">🤖 直播智能助手</div>
        <div class="hero-sub">
          给老板看数据，给主播排内容，给客服备话术 —— 全部基于本平台实时数据
        </div>
      </div>
      <div class="hero-badge">
        <div class="badge-num">{{ sessions.length }}</div>
        <div class="badge-label">可复盘场次</div>
      </div>
    </div>

    <el-tabs v-model="tab" class="tabs">
      <!-- ============ 一键查询 ============ -->
      <el-tab-pane label="一键查询" name="query">
        <el-card class="ask-card">
          <div class="chips">
            <el-button v-for="c in QUICK" :key="c" class="chip" size="small" round plain @click="ask(c)">
              {{ c }}
            </el-button>
          </div>
          <div class="ask-row">
            <el-input
              v-model="question" size="large" clearable
              placeholder="例如：近 7 天流水怎么样？哪个主播表现最好？哪些 SKU 快缺货了？"
              @keyup.enter="ask()"
            />
            <el-button type="primary" size="large" :loading="querying" @click="ask()">问一下</el-button>
          </div>
          <div class="ask-tip">支持问：主播排名 / 商品销量 / 库存预警 / 优惠券 / 流水趋势 / 订单概况 / 当前直播情况，可直接说“近 30 天”；闲聊、问候、问“你是谁”也能答</div>
        </el-card>

        <template v-if="result">
          <el-card class="answer-card">
            <div class="answer">
              <span class="bot">🤖</span>
              <div class="answer-text">{{ result.answer }}</div>
            </div>
            <div v-if="result.topic !== 'chat'" class="answer-meta">统计区间：近 {{ result.days }} 天 · 数据取自订单 / 弹幕 / 库存 / 券表</div>
          </el-card>

          <el-row v-if="result.table?.columns?.length" :gutter="16" style="margin-top:16px">
            <el-col :span="result.chart ? 12 : 24">
              <el-card class="full-h">
                <template #header><b>📋 明细数据</b></template>
                <el-table :data="tableRows" size="small" stripe max-height="360">
                  <el-table-column
                    v-for="(c, i) in result.table.columns" :key="i"
                    :prop="'c' + i" :label="c" show-overflow-tooltip
                  />
                </el-table>
                <el-empty v-if="!tableRows.length" description="暂无明细" :image-size="70" />
              </el-card>
            </el-col>
            <el-col v-if="result.chart" :span="12">
              <el-card class="full-h">
                <template #header><b>📈 图上看一眼</b></template>
                <div ref="chartRef" style="height:360px"></div>
              </el-card>
            </el-col>
          </el-row>
        </template>
        <el-empty v-else description="点上面的快捷问题，或直接输入你想查的数据" :image-size="90" />
      </el-tab-pane>

      <!-- ============ 直播规划 ============ -->
      <el-tab-pane label="直播规划" name="plan">
        <el-card>
          <el-form inline @submit.prevent="makePlan">
            <el-form-item label="推流平台">
              <el-select v-model="planForm.platform" style="width:140px">
                <el-option label="抖音" value="douyin" />
              </el-select>
            </el-form-item>
            <el-form-item label="参考场次">
              <el-select v-model="planForm.session_id" clearable placeholder="选一场做参考" style="width:260px">
                <el-option v-for="s in sessions" :key="s.session_id"
                  :label="`#${s.session_id} ${s.title}`" :value="s.session_id" />
              </el-select>
            </el-form-item>
            <el-form-item label="计划时长">
              <el-select v-model="planForm.duration_minutes" style="width:120px">
                <el-option v-for="m in [30, 45, 60, 90, 120]" :key="m" :label="m + ' 分钟'" :value="m" />
              </el-select>
            </el-form-item>
            <el-form-item label="主推方向">
              <el-input v-model="planForm.focus" placeholder="如：主推面霜 / 秋冬换季" style="width:220px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="planning" @click="makePlan">生成规划</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <template v-if="plan">
          <el-card v-if="plan.recommendations?.length" class="rec-card">
            <template #header>
              <div class="head-row">
                <b>✨ 本场内容推荐</b>
                <el-tag type="danger" effect="dark" size="small">主推：{{ plan.focus_product }}</el-tag>
              </div>
            </template>
            <div class="rec-list">
              <div v-for="(r, i) in plan.recommendations" :key="i" class="rec-item">
                <div class="rec-idx">{{ i + 1 }}</div>
                <div>
                  <div class="rec-title">{{ r.title }}</div>
                  <div class="rec-reason">{{ r.reason }}</div>
                  <div class="rec-action">→ {{ r.action }}</div>
                </div>
              </div>
            </div>
          </el-card>

          <el-card v-if="plan.platform_rules" class="rule-card">
            <template #header>
              <div class="head-row">
                <b>📡 {{ plan.platform }}推流规则（本次规划已按此排节奏）</b>
                <el-tag type="warning" effect="plain" size="small">
                  最佳时段：{{ plan.platform_rules.schedule?.best?.join(' / ') }}
                </el-tag>
              </div>
            </template>
            <el-row :gutter="16">
              <el-col :span="12">
                <div class="rule-block">
                  <div class="rule-title">🚦 流量推荐逻辑</div>
                  <div v-for="(t, i) in plan.platform_rules.algorithm" :key="'a' + i" class="rule-line">{{ t }}</div>
                </div>
                <div class="rule-block">
                  <div class="rule-title">🚀 冷启动动作（前 30 分钟）</div>
                  <div v-for="(t, i) in plan.platform_rules.cold_start" :key="'c' + i" class="rule-line">{{ t }}</div>
                </div>
                <div class="rule-block">
                  <div class="rule-title">⏱ 节奏限制</div>
                  <div v-for="(t, i) in plan.platform_rules.rhythm" :key="'r' + i" class="rule-line">{{ t }}</div>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="rule-block warn">
                  <div class="rule-title">🚫 合规红线</div>
                  <div v-for="(t, i) in plan.platform_rules.compliance" :key="'p' + i" class="rule-line">{{ t }}</div>
                </div>
                <div class="rule-block">
                  <div class="rule-title">🎁 福利发放建议</div>
                  <div v-for="(t, i) in plan.platform_rules.welfare" :key="'w' + i" class="rule-line">{{ t }}</div>
                </div>
                <el-alert
                  v-if="plan.platform_rules.schedule?.note"
                  :title="plan.platform_rules.schedule.note" type="info" :closable="false" show-icon
                  style="margin-top:8px"
                />
              </el-col>
            </el-row>
          </el-card>

          <el-row :gutter="16" style="margin-top:16px">
            <el-col :span="14">
              <el-card class="full-h">
                <template #header>
                  <div class="head-row">
                    <b>🕐 本场节奏脚本</b>
                    <el-tag type="danger" effect="dark" size="small">主推：{{ plan.focus_product }}</el-tag>
                  </div>
                </template>
                <el-timeline>
                  <el-timeline-item
                    v-for="(s, i) in plan.script" :key="i"
                    :timestamp="`${s.phase} · ${s.minutes} 分钟`"
                    :color="PHASE_COLORS[i % PHASE_COLORS.length]"
                    placement="top"
                  >
                    <div class="script-action">{{ s.action }}</div>
                  </el-timeline-item>
                </el-timeline>
              </el-card>
            </el-col>

            <el-col :span="10">
              <el-card style="margin-bottom:16px">
                <template #header><b>🔥 近期热点（可作为讲解切入点）</b></template>
                <div v-for="t in plan.hot_topics" :key="t.topic" class="topic-row">
                  <el-tag size="small" type="warning" effect="plain">{{ t.topic }}</el-tag>
                  <span class="topic-reason">{{ t.reason }}</span>
                </div>
              </el-card>

              <el-card style="margin-bottom:16px">
                <template #header><b>📦 近 14 天热销 & 库存风险</b></template>
                <div v-for="p in plan.hot_products" :key="p.name" class="hot-row">
                  <span class="hot-name">{{ p.name }}</span>
                  <span class="hot-num">{{ p.qty }} 件 · ¥{{ p.gmv }}</span>
                </div>
                <el-alert
                  v-for="p in plan.low_stock" :key="'ls' + p.name"
                  :title="`「${p.name}」库存仅 ${p.stock} 件`"
                  type="warning" :closable="false" show-icon style="margin-top:8px"
                />
                <el-empty v-if="!plan.hot_products.length" description="近 14 天暂无成交" :image-size="60" />
              </el-card>

              <el-card>
                <template #header><b>✅ 开播清单</b></template>
                <div v-for="(c, i) in plan.checklist" :key="i" class="check-row">
                  <span class="check-dot">✓</span><span>{{ c }}</span>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <el-card v-if="plan.risks.length" style="margin-top:16px">
            <template #header><b>⚠️ 风险提示</b></template>
            <el-alert v-for="(r, i) in plan.risks" :key="i" :title="r" type="warning"
              :closable="false" show-icon style="margin-bottom:8px" />
          </el-card>
        </template>
      </el-tab-pane>

      <!-- ============ 客服话术 ============ -->
      <el-tab-pane label="客服话术" name="reply">
        <el-card>
          <el-form inline>
            <el-form-item label="当前场次">
              <el-select v-model="replySession" clearable placeholder="选择场次" style="width:300px" @change="() => loadReplies(false)">
                <el-option v-for="s in sessions" :key="s.session_id"
                  :label="`#${s.session_id} ${s.title}`" :value="s.session_id" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button :loading="replyLoading" @click="loadReplies(false)">刷新话术</el-button>
            </el-form-item>
            <el-form-item v-if="ingestState">
              <el-tag :type="ingestState.connected ? 'success' : 'info'" effect="plain" size="small">
                采集器{{ ingestState.connected ? '在线' : '离线' }}
              </el-tag>
              <span class="ingest-note">今日已采集 {{ ingestState.today_count }} 条 · 过滤 {{ ingestState.filtered_count }} 条</span>
            </el-form-item>
          </el-form>
        </el-card>

        <div class="reply-list">
          <el-card v-for="r in replies" :key="r.msg_id" class="reply-card">
            <div class="reply-head">
              <span class="nick">{{ r.nickname }}</span>
              <el-tag size="small" effect="plain">{{ r.intent }}</el-tag>
              <el-tag v-if="r.need_human" size="small" type="danger" effect="dark">建议人工跟进</el-tag>
              <span class="time">#{{ r.msg_id }}</span>
            </div>
            <div class="question">{{ r.content }}</div>
            <div class="suggest">
              <span class="suggest-label">推荐回复</span>
              <span class="suggest-text">{{ r.suggested_reply }}</span>
              <el-button size="small" text type="primary" @click="copy(r.suggested_reply)">复制</el-button>
            </div>
          </el-card>
          <el-empty v-if="!replies.length" description="该场次暂无弹幕，或先启动采集器" :image-size="90" />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import api from '@/api'

const QUICK = [
  '近 7 天流水趋势',
  '哪个主播表现最好',
  '哪个商品卖得最好',
  '哪些 SKU 快缺货了',
  '优惠券发放情况',
  '近 30 天订单概况',
]
const PHASE_COLORS = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399']

const tab = ref('query')
const question = ref('')
const querying = ref(false)
const result = ref<any>(null)
const tableRows = ref<any[]>([])
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const sessions = ref<any[]>([])
const planning = ref(false)
const plan = ref<any>(null)
const planForm = reactive<any>({ session_id: undefined, duration_minutes: 60, focus: '', platform: 'douyin' })

const replySession = ref<number | undefined>(undefined)
const replyLoading = ref(false)
const replies = ref<any[]>([])
const ingestState = ref<any>(null)

async function ask(q?: string) {
  const text = (q ?? question.value).trim()
  if (!text) { ElMessage.warning('先输入你想查的问题'); return }
  question.value = text
  querying.value = true
  try {
    const r: any = await api.assistantQuery({ question: text })
    result.value = r
    tableRows.value = (r.table?.rows || []).map((row: any[]) => {
      const o: any = {}
      row.forEach((v, i) => { o['c' + i] = v })
      return o
    })
    await nextTick()
    renderChart()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '查询失败')
  } finally {
    querying.value = false
  }
}

function renderChart() {
  const c = result.value?.chart
  if (!c || !chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 30, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: c.x, axisLabel: { interval: 'auto', rotate: c.x.length > 8 ? 30 : 0 } },
    yAxis: { type: 'value' },
    series: [{
      name: c.name, type: c.type === 'line' ? 'line' : 'bar',
      data: c.y, smooth: true, barMaxWidth: 28,
      itemStyle: { color: '#409eff', borderRadius: c.type === 'bar' ? [4, 4, 0, 0] : 0 },
      areaStyle: c.type === 'line' ? { opacity: 0.16 } : undefined,
    }],
  }, true)
  chart.resize()
}

async function makePlan() {
  planning.value = true
  try {
    plan.value = await api.assistantPlan({ ...planForm })
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '生成失败')
  } finally {
    planning.value = false
  }
}

async function loadReplies(auto = false) {
  replyLoading.value = true
  try {
    let target = replySession.value
    if (auto) {
      // 首次进入时自动挑一场有弹幕的场次，避免落在空场次
      if (!sessions.value.length) {
        const r: any = await api.listLiveSessions({ size: 50 }).catch(() => null)
        sessions.value = r?.items || []
      }
      const ids = [...new Set([target, ...sessions.value.map((s: any) => s.session_id)])]
        .filter(Boolean) as number[]
      for (const sid of ids.slice(0, 6)) {
        const r: any = await api.assistantReplies(sid, 5)
        if (r?.items?.length) { target = sid; break }
      }
    }
    if (!target) { replies.value = []; return }
    replySession.value = target
    const [r, s]: any = await Promise.all([
      api.assistantReplies(target, 30),
      api.ingestStatus(target).catch(() => null),
    ])
    replies.value = r?.items || []
    ingestState.value = s
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载失败')
  } finally {
    replyLoading.value = false
  }
}

async function copy(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制，可直接粘贴到客服窗口')
  } catch {
    ElMessage.warning('浏览器不允许自动复制，请手动选择文本')
  }
}

function onResize() { chart?.resize() }

watch(tab, async (t) => {
  if (t === 'reply' && !replies.value.length) await loadReplies(true)
  if (t === 'query') { await nextTick(); chart?.resize() }
  if (t === 'plan') { await nextTick(); chart?.resize() }
})

onMounted(async () => {
  window.addEventListener('resize', onResize)
  try {
    const r: any = await api.listLiveSessions({ size: 50 })
    sessions.value = r?.items || []
    if (sessions.value.length) {
      const living = sessions.value.find((s: any) => s.status === 'living')
      replySession.value = (living || sessions.value[0]).session_id
    }
  } catch { /* noop */ }
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
})
</script>

<style scoped>
.hero {
  background: linear-gradient(120deg, #1e3c72 0%, #2a5298 55%, #5b8def 100%);
  border-radius: 12px; padding: 20px 24px; color: #fff;
  display: flex; justify-content: space-between; align-items: center;
  box-shadow: 0 6px 20px rgba(30, 60, 114, 0.25);
}
.hero-title { font-size: 21px; font-weight: 700; }
.hero-sub { font-size: 13px; opacity: 0.82; margin-top: 6px; }
.hero-badge { text-align: center; background: rgba(255, 255, 255, 0.12); padding: 8px 18px; border-radius: 10px; }
.badge-num { font-size: 26px; font-weight: 800; color: #5eead4; line-height: 1.1; }
.badge-label { font-size: 12px; opacity: 0.8; }

.tabs { margin-top: 16px; }
.ask-card { border-radius: 10px; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
.chip { transition: all 0.15s; }
.chip:hover { color: #409eff; border-color: #409eff; }
.ask-row { display: flex; gap: 10px; }
.ask-tip { font-size: 12px; color: #909399; margin-top: 8px; }

.answer-card { margin-top: 16px; background: #f7fbff; border-left: 4px solid #409eff; }
.answer { display: flex; gap: 12px; align-items: flex-start; }
.bot { font-size: 22px; }
.answer-text { font-size: 15px; line-height: 1.8; color: #303133; font-weight: 500; }
.answer-meta { font-size: 12px; color: #909399; margin-top: 8px; padding-left: 34px; }

.full-h { height: 100%; }
.head-row { display: flex; justify-content: space-between; align-items: center; }

.script-action { font-size: 13px; color: #303133; line-height: 1.7; }
.topic-row { display: flex; gap: 8px; align-items: flex-start; margin-bottom: 10px; }
.topic-reason { font-size: 12px; color: #606266; line-height: 1.6; }
.hot-row { display: flex; justify-content: space-between; font-size: 13px; padding: 5px 0; border-bottom: 1px dashed #ebeef5; }
.hot-name { color: #303133; }
.hot-num { color: #f56c6c; font-weight: 600; }
.check-row { display: flex; gap: 8px; font-size: 13px; color: #606266; line-height: 2; }
.check-dot { color: #67c23a; font-weight: 700; }

.rec-card { margin-top: 16px; border-left: 4px solid #e6a23c; }

.rule-card { margin-top: 16px; border-left: 4px solid #409eff; }
.rule-block { margin-bottom: 14px; }
.rule-block.warn { background: #fef0f0; border-radius: 8px; padding: 10px 12px; }
.rule-title { font-size: 13px; font-weight: 700; color: #303133; margin-bottom: 6px; }
.rule-line { font-size: 12px; color: #606266; line-height: 1.75; padding-left: 10px; position: relative; }
.rule-line::before {
  content: '·'; position: absolute; left: 0; color: #909399; font-weight: 700;
}
.rec-list { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.rec-item { display: flex; gap: 10px; background: #fdfaf4; border-radius: 8px; padding: 12px 14px; }
.rec-idx {
  width: 22px; height: 22px; border-radius: 50%; flex-shrink: 0;
  background: #e6a23c; color: #fff; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.rec-title { font-size: 14px; font-weight: 700; color: #303133; }
.rec-reason { font-size: 12px; color: #606266; margin-top: 4px; line-height: 1.6; }
.rec-action { font-size: 12px; color: #409eff; margin-top: 4px; }

.reply-list { margin-top: 16px; }
.reply-card { margin-bottom: 12px; }
.reply-head { display: flex; align-items: center; gap: 8px; }
.nick { font-weight: 700; color: #303133; }
.time { margin-left: auto; font-size: 12px; color: #c0c4cc; }
.question { font-size: 14px; color: #303133; margin: 10px 0; }
.suggest {
  display: flex; align-items: flex-start; gap: 8px;
  background: #f0f9eb; border-radius: 8px; padding: 10px 12px;
}
.suggest-label { font-size: 12px; color: #67c23a; font-weight: 700; white-space: nowrap; }
.suggest-text { font-size: 13px; color: #4b5563; line-height: 1.7; flex: 1; }
.ingest-note { font-size: 12px; color: #909399; margin-left: 8px; }
</style>
