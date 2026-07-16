<template>
  <div class="images-manage-container app-container">
    <el-card shadow="never" v-loading="tableLoading">
      <template #header>
        <div class="card-header">
          <span class="card-title">靶场管理</span>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="按镜像名称搜索"
              style="width: 230px"
              clearable
              size="default"
              @keyup.enter="handleSearch"
            >
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button type="primary" @click="handleSearch">查询</el-button>
            <el-button type="success" @click="openAddDialog('add')">添加</el-button>
            <el-button @click="syncFromWebsite">一键同步</el-button>
          </div>
        </div>
      </template>

      <!-- Image Table -->
      <el-table :data="imageList" stripe border style="width: 100%" @selection-change="handleSelectionChange">
        <el-table-column type="index" label="序号" width="55" align="center" />
        <el-table-column prop="image_name" label="镜像名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="image_vul_name" label="漏洞名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="image_port" label="端口" width="150" show-overflow-tooltip />
        <el-table-column prop="rank" label="分数" width="55" align="center" />
        <el-table-column label="标签" min-width="260">
          <template #default="scope">
            <el-tag
              v-for="(tag, i) in (scope.row.degree || []).slice(0, 4)"
              :key="i"
              size="small"
              style="margin-right: 4px; margin-bottom: 2px;"
            >{{ tag }}</el-tag>
            <el-popover v-if="(scope.row.degree || []).length > 4" placement="top" trigger="hover">
              <template #reference>
                <el-tag size="small">+{{ scope.row.degree.length - 4 }}</el-tag>
              </template>
              <el-tag v-for="(tag, i) in scope.row.degree" :key="i" size="small" style="margin: 2px;">{{ tag }}</el-tag>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column prop="image_desc" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="update_date" label="修改时间" width="160" />
        <el-table-column label="操作" width="290" fixed="right" align="center">
          <template #default="scope">
            <el-button v-if="scope.row.status && scope.row.status.progress_status === 'download'" type="primary" size="small" :icon="Download" @click="showProgress(scope.row, 'download')">
              {{ scope.row.status.progress ? scope.row.status.progress + '%' : '下载中' }}
            </el-button>
            <el-button v-else-if="!scope.row.is_ok" size="small" :icon="Download" @click="handleDownload(scope.row)">下载</el-button>

            <el-button size="small" :icon="Edit" @click="openEditDialog(scope.row)">修改</el-button>

            <el-button size="small" :icon="Delete" type="danger" @click="handleDelete(scope.row)">删除</el-button>

            <el-tag v-if="scope.row.is_share" type="success" size="small">已分享</el-tag>
            <el-button v-else-if="scope.row.status && scope.row.status.progress_status === 'share'" type="primary" size="small" :icon="Share" @click="showProgress(scope.row, 'share')">
              {{ scope.row.status.progress ? scope.row.status.progress + '%' : '分享中' }}
            </el-button>
            <el-button v-else size="small" :icon="Share" @click="handleShare(scope.row)">分享</el-button>
          </template>
        </el-table-column>
      </el-table>

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

    <!-- ══════ Add / Edit Dialog ══════ -->
    <el-dialog
      v-model="formDialogVisible"
      :title="isEditing ? '修改镜像' : '添加镜像'"
      width="700px"
      destroy-on-close
      :close-on-click-modal="false"
    >
      <el-tabs v-model="formTab" @tab-change="handleFormTabChange">
        <el-tab-pane label="添加" name="add" />
        <el-tab-pane label="本地导入" name="local" />
        <el-tab-pane label="Compose编译" name="addcompose" />
      </el-tabs>

      <!-- ── Tab 1: Add Image ── -->
      <div v-show="formTab === 'add'" class="form-tab-content">
        <el-form :model="addForm" label-width="110px" size="small">
          <el-form-item label="漏洞名称">
            <el-input v-model="addForm.image_vul_name" placeholder="输入漏洞名称" />
          </el-form-item>

          <!-- Image Name -->
          <el-form-item label="镜像">
            <el-radio-group v-model="imageInputMode" size="small" style="margin-bottom: 8px;">
              <el-radio-button value="text">文本输入</el-radio-button>
              <el-radio-button value="file">文件上传</el-radio-button>
            </el-radio-group>
            <el-autocomplete
              v-if="imageInputMode === 'text'"
              v-model="addForm.image_name"
              :fetch-suggestions="querySearchImageAsync"
              :trigger-on-focus="false"
              placeholder="输入 Docker 镜像名称(自动补全)"
              value-key="value"
              style="width: 100%"
              clearable
            />
            <el-upload
              v-else
              :before-upload="beforeImageUpload"
              :http-request="handleImageUpload"
              action=""
              :show-file-list="false"
              accept=".tar"
            >
              <el-button type="primary" :icon="Upload">选择 .tar 文件</el-button>
              <span v-if="addForm.image_name" style="margin-left: 8px; color: #67c23a;">已选择: {{ addForm.image_name }}</span>
            </el-upload>
          </el-form-item>

          <!-- Tags -->
          <el-form-item label="漏洞类型">
            <el-tag
              v-for="(t, i) in addForm.HoleType"
              :key="i"
              closable
              size="small"
              style="margin-right: 4px; margin-bottom: 4px;"
              @close="removeTag('HoleType', i)"
            >{{ t }}</el-tag>
            <el-autocomplete
              v-model="newTagInputs.HoleType"
              :fetch-suggestions="(q, cb) => tagSuggestions(q, cb, 'HoleType')"
              placeholder="+ 新标签"
              value-key="value"
              size="small"
              style="width: 120px;"
              trigger-on-focus
              @select="(item) => addTag('HoleType', item.value)"
              @keyup.enter="addTag('HoleType', newTagInputs.HoleType)"
            />
          </el-form-item>
          <el-form-item label="开发语言">
            <el-tag
              v-for="(t, i) in addForm.devLanguage"
              :key="i"
              closable size="small" style="margin-right: 4px; margin-bottom: 4px;"
              @close="removeTag('devLanguage', i)"
            >{{ t }}</el-tag>
            <el-autocomplete
              v-model="newTagInputs.devLanguage"
              :fetch-suggestions="(q, cb) => tagSuggestions(q, cb, 'devLanguage')"
              placeholder="+ 新标签" value-key="value" size="small" style="width: 120px;"
              :trigger-on-focus="true"
              @select="(item) => addTag('devLanguage', item.value)"
              @keyup.enter="addTag('devLanguage', newTagInputs.devLanguage)"
            />
          </el-form-item>
          <el-form-item label="数据库">
            <el-tag
              v-for="(t, i) in addForm.devDatabase"
              :key="i"
              closable size="small" style="margin-right: 4px; margin-bottom: 4px;"
              @close="removeTag('devDatabase', i)"
            >{{ t }}</el-tag>
            <el-autocomplete
              v-model="newTagInputs.devDatabase"
              :fetch-suggestions="(q, cb) => tagSuggestions(q, cb, 'devDatabase')"
              placeholder="+ 新标签" value-key="value" size="small" style="width: 120px;"
              :trigger-on-focus="true"
              @select="(item) => addTag('devDatabase', item.value)"
              @keyup.enter="addTag('devDatabase', newTagInputs.devDatabase)"
            />
          </el-form-item>
          <el-form-item label="分类">
            <el-tag
              v-for="(t, i) in addForm.devClassify"
              :key="i"
              closable size="small" style="margin-right: 4px; margin-bottom: 4px;"
              @close="removeTag('devClassify', i)"
            >{{ t }}</el-tag>
            <el-autocomplete
              v-model="newTagInputs.devClassify"
              :fetch-suggestions="(q, cb) => tagSuggestions(q, cb, 'devClassify')"
              placeholder="+ 新标签" value-key="value" size="small" style="width: 120px;"
              :trigger-on-focus="true"
              @select="(item) => addTag('devClassify', item.value)"
              @keyup.enter="addTag('devClassify', newTagInputs.devClassify)"
            />
          </el-form-item>

          <el-form-item label="Rank">
            <el-input-number v-model="addForm.rank" :min="0.5" :max="5.0" :step="0.5" :precision="1" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="addForm.image_desc" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="Flag">
            <el-switch v-model="addForm.is_flag" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="saving" @click="submitAddForm">提交</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- ── Tab 2: Local Import ── -->
      <div v-show="formTab === 'local'" class="form-tab-content">
        <div class="local-import-toolbar">
          <el-input
            v-model="localSearchQuery"
            placeholder="按名称过滤"
            style="width: 220px"
            size="small"
            clearable
            @input="filterLocalImages"
          />
          <el-button type="primary" size="small" :disabled="selectedLocals.length === 0" @click="importLocalImages">
            一键导入 ({{ selectedLocals.length }})
          </el-button>
        </div>
        <el-table
          ref="localTableRef"
          :data="filteredLocalImages"
          stripe border size="small"
          max-height="360"
          @selection-change="handleLocalSelection"
        >
          <el-table-column type="selection" width="40" />
          <el-table-column prop="image_name" label="名称" min-width="200" />
          <el-table-column label="状态" width="100" align="center">
            <template #default="scope">
              <el-tag v-if="scope.row.flag" type="success" size="small">已导入</el-tag>
              <el-tag v-else type="info" size="small">未导入</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="scope">
              <el-button v-if="scope.row.flag" size="small" type="danger" text>移除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- ── Tab 3: Compose Build ── -->
      <div v-show="formTab === 'addcompose'" class="form-tab-content">
        <p style="color: #909399; font-size: 13px;">通过 Docker Compose 文件编译构建镜像</p>
        <el-input
          v-model="composeYml"
          type="textarea"
          :rows="10"
          placeholder="粘贴 docker-compose.yml 内容..."
          style="margin-bottom: 12px;"
        />
        <el-upload
          :before-upload="(f) => { readFileAsText(f); return false; }"
          action=""
          :show-file-list="false"
          accept=".yml,.yaml"
        >
          <el-button size="small" :icon="Upload">上传 YAML 文件</el-button>
        </el-upload>
        <div style="margin-top: 12px;">
          <el-button type="primary" :loading="composeLoading" @click="buildCompose">编译</el-button>
        </div>
      </div>
    </el-dialog>

    <!-- ══════ Edit Image Dialog ══════ -->
    <el-dialog
      v-model="editDialogVisible"
      title="修改镜像"
      width="700px"
      destroy-on-close
      :close-on-click-modal="false"
    >
      <el-tabs v-model="editTab">
        <el-tab-pane label="修改" name="first" />
        <el-tab-pane v-if="editForm.is_docker_compose" label="Compose修改" name="secnd" />
      </el-tabs>

      <div v-show="editTab === 'first'" class="form-tab-content">
        <el-form :model="editForm" label-width="110px" size="small">
          <el-form-item label="镜像名称">
            <el-input v-model="editForm.image_name" disabled />
          </el-form-item>
          <el-form-item label="漏洞名称">
            <el-input v-model="editForm.image_vul_name" />
          </el-form-item>

          <el-form-item label="漏洞类型">
            <el-tag
              v-for="(t, i) in editForm.HoleType"
              :key="i" closable size="small" style="margin-right: 4px;"
              @close="editForm.HoleType.splice(i, 1)"
            >{{ t }}</el-tag>
            <el-autocomplete
              v-model="editNewTag"
              :fetch-suggestions="(q, cb) => tagSuggestions(q, cb, 'HoleType')"
              placeholder="+ 添加" value-key="value" size="small" style="width: 100px;"
              @select="(item) => { editForm.HoleType.push(item.value); editNewTag = ''; }"
              @keyup.enter="editForm.HoleType.push(editNewTag); editNewTag = ''"
            />
          </el-form-item>
          <el-form-item label="开发语言">
            <el-tag v-for="(t, i) in editForm.devLanguage" :key="i" closable size="small" style="margin-right: 4px;"
              @close="editForm.devLanguage.splice(i, 1)">{{ t }}</el-tag>
            <el-autocomplete v-model="editNewTag2" :fetch-suggestions="(q, cb) => tagSuggestions(q, cb, 'devLanguage')"
              placeholder="+ 添加" value-key="value" size="small" style="width: 100px;"
              @select="(item) => { editForm.devLanguage.push(item.value); editNewTag2 = ''; }"
              @keyup.enter="editForm.devLanguage.push(editNewTag2); editNewTag2 = ''" />
          </el-form-item>
          <el-form-item label="数据库">
            <el-tag v-for="(t, i) in editForm.devDatabase" :key="i" closable size="small" style="margin-right: 4px;"
              @close="editForm.devDatabase.splice(i, 1)">{{ t }}</el-tag>
            <el-autocomplete v-model="editNewTag3" :fetch-suggestions="(q, cb) => tagSuggestions(q, cb, 'devDatabase')"
              placeholder="+ 添加" value-key="value" size="small" style="width: 100px;"
              @select="(item) => { editForm.devDatabase.push(item.value); editNewTag3 = ''; }"
              @keyup.enter="editForm.devDatabase.push(editNewTag3); editNewTag3 = ''" />
          </el-form-item>
          <el-form-item label="分类">
            <el-tag v-for="(t, i) in editForm.devClassify" :key="i" closable size="small" style="margin-right: 4px;"
              @close="editForm.devClassify.splice(i, 1)">{{ t }}</el-tag>
            <el-autocomplete v-model="editNewTag4" :fetch-suggestions="(q, cb) => tagSuggestions(q, cb, 'devClassify')"
              placeholder="+ 添加" value-key="value" size="small" style="width: 100px;"
              @select="(item) => { editForm.devClassify.push(item.value); editNewTag4 = ''; }"
              @keyup.enter="editForm.devClassify.push(editNewTag4); editNewTag4 = ''" />
          </el-form-item>

          <el-form-item label="Rank">
            <el-input-number v-model="editForm.rank" :min="0.5" :max="5.0" :step="0.5" :precision="1" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="editForm.image_desc" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="saving" @click="submitEditForm">保存修改</el-button>
          </el-form-item>
        </el-form>
      </div>

      <div v-show="editTab === 'secnd'" class="form-tab-content">
        <el-input
          v-model="editComposeYml"
          type="textarea"
          :rows="12"
          placeholder="docker-compose.yml 内容"
        />
        <div style="margin-top: 12px; display: flex; gap: 8px;">
          <el-button type="primary" @click="updateCompose">编译</el-button>
          <el-upload
            :before-upload="(f) => { readFileAsText(f, true); return false; }"
            action="" :show-file-list="false" accept=".yml,.yaml"
          >
            <el-button size="small" :icon="Upload">上传 YAML</el-button>
          </el-upload>
        </div>
      </div>
    </el-dialog>

    <!-- ══════ Progress Dialog ══════ -->
    <el-dialog
      v-model="progressDialogVisible"
      :title="progressTitle"
      width="550px"
      :close-on-click-modal="false"
      @close="clearProgressTimer"
    >
      <el-table :data="progressLayers" stripe size="small" max-height="400">
        <el-table-column prop="id" label="层 ID" min-width="180" show-overflow-tooltip />
        <el-table-column label="进度" width="200">
          <template #default="scope">
            <el-progress :percentage="scope.row.progress || 0" :stroke-width="12" />
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- ══════ Delete Confirmation (with container list) ══════ -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="删除确认"
      width="650px"
      :close-on-click-modal="false"
    >
      <p v-if="deleteContainers.length > 0" style="color: #e6a23c; margin-bottom: 12px;">
        该镜像存在运行中的容器，请先删除：
      </p>
      <el-table v-if="deleteContainers.length > 0" :data="deleteContainers" stripe border size="small" max-height="300">
        <el-table-column prop="image_vul_name" label="漏洞名称" min-width="120" />
        <el-table-column prop="user_name" label="用户" width="100" />
        <el-table-column prop="vul_host" label="访问地址" min-width="160" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="s"><el-tag :type="s.row.container_status === 'running' ? 'success' : 'info'" size="small">{{ s.row.container_status }}</el-tag></template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center">
          <template #default="s">
            <el-button type="danger" size="small" @click="deleteSingleContainer(s.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="deleting" @click="confirmDeleteImage">确认删除镜像</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { Search, Download, Edit, Delete, Share, Upload } from '@element-plus/icons-vue'
