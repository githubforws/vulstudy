<template>
  <div class="rank-container app-container">
    <el-card shadow="never" class="rank-card">
      <template #header>
        <div class="rank-header">
          <span class="rank-title">积分总榜</span>
          <el-select v-model="selectedTemplate" placeholder="选择排行榜" size="default" style="width: 200px" @change="handleTemplateChange">
            <el-option label="🏆 总榜" :value="null" />
            <el-option
              v-for="item in templateOptions"
              :key="item.temp_id"
              :label="item.name"
              :value="item.temp_id"
            />
          </el-select>
        </div>
      </template>

      <!-- Rank Table -->
      <el-table
        :data="rankList"
        stripe
        border
        style="width: 100%"
        v-loading="loading"
        :default-sort="{ prop: 'rank', order: 'ascending' }"
      >
        <!-- Rank Column -->
        <el-table-column label="排名" width="100" align="center">
          <template #default="scope">
            <div class="rank-cell">
              <!-- 1st place: Gold Trophy -->
              <svg-icon
                v-if="calcRank(scope.$index) === 1"
                icon-class="trophy1"
                class="trophy-icon trophy-gold"
              />
              <!-- 2nd place: Silver Trophy -->
              <svg-icon
                v-else-if="calcRank(scope.$index) === 2"
                icon-class="trophy2"
                class="trophy-icon trophy-silver"
              />
              <!-- 3rd place: Bronze Trophy -->
              <svg-icon
                v-else-if="calcRank(scope.$index) === 3"
                icon-class="trophy3"
                class="trophy-icon trophy-bronze"
              />
              <!-- Others: numeric -->
              <span v-else class="rank-number">{{ calcRank(scope.$index) }}</span>
            </div>
          </template>
        </el-table-column>

        <!-- User Column -->
        <el-table-column label="用户" min-width="200">
          <template #default="scope">
            <div class="user-cell">
              <el-avatar
                :size="30"
                :src="scope.row.image_url ? scope.row.image_url + '?imageView2' : ''"
                class="user-avatar"
              />
              <span class="user-name">{{ scope.row.name }}</span>
            </div>
          </template>
        </el-table-column>

        <!-- Score Column -->
        <el-table-column prop="rank" label="积分" width="120" align="center" sortable>
          <template #default="scope">
            <span class="score-value">{{ scope.row.rank }}</span>
          </template>
        </el-table-column>

        <!-- Pass Count Column (only in 总榜 mode) -->
        <el-table-column
          v-if="!selectedTemplate"
          prop="pass_container_count"
          label="通过数量"
          width="120"
          align="center"
          sortable
        />
      </el-table>

      <!-- Pagination -->
      <div class="pagination-wrap">
        <el-pagination
          v-if="total > 0"
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next, jumper"
          background
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { userranklist, timeranklist, timetemplist } from '@/api/timemoudel'

// ── Constants ──
const pageSize = 20

// ── Reactive State ──
const rankList = ref([])
const total = ref(0)
const loading = ref(true)
const currentPage = ref(1)
const selectedTemplate = ref(null)
const templateOptions = ref([])

// ── Computed Rank ──
function calcRank(index) {
  return (currentPage.value - 1) * pageSize + index + 1
}

// ── Data Fetching ──
function fetchRankList(page) {
  loading.value = true

  if (selectedTemplate.value) {
    // Timer template mode
    timeranklist(selectedTemplate.value, page)
      .then(response => {
        const data = response.data
        rankList.value = data.results || []
        total.value = data.count || 0
        loading.value = false
      })
      .catch(() => {
        loading.value = false
      })
  } else {
    // 总榜 mode
    userranklist(page)
      .then(response => {
        const data = response.data
        // userranklist wraps results in R.ok() → {data: {results, count}, status, msg}
        // So we need response.data.data.results / response.data.data.count
        const innerData = data.data || data
        rankList.value = innerData.results || []
        total.value = innerData.count || 0
        loading.value = false
      })
      .catch(() => {
        loading.value = false
      })
  }
}

function fetchTemplates() {
  timetemplist('temp')
    .then(response => {
      const data = response.data
      templateOptions.value = data.results || data.data?.results || []
    })
    .catch(() => {
      templateOptions.value = []
    })
}

function handleTemplateChange() {
  currentPage.value = 1
  fetchRankList(1)
}

function handlePageChange(page) {
  currentPage.value = page
  fetchRankList(page)
}

// ── Watch template changes ──
watch(selectedTemplate, () => {
  currentPage.value = 1
  fetchRankList(1)
})

// ── Lifecycle ──
onMounted(() => {
  fetchRankList(1)
  fetchTemplates()
})
</script>

<style lang="scss" scoped>
.rank-container {
  padding: 20px;

  .rank-card {
    border-radius: 8px;

    .rank-header {
      display: flex;
      align-items: center;
      justify-content: space-between;

      .rank-title {
        font-size: 16px;
        font-weight: 600;
      }
    }
  }

  .rank-cell {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 32px;
  }

  .trophy-icon {
    transition: transform 0.2s;

    &:hover {
      transform: scale(1.2);
    }
  }

  .trophy-gold {
    width: 28px;
    height: 28px;
    color: #ffd700;
  }

  .trophy-silver {
    width: 24px;
    height: 24px;
    color: #c0c0c0;
  }

  .trophy-bronze {
    width: 20px;
    height: 20px;
    color: #cd7f32;
  }

  .rank-number {
    font-size: 15px;
    font-weight: 600;
    color: #606266;
  }

  .user-cell {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 0;

    .user-avatar {
      flex-shrink: 0;
    }

    .user-name {
      font-size: 14px;
      font-weight: 500;
      color: #303133;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  .score-value {
    font-weight: 600;
    color: #e6a23c;
    font-size: 15px;
  }

  .pagination-wrap {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
    padding: 8px 0;
  }
}
</style>
