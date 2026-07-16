<template>
  <div class="profile-container app-container">
    <el-row :gutter="24">
      <!-- Left: UserCard (6 cols) -->
      <el-col :xs="24" :sm="24" :md="8" :lg="6" :xl="6">
        <UserCard />
      </el-col>

      <!-- Right: Tabs (18 cols) -->
      <el-col :xs="24" :sm="24" :md="16" :lg="18" :xl="18">
        <el-card shadow="never" class="profile-tabs-card">
          <el-tabs v-model="activeTab">
            <el-tab-pane label="活动时间线" name="timeline">
              <Timeline />
            </el-tab-pane>
            <el-tab-pane label="账户管理" name="account">
              <Account />
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import UserCard from './components/UserCard.vue'
import Timeline from './components/Timeline.vue'
import Account from './components/Account.vue'

const activeTab = ref('timeline')
</script>

<style lang="scss" scoped>
.profile-container {
  padding: 24px;

  .profile-tabs-card {
    border-radius: 8px;
    min-height: 400px;

    :deep(.el-tabs__header) {
      margin-bottom: 20px;
    }
  }
}
</style>
