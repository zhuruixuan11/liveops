<template>
  <div style="height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#1e3c72,#2a5298)">
    <el-card style="width:380px">
      <template #header><b style="font-size:18px">注册 LiveOps</b></template>
      <el-form :model="form" label-width="60px" @submit.prevent="doReg">
        <el-form-item label="账号"><el-input v-model="form.username" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" type="password" show-password /></el-form-item>
        <el-form-item label="手机"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item>
          <el-button type="primary" style="width:100%" :loading="loading" @click="doReg">注册</el-button>
        </el-form-item>
        <div style="text-align:right;font-size:13px">
          已有账号？<router-link to="/login">登录</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'

const router = useRouter()
const loading = ref(false)
const form = reactive({ username: '', password: '', phone: '' })

async function doReg() {
  loading.value = true
  try {
    await api.register(form)
    ElMessage.success('注册成功，请登录')
    router.push({ name: 'login' })
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '注册失败')
  } finally { loading.value = false }
}
</script>
