<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">📈 销售看板</div>
        <div class="page-sub">近 7 天成交概览 · 门店 GMV 排行与异常提醒</div>
      </div>
    </div>

    <el-row :gutter="16">
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

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :xs="24" :md="16">
        <el-card>
          <template #header>门店 GMV 排行 TOP 10</template>
          <div ref="chartRef" style="height:320px"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card>
          <template #header>
            <div class="card-head">
              <b>异常门店</b>
              <span class="anomaly-tip">点门店看明细</span>
            </div>
          </template>
          <el-empty v-if="anomalies.length===0" description="暂无异常门店，可点左侧排行柱查看门店明细" :image-size="70" />
          <div
            v-for="a in anomalies" :key="a.storeId"
            class="anomaly-row" @click="openStore(a)"
          >
            <div><b>{{ a.storeName || a.storeId }}</b>
              <el-tag :type="a.level==='CRITICAL'?'danger':'warning'" size="small" style="margin-left:4px">{{ a.level }}</el-tag>
              <span class="anomaly-arrow">→</span>
            </div>
            <div class="anomaly-reason">{{ a.reason || a.detail }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="storeDialog" :title="`门店明细 · ${storeDetail?.name || selected?.storeName || ''}`" width="720px">
      <div v-loading="storeLoading">
        <div class="store-meta">
          <span>城市：{{ storeDetail?.city || '—' }}</span>
          <span>店长：{{ storeDetail?.manager || '—' }}</span>
          <span>历史场次：{{ storeDetail?.live_session_count ?? '—' }}</span>
          <span>员工数：{{ storeDetail?.staff_count ?? '—' }}</span>
        </div>
        <el-alert
          v-if="selected && (selected.reason || selected.detail)" type="warning" :closable="false" show-icon
          :title="selected.reason || selected.detail" style="margin-bottom:12px"
        />
        <el-table :data="storeSessions" size="small" stripe>
          <el-table-column prop="session_id" label="ID" width="60" />
          <el-table-column prop="title" label="场次" show-overflow-tooltip />
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag size="small" effect="plain" :type="row.status === 'living' ? 'success' : 'info'">
                {{ statusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="开播时间" width="150">
            <template #default="{ row }">{{ fmt(row.start_time) }}</template>
          </el-table-column>
          <el-table-column label="GMV" width="110" align="right">
            <template #default="{ row }">¥{{ Number(row.gmv || 0).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center">
            <template #default="{ row }">
              <router-link :to="`/live/${row.session_id}`">
                <el-button size="small" text type="primary">进入</el-button>
              </router-link>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!storeLoading && storeSessions.length === 0" description="该门店暂无直播场次" :image-size="60" />
      </div>
      <template #footer>
        <router-link to="/live-sessions"><el-button size="small">查看全部场次</el-button></router-link>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import * as echarts from 'echarts'
import api from '@/api'

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null
const overview = ref<any>({})
const rank = ref<any[]>([])
const anomalies = ref<any[]>([])

const kpis = computed(() => [
  { label: '近 7 天 GMV', value: `¥${Number(overview.value.gmv || 0).toFixed(2)}`, icon: '💰', color: '#16a34a', bg: 'rgba(34,197,94,.12)' },
  { label: '近 7 天订单数', value: overview.value.orders ?? '-', icon: '🧾', color: '#1f2430', bg: 'rgba(59,110,245,.12)' },
  { label: '客单价', value: `¥${Number(overview.value.aov || 0).toFixed(2)}`, icon: '📊', color: '#3b6ef5', bg: 'rgba(59,110,245,.12)' },
  { label: '开播场次', value: overview.value.sessions ?? '-', icon: '🎥', color: '#f59e0b', bg: 'rgba(245,158,11,.14)' },
])

const storeDialog = ref(false)
const storeLoading = ref(false)
const storeDetail = ref<any>(null)
const storeSessions = ref<any[]>([])
const selected = ref<any>(null)

function statusLabel(s: string) {
  return ({ living: '直播中', planned: '未开始', ended: '已结束', cancelled: '已取消' } as any)[s] || s
}
function fmt(d: any) {
  if (!d) return '-'
  return String(d).replace('T', ' ').slice(0, 16)
}

async function openStore(a: any) {
  selected.value = a
  storeDialog.value = true
  storeLoading.value = true
  storeDetail.value = null
  storeSessions.value = []
  try { storeDetail.value = await api.getStore(Number(a.storeId)) } catch { /* noop */ }
  try {
    const r: any = await api.listLiveSessions({ store_id: a.storeId, size: 20 })
    storeSessions.value = r?.items || []
  } catch { /* noop */ }
  storeLoading.value = false
}

function renderChart() {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  const narrow = (chartRef.value?.clientWidth || 999) < 460
  chart.setOption({
    tooltip: {},
    grid: { top: 10, bottom: 40, left: narrow ? 78 : 100, right: 56 },
    xAxis: {
      type: 'value',
      splitNumber: narrow ? 3 : 5,
      axisLabel: {
        color: '#9aa3b2',
        hideOverlap: true,
        formatter: (v: number) => (v >= 1000 ? `${v / 1000}k` : `${v}`),
      },
    },
    yAxis: {
      type: 'category',
      data: rank.value.map((r) => r.name || r.storeName).reverse(),
      axisLabel: { color: '#6b7280', width: narrow ? 64 : 88, overflow: 'truncate' },
    },
    series: [{
      type: 'bar', data: rank.value.map((r) => Number(r.gmv || 0)).reverse(),
      cursor: 'pointer',
      itemStyle: { color: '#409eff' },
      label: { show: true, position: 'right', formatter: (p: any) => (Number(p.value) >= 1000 ? `${(p.value / 1000).toFixed(1)}k` : `${p.value}`) },
    }],
  })
  chart.off('click')
  chart.on('click', (p: any) => {
    const s = rank.value[rank.value.length - 1 - p.dataIndex]
    if (s?.store_id) {
      openStore({
        storeId: s.store_id,
        storeName: s.store_name,
        level: 'WARNING',
        reason: `近 7 天 GMV ¥${Number(s.gmv || 0).toFixed(2)}，点击可查看门店最近场次`,
      })
    }
  })
}

onMounted(async () => {
  try {
    const [o, r, a]: any = await Promise.all([api.salesOverview(), api.storeRank({ topN: 10 }), api.anomalies()])
    overview.value = o?.summary || {}
    rank.value = (r?.items || r?.data || r || []).map((x: any) => ({ ...x, name: x.store_name, storeName: x.store_name }))
    anomalies.value = (a?.items || a?.data || a || []).map((x: any) => ({
      storeId: x.store_id,
      storeName: x.store_name || `门店#${x.store_id}`,
      level: Number(x.drop_percent) >= 50 ? 'CRITICAL' : 'WARNING',
      reason: `GMV 环比下降 ${x.drop_percent}%（当前 ¥${Number(x.current_revenue).toFixed(0)} / 上期 ¥${Number(x.previous_revenue).toFixed(0)}）`,
      detail: x.drop_percent,
    }))
    renderChart()
  } catch { /* noop */ }
})
</script>

<style scoped>
.anomaly-tip { font-size: 12px; color: var(--lo-text-muted); }
.anomaly-row {
  padding: 9px 8px; margin: 0 -8px; border-radius: 8px;
  border-bottom: 1px dashed var(--lo-border); cursor: pointer;
  transition: background .18s ease;
}
.anomaly-row:hover { background: var(--lo-primary-soft); }
.anomaly-arrow { float: right; color: var(--lo-text-muted); font-size: 12px; }
.anomaly-reason { color: var(--lo-text-sub); font-size: 12px; margin-top: 3px; }
.store-meta {
  display: flex; flex-wrap: wrap; gap: 8px 20px; font-size: 13px;
  color: var(--lo-text-sub); margin-bottom: 12px;
}
</style>
