<template>
  <div class="history-container">
    <h3>查询检测历史记录（来自后端数据库）</h3>
    
    <el-row :gutter="20" class="filter-row">
      <el-col :span="6">
        <el-input-number 
          v-model="page" 
          :min="1" 
          label="页码"
          controls-position="right"
          style="width: 100%;"
        />
      </el-col>
      
      <el-col :span="6">
        <el-select v-model="finalLabel" placeholder="最终标签过滤" style="width: 100%;">
          <el-option label="全部" value="all" />
          <el-option label="通过" value="pass" />
          <el-option label="疑似欺诈" value="fraud_risk" />
          <el-option label="身份未知" value="identity_unknown" />
        </el-select>
      </el-col>
      
      <el-col :span="6">
        <el-select v-model="inputType" placeholder="输入类型过滤" style="width: 100%;">
          <el-option label="全部" value="all" />
          <el-option label="上传" value="upload" />
          <el-option label="录音" value="record" />
        </el-select>
      </el-col>
      
      <el-col :span="6">
        <el-button type="primary" :loading="loading" @click="fetchRecords" style="width: 100%;">
          刷新记录
        </el-button>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 10px;">
      <el-col :span="12">
        <el-button type="success" :loading="exportLoading" @click="exportCurrent" style="width: 100%;">
          导出当前筛选CSV
        </el-button>
      </el-col>
      <el-col :span="12">
        <el-button type="warning" :loading="exportAllLoading" @click="exportAll" style="width: 100%;">
          导出全部筛选CSV
        </el-button>
      </el-col>
    </el-row>

    <el-alert
      v-if="summary"
      :title="summary"
      type="info"
      :closable="false"
      style="margin-top: 20px;"
    />

    <el-table
      :data="tableData"
      stripe
      border
      style="width: 100%; margin-top: 20px;"
      :max-height="500"
    >
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="created_at" label="时间" width="180" />
      <el-table-column prop="input_type" label="输入类型" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.input_type === 'upload' ? 'primary' : 'success'" size="small">
            {{ scope.row.input_type === 'upload' ? '上传' : '录音' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="final_label" label="最终标签" width="120">
        <template #default="scope">
          <el-tag :type="getLabelType(scope.row.final_label)" size="small">
            {{ getLabelText(scope.row.final_label) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="risk_score" label="风险分数" width="100">
        <template #default="scope">
          <span :style="{ color: getRiskColor(scope.row.risk_score) }">
            {{ (scope.row.risk_score * 100).toFixed(0) }}%
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="latency_ms" label="耗时(ms)" width="100" />
      <el-table-column prop="speaker_result" label="说话人" width="120" />
      <el-table-column prop="spoof_result" label="反欺诈结果" width="120">
        <template #default="scope">
          <el-tag :type="scope.row.spoof_result === 'spoof' ? 'danger' : 'success'" size="small">
            {{ scope.row.spoof_result === 'spoof' ? '伪造' : '真实' }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="pagination.total > 0"
      v-model:current-page="page"
      :page-size="pagination.limit"
      :total="pagination.total"
      layout="total, prev, pager, next, jumper"
      style="margin-top: 20px; justify-content: center;"
      @current-change="fetchRecords"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getRecords } from '@/api'

const page = ref(1)
const finalLabel = ref('all')
const inputType = ref('all')
const loading = ref(false)
const exportLoading = ref(false)
const exportAllLoading = ref(false)
const summary = ref('')
const tableData = ref([])
const pagination = ref({
  page: 1,
  limit: 20,
  total: 0
})

const fetchRecords = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      limit: 20,
      final_label: finalLabel.value === 'all' ? '' : finalLabel.value,
      input_type: inputType.value === 'all' ? '' : inputType.value
    }
    
    const response = await getRecords(params)
    if (response.data.ok) {
      tableData.value = response.data.items
      pagination.value = response.data.pagination
      summary.value = `✅ 共 ${pagination.value.total} 条记录，当前第 ${pagination.value.page} 页，每页 ${pagination.value.limit} 条`
    } else {
      ElMessage.error('获取历史记录失败')
    }
  } catch (error) {
    ElMessage.error('获取历史记录失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const exportCurrent = async () => {
  exportLoading.value = true
  try {
    await fetchRecords()
    if (tableData.value.length === 0) {
      ElMessage.warning('没有可导出的记录')
      return
    }
    
    const csv = convertToCSV(tableData.value)
    downloadCSV(csv, `records_page${page.value}.csv`)
    ElMessage.success(`✅ 导出成功，共 ${tableData.value.length} 条`)
  } catch (error) {
    ElMessage.error('导出失败: ' + (error.message || '未知错误'))
  } finally {
    exportLoading.value = false
  }
}

const exportAll = async () => {
  exportAllLoading.value = true
  try {
    const allRecords = []
    let currentPage = 1
    let hasMore = true
    
    while (hasMore) {
      const params = {
        page: currentPage,
        limit: 200,
        final_label: finalLabel.value === 'all' ? '' : finalLabel.value,
        input_type: inputType.value === 'all' ? '' : inputType.value
      }
      
      const response = await getRecords(params)
      if (response.data.ok) {
        allRecords.push(...response.data.items)
        const total = response.data.pagination.total
        hasMore = allRecords.length < total
        currentPage++
      } else {
        hasMore = false
      }
    }
    
    if (allRecords.length === 0) {
      ElMessage.warning('没有可导出的记录')
      return
    }
    
    const csv = convertToCSV(allRecords)
    downloadCSV(csv, `records_all_${Date.now()}.csv`)
    ElMessage.success(`✅ 全量导出成功，共 ${allRecords.length} 条`)
  } catch (error) {
    ElMessage.error('导出失败: ' + (error.message || '未知错误'))
  } finally {
    exportAllLoading.value = false
  }
}

const convertToCSV = (data) => {
  const headers = ['ID', '时间', '输入类型', '最终标签', '风险分数', '耗时(ms)', '说话人', '反欺诈结果']
  const rows = data.map(item => [
    item.id,
    item.created_at,
    item.input_type,
    item.final_label,
    item.risk_score,
    item.latency_ms,
    item.speaker_result,
    item.spoof_result
  ])
  
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n')
  
  return '\uFEFF' + csvContent
}

const downloadCSV = (csv, filename) => {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
}

const getLabelText = (label) => {
  const map = {
    pass: '通过',
    fraud_risk: '疑似欺诈',
    identity_unknown: '身份未知'
  }
  return map[label] || '未知'
}

const getLabelType = (label) => {
  const map = {
    pass: 'success',
    fraud_risk: 'danger',
    identity_unknown: 'warning'
  }
  return map[label] || 'info'
}

const getRiskColor = (score) => {
  if (score < 0.3) return '#67c23a'
  if (score < 0.7) return '#e6a23c'
  return '#f56c6c'
}

onMounted(() => {
  fetchRecords()
})
</script>

<style scoped>
.history-container {
  padding: 20px;
}

h3 {
  color: #667eea;
  margin-bottom: 20px;
}

.filter-row {
  margin-bottom: 10px;
}
</style>
