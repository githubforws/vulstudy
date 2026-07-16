<template>
  <div class="log-container app-container">
    <el-card shadow="never" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span class="card-title">日志管理</span>
          <div class="search-area">
            <el-input
              v-model="searchQuery"
              placeholder="按关键字搜索"
              style="width: 230px"
              clearable
              size="default"
              @keyup.enter="handleSearch"
            >
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button type="primary" @click="handleSearch">查询</el-button>
          </div>
        </div>
      </template>

      <!-- Log Table -->
      <el-table
        :data="logList"
        stripe
        border
        style="width: 100%"
        :default-sort="{ prop: 'create_date', order: 'descending' }"
      >
        <el-table-column type="index" label="序号" width="55" align="center" />
        <el-table-column prop="user_name" label="用户名" min-width="130" show-overflow-tooltip />
        <el-table-column prop="operation_type" label="操作类型" min-width="120" show-overflow-tooltip />
        <el-table-column label="操作名称" min-width="100" show-overflow-tooltip>
          <template #default="scope">
            <el-tag size="small" :type="getOperationTagType(scope.row.operation_name)">
              {{ scope.row.operation_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operation_value" label="操作对象" min-width="180" show-overflow-tooltip />
        <el-table-column prop="operation_args" label="参数" min-width="200" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP 地址" min-width="140" show-overflow-tooltip />
        <el-table-column prop="create_date" label="时间" min-width="170" sortable />
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
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { LogList } from '@/api/log'

// ── Constants ──
const pageSize = 20

// ── State ──
const logList = ref([])
const total = ref(0)
const loading = ref(true)
const currentPage = ref(1)
const searchQuery = ref('')

// =====================================================================
//  Data Loading
// =====================================================================
async function fetchData(page) {
  loading.value = true
  try {
    const res = await LogList(searchQuery.value, page)
    const data = res.data
    logList.value = data.results || []
    total.value = data.count || 0
  } catch {
    ElMessage.error('加载日志失败')
  } finally {
    loading.value = false
  }
}

// =====================================================================
//  Search & Pagination
// =====================================================================
function handleSearch() {
  currentPage.value = 1
  fetchData(1)
}

function handlePageChange(page) {
  currentPage.value = page
  fetchData(page)
}

// =====================================================================
//  Helpers
// =====================================================================
function getOperationTagType(operationName) {
  if (!operationName) return 'info'
  const name = operationName.toLowerCase()
  if (name.includes('创建') || name.includes('添加') || name.includes('启动')) return 'success'
  if (name.includes('删除') || name.includes('停止')) return 'danger'
  if (name.includes('修改') || name.includes('更新') || name.includes('编辑')) return 'warning'
  return 'info'
}

// =====================================================================
//  Lifecycle
// =====================================================================
onMounted(() => {
  fetchData(1)
})
</script>

<style lang="scss" scoped>
.log-container {
  padding: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;

    .card-title {
      font-size: 16px;
      font-weight: 600;
    }

    .search-area {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }

  .pagination-wrap {
    display: flex;
    justify-content: center;
    margin-top: 20px;
    padding: 8px 0;
  }
}
</style>
