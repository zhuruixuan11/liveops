<template>
  <div v-if="traffic">
    <!-- 头部 -->
    <div class="hero">
      <div>
        <div class="hero-title">{{ traffic.title }}</div>
        <div class="hero-sub">
          <el-tag :type="traffic.status === 'living' ? 'success' : 'info'" size="small" effect="dark">
            {{ traffic.status === 'living' ? '直播中' : '已结束' }}
          </el-tag>
          <span class="sub-text">每 {{ traffic.bucket_minutes }} 分钟一个统计点 · 在线人数为互动热度折算的估算值</span>
        </div>
      </div>
      <el-button plain @click="$router.back()">返回</el-button>
    </div>

    <!-- 关键指标 -->
    <el-row :gutter="16" style="margin:16px 0">
      <el-col :xs="12" :sm="8" :md="4" v-for="k in kpis" :key="k.label">
        <el-card class="kpi">
          <div class="kpi-value" :style="{ color: k.color }">{{ k.value }}</div>
          <div class="kpi-label">{{ k.label }}</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card class="kpi score-card">
          <div class="kpi-value" :style="{ color: scoreColor }">{{ review?.score ?? '-' }}</div>
          <div class="kpi-label">综合评分</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 曲线 -->
    <el-card style="margin-bottom:16px">
      <template #header><b>📈 流量与成交走势</b></template>
      <div ref="chartRef" style="height:320px"></div>
    </el-card>

    <el-row :gutter="16">
      <!-- 漏斗 -->
      <el-col :xs="24" :lg="10">
        <el-card class="full-h">
          <template #header><b>🔻 转化漏斗</b></template>
          <div v-for="(f, i) in traffic.funnel" :key="f.stage" class="funnel-row">
            <div class="funnel-head">
              <span>{{ f.stage }}</span>
              <span class="funnel-num">{{ f.value }}</span>
            </div>
            <div class="funnel-bar" :style="{ width: funnelWidth(f.value), background: funnelColors[i] }"></div>
            <div v-if="i > 0 && traffic.funnel[i - 1].value" class="funnel-rate">
              转化 {{ rate(traffic.funnel[i - 1].value, f.value) }}%
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 复盘 -->
      <el-col :xs="24" :lg="14">
        <el-card class="full-h">
          <template #header>
            <div class="head-row">
              <b>🤖 本场复盘与建议</b>
              <el-tag size="small" type="info" effect="plain">基于本场弹幕/订单/告警自动生成</el-tag>
            </div>
          </template>
          <div class="review-block" v-if="review">
            <div class="rv-title ok">✅ 做得好的</div>
            <ul><li v-for="(h, i) in review.highlights" :key="i">{{ h }}</li></ul>
            <div class="rv-title warn" v-if="review.risks.length">⚠️ 需要改进</div>
            <ul><li v-for="(r, i) in review.risks" :key="'r' + i" class="risk">{{ r }}</li></ul>
            <div class="rv-title tip">💡 下一场怎么改</div>
            <ul><li v-for="(s, i) in review.suggestions" :key="'s' + i">{{ s }}</li></ul>
          </div>
          <el-empty v-else description="暂无复盘数据" :image-size="80" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 下一场规划 -->
    <el-card style="margin-top:16px" v-if="review?.next_plan">
      <template #header><b>🗓️ 下一场直播规划建议</b></template>
      <div class="plan-start">建议开播时间：<el-tag type="success" effect="dark">{{ review.next_plan.suggested_start }}</el-tag></div>
      <el-steps direction="vertical" :active="review.next_plan.structure.length" style="margin-top:16px">
        <el-step v-for="(s, i) in review.next_plan.structure" :key="i" :title="s" />
      </el-steps>
      <div class="focus-intents" v-if="review.next_plan.focus_intents?.length">
        重点关注弹幕类型：
        <el-tag v-for="t in review.next_plan.focus_intents" :key="t" size="small" style="margin-right:6px">{{ t }}</el-tag>
      </div>
    </el-card>
  </div>
  <el-empty v-else description="加载中…" />
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import api from '@/api'

const route = useRoute()
const sessionId = Number(route.params.id)
const traffic = ref<any>(null)
const review = ref<any>(null)
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null
let timer: any = null

const funnelColors = ['#8fa8ff', '#5eead4', '#f6a547', '#f5576c']

const kpis = computed(() => {
  const s = traffic.value?.summary
  if (!s) return []
  return [
    { label: '峰值在线', value: s.peak_viewer, color: '#409eff' },
    { label: '互动条数', value: s.interactions, color: '#67c23a' },
    { label: '支付订单', value: s.paid_orders, color: '#e6a23c' },
    { label: 'GMV', value: '¥' + Number(s.gmv).toFixed(0), color: '#f56c6c' },
    { label: '转化率', value: s.conversion_rate + '%', color: '#909399' },
  ]
})

