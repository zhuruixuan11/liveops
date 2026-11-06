<template>
  <div class="login-page">
    <div class="login-card">
      <!-- 左侧品牌区 -->
      <div class="brand-panel">
        <div class="brand-logo">🎬</div>
        <div class="brand-name">LiveOps 连锁门店直播运营平台</div>
        <div class="brand-desc">场控 Agent · 弹幕智能处理 · 门店销售看板</div>
        <ul class="brand-features">
          <li>🤖 弹幕意图识别 + 自动发券/查库存</li>
          <li>📊 掉线/库存/转化率并行监控告警</li>
          <li>🏪 多门店多主播统一运营</li>
        </ul>
      </div>

      <!-- 右侧表单区 -->
      <div class="form-panel">
        <div class="form-title">登录</div>
        <el-form :model="form" @submit.prevent="doLogin" size="large">
          <el-form-item>
            <el-input v-model="form.username" placeholder="账号" :prefix-icon="User" />
          </el-form-item>
          <el-form-item>
            <el-input v-model="form.password" type="password" show-password placeholder="密码" :prefix-icon="Lock" @keyup.enter="doLogin" />
          </el-form-item>
          <el-button type="primary" class="login-btn" :loading="loading" @click="doLogin">登 录</el-button>
        </el-form>

        <el-divider>演示账号一键登录</el-divider>
        <div class="demo-accounts">
          <el-button @click="quickLogin('admin1')" :loading="loading && form.username === 'admin1'">👔 老板/管理</el-button>
          <el-button type="success" plain @click="quickLogin('host6')" :loading="loading && form.username === 'host6'">🎙️ 主播</el-button>
        </div>

        <div class="to-register">还没有账号？<router-link to="/register">立即注册</router-link></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

function afterLogin() {
  const redirect = route.query.redirect as string
  if (redirect) {
    router.push(redirect)
    return
  }
  const role = auth.user?.role
  if (role === 'HOST') router.push('/host')
  else router.push('/')
}

async function doLogin() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    ElMessage.success('登录成功')
    afterLogin()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '登录失败')
  } finally { loading.value = false }
}

async function quickLogin(username: string) {
  form.username = username
  form.password = '123456'
  await doLogin()
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 55%, #4a7bc8 100%);
  position: relative;
  overflow: hidden;
}
.login-page::before, .login-page::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.06);
}
.login-page::before { width: 420px; height: 420px; top: -140px; left: -120px; }
.login-page::after { width: 320px; height: 320px; bottom: -110px; right: -80px; }

.login-card {
  width: 760px;
  min-height: 440px;
  display: flex;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
  position: relative;
  z-index: 1;
}
.brand-panel {
  width: 320px;
  background: linear-gradient(160deg, #16274f, #1e3c72);
  color: #fff;
  padding: 40px 28px;
  display: flex;
  flex-direction: column;
}
.brand-logo { font-size: 44px; margin-bottom: 12px; }
.brand-name { font-size: 19px; font-weight: 700; line-height: 1.5; }
.brand-desc { font-size: 13px; opacity: 0.75; margin-top: 8px; }
.brand-features { margin-top: auto; padding: 0; list-style: none; }
.brand-features li { font-size: 13px; opacity: 0.88; margin-top: 12px; line-height: 1.5; }

.form-panel {
  flex: 1;
  background: #fff;
  padding: 40px 44px 24px;
  display: flex;
  flex-direction: column;
}
.form-title { font-size: 22px; font-weight: 700; color: #1f2d3d; margin-bottom: 22px; }
.login-btn { width: 100%; margin-top: 4px; letter-spacing: 6px; }
.to-register { margin-top: auto; padding-top: 14px; font-size: 13px; color: #909399; text-align: center; }

.demo-accounts { display: flex; gap: 10px; justify-content: center; }
.demo-accounts .el-button { flex: 1; }

@media (max-width: 840px) {
  .login-page { min-height: 100vh; height: auto; padding: 20px 16px; overflow-y: auto; }
  .login-card { width: 100%; max-width: 420px; min-height: auto; flex-direction: column; }
  .brand-panel { width: 100%; padding: 26px 24px; }
  .brand-logo { font-size: 34px; margin-bottom: 6px; }
  .brand-features { display: none; }
  .form-panel { padding: 26px 24px 20px; }
}
</style>
