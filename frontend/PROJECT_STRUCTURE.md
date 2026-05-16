# Vue前端项目结构

## 完整目录树

```
frontend/
├── src/                          # 源代码目录
│   ├── api/                      # API接口封装
│   │   └── index.js              # Axios配置和API函数
│   │
│   ├── components/               # Vue组件
│   │   ├── FileDetection.vue     # 文件上传检测组件
│   │   ├── RecordDetection.vue   # 录音检测组件
│   │   ├── RegisterRecord.vue    # 录音注册组件
│   │   ├── RegisterFile.vue      # 文件注册组件
│   │   ├── HistoryRecords.vue    # 历史记录组件
│   │   └── ResultDisplay.vue     # 结果展示组件
│   │
│   ├── router/                   # 路由配置
│   │   └── index.js              # Vue Router配置
│   │
│   ├── views/                    # 页面视图
│   │   └── MainLayout.vue        # 主布局页面
│   │
│   ├── utils/                    # 工具函数
│   │   └── audioConverter.js    # 音频格式转换工具
│   │
│   ├── App.vue                   # 根组件
│   └── main.js                   # 应用入口文件
│
├── public/                       # 静态资源目录（可选）
│
├── index.html                    # HTML模板
├── vite.config.js                # Vite配置文件
├── package.json                  # 项目配置和依赖
├── package-lock.json             # 依赖锁定文件
├── .gitignore                    # Git忽略规则
├── run.sh                        # 启动脚本
│
└── docs/                         # 文档目录
    ├── README.md                 # 详细使用文档
    ├── QUICKSTART.md             # 快速入门指南
    ├── FEATURES.md               # 功能详解
    ├── MIGRATION_GUIDE.md        # 迁移指南
    ├── CHECKLIST.md              # 开发检查清单
    └── PROJECT_STRUCTURE.md      # 本文件
```

---

## 目录说明

### `/src` - 源代码目录

所有应用源代码都在这个目录下。

#### `/src/api` - API接口层

**文件**: `index.js`

**职责**:
- Axios实例配置
- API基础URL设置
- 请求/响应拦截器
- API函数封装

**主要函数**:
```javascript
verifyAudio(formData)      // 音频检测
registerSpeaker(formData)  // 注册说话人
getRecords(params)         // 查询历史记录
healthCheck()              // 健康检查
```

#### `/src/components` - 组件目录

**FileDetection.vue** - 文件上传检测
- 拖拽上传功能
- 文件选择功能
- 音频预览
- 检测按钮
- 结果展示

**RecordDetection.vue** - 录音检测
- 浏览器录音
- 录音状态显示
- 录音预览
- 检测按钮
- 结果展示

**RegisterRecord.vue** - 录音注册
- 录音功能
- 说话人名称输入
- 名称格式验证
- 注册按钮
- 注册结果反馈

**RegisterFile.vue** - 文件注册
- 文件上传
- 说话人名称输入
- 名称格式验证
- 注册按钮
- 注册结果反馈

**HistoryRecords.vue** - 历史记录
- 分页查询
- 条件筛选（标签、类型）
- 数据表格展示
- CSV导出（当前页）
- CSV导出（全部）

**ResultDisplay.vue** - 结果展示
- 检测状态展示
- 说话人识别结果
- 反欺骗检测结果
- 风险分数可视化
- 详细信息展示

#### `/src/router` - 路由配置

**文件**: `index.js`

**职责**:
- 路由定义
- 路由守卫
- 路由配置

**当前路由**:
```javascript
{
  path: '/',
  component: MainLayout
}
```

#### `/src/views` - 页面视图

**MainLayout.vue** - 主布局页面
- 页面头部
- 标签页导航
- 组件容器
- 使用说明

#### `/src/utils` - 工具函数

**audioConverter.js** - 音频转换工具
- 音频重采样（16kHz）
- 单声道转换
- WAV格式输出
- AudioBuffer处理

#### 根组件和入口

**App.vue** - 根组件
- 全局样式
- 路由视图容器

**main.js** - 应用入口
- Vue应用创建
- 插件注册（Router, Element Plus）
- 图标注册
- 应用挂载

---

### 配置文件

#### `index.html`
- HTML模板
- 应用挂载点
- Meta标签

#### `vite.config.js`
```javascript
{
  plugins: [vue()],
  resolve: {
    alias: { '@': 'src' }
  },
  server: {
    port: 7860,
    proxy: {
      '/api': 'http://127.0.0.1:8000'
    }
  }
}
```

