<template>
  <div class="coupon-panel">
    <el-table :data="coupons" border size="small">
      <el-table-column prop="type" label="类型" width="100">
        <template #default="{ row }">{{ typeLabel(row.type) }}</template>
      </el-table-column>
      <el-table-column prop="threshold" label="门槛" width="90">
        <template #default="{ row }">¥{{ row.threshold }}</template>
      </el-table-column>
      <el-table-column prop="discount" label="优惠" width="90">
        <template #default="{ row }">{{ row.type === 'discount' ? `${row.discount / 10}折` : `¥${row.discount}` }}</template>
      </el-table-column>
      <el-table-column label="库存/已发" width="120">
        <template #default="{ row }">{{ row.stock }} / {{ row.issued }}</template>
      </el-table-column>
      <el-table-column label="有效期" min-width="200">
        <template #default="{ row }">
          {{ row.valid_from || '—' }} ~ {{ row.valid_to || '—' }}
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import type { Coupon } from '../types'
defineProps<{ coupons: Coupon[] }>()
function typeLabel(t: string) {
  return { discount: '折扣券', threshold: '满减券', cash: '现金券' }[t] || t
}
</script>
