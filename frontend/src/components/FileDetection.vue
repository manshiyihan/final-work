<template>
  <div class="detection-container">
    <h3>上传音频文件进行检测</h3>
    
    <el-row :gutter="20">
      <el-col :span="12">
        <el-upload
          class="upload-demo"
          drag
          :auto-upload="false"
          :on-change="handleFileChange"
          :limit="1"
          accept="audio/*"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            拖拽文件到此处或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 wav, mp3, flac 等音频格式
            </div>
          </template>
        </el-upload>
        
        <el-button 
          type="primary" 
          size="large" 
          :loading="loading"
          :disabled="!audioFile"
          @click="handleDetect"
          style="width: 100%; margin-top: 20px;"
        >
          开始检测
        </el-button>
      </el-col>
      
      <el-col :span="12">
        <div v-if="audioUrl" class="audio-preview">
          <h4>音频预览</h4>
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
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { verifyAudio } from '@/api'
import ResultDisplay from './ResultDisplay.vue'

const audioFile = ref(null)
const audioUrl = ref('')
const loading = ref(false)
const result = ref(null)
const mfaResult = ref('')
const rawgatResult = ref('')

const handleFileChange = (file) => {
  // 验证文件格式
  const validAudioTypes = [
    'audio/wav', 'audio/x-wav', 'audio/wave',
    'audio/mpeg', 'audio/mp3',
    'audio/flac', 'audio/x-flac',
    'audio/ogg', 'audio/opus',
    'audio/aac', 'audio/m4a', 'audio/x-m4a',
    'audio/webm'
  ]
  
  const fileType = file.raw.type
  const fileName = file.raw.name.toLowerCase()
  
  // 检查MIME类型或文件扩展名
  const isValidType = validAudioTypes.includes(fileType)
  const hasValidExtension = /\.(wav|mp3|flac|ogg|opus|aac|m4a|webm)$/i.test(fileName)
  
  if (!isValidType && !hasValidExtension) {
    ElMessage.error('不支持的文件格式，请上传音频文件（支持 wav, mp3, flac, ogg, aac, m4a 等格式）')
    return false
  }
  
  audioFile.value = file.raw
  audioUrl.value = URL.createObjectURL(file.raw)
  result.value = null
}

const handleDetect = async () => {
  if (!audioFile.value) {
    ElMessage.warning('请先上传音频文件')
    return
  }

  loading.value = true
  const formData = new FormData()
  formData.append('audio', audioFile.value)
  formData.append('input_type', 'upload')

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
