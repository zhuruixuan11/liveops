<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">🏅 主播绩效</div>
        <div class="page-sub">按成交 GMV 排名，管理者可对比主播产能与转化效率</div>
      </div>
      <el-radio-group v-model="days" @change="load">
        <el-radio-button :value="7">近 7 天</el-radio-button>
        <el-radio-button :value="30">近 30 天</el-radio-button>
        <el-radio-button :value="90">近 90 天</el-radio-button>
      </el-radio-group>
    </div>

    <el-card>
      <el-table :data="items" stripe v-loading="loading">
        <el-table-column label="排名" width="80" align="center">
          <template #default="{ row }">
            <span class="rank" :class="'rank-' + row.rank">{{ row.rank }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="host_name" label="主播" width="140" />
        <el-table-column prop="store_name" label="所属门店" width="150" />
        <el-table-column prop="sessions" label="场次" width="80" align="center" />
        <el-table-column label="GMV" width="130" align="right" sortable prop="gmv">
          <template #default="{ row }"><span class="gmv">¥{{ row.gmv.toFixed(2) }}</span></template>
        </el-table-column>
        <el-table-column prop="orders" label="成交单" width="90" align="center" />
        <el-table-column label="客单价" width="100" align="right">
          <template #default="{ row }">¥{{ row.avg_ticket.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="avg_viewer" label="场均在线" width="100" align="center" />
        <el-table-column prop="peak_viewer" label="峰值在线" width="100" align="center" />
        <el-table-column label="转化率" width="110" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.conversion_rate >= 3 ? 'success' : row.conversion_rate >= 1.5 ? 'warning' : 'danger'">
              {{ row.conversion_rate }}%
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && items.length === 0" description="该时间段暂无主播数据" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api from '@/api'

const items = ref<any[]>([])
const loading = ref(false)
const days = ref(30)

async function load() {
  loading.value = true
  try {
    const r: any = await api.hostRank({ days: days.value })
    items.value = r?.items || []
  } catch { /* noop */ }
  finally { loading.value = false }
}

onMounted(load)
</script>

<style scoped>
.rank {
  display: inline-flex; width: 24px; height: 24px; border-radius: 50%;
  align-items: center; justify-content: center; font-weight: 700; font-size: 12px;
  background: #f0f2f5; color: #909399;
}
.rank-1 { background: linear-gradient(135deg, #ffd700, #ffb400); color: #fff; }
.rank-2 { background: linear-gradient(135deg, #cfd8dc, #90a4ae); color: #fff; }
.rank-3 { background: linear-gradient(135deg, #ffb088, #e07a4b); color: #fff; }
.gmv { color: #f56c6c; font-weight: 700; }
</style>