import { ImgList, get_website_imgs, ContainerINFO } from '@/api/docker'
import { searchImage, ImageAdd, ImageDelete, ImageEdit, ImageLocal, ImageLocalAdd, ImageDownload, ImageShare } from '@/api/image'
import { containerDel } from '@/api/container'
import { getTask, batchTask, progressTask } from '@/api/tasks'
import { build_compose, update_build_compose, uploadFile, deleteFile } from '@/api/layout'

// =====================================================================
//  Constants
// =====================================================================
const pageSize = 20

const tagOptions = reactive({
  HoleType: [],
  devLanguage: [],
  devDatabase: [],
  devClassify: [],
})

// =====================================================================
//  State: Table
// =====================================================================
const imageList = ref([])
const total = ref(0)
const currentPage = ref(1)
const tableLoading = ref(false)
const searchQuery = ref('')

// =====================================================================
//  State: Add/Edit Dialog
// =====================================================================
const formDialogVisible = ref(false)
const formTab = ref('add')
const isEditing = ref(false)
const editingId = ref(null)
const saving = ref(false)
const imageInputMode = ref('text')

const addForm = reactive({
  image_name: '',
  image_vul_name: '',
  rank: 0.5,
  image_desc: '',
  is_flag: false,
  HoleType: [],
  devLanguage: [],
  devDatabase: [],
  devClassify: [],
})

