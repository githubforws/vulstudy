<template>
  <div class="user-manage-container app-container">
    <el-card shadow="never" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span class="card-title">用户管理</span>
          <div class="search-area">
            <el-input
              v-model="searchQuery"
              placeholder="按用户名搜索"
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

      <!-- User Table -->
      <el-table
        :data="userListData"
        stripe
        border
        style="width: 100%"
        :default-sort="{ prop: 'rank', order: 'descending' }"
      >
        <el-table-column type="index" label="序号" width="55" align="center" />
        <el-table-column prop="name" label="用户名" min-width="120" show-overflow-tooltip />
        <el-table-column prop="email" label="邮箱" min-width="200" show-overflow-tooltip />
        <el-table-column label="权限" width="100" align="center">
          <template #default="scope">
            <el-tag v-if="Array.isArray(scope.row.roles) && scope.row.roles.includes('admin')" type="danger" size="small">管理员</el-tag>
            <el-tag v-else type="info" size="small">普通用户</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="rank" label="积分" width="80" align="center" sortable />
        <el-table-column prop="rank_count" label="通过数量" width="100" align="center" sortable />
        <el-table-column prop="date_joined" label="注册时间" min-width="170" />
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="scope">
            <el-button type="warning" size="small" @click="handleChangePwd(scope.row)">修改密码</el-button>
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
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { userList, userChangePwd } from '@/api/user'

// ── Constants ──
const pageSize = 20

// ── State ──
const userListData = ref([])
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
    const res = await userList(page, searchQuery.value)
    const data = res.data
    userListData.value = data.results || []
    total.value = data.count || 0
  } catch {
    ElMessage.error('加载用户列表失败')
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
//  Change Password
// =====================================================================
async function handleChangePwd(row) {
  try {
    const { value: newPassword } = await ElMessageBox.prompt(
      `请输入用户 "${row.name}" 的新密码：`,
      '修改密码',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /^.{6,}$/,
        inputErrorMessage: '密码长度不得小于6位',
        inputPlaceholder: '密码长度不得小于6位',
        inputType: 'password',
      }
    )
    if (!newPassword || !newPassword.trim()) {
      ElMessage.error('密码不能为空')
      return
    }
    await userChangePwd({ pwd: newPassword.trim() }, row.id)
    ElMessage.success(`用户 "${row.name}" 密码修改成功`)
  } catch (err) {
    if (err === 'cancel') return
    ElMessage.error(err?.response?.data?.msg || '密码修改失败')
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
.user-manage-container {
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
