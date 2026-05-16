<template>
  <div class="result-container">
    <el-card class="result-card" :class="statusClass">
      <template #header>
        <div class="card-header">
          <span class="status-icon">{{ statusIcon }}</span>
          <span class="status-text">{{ statusText }}</span>
        </div>
      </template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="说话人">
          <el-tag :type="speakerTagType" size="large">
            {{ result.speaker_result || '未知' }}
          </el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="反欺诈">
          <el-tag :type="spoofTagType" size="large">
            {{ spoofText }}
          </el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="风险分数">
          <el-progress 
            :percentage="riskPercentage" 
            :color="riskColor"
            :stroke-width="20"
          />
        </el-descriptions-item>
        
        <el-descriptions-item label="耗时">
          <span class="latency">{{ result.latency_ms }} ms</span>
        </el-descriptions-item>
      </el-descriptions>
      
      <div class="timestamp">
        检测时间: {{ currentTime }}
      </div>
    </el-card>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="detail-header">说话人验证详情</div>
          </template>
          <pre class="detail-text">{{ mfaResult }}</pre>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="detail-header">反欺骗检测详情</div>
          </template>
          <pre class="detail-text">{{ rawgatResult }}</pre>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  result: {
    type: Object,
    required: true
  },
  mfaResult: {
    type: String,
    default: ''
  },
  rawgatResult: {
    type: String,
    default: ''
  }
})

const currentTime = computed(() => {
  return new Date().toLocaleString('zh-CN')
})

const statusText = computed(() => {
  const label = props.result.final_label
  if (label === 'pass') return '通过'
  if (label === 'fraud_risk') return '疑似欺诈'
  if (label === 'identity_unknown') return '身份未知'
  return '待确认'
})

const statusIcon = computed(() => {
  const label = props.result.final_label
  if (label === 'pass') return '✅'
  if (label === 'fraud_risk') return '🚨'
  if (label === 'identity_unknown') return '⚠️'
  return '❓'
})

const statusClass = computed(() => {
  const label = props.result.final_label
  if (label === 'pass') return 'status-pass'
  if (label === 'fraud_risk') return 'status-fraud'
  if (label === 'identity_unknown') return 'status-unknown'
  return 'status-default'
})

const spoofText = computed(() => {
  return props.result.spoof_result === 'spoof' ? '伪造语音' : '真实语音'
})

const spoofTagType = computed(() => {
  return props.result.spoof_result === 'spoof' ? 'danger' : 'success'
})

const speakerTagType = computed(() => {
  const speaker = props.result.speaker_result || '未知'
  return speaker === '未知' ? 'info' : 'success'
})

const riskPercentage = computed(() => {
  return Math.round((props.result.risk_score || 0) * 100)
})

const riskColor = computed(() => {
  const score = props.result.risk_score || 0
  if (score < 0.3) return '#67c23a'
  if (score < 0.7) return '#e6a23c'
  return '#f56c6c'
})
</script>

<style scoped>
.result-container {
  margin-top: 30px;
}

.result-card {
  border-radius: 10px;
  overflow: hidden;
}

.status-pass {
  border: 2px solid #67c23a;
}

.status-fraud {
  border: 2px solid #f56c6c;
}

.status-unknown {
  border: 2px solid #e6a23c;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: bold;
}

.status-icon {
  font-size: 24px;
}

.latency {
  font-weight: bold;
  color: #409eff;
}

.timestamp {
  margin-top: 15px;
  text-align: right;
  color: #909399;
  font-size: 14px;
}

.detail-header {
  font-weight: bold;
  color: #606266;
}

.detail-text {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #606266;
  margin: 0;
  max-height: 200px;
  overflow-y: auto;
}
</style>
