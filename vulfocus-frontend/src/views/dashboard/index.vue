<template>
  <div class="dashboard-container">
    <!-- Detail Dialog -->
    <el-dialog v-model="dialogVisible" @close="handleDialogClose" title="镜像信息" width="620px" destroy-on-close>
      <template #header>
        <div class="dialog-header">
          <span class="dialog-header-title">镜像信息</span>
          <el-button v-if="!writeupLoading" link type="primary" @click="openWriteupDrawer" style="margin-left: 12px;">
            <el-icon><Reading /></el-icon> 查看Writeup
          </el-button>
        </div>
      </template>

      <div v-loading="detailLoading" element-loading-text="环境启动中...">
        <div class="detail-item">
          <span class="detail-label">访问地址：</span>
          <div class="detail-value">
            <a v-if="accessUrl" :href="accessUrl" target="_blank" class="access-link">{{ accessUrl }}</a>
            <span v-else>{{ vulHost }}</span>
          </div>
          <el-button v-if="accessUrl" link type="primary" size="small" @click="copyText(accessUrl)" style="margin-left: 8px;">
            <el-icon><CopyDocument /></el-icon>
          </el-button>
        </div>
        <div class="detail-item">
          <span class="detail-label">映射端口：</span>
          <div class="detail-value">
            <el-tag v-for="port in vulPortSimple" :key="port" class="port-tag" size="small">
              {{ port }}
            </el-tag>
            <span v-if="vulPortSimple.length === 0" style="color: #909399;">无端口映射</span>
          </div>
        </div>
        <div class="detail-item">
          <span class="detail-label">名称：</span>
          <span class="detail-value">{{ imagesName }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">描述：</span>
          <span class="detail-value">{{ imagesDesc }}</span>
        </div>

        <!-- Flag Submission -->
        <div v-if="isFlag" class="flag-section">
          <el-divider />
          <el-form class="flag-form" @submit.prevent="submitFlag">
            <el-form-item label="Flag">
              <el-input
                v-model="flagInput"
                placeholder="请输入Flag：格式 flag-{xxxxxxxx}"
                :disabled="flagSubmitting"
                clearable
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="submitFlag" :loading="flagSubmitting" :disabled="!flagInput.trim()">
                提交
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </el-dialog>

    <!-- Writeup Drawer -->
    <el-drawer
      v-model="writeupDrawer"
      :title="imagesName + ' writeup'"
      size="50%"
      direction="btt"
      :before-close="closeWriteupDrawer"
    >
      <div class="writeup-content" v-loading="writeupLoading">
        <ViewerEditor v-if="!writeupLoading" v-model="writeupContent" height="600px" />
        <el-empty v-if="!writeupLoading && !writeupContent" description="当前环境还没有writeup，赶紧去官网发表解题思路吧" />
      </div>
    </el-drawer>

    <!-- Main Dashboard -->
    <div class="dashboard-main">
      <!-- ★ Filter Card -->
      <el-card class="filter-card" shadow="never">
        <!-- Search Bar -->
        <div class="filter-search">
          <el-input
            v-model="searchQuery"
            placeholder="按镜像名称搜索"
            style="width: 280px"
            clearable
            size="default"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button v-if="hasActiveFilter" text type="warning" @click="resetAllFilters" size="small">
            清除筛选
          </el-button>
        </div>

        <!-- ① 难易程度 -->
        <div class="filter-line">
          <div class="filter-label">难易程度</div>
          <div class="filter-tags">
            <span
              v-for="(item, idx) in difficultyList"
              :key="idx"
              :class="{ active: activeDifficulty === idx }"
              @click="selectDifficulty(idx, item)"
            >{{ item.label }}</span>
          </div>
        </div>

        <!-- ② 开发语言 -->
        <div class="filter-line">
          <div class="filter-label">开发语言</div>
          <div class="filter-tags">
            <span
              v-for="(item, idx) in languageListSlice"
              :key="idx"
              :class="{ active: activeLanguage === idx }"
              @click="selectLanguage(idx, item)"
            >{{ item.value }}</span>
            <span v-if="languageList.length > TAG_LIMIT + 1" class="toggle-btn" @click="toggleTag('language')">
              {{ showAllLanguage ? '收起 ▲' : '更多...' }}
            </span>
          </div>
        </div>

        <!-- ③ 漏洞类型 -->
        <div class="filter-line">
          <div class="filter-label">漏洞类型</div>
          <div class="filter-tags">
            <span
              v-for="(item, idx) in vulnTypeListSlice"
              :key="idx"
              :class="{ active: activeVulnType === idx }"
              @click="selectVulnType(idx, item)"
            >{{ item.value }}</span>
            <span v-if="vulnTypeList.length > TAG_LIMIT + 1" class="toggle-btn" @click="toggleTag('vulnType')">
              {{ showAllVulnType ? '收起 ▲' : '更多...' }}
            </span>
          </div>
        </div>

        <!-- ④ 数据库 -->
        <div class="filter-line">
          <div class="filter-label">数据库</div>
          <div class="filter-tags">
            <span
              v-for="(item, idx) in databaseListSlice"
              :key="idx"
              :class="{ active: activeDatabase === idx }"
              @click="selectDatabase(idx, item)"
            >{{ item.value }}</span>
            <span v-if="databaseList.length > TAG_LIMIT + 1" class="toggle-btn" @click="toggleTag('database')">
              {{ showAllDatabase ? '收起 ▲' : '更多...' }}
            </span>
          </div>
        </div>

        <!-- ⑤ 框架 -->
        <div class="filter-line">
          <div class="filter-label">框架</div>
          <div class="filter-tags">
            <span
              v-for="(item, idx) in frameworkListSlice"
              :key="idx"
              :class="{ active: activeFramework === idx }"
              @click="selectFramework(idx, item)"
            >{{ item.value }}</span>
            <span v-if="frameworkList.length > TAG_LIMIT + 1" class="toggle-btn" @click="toggleTag('framework')">
              {{ showAllFramework ? '收起 ▲' : '更多...' }}
            </span>
          </div>
        </div>
      </el-card>

      <!-- ★ Tabs -->
      <div class="tab-section">
        <el-tabs v-model="activeTab" @tab-change="handleTabChange">
          <el-tab-pane label="全部" name="all" />
          <el-tab-pane label="已启动" name="started" />
        </el-tabs>
      </div>

      <!-- ★ Card List -->
      <div v-loading="loading" class="card-grid">
        <template v-if="!loading && currentList.length > 0">
          <el-row :gutter="[20, 20]">
            <el-col
              v-for="(item, idx) in currentList"
              :key="item.image_id || idx"
              :xs="24"
              :sm="12"
              :md="8"
              :lg="6"
              :xl="6"
            >
              <el-card
                shadow="hover"
                :body-style="{ padding: '16px' }"
                class="image-card"
                @click="item.status && item.status.status === 'running' && openDetail(item)"
              >
                <!-- Header: title + status -->
                <div class="card-header">
                  <div class="card-title-row">
                    <svg-icon icon-class="bug" style="font-size: 18px; margin-right: 6px; flex-shrink: 0;" />
                    <span class="card-title-text" :title="item.image_vul_name">{{ item.image_vul_name }}</span>
                  </div>
                  <div class="card-badges">
                    <!-- 已通过（海关图标） -->
                    <span v-if="item.status && item.status.is_check === true" class="status-badge status-passed" title="已通过">
                      <img :src="customsImg" style="width: 24px; height: 24px;" />
                    </span>
                    <!-- 运行中 -->
                    <span v-else-if="item.status && item.status.status === 'running'" class="status-badge status-running" title="运行中">
                      <el-icon :size="18"><Loading /></el-icon>
                    </span>
                    <!-- 暂停中 -->
                    <span v-else-if="item.status && item.status.status === 'stop'" class="status-badge status-stopped" title="暂停中">
                      <svg-icon icon-class="stop" style="font-size: 18px;" />
                    </span>
                  </div>
                </div>

                <!-- Difficulty Rating -->
                <div class="card-rating">
                  <el-rate
                    v-model="item.rank"
                    disabled
                    show-score
                    text-color="#ff9900"
                    score-template="{value}"
                  />
                </div>

                <!-- Countdown -->
                <div v-if="item.status && item.status.status === 'running' && item.status.end_date && item.status.end_date !== 0" class="card-countdown">
                  <el-icon><Clock /></el-icon>
                  <count-down
                    :key="item.image_id + '_cd'"
                    :current-time="item.status.now"
                    :start-time="item.status.now"
                    :end-time="item.status.end_date"
                    :seconds-txt="''"
                    @end-callback="handleCountdownEnd(item)"
                  />
                </div>
                <div v-else-if="item.status && item.status.status === 'running' && item.status.end_date === 0" class="card-countdown">
                  <el-icon><Clock /></el-icon>
                  <span>永不过期</span>
                </div>

                <!-- Description -->
                <div class="card-desc" :title="item.image_desc">{{ item.image_desc }}</div>

                <!-- Action Buttons -->
                <div class="card-actions">
                  <template v-if="item.status && item.status.status === 'running'">
                    <el-button
                      type="warning"
                      size="small"
                      :loading="item.status.stop_flag"
                      :disabled="item.status.stop_flag"
                      @click.stop="stopContainer(item.status.container_id, item)"
                    >停止</el-button>
                    <el-button
                      type="danger"
                      size="small"
                      :loading="item.status.delete_flag"
                      :disabled="item.status.delete_flag"
                      @click.stop="deleteContainer(item.status.container_id, item)"
                    >删除</el-button>
                  </template>
                  <template v-else>
                    <el-button
                      type="primary"
                      size="small"
                      :loading="item.status && item.status.start_flag"
                      :disabled="item.status && item.status.start_flag"
                      @click.stop="startContainer(item)"
                    >启动</el-button>
                  </template>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </template>
        <!-- Loading Skeleton -->
        <template v-if="loading">
          <el-row :gutter="[20, 20]">
            <el-col v-for="n in 8" :key="n" :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
              <el-card :body-style="{ padding: '16px' }">
                <el-skeleton :rows="4" animated />
              </el-card>
            </el-col>
          </el-row>
        </template>
        <!-- Empty -->
        <el-empty v-if="!loading && currentList.length === 0" description="暂无镜像数据" />
      </div>

      <!-- ★ Pagination -->
      <div v-if="total > pageSize" class="pagination-wrap">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next, jumper"
          background
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'
import ViewerEditor from '@/components/ViewerEditor/index.vue'
import {
  ImgDashboard,
  SubFlag,
  ContainerSTART,
  ContainerDelete,
  ContainerStop,
  getWriteup,
  get_container_status,
} from '@/api/docker'
import { getTask } from '@/api/tasks'
import { gettimetemp, stoptimetemp, publicMethod } from '@/api/timemoudel'
import customsImg from '@/assets/Customs.png'

// =====================================================================
//  Stores & Constants
// =====================================================================
const userStore = useUserStore()
const { greenhand } = storeToRefs(userStore)

const pageSize = 20
const TAG_LIMIT = 10

const difficultyList = [
  { value: 0, label: '全部' },
  { value: 0.5, label: '入门' },
  { value: 2.0, label: '初级' },
  { value: 3.5, label: '中级' },
  { value: 5, label: '高级' },
]

// =====================================================================
//  Reactive State
// =====================================================================

// --- Pagination ---
const currentPage = ref(1)
const total = ref(0)

// --- Data ---
const listData = ref([])
const startedListData = ref([])
const loading = ref(true)

// --- Filter ---
const searchQuery = ref('')
const activeTab = ref('all')
const searchRank = ref(0)

const activeDifficulty = ref(0)
const activeLanguage = ref(0)
const activeVulnType = ref(0)
const activeDatabase = ref(0)
const activeFramework = ref(0)

const selectedTags = reactive({
  language: [],
  vulnType: [],
  database: [],
  framework: [],
})

const languageList = ref([{ value: '全部' }])
const vulnTypeList = ref([{ value: '全部' }])
const databaseList = ref([{ value: '全部' }])
const frameworkList = ref([{ value: '全部' }])

const tagExpanded = reactive({
  language: false,
  vulnType: false,
  database: false,
  framework: false,
})

// --- Dialog ---
const dialogVisible = ref(false)
const detailLoading = ref(false)
const vulHost = ref('')
const vulPort = ref({})
const imagesName = ref('')
const imagesDesc = ref('')
const imagesId = ref('')
const containerId = ref('')
const isFlag = ref(false)
const currentRawItem = ref(null)
const dialogOpenedWithFlag = ref(false)

// --- Flag ---
const flagInput = ref('')
const flagSubmitting = ref(false)

// --- Writeup ---
const writeupDrawer = ref(false)
const writeupLoading = ref(false)
const writeupContent = ref('')

// --- Timer Mode ---
const countList = ref([])
const getTime = ref('')

// --- Polling cleanup refs ---
const pollingTimers = ref([])

// =====================================================================
//  Computed
// =====================================================================
const currentList = computed(() =>
  activeTab.value === 'started' ? startedListData.value : listData.value
)

// Extract unique HostPort values from Docker port mapping:
// {"9000/tcp": [{"HostIp":"0.0.0.0","HostPort":"41444"},...], ...} → ["41444", "42747"]
const vulPortSimple = computed(() => {
  const ports = vulPort.value
  if (!ports || typeof ports !== 'object') return []
  const seen = new Set()
  Object.values(ports).forEach(entries => {
    if (Array.isArray(entries)) {
      entries.forEach(e => {
        if (e && e.HostPort && !seen.has(e.HostPort)) {
          seen.add(e.HostPort)
        }
      })
    }
  })
  return Array.from(seen)
})

// Build clickable URL from host + first port
const accessUrl = computed(() => {
  let host = vulHost.value
  const simplePorts = vulPortSimple.value
  // Fallback to localhost when host is empty but ports exist
  if (!host && simplePorts.length > 0) {
    host = 'localhost'
  }
  if (!host) return ''
  if (simplePorts.length > 0) {
    return `http://${host}:${simplePorts[0]}`
  }
  return `http://${host}`
})

const showAllLanguage = computed(() => tagExpanded.language)
const showAllVulnType = computed(() => tagExpanded.vulnType)
const showAllDatabase = computed(() => tagExpanded.database)
const showAllFramework = computed(() => tagExpanded.framework)

const languageListSlice = computed(() =>
  tagExpanded.language ? languageList.value : languageList.value.slice(0, TAG_LIMIT + 1)
)
const vulnTypeListSlice = computed(() =>
  tagExpanded.vulnType ? vulnTypeList.value : vulnTypeList.value.slice(0, TAG_LIMIT + 1)
)
const databaseListSlice = computed(() =>
  tagExpanded.database ? databaseList.value : databaseList.value.slice(0, TAG_LIMIT + 1)
)
const frameworkListSlice = computed(() =>
  tagExpanded.framework ? frameworkList.value : frameworkList.value.slice(0, TAG_LIMIT + 1)
)

const hasActiveFilter = computed(() =>
  searchRank.value !== 0 ||
  selectedTags.language.length > 0 ||
  selectedTags.vulnType.length > 0 ||
  selectedTags.database.length > 0 ||
  selectedTags.framework.length > 0
)

// =====================================================================
//  Data Fetching
// =====================================================================
function fetchData() {
  loading.value = true
  const tagFilters = collectTags()
  ImgDashboard(searchQuery.value, false, currentPage.value, false, '', searchRank.value, activeTab.value, tagFilters)
    .then(response => {
      const data = response.data
      if (activeTab.value === 'started') {
        startedListData.value = data.results || []
        total.value = data.count || 0
      } else {
        listData.value = data.results || []
        total.value = data.count || 0
      }
      initFilterTags(data)
      resetStatusFlags()
      loading.value = false
    })
    .catch(() => {
      loading.value = false
    })
}

function fetchDataWithFilters(resetPage = true) {
  if (resetPage) currentPage.value = 1
  loading.value = true
  const tagFilters = collectTags()
  ImgDashboard(searchQuery.value, false, currentPage.value, false, '', searchRank.value, activeTab.value, tagFilters)
    .then(response => {
      const data = response.data
      if (activeTab.value === 'started') {
        startedListData.value = data.results || []
        total.value = data.count || 0
      } else {
        listData.value = data.results || []
        total.value = data.count || 0
      }
      initFilterTags(data)
      resetStatusFlags()
      loading.value = false
    })
    .catch(() => {
      loading.value = false
    })
}

function collectTags() {
  return {
    holeType: selectedTags.vulnType,
    devLanguage: selectedTags.language,
    devDatabase: selectedTags.database,
    devClassify: selectedTags.framework,
  }
}

function resetStatusFlags() {
  const lists = activeTab.value === 'started' ? startedListData : listData
  lists.value.forEach(item => {
    if (item.status) {
      item.status.start_flag = false
      item.status.stop_flag = false
      item.status.delete_flag = false
    }
  })
}

const DEFAULT_TAG_OPTIONS = {
  HoleType: ['SQL注入', 'XSS', 'RCE', '文件上传', '反序列化', '命令执行', 'CSRF', 'SSRF', '代码执行', '弱口令', '信息泄露', '未授权访问'],
  devLanguage: ['PHP', 'Java', 'Python', 'Node.js', 'Go', 'Ruby', 'ASP.NET', 'C#', 'Perl'],
  devDatabase: ['MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite', 'Oracle', 'MSSQL'],
  devClassify: ['Laravel', 'Struts2', 'Spring', 'ThinkPHP', 'WordPress', 'Django', 'Flask', 'Tomcat', 'Nginx', 'Apache'],
}

function initFilterTags(data) {
  const degree = data?.degree || {}
  // Try API data first; fall back to hardcoded defaults
  if (degree.HoleType && degree.HoleType.length > 0) {
    vulnTypeList.value = [{ value: '全部' }, ...degree.HoleType.map(v => ({ value: v }))]
  } else if (vulnTypeList.value.length <= 1) {
    vulnTypeList.value = [{ value: '全部' }, ...DEFAULT_TAG_OPTIONS.HoleType.map(v => ({ value: v }))]
  }
  if (degree.devLanguage && degree.devLanguage.length > 0) {
    languageList.value = [{ value: '全部' }, ...degree.devLanguage.map(v => ({ value: v }))]
  } else if (languageList.value.length <= 1) {
    languageList.value = [{ value: '全部' }, ...DEFAULT_TAG_OPTIONS.devLanguage.map(v => ({ value: v }))]
  }
  if (degree.devDatabase && degree.devDatabase.length > 0) {
    databaseList.value = [{ value: '全部' }, ...degree.devDatabase.map(v => ({ value: v }))]
  } else if (databaseList.value.length <= 1) {
    databaseList.value = [{ value: '全部' }, ...DEFAULT_TAG_OPTIONS.devDatabase.map(v => ({ value: v }))]
  }
  if (degree.devClassify && degree.devClassify.length > 0) {
    frameworkList.value = [{ value: '全部' }, ...degree.devClassify.map(v => ({ value: v }))]
  } else if (frameworkList.value.length <= 1) {
    frameworkList.value = [{ value: '全部' }, ...DEFAULT_TAG_OPTIONS.devClassify.map(v => ({ value: v }))]
  }
}

// =====================================================================
//  Filter Handlers
// =====================================================================
function handleSearch() {
  fetchDataWithFilters()
}

function handleTabChange() {
  fetchDataWithFilters()
}

function handlePageChange(page) {
  currentPage.value = page
  fetchData()
}

function selectDifficulty(idx, item) {
  activeDifficulty.value = idx
  searchRank.value = item.value
  fetchDataWithFilters()
}

function selectLanguage(idx, item) {
  activeLanguage.value = idx
  selectedTags.language = item.value === '全部' ? [] : [item.value]
  fetchDataWithFilters()
}

function selectVulnType(idx, item) {
  activeVulnType.value = idx
  selectedTags.vulnType = item.value === '全部' ? [] : [item.value]
  fetchDataWithFilters()
}

function selectDatabase(idx, item) {
  activeDatabase.value = idx
  selectedTags.database = item.value === '全部' ? [] : [item.value]
  fetchDataWithFilters()
}

function selectFramework(idx, item) {
  activeFramework.value = idx
  selectedTags.framework = item.value === '全部' ? [] : [item.value]
  fetchDataWithFilters()
}

function toggleTag(type) {
  tagExpanded[type] = !tagExpanded[type]
}

function resetAllFilters() {
  activeDifficulty.value = 0
  activeLanguage.value = 0
  activeVulnType.value = 0
  activeDatabase.value = 0
  activeFramework.value = 0
  searchRank.value = 0
  selectedTags.language = []
  selectedTags.vulnType = []
  selectedTags.database = []
  selectedTags.framework = []
  searchQuery.value = ''
  fetchDataWithFilters()
}

// =====================================================================
//  Container Lifecycle
// =====================================================================
function startContainer(item) {
  if (!item || !item.image_id) return
  if (!item.status) item.status = {}
  item.status.start_flag = true

  ContainerSTART(item.image_id)
    .then(response => {
      const taskId = response.data && response.data.data
      if (!taskId) {
        item.status.start_flag = false
        ElMessage.error('启动失败：无法获取任务ID')
        return
      }
      const timerId = setInterval(() => {
        getTask(taskId)
          .then(res => {
            const status = res.data.status
            if (status === 1001) return // 进行中

            clearInterval(timerId)
            removeTimer(timerId)
            item.status.start_flag = false

            if (status === 200) {
              const d = res.data.data
              if (d) {
                item.status.status = 'running'
                item.status.container_id = d.id || ''
                item.status.host = d.host || ''
                item.status.port = d.port || '{}'
                item.status.now = d._now || ''
                item.status.start_date = d.start_date || ''
                item.status.end_date = d.end_date || ''
              }
              ElMessage.success('启动成功')
              fetchData()
            } else {
              ElMessage.error(res.data.msg || '启动失败')
              fetchData()
            }
          })
          .catch(() => {
            clearInterval(timerId)
            removeTimer(timerId)
            item.status.start_flag = false
            ElMessage.error('启动失败')
          })
      }, 2000)
      addTimer(timerId)
    })
    .catch(() => {
      item.status.start_flag = false
      ElMessage.error('启动请求失败')
    })
}

function stopContainer(containerId, item, expire = false) {
  if (!containerId) return
  if (!item.status) item.status = {}
  item.status.stop_flag = true

  // 先查当前状态
  get_container_status(containerId)
    .then(response => {
      if (response.data.code === 200 && response.data.status === 'stop') {
        // 已经是停止状态
        item.status.status = 'stop'
        item.status.stop_flag = false
        ElMessage.success('停止成功')
        fetchData()
        return
      }
      // 发起停止请求
      ContainerStop(containerId, expire)
        .then(res => {
          const taskId = res.data && res.data.data
          if (!taskId) {
            item.status.stop_flag = false
            ElMessage.error('停止失败：无法获取任务ID')
            return
          }
          const timerId = setInterval(() => {
            getTask(taskId)
              .then(r => {
                if (r.data.status === 1001) return
                clearInterval(timerId)
                removeTimer(timerId)
                item.status.stop_flag = false

                if (r.data.status === 200) {
                  item.status.status = 'stop'
                  ElMessage.success(r.data.msg || '停止成功')
                } else {
                  ElMessage.error(r.data.msg || '停止失败')
                }
                fetchData()
              })
              .catch(() => {
                clearInterval(timerId)
                removeTimer(timerId)
                item.status.stop_flag = false
              })
          }, 2000)
          addTimer(timerId)
        })
        .catch(() => {
          item.status.stop_flag = false
          ElMessage.error('停止请求失败')
        })
    })
    .catch(() => {
      item.status.stop_flag = false
      ElMessage.error('状态查询失败')
    })
}

function deleteContainer(containerId, item) {
  if (!containerId) return
  if (!item.status) item.status = {}
  item.status.delete_flag = true

  ContainerDelete(containerId)
    .then(response => {
      const taskId = response.data && response.data.data
      if (!taskId) {
        item.status.delete_flag = false
        ElMessage.error('删除失败：无法获取任务ID')
        return
      }
      const timerId = setInterval(() => {
        getTask(taskId)
          .then(res => {
            if (res.data.status === 1001) return
            clearInterval(timerId)
            removeTimer(timerId)
            item.status.delete_flag = false

            if (res.data.status === 200) {
              item.status.status = ''
              item.status.container_id = ''
              ElMessage.success(res.data.msg || '删除成功')
            } else {
              ElMessage.error(res.data.msg || '删除失败')
            }
            fetchData()
          })
          .catch(() => {
            clearInterval(timerId)
            removeTimer(timerId)
            item.status.delete_flag = false
          })
      }, 2000)
      addTimer(timerId)
    })
    .catch(() => {
      item.status.delete_flag = false
      ElMessage.error('删除请求失败')
    })
}

function handleCountdownEnd(item) {
  if (item.status && item.status.status === 'running') {
    stopContainer(item.status.container_id, item, true)
  }
}

// --- Timer Management ---
function addTimer(timerId) {
  pollingTimers.value.push(timerId)
}

function removeTimer(timerId) {
  pollingTimers.value = pollingTimers.value.filter(id => id !== timerId)
}

function clearAllTimers() {
  pollingTimers.value.forEach(id => clearInterval(id))
  pollingTimers.value = []
}

// =====================================================================
//  Detail Dialog
// =====================================================================
function openDetail(item) {
  imagesId.value = item.image_id || ''
  imagesName.value = item.image_vul_name || ''
  imagesDesc.value = item.image_desc || ''
  isFlag.value = item.is_flag || false
  writeupContent.value = item.writeup_date || ''
  currentRawItem.value = item
  dialogOpenedWithFlag.value = false
  detailLoading.value = true
  dialogVisible.value = true

  if (item.status && item.status.status === 'running') {
    vulHost.value = item.status.host || ''
    containerId.value = item.status.container_id || ''
    try {
      vulPort.value = typeof item.status.port === 'string'
        ? JSON.parse(item.status.port)
        : (item.status.port || {})
    } catch {
      vulPort.value = {}
    }
    detailLoading.value = false
  }
}

function handleDialogClose() {
  dialogVisible.value = false
  setTimeout(() => {
    flagInput.value = ''
    writeupDrawer.value = false
  }, 300)
}

// =====================================================================
//  Writeup
// =====================================================================
function openWriteupDrawer() {
  writeupLoading.value = true
  writeupDrawer.value = true
  getWriteup(imagesId.value)
    .then(response => {
      if (response.data.code === 200) {
        writeupContent.value = response.data.data.writeup_date || ''
      }
      writeupLoading.value = false
    })
    .catch(() => {
      writeupLoading.value = false
    })
}

function closeWriteupDrawer() {
  writeupDrawer.value = false
}

// =====================================================================
//  Flag Submission
// =====================================================================
function submitFlag() {
  if (!flagInput.value.trim() || !containerId.value) return
  flagSubmitting.value = true

  SubFlag(containerId.value, flagInput.value.trim())
    .then(response => {
      const data = response.data
      if (data.status === 200) {
        ElMessage.success('恭喜！Flag正确！')
        // 标记为已通过
        if (currentRawItem.value && currentRawItem.value.status) {
          currentRawItem.value.status.is_check = true
        }
        userStore.greenhand = false
        dialogOpenedWithFlag.value = true
        dialogVisible.value = false
        fetchData()
      } else if (data.status === 201) {
        ElMessage.error(data.msg || 'Flag错误，请重试')
      } else {
        ElMessage.error(data.msg || 'Flag验证失败')
      }
      flagInput.value = ''
      flagSubmitting.value = false
    })
    .catch(() => {
      flagSubmitting.value = false
      ElMessage.error('提交失败，请检查网络')
    })
}

// =====================================================================
//  Utility
// =====================================================================
function copyText(text) {
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制')
  })
}

