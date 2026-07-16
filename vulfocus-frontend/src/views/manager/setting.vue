<template>
  <div class="setting-container app-container">
    <el-card shadow="never">
      <template #header>
        <span class="card-title">系统配置</span>
      </template>

      <el-tabs v-model="activeTab">
        <!-- ═══ System Settings Tab ═══ -->
        <el-tab-pane label="系统设置" name="system">
          <el-form
            ref="systemFormRef"
            :model="systemForm"
            label-width="170px"
            v-loading="loading"
            class="setting-form"
          >
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="分享用户名">
                  <template #label>
                    <span>
                      分享用户名
                      <el-tooltip content="用于镜像分享时的贡献用户名（建议Github用户名）" placement="top">
                        <el-icon class="help-icon"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </span>
                  </template>
                  <el-input v-model="systemForm.share_username" placeholder="输入分享用户名" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="Dockerhub 用户名">
                  <template #label>
                    <span>
                      Dockerhub 用户名
                      <el-tooltip content="镜像分享时的登录用户名" placement="top">
                        <el-icon class="help-icon"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </span>
                  </template>
                  <el-input v-model="systemForm.username" placeholder="输入 Dockerhub 用户名" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="Dockerhub Token">
                  <template #label>
                    <span>
                      Dockerhub Token
                      <el-tooltip content="镜像分享时的登录凭证" placement="top">
                        <el-icon class="help-icon"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </span>
                  </template>
                  <el-input v-model="systemForm.pwd" type="password" show-password placeholder="输入 Dockerhub Token" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="镜像过期时间（秒）">
                  <template #label>
                    <span>
                      镜像过期时间（秒）
                      <el-tooltip content="默认1800秒（30分钟），0为永不过期" placement="top">
                        <el-icon class="help-icon"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </span>
                  </template>
                  <el-input v-model.number="systemForm.time" placeholder="输入过期时间" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-divider />

            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="镜像过期删除">
                  <template #label>
                    <span>
                      镜像过期删除
                      <el-tooltip content="开启后镜像到期自动删除容器，默认开启" placement="top">
                        <el-icon class="help-icon"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </span>
                  </template>
                  <el-switch v-model="systemForm.del_container" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="注册验证">
                  <template #label>
                    <span>
                      注册验证
                      <el-tooltip content="关闭后用户注册无需邮箱验证，默认开启" placement="top">
                        <el-icon class="help-icon"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </span>
                  </template>
                  <el-switch v-model="systemForm.cancel_validation" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="用户注册">
                  <template #label>
                    <span>
                      用户注册
                      <el-tooltip content="关闭后无法注册，默认开启" placement="top">
                        <el-icon class="help-icon"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </span>
                  </template>
                  <el-switch v-model="systemForm.cancel_registration" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="自动下载镜像">
                  <template #label>
                    <span>
                      自动下载镜像
                      <el-tooltip content="开启后每隔1小时自动下载最新镜像" placement="top">
                        <el-icon class="help-icon"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </span>
                  </template>
                  <el-switch v-model="systemForm.is_synchronization" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-divider />

            <el-form-item>
              <el-button type="primary" :loading="systemSaving" @click="handleSaveSystem">修改</el-button>
              <el-button @click="handleCancelSystem">取消</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- ═══ Website Settings Tab ═══ -->
        <el-tab-pane label="网站设置" name="website">
          <el-form
            ref="websiteFormRef"
            :model="websiteForm"
            label-width="170px"
            v-loading="loading"
            class="setting-form"
          >
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="系统名称">
                  <template #label>
                    <span>
                      系统名称
                      <el-tooltip content="自定义系统名称" placement="top">
                        <el-icon class="help-icon"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </span>
                  </template>
                  <el-input v-model="websiteForm.url_name" placeholder="输入系统名称" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="系统 LOGO">
                  <template #label>
                    <span>
                      系统 LOGO
                      <el-tooltip content="建议尺寸 289×66，支持 jpeg/png，不超过 2M" placement="top">
                        <el-icon class="help-icon"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </span>
                  </template>
                  <div class="upload-wrap">
                    <el-upload
                      :show-file-list="false"
                      :before-upload="beforeImageUpload"
                      :http-request="handleUploadLogo"
                      action=""
                      class="image-uploader"
                    >
                      <div v-if="websiteForm.enterprise_logo" class="upload-preview">
                        <img :src="websiteForm.enterprise_logo" class="upload-img" />
                      </div>
                      <div v-else class="upload-placeholder">
                        <el-icon :size="32"><Plus /></el-icon>
                        <span>上传 LOGO</span>
                      </div>
                    </el-upload>
                  </div>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="系统登录背景图">
                  <template #label>
                    <span>
                      系统登录背景图
                      <el-tooltip content="建议尺寸 1920×1080，支持 jpeg/png，不超过 2M" placement="top">
                        <el-icon class="help-icon"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </span>
                  </template>
                  <div class="upload-wrap">
                    <el-upload
                      :show-file-list="false"
                      :before-upload="beforeImageUpload"
                      :http-request="handleUploadBg"
                      action=""
                      class="image-uploader"
                    >
                      <div v-if="websiteForm.enterprise_bg" class="upload-preview">
                        <img :src="websiteForm.enterprise_bg" class="upload-img" />
                      </div>
                      <div v-else class="upload-placeholder">
                        <el-icon :size="32"><Plus /></el-icon>
                        <span>上传背景图</span>
                      </div>
                    </el-upload>
                  </div>
                </el-form-item>
              </el-col>
            </el-row>

            <el-divider />

            <el-form-item>
              <el-button type="primary" :loading="websiteSaving" @click="handleSaveWebsite">修改</el-button>
              <el-button @click="handleResetWebsite">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { QuestionFilled, Plus } from '@element-plus/icons-vue'
