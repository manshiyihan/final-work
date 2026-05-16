<template>
  <div class="register-container">
    <h3>录制音频注册新的说话人</h3>
    
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
        
        <el-input
          v-model="speakerName"
          placeholder="请输入说话人名称（例如：张三、John等）"
          size="large"
          style="margin-top: 20px;"
        >
          <template #prepend>说话人名称</template>
        </el-input>
        
        <el-button 
          type="primary" 
          size="large" 
          :loading="loading"
          :disabled="!audioBlob || !speakerName"
          @click="handleRegister"
          style="width: 100%; margin-top: 20px;"
        >
          ✅ 注册说话人
        </el-button>
      </el-col>
      
      <el-col :span="12">
        <div v-if="audioUrl" class="audio-preview">
          <h4>录音预览</h4>
          <audio :src="audioUrl" controls style="width: 100%;"></audio>
        </div>
      </el-col>
    </el-row>

    <el-card v-if="registerResult" class="result-card" style="margin-top: 20px;">
      <div v-html="registerResult"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Microphone, VideoPause } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { registerSpeaker } from '@/api'

const isRecording = ref(false)
const audioBlob = ref(null)
const audioUrl = ref('')
const speakerName = ref('')
const loading = ref(false)
const registerResult = ref('')
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
  registerResult.value = ''
}

const handleRegister = async () => {
  if (!audioBlob.value) {
    ElMessage.warning('请先录制音频')
    return
  }
  
  if (!speakerName.value.trim()) {
    ElMessage.warning('请输入说话人名称')
    return
  }

  loading.value = true
  const formData = new FormData()
  formData.append('audio', audioBlob.value, 'recording.wav')
  formData.append('speaker_name', speakerName.value.trim())

  try {
    const response = await registerSpeaker(formData)
    if (response.data.ok) {
      const currentTime = new Date().toLocaleString('zh-CN')
      registerResult.value = `
        <h3>✅ 注册成功！</h3>
        <p><strong>说话人名称</strong>: ${response.data.speaker_name}</p>
        <p><strong>注册时间</strong>: ${currentTime}</p>
        <p>说话人已成功添加到系统中，现在可以使用该说话人的音频进行验证了。</p>
      `
      ElMessage.success('注册成功')
      speakerName.value = ''
    } else {
      const errorMsg = response.data.error || '注册失败'
      registerResult.value = `<p style="color: #f56c6c;">❌ ${errorMsg}</p>`
      
      // 根据错误类型显示不同的提示
      if (errorMsg.includes('已存在')) {
        ElMessage.error(errorMsg)
      } else {
        ElMessage.error('注册失败: ' + errorMsg)
      }
    }
  } catch (error) {
    const errorMsg = error.response?.data?.error || error.message || '未知错误'
    registerResult.value = `<p style="color: #f56c6c;">❌ 注册失败: ${errorMsg}</p>`
    
    if (errorMsg.includes('已存在')) {
      ElMessage.error(errorMsg)
    } else {
      ElMessage.error('注册失败: ' + errorMsg)
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
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

.result-card {
  border: 2px solid #67c23a;
  border-radius: 10px;
}
</style>