// =====================================================================
//  Timer Mode
// =====================================================================
const TIMER_NOTIF_CLASS = 'timer-countdown-notif'
let countdownTimer = null
let timerModePoll = null
function fetchTimerMode() {
  gettimetemp()
    .then(response => {
      const results = response.data.results || []
      countList.value = results
      // 无活跃计时 → 移除通知、清定时器
      if (results.length === 0) {
        if (countdownTimer) { clearInterval(countdownTimer); countdownTimer = null }
        const oldEl = document.querySelector('.' + TIMER_NOTIF_CLASS)
        if (oldEl) oldEl.remove()
        return
      }
      if (results.length > 0) {
        const item = results[0]
        const endMs = publicMethod.getTimestamp(item.end_date) * 1000

        const formatText = () => {
          const now = Date.now()
          const left = Math.max(0, Math.floor((endMs - now) / 1000))
          const m = Math.floor(left / 60)
          const s = left % 60
          return `剩余 ${m} 分 ${s} 秒`
        }

        // 通知不存在时才创建（整个计时周期只创建一次）
        if (!document.querySelector('.' + TIMER_NOTIF_CLASS)) {
          ElNotification({
            customClass: TIMER_NOTIF_CLASS,
            title: '计时模式',
            message: formatText(),
            duration: 0,
            position: 'bottom-right',
            showClose: false,
          })
        }

        // 重置计数定时器（每秒更新通知文字）
        if (countdownTimer) clearInterval(countdownTimer)
        countdownTimer = setInterval(() => {
          const el = document.querySelector('.' + TIMER_NOTIF_CLASS)
          const content = el?.querySelector?.('.el-notification__content')
          if (content) {
            const text = formatText()
            content.textContent = text
            if (text.includes('剩余 0 分 0 秒')) {
              clearInterval(countdownTimer)
              countdownTimer = null
              el.remove()
              autoStopTimerMode()
            }
          }
        }, 1000)
      }
    })
    .catch(() => {
      // ignore if no timer mode
    })
}

