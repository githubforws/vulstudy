<template>
  <div class="network-container app-container">
    <el-card shadow="never" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span class="card-title">网卡管理</span>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="按网卡名称搜索"
              style="width: 230px"
              clearable
              size="default"
              @keyup.enter="handleSearch"
            >
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button type="primary" @click="handleSearch">查询</el-button>
            <el-button type="success" @click="openAddDialog">添加</el-button>
          </div>
        </div>
      </template>

      <!-- Network Table -->
      <el-table :data="networkList" stripe border style="width: 100%">
        <el-table-column type="index" label="序号" width="55" align="center" />
        <el-table-column prop="net_work_name" label="网卡名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="net_work_subnet" label="子网" min-width="180" show-overflow-tooltip />
        <el-table-column prop="net_work_gateway" label="网关" min-width="180" show-overflow-tooltip />
        <el-table-column label="范围" width="100" align="center">
          <template #default="scope">
            <el-tag size="small">{{ scope.row.net_work_scope }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="驱动" width="100" align="center">
          <template #default="scope">
            <el-tag size="small">{{ scope.row.net_work_driver }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="IPv6" width="90" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.enable_ipv6 ? 'success' : 'info'" size="small">
              {{ scope.row.enable_ipv6 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="scope">
            <el-button type="danger" size="small" :icon="Delete" @click="handleDelete(scope.row)">删除</el-button>
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

    <!-- Add Network Dialog -->
    <el-dialog
      v-model="addDialogVisible"
      title="添加网卡"
      width="500px"
      destroy-on-close
      :close-on-click-modal="false"
      @close="resetAddForm"
    >
      <el-form ref="addFormRef" :model="addForm" :rules="addRules" label-width="100px" size="default">
        <el-form-item label="网卡名称" prop="net_work_name">
          <el-input v-model="addForm.net_work_name" placeholder="输入网卡名称" />
        </el-form-item>
        <el-form-item label="子网" prop="net_work_subnet">
          <el-input v-model="addForm.net_work_subnet" placeholder="如 172.18.0.0/16" />
        </el-form-item>
        <el-form-item label="网关" prop="net_work_gateway">
          <el-input v-model="addForm.net_work_gateway" placeholder="如 172.18.0.1" />
        </el-form-item>
        <el-form-item label="范围">
          <el-select v-model="addForm.net_work_scope" style="width: 100%">
            <el-option label="local" value="local" />
          </el-select>
        </el-form-item>
        <el-form-item label="驱动">
          <el-select v-model="addForm.net_work_driver" style="width: 100%">
            <el-option label="bridge" value="bridge" />
          </el-select>
        </el-form-item>
        <el-form-item label="IPv6">
          <el-switch v-model="addForm.enable_ipv6" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitAdd">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Delete } from '@element-plus/icons-vue'
import { NetWorkList, NetWorkAdd, NetworkDelete } from '@/api/network'

// ── Constants ──
const pageSize = 20

// ── Table State ──
const networkList = ref([])
const total = ref(0)
const loading = ref(true)
const currentPage = ref(1)
const searchQuery = ref('')

// ── Add Dialog State ──
const addDialogVisible = ref(false)
const submitting = ref(false)
const addFormRef = ref(null)

const defaultForm = {
  net_work_name: '',
  net_work_subnet: '',
  net_work_gateway: '',
  net_work_scope: 'local',
  net_work_driver: 'bridge',
  enable_ipv6: false,
}

const addForm = reactive({ ...defaultForm })

const addRules = {
  net_work_name: [{ required: true, message: '请输入网卡名称', trigger: 'blur' }],
  net_work_subnet: [
    { required: true, message: '请输入子网', trigger: 'blur' },
    { pattern: /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}$/, message: '子网格式不正确，如 172.18.0.0/16', trigger: 'blur' },
  ],
  net_work_gateway: [
    { required: true, message: '请输入网关', trigger: 'blur' },
    { pattern: /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/, message: '网关格式不正确，如 172.18.0.1', trigger: 'blur' },
  ],
}

// =====================================================================
//  Data Loading
// =====================================================================
async function loadData(page) {
  loading.value = true
  try {
    const res = await NetWorkList(searchQuery.value, page)
    networkList.value = res.data.results || []
    total.value = res.data.count || 0
  } catch {
    ElMessage.error('加载网卡列表失败')
  } finally {
    loading.value = false
  }
}

// =====================================================================
//  Search & Pagination
// =====================================================================
function handleSearch() {
  currentPage.value = 1
  loadData(1)
}

function handlePageChange(page) {
  currentPage.value = page
  loadData(page)
}

// =====================================================================
//  Add Network
// =====================================================================
function openAddDialog() {
  resetAddForm()
  addDialogVisible.value = true
}

function resetAddForm() {
  Object.assign(addForm, { ...defaultForm })
  addFormRef.value?.clearValidate()
}

async function submitAdd() {
  const valid = await addFormRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    await NetWorkAdd({
      net_work_name: addForm.net_work_name,
      net_work_subnet: addForm.net_work_subnet,
      net_work_gateway: addForm.net_work_gateway,
      net_work_scope: addForm.net_work_scope,
      net_work_driver: addForm.net_work_driver,
      enable_ipv6: addForm.enable_ipv6,
    })
    ElMessage.success('网卡创建成功')
    addDialogVisible.value = false
    currentPage.value = 1
    loadData(1)
  } catch (err) {
    const msg = err?.response?.data?.msg || err?.response?.data?.message || '创建网卡失败'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}

// =====================================================================
//  Delete Network
// =====================================================================
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除网卡 "${row.net_work_name}"（${row.net_work_subnet}）吗？`,
      '删除确认',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' }
    )
    await NetworkDelete(row.net_work_id)
    ElMessage.success('网卡已删除')
    loadData(currentPage.value)
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err?.response?.data?.msg || '删除网卡失败')
    }
  }
}

// =====================================================================
//  Lifecycle
// =====================================================================
onMounted(() => {
  loadData(1)
})
</script>

<style lang="scss" scoped>
.network-container {
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
</style>