const scoreColor = computed(() => {
  const v = review.value?.score ?? 0
  return v >= 80 ? '#67c23a' : v >= 60 ? '#e6a23c' : '#f56c6c'
})

function rate(prev: number, cur: number) {
  return ((cur / prev) * 100).toFixed(1)
}
function funnelWidth(v: number) {
  const max = traffic.value?.funnel?.[0]?.value || 1
  return Math.max(6, (v / max) * 100) + '%'
}

function renderChart() {
  if (!chartRef.value || !traffic.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  const b = traffic.value.buckets
  const narrow = (chartRef.value?.clientWidth || 999) < 460
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: narrow
      ? { left: 0, top: 0, itemWidth: 10, itemHeight: 8, itemGap: 8, textStyle: { fontSize: 10 } }
      : { right: 10 },
    grid: { left: narrow ? 44 : 50, right: narrow ? 40 : 50, top: narrow ? 42 : 40, bottom: 30 },
    xAxis: {
      type: 'category',
      data: b.map((x: any) => x.time),
      boundaryGap: false,
      axisLabel: { color: '#9aa3b2', interval: narrow ? Math.max(1, Math.ceil(b.length / 4)) : 'auto' },
    },
    yAxis: [
      { type: 'value', name: narrow ? '' : '在线', axisLabel: { color: '#9aa3b2' } },
      { type: 'value', name: narrow ? '' : '互动/单', splitLine: { show: false }, axisLabel: { color: '#9aa3b2' } },
    ],
    series: [
      {
        name: '预估在线', type: 'line', smooth: true, data: b.map((x: any) => x.online_est),
        areaStyle: { opacity: 0.18 }, lineStyle: { width: 2 }, itemStyle: { color: '#409eff' },
      },
      {
        name: '互动条数', type: 'bar', yAxisIndex: 1, data: b.map((x: any) => x.interactions),
        itemStyle: { color: '#5eead4' }, barMaxWidth: 10,
      },
      {
        name: '成交单数', type: 'bar', yAxisIndex: 1, data: b.map((x: any) => x.orders),
        itemStyle: { color: '#f5576c' }, barMaxWidth: 10,
      },
    ],
  })
}

async function load() {
  try {
    const [t, r] = await Promise.all([
      api.sessionTraffic(sessionId) as any,
      api.sessionReview(sessionId) as any,
    ])
    traffic.value = t
    review.value = r
    await nextTick()
    renderChart()
  } catch { /* noop */ }
}

function onResize() { chart?.resize() }

onMounted(() => {
  load()
  window.addEventListener('resize', onResize)
  timer = setInterval(load, 8000)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  if (timer) clearInterval(timer)
  chart?.dispose()
})
</script>

<style scoped>
.hero {
  background: linear-gradient(120deg, #1e3c72 0%, #2a5298 60%, #4a7bc8 100%);
  border-radius: 12px; padding: 18px 24px; color: #fff;
  display: flex; justify-content: space-between; align-items: center;
}
.hero-title { font-size: 20px; font-weight: 700; }
.hero-sub { display: flex; align-items: center; gap: 10px; margin-top: 8px; }
.sub-text { font-size: 12px; opacity: 0.78; }

.kpi { text-align: center; }
.kpi :deep(.el-card__body) { padding: 14px; }
.kpi-value { font-size: 22px; font-weight: 700; }
.kpi-label { font-size: 12px; color: #909399; margin-top: 4px; }
.score-card { background: #fbfdff; }

.full-h { height: 100%; }
.head-row { display: flex; justify-content: space-between; align-items: center; }

.funnel-row { margin-bottom: 14px; }
.funnel-head { display: flex; justify-content: space-between; font-size: 13px; color: #303133; margin-bottom: 4px; }
.funnel-num { font-weight: 700; }
.funnel-bar { height: 14px; border-radius: 7px; transition: width 0.4s; }
.funnel-rate { font-size: 11px; color: #909399; margin-top: 2px; }

.review-block ul { margin: 4px 0 12px; padding-left: 20px; }
.review-block li { color: #606266; font-size: 13px; line-height: 1.9; }
.review-block li.risk { color: #e6a23c; }
.rv-title { font-weight: 700; font-size: 13px; margin-top: 6px; }
.rv-title.ok { color: #67c23a; }
.rv-title.warn { color: #e6a23c; }
.rv-title.tip { color: #409eff; }

.plan-start { font-size: 13px; color: #606266; }
.focus-intents { margin-top: 8px; font-size: 13px; color: #606266; }
</style>
