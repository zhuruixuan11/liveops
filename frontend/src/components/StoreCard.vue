<template>
  <div class="store-card" @click="$emit('click')">
    <div class="store-head">
      <div class="name">{{ store.name }}</div>
      <el-tag :type="statusTag" size="small">{{ statusLabel }}</el-tag>
    </div>
    <div class="city text-sm text-muted mt-8">
      <el-icon><Location /></el-icon>
      {{ store.city }}<span v-if="store.address"> · {{ store.address }}</span>
    </div>
    <div v-if="store.phone" class="phone text-sm text-muted mt-8">
      <el-icon><Phone /></el-icon> {{ store.phone }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Store } from '../types'

const props = defineProps<{ store: Store }>()
defineEmits<{ (e: 'click'): void }>()

const statusLabel = computed(() => {
  switch (props.store.status) {
    case 'opening': return '营业中'
    case 'opening_soon': return '即将营业'
    default: return '已歇业'
  }
})
const statusTag = computed(() => {
  switch (props.store.status) {
    case 'opening': return 'success'
    case 'opening_soon': return 'warning'
    default: return 'info'
  }
})
</script>

<style scoped>
.store-card {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 14px 16px;
  background: #fff;
  cursor: pointer;
  transition: all .2s;
}
.store-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.08); transform: translateY(-2px); }
.store-head { display: flex; justify-content: space-between; align-items: center; }
.name { font-weight: 600; font-size: 15px; }
.city, .phone { display: flex; align-items: center; gap: 4px; }
</style>
