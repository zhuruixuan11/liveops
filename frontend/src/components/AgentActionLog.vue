<template>
  <div class="agent-action-log">
    <div v-if="items.length === 0" style="color:#909399;font-size:13px;padding:8px">暂无决策</div>
    <div v-for="(a, i) in items" :key="i" class="agent-log-line">
      <div><b style="color:#409eff">Agent</b> <span style="color:#909399">{{ fmt(a.ts) }}</span></div>
      <div style="margin-top:4px">{{ a.action || a.message || JSON.stringify(a) }}</div>
      <div v-if="a.reason" style="color:#606266;margin-top:2px">理由：{{ a.reason }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ items: Array<{ ts?: number | string; action?: string; message?: string; reason?: string }> }>()

function fmt(ts?: number | string) {
  if (!ts) return ''
  const d = typeof ts === 'number' ? new Date(ts) : new Date(ts)
  if (isNaN(d.getTime())) return String(ts)
  return d.toLocaleTimeString('zh-CN', { hour12: false })
}
</script>
