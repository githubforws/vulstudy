<template>
  <div class="timeline-container">
    <div v-if="isTimingMode" class="timing-banner">
      <el-alert title="正在进行计时挑战赛" type="warning" :closable="false" show-icon />
    </div>

    <el-timeline v-loading="loading">
      <el-timeline-item
        v-for="(item, index) in historyList"
        :key="index"
        :timestamp="item.create_date"
        placement="top"
      >
        <el-card shadow="hover" class="timeline-card">
          <div class="timeline-content">
            <span class="timeline-action">{{ item.name }}</span>
            <el-tag
              v-if="item.is_check_date"
              type="success"
              size="small"
              effect="plain"
            >已通过 {{ item.is_check_date }}</el-tag>
          </div>
        </el-card>
      </el-timeline-item>

      <el-empty v-if="!loading && historyList.length === 0" description="暂无活动记录" />
    </el-timeline>

    <div v-if="total > pageSize" class="pagination-wrap">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next, jumper"
        background
        small
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ContainerHisory } from '@/api/docker'
import { gettimetemp } from '@/api/timemoudel'

const pageSize = 20
const currentPage = ref(1)
const total = ref(0)
const historyList = ref([])
const loading = ref(true)
const isTimingMode = ref(false)

function fetchHistory(page) {
  loading.value = true
  ContainerHisory(page)
    .then(response => {
      const data = response.data || {}
      historyList.value = data.results || []
      total.value = data.count || 0
      loading.value = false
    })
    .catch(() => {
      loading.value = false
    })
}

function fetchTimingMode() {
  gettimetemp()
    .then(response => {
      const results = response.data.results || []
      isTimingMode.value = results.length > 0
    })
    .catch(() => {
      isTimingMode.value = false
    })
}

function handlePageChange(page) {
  currentPage.value = page
  fetchHistory(page)
}

onMounted(() => {
  fetchHistory(1)
  fetchTimingMode()
})
</script>

<style lang="scss" scoped>
.timeline-container {
  padding: 4px 0;

  .timing-banner {
    margin-bottom: 16px;
  }

  .timeline-card {
    border-radius: 6px;

    .timeline-content {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;

      .timeline-action {
        font-size: 14px;
        color: #303133;
        word-break: break-all;
      }
    }
  }

  .pagination-wrap {
    display: flex;
    justify-content: center;
    margin-top: 20px;
  }
}
</style>
