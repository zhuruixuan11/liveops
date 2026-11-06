<template>
  <span class="intent-tag" :class="'intent-' + intent">{{ label }}</span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ intent: string }>()

const LABEL: Record<string, string> = {
  faq: '咨询', coupon: '要券', stock: '库存', human: '转人工', filter: '垃圾', general: '通用',
}
const label = computed(() => LABEL[props.intent] || props.intent)
</script>
