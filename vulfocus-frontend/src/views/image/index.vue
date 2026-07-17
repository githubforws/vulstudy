<template>
  <div class="image-manage-container app-container">
    <el-card shadow="never" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span class="card-title">容器管理</span>
          <div class="search-area">
            <el-autocomplete
              v-model="searchInput"
              :fetch-suggestions="querySearchImageAsync"
              :trigger-on-focus="false"
              placeholder="按镜像名称搜索"
              style="width: 300px"
              clearable
              value-key="value"
              @select="handleSelectImage"
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-autocomplete>
            <el-button type="primary" @click="handleSearch">查询</el-button>
          </div>
        </div>
      </template>

      <!-- Container Table -->
      <el-table
        :data="containerList"
        stripe
        border
        style="width: 100%"
        v-loading="loading"
        :default-sort="{ prop: 'container_id', order: 'descending' }"
      >
        <el-table-column type="index" label="序号" width="60" align="center" />

        <el-table-column prop="image_vul_name" label="漏洞名称" min-width="150" show-overflow-tooltip />

        <el-table-column prop="user_name" label="用户名" width="110" show-overflow-tooltip />

        <el-table-column prop="vul_host" label="访问地址" min-width="200" show-overflow-tooltip />

        <el-table-column label="状态" width="90" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.container_status === 'running' ? 'success' : 'info'" size="small">
              {{ scope.row.container_status === 'running' ? '运行中' : '已停止' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="vul_desc" label="漏洞描述" min-width="280" show-overflow-tooltip />

        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="scope">
            <el-button
              v-if="scope.row.container_status === 'stop'"
              type="primary"
              size="small"
              :loading="scope.row._loading === 'start'"
              :disabled="!!scope.row._loading"
              @click="handleStart(scope.row)"
            >
              <el-icon style="margin-right: 4px;"><CaretRight /></el-icon>启动
            </el-button>
            <el-button
              v-else-if="scope.row.container_status === 'running'"
              type="warning"
              size="small"
              :loading="scope.row._loading === 'stop'"
              :disabled="!!scope.row._loading"
              @click="handleStop(scope.row)"
            >
              <el-icon style="margin-right: 4px;"><VideoPause /></el-icon>停止
            </el-button>
            <el-button
              v-if="scope.row.container_status === 'running' || scope.row.container_status === 'stop'"
              type="danger"
              size="small"
              :loading="scope.row._loading === 'delete'"
              :disabled="!!scope.row._loading"
              @click="handleDelete(scope.row)"
            >
              <el-icon style="margin-right: 4px;"><Delete /></el-icon>删除
            </el-button>
          </template>
        </el-table-column>
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
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { ImgList } from '@/api/docker'
import { containerList, containerStart, containerStop, containerDel } from '@/api/container'
import { getTask } from '@/api/tasks'

// ── Constants ──
const pageSize = 20

// ── State ──
const containerListData = ref([])
const total = ref(0)
const loading = ref(true)
const currentPage = ref(1)

// ── Search ──
const searchInput = ref('')
const searchImageId = ref('')
const searchImageName = ref('')

// ── Polling Timer Pool ──
const timerPool = ref([])

// =====================================================================
//  Data Loading
// =====================================================================
async function loadData(page) {
  loading.value = true
  try {
    const response = await containerList('list', page, searchImageId.value)
    const data = response.data
    containerListData.value = (data.results || []).map(item => ({ ...item, _loading: false }))
    total.value = data.count || 0
  } catch {
    ElMessage.error('加载容器列表失败')
  } finally {
    loading.value = false
  }
}

// =====================================================================
//  Search
// =====================================================================
async function querySearchImageAsync(queryString, cb) {
  if (!queryString || queryString.trim() === '') {
    cb([])
    return
  }
  try {
    const res = await ImgList(queryString, true, 1)
    const results = res.data.results || []
    const list = results.map(item => ({
      value: item.image_vul_name || item.image_name || item.image_vul,
      id: item.image_id || item.id,
    }))
    cb(list.slice(0, 10))
  } catch {
    cb([])
  }
}

function handleSelectImage(item) {
  searchImageId.value = item.id
  searchImageName.value = item.value
}

function handleSearch() {
  // If user typed but didn't select from autocomplete, search by name with empty id
  if (!searchImageId.value && searchInput.value) {
    // Keep the text but send empty id
  }
  currentPage.value = 1
  loadData(1)
}

// =====================================================================
//  Container Lifecycle – Task Polling
// =====================================================================
function startPolling(taskId, row, action, onSuccess) {
  if (!taskId) {
    row._loading = false
    ElMessage.error('无法获取任务ID')
    return
  }

  const timerId = setInterval(async () => {
    try {
      const res = await getTask(taskId)
      const status = res.data.status
      if (status === 1001) return // still running

      clearInterval(timerId)
      removeTimer(timerId)
      row._loading = false

      if (status === 200) {
        ElMessage.success(res.data.msg || `${action}成功`)
        if (onSuccess) onSuccess()
        await loadData(currentPage.value)
      } else {
        ElMessage.error(res.data.msg || `${action}失败`)
      }
    } catch {
      clearInterval(timerId)
      removeTimer(timerId)
      row._loading = false
      ElMessage.error(`${action}失败：网络错误`)
    }
  }, 1000)
  addTimer(timerId)
}

// ── Start ──
async function handleStart(row) {
  if (!row.container_id) return
  row._loading = 'start'
  try {
    const res = await containerStart(row.container_id)
    startPolling(res.data?.data, row, '启动', () => {
      row.container_status = 'running'
    })
  } catch {
    row._loading = false
    ElMessage.error('启动请求失败')
  }
}

// ── Stop ──
async function handleStop(row) {
  if (!row.container_id) return
  row._loading = 'stop'
  try {
    const res = await containerStop(row.container_id)
    startPolling(res.data?.data, row, '停止', () => {
      row.container_status = 'stop'
    })
  } catch {
    row._loading = false
    ElMessage.error('停止请求失败')
  }
}

// ── Delete ──
async function handleDelete(row) {
  if (!row.container_id) return
  row._loading = 'delete'
  try {
    const res = await containerDel(row.container_id)
    startPolling(res.data?.data, row, '删除', () => {
      row.container_status = ''
    })
  } catch {
    row._loading = false
    ElMessage.error('删除请求失败')
  }
}

// =====================================================================
//  Pagination
// =====================================================================
function handlePageChange(page) {
  currentPage.value = page
  loadData(page)
}

// =====================================================================
//  Timer Management
// =====================================================================
function addTimer(id) { timerPool.value.push(id) }
function removeTimer(id) { timerPool.value = timerPool.value.filter(t => t !== id) }
function clearAllTimers() {
  timerPool.value.forEach(id => clearInterval(id))
  timerPool.value = []
}

// ── Lifecycle ──
onMounted(() => {
  loadData(1)
})

onBeforeUnmount(() => {
  clearAllTimers()
})
</script>

<style lang="scss" scoped>
.image-manage-container {
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
      gap: 10px;
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
