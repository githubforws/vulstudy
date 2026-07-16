<template>
  <div class="layout-manager-container app-container">
    <!-- Header & Search -->
    <el-card shadow="never" class="search-card">
      <div class="search-area">
        <el-input
          v-model="searchQuery"
          placeholder="按关键字搜索场景"
          style="width: 360px; background: #f2f4f7"
          clearable
          size="default"
          @keyup.enter="handleSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" @click="handleSearch">搜索</el-button>

        <!-- Official Store Preview -->
        <div class="store-preview">
          <span class="store-label">场景商店：</span>
          <template v-if="officialScenes.length > 0">
            <span
              v-for="item in officialScenes.slice(0, 5)"
              :key="item.layout_id"
              class="store-link"
              @click="downloadOfficial(item)"
            >{{ item.layout_name }}</span>
          </template>
          <span v-else style="color: #c0c4cc; font-size: 13px;">暂无官方场景</span>
          <el-link v-if="officialScenes.length > 5" type="primary" :underline="false" style="margin-left: 8px;" @click="storeDrawer = true">
            查看更多 >
          </el-link>
        </div>
      </div>
    </el-card>

    <!-- Tabs -->
    <el-card shadow="never" class="scene-card">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane label="环境编排" name="layout" />
        <el-tab-pane label="计时场景" name="time" />
      </el-tabs>

      <!-- Scene Grid -->
      <div v-loading="loading" class="scene-grid">
        <el-row :gutter="[20, 24]" v-if="!loading">
          <!-- Add Card (only on all/layout tab) -->
          <el-col v-if="activeTab !== 'time'" :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
            <el-card shadow="hover" class="add-card" @click="openCreateDialog">
              <div class="add-card-content">
                <el-icon :size="48"><Plus /></el-icon>
                <span>添加场景</span>
              </div>
            </el-card>
          </el-col>

          <!-- Scene Cards -->
          <el-col
            v-for="item in displayList"
            :key="item.id"
            :xs="24" :sm="12" :md="8" :lg="6" :xl="6"
          >
            <el-card shadow="hover" :body-style="{ padding: '0' }" class="scene-card-item">
              <!-- Image -->
              <div class="scene-img-wrap">
                <el-image :src="item.image_name || '/logo.svg'" fit="cover" class="scene-img">
                  <template #error>
                    <div class="img-placeholder"><el-icon :size="40"><Picture /></el-icon></div>
                  </template>
                </el-image>
                <!-- Not published badge -->
                <div v-if="!item.is_release && item.type === 'layoutScene'" class="unpublished-badge">未发布</div>
                <!-- Action buttons overlay -->
                <div class="action-overlay">
                  <el-button v-if="item.type === 'layoutScene'" size="small" :icon="View" @click.stop="handleViewYaml(item)">查看</el-button>
                  <el-button size="small" :icon="Edit" @click.stop="handleEdit(item)">编辑</el-button>
                  <el-button size="small" :icon="Delete" type="danger" @click.stop="handleDelete(item)">删除</el-button>
                  <template v-if="item.type === 'layoutScene'">
                    <el-button
                      v-if="!item.is_release && item.status?.progress !== 100"
                      size="small" :icon="Upload"
                      @click.stop="handlePublish(item)"
                    >发布</el-button>
                    <el-tag v-else-if="item.is_release" size="small" type="success">已发布</el-tag>
                    <el-button
                      v-if="item.status?.progress !== 100"
                      size="small" :icon="Download"
                      @click.stop="handleDownload(item)"
                    >下载</el-button>
                    <el-button
                      v-if="item.status?.task_id && item.status?.progress < 100"
                      size="small" type="warning"
                      @click.stop="showProgress(item)"
                    >{{ item.status?.progress || 0 }}%</el-button>
                  </template>
                </div>
              </div>
              <!-- Info -->
              <div class="scene-info">
                <h4 class="scene-name">{{ item.name }}</h4>
                <p class="scene-desc">{{ item.desc }}</p>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <el-empty v-if="!loading && displayList.length === 0" description="暂无场景数据" />
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

    <!-- ═══ Official Store Drawer ═══ -->
    <el-drawer v-model="storeDrawer" title="官方场景商店" size="80%" destroy-on-close>
      <el-row :gutter="[20, 24]">
        <el-col
          v-for="item in officialScenes"
          :key="item.layout_id"
          :xs="24" :sm="12" :md="8" :lg="6"
        >
          <el-card shadow="hover" :body-style="{ padding: '0' }" class="store-card" @click="downloadOfficial(item)">
            <el-image :src="item.image_name" fit="cover" class="store-img">
              <template #error>
                <div class="img-placeholder" style="height: 180px;"><el-icon :size="32"><Picture /></el-icon></div>
              </template>
            </el-image>
            <div class="store-card-info">
              <span>{{ item.layout_name }}</span>
            </div>
          </el-card>
        </el-col>
      </el-row>
      <el-empty v-if="officialScenes.length === 0" description="暂无官方场景" />
    </el-drawer>

    <!-- ═══ Create Dialog ═══ -->
    <el-dialog v-model="createDialogVisible" title="创建场景" width="420px" destroy-on-close>
      <div class="create-options">
        <div class="create-option-card" @click="handleCreateLayout">
          <el-icon :size="40"><Collection /></el-icon>
          <span class="option-title">创建编排模式</span>
          <span class="option-desc">使用 Docker Compose 编排多容器场景</span>
        </div>
        <div class="create-option-card" @click="handleCreateTime">
          <el-icon :size="40"><Timer /></el-icon>
          <span class="option-title">创建计时模式</span>
          <span class="option-desc">创建限时挑战的盲盒场景</span>
        </div>
      </div>
    </el-dialog>

    <!-- ═══ Time Template Dialog ═══ -->
    <el-dialog v-model="timeDialogVisible" title="创建计时模板" width="500px" destroy-on-close :close-on-click-modal="false">
      <el-form ref="timeFormRef" :model="timeForm" label-width="110px" size="small">
        <el-form-item label="模板名称" prop="name" :rules="[{ required: true, message: '请输入名称' }]">
          <el-input v-model="timeForm.name" placeholder="输入计时模板名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="timeForm.time_desc" type="textarea" :rows="3" placeholder="输入描述" />
        </el-form-item>
        <el-form-item label="时间(分钟)" prop="timer_minutes" :rules="[{ required: true, message: '请输入时间' }]">
          <el-input-number v-model="timeForm.timer_minutes" :min="1" :max="1440" />
        </el-form-item>
        <el-form-item label="Rank范围">
          <el-input v-model="timeForm.rank_range" placeholder="如 0.5-5.0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="timeDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="timeSaving" @click="submitTimeTemplate">创建</el-button>
      </template>
    </el-dialog>

    <!-- ═══ YAML View Dialog ═══ -->
    <el-dialog v-model="yamlDialogVisible" title="YAML 内容" width="700px" destroy-on-close>
      <el-input v-model="yamlContent" type="textarea" :rows="16" readonly />
    </el-dialog>

    <!-- ═══ Progress Dialog ═══ -->
    <el-dialog v-model="progressDialogVisible" :title="progressTitle" width="550px" :close-on-click-modal="false" @close="clearProgressTimer">
      <el-table :data="progressLayers" stripe size="small" max-height="400">
        <el-table-column prop="id" label="层 ID" min-width="180" show-overflow-tooltip />
        <el-table-column label="进度" width="200">
          <template #default="scope">
            <el-progress :percentage="scope.row.progress || 0" :stroke-width="14" />
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { Search, Plus, View, Edit, Delete, Upload, Download, Collection, Timer, Picture } from '@element-plus/icons-vue'
import {
  layoutList, layoutDelete, layoutRelease, layoutDownload,
  download_layout_image, getOfficialWebsiteLayout, downloadWebsiteLayout,
} from '@/api/layout'
import { getSceneData } from '@/api/scene'
import { timetempadd, timetempdelete } from '@/api/timemoudel'
import { layoutbathchTask, progressTask } from '@/api/tasks'