const newTagInputs = reactive({
  HoleType: '',
  devLanguage: '',
  devDatabase: '',
  devClassify: '',
})

// Local import
const localImages = ref([])
const filteredLocalImages = ref([])
const localSearchQuery = ref('')
const selectedLocals = ref([])
const localTableRef = ref(null)

// Compose
const composeYml = ref('')
const composeLoading = ref(false)

// =====================================================================
//  State: Edit Dialog
// =====================================================================
const editDialogVisible = ref(false)
const editTab = ref('first')
const editForm = reactive({
  image_id: '',
  image_name: '',
  image_vul_name: '',
  rank: 0.5,
  image_desc: '',
  is_flag: false,
  is_docker_compose: false,
  HoleType: [],
  devLanguage: [],
  devDatabase: [],
  devClassify: [],
})
const editComposeYml = ref('')
const editNewTag = ref('')
const editNewTag2 = ref('')
const editNewTag3 = ref('')
const editNewTag4 = ref('')

// =====================================================================
//  State: Progress Dialog
// =====================================================================
const progressDialogVisible = ref(false)
const progressTitle = ref('')
const progressLayers = ref([])
let progressTimer = null

// =====================================================================
//  State: Delete
// =====================================================================
const deleteDialogVisible = ref(false)
const deleteImageTarget = ref(null)
const deleteContainers = ref([])
const deleting = ref(false)
const deleteTaskId = ref('')

