<template>
  <div class="danmaku-stream">
    <div v-if="items.length === 0" style="color:#909399;font-size:13px;padding:8px">等待弹幕…</div>
    <div
      v-for="(m, i) in items"
      :key="i"
      class="danmaku-line"
      :class="{ 'ai-line': isAI(m.username) }"
      :style="{ background: m.highlight ? '#ecf5ff' : undefined }"
    >
      <span v-if="isAI(m.username)" class="ai-tag">AI</span>
      <span v-else-if="m.handled_by === 'HUMAN'" class="human-tag">人工</span>
      <span :class="{ 'ai-name': isAI(m.username) }" style="font-weight:600">{{ displayName(m.username) }}</span>
      <span style="margin-left:6px">{{ m.content }}</span>
      <IntentTag v-if="m.intent && !isAI(m.username)" :intent="m.intent" />
      <el-button
        v-if="actionable && m.msg_id && !isAI(m.username) && m.nickname !== '主播'"
        class="reply-btn" size="small" text type="primary"
        @click="emit('reply', m)"
      >人工回复</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import IntentTag from './IntentTag.vue'

defineProps<{
  items: Array<{
    msg_id?: number; username?: string; nickname?: string
    content: string; intent?: string; highlight?: boolean; handled_by?: string
  }>
  actionable?: boolean
}>()
const emit = defineEmits<{ (e: 'reply', item: any): void }>()

function isAI(name?: string) {
  return Boolean(name && (name.includes('AI助理') || name.startsWith('🤖')))
}
function displayName(name?: string) {
  if (!name) return '观众'
  if (name.startsWith('🤖')) return name.slice(2).trim()
  return name
}
</script>

<style scoped>
.danmaku-line { padding: 3px 6px; border-radius: 4px; font-size: 13px; line-height: 1.6; }
.ai-line { background: linear-gradient(90deg, #f0f9eb 0%, transparent 100%); }
.ai-tag {
  display: inline-block; background: #67c23a; color: #fff; font-size: 10px;
  border-radius: 3px; padding: 0 4px; margin-right: 4px; vertical-align: 1px;
}
.ai-name { color: #67c23a !important; }
.human-tag {
  display: inline-block; background: #3b6ef5; color: #fff; font-size: 10px;
  border-radius: 3px; padding: 0 4px; margin-right: 4px; vertical-align: 1px;
}
.reply-btn {
  height: 20px; padding: 0 6px; margin-left: 8px; font-size: 12px;
  opacity: 0; transition: opacity .15s ease;
}
.danmaku-line:hover .reply-btn { opacity: 1; }
</style>