// ── Constants ──
const pageSize = 20

// ── Router ──
const router = useRouter()

// ── State: Search & Tabs ──
const searchQuery = ref('')
const activeTab = ref('all')
const loading = ref(false)
const sceneList = ref([])
const total = ref(0)
const currentPage = ref(1)

// ── State: Official Store ──
const officialScenes = ref([])
const storeDrawer = ref(false)

// ── State: Create Dialog ──
const createDialogVisible = ref(false)

// ── State: Time Template ──
const timeDialogVisible = ref(false)
const timeFormRef = ref(null)
const timeSaving = ref(false)
const timeForm = reactive({
  name: '',
  time_desc: '',
  timer_minutes: 30,
  rank_range: '',
})

// ── State: YAML Dialog ──
const yamlDialogVisible = ref(false)
const yamlContent = ref('')

// ── State: Progress Dialog ──
const progressDialogVisible = ref(false)
const progressTitle = ref('')
const progressLayers = ref([])
let progressTimer = null

// ── Task Polling ──
let taskPollTimer = null

// =====================================================================
//  Computed
// =====================================================================
const displayList = computed(() => {
  if (activeTab.value === 'layout') {
    return sceneList.value.filter(item => item.type === 'layoutScene')
  }
  if (activeTab.value === 'time') {
    return sceneList.value.filter(item => item.type !== 'layoutScene')
  }
  return sceneList.value
})

