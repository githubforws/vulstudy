<template>
  <div class="notice-manage-container app-container">
    <el-card shadow="never" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span class="card-title">公告管理</span>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="按公告名称搜索"
              style="width: 230px"
              clearable
              size="default"
              @keyup.enter="handleSearch"
            >
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button type="primary" @click="handleSearch">查询</el-button>
            <el-button type="success" @click="openAddDrawer">添加</el-button>
          </div>
        </div>
      </template>

      <!-- Notice Table -->
      <el-table :data="noticeList" stripe border style="width: 100%">
        <el-table-column type="index" label="序号" width="55" align="center" />
        <el-table-column prop="title" label="公告名称" min-width="240" show-overflow-tooltip />
        <el-table-column prop="update_date" label="修改时间" min-width="170" show-overflow-tooltip />
        <el-table-column label="最新发布" width="130" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.is_newest ? 'success' : 'info'" size="small">
              {{ scope.row.is_newest ? 'YES' : 'NO' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="360" fixed="right" align="center">
          <template #default="scope">
            <!-- Not published -->
            <template v-if="!scope.row.is_public">
              <el-button size="small" :icon="Edit" @click="openEditDrawer(scope.row)">修改</el-button>
              <el-button size="small" :icon="View" @click="openViewDrawer(scope.row)">查看</el-button>
              <el-button size="small" type="primary" :icon="Upload" @click="handlePublish(scope.row)">发布</el-button>
              <el-button size="small" type="danger" :icon="Delete" @click="handleDelete(scope.row)">删除</el-button>
            </template>
            <!-- Published -->
            <template v-else>
              <el-button size="small" :icon="View" @click="openViewDrawer(scope.row)">查看</el-button>
              <el-tag type="success" size="small" style="margin: 0 4px;">已发布</el-tag>
              <el-button size="small" type="danger" :icon="Delete" @click="handleDelete(scope.row)">删除</el-button>
            </template>
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

    <!-- ═══ Add Notice Drawer ═══ -->
    <el-drawer
      v-model="addDrawerVisible"
      title="添加公告"
      size="50%"
      direction="btt"
      destroy-on-close
      :before-close="closeAddDrawer"
    >
      <template #extra>
        <el-button type="primary" :loading="addSaving" @click="handleAddSubmit">提交</el-button>
      </template>

      <div class="drawer-body">
        <el-input
          v-model="addForm.title"
          placeholder="公告标题"
          style="width: 600px; margin-bottom: 16px;"
          size="default"
        />
        <MarkdownEditor
          ref="addEditorRef"
          v-model="addForm.content"
          height="400px"
          :options="{ hideModeSwitch: true, previewStyle: 'vertical' }"
        />
      </div>
    </el-drawer>

    <!-- ═══ Edit Notice Drawer ═══ -->
    <el-drawer
      v-model="editDrawerVisible"
      title="编辑公告"
      size="60%"
      direction="btt"
      destroy-on-close
      :before-close="closeEditDrawer"
    >
      <template #extra>
        <el-button type="primary" :loading="editSaving" @click="handleEditSubmit">保存</el-button>
      </template>

      <div class="drawer-body" v-loading="editLoading">
        <el-input
          v-model="editForm.title"
          placeholder="公告标题"
          style="width: 600px; margin-bottom: 16px;"
          size="default"
        />
        <MarkdownEditor
          ref="editEditorRef"
          v-model="editForm.content"
          height="500px"
          :options="{ hideModeSwitch: true, previewStyle: 'vertical' }"
        />
      </div>
    </el-drawer>

    <!-- ═══ View Notice Drawer ═══ -->
    <el-drawer
      v-model="viewDrawerVisible"
      :title="viewForm.title"
      size="60%"
      direction="btt"
      destroy-on-close
    >
      <div class="drawer-body" v-loading="viewLoading">
        <el-input
          v-model="viewForm.title"
          disabled
          style="width: 600px; margin-bottom: 16px; margin-left: 200px;"
        />
        <ViewerEditor
          ref="viewEditorRef"
          v-model="viewForm.content"
          height="500px"
        />
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Edit, View, Upload, Delete } from '@element-plus/icons-vue'
import MarkdownEditor from '@/components/MarkdownEditor/index.vue'
import ViewerEditor from '@/components/ViewerEditor/index.vue'
import { get_notice, create_notice, delete_notice, public_notice, get_content } from '@/api/notice'

// ── Constants ──
const pageSize = 20

// ── Table State ──
const noticeList = ref([])
const total = ref(0)
const loading = ref(true)
const currentPage = ref(1)
const searchQuery = ref('')

// ── Add Drawer State ──
const addDrawerVisible = ref(false)
const addSaving = ref(false)
const addEditorRef = ref(null)
const addForm = reactive({ title: '', content: '' })

// ── Edit Drawer State ──
const editDrawerVisible = ref(false)
const editSaving = ref(false)
const editLoading = ref(false)
const editEditorRef = ref(null)
const editForm = reactive({ notice_id: '', title: '', content: '' })

// ── View Drawer State ──
const viewDrawerVisible = ref(false)
const viewLoading = ref(false)
const viewEditorRef = ref(null)
const viewForm = reactive({ title: '', content: '' })

// =====================================================================
//  Data Loading
// =====================================================================
async function fetchData(page) {
  loading.value = true
  try {
    const res = await get_notice(searchQuery.value, page)
    const data = res.data
    noticeList.value = data.results || []
    total.value = data.count || 0
  } catch {
    ElMessage.error('加载公告列表失败')
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
//  Add Notice
// =====================================================================
function openAddDrawer() {
  addForm.title = ''
  addForm.content = ''
  addDrawerVisible.value = true
}

function closeAddDrawer() {
  addDrawerVisible.value = false
}

async function handleAddSubmit() {
  if (!addForm.title.trim()) {
    ElMessage.warning('请输入公告标题')
    return
  }
  if (!addForm.content.trim()) {
    ElMessage.warning('请输入公告内容')
    return
  }
  try {
    await ElMessageBox.confirm('确认提交公告？', '提示')
  } catch {
    return
  }
  addSaving.value = true
  try {
    await create_notice({
      title: addForm.title,
      notice_content: addForm.content,
    })
    ElMessage.success('公告提交成功')
    addDrawerVisible.value = false
    fetchData(1)
  } catch (err) {
    ElMessage.error(err?.response?.data?.msg || '提交失败')
  } finally {
    addSaving.value = false
  }
}

// =====================================================================
//  Edit Notice
// =====================================================================
async function openEditDrawer(row) {
  editLoading.value = true
  editDrawerVisible.value = true
  editForm.notice_id = row.notice_id || row.id
  editForm.title = row.title || ''
  editForm.content = ''
  try {
    const res = await get_content(editForm.notice_id)
    if (res.data.code === 200) {
      const content = res.data.content
      editForm.content = typeof content === 'string' ? content : (content?.notice_content || '')
    }
  } catch {
    ElMessage.error('获取公告内容失败')
  } finally {
    editLoading.value = false
  }
}

function closeEditDrawer() {
  editDrawerVisible.value = false
}

async function handleEditSubmit() {
  if (!editForm.title.trim()) {
    ElMessage.warning('请输入公告标题')
    return
  }
  if (!editForm.content.trim()) {
    ElMessage.warning('请输入公告内容')
    return
  }
  try {
    await ElMessageBox.confirm('确认保存修改？', '提示')
  } catch {
    return
  }
  editSaving.value = true
  try {
    await create_notice({
      title: editForm.title,
      notice_content: editForm.content,
      notice_id: editForm.notice_id,
      update_notice: true,
    })
    ElMessage.success('公告修改成功')
    editDrawerVisible.value = false
    fetchData(currentPage.value)
  } catch (err) {
    ElMessage.error(err?.response?.data?.msg || '修改失败')
  } finally {
    editSaving.value = false
  }
}

// =====================================================================
//  View Notice
// =====================================================================
async function openViewDrawer(row) {
  viewLoading.value = true
  viewDrawerVisible.value = true
  viewForm.title = row.title || ''
  viewForm.content = ''
  try {
    const res = await get_content(row.notice_id || row.id)
    if (res.data.code === 200) {
      viewForm.content = res.data.content || ''
    }
  } catch {
    ElMessage.error('获取公告内容失败')
  } finally {
    viewLoading.value = false
  }
}

// =====================================================================
//  Publish
// =====================================================================
async function handlePublish(row) {
  try {
    await public_notice(row.notice_id || row.id)
    ElMessage.success('公告发布成功')
    fetchData(currentPage.value)
  } catch (err) {
    ElMessage.error(err?.response?.data?.msg || '发布失败')
  }
}

// =====================================================================
//  Delete
// =====================================================================
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除公告 "${row.title}" 吗？`,
      '删除确认',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' }
    )
    await delete_notice(row.notice_id || row.id)
    ElMessage.success('公告已删除')
    fetchData(currentPage.value)
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err?.response?.data?.msg || '删除失败')
    }
  }
}

// =====================================================================
//  Lifecycle
// =====================================================================
onMounted(() => {
  fetchData(1)
})
</script>

<style lang="scss" scoped>
.notice-manage-container {
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
    }
  }

  .pagination-wrap {
    display: flex;
    justify-content: center;
    margin-top: 20px;
    padding: 8px 0;
  }
}

.drawer-body {
  padding: 0 4px;
}
</style>
