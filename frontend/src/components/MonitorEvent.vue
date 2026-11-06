<template>
  <div class="monitor-event">
    <div v-if="items.length === 0" style="color:#909399;font-size:13px;padding:8px">暂无监控事件</div>
    <div v-for="(e, i) in items" :key="i" class="monitor-line">
      <div>
        <el-tag :type="levelType(e.level)" size="small" effect="light">{{ e.level }}</el-tag>
        <span style="margin-left:6px;font-weight:600">{{ e.title || e.type }}</span>
      </div>
      <div v-if="e.detail" style="margin-top:3px;color:#606266">{{ e.detail }}</div>
      <div v-if="e.ts" style="color:#909399;font-size:11px;margin-top:2px">{{ fmt(e.ts) }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ items: Array<{ level?: string; type?: string; title?: string; detail?: string; ts?: number | string }> }>()

function levelType(l?: string): 'success' | 'warning' | 'danger' | 'info' {
  if (l === 'CRITICAL' || l === 'ERROR') return 'danger'
  if (l === 'WARN') return 'warning'
  if (l === 'INFO') return 'success'
  return 'info'
}

function fmt(ts?: number | string) {
  if (!ts) return ''
  const d = typeof ts === 'number' ? new Date(ts) : new Date(ts)
  if (isNaN(d.getTime())) return String(ts)
  return d.toLocaleTimeString('zh-CN', { hour12: false })
}
</script>