// =====================================================================
//  Data Loading
// =====================================================================
async function fetchScenes(page) {
  loading.value = true
  try {
    const tag = activeTab.value === 'layout' ? 'all' : activeTab.value
    const res = await getSceneData(searchQuery.value, page, tag, 'backstage')
    const data = res.data
    let list = data.results || []
    if (activeTab.value === 'layout') {
      list = list.filter(item => item.type === 'layoutScene')
    }
    sceneList.value = list.map(item => ({
      ...item,
      status: item.status || { task_id: '', progress: 100 },
    }))
    total.value = data.count || 0
  } catch {
    ElMessage.error('加载场景列表失败')
  } finally {
    loading.value = false
  }
}

async function fetchOfficialScenes() {
  try {
    const res = await getOfficialWebsiteLayout()
    const data = res.data
    officialScenes.value = data.data || data.results || []
  } catch {
    // silently fail
  }
}

// =====================================================================
//  Search & Tabs & Pagination
// =====================================================================
function handleSearch() {
  currentPage.value = 1
  fetchScenes(1)
}

function handleTabChange() {
  currentPage.value = 1
  fetchScenes(1)
}

function handlePageChange(page) {
  currentPage.value = page
  fetchScenes(page)
}

// =====================================================================
//  Create Scene
// =====================================================================
function openCreateDialog() {
  createDialogVisible.value = true
}

function handleCreateLayout() {
  createDialogVisible.value = false
  router.push('/layout/index')
}

function handleCreateTime() {
  createDialogVisible.value = false
  timeDialogVisible.value = true
  resetTimeForm()
}

function resetTimeForm() {
  timeForm.name = ''
  timeForm.time_desc = ''
  timeForm.timer_minutes = 30
  timeForm.rank_range = ''
}

async function submitTimeTemplate() {
  const valid = await timeFormRef.value.validate().catch(() => false)
  if (!valid) return
  timeSaving.value = true
  try {
    await timetempadd({
      name: timeForm.name,
      time_desc: timeForm.time_desc,
      timer_minutes: timeForm.timer_minutes,
      rank_range: timeForm.rank_range,
    })
    ElMessage.success('计时模板创建成功')
    timeDialogVisible.value = false
    fetchScenes(currentPage.value)
  } catch (err) {
    ElMessage.error(err?.response?.data?.msg || '创建失败')
  } finally {
    timeSaving.value = false
  }
}

// =====================================================================
//  Edit / View YAML
// =====================================================================
async function handleEdit(item) {
  try {
    const res = await layoutList(item.id)
    const data = res.data?.data || {}
    router.push(`/layout/index?id=${data.layout_id}`)
  } catch {
    ElMessage.error('获取场景详情失败')
  }
}