function autoStopTimerMode() {
  stoptimetemp()
    .then(response => {
      const data = response.data || {}
      if (data.code === '2000') {
        ElMessage.success('计时模式已关闭')
      }
    })
    .catch(() => {
      // ignore
    })
}

// =====================================================================
//  Init Time
// =====================================================================
function setCurrentTime() {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  const h = String(now.getHours()).padStart(2, '0')
  const min = String(now.getMinutes()).padStart(2, '0')
  const s = String(now.getSeconds()).padStart(2, '0')
  getTime.value = `${y}-${m}-${d} ${h}:${min}:${s}`
}

// =====================================================================
//  Lifecycle
// =====================================================================
onMounted(() => {
  setCurrentTime()
  fetchData()
  fetchTimerMode()
  timerModePoll = setInterval(fetchTimerMode, 10000)
})

onBeforeUnmount(() => {
  clearAllTimers()
  if (timerModePoll) clearInterval(timerModePoll)
  if (countdownTimer) clearInterval(countdownTimer)
  ElNotification.closeAll()
})
</script>

<style lang="scss" scoped>
.dashboard-container {
  padding: 20px;

  .dashboard-main {
    max-width: 1400px;
    margin: 0 auto;
  }
}

// ── Filter Card ──────────────────────────────────────────────
.filter-card {
  margin-bottom: 16px;
  border-radius: 8px;

  .filter-search {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
  }
}

