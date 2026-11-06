<template>
  <div class="control-layout" style="height:calc(100vh - 120px)">
    <div class="col col-left" style="flex:0 0 260px">
      <div style="font-weight:600;margin-bottom:8px">分类</div>
      <el-input v-model="kw" placeholder="搜索商品" clearable style="margin-bottom:8px"
        @keyup.enter="load" @clear="load" />
      <el-tree :data="cats" node-key="category_id" default-expand-all :props="{ label: 'name', children: 'children' }" @node-click="onCat" />
    </div>
    <div class="col col-center">
      <el-table :data="items" stripe size="small" row-key="product_id" style="width:100%">
        <el-table-column prop="product_id" label="ID" width="60" />
        <el-table-column label="图片" width="70">
          <template #default="{ row }">
            <el-image :src="row.main_image" :preview-src-list="[row.main_image]" style="width:48px;height:48px;border-radius:4px" fit="cover" />
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="商品" show-overflow-tooltip />
        <el-table-column prop="brand" label="品牌" width="90" />
        <el-table-column label="SKU数" width="80">
          <template #default="{ row }">{{ (row.skus || []).length }}</template>
        </el-table-column>
        <el-table-column label="最低价" width="110">
          <template #default="{ row }">¥{{ minPrice(row) }}</template>
        </el-table-column>
        <el-table-column label="总库存" width="90">
          <template #default="{ row }">{{ totalStock(row) }}</template>
        </el-table-column>
        <el-table-column label="门店覆盖" width="130" align="center">
          <template #default="{ row }">
            <el-tooltip content="点击查看哪些门店有、哪些门店没有" placement="top">
              <el-tag
                size="small" effect="plain" style="cursor:pointer"
                :type="coverType(row.product_id)" @click="openCoverage(row)"
              >
                {{ coveredText(row.product_id) }}
              </el-tag>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <router-link :to="`/products/${row.product_id}`"><el-button size="small" text>详情</el-button></router-link>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="covDlg" :title="`门店覆盖 · ${covRow?.product_name || ''}`" width="620px">
      <div class="cov-summary">
        共 {{ coverage.total_stores }} 家门店，
        <b class="ok">{{ cov( covRow?.product_id).stores.length }} 家</b> 有货，
        <b class="no">{{ missingStores(covRow?.product_id).length }} 家</b> 无货
      </div>
      <div class="cov-group">
        <div class="cov-label ok">✅ 有货门店</div>
        <div class="cov-tags">
          <el-tag v-for="s in cov(covRow?.product_id).stores" :key="s.store_id" type="success" effect="plain" size="small">
            {{ s.name }} · {{ s.stock }} 件
          </el-tag>
          <span v-if="!cov(covRow?.product_id).stores.length" class="cov-empty">暂无</span>
        </div>
      </div>
      <div class="cov-group">
        <div class="cov-label no">⛔ 无货门店</div>
        <div class="cov-tags">
          <el-tag v-for="s in missingStores(covRow?.product_id)" :key="s.store_id" type="info" effect="plain" size="small">
            {{ s.name }}
          </el-tag>
          <span v-if="!missingStores(covRow?.product_id).length" class="cov-empty">全部门店都有</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api from '@/api'

const cats = ref<any[]>([])
const items = ref<any[]>([])
const kw = ref('')
const coverage = ref<any>({ total_stores: 0, stores: [], coverage: {} })
const covDlg = ref(false)
const covRow = ref<any>(null)

function minPrice(row: any) {
  const skus = row.skus || []
  if (!skus.length) return '0.00'
  return Math.min(...skus.map((s: any) => Number(s.price))).toFixed(2)
}
function totalStock(row: any) {
  return (row.skus || []).reduce((acc: number, s: any) => acc + (Number(s.stock) || 0), 0)
}

function cov(pid?: number) {
  if (!pid) return { covered: 0, stores: [] }
  return coverage.value.coverage?.[String(pid)] || { covered: 0, stores: [] }
}
function coveredText(pid: number) {
  return `${cov(pid).covered}/${coverage.value.total_stores || 0} 门店`
}
function coverType(pid: number) {
  const total = coverage.value.total_stores || 1
  const ratio = cov(pid).covered / total
  if (ratio >= 0.9) return 'success'
  if (ratio >= 0.6) return 'warning'
  return 'danger'
}
function missingStores(pid?: number) {
  const has = new Set(cov(pid).stores.map((s: any) => s.store_id))
  return (coverage.value.stores || []).filter((s: any) => !has.has(s.store_id))
}
function openCoverage(row: any) {
  covRow.value = row
  covDlg.value = true
}

const activeCat = ref<number | undefined>()

async function load() {
  try {
    const params: any = { keyword: kw.value || undefined }
    if (activeCat.value) params.category_id = activeCat.value
    const r: any = await api.listProducts(params)
    items.value = r?.items || r?.data || r || []
  } catch { /* noop */ }
}
async function loadCats() {
  try { cats.value = (await api.listCategories() as any) || [] } catch { /* noop */ }
}
async function loadCoverage() {
  try {
    const r: any = await api.storeCoverage()
    coverage.value = r || coverage.value
  } catch { /* noop */ }
}
function onCat(node: any) {
  activeCat.value = node?.category_id
  load()
}

onMounted(() => { load(); loadCats(); loadCoverage() })
</script>

<style scoped>
.cov-summary { font-size: 13px; color: #606266; margin-bottom: 12px; }
.cov-summary .ok { color: #67c23a; }
.cov-summary .no { color: #f56c6c; }
.cov-group { margin-bottom: 14px; }
.cov-label { font-size: 13px; font-weight: 700; margin-bottom: 8px; }
.cov-label.ok { color: #67c23a; }
.cov-label.no { color: #909399; }
.cov-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.cov-empty { font-size: 12px; color: #c0c4cc; }
</style>