async function handleViewYaml(item) {
  try {
    const res = await layoutList(item.id)
    const data = res.data?.data || {}
    yamlContent.value = data.yml_content || '# 无 YAML 内容'
    yamlDialogVisible.value = true
  } catch {
    ElMessage.error('获取 YAML 失败')
  }
}

// =====================================================================
//  Delete
// =====================================================================
async function handleDelete(item) {
  try {
    await ElMessageBox.confirm(`确定删除场景 "${item.name}" 吗？`, '删除确认', {
      confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning',
    })
    if (item.type === 'layoutScene') {
      await layoutDelete(item.id)
    } else {
      await timetempdelete(item.id)
    }
    ElMessage.success('删除成功')
    fetchScenes(currentPage.value)
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err?.response?.data?.msg || '删除失败')
    }
  }
}

// =====================================================================
//  Publish
// =====================================================================
async function handlePublish(item) {
  if (item.is_uesful === false) {
    try {
      await ElMessageBox.confirm(
        '该场景镜像未完全下载，是否先下载镜像？', '提示',
        { confirmButtonText: '下载镜像', cancelButtonText: '取消', type: 'warning' }
      )
      await download_layout_image({ id: item.id })
      ElMessage.success('镜像下载任务已创建')
    } catch {
      return
    }
  }
  try {
    await layoutRelease(item.id)
    ElMessage.success('场景已发布')
    fetchScenes(currentPage.value)
  } catch (err) {
    ElMessage.error(err?.response?.data?.msg || '发布失败')
  }
}