import { settingGet, settingUpdate, enterpriseUpdate } from '@/api/setting'
import { uploadImage } from '@/api/layout'

// ── State ──
const loading = ref(true)
const activeTab = ref('system')
const systemSaving = ref(false)
const websiteSaving = ref(false)

// ── System Settings Form ──
const systemForm = reactive({
  share_username: '',
  username: '',
  pwd: '',
  time: 3600,
  del_container: true,
  cancel_validation: true,
  cancel_registration: true,
  is_synchronization: false,
})

// ── Website Settings Form ──
const websiteForm = reactive({
  url_name: 'vulfocus',
  enterprise_logo: '',
  enterprise_bg: '',
})

// =====================================================================
//  Data Loading
// =====================================================================
async function fetchSettings() {
  loading.value = true
  try {
    const res = await settingGet()
    const data = res.data?.data
    if (data) {
      systemForm.share_username = data.share_username || ''
      systemForm.username = data.username || ''
      systemForm.pwd = data.pwd || ''
      systemForm.time = data.time !== undefined ? Number(data.time) : 3600
      systemForm.del_container = data.del_container === true || data.del_container === '1'
      // Invert: backend "cancel_validation=True" means "validation cancelled",
      // frontend switch "注册验证" ON should mean "validation required"
      systemForm.cancel_validation = !(data.cancel_validation === true || data.cancel_validation === '1')
      // Invert: backend "cancel_registration=True" means "registration cancelled",
      // frontend switch "用户注册" ON should mean "registration allowed"
      systemForm.cancel_registration = !(data.cancel_registration === true || data.cancel_registration === '1')
      systemForm.is_synchronization = data.is_synchronization === true || data.is_synchronization === '1'
      websiteForm.url_name = data.url_name || 'vulfocus'
      websiteForm.enterprise_logo = data.enterprise_logo || ''
      websiteForm.enterprise_bg = data.enterprise_bg || ''
    }
  } catch {
    ElMessage.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

// =====================================================================
//  System Settings
// =====================================================================
async function handleSaveSystem() {
  systemSaving.value = true
  const formData = new FormData()
  formData.append('share_username', systemForm.share_username)
  formData.append('username', systemForm.username)
  formData.append('pwd', systemForm.pwd)
  formData.append('time', String(systemForm.time))
  formData.append('del_container', systemForm.del_container ? 'true' : 'false')
  // Invert: frontend switch ON → user wants validation → cancel_validation should be false
  formData.append('cancel_validation', systemForm.cancel_validation ? 'false' : 'true')
  // Invert: frontend switch ON → user wants registration → cancel_registration should be false
  formData.append('cancel_registration', systemForm.cancel_registration ? 'false' : 'true')
  formData.append('is_synchronization', systemForm.is_synchronization ? 'true' : 'false')
  formData.append('url_name', websiteForm.url_name)

  try {
    const res = await settingUpdate(formData)
    if (res.data && res.data.code !== 200) {
      ElMessage.error(res.data.msg || '保存失败')
    } else {
      ElMessage.success('系统设置保存成功')
    }
  } catch (err) {
    // Error already displayed by request.js interceptor
  } finally {
    systemSaving.value = false
  }
}

function handleCancelSystem() {
  fetchSettings()
  ElMessage.info('已放弃修改')
}

// =====================================================================
//  Image Upload
// =====================================================================
function beforeImageUpload(file) {
  const isImage = file.type === 'image/jpeg' || file.type === 'image/png'
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isImage) {
    ElMessage.error('仅支持 jpeg/png 格式')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2M')
    return false
  }
  return true
}

async function handleUploadLogo(options) {
  const formData = new FormData()
  formData.append('img', options.file)
  try {
    const res = await uploadImage(formData)
    if (res.data?.status === 200 || res.data?.code === 200) {
      websiteForm.enterprise_logo = '/images/' + (res.data.data || res.data.msg || options.file.name)
      ElMessage.success('LOGO 上传成功')
    } else {
      ElMessage.error(res.data?.msg || '上传失败')
    }
  } catch {
    ElMessage.error('LOGO 上传失败')
  }
}

async function handleUploadBg(options) {
  const formData = new FormData()
  formData.append('img', options.file)
  try {
    const res = await uploadImage(formData)
    if (res.data?.status === 200 || res.data?.code === 200) {
      websiteForm.enterprise_bg = '/images/' + (res.data.data || res.data.msg || options.file.name)
      ElMessage.success('背景图上传成功')
    } else {
      ElMessage.error(res.data?.msg || '上传失败')
    }
  } catch {
    ElMessage.error('背景图上传失败')
  }
}

// =====================================================================
//  Website Settings
// =====================================================================
async function handleSaveWebsite() {
  websiteSaving.value = true
  const formData = new FormData()
  formData.append('url_name', websiteForm.url_name)
  formData.append('enterprise_logo', websiteForm.enterprise_logo)
  formData.append('enterprise_bg', websiteForm.enterprise_bg)

  try {
    const res = await enterpriseUpdate(formData)
    if (res.data && res.data.code !== 200) {
      ElMessage.error(res.data.msg || '保存失败')
    } else {
      ElMessage.success('网站设置保存成功')
    }
  } catch (err) {
    // Error already displayed by request.js interceptor
  } finally {
    websiteSaving.value = false
  }
}

async function handleResetWebsite() {
  websiteSaving.value = true
  const formData = new FormData()
  formData.append('url_name', 'vulfocus')
  formData.append('enterprise_logo', '')
  formData.append('enterprise_bg', '')
  try {
    const res = await enterpriseUpdate(formData)
    if (res.data && res.data.code !== 200) {
      ElMessage.error(res.data.msg || '重置失败')
    } else {
      ElMessage.success('网站设置已重置')
      fetchSettings()
    }
  } catch (err) {
    // Error already displayed by request.js interceptor
    websiteSaving.value = false
  }
}

// =====================================================================
//  Lifecycle
// =====================================================================
onMounted(() => {
  fetchSettings()
})
</script>

<style lang="scss" scoped>
.setting-container {
  padding: 20px;

  .card-title {
    font-size: 16px;
    font-weight: 600;
  }

  .setting-form {
    max-width: 960px;

    .el-divider {
      margin: 16px 0;
    }

    .help-icon {
      margin-left: 4px;
      font-size: 14px;
      color: #c0c4cc;
      cursor: help;
      vertical-align: middle;

      &:hover {
        color: #409eff;
      }
    }
  }

  .upload-wrap {
    .image-uploader {
      display: block;
    }

    .upload-preview {
      width: 330px;
      height: 178px;
      border: 1px dashed #dcdfe6;
      border-radius: 6px;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: border-color 0.3s;

      &:hover {
        border-color: #409eff;
      }

      .upload-img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
      }
    }

    .upload-placeholder {
      width: 330px;
      height: 178px;
      border: 1px dashed #dcdfe6;
      border-radius: 6px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 8px;
      color: #909399;
      font-size: 13px;
      cursor: pointer;
      transition: border-color 0.3s, color 0.3s;

      &:hover {
        border-color: #409eff;
        color: #409eff;
      }
    }
  }
}
</style>
