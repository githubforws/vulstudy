<template>
  <div class="scene-list-container app-container">
    <el-card shadow="never" class="scene-list-card">
      <!-- Search Bar -->
      <div class="scene-search">
        <el-input
          v-model="searchQuery"
          placeholder="按场景名称搜索"
          style="width: 280px"
          clearable
          size="default"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
      </div>

      <!-- Tabs -->
      <el-tabs v-model="activeTag" @tab-change="handleTagChange" class="scene-tabs">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane label="热门" name="hot" />
        <el-tab-pane label="计时场景" name="time" />
      </el-tabs>

      <!-- Card Grid -->
      <div v-loading="loading" class="scene-grid">
        <el-row :gutter="[20, 20]" v-if="!loading && sceneList.length > 0">
          <el-col
            v-for="item in sceneList"
            :key="item.id"
            :xs="24"
            :sm="12"
            :md="8"
            :lg="6"
            :xl="6"
          >
            <el-card shadow="hover" :body-style="{ padding: '0' }" class="scene-card">
              <!-- Scene Image -->
              <div class="scene-img-wrap" @click="goToDetail(item)">
                <el-image
                  :src="item.image_name || '/logo.svg'"
                  fit="cover"
                  class="scene-img"
                >
                  <template #error>
                    <div class="img-placeholder">
                      <el-icon :size="32"><Picture /></el-icon>
                    </div>
                  </template>
                </el-image>
                <el-tag
                  :type="item.type === 'timeScene' ? 'warning' : 'primary'"
                  size="small"
                  class="scene-type-tag"
                  effect="dark"
                >
                  {{ item.type === 'timeScene' ? '计时场景' : '普通场景' }}
                </el-tag>
              </div>

              <!-- Card Body -->
              <div class="scene-card-body">
                <h3 class="scene-name" @click="goToDetail(item)">{{ item.name }}</h3>
                <p class="scene-desc">{{ item.desc }}</p>

                <!-- Stats Row -->
                <div class="scene-stats">
                  <span class="stat-item" title="收藏数">
                    <el-icon
                      :color="item.have_fav ? '#e6a23c' : '#909399'"
                      style="cursor: pointer;"
                      @click.stop="toggleFav(item)"
                    >
                      <StarFilled v-if="item.have_fav" />
                      <Star v-else />
                    </el-icon>
                    {{ item.fav_num || 0 }}
                  </span>
                  <span class="stat-item" title="浏览数">
                    <el-icon><View /></el-icon>
                    {{ item.total_view || 0 }}
                  </span>
                  <span v-if="item.type !== 'timeScene'" class="stat-item" title="下载数">
                    <el-icon><Download /></el-icon>
                    {{ item.download_num || 0 }}
                  </span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-empty v-if="!loading && sceneList.length === 0" description="暂无场景数据" />
      </div>

      <!-- Pagination -->
      <div v-if="total > 0" class="pagination-wrap">
        <el-pagination
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getSceneData, thumbup } from '@/api/scene'

const router = useRouter()

// ── Constants ──
const pageSize = 20

// ── State ──
const sceneList = ref([])
const total = ref(0)
const loading = ref(true)
const currentPage = ref(1)
const searchQuery = ref('')
const activeTag = ref('all')

// ── Data Fetching ──
function fetchData() {
  loading.value = true
  getSceneData(searchQuery.value, currentPage.value, activeTag.value, '')
    .then(response => {
      const data = response.data
      sceneList.value = data.results || []
      total.value = data.count || 0
      loading.value = false
    })
    .catch(() => {
      loading.value = false
    })
}

// ── Handlers ──
function handleSearch() {
  currentPage.value = 1
  fetchData()
}

function handleTagChange() {
  currentPage.value = 1
  fetchData()
}

function handlePageChange(page) {
  currentPage.value = page
  fetchData()
}

function goToDetail(item) {
  if (item.type === 'timeScene') {
    router.push(`/scene/timeindex/${item.id}`)
  } else {
    router.push(`/scene/index/${item.id}`)
  }
}

function toggleFav(item) {
  thumbup(item.id)
    .then(() => {
      item.have_fav = !item.have_fav
      item.fav_num += item.have_fav ? 1 : -1
    })
    .catch(() => {
      ElMessage.error('操作失败')
    })
}

// ── Lifecycle ──
onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
.scene-list-container {
  padding: 20px;

  .scene-list-card {
    border-radius: 8px;

    .scene-search {
      margin-bottom: 16px;
      display: flex;
      gap: 10px;
    }

    .scene-tabs {
      margin-bottom: 16px;
    }
  }

  .scene-card {
    border-radius: 8px;
    overflow: hidden;
    cursor: default;
    transition: transform 0.25s, box-shadow 0.25s;

    &:hover {
      transform: translateY(-3px);
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
    }

    .scene-img-wrap {
      position: relative;
      height: 160px;
      overflow: hidden;
      cursor: pointer;

      .scene-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .img-placeholder {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f0f2f5;
        color: #c0c4cc;
      }

      .scene-type-tag {
        position: absolute;
        top: 8px;
        left: 8px;
      }
    }

    .scene-card-body {
      padding: 12px 16px 16px;

      .scene-name {
        margin: 0 0 6px;
        font-size: 15px;
        font-weight: 600;
        cursor: pointer;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;

        &:hover {
          color: #409eff;
        }
      }

      .scene-desc {
        margin: 0 0 12px;
        font-size: 12px;
        color: #909399;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        min-height: 18px;
      }

      .scene-stats {
        display: flex;
        gap: 16px;
        font-size: 12px;
        color: #909399;

        .stat-item {
          display: flex;
          align-items: center;
          gap: 4px;

          .el-icon {
            font-size: 14px;
          }
        }
      }
    }
  }

  .pagination-wrap {
    display: flex;
    justify-content: center;
    margin-top: 24px;
  }
}
</style>
