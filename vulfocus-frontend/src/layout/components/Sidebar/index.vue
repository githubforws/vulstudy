<template>
  <div :class="{ 'has-logo': showLogo }" class="sidebar-wrapper">
    <logo v-if="showLogo" :collapse="isCollapse" />
    <el-scrollbar wrap-class="scrollbar-wrapper" class="sidebar-scroll">
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :background-color="variables.menuBg"
        :text-color="variables.menuText"
        :active-text-color="variables.menuActiveText"
        :collapse-transition="false"
        mode="vertical"
      >
        <sidebar-item v-for="route in permissionRoutes" :key="route.path" :item="route" :base-path="route.path" />
      </el-menu>
    </el-scrollbar>

    <!-- Version info at bottom -->
    <div class="sidebar-footer">
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :background-color="variables.menuBg"
        :text-color="variables.menuText"
        :collapse-transition="false"
        mode="vertical"
      >
        <el-menu-item class="version-item">
          <a href="https://github.com/fofapro/vulfocus" target="_blank" class="version-link">
            <img
              src="https://img.shields.io/github/stars/fofapro/vulfocus.svg?style=flat-square"
              style="width: 60px"
            />
            <img
              src="https://img.shields.io/github/release/fofapro/vulfocus.svg?style=flat-square"
              style="width: 90px"
            />
          </a>
        </el-menu-item>
      </el-menu>
    </div>
  </div>
</template>

<script setup>
import { computed, inject } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { usePermissionStore } from '@/stores/permission'
import { useSettingsStore } from '@/stores/settings'
import { storeToRefs } from 'pinia'
import Logo from './Logo.vue'
import SidebarItem from './SidebarItem.vue'
import variables from '@/styles/variables.js'

const route = useRoute()
const appStore = useAppStore()
const permissionStore = usePermissionStore()
const settingsStore = useSettingsStore()

const { sidebar } = storeToRefs(appStore)
const permissionRoutes = computed(() => permissionStore.routes)
const showLogo = computed(() => settingsStore.sidebarLogo)
const isCollapse = computed(() => !sidebar.value.opened)

const activeMenu = computed(() => {
  const { meta, path } = route
  if (meta.activeMenu) {
    return meta.activeMenu
  }
  return path
})
</script>

<style lang="scss" scoped>
.sidebar-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;

  .sidebar-scroll {
    flex: 1;
    overflow: hidden;

    :deep(.scrollbar-wrapper) {
      overflow-x: hidden !important;
    }

    :deep(.el-scrollbar__view) {
      height: 100%;
    }
  }

  .sidebar-footer {
    flex-shrink: 0;

    .version-item {
      padding: 0 8px !important;
      height: 48px;
      line-height: 48px;

      .version-link {
        display: flex;
        align-items: center;
        gap: 4px;
      }
    }
  }
}
</style>
