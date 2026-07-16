<template>
  <div class="retrieve-container">
    <div class="retrieve-card">
      <h2>找回密码</h2>
      <el-form ref="formRef" :model="form" label-width="100px">
        <el-form-item label="邮箱" prop="email" :rules="[{ required: true, message: '请输入邮箱' }]">
          <el-input v-model="form.email" placeholder="请输入注册邮箱" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSend" :loading="loading" style="width: 100%">发送重置邮件</el-button>
        </el-form-item>
      </el-form>
      <div class="retrieve-footer">
        <router-link to="/login">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { sendMail } from '@/api/user'
import { ElMessage } from 'element-plus'

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  email: '',
})

function handleSend() {
  formRef.value.validate(valid => {
    if (!valid) return
    loading.value = true
    sendMail(form).then(() => {
      ElMessage.success('重置邮件已发送，请查收')
    }).catch(err => {
      ElMessage.error(err?.response?.data?.msg || '发送失败')
    }).finally(() => {
      loading.value = false
    })
  })
}
</script>

<style lang="scss" scoped>
.retrieve-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

  .retrieve-card {
    width: 420px;
    padding: 40px;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);

    h2 {
      text-align: center;
      margin-bottom: 24px;
    }
  }

  .retrieve-footer {
    text-align: center;
    margin-top: 16px;

    a {
      color: #409eff;
      text-decoration: none;
    }
  }
}
</style>
