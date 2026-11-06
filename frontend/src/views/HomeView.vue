<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">📊 首页概览</div>
        <div class="page-sub">门店直播全局态势 · 数据实时取自业务库</div>
      </div>
      <el-button :icon="Refresh" circle :loading="loading" @click="load" />
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :sm="12" :md="6" v-for="kpi in kpis" :key="kpi.label">
        <div class="kpi-card">
          <div class="kpi-icon" :style="{ background: kpi.bg }">{{ kpi.icon }}</div>
          <div>
            <div class="kpi-value" :style="{ color: kpi.color }">{{ kpi.value }}</div>
            <div class="kpi-label">{{ kpi.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-card class="trend-card">
      <template #header>
        <div class="card-head">
          <b>今日成交趋势（按小时）</b>
          <span class="trend-total">
            今日 GMV ¥{{ Number(intraday.total_gmv || 0).toFixed(2) }} · {{ intraday.total_orders ?? 0 }} 单
          </span>
        </div>
      </template>
      <div ref="chartRef" style="height:210px"></div>
    </el-card>

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :xs="24" :md="16">
        <el-card>
          <template #header>
            <div class="card-head">
              <b>最近直播场次</b>
              <router-link to="/live-sessions"><el-button size="small" text type="primary">全部场次 →</el-button></router-link>
            </div>
          </template>
          <el-table :data="sessions" size="small" stripe v-loading="loading">
            <el-table-column prop="session_id" label="ID" width="60" />
            <el-table-column prop="store_name" label="门店" show-overflow-tooltip />
            <el-table-column prop="host_name" label="主播" width="100" />
            <el-table-column prop="title" label="标题" show-overflow-tooltip />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="statusTag(row.status)" size="small" effect="dark">{{ statusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="viewer_count" label="在线" width="80" align="center" />
            <el-table-column label="GMV" width="110" align="right">
              <template #default="{ row }">¥{{ Number(row.gmv || 0).toFixed(2) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="110" align="center">
              <template #default="{ row }">
                <router-link :to="`/live/${row.session_id}`">
                  <el-button size="small" type="primary" plain round>进入直播间</el-button>
                </router-link>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!loading && sessions.length === 0" description="暂无直播场次" :image-size="70" />
        </el-card>
      </el-col>

      <el-col :xs="24" :md="8">
        <el-card>
          <template #header>
            <div class="card-head">
              <b>门店 GMV 排行 TOP 5</b>
              <router-link to="/dashboard"><el-button size="small" text type="primary">看板 →</el-button></router-link>
            </div>
          </template>
          <div v-for="(s, i) in rank" :key="s.store_id" class="rank-row">
            <span class="rank-no" :class="i < 3 ? 'hot' : ''">{{ i + 1 }}</span>
            <div class="rank-main">
              <div class="rank-name">{{ s.store_name }}</div>
              <div class="rank-sub">{{ s.city || '—' }} · {{ s.orders }} 单</div>
            </div>
            <span class="rank-gmv">¥{{ Number(s.gmv || 0).toFixed(0) }}</span>
          </div>
          <el-empty v-if="rank.length === 0" description="暂无成交数据" :image-size="70" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '@/api'

const loading = ref(false)
const stats = ref<any>({})
const sessions = ref<any[]>([])
const rank = ref<any[]>([])
const intraday = ref<any>({})
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

function renderChart() {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (ps: any[]) => {
        const p = ps[0]
        const o = intraday.value.orders?.[p.dataIndex] ?? 0
        return `${p.axisValue}<br/>GMV ¥${Number(p.value).toFixed(2)}<br/>订单 ${o} 单`
      },
    },
    grid: { top: 16, bottom: 28, left: 56, right: 20 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: intraday.value.hours || [],
      axisLine: { lineStyle: { color: '#e5e9f0' } },
      axisLabel: {
        color: '#9aa3b2',
        interval: (chartRef.value?.clientWidth || 999) < 460 ? 5 : 3,
      },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#9aa3b2', formatter: (v: number) => (v >= 1000 ? `${v / 1000}k` : v) },
      splitLine: { lineStyle: { color: '#f0f2f7' } },
    },
    series: [{
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 5,
      data: intraday.value.gmv || [],
      lineStyle: { width: 2.5, color: '#3b6ef5' },
      itemStyle: { color: '#3b6ef5' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(59,110,245,.28)' },
          { offset: 1, color: 'rgba(59,110,245,.02)' },
        ]),
      },
    }],
  })
}

function onResize() { chart?.resize() }

const kpis = computed(() => [
  { label: '门店总数', value: stats.value.store_count ?? '-', icon: '🏬', bg: 'linear-gradient(135deg,#a6c1ee,#89b4fa)', color: '#409eff' },
  { label: `直播中场次（在线 ${stats.value.online_viewers ?? 0}）`, value: stats.value.living_count ?? '-', icon: '🔴', bg: 'linear-gradient(135deg,#fbc2eb,#f5576c)', color: '#f56c6c' },
  { label: '近 7 天 GMV', value: stats.value.gmv_7d != null ? '¥' + Number(stats.value.gmv_7d).toFixed(2) : '-', icon: '💰', bg: 'linear-gradient(135deg,#a8edea,#5eead4)', color: '#67c23a' },
  { label: '近 7 天订单', value: stats.value.orders_7d ?? '-', icon: '🧾', bg: 'linear-gradient(135deg,#fddb92,#f6a547)', color: '#e6a23c' },
])

function statusTag(s: string): 'success' | 'info' | 'warning' | 'danger' {
  return ({ living: 'success', planned: 'warning', ended: 'info', cancelled: 'danger' } as any)[s] || 'info'
}
function statusLabel(s: string) {
  return { living: '直播中', planned: '未开始', ended: '已结束', cancelled: '已取消' }[s] || s
}

async function load() {
  loading.value = true
  try {
    const s: any = await api.homeStats()
    stats.value = s || {}
  } catch { stats.value = {} }

  try {
    const list: any = await api.listLiveSessions({ page: 1, size: 10 })
    sessions.value = list?.items || []
  } catch { sessions.value = [] }

  try {
    const r: any = await api.storeRank({ topN: 5 })
    rank.value = r?.items || []
  } catch { rank.value = [] }

  try {
    intraday.value = (await api.intradaySales()) || {}
    renderChart()
  } catch { /* noop */ }

  loading.value = false
}

onMounted(() => {
  load()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
})
</script>

<style scoped>
.rank-row {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 0; border-bottom: 1px dashed #ebeef5;
}
.rank-row:last-child { border-bottom: none; }
.rank-no {
  width: 22px; height: 22px; border-radius: 6px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; color: #909399; background: #f2f3f5;
}
.rank-no.hot { color: #fff; background: linear-gradient(135deg, #f6a547, #f5576c); }
.rank-main { flex: 1; min-width: 0; }
.rank-name { font-size: 13px; font-weight: 600; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rank-sub { font-size: 12px; color: #909399; margin-top: 2px; }
.rank-gmv { font-size: 13px; font-weight: 700; color: #16a34a; }
.trend-card { margin-top: 16px; }
.trend-total { font-size: 12px; color: var(--lo-text-sub); font-variant-numeric: tabular-nums; }
@media (max-width: 768px) {
  .trend-card :deep(.card-head) { flex-wrap: wrap; gap: 4px; }
}
</style>
