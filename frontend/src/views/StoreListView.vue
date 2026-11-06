<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>门店管理</span>
          <el-button type="primary" @click="openAdd">新增门店</el-button>
        </div>
      </template>
      <el-form inline :model="q" @submit.prevent="load">
        <el-form-item label="城市"><el-input v-model="q.city" clearable /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="q.status" clearable placeholder="全部">
            <el-option label="营业中" :value="1" />
            <el-option label="停业" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item><el-button type="primary" @click="load">查询</el-button></el-form-item>
      </el-form>

      <el-table :data="items" stripe size="small">
        <el-table-column prop="store_id" label="ID" width="60" />
        <el-table-column prop="name" label="名称" min-width="140" />
        <el-table-column prop="city" label="城市" width="100" />
        <el-table-column prop="address" label="地址" show-overflow-tooltip />
        <el-table-column prop="manager" label="负责人" width="100" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status===1?'success':'info'" size="small">
              {{ row.status===1 ? '营业中' : '停业' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="q.page" v-model:page-size="q.pageSize"
          :total="total" layout="prev, pager, next, total" @current-change="load"
        />
      </div>
    </el-card>

    <el-dialog v-model="dlg" title="新增门店" width="460px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="城市"><el-input v-model="form.city" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="负责人"><el-input v-model="form.manager" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg=false">取消</el-button>
        <el-button type="primary" @click="doAdd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const q = reactive({ page: 1, pageSize: 20, city: '', status: '' as any })
const items = ref<any[]>([])
const total = ref(0)
const dlg = ref(false)
const form = reactive({ name: '', city: '', address: '', manager: '' })

async function load() {
  try {
    // 空值不能传给后端：status 是 int 类型，传 "" 会触发 422 导致表格空白
    const params: any = { page: q.page, size: q.pageSize }
    if (q.city) params.city = q.city
    if (q.status !== '' && q.status !== null && q.status !== undefined) params.status = q.status

    const r: any = await api.listStores(params)
    const d = r?.items || r?.data || r || []
    items.value = d
    total.value = r?.total ?? d.length
  } catch (e: any) {
    items.value = []
    total.value = 0
    ElMessage.error(e?.response?.data?.detail?.[0]?.msg || e?.response?.data?.detail || '门店列表加载失败')
  }
}

function openAdd() { dlg.value = true; Object.assign(form, { name: '', city: '', address: '', manager: '' }) }

async function doAdd() {
  try {
    await api.createStore(form)
    ElMessage.success('已创建')
    dlg.value = false
    load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '失败') }
}

onMounted(load)
</script>
