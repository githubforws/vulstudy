<template>
  <div class="scene-detail-container app-container">
    <el-row :gutter="24">
      <!-- Main Content (16 cols) -->
      <el-col :xs="24" :md="17" :lg="16">
        <el-card shadow="never" class="detail-card">
          <template #header>
            <div class="detail-header">
              <span>{{ sceneName || '计时场景' }}</span>
              <el-tag v-if="isRunning" type="success" effect="dark">运行中</el-tag>
              <el-tag v-else type="info">未启动</el-tag>
            </div>
          </template>

          <div v-loading="loading" class="detail-body">
            <div v-if="!loading">
              <!-- Image -->
              <el-image
                :src="sceneImage ? '/images/' + sceneImage : ''"
                fit="cover"
                class="detail-img"
              >
                <template #error>
                  <div class="img-placeholder"><el-icon :size="48"><Picture /></el-icon></div>
                </template>
              </el-image>

              <h2>{{ sceneName }}</h2>

              <!-- Timer Info -->
              <el-row :gutter="16" class="detail-stats">
                <el-col :span="8">
                  <div class="stat-box">
                    <span class="stat-label">计时时间</span>
                    <span class="stat-value">{{ timerMinutes }} 分钟</span>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="stat-box">
                    <span class="stat-label">Rank范围</span>
                    <span class="stat-value">{{ rankRange || '-' }}</span>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="stat-box">
                    <span class="stat-label">当前积分</span>
                    <span class="stat-value score">{{ currentScore }}</span>
                  </div>
                </el-col>
              </el-row>

              <!-- Current Rank -->
              <div class="current-rank">
                当前排名：<strong>{{ currentRank > 0 ? `#${currentRank}` : '未上榜' }}</strong>
              </div>

              <!-- Countdown -->
              <div v-if="isRunning && endTime" class="countdown-section">
                <el-icon :size="20"><Clock /></el-icon>
                <count-down
                  :current-time="currentTime"
                  :start-time="currentTime"
                  :end-time="endTime"
                  day-txt="天"
                  hour-txt="小时"
                  minutes-txt="分钟"
                  seconds-txt="秒"
                  :auto-start="true"
                  @end-callback="handleTimerEnd"
                />
              </div>

              <!-- Actions (admin only) -->
              <div v-if="isAdmin" class="timer-actions">
                <el-button v-if="!isRunning" type="primary" :loading="startLoading" @click="startTimer">
                  启动计时
                </el-button>
                <el-button v-else type="warning" :loading="stopLoading" @click="stopTimer">
                  停止计时
                </el-button>
              </div>

              <!-- Participants -->
              <div class="participants">参加人数：{{ participantCount }}</div>

              <!-- Description -->
              <el-divider />
              <div class="section-title">盲盒描述</div>
              <p class="scene-desc">{{ sceneDesc }}</p>

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

      <!-- Sidebar - Rankings -->
      <el-col :xs="24" :md="7" :lg="7">
        <el-card shadow="never" class="rank-sidebar">
          <template #header><span>计时排名</span></template>
          <el-table :data="rankList" v-loading="rankLoading" stripe size="small" max-height="400">
            <el-table-column label="#" width="50" align="center">
              <template #default="scope">
                <svg-icon v-if="scope.$index === 0" icon-class="trophy1" class="trophy g" />
                <svg-icon v-else-if="scope.$index === 1" icon-class="trophy2" class="trophy s" />
                <svg-icon v-else-if="scope.$index === 2" icon-class="trophy3" class="trophy b" />
                <span v-else>{{ scope.$index + 1 }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="name" label="用户" min-width="80" />
            <el-table-column prop="rank" label="积分" width="60" align="center" />
          </el-table>
          <div class="rank-pagination">
            <el-pagination
              v-if="rankTotal > 20"
              :page-size="20"
              :total="rankTotal"
              layout="prev, pager, next"
              small
              @current-change="fetchTimeRank"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Captcha Dialog -->
    <el-dialog v-model="captchaDialog" title="验证码验证" width="360px" destroy-on-close>
      <Verification ref="captchaRef" @update:code="captchaCode = $event" />
      <el-input v-model="captchaInput" placeholder="输入验证码" style="margin-top: 12px" />
      <template #footer>
        <el-button @click="captchaDialog = false">取消</el-button>
        <el-button type="primary" @click="verifyCaptcha">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { sceneGetTemp } from '@/api/timemoudel'
import { start as startTimerMode, stoptimetemp, gettimetemp, timeranklist, publicMethod } from '@/api/timemoudel'
import { getComment, commitComment, CommentDelete } from '@/api/user'
import CountDown from '@chenfengyuan/vue-countdown'
import Verification from './components/verification.vue'

const route = useRoute()
const userStore = useUserStore()

const tempId = computed(() => route.params.id)
const isAdmin = computed(() => userStore.roles?.includes('admin'))
const currentUser = computed(() => userStore.name)

// State
const loading = ref(true)
const sceneName = ref('')
const sceneDesc = ref('')
const sceneImage = ref('')
const isRunning = ref(false)
const timerMinutes = ref(0)
const rankRange = ref('')
const currentRank = ref(0)
const currentScore = ref(0)
const participantCount = ref(0)
const currentTime = ref(Math.floor(Date.now() / 1000))
const endTime = ref(0)

// Actions
const startLoading = ref(false)
const stopLoading = ref(false)

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

let timerInterval = null
let statusPollInterval = null

function fetchDetail() {
  loading.value = true
  sceneGetTemp(tempId.value)
    .then(response => {
      const data = response.data.data || response.data
      sceneName.value = data.name || data.layout_name || ''
      sceneDesc.value = data.desc || data.layout_desc || ''
      sceneImage.value = data.image_name || ''
      timerMinutes.value = data.timer_minutes || data.time_minutes || 0
      rankRange.value = data.rank_range || ''
      loading.value = false
    })
    .catch(() => {
      loading.value = false
    })
}

function fetchTimeRank(page = 1) {
  rankLoading.value = true
  timeranklist(tempId.value, page)
    .then(response => {
      const data = response.data
      rankList.value = data.results || []
      rankTotal.value = data.count || 0
      currentRank.value = data.current_rank || 0
      currentScore.value = data.current_score || 0
      rankLoading.value = false
    })
    .catch(() => {
      rankLoading.value = false
    })
}

function fetchComments() {
  getComment(tempId.value)
    .then(response => {
      commentList.value = response.data.results || []
    })
    .catch(() => {})
}

function checkTimerStatus() {
  // 轮询全局计时会话状态，所有用户均可查看
  gettimetemp()
    .then(response => {
      const results = response.data.results || response.data
      if (Array.isArray(results) && results.length > 0) {
        const session = results[0]
        isRunning.value = true
        endTime.value = publicMethod.getTimestamp(session.end_date || session.end_time)
        if (!timerInterval) {
          startTimerTick()
        }
      } else {
        isRunning.value = false
        endTime.value = 0
        if (timerInterval) {
          clearInterval(timerInterval)
          timerInterval = null
        }
      }
    })
    .catch(() => {})
}

function startTimer() {
  startLoading.value = true
  startTimerMode({ temp_id: tempId.value })
    .then(response => {
      const data = response.data
      if (data.code === '2000' || data.code === '200' || data.status === 200) {
        ElMessage.success('计时已启动')
        // 轮询获取全局会话状态
        checkTimerStatus()
      } else {
        ElMessage.error(data.msg || '启动失败')
      }
      startLoading.value = false
    })
    .catch(() => {
      startLoading.value = false
    })
}

function stopTimer() {
  stopLoading.value = true
  stoptimetemp()
    .then(() => {
      ElMessage.success('计时已停止')
      isRunning.value = false
      endTime.value = 0
      if (timerInterval) {
        clearInterval(timerInterval)
        timerInterval = null
      }
      stopLoading.value = false
    })
    .catch(() => {
      stopLoading.value = false
    })
}

function startTimerTick() {
  timerInterval = setInterval(() => {
    currentTime.value = Math.floor(Date.now() / 1000)
  }, 1000)
}

function handleTimerEnd() {
  ElMessage.info('计时结束')
  isRunning.value = false
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
  commitComment({
    sceneId: tempId.value,
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
  fetchTimeRank(1)
  fetchComments()
  checkTimerStatus()
  // 每 5 秒轮询一次全局计时状态
  statusPollInterval = setInterval(checkTimerStatus, 5000)
})

onBeforeUnmount(() => {
  if (timerInterval) clearInterval(timerInterval)
  if (statusPollInterval) clearInterval(statusPollInterval)
})
</script>

<style lang="scss" scoped>
.scene-detail-container {
  padding: 20px;

  .detail-card {
    border-radius: 8px;
    margin-bottom: 20px;

    .detail-header {
      display: flex; align-items: center; gap: 12px;
    }

    .detail-body { min-height: 300px; }
    .detail-img { width: 100%; max-height: 300px; border-radius: 6px; margin-bottom: 16px; }

    .img-placeholder {
      height: 200px; display: flex; align-items: center; justify-content: center;
      background: #f0f2f5; color: #c0c4cc; border-radius: 6px;
    }

    h2 { margin: 0 0 16px; }

    .detail-stats { margin-bottom: 16px; }
    .stat-box { background: #f9fafb; border-radius: 8px; padding: 12px; text-align: center;
      .stat-label { font-size: 12px; color: #909399; display: block; margin-bottom: 4px; }
      .stat-value { font-size: 20px; font-weight: 600; &.score { color: #e6a23c; } }
    }

    .current-rank { font-size: 14px; margin-bottom: 12px; }
    .countdown-section { display: flex; align-items: center; gap: 8px; font-size: 16px; margin-bottom: 12px; color: #e6a23c; font-weight: 600; }
    .timer-actions { margin-bottom: 12px; }
    .participants { font-size: 13px; color: #909399; margin-bottom: 12px; }
    .section-title { font-size: 15px; font-weight: 600; margin-bottom: 8px; }
    .scene-desc { color: #606266; font-size: 14px; line-height: 1.7; }

    .comment-input-area { display: flex; gap: 10px; align-items: flex-start; margin-bottom: 16px; .el-textarea { flex: 1; } }

    .comment-item { display: flex; gap: 12px; padding: 12px 0; border-bottom: 1px solid #f0f2f5;
      .comment-body { flex: 1; }
      .comment-header { display: flex; justify-content: space-between; margin-bottom: 4px;
        .comment-user { font-weight: 500; font-size: 13px; }
        .comment-time { font-size: 11px; color: #c0c4cc; }
      }
      .comment-content { font-size: 13px; color: #606266; }
    }
  }

  .rank-sidebar { border-radius: 8px;
    .trophy { width: 18px; height: 18px; }
    .trophy.g { color: #ffd700; }
    .trophy.s { color: #c0c0c0; }
    .trophy.b { color: #cd7f32; }
    .rank-pagination { margin-top: 12px; display: flex; justify-content: center; }
  }
}
</style>
