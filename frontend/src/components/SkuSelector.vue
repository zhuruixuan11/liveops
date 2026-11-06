<template>
  <div class="sku-selector">
    <div v-for="sk in groups" :key="sk.name" style="margin-bottom:8px">
      <div style="color:#606266;font-size:12px;margin-bottom:4px">{{ sk.name }}</div>
      <el-radio-group v-model="selected[sk.name]" size="small">
        <el-radio-button v-for="v in sk.values" :key="v" :label="v">{{ v }}</el-radio-button>
      </el-radio-group>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

interface SkuGroup { name: string; values: string[] }
const props = defineProps<{ groups: SkuGroup[]; modelValue?: Record<string, string> }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: Record<string, string>): void }>()

const selected = reactive<Record<string, string>>({})
watch(() => props.groups, (gs) => {
  gs.forEach((g) => { if (!selected[g.name]) selected[g.name] = g.values[0] })
}, { immediate: true })
watch(selected, (v) => emit('update:modelValue', { ...v }), { deep: true })
</script>
