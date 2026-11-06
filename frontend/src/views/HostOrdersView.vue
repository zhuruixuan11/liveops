<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">📦 我的订单</div>
        <div class="page-sub">只显示你直播场次产生的订单，看得到顾客有没有付款</div>
      </div>
      <div class="head-actions">
        <el-radio-group v-model="status" size="small" @change="load">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button label="02">已支付</el-radio-button>
          <el-radio-button label="01">待支付</el-radio-button>
        </el-radio-group>
        <el-button :icon="Refresh" circle @click="load" />
      </div>
    </div>

    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :xs="24" :sm="8" v-for="k in cards" :key="k.label">
        <el-card class="stat-card">
          <div class="stat-value" :style="{ color: k.color }">{{ k.value }}</div>
          <div class="stat-label">{{ k.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <el-table :data="items" stripe size="small" v-loading="loading">
        <el-table-column prop="order_id" label="订单号" width="190" />
        <el-table-column prop="session_id" label="场次" width="80" align="center">
          <template #default="{ row }">#{{ row.session_id }}</template>
        </el-table-column>
        <el-table-column label="支付状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="statusType(row.status)" effect="plain">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="应付" width="120" align="right">
          <template #default="{ row }">¥{{ Number(row.total_amount || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="实付" width="120" align="right">
          <template #default="{ row }">¥{{ Number(row.pay_amount || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="下单时间" min-width="160">
          <template #default="{ row }">{{ fmt(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="支付时间" min-width="160">
          <template #default="{ row }">
            <span v-if="row.pay_time">{{ fmt(row.pay_time) }}</span>
            <span v-else class="muted">顾客未支付</span>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !items.length" description="你的场次还没有订单" :image-size="80" />
      <div class="pager">
        <el-pagination
          v-model:current-page="page" :page-size="size" :total="total"
          layout="prev, pager, next, total" background @current-change="load"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const size = 20
const status = ref('')
const loading = ref(false)

const cards = computed(() => {
  const paid = items.value.filter((o) => o.status === '02' || o.status === '07')
  const gmv = paid.reduce((sum, o) => sum + Number(o.pay_amount || 0), 0)
  return [
    { label: '本页订单', value: items.value.length, color: '#409eff' },
    { label: '已支付', value: paid.length, color: '#67c23a' },
    { label: '本页成交额', value: `¥${gmv.toFixed(2)}`, color: '#e6a23c' },
  ]
})

function statusType(s: string): 'success' | 'info' | 'warning' | 'danger' {
  if (s === '02' || s === '07') return 'success'
  if (s === '01') return 'warning'
  return 'info'
}
function statusLabel(s: string) {
  return { '01': '待支付', '02': '已支付', '03': '已取消', '07': '已完成' }[s] || s
}
function fmt(d: any) {
  if (!d) return '-'
  return String(d).replace('T', ' ').slice(0, 16)
}

async function load() {
  loading.value = true
  try {
    const params: any = { host_id: auth.user?.staff_id, page: page.value, size }
    if (status.value) params.status = status.value
    const r: any = await api.listOrders(params)
    items.value = r?.items || []
    total.value = r?.total ?? items.value.length
  } catch {
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.head-actions { display: flex; align-items: center; gap: 10px; }
.stat-card :deep(.el-card__body) { padding: 16px 18px; }
.stat-value { font-size: 24px; font-weight: 700; line-height: 1.2; font-variant-numeric: tabular-nums; }
.stat-label { font-size: 12px; color: var(--lo-text-sub); margin-top: 4px; }
.muted { color: #c0c4cc; font-size: 12px; }
.pager { display: flex; justify-content: flex-end; margin-top: 12px; }
</style>