// =====================================================================
//  State: Task Polling
// =====================================================================
let taskPollTimer = null

// =====================================================================
//  Data Loading
// =====================================================================
async function loadImages(page) {
  tableLoading.value = true
  try {
    const res = await ImgList(searchQuery.value, false, page, false, '', 0)
    const data = res.data
    imageList.value = (data.results || []).map(item => ({
      ...item,
      status: item.status || { progress_status: '', progress: 0 },
    }))
    total.value = data.count || 0
  } catch {
    ElMessage.error('加载镜像列表失败')
  } finally {
    tableLoading.value = false
  }
}


function handlePageChange(page) {
  currentPage.value = page
  loadImages(page)
}

function handleSearch() {
  currentPage.value = 1
  loadImages(1)
}

// =====================================================================
//  Task Polling (for downloads/shares)
// =====================================================================
function startTaskPolling() {
  taskPollTimer = setInterval(async () => {
    const taskIds = []
    const taskMap = {}
    for (const img of imageList.value) {
      if (img.status && img.status.task_id) {
        taskIds.push(img.status.task_id)
        taskMap[img.status.task_id] = img
      }
    }
    if (taskIds.length === 0) return

    try {
      const res = await batchTask({ task_ids: taskIds })
      const statusList = res.data.data || res.data.status || []
      for (const s of statusList) {
        const img = taskMap[s.task_id]
        if (!img) continue
        if (s.status === 200) {
          delete img.status
          ElNotification.success({ title: '任务完成', message: `${img.image_vul_name || img.image_name} 已完成`, duration: 3000 })
        } else if (s.status !== 1001) {
          img.status.progress_status = ''
          img.status.progress = 0
        }
      }
    } catch { /* ignore polling errors */ }
  }, 2000)
}

