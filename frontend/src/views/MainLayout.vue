<template>
  <div class="main-layout">
    <div class="header">
      <div class="header-content">
        <div class="header-left">
          <h1>抗欺诈说话人识别系统</h1>
          <p>说话人验证 + 反欺骗检测</p>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><UserFilled /></el-icon>
              <span>{{ username }}</span>
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  <div class="user-detail">
                    <div>用户名: {{ username }}</div>
                    <div v-if="userEmail">邮箱: {{ userEmail }}</div>
                  </div>
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>

    <div class="content-wrapper">
      <el-tabs v-model="activeTab" class="tabs-container">
        <el-tab-pane label="本地文件检测" name="file">
          <FileDetection />
        </el-tab-pane>
        
        <el-tab-pane label="录音检测" name="record">
          <RecordDetection />
        </el-tab-pane>
        
        <el-tab-pane label="注册说话人（录音）" name="register-record">
          <RegisterRecord />
        </el-tab-pane>
        
        <el-tab-pane label="注册说话人（文件）" name="register-file">
          <RegisterFile />
        </el-tab-pane>
        
        <el-tab-pane label="历史记录" name="history">
          <HistoryRecords />
        </el-tab-pane>
      </el-tabs>

      <div class="usage-guide">
        <el-divider />
        <h3>使用说明</h3>
        <ol>
          <li><strong>本地文件检测</strong>: 上传本地音频文件（支持 wav, mp3, flac 等格式）</li>
          <li><strong>录音检测</strong>: 点击录音按钮，录制音频后进行检测</li>
          <li><strong>注册说话人（录音）</strong>: 录制音频并输入说话人名称，将说话人注册到系统中</li>
          <li><strong>注册说话人（文件）</strong>: 上传音频文件并输入说话人名称，将说话人注册到系统中</li>
          <li>系统将同时进行说话人验证和反欺骗检测</li>
          <li>检测结果会实时显示在下方</li>
        </ol>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { UserFilled, ArrowDown, SwitchButton } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { logout } from '@/api/auth'
import FileDetection from '@/components/FileDetection.vue'
import RecordDetection from '@/components/RecordDetection.vue'
import RegisterRecord from '@/components/RegisterRecord.vue'
import RegisterFile from '@/components/RegisterFile.vue'
import HistoryRecords from '@/components/HistoryRecords.vue'

const router = useRouter()
const activeTab = ref('file')

// 获取用户信息
const user = computed(() => {
  const userStr = localStorage.getItem('user')
  return userStr ? JSON.parse(userStr) : null
})

const username = computed(() => user.value?.username || '用户')
const userEmail = computed(() => user.value?.email || '')

// 处理下拉菜单命令
const handleCommand = async (command) => {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      
      // 调用登出API
      await logout()
      
      // 清除本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      
      ElMessage.success('已退出登录')
      
      // 跳转到登录页
      router.push('/login')
    } catch (error) {
      if (error !== 'cancel') {
        console.error('登出失败:', error)
      }
    }
  }
}

onMounted(() => {
  // 检查是否已登录
  if (!user.value) {
    router.push('/login')
  }
})
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
  padding: 20px;
}

.header {
  text-align: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px 30px;
  border-radius: 10px;
  color: white;
  margin-bottom: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
}

.header-left h1 {
  font-size: 2em;
  margin: 0 0 5px 0;
  text-align: left;
}

.header-left p {
  font-size: 1em;
  opacity: 0.9;
  margin: 0;
  text-align: left;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  transition: background 0.3s;
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.3);
}

.user-detail {
  padding: 5px 0;
  font-size: 14px;
  color: #606266;
}

.user-detail div {
  margin: 5px 0;
}

.content-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  background: white;
  border-radius: 10px;
  padding: 30px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.tabs-container {
  margin-bottom: 20px;
}

.usage-guide {
  margin-top: 30px;
}

.usage-guide h3 {
  color: #667eea;
  margin-bottom: 15px;
}

.usage-guide ol {
  padding-left: 20px;
}

.usage-guide li {
  margin-bottom: 10px;
  line-height: 1.6;
}
</style>
