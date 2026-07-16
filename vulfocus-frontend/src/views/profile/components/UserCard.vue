<template>
  <el-card shadow="never" class="user-card">
    <div class="user-card-body">
      <!-- Avatar Upload -->
      <div class="avatar-wrapper">
        <el-upload
          :show-file-list="false"
          :before-upload="beforeAvatarUpload"
          :http-request="uploadAvatar"
          action=""
          class="avatar-uploader"
        >
          <div class="avatar-hover-wrap">
            <el-avatar :size="100" :src="userStore.avatar + '?imageView2'" class="user-avatar" />
            <div class="avatar-overlay">
              <el-icon :size="28"><Camera /></el-icon>
              <span>更换头像</span>
            </div>
          </div>
        </el-upload>
      </div>

      <!-- User Info -->
      <h3 class="user-name">{{ userStore.name }}</h3>
      <p class="user-role">{{ userStore.roles?.join(', ') || '注册用户' }}</p>

      <el-divider />

      <div class="info-list">
        <div class="info-item">
          <el-icon :size="18"><Trophy /></el-icon>
          <span>积分：{{ userStore.rank ?? 0 }}</span>
        </div>
        <div class="info-item">
          <el-icon :size="18"><Message /></el-icon>
          <span>{{ userStore.email || '未设置邮箱' }}</span>
        </div>
        <div class="info-item">
          <el-icon :size="18"><Key /></el-icon>
          <span class="licence-text" @click="copyLicence" title="点击复制 Licence">
            {{ userStore.licence ? userStore.licence.substring(0, 12) + '...' : '无' }}
            <el-icon style="margin-left: 4px; cursor: pointer;"><CopyDocument /></el-icon>
          </span>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { uploaduserimgae } from '@/api/user'

const userStore = useUserStore()

function beforeAvatarUpload(file) {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('请上传图片文件')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB')
    return false
  }
  return true
}

function uploadAvatar(options) {
  const formData = new FormData()
  formData.append('file', options.file)
  uploaduserimgae(formData)
    .then(() => {
      ElMessage.success('头像更新成功')
      // Reload user info from store
      userStore.getInfo()
      // Force a re-render by timestamping the avatar URL
      setTimeout(() => {
        location.reload()
      }, 500)
    })
    .catch(() => {
      ElMessage.error('头像上传失败')
    })
}

function copyLicence() {
  if (userStore.licence) {
    navigator.clipboard.writeText(userStore.licence).then(() => {
      ElMessage.success('Licence 已复制')
    })
  }
}
</script>

<style lang="scss" scoped>
.user-card {
  border-radius: 8px;
  margin-bottom: 20px;

  .user-card-body {
    text-align: center;
    padding: 8px 0;
  }

  .avatar-wrapper {
    display: flex;
    justify-content: center;
    margin-bottom: 16px;
  }

  .avatar-uploader {
    cursor: pointer;
  }

  .avatar-hover-wrap {
    position: relative;
    border-radius: 50%;
    overflow: hidden;

    .user-avatar {
      display: block;
    }

    .avatar-overlay {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.5);
      color: #fff;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 4px;
      opacity: 0;
      transition: opacity 0.3s;
      font-size: 12px;
    }

    &:hover .avatar-overlay {
      opacity: 1;
    }
  }

  .user-name {
    margin: 0 0 4px;
    font-size: 18px;
    font-weight: 600;
  }

  .user-role {
    margin: 0;
    color: #909399;
    font-size: 13px;
  }

  .info-list {
    text-align: left;
    font-size: 14px;

    .info-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 0;
      color: #606266;

      .el-icon {
        flex-shrink: 0;
        color: #409eff;
      }
    }

    .licence-text {
      display: flex;
      align-items: center;
      cursor: pointer;
      color: #409eff;

      &:hover {
        color: #66b1ff;
      }
    }
  }
}
</style>
