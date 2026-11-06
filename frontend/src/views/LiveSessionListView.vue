<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">📺 直播场次</div>
        <div class="page-sub">正在直播的门店实时可见 · 其余场次可进入回看数据</div>
      </div>
    </div>

    <el-card v-if="living.length" class="live-card">
      <template #header>
        <div class="head-row">
          <span><b>🔴 正在直播</b><el-tag type="danger" effect="dark" size="small" style="margin-left:8px">{{ living.length }} 场</el-tag></span>
          <span class="sub">这些门店现在就在播，点「进入直播间」可以看实时画面和弹幕</span>
        </div>
      </template>
      <el-table :data="living" stripe size="small" :row-class-name="() => 'living-row'">
        <el-table-column prop="store_name" label="门店" min-width="140" />
        <el-table-column prop="host_name" label="主播" width="100" />
        <el-table-column prop="title" label="标题" show-overflow-tooltip />
        <el-table-column label="开播时间" width="160">
          <template #default="{ row }">{{ fmt(row.start_time) }}</template>
        </el-table-column>
        <el-table-column prop="viewer_count" label="在线" width="80" align="center" />
        <el-table-column label="GMV" width="110" align="right">
          <template #default="{ row }">¥{{ (Number(row.gmv) || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <router-link :to="`/live/${row.session_id}`">
              <el-button size="small" type="primary" round>进入直播间</el-button>
            </router-link>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card>
      <template #header>
        <div class="head-row">
          <span><b>未在直播</b>（{{ others.length }} 场）</span>
          <span class="sub">未开始 / 已结束的场次，同样可以进入回看直播数据</span>
        </div>
      </template>
      <el-table :data="others" stripe size="small">
        <el-table-column prop="session_id" label="ID" width="60" />
        <el-table-column prop="store_name" label="门店" min-width="140" />
        <el-table-column prop="host_name" label="主播" width="100" />
        <el-table-column prop="title" label="标题" show-overflow-tooltip />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" effect="plain" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="开播时间" width="160">
          <template #default="{ row }">{{ fmt(row.start_time) }}</template>
        </el-table-column>
        <el-table-column label="GMV" width="110" align="right">
          <template #default="{ row }">¥{{ (Number(row.gmv) || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <router-link :to="`/live/${row.session_id}`">
              <el-button size="small" type="primary" plain round>进入直播间</el-button>
            </router-link>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!others.length" description="暂无其他场次" :image-size="70" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api from '@/api'

const items = ref<any[]>([])

const living = computed(() => items.value.filter((s) => s.status === 'living'))
const others = computed(() =>
  [...items.value.filter((s) => s.status !== 'living')].sort(
    (a, b) => String(b.start_time || '').localeCompare(String(a.start_time || '')),
  ),
)

function statusType(s: string): 'success' | 'info' | 'warning' | 'danger' {
  if (s === 'ended') return 'info'
  if (s === 'cancelled') return 'danger'
  return 'warning'
}
function statusLabel(s: string) {
  return { planned: '未开播', living: '进行中', ended: '已结束', cancelled: '已取消' }[s] || s
}
function fmt(d: any) {
  if (!d) return '-'
  return String(d).replace('T', ' ').slice(0, 16)
}

async function load() {
  try {
    const r: any = await api.listLiveSessions({ size: 100 })
    items.value = r?.items || r?.data || r || []
  } catch { /* noop */ }
}

onMounted(load)
</script>

<style scoped>
.live-card { margin-bottom: 16px; border-left: 4px solid #f43f5e !important; }
.head-row { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
.sub { color: var(--lo-text-muted); font-size: 12px; }
:deep(.living-row) { background: #fff7f7; }
</style>