// =====================================================================
//  Add Image
// =====================================================================
function openAddDialog(tab) {
  formTab.value = tab || 'add'
  formDialogVisible.value = true
  isEditing.value = false
  resetAddForm()
  if (tab === 'local') loadLocalImages()
}

function resetAddForm() {
  addForm.image_name = ''
  addForm.image_vul_name = ''
  addForm.rank = 0.5
  addForm.image_desc = ''
  addForm.is_flag = false
  addForm.HoleType = []
  addForm.devLanguage = []
  addForm.devDatabase = []
  addForm.devClassify = []
  composeYml.value = ''
  imageInputMode.value = 'text'
}

function handleFormTabChange(tab) {
  if (tab === 'local') loadLocalImages()
}

// ── Image suggestions (from Docker Hub via backend proxy) ──
async function querySearchImageAsync(queryString, cb) {
  if (!queryString) { cb([]); return }
  try {
    const res = await searchImage(queryString)
    const data = res.data
    const list = []
    if (data.data && Array.isArray(data.data.summaries)) {
      data.data.summaries.forEach(item => {
        if (item.name) list.push({ value: item.name })
      })
    }
    cb(list.slice(0, 15))
  } catch (err) {
    // Error already displayed by request.js interceptor
    cb([])
  }
}

// ── Tag suggestions ──
const TAG_FALLBACKS = {
  HoleType: ['SQL注入', 'XSS', 'RCE', '文件上传', '反序列化', '命令执行', 'CSRF', 'SSRF', '代码执行', '弱口令', '信息泄露', '未授权访问'],
  devLanguage: ['PHP', 'Java', 'Python', 'Node.js', 'Go', 'Ruby', 'ASP.NET', 'C#', 'Perl'],
  devDatabase: ['MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite', 'Oracle', 'MSSQL'],
  devClassify: ['Laravel', 'Struts2', 'Spring', 'ThinkPHP', 'WordPress', 'Django', 'Flask', 'Tomcat', 'Nginx', 'Apache'],
}

