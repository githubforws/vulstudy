<template>
  <div class="activate-container">
    <div class="activate-card">
      <h2>激活账号</h2>
      <p>正在激活您的账号...</p>
      <el-result v-if="activated" icon="success" title="激活成功" sub-title="您的账号已成功激活">
        <template #extra>
          <router-link to="/login">
            <el-button type="primary">去登录</el-button>
          </router-link>
        </template>
      </el-result>
      <el-result v-else-if="error" icon="error" title="激活失败" :sub-title="errorMsg">
        <template #extra>
          <router-link to="/login">
            <el-button type="primary">返回登录</el-button>
          </router-link>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { accessCode } from '@/api/user'

const route = useRoute()
const activated = ref(false)
const error = ref(false)
const errorMsg = ref('')

onMounted(() => {
  const code = route.query.code
  if (code) {
    accessCode(code).then(() => {
      activated.value = true
    }).catch(err => {
      error.value = true
      errorMsg.value = err?.response?.data?.msg || '激活失败'
    })
  } else {
    error.value = true
    errorMsg.value = '缺少激活码'
  }
})
</script>

<style lang="scss" scoped>
.activate-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

  .activate-card {
    width: 460px;
    padding: 40px;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);

    h2 {
      text-align: center;
      margin-bottom: 24px;
    }
  }
}
</style>
