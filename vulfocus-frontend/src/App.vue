<template>
  <div id="app">
    <router-view v-if="isRouterAlive" />
  </div>
</template>

<script setup>
import { ref, provide, nextTick } from 'vue'

const isRouterAlive = ref(true)

function reload() {
  isRouterAlive.value = false
  nextTick(() => {
    isRouterAlive.value = true
  })
}

provide('reload', reload)
</script>