function tagSuggestions(queryString, cb, field) {
  const all = TAG_FALLBACKS[field] || []
  if (!queryString) {
    cb(all.slice(0, 20).map(v => ({ value: v })))
    return
  }
  const filtered = all.filter(v => v.toLowerCase().includes(queryString.toLowerCase()))
  cb(filtered.slice(0, 20).map(v => ({ value: v })))
}

function addTag(field, value) {
  if (!value || !value.trim()) return
  const v = value.trim()
  if (!addForm[field].includes(v)) addForm[field].push(v)
  newTagInputs[field] = ''
}

function removeTag(field, index) {
  addForm[field].splice(index, 1)
}

function beforeImageUpload(file) {
  const isTar = file.name.endsWith('.tar')
  if (!isTar) { ElMessage.error('只支持 .tar 文件'); return false }
  return true
}

function handleImageUpload(options) {
  addForm.image_name = options.file.name
}

async function submitAddForm() {
  if (!addForm.image_vul_name) { ElMessage.warning('请输入漏洞名称'); return }
  saving.value = true
  const formData = new FormData()
  formData.append('image_vul_name', addForm.image_vul_name)
  formData.append('image_name', addForm.image_name)
  formData.append('rank', String(addForm.rank))
  formData.append('image_desc', addForm.image_desc || '')
  formData.append('is_flag', addForm.is_flag ? 'true' : 'false')
  formData.append('HoleType', addForm.HoleType.join(','))
  formData.append('devLanguage', addForm.devLanguage.join(','))
  formData.append('devDatabase', addForm.devDatabase.join(','))
  formData.append('devClassify', addForm.devClassify.join(','))
  try {
    const res = await ImageAdd(formData)
    if (res.data?.status === 200 || res.data?.code === 200) {
      ElMessage.success('镜像添加成功')
      formDialogVisible.value = false
      loadImages(1)
    } else {
      ElMessage.error(res.data?.msg || '添加失败')
    }
  } catch (err) {
    ElMessage.error(err?.response?.data?.msg || '添加失败')
  } finally {
    saving.value = false
  }
}

