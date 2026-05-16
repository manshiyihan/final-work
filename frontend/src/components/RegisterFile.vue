<template>
  <div class="register-container">
    <h3>上传音频文件注册新的说话人</h3>
    
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
          :disabled="!audioFile || !speakerName"
          @click="handleRegister"
          style="width: 100%; margin-top: 20px;"
        >
          ✅ 注册说话人
        </el-button>
      </el-col>
      
      <el-col :span="12">
        <div v-if="audioUrl" class="audio-preview">
          <h4>音频预览</h4>
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
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { registerSpeaker } from '@/api'

const audioFile = ref(null)
const audioUrl = ref('')
const speakerName = ref('')
const loading = ref(false)
const registerResult = ref('')

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
  registerResult.value = ''
}

const handleRegister = async () => {
  if (!audioFile.value) {
    ElMessage.warning('请先上传音频文件')
    return
  }
  
  if (!speakerName.value.trim()) {
    ElMessage.warning('请输入说话人名称')
    return
  }

  loading.value = true
  const formData = new FormData()
  formData.append('audio', audioFile.value)
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
