<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">🧾 订单详情</div>
        <div class="page-sub">订单号 {{ o?.order_id || '-' }}</div>
      </div>
      <el-button @click="$router.back()">返回</el-button>
    </div>

    <el-card v-if="o" v-loading="loading">
      <template #header>
        <div class="card-head">
          <b>订单 {{ o.order_id }}</b>
          <el-tag :type="statusType(o.status)" effect="plain">{{ statusLabel(o.status) }}</el-tag>
        </div>
      </template>

      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="门店">{{ storeName(o.store_id) }}</el-descriptions-item>
        <el-descriptions-item label="来源">{{ channelLabel(o.channel) }}</el-descriptions-item>
        <el-descriptions-item label="原价">¥{{ money(o.total_amount) }}</el-descriptions-item>
        <el-descriptions-item label="优惠">-¥{{ money(o.discount_amount) }}</el-descriptions-item>
        <el-descriptions-item label="实付">
          <b class="pay-amount">¥{{ money(o.pay_amount) }}</b>
        </el-descriptions-item>
        <el-descriptions-item label="关联场次">{{ o.session_id ? `#${o.session_id}` : '-' }}</el-descriptions-item>
        <el-descriptions-item label="下单时间">{{ fmt(o.create_time) }}</el-descriptions-item>
        <el-descriptions-item label="支付时间">{{ fmt(o.pay_time) }}</el-descriptions-item>
      </el-descriptions>

      <div class="section-title">商品明细</div>
      <el-table :data="o.details || []" size="small" stripe>
        <el-table-column prop="product_name" label="商品" min-width="160" show-overflow-tooltip />
        <el-table-column prop="spec" label="规格" min-width="120" show-overflow-tooltip />
        <el-table-column label="单价" width="110" align="right">
          <template #default="{ row }">¥{{ money(row.price) }}</template>
        </el-table-column>
        <el-table-column prop="qty" label="数量" width="80" align="center" />
        <el-table-column label="小计" width="120" align="right">
          <template #default="{ row }"><b>¥{{ money(row.subtotal) }}</b></template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-else v-loading="loading">
      <el-empty description="订单不存在或已删除" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'

const route = useRoute()
const o = ref<any>(null)
const stores = ref<any[]>([])
const loading = ref(false)

const STATUS: Record<string, { label: string; type: string }> = {
  '01': { label: '待支付', type: 'warning' },
  '02': { label: '已支付', type: 'success' },
  '03': { label: '已取消', type: 'info' },
  '07': { label: '已完成', type: 'success' },
}
function statusLabel(s: string) { return STATUS[s]?.label || s || '-' }
function statusType(s: string) { return (STATUS[s]?.type || 'info') as any }
function channelLabel(c: string) {
  return ({ LIVE: '直播间', STORE_PICKUP: '门店自提', DOUYIN: '抖音', KUAISHOU: '快手', WECHAT_CHANNEL: '视频号' } as any)[c] || c || '-'
}
function money(v: any) { return Number(v ?? 0).toFixed(2) }
function fmt(t: string) { return t ? String(t).replace('T', ' ').slice(0, 19) : '-' }
function storeName(id: number) {
  return stores.value.find((s) => s.store_id === id)?.name || (id ? `门店#${id}` : '-')
}

onMounted(async () => {
  loading.value = true
  try { o.value = await api.getOrder(String(route.params.id)) } catch { o.value = null }
  try {
    const r: any = await api.listStores({ size: 100 })
    stores.value = r?.items || r || []
  } catch { /* noop */ }
  loading.value = false
})
</script>

<style scoped>
.pay-amount { color: #f56c6c; font-size: 16px; }
.section-title { font-weight: 700; margin: 18px 0 10px; font-size: 14px; }
</style>
