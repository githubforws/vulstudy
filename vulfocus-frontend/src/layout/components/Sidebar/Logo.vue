<template>
  <div class="sidebar-logo-container" :class="{ collapse }">
    <router-link key="expand" class="sidebar-logo-link" to="/">
      <img src="/logo.svg" class="sidebar-logo" />
      <span class="sidebar-title">Vulfocus</span>
    </router-link>
  </div>
</template>

<script setup>
defineProps({
  collapse: {
    type: Boolean,
    default: false,
  },
})
</script>

<style lang="scss" scoped>
.sidebar-logo-container {
  position: relative;
  width: 100%;
  height: 56px;
  line-height: 56px;
  background: #2b2f3a;
  text-align: center;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;

  .sidebar-logo-link {
    height: 100%;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;

    .sidebar-logo {
      width: 28px;
      height: 28px;
      vertical-align: middle;
    }

    .sidebar-title {
      display: inline-block;
      margin: 0;
      color: #fff;
      font-weight: 600;
      font-size: 15px;
      font-family: Avenir, Helvetica Neue, Arial, Helvetica, sans-serif;
      vertical-align: middle;
    }
  }

  &.collapse {
    .sidebar-title {
      display: none;
    }
  }
}
</style>