.filter-line {
  display: flex;
  align-items: flex-start;
  padding: 7px 0;
  border-bottom: 1px dashed #e8ecf1;
  font-size: 13px;

  &:last-of-type {
    border-bottom: none;
  }
}

.filter-label {
  width: 80px;
  min-width: 80px;
  height: 28px;
  line-height: 28px;
  text-align: center;
  color: #fff;
  background: #409eff;
  border-radius: 14px 0 14px 14px;
  margin-right: 16px;
  font-size: 12px;
}

.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  flex: 1;

  span {
    display: inline-block;
    padding: 3px 14px;
    cursor: pointer;
    border-radius: 14px;
    font-size: 13px;
    color: #606266;
    transition: all 0.2s;
    user-select: none;

    &:hover {
      color: #409eff;
      background: #ecf5ff;
    }

    &.active {
      color: #409eff;
      background: #ecf5ff;
      font-weight: 500;
    }
  }

  .toggle-btn {
    color: #409eff !important;
    font-size: 12px;
    opacity: 0.8;

    &:hover {
      opacity: 1;
      background: transparent;
    }
  }
}

// ── Tabs ─────────────────────────────────────────────────────
.tab-section {
  margin-bottom: 16px;
}

// ── Card Grid ────────────────────────────────────────────────
.card-grid {
  min-height: 200px;
}

