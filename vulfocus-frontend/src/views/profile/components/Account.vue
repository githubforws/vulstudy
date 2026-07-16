<template>
  <div class="account-container">
    <!-- User Info (read-only) -->
    <el-form label-width="120px" class="info-form">
      <el-form-item label="用户名">
        <el-input :model-value="userStore.name" disabled />
      </el-form-item>
      <el-form-item label="邮箱">
        <el-input :model-value="userStore.email" disabled />
      </el-form-item>
      <el-form-item label="Licence">
        <div class="licence-field">
          <el-input :model-value="userStore.licence" disabled class="licence-input" />
          <el-button type="primary" :icon="CopyDocument" @click="copyLicence">复制</el-button>
        </div>
      </el-form-item>
    </el-form>

    <el-divider />

    <!-- Change Password -->
    <div class="password-section">
      <el-button
        v-if="!showPasswordForm"
        type="warning"
        plain
        :icon="Edit"
        @click="showPasswordForm = true"
      >修改密码</el-button>

      <transition name="el-zoom-in-top">
        <el-form
          v-if="showPasswordForm"
          ref="formRef"
          :model="pwdForm"
          :rules="pwdRules"
          label-width="120px"
          class="password-form"
          @submit.prevent="submitPassword"
        >
          <el-form-item label="旧密码" prop="oldPassword">
            <el-input
              v-model="pwdForm.oldPassword"
              type="password"
              show-password
              placeholder="请输入旧密码"
            />
          </el-form-item>
          <el-form-item label="新密码" prop="pass">
            <el-input
              v-model="pwdForm.pass"
              type="password"
              show-password
              placeholder="至少8位字符"
            />
          </el-form-item>
          <el-form-item label="确认新密码" prop="checkPass">
            <el-input
              v-model="pwdForm.checkPass"
              type="password"
              show-password
              placeholder="请再次输入新密码"
            />
          </el-form-item>
          <el-form-item>
            <div class="form-actions">
              <el-button type="primary" :loading="submitting" @click="submitPassword">修改</el-button>
              <el-button @click="cancelPassword">关闭</el-button>
            </div>
          </el-form-item>
        </el-form>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { updatePassword } from '@/api/user'
import { CopyDocument, Edit } from '@element-plus/icons-vue'

const userStore = useUserStore()

// ── Password Form ──
const showPasswordForm = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const pwdForm = reactive({
  oldPassword: '',
  pass: '',
  checkPass: '',
})

const validateCheckPass = (_rule, value, callback) => {
  if (!value) {
    callback(new Error('请确认新密码'))
  } else if (value !== pwdForm.pass) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const pwdRules = {
  oldPassword: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  pass: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码至少8位字符', trigger: 'blur' },
  ],
  checkPass: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateCheckPass, trigger: 'blur' },
  ],
}

function submitPassword() {
  formRef.value.validate(valid => {
    if (!valid) return
    submitting.value = true
    updatePassword({
      old_password: pwdForm.oldPassword,
      new_password: pwdForm.pass,
    })
      .then(() => {
        ElMessage.success('密码修改成功')
        showPasswordForm.value = false
        resetPasswordForm()
      })
      .catch(err => {
        const msg = err?.response?.data?.msg || err?.response?.data?.non_field_errors?.[0] || '密码修改失败'
        ElMessage.error(msg)
      })
      .finally(() => {
        submitting.value = false
      })
  })
}

function cancelPassword() {
  showPasswordForm.value = false
  resetPasswordForm()
}

function resetPasswordForm() {
  pwdForm.oldPassword = ''
  pwdForm.pass = ''
  pwdForm.checkPass = ''
}

// ── Licence ──
function copyLicence() {
  if (userStore.licence) {
    navigator.clipboard.writeText(userStore.licence).then(() => {
      ElMessage.success('Licence 已复制到剪贴板')
    })
  }
}
</script>

<style lang="scss" scoped>
.account-container {
  padding: 4px 0;

  .info-form {
    max-width: 560px;

    .licence-field {
      display: flex;
      width: 100%;
      gap: 8px;

      .licence-input {
        flex: 1;
      }
    }
  }

  .password-section {
    .password-form {
      max-width: 480px;
      margin-top: 16px;
      padding: 16px;
      background: #fafafa;
      border-radius: 8px;
    }

    .form-actions {
      display: flex;
      gap: 12px;
    }
  }
}
</style>
