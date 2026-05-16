<template>
  <div class="detection-container">
    <h3>录制音频进行实时检测</h3>
    
    <el-row :gutter="20">
      <el-col :span="12">
        <div class="record-controls">
          <el-button 
            v-if="!isRecording && !audioBlob"
            type="danger" 
            size="large"
            :icon="Microphone"
            @click="startRecording"
          >
            开始录音
          </el-button>
          
          <el-button 
            v-if="isRecording"
            type="warning" 
            size="large"
            :icon="VideoPause"
            @click="stopRecording"
          >
            停止录音
          </el-button>
          
          <el-button 
            v-if="audioBlob && !isRecording"
            type="info" 
            size="large"
            @click="resetRecording"
          >
            重新录音
          </el-button>
          
          <div v-if="isRecording" class="recording-indicator">
            <span class="pulse"></span>
            录音中...
          </div>
        </div>
        
        <el-button 
          type="primary" 
          size="large" 
          :loading="loading"
          :disabled="!audioBlob"
          @click="handleDetect"
          style="width: 100%; margin-top: 20px;"
        >
          开始检测
        </el-button>
      </el-col>
      
      <el-col :span="12">
        <div v-if="audioUrl" class="audio-preview">
          <h4>录音预览</h4>
          <audio :src="audioUrl" controls style="width: 100%;"></audio>
        </div>
      </el-col>
    </el-row>

    <ResultDisplay 
      v-if="result"
      :result="result"
      :mfa-result="mfaResult"
      :rawgat-result="rawgatResult"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Microphone, VideoPause } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { verifyAudio } from '@/api'
import ResultDisplay from './ResultDisplay.vue'

const isRecording = ref(false)
const audioBlob = ref(null)
const audioUrl = ref('')
const loading = ref(false)
const result = ref(null)
const mfaResult = ref('')
const rawgatResult = ref('')
let mediaRecorder = null
let audioChunks = []

const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(stream)
    audioChunks = []

    mediaRecorder.ondataavailable = (event) => {
      audioChunks.push(event.data)
    }

    mediaRecorder.onstop = () => {
      const blob = new Blob(audioChunks, { type: 'audio/wav' })
      audioBlob.value = blob
      audioUrl.value = URL.createObjectURL(blob)
      stream.getTracks().forEach(track => track.stop())
    }

    mediaRecorder.start()
    isRecording.value = true
    ElMessage.success('开始录音')
  } catch (error) {
    ElMessage.error('无法访问麦克风: ' + error.message)
  }
}

const stopRecording = () => {
  if (mediaRecorder && isRecording.value) {
    mediaRecorder.stop()
    isRecording.value = false
    ElMessage.info('录音已停止')
  }
}

const resetRecording = () => {
  audioBlob.value = null
  audioUrl.value = ''
  result.value = null
}

const handleDetect = async () => {
  if (!audioBlob.value) {
    ElMessage.warning('请先录制音频')
    return
  }

  loading.value = true
  const formData = new FormData()
  formData.append('audio', audioBlob.value, 'recording.wav')
  formData.append('input_type', 'record')

  try {
    const response = await verifyAudio(formData)
    if (response.data.ok) {
      result.value = response.data
      mfaResult.value = response.data.mfa_result
      rawgatResult.value = response.data.rawgat_result
      ElMessage.success('检测完成')
    } else {
      ElMessage.error(response.data.error || '检测失败')
    }
  } catch (error) {
    ElMessage.error('检测失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.detection-container {
  padding: 20px;
}

h3 {
  color: #667eea;
  margin-bottom: 20px;
}

.record-controls {
  text-align: center;
  padding: 40px 20px;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 20px;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #f56c6c;
  font-weight: bold;
  font-size: 16px;
}

.pulse {
  width: 12px;
  height: 12px;
  background: #f56c6c;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.2);
  }
}

.audio-preview {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
}

.audio-preview h4 {
  margin-bottom: 15px;
  color: #606266;
}
</style>
