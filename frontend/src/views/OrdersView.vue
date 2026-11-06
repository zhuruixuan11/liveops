<template>
  <el-card>
    <el-form inline :model="q" @submit.prevent="load">
      <el-form-item label="状态">
        <el-select v-model="q.status" clearable placeholder="全部" style="width:140px">
          <el-option label="待支付" value="01" />
          <el-option label="已支付" value="02" />
          <el-option label="已取消" value="03" />
          <el-option label="已完成" value="07" />
        </el-select>
      </el-form-item>
      <el-form-item label="门店">
        <el-select v-model="q.store_id" clearable placeholder="全部门店" style="width:180px">
          <el-option v-for="s in stores" :key="s.store_id" :label="s.name" :value="s.store_id" />
        </el-select>
      </el-form-item>
      <el-form-item><el-button type="primary" @click="load">查询</el-button></el-form-item>
    </el-form>

    <el-table :data="items" stripe size="small" v-loading="loading">
      <el-table-column prop="order_id" label="订单号" width="220" show-overflow-tooltip />
      <el-table-column label="来源" width="100" align="center">
        <template #default="{ row }">
          <el-tag size="small" :type="channelType(row.channel)" effect="plain">{{ channelLabel(row.channel) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="门店" width="140">
        <template #default="{ row }">{{ storeName(row.store_id) }}</template>
      </el-table-column>
      <el-table-column label="原价" width="100" align="right">
        <template #default="{ row }">¥{{ money(row.total_amount) }}</template>
      </el-table-column>
      <el-table-column label="优惠" width="90" align="right">
        <template #default="{ row }">-¥{{ money(row.discount_amount) }}</template>
      </el-table-column>
      <el-table-column label="实付" width="110" align="right">
        <template #default="{ row }">
          <span class="pay-amount">¥{{ money(row.pay_amount) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="支付状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag size="small" :type="statusType(row.status)" effect="plain">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="170">
        <template #default="{ row }">{{ fmt(row.create_time) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="90" align="center">
        <template #default="{ row }">
          <router-link :to="`/orders/${row.order_id}`"><el-button size="small" text>详情</el-button></router-link>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap">
      <el-pagination v-model:current-page="q.page" v-model:page-size="q.size"
        :total="total" layout="prev, pager, next, total" @current-change="load" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import api from '@/api'

const q = reactive({ page: 1, size: 20, status: '', store_id: undefined as number | undefined })
const items = ref<any[]>([])
const stores = ref<any[]>([])
const total = ref(0)
const loading = ref(false)

const STATUS = {
  '01': { label: '待支付', type: 'warning' },
  '02': { label: '已支付', type: 'success' },
  '03': { label: '已取消', type: 'info' },
  '07': { label: '已完成', type: 'success' },
} as const

function statusLabel(s: string) { return (STATUS as any)[s]?.label || s }
function statusType(s: string) { return ((STATUS as any)[s]?.type || 'info') as any }
function channelLabel(c: string) {
  return { LIVE: '直播间', STORE_PICKUP: '门店自提', DOUYIN: '抖音', KUAISHOU: '快手', WECHAT_CHANNEL: '视频号' }[c] || c
}
function channelType(c: string) {
  return c === 'DOUYIN' ? 'danger' : c === 'KUAISHOU' ? 'warning' : c === 'LIVE' ? 'primary' : 'info'
}
function money(v: any) { return Number(v ?? 0).toFixed(2) }
function fmt(t: string) { return t ? t.replace('T', ' ').slice(0, 19) : '-' }
function storeName(id: number) { return stores.value.find((s) => s.store_id === id)?.name || (id ? `门店#${id}` : '-') }

async function load() {
  loading.value = true
  try {
    const params: any = { page: q.page, size: q.size }
    if (q.status) params.status = q.status
    if (q.store_id) params.store_id = q.store_id
    const r: any = await api.listOrders(params)
    items.value = r?.items || []
    total.value = r?.total ?? items.value.length
  } catch { /* noop */ }
  finally { loading.value = false }
}

onMounted(async () => {
  load()
  try {
    const r: any = await api.listStores({ size: 100 })
    stores.value = r?.items || r || []
  } catch { /* noop */ }
})
</script>

<style scoped>
.pay-amount { color: #f56c6c; font-weight: 700; }
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 12px; }
</style>