#### `package.json`
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.5",
    "axios": "^1.6.0",
    "element-plus": "^2.5.0",
    "@element-plus/icons-vue": "^2.3.1"
  }
}
```

---

## 组件依赖关系

```
App.vue
  └── MainLayout.vue
      ├── FileDetection.vue
      │   └── ResultDisplay.vue
      ├── RecordDetection.vue
      │   └── ResultDisplay.vue
      ├── RegisterRecord.vue
      ├── RegisterFile.vue
      └── HistoryRecords.vue
```

---

## 数据流

```
用户操作
  ↓
Vue组件
  ↓
API函数 (src/api/index.js)
  ↓
Axios请求
  ↓
后端API (FastAPI)
  ↓
响应数据
  ↓
Vue组件更新
  ↓
UI渲染
```

---

## 文件大小参考

| 文件 | 行数 | 大小 |
|-----|------|------|
| FileDetection.vue | ~150 | ~4KB |
| RecordDetection.vue | ~180 | ~5KB |
| RegisterRecord.vue | ~180 | ~5KB |
| RegisterFile.vue | ~150 | ~4KB |
| HistoryRecords.vue | ~250 | ~7KB |
| ResultDisplay.vue | ~180 | ~5KB |
| MainLayout.vue | ~100 | ~3KB |
| api/index.js | ~30 | ~1KB |
| router/index.js | ~20 | ~0.5KB |
| main.js | ~15 | ~0.5KB |
| App.vue | ~30 | ~1KB |

**总计**: ~1,285行代码，~36KB

---

## 构建产物

运行 `npm run build` 后生成：

```
dist/
├── assets/
│   ├── index-[hash].js      # 主应用JS
│   ├── index-[hash].css     # 主应用CSS
│   └── vendor-[hash].js     # 第三方库
├── index.html               # 入口HTML
└── favicon.ico              # 图标（可选）
```

**构建大小参考**:
- JS: ~500KB (gzip后 ~150KB)
- CSS: ~200KB (gzip后 ~30KB)
- 总计: ~700KB (gzip后 ~180KB)

---

## 开发工作流

### 1. 开发新功能

```bash
# 1. 创建新组件
touch src/components/NewFeature.vue

# 2. 编写组件代码
# 3. 在MainLayout.vue中引入
# 4. 添加到标签页
# 5. 测试功能
```

### 2. 添加新API

```bash
# 1. 在src/api/index.js添加函数
export const newApi = (data) => {
  return api.post('/new-endpoint', data)
}

# 2. 在组件中使用
import { newApi } from '@/api'
```

### 3. 修改样式

```bash
# 1. 在组件的<style scoped>中修改
# 2. 或在App.vue中修改全局样式
# 3. 热更新自动生效
```

---

## 代码规范

### 命名规范

- **组件**: PascalCase (FileDetection.vue)
- **文件夹**: kebab-case (api/, components/)
- **变量**: camelCase (audioFile, isLoading)
- **常量**: UPPER_SNAKE_CASE (API_BASE_URL)

### 组件结构

```vue
<template>
  <!-- HTML模板 -->
</template>

<script setup>
// 导入
import { ref } from 'vue'

// 响应式数据
const data = ref(null)

// 方法
const handleClick = () => {}
</script>

<style scoped>
/* 组件样式 */
</style>
```

### 注释规范

```javascript
/**
 * 函数说明
 * @param {Type} param - 参数说明
 * @returns {Type} 返回值说明
 */
function example(param) {
  // 实现
}
```

---

## 性能优化点

### 1. 代码分割
- 路由懒加载
- 组件异步加载

### 2. 资源优化
- 图片懒加载
- 音频流式传输

### 3. 请求优化
- 请求防抖
- 请求缓存

### 4. 渲染优化
- 计算属性缓存
- v-show vs v-if
- 虚拟滚动

---

## 扩展建议

### 短期扩展
- [ ] 添加单元测试
- [ ] 添加E2E测试
- [ ] 优化移动端

### 中期扩展
- [ ] 添加用户系统
- [ ] 添加权限管理
- [ ] 添加数据统计

### 长期扩展
- [ ] PWA支持
- [ ] 离线功能
- [ ] 国际化

---

## 相关文档

- [快速入门](QUICKSTART.md)
- [功能详解](FEATURES.md)
- [开发检查清单](CHECKLIST.md)
- [迁移指南](MIGRATION_GUIDE.md)

---

**最后更新**: 2024-XX-XX
