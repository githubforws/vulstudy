<template>
  <div class="update-pwd-container">
    <div class="update-card">
      <h2>重置密码</h2>
      <el-form ref="formRef" :model="form" label-width="100px">
        <el-form-item label="新密码" prop="password" :rules="[{ required: true, message: '请输入新密码' }]">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="checkpass" :rules="[{ required: true, message: '请确认密码' }]">
          <el-input v-model="form.checkpass" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleUpdate" :loading="loading" style="width: 100%">重置密码</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { updatePassword } from '@/api/user'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  password: '',
  checkpass: '',
})

function handleUpdate() {
  formRef.value.validate(valid => {
    if (!valid) return
    if (form.password !== form.checkpass) {
      ElMessage.error('两次密码不一致')
      return
    }
    loading.value = true
    updatePassword({
      new_password: form.password,
      code: route.query.code || '',
    }).then(() => {
      ElMessage.success('密码重置成功')
      router.push('/login')
    }).catch(err => {
      ElMessage.error(err?.response?.data?.msg || '重置失败')
    }).finally(() => {
      loading.value = false
    })
  })
}
</script>

<style lang="scss" scoped>
.update-pwd-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

  .update-card {
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
}
</style>
