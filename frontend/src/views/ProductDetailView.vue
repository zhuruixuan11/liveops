<template>
  <div>
    <div v-if="p" class="control-layout" style="height:auto">
      <div style="flex:0 0 420px">
        <el-image :src="p.imageUrl" style="width:420px;height:420px;border-radius:8px" fit="cover" />
      </div>
      <div style="flex:1;padding:0 16px">
        <h2>{{ p.name }}</h2>
        <div style="color:#f56c6c;font-size:24px;font-weight:600;margin:12px 0">¥{{ Number(p.price).toFixed(2) }}</div>
        <div style="color:#909399">SKU：{{ p.skuCode }}</div>
        <div style="margin:12px 0">
          <SkuSelector v-if="skuGroups.length" v-model="selectedSku" :groups="skuGroups" />
        </div>
        <div style="margin:12px 0">
          <el-tag :type="p.stock>10?'success':p.stock>0?'warning':'danger'" size="large">
            库存 {{ p.stock }}
          </el-tag>
        </div>
        <el-descriptions v-if="p.description" :column="1" border size="small" style="margin-top:16px">
          <el-descriptions-item label="描述">{{ p.description }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </div>
    <el-empty v-else description="加载中…" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'
import SkuSelector from '@/components/SkuSelector.vue'

const route = useRoute()
const p = ref<any>(null)
const selectedSku = reactive<Record<string, string>>({})
const skuGroups = computed(() => {
  const g = p.value?.skuGroups
  return Array.isArray(g) ? g : []
})

onMounted(async () => {
  try { p.value = await api.getProduct(Number(route.params.id)) as any } catch { /* noop */ }
})
</script>
