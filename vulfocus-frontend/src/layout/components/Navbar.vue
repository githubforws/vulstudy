<template>
  <div class="navbar">
    <div class="navbar-left">
      <div class="hamburger-container" @click="toggleSideBar">
        <el-icon :size="20">
          <Fold v-if="sidebar.opened" />
          <Expand v-else />
        </el-icon>
      </div>
      <Breadcrumb class="breadcrumb-container" />
    </div>

    <div class="right-menu">
      <!-- Notifications -->
      <el-dropdown class="notice-dropdown" trigger="click">
        <div class="notice-wrapper">
          <el-badge :value="notificationsCount" :hidden="notificationsCount === 0" class="notice-badge">
            <el-icon :size="22"><Bell /></el-icon>
          </el-badge>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item v-for="(item, index) in noticeList" :key="index">
              <router-link to="/notices/all">{{ item }}</router-link>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <!-- User Avatar -->
      <el-dropdown class="avatar-container" trigger="click">
        <div class="avatar-wrapper">
          <el-avatar :size="28" :src="avatar + '?imageView2'" />
          <el-icon class="caret-icon"><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item>
              <router-link to="/">主页</router-link>
            </el-dropdown-item>
            <el-dropdown-item divided @click="goProfile">
              <span>修改密码</span>
            </el-dropdown-item>
            <el-dropdown-item divided @click="logout">
              <span>退出登录</span>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'
import Breadcrumb from '@/components/Breadcrumb/index.vue'
import { get_notifications_count } from '@/api/notice'

const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()

const { sidebar } = storeToRefs(appStore)
const { avatar } = storeToRefs(userStore)

const noticeList = ref([])
const notificationsCount = ref(0)
let noticeTimer = null

function toggleSideBar() {
  appStore.toggleSideBar()
}

async function logout() {
  await userStore.logout()
  router.push(`/login?redirect=/`)
}

function goProfile() {
  router.push('/profile/index')
}

function fetchNotifications() {
  get_notifications_count().then(response => {
    notificationsCount.value = response.data.notifications_count
    noticeList.value = response.data.results
  })
}

onMounted(() => {
  fetchNotifications()
  noticeTimer = setInterval(fetchNotifications, 30000)
})

onBeforeUnmount(() => {
  if (noticeTimer) clearInterval(noticeTimer)
})
</script>

<style lang="scss" scoped>
.navbar {
  height: 50px;
  overflow: hidden;
  position: relative;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;

  .navbar-left {
    display: flex;
    align-items: center;
    height: 100%;
  }

  .hamburger-container {
    line-height: 46px;
    height: 100%;
    cursor: pointer;
    transition: background 0.3s;
    -webkit-tap-highlight-color: transparent;
    display: flex;
    align-items: center;

    &:hover {
      background: rgba(0, 0, 0, 0.025);
    }
  }

  .breadcrumb-container {
    margin-left: 8px;
  }

  .right-menu {
    display: flex;
    align-items: center;
    height: 100%;
    gap: 16px;

    &:focus {
      outline: none;
    }

    .notice-wrapper {
      cursor: pointer;
      padding: 4px 8px;
      border-radius: 4px;
      transition: background 0.3s;

      &:hover {
        background: rgba(0, 0, 0, 0.025);
      }
    }

    .avatar-container {
      cursor: pointer;

      .avatar-wrapper {
        display: flex;
        align-items: center;
        gap: 6px;

        .caret-icon {
          font-size: 12px;
        }
      }
    }
  }
}
</style>
