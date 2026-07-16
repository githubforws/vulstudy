<template>
  <div class="register-container">
    <div class="register-card">
      <h2>注册账号</h2>
      <el-form ref="formRef" :model="registerForm" :rules="rules" label-width="100px">
        <el-form-item label="用户名" prop="name">
          <el-input v-model="registerForm.name" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="registerForm.email" />
        </el-form-item>
        <el-form-item label="密码" prop="pass">
          <el-input v-model="registerForm.pass" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="checkpass">
          <el-input v-model="registerForm.checkpass" type="password" show-password />
        </el-form-item>
        <el-form-item label="验证码" prop="captcha_code">
          <div style="display: flex; gap: 10px; align-items: center;">
            <el-input v-model="registerForm.captcha_code" style="width: 120px;" placeholder="验证码" />
            <img
              v-if="captchaImg"
              :src="captchaImg"
              style="cursor: pointer; height: 36px; border-radius: 4px; border: 1px solid #dcdfe6;"
              @click="refreshCaptcha"
              title="点击刷新"
            />
            <span v-else style="color: #909399; font-size: 12px;">加载中...</span>
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleRegister" :loading="loading" style="width: 100%">注册</el-button>
        </el-form-item>
      </el-form>
      <div class="register-footer">
        <router-link to="/login">已有账号？去登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { register as registerApi, get_captcha } from '@/api/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const captchaImg = ref('')

const registerForm = reactive({
  name: '',
  email: '',
  pass: '',
  checkpass: '',
  captcha_code: '',
  hashkey: '',
})

const rules = {
  name: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
  pass: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  checkpass: [{ required: true, message: '请确认密码', trigger: 'blur' }],
  captcha_code: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
}

function refreshCaptcha() {
  captchaImg.value = ''
  get_captcha().then(response => {
    const data = response.data || {}
    // backend returns: {hashkey: "...", image_url: "/captcha/image/xxx/"}
    registerForm.hashkey = data.hashkey || ''
    // nginx only proxies /api/ to Django, so prefix /api to reach the captcha endpoint
    captchaImg.value = data.image_url ? '/api' + data.image_url : ''
    registerForm.captcha_code = ''
  }).catch(() => {
    ElMessage.error('获取验证码失败')
  })
}

function handleRegister() {
  formRef.value.validate(valid => {
    if (!valid) return
    if (registerForm.pass !== registerForm.checkpass) {
      ElMessage.error('两次密码不一致')
      return
    }
    loading.value = true
    registerApi({
      username: registerForm.name.trim(),
      password: registerForm.pass,
      checkpass: registerForm.checkpass,
      captcha_code: registerForm.captcha_code,
      hashkey: registerForm.hashkey,
    }).then(response => {
      // Backend returns HTTP 200 with body {code: 200, msg: "注册成功"} on success,
      // or HTTP 200 with body {code: 400, msg: "..."} on failure.
      // The axios interceptor treats all 200s as success.
      const data = response.data || {}
      if (data.code === 200) {
        ElMessage.success('注册成功，请登录')
        router.push('/login')
      } else {
        ElMessage.error(data.msg || '注册失败')
        refreshCaptcha()
      }
    }).catch(err => {
      const msg = err?.response?.data?.msg || err?.response?.data?.non_field_errors?.[0] || '注册失败'
      ElMessage.error(msg)
      refreshCaptcha()
    }).finally(() => {
      loading.value = false
    })
  })
}

onMounted(() => {
  refreshCaptcha()
})
</script>

<style lang="scss" scoped>
.register-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

  .register-card {
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

  .register-footer {
    text-align: center;
    margin-top: 16px;
    a { color: #409eff; text-decoration: none; }
  }
}
</style>