// =====================================================================
//  Local Import
// =====================================================================
async function loadLocalImages() {
  try {
    const res = await ImageLocal()
    const data = res.data
    // 检查后端返回的业务状态码
    if (data.code && data.code !== 200) {
      ElMessage.warning(data.msg || '加载本地镜像失败')
      localImages.value = []
      filteredLocalImages.value = []
      selectedLocals.value = []
      return
    }
    const list = data.data || data.results || []
    localImages.value = (Array.isArray(list) ? list : []).map(item => ({
      image_name: item.image_name || item.name || item,
      flag: item.flag || item.is_ok || false,
    }))
    filteredLocalImages.value = [...localImages.value]
    selectedLocals.value = []
  } catch {
    ElMessage.error('加载本地镜像失败')
  }
}

function filterLocalImages() {
  const q = localSearchQuery.value.toLowerCase()
  filteredLocalImages.value = localImages.value.filter(item =>
    !q || item.image_name.toLowerCase().includes(q)
  )
}

function handleLocalSelection(selection) {
  selectedLocals.value = selection
}

async function importLocalImages() {
  const names = selectedLocals.value.map(item => item.image_name)
  try {
    // Backend expects form-data: image_names 是逗号分隔的字符串
    const formData = new FormData()
    formData.append('image_names', names.join(','))
    await ImageLocalAdd(formData)
    ElMessage.success('导入成功')
    loadLocalImages()
  } catch (err) {
    ElMessage.error(err?.response?.data?.msg || '导入失败')
  }
}

// =====================================================================
//  Compose Build
// =====================================================================
function readFileAsText(file, isEdit = false) {
  const reader = new FileReader()
  reader.onload = (e) => {
    if (isEdit) editComposeYml.value = e.target.result
    else composeYml.value = e.target.result
  }
  reader.readAsText(file)
}

async function buildCompose() {
  if (!composeYml.value) { ElMessage.warning('请先输入或上传 compose 文件'); return }
  composeLoading.value = true
  try {
    await build_compose({ yml_content: composeYml.value })
    ElMessage.success('编译成功')
    composeYml.value = ''
  } catch (err) {
    ElMessage.error(err?.response?.data?.msg || '编译失败')
  } finally {
    composeLoading.value = false
  }
}

// =====================================================================
//  Edit Image
// =====================================================================
async function openEditDialog(row) {
  editTab.value = 'first'
  editForm.image_id = row.image_id
  editForm.image_name = row.image_name
  editForm.image_vul_name = row.image_vul_name
  editForm.rank = row.rank || 0.5
  editForm.image_desc = row.image_desc || ''
  editForm.is_flag = row.is_flag || false
  editForm.is_docker_compose = row.is_docker_compose || false
  editForm.HoleType = [...(row.HoleType || [])]
  editForm.devLanguage = [...(row.devLanguage || [])]
  editForm.devDatabase = [...(row.devDatabase || [])]
  editForm.devClassify = [...(row.devClassify || [])]
  editComposeYml.value = ''
  editDialogVisible.value = true
}

async function submitEditForm() {
  saving.value = true
  const data = {
    image_vul_name: editForm.image_vul_name,
    rank: editForm.rank,
    image_desc: editForm.image_desc,
    is_flag: editForm.is_flag,
    degree: JSON.stringify({
      HoleType: editForm.HoleType,
      devLanguage: editForm.devLanguage,
      devDatabase: editForm.devDatabase,
      devClassify: editForm.devClassify,
    }),
  }
  try {
    await ImageEdit(editForm.image_id, data)
    ElMessage.success('修改成功')
    editDialogVisible.value = false
    loadImages(currentPage.value)
  } catch (err) {
    ElMessage.error(err?.response?.data?.msg || '修改失败')
  } finally {
    saving.value = false
  }
}

async function updateCompose() {
  if (!editComposeYml.value) { ElMessage.warning('请先输入 compose 内容'); return }
  try {
    await update_build_compose({ image_id: editForm.image_id, yml_content: editComposeYml.value })
    ElMessage.success('Compose 更新成功')
  } catch (err) {
    ElMessage.error(err?.response?.data?.msg || '更新失败')
  }
}

