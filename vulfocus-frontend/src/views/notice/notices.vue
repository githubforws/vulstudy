<template>
  <div class="notice-container app-container">
    <!-- ═══ List View ═══ -->
    <template v-if="show">
      <el-card shadow="never" v-loading="loading">
        <template #header>
          <span class="card-title">公告列表</span>
        </template>

        <el-table
          v-if="noticeList.length > 0"
          :data="noticeList"
          stripe
          border
          style="width: 70%; margin: 20px auto;"
        >
          <el-table-column label="序号" width="55" align="center">
            <template #default="scope">
              <el-icon
                :size="scope.row.notification?.unread !== false ? 20 : 16"
                :color="scope.row.notification?.unread !== false ? '#303133' : '#c0c4cc'"
                style="cursor: pointer;"
                @click="openDetail(scope.row)"
              >
                <Message />
              </el-icon>
            </template>
          </el-table-column>

          <el-table-column label="公告" min-width="300">
            <template #default="scope">
              <span
                :style="{
                  fontSize: scope.row.notification?.unread !== false ? '20px' : '16px',
                  color: scope.row.notification?.unread !== false ? '#303133' : '#c0c4cc',
                  cursor: 'pointer',
                  fontWeight: scope.row.notification?.unread !== false ? 600 : 400,
                }"
                @click="openDetail(scope.row)"
              >{{ scope.row.title }}</span>
            </template>
          </el-table-column>

          <el-table-column label="发布时间" width="200" align="center">
            <template #default="scope">
              <span
                :style="{
                  color: scope.row.notification?.unread !== false ? '#606266' : '#c0c4cc',
                  fontSize: scope.row.notification?.unread !== false ? '14px' : '13px',
                }"
              >{{ scope.row.update_date }}</span>
            </template>
          </el-table-column>
        </el-table>

        <el-empty v-if="!loading && noticeList.length === 0" description="暂无公告" />

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
    </template>

    <!-- ═══ Detail View ═══ -->
    <template v-else>
      <div class="detail-container" v-loading="detailLoading">
        <div class="detail-header">
          <el-icon :size="24" color="rgb(64, 158, 255)" style="cursor: pointer;" @click="goBack">
            <ArrowLeft />
          </el-icon>
          <span class="detail-title">{{ detailTitle }}</span>
        </div>
        <div class="detail-content" v-if="!detailLoading">
          <ViewerEditor v-model="detailContent" height="600px" :options="{ hideModeSwitch: true }" />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Message, ArrowLeft } from '@element-plus/icons-vue'
import { get_public_notice, notice_detail } from '@/api/notice'
import ViewerEditor from '@/components/ViewerEditor/index.vue'

// ── Constants ──
const pageSize = 20

// ── State: List View ──
const noticeList = ref([])
const total = ref(0)
const loading = ref(true)
const currentPage = ref(1)

// ── State: Detail View ──
const show = ref(true)
const detailLoading = ref(false)
const detailTitle = ref('')
const detailContent = ref('')

// =====================================================================
//  Data Loading
// =====================================================================
async function fetchData(page) {
  loading.value = true
  try {
    const res = await get_public_notice(page)
    const data = res.data?.data || res.data || {}
    noticeList.value = data.results || []
    total.value = data.count || 0
  } catch {
    ElMessage.error('加载公告列表失败')
  } finally {
    loading.value = false
  }
}

// =====================================================================
//  Pagination
// =====================================================================
function handlePageChange(page) {
  currentPage.value = page
  fetchData(page)
}

// =====================================================================
//  Detail
// =====================================================================
async function openDetail(item) {
  show.value = false
  detailLoading.value = true
  detailTitle.value = item.title || ''
  detailContent.value = ''
  try {
    const res = await notice_detail(item.notice_id)
    if (res.data.code === 200) {
      const content = res.data.data
      detailContent.value = typeof content === 'string' ? content : JSON.stringify(content || '')
    } else {
      ElMessage.error(res.data.msg || '获取公告详情失败')
    }
  } catch {
    ElMessage.error('获取公告详情失败')
  } finally {
    detailLoading.value = false
  }
}

function goBack() {
  location.reload()
}

// =====================================================================
//  Lifecycle
// =====================================================================
onMounted(() => {
  fetchData(1)
})
</script>

<style lang="scss" scoped>
.notice-container {
  padding: 20px;

  .card-title {
    font-size: 16px;
    font-weight: 600;
  }

  .pagination-wrap {
    margin-top: 20px;
    margin-left: 280px;
    padding: 8px 0;
  }
}

.detail-container {
  max-width: 900px;
  margin: 0 auto;
  min-height: 400px;

  .detail-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
    padding: 16px 0;

    .detail-title {
      font-size: 22px;
      font-weight: 600;
      color: #303133;
    }
  }

  .detail-content {
    padding: 0 4px;
  }
}
</style>