.image-card {
  cursor: pointer;
  transition: transform 0.25s, box-shadow 0.25s;
  border-radius: 8px;
  overflow: hidden;

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
  }
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.card-title-row {
  display: flex;
  align-items: center;
  overflow: hidden;
  flex: 1;
  min-width: 0;
}

.card-title-text {
  font-weight: 600;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-badges {
  display: flex;
  align-items: center;
  margin-left: 8px;
  flex-shrink: 0;
}

.status-badge {
  display: flex;
  align-items: center;

  &.status-running {
    color: #67c23a;
  }
  &.status-stopped {
    color: #e6a23c;
  }
  &.status-passed {
    color: #909399;
  }
}

.card-rating {
  margin-bottom: 6px;

  :deep(.el-rate) {
    height: auto;
    line-height: 1;
  }
}

.card-countdown {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;

  .el-icon {
    flex-shrink: 0;
  }
}

.card-desc {
  font-size: 12px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 12px;
}

.card-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

// ── Pagination ───────────────────────────────────────────────
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 16px 0;
}

// ── Dialog ───────────────────────────────────────────────────
.dialog-header {
  display: flex;
  align-items: center;
}

.detail-item {
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  font-size: 14px;
  line-height: 1.6;
}

.detail-label {
  min-width: 80px;
  color: #606266;
  flex-shrink: 0;
  font-weight: 500;
}

.detail-value {
  color: #303133;
  word-break: break-all;
}

.port-tag {
  margin-right: 4px;
  margin-bottom: 4px;
}

.access-link {
  color: #409eff;
  text-decoration: none;
  font-weight: 500;

  &:hover {
    text-decoration: underline;
    color: #66b1ff;
  }
}

.flag-section {
  margin-top: 8px;
}

.flag-form {
  max-width: 400px;
}

// ── Writeup ──────────────────────────────────────────────────
.writeup-content {
  min-height: 300px;
}
</style>
