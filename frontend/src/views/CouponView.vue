<template>
  <div>
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="6" v-for="k in cards" :key="k.label">
        <el-card class="stat-card">
          <div class="stat-value" :style="{ color: k.color }">{{ k.value }}</div>
          <div class="stat-label">{{ k.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header>
        <div class="head-row">
          <div>
            <b>优惠券</b>
            <span class="sub">按状态分组，看得到发放进度、剩余量和到期风险</span>
          </div>
          <div>
            <el-radio-group v-model="filter" size="small" style="margin-right:12px">
              <el-radio-button label="all">全部</el-radio-button>
              <el-radio-button label="active">可领取</el-radio-button>
              <el-radio-button label="sold_out">已抢完</el-radio-button>
              <el-radio-button label="expiring">7 天内到期</el-radio-button>
            </el-radio-group>
            <el-button type="primary" @click="dlg = true">新建优惠券</el-button>
          </div>
        </div>
      </template>

      <el-table :data="filtered" stripe size="small">
        <el-table-column prop="coupon_id" label="ID" width="60" />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="typeTag(row.type)" effect="plain">{{ typeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="面值/规则" min-width="150">
          <template #default="{ row }">{{ valueLabel(row) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="statusMeta(row.status).type" effect="dark">{{ statusMeta(row.status).label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="发放进度" width="170">
          <template #default="{ row }">
            <el-progress :percentage="percent(row)" :stroke-width="10" :color="progressColor(row)" />
            <div class="progress-text">{{ row.issued }} / {{ row.stock }}</div>
          </template>
        </el-table-column>
        <el-table-column label="剩余" width="80" align="center">
          <template #default="{ row }">
            <span :class="{ 'low-stock': row.remain > 0 && row.remain < 20 }">{{ row.remain }}</span>
          </template>
        </el-table-column>
        <el-table-column label="AI 发放" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.issued_agent" size="small" type="success" effect="plain">{{ row.issued_agent }}</el-tag>
            <span v-else class="muted">0</span>
          </template>
        </el-table-column>
        <el-table-column label="有效期" width="240">
          <template #default="{ row }">
            <div>{{ fmt(row.valid_start) }} ~ {{ fmt(row.valid_end) }}</div>
            <div v-if="nearExpiry(row)" class="expire-hint">
              {{ row.expire_days <= 0 ? '今天到期' : `还剩 ${row.expire_days} 天` }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button
              size="small" type="primary" plain round
              :disabled="row.status !== 'active'"
              @click="issueOne(row)"
            >发一张</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!filtered.length" description="没有符合条件的优惠券" :image-size="70" />
    </el-card>

    <el-dialog v-model="dlg" title="新建优惠券" width="460px">
      <el-form :model="f" label-width="90px">
        <el-form-item label="所属场次">
          <el-select v-model="f.session_id" placeholder="选择场次" style="width:100%">
            <el-option v-for="s in sessions" :key="s.session_id" :label="`#${s.session_id} ${s.title}`" :value="s.session_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="f.type">
            <el-option label="满减券" value="discount" />
            <el-option label="折扣券" value="percent" />
            <el-option label="包邮券" value="shipping" />
          </el-select>
        </el-form-item>
        <el-form-item label="门槛"><el-input-number v-model="f.threshold" :min="0" /></el-form-item>
        <el-form-item label="面值/折扣"><el-input-number v-model="f.discount" :min="0" :step="0.1" /></el-form-item>
        <el-form-item label="数量"><el-input-number v-model="f.count" :min="1" /></el-form-item>
        <el-form-item label="有效天数"><el-input-number v-model="f.days" :min="1" :max="365" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="createCoupon">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const items = ref<any[]>([])
const sessions = ref<any[]>([])
const stats = ref<any>({ total: 0, total_stock: 0, total_issued: 0, total_remain: 0, expiring_7d: 0, agent_issued: 0 })
const filter = ref('all')
const dlg = ref(false)
const f = reactive({ session_id: undefined as number | undefined, type: 'discount', threshold: 100, discount: 20, count: 100, days: 30 })

const cards = computed(() => [
  { label: '优惠券数量', value: stats.value.total, color: '#409eff' },
  { label: '累计发放', value: stats.value.total_issued, color: '#67c23a' },
  { label: '剩余可发', value: stats.value.total_remain, color: '#e6a23c' },
  { label: '7 天内到期', value: stats.value.expiring_7d, color: '#f56c6c' },
])

const filtered = computed(() => {
  const list = items.value
  if (filter.value === 'active') return list.filter((c) => c.status === 'active')
  if (filter.value === 'sold_out') return list.filter((c) => c.status === 'sold_out')
  if (filter.value === 'expiring') return list.filter(nearExpiry)
  return list
})

function typeLabel(t: string) {
  return { discount: '满减券', percent: '折扣券', shipping: '包邮券' }[t] || t
}
function typeTag(t: string) {
  return { discount: 'warning', percent: 'success', shipping: 'info' }[t] || ''
}
function valueLabel(row: any) {
  if (row.type === 'percent') return `${(Number(row.discount) * 10).toFixed(1)}折`
  if (row.type === 'discount') return `满¥${row.threshold} 减¥${row.discount}`
  if (row.type === 'shipping') return '包邮'
  return row.discount
}
function statusMeta(s: string): { label: string; type: any } {
  return {
    active: { label: '可领取', type: 'success' },
    upcoming: { label: '未开始', type: 'warning' },
    sold_out: { label: '已抢完', type: 'danger' },
    expired: { label: '已过期', type: 'info' },
  }[s] || { label: s, type: 'info' }
}
function percent(row: any) {
  if (!row.stock) return 0
  return Math.min(100, Math.round((Number(row.issued) / Number(row.stock)) * 100))
}
function progressColor(row: any) {
  if (percent(row) >= 90) return '#f56c6c'
  if (percent(row) >= 60) return '#e6a23c'
  return '#67c23a'
}
function nearExpiry(row: any) {
  return row.expire_days !== null && row.expire_days !== undefined && row.expire_days >= 0 && row.expire_days <= 7
}
function fmt(d: any) {
  if (!d) return '-'
  return String(d).replace('T', ' ').slice(0, 16)
}

async function load() {
  try {
    const r: any = await api.couponStats()
    items.value = r?.items || []
    stats.value = r || stats.value
  } catch { /* noop */ }
}

async function issueOne(row: any) {
  await ElMessageBox.confirm(
    `确认给当前场次发放一张「${valueLabel(row)}」？剩余 ${row.remain} 张。`,
    '发券确认',
  )
  try {
    await api.issueCoupon({ coupon_id: row.coupon_id, session_id: row.session_id })
    ElMessage.success('已发放 1 张')
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '发放失败')
  }
}

async function loadSessions() {
  try {
    const r: any = await api.listLiveSessions({ size: 100 })
    sessions.value = r?.items || []
  } catch { /* noop */ }
}

async function createCoupon() {
  if (!f.session_id) {
    ElMessage.warning('请先选择所属场次')
    return
  }
  const now = new Date()
  const end = new Date(now.getTime() + f.days * 86400000)
  try {
    await api.createCoupon({
      session_id: f.session_id,
      type: f.type,
      threshold: f.threshold,
      discount: f.discount,
      stock: f.count,
      valid_start: now.toISOString().slice(0, 19),
      valid_end: end.toISOString().slice(0, 19),
    })
    ElMessage.success('已创建')
    dlg.value = false
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '创建失败')
  }
}

onMounted(() => { load(); loadSessions() })
</script>

<style scoped>
.stat-card :deep(.el-card__body) { padding: 16px 18px; }
.stat-value { font-size: 26px; font-weight: 700; line-height: 1.2; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }
.head-row { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
.sub { font-size: 12px; color: #909399; margin-left: 10px; }
.progress-text { font-size: 11px; color: #909399; margin-top: 2px; }
.low-stock { color: #f56c6c; font-weight: 700; }
.muted { color: #c0c4cc; }
.expire-hint { font-size: 11px; color: #e6a23c; margin-top: 2px; }
</style>