// =====================================================================
//  Download / Share
// =====================================================================
async function handleDownload(row) {
  try {
    await ImageDownload(row.image_id)
    if (!row.status) row.status = {}
    row.status.progress_status = 'download'
    row.status.progress = 0
    ElMessage.success('下载任务已创建')
    loadImages(currentPage.value)
  } catch (err) {
    ElMessage.error(err?.response?.data?.msg || '下载失败')
  }
}

async function handleShare(row) {
  try {
    await ImageShare(row.image_id)
    if (!row.status) row.status = {}
    row.status.progress_status = 'share'
    row.status.progress = 0
    ElMessage.success('分享任务已创建')
    loadImages(currentPage.value)
  } catch (err) {
    ElMessage.error(err?.response?.data?.msg || '分享失败')
  }
}

// ── Progress Dialog ──
function showProgress(row, type) {
  const taskId = row.status?.task_id
  if (!taskId) { ElMessage.info('任务已近完成，请刷新列表'); return }
  progressTitle.value = type === 'download' ? `下载: ${row.image_vul_name || row.image_name}` : `分享: ${row.image_vul_name || row.image_name}`
  progressLayers.value = [{ id: taskId, progress: row.status?.progress || 0 }]
  progressDialogVisible.value = true

  clearProgressTimer()
  progressTimer = setInterval(async () => {
    try {
      const res = await progressTask(taskId)
      const data = res.data
      if (data.progress) {
        progressLayers.value = [{ id: taskId, progress: data.progress }]
      }
      if (data.status === 200 || data.progress >= 100) {
        clearProgressTimer()
        ElMessage.success('任务完成')
        progressDialogVisible.value = false
        loadImages(currentPage.value)
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
//  Delete
// =====================================================================
async function handleDelete(row) {
  deleteImageTarget.value = row
  try {
    const res = await ContainerINFO(row.image_id)
    const containers = res.data.results || res.data.containers || []
    if (containers.length > 0) {
      deleteContainers.value = containers
      deleteDialogVisible.value = true
    } else {
      await ElMessageBox.confirm(`确定删除镜像 "${row.image_vul_name || row.image_name}"？`, '确认')
      await ImageDelete(row.image_id)
      ElMessage.success('删除成功')
      loadImages(currentPage.value)
    }
  } catch (err) {
    if (err === 'cancel') return
    // Direct delete attempt
    try {
      await ImageDelete(row.image_id)
      ElMessage.success('删除成功')
      loadImages(currentPage.value)
    } catch (e) {
      ElMessage.error(e?.response?.data?.msg || '删除失败')
    }
  }
}

async function deleteSingleContainer(row) {
  try {
    await containerDel(row.container_id)
    ElMessage.success('容器已删除')
    deleteContainers.value = deleteContainers.value.filter(c => c.container_id !== row.container_id)
  } catch {
    ElMessage.error('删除容器失败')
  }
}

async function confirmDeleteImage() {
  deleting.value = true
  try {
    await ImageDelete(deleteImageTarget.value.image_id)
    ElMessage.success('镜像已删除')
    deleteDialogVisible.value = false
    loadImages(currentPage.value)
  } catch (err) {
    ElMessage.error(err?.response?.data?.msg || '删除失败')
  } finally {
    deleting.value = false
  }
}

// =====================================================================
//  Sync from Website
// =====================================================================
async function syncFromWebsite() {
  try {
    await get_website_imgs()
    ElMessage.success('同步任务已创建，请稍后刷新列表查看')
    loadImages(1)
  } catch {
    ElMessage.error('同步失败')
  }
}

// =====================================================================
//  Misc
// =====================================================================
function handleSelectionChange() { /* no-op for now */ }

// =====================================================================
//  Lifecycle
// =====================================================================
onMounted(() => {
  loadImages(1)
  startTaskPolling()
})

onBeforeUnmount(() => {
  if (taskPollTimer) clearInterval(taskPollTimer)
  clearProgressTimer()
})
</script>

<style lang="scss" scoped>
.images-manage-container {
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

    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
  }

  .pagination-wrap {
    display: flex;
    justify-content: center;
    margin-top: 20px;
    padding: 8px 0;
  }
}

.form-tab-content {
  min-height: 200px;
  padding: 8px 0;
}

.local-import-toolbar {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 12px;
}
</style>