// =====================================================================
//  Download ZIP
// =====================================================================
async function handleDownload(item) {
  try {
    const res = await layoutDownload(item.id)
    const blob = new Blob([res.data], { type: 'application/zip' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${item.name || 'scene'}.zip`
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载已开始')
  } catch {
    ElMessage.error('下载失败')
  }
}

// =====================================================================
//  Official Store
// =====================================================================
async function downloadOfficial(item) {
  try {
    await ElMessageBox.confirm(`确定下载场景 "${item.layout_name}"？`, '确认下载')
    await downloadWebsiteLayout({ layout_id: item.layout_id })
    ElMessage.success('下载任务已创建，请稍后刷新页面')
    fetchScenes(1)
  } catch {
    // cancelled
  }
}

// =====================================================================
//  Progress
// =====================================================================
function showProgress(item) {
  const taskId = item.status?.task_id
  if (!taskId) { ElMessage.info('任务状态已更新，请刷新列表'); return }
  progressTitle.value = `下载: ${item.name}`
  progressLayers.value = [{ id: taskId, progress: item.status?.progress || 0 }]
  progressDialogVisible.value = true

  clearProgressTimer()
  progressTimer = setInterval(async () => {
    try {
      const res = await progressTask(taskId)
      const data = res.data
      if (data.progress !== undefined) {
        progressLayers.value = [{ id: taskId, progress: data.progress }]
      }
      if (data.status === 200 || data.progress >= 100) {
        clearProgressTimer()
        ElMessage.success('下载完成')
        progressDialogVisible.value = false
        fetchScenes(currentPage.value)
      }
    } catch {
      clearProgressTimer()
    }
  }, 2000)
}

function clearProgressTimer() {
  if (progressTimer) { clearInterval(progressTimer); progressTimer = null }
}

// =====================================================================
//  Task Polling (auto-refresh download status)
// =====================================================================
function startTaskPolling() {
  taskPollTimer = setInterval(async () => {
    const taskIds = []
    const taskMap = {}
    for (const item of sceneList.value) {
      if (item.status?.task_id) {
        taskIds.push(item.status.task_id)
        taskMap[item.status.task_id] = item
      }
    }
    if (taskIds.length === 0) return
    try {
      const res = await layoutbathchTask({ task_ids: taskIds })
      const statusList = res.data?.data || res.data?.status || []
      for (const s of statusList) {
        const scene = taskMap[s.task_id]
        if (!scene) continue
        if (s.status === 200) {
          scene.status.task_id = ''
          scene.status.progress = 100
          ElNotification.success({ title: '下载完成', message: `${scene.name} 下载已就绪`, duration: 3000 })
        } else if (s.status !== 1001) {
          scene.status.task_id = ''
        }
      }
    } catch { /* ignore */ }
  }, 3000)
}

// =====================================================================
//  Lifecycle
// =====================================================================
onMounted(() => {
  fetchScenes(1)
  fetchOfficialScenes()
  startTaskPolling()
})

onBeforeUnmount(() => {
  if (taskPollTimer) clearInterval(taskPollTimer)
  clearProgressTimer()
})
</script>

<style lang="scss" scoped>
.layout-manager-container {
  padding: 20px;

  .search-card {
    margin-bottom: 16px;
    border-radius: 8px;

    .search-area {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;

      .store-preview {
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;
        margin-left: 8px;

        .store-label {
          font-size: 13px;
          color: #606266;
          white-space: nowrap;
        }

        .store-link {
          font-size: 13px;
          color: #409eff;
          cursor: pointer;
          white-space: nowrap;

          &:hover {
            color: #66b1ff;
            text-decoration: underline;
          }

          &::after {
            content: '·';
            color: #c0c4cc;
            margin-left: 6px;
          }

          &:last-child::after {
            content: '';
          }
        }
      }
    }
  }

  .scene-card {
    border-radius: 8px;
  }

  .scene-grid {
    min-height: 200px;
  }

  // Add Card
  .add-card {
    border-radius: 8px;
    cursor: pointer;
    height: 100%;
    min-height: 220px;
    transition: all 0.25s;
    border: 2px dashed #dcdfe6;

    &:hover {
      border-color: #409eff;
      background: #ecf5ff;
    }

    .add-card-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 12px;
      height: 220px;
      color: #909399;
    }
  }

  // Scene Card
  .scene-card-item {
    border-radius: 8px;
    overflow: hidden;
    transition: transform 0.25s, box-shadow 0.25s;

    &:hover {
      transform: translateY(-3px);
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);

      .action-overlay {
        opacity: 1;
      }
    }

    .scene-img-wrap {
      position: relative;
      height: 200px;
      overflow: hidden;

      .scene-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .img-placeholder {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f0f2f5;
        color: #c0c4cc;
      }

      .unpublished-badge {
        position: absolute;
        top: 10px;
        left: 10px;
        background: rgba(250, 63, 63, 1);
        color: #fff;
        font-size: 12px;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 500;
      }

      .action-overlay {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(0, 0, 0, 0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 8px;
        opacity: 0;
        transition: opacity 0.25s;
        flex-wrap: wrap;

        .el-button {
          font-size: 12px;
          padding: 4px 8px;
        }
      }
    }

    .scene-info {
      padding: 12px 14px 14px;

      .scene-name {
        margin: 0 0 6px;
        font-size: 14px;
        font-weight: 600;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .scene-desc {
        margin: 0;
        font-size: 12px;
        color: #909399;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }

  .pagination-wrap {
    display: flex;
    justify-content: center;
    margin-top: 24px;
    padding: 8px 0;
  }
}

// Store Drawer Cards
.store-card {
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.25s;

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
  }

  .store-img {
    width: 100%;
    height: 180px;
  }

  .store-card-info {
    padding: 10px 14px;
    font-size: 14px;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

// Create Options
.create-options {
  display: flex;
  gap: 20px;
  padding: 12px 0;

  .create-option-card {
    flex: 1;
    border: 1px solid #e8ecf1;
    border-radius: 12px;
    padding: 28px 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    transition: all 0.25s;

    &:hover {
      border-color: #409eff;
      background: #ecf5ff;
    }

    .el-icon {
      color: #409eff;
    }

    .option-title {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }

    .option-desc {
      font-size: 12px;
      color: #909399;
      text-align: center;
    }
  }
}
</style>
