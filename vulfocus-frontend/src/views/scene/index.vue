<template>
  <div class="scene-detail-container app-container">
    <el-row :gutter="24">
      <!-- Main Content (16 cols) -->
      <el-col :xs="24" :md="17" :lg="16">
        <!-- Scene Info Card -->
        <el-card shadow="never" class="detail-card">
          <template #header>
            <div class="detail-header">
              <span>{{ layoutInfo?.name || '场景详情' }}</span>
              <el-tag v-if="isRunning" type="success" effect="dark">运行中</el-tag>
              <el-tag v-else type="info">未启动</el-tag>
            </div>
          </template>

          <div v-loading="loading" class="detail-body">
            <div v-if="!loading">
              <!-- Image -->
              <el-image
                :src="layoutInfo?.image_name"
                fit="cover"
                class="detail-img"
              >
                <template #error>
                  <div class="img-placeholder"><el-icon :size="48"><Picture /></el-icon></div>
                </template>
              </el-image>

              <!-- Name & Difficulty -->
              <h2>{{ layoutInfo?.name }}</h2>
              <div class="detail-rate">
                <el-rate v-model="difficulty" disabled />
              </div>

              <!-- Progress & Rank -->
              <el-row :gutter="16" class="detail-stats">
                <el-col :span="8">
                  <div class="stat-box">
                    <span class="stat-label">当前进度</span>
                    <el-progress :percentage="progressPct" :stroke-width="10" />
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="stat-box">
                    <span class="stat-label">当前排名</span>
                    <span class="stat-value">{{ currentRank > 0 ? `#${currentRank}` : '未上榜' }}</span>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="stat-box">
                    <span class="stat-label">当前积分</span>
                    <span class="stat-value score">{{ currentScore }}</span>
                  </div>
                </el-col>
              </el-row>

              <!-- Flag Submit -->
              <div class="flag-section">
                <el-input v-model="flagInput" placeholder="输入 Flag" style="width: 300px" />
                <el-button type="primary" :loading="flagLoading" @click="submitFlag">提交</el-button>
              </div>

              <!-- Admin Controls -->
              <div v-if="isAdmin" class="admin-actions">
                <el-button type="success" :loading="startLoading" @click="startScene">
                  启动场景
                </el-button>
                <el-button type="warning" :loading="stopLoading" @click="stopScene">
                  停止场景
                </el-button>
              </div>

              <!-- Completion Stats -->
              <div class="completion-stats">
                <span>完成人数：通过 {{ passCount }} / 未通过 {{ failCount }}</span>
              </div>

              <!-- Environment Description -->
              <el-divider />
              <div class="section-title">环境描述</div>
              <div class="env-desc">
                <ViewerEditor v-model="layoutDesc" height="300px" />
              </div>
              <el-button v-if="isAdmin" link type="primary" @click="openDescEditor">编辑描述</el-button>

              <!-- Access URLs -->
              <el-divider />
              <div class="section-title">访问地址</div>
              <div v-if="openList.length > 0" class="url-list">
                <div v-for="(url, i) in openList" :key="i" class="url-item">
                  <el-tag>{{ url }}</el-tag>
                  <el-button link type="primary" :icon="Link" @click="openUrl(url)" />
                </div>
              </div>
              <span v-else class="no-data">暂无访问地址</span>

              <!-- Comments -->
              <el-divider />
              <div class="section-title">评论 ({{ commentList.length }})</div>
              <div class="comment-input-area">
                <el-input
                  v-model="commentContent"
                  type="textarea"
                  :rows="3"
                  maxlength="500"
                  show-word-limit
                  placeholder="写下你的评论..."
                />
                <el-button type="primary" @click="showCaptchaDialog">发表评论</el-button>
              </div>

              <div class="comment-list">
                <div v-for="c in commentList" :key="c.comment_id" class="comment-item">
                  <el-avatar :size="32" :src="c.user_avatar" />
                  <div class="comment-body">
                    <div class="comment-header">
                      <span class="comment-user">{{ c.username }}</span>
                      <span class="comment-time">{{ c.create_time }}</span>
                    </div>
                    <div class="comment-content">{{ c.content }}</div>
                  </div>
                  <el-button
                    v-if="isAdmin || c.username === currentUser"
                    text type="danger" size="small"
                    @click="deleteComment(c.comment_id)"
                  >删除</el-button>
                </div>
                <el-empty v-if="commentList.length === 0" description="暂无评论" :image-size="60" />
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Sidebar - Rankings (7 cols) -->
      <el-col :xs="24" :md="7" :lg="7">
        <el-card shadow="never" class="rank-sidebar">
          <template #header><span>场景排名</span></template>
          <el-table :data="rankList" v-loading="rankLoading" stripe size="small" max-height="400">
            <el-table-column label="#" width="50" align="center">
              <template #default="scope">
                <svg-icon v-if="scope.$index === 0" icon-class="trophy1" class="trophy g" />
                <svg-icon v-else-if="scope.$index === 1" icon-class="trophy2" class="trophy s" />
                <svg-icon v-else-if="scope.$index === 2" icon-class="trophy3" class="trophy b" />
                <span v-else>{{ scope.$index + 1 }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="username" label="用户" min-width="80" />
            <el-table-column prop="score" label="积分" width="60" align="center" />
          </el-table>
          <div class="rank-pagination">
            <el-pagination
              v-if="rankTotal > 20"
              :page-size="20"
              :total="rankTotal"
              layout="prev, pager, next"
              small
              @current-change="fetchRank"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Description Editor Drawer (admin) -->
    <el-drawer v-model="descDrawer" title="编辑环境描述" size="40%">
      <MarkdownEditor v-model="editDescContent" height="400px" />
      <template #footer>
        <el-button @click="descDrawer = false">取消</el-button>
        <el-button type="primary" :loading="savingDesc" @click="saveDesc">保存</el-button>
      </template>
    </el-drawer>

    <!-- Captcha Dialog -->
    <el-dialog v-model="captchaDialog" title="验证码验证" width="360px" destroy-on-close>
      <verification ref="captchaRef" @update:code="captchaCode = $event" />
      <el-input v-model="captchaInput" placeholder="输入验证码" style="margin-top: 12px" />
      <template #footer>
        <el-button @click="captchaDialog = false">取消</el-button>
        <el-button type="primary" @click="verifyCaptcha">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { sceneGet, sceneStart, sceneStop, sceneFlag, sceneRank, getSceneData } from '@/api/scene'
import { getComment, commitComment, CommentDelete } from '@/api/user'
import { updateLayoutDesc } from '@/api/layout'
import ViewerEditor from '@/components/ViewerEditor/index.vue'
import MarkdownEditor from '@/components/MarkdownEditor/index.vue'
import Verification from './components/verification.vue'
import { Link } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const layoutId = computed(() => route.params.id)
const isAdmin = computed(() => userStore.roles?.includes('admin'))
const currentUser = computed(() => userStore.name)
const isRunning = ref(false)
const loading = ref(true)
const difficulty = ref(0)

const layoutInfo = ref(null)
const layoutDesc = ref('')
const openList = ref([])
const progressPct = ref(0)
const currentRank = ref(0)
const currentScore = ref(0)
const passCount = ref(0)
const failCount = ref(0)

// Flag
const flagInput = ref('')
const flagLoading = ref(false)

// Admin controls
const startLoading = ref(false)
const stopLoading = ref(false)

// Description editor
const descDrawer = ref(false)
const editDescContent = ref('')
const savingDesc = ref(false)

// Rankings
const rankList = ref([])
const rankTotal = ref(0)
const rankLoading = ref(false)

// Comments
const commentList = ref([])
const commentContent = ref('')

// Captcha
const captchaDialog = ref(false)
const captchaInput = ref('')
const captchaCode = ref('')
const captchaRef = ref(null)

function fetchDetail() {
  loading.value = true
  sceneGet(layoutId.value)
    .then(response => {
      const data = response.data.data || {}
      layoutInfo.value = data.layout || data
      layoutDesc.value = data.layout?.desc || ''
      openList.value = data.open || []
      isRunning.value = data.is_run || false
      loading.value = false
    })
    .catch(() => {
      loading.value = false
      ElMessage.error('获取场景详情失败')
    })
}

function fetchRank(page = 1) {
  rankLoading.value = true
  sceneRank(layoutId.value, page)
    .then(response => {
      const data = response.data.data || response.data
      rankList.value = data.results || []
      rankTotal.value = data.count || 0
      rankLoading.value = false
    })
    .catch(() => {
      rankLoading.value = false
    })
}

function fetchComments() {
  getComment(layoutId.value)
    .then(response => {
      commentList.value = response.data.results || []
    })
    .catch(() => {})
}

function submitFlag() {
  if (!flagInput.value.trim()) return
  flagLoading.value = true
  sceneFlag(layoutId.value, flagInput.value.trim())
    .then(response => {
      const data = response.data
      if (data.status === 200 || data.code === 200) {
        ElMessage.success('Flag 正确！')
        fetchRank(1)
      } else {
        ElMessage.error(data.msg || 'Flag 错误')
      }
      flagInput.value = ''
      flagLoading.value = false
    })
    .catch(() => {
      flagLoading.value = false
    })
}

function startScene() {
  startLoading.value = true
  sceneStart(layoutId.value)
    .then(response => {
      const body = response.data || {}
      if (body.status !== 200 && body.code !== 200) {
        ElMessage.error(body.msg || '启动失败')
        startLoading.value = false
        return
      }
      const data = body.data || {}
      openList.value = data.open || []
      ElMessage.success('场景启动成功')
      isRunning.value = true
      startLoading.value = false
      fetchDetail()
    })
    .catch(() => {
      ElMessage.error('启动请求失败')
      startLoading.value = false
    })
}

function stopScene() {
  stopLoading.value = true
  sceneStop(layoutId.value)
    .then(() => {
      ElMessage.success('场景已停止')
      isRunning.value = false
      stopLoading.value = false
    })
    .catch(() => {
      stopLoading.value = false
    })
}

function openDescEditor() {
  editDescContent.value = layoutDesc.value
  descDrawer.value = true
}

function saveDesc() {
  savingDesc.value = true
  updateLayoutDesc(layoutId.value, { desc: editDescContent.value })
    .then(() => {
      ElMessage.success('描述已更新')
      layoutDesc.value = editDescContent.value
      descDrawer.value = false
      savingDesc.value = false
    })
    .catch(() => {
      savingDesc.value = false
    })
}

function openUrl(url) {
  window.open(`http://${url}`, '_blank')
}

function showCaptchaDialog() {
  if (!commentContent.value.trim()) {
    ElMessage.warning('请先输入评论内容')
    return
  }
  captchaDialog.value = true
  setTimeout(() => captchaRef.value?.refreshCode(), 200)
}

function verifyCaptcha() {
  if (captchaInput.value.toLowerCase() !== captchaCode.value.toLowerCase()) {
    ElMessage.error('验证码错误')
    captchaRef.value?.refreshCode()
    captchaInput.value = ''
    return
  }
  // Submit comment
  commitComment({
    sceneId: layoutId.value,
    content: commentContent.value,
  })
    .then(() => {
      ElMessage.success('评论发表成功')
      commentContent.value = ''
      captchaDialog.value = false
      captchaInput.value = ''
      fetchComments()
    })
    .catch(() => {
      ElMessage.error('评论发表失败')
    })
}

function deleteComment(commentId) {
  CommentDelete(commentId)
    .then(() => {
      ElMessage.success('评论已删除')
      fetchComments()
    })
    .catch(() => {
      ElMessage.error('删除失败')
    })
}

onMounted(() => {
  fetchDetail()
  fetchRank(1)
  fetchComments()
})
</script>

<style lang="scss" scoped>
.scene-detail-container {
  padding: 20px;

  .detail-card {
    border-radius: 8px;
    margin-bottom: 20px;

    .detail-header {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .detail-body {
      min-height: 300px;
    }

    .detail-img {
      width: 100%;
      max-height: 300px;
      border-radius: 6px;
      margin-bottom: 16px;
    }

    .img-placeholder {
      height: 200px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f0f2f5;
      color: #c0c4cc;
      border-radius: 6px;
    }

    h2 {
      margin: 0 0 8px;
    }

    .detail-rate { margin-bottom: 16px; }

    .detail-stats { margin-bottom: 16px; }

    .stat-box {
      background: #f9fafb;
      border-radius: 8px;
      padding: 12px;
      text-align: center;
      .stat-label { font-size: 12px; color: #909399; display: block; margin-bottom: 4px; }
      .stat-value { font-size: 20px; font-weight: 600; &.score { color: #e6a23c; } }
    }

    .flag-section {
      display: flex; gap: 10px; align-items: center; margin-bottom: 16px;
    }

    .admin-actions {
      display: flex; gap: 10px; margin-bottom: 16px;
    }

    .completion-stats {
      font-size: 13px; color: #606266; margin-bottom: 16px;
    }

    .section-title { font-size: 15px; font-weight: 600; margin-bottom: 8px; }
    .env-desc { margin-bottom: 8px; }
    .url-list { display: flex; flex-wrap: wrap; gap: 8px; }
    .url-item { display: flex; align-items: center; gap: 4px; }
    .no-data { color: #c0c4cc; font-size: 13px; }

    .comment-input-area {
      display: flex; gap: 10px; align-items: flex-start; margin-bottom: 16px;
      .el-textarea { flex: 1; }
    }

    .comment-list { margin-top: 8px; }

    .comment-item {
      display: flex; gap: 12px; padding: 12px 0; border-bottom: 1px solid #f0f2f5;
      .comment-body { flex: 1; }
      .comment-header {
        display: flex; justify-content: space-between; margin-bottom: 4px;
        .comment-user { font-weight: 500; font-size: 13px; }
        .comment-time { font-size: 11px; color: #c0c4cc; }
      }
      .comment-content { font-size: 13px; color: #606266; }
    }
  }

  .rank-sidebar {
    border-radius: 8px;
    .trophy { width: 18px; height: 18px; }
    .trophy.g { color: #ffd700; }
    .trophy.s { color: #c0c0c0; }
    .trophy.b { color: #cd7f32; }
    .rank-pagination { margin-top: 12px; display: flex; justify-content: center; }
  }
}
</style>
