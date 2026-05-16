# Vue前端功能详解

## 核心功能

### 1. 文件上传检测 (FileDetection.vue)

**功能描述**
- 支持拖拽上传音频文件
- 支持点击选择文件
- 实时音频预览
- 一键检测

**支持格式**
- WAV
- MP3
- FLAC
- M4A
- OGG

**用户体验**
- 拖拽区域高亮提示
- 上传进度显示
- 音频波形预览
- 检测结果可视化

**技术实现**
```vue
<el-upload
  drag
  :auto-upload="false"
  :on-change="handleFileChange"
  accept="audio/*"
>
```

---

### 2. 实时录音检测 (RecordDetection.vue)

**功能描述**
- 浏览器内录音
- 实时录音状态显示
- 录音预览播放
- 自动格式转换

**录音流程**
1. 请求麦克风权限
2. 开始录音（显示录音指示器）
3. 停止录音
4. 预览录音
5. 提交检测

**技术实现**
```javascript
// 使用MediaRecorder API
const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
const mediaRecorder = new MediaRecorder(stream)
```

**音频处理**
- 自动转换为16kHz单声道
- WAV格式输出
- 音频质量优化

---

### 3. 说话人注册 (RegisterRecord.vue & RegisterFile.vue)

**录音注册功能**
- 实时录音
- 说话人名称输入
- 名称格式验证
- 注册结果反馈

**文件注册功能**
- 文件上传
- 格式自动检测
- 音频预处理
- 注册确认

**名称验证规则**
- 支持中文、英文、数字
- 支持下划线和连字符
- 自动清理特殊字符
- 防止重复注册

**技术实现**
```javascript
// 名称清理
const cleanName = name.replace(/[^\w\s\u4e00-\u9fff-]/g, '')
                      .replace(/[-\s]+/g, '_')
```

---

### 4. 历史记录查询 (HistoryRecords.vue)

**查询功能**
- 分页查询
- 多条件筛选
- 实时刷新
- 数据排序

**筛选条件**
- 最终标签（通过/疑似欺诈/身份未知）
- 输入类型（上传/录音）
- 页码选择
- 每页数量

**导出功能**
- 导出当前页CSV
- 导出全部数据CSV
- 自动分页获取
- UTF-8编码支持

**数据展示**
- 表格形式展示
- 状态标签着色
- 风险分数可视化
- 时间格式化

**技术实现**
```javascript
// CSV导出
const csv = '\uFEFF' + data.map(row => row.join(',')).join('\n')
const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
```

---

### 5. 结果展示 (ResultDisplay.vue)

**展示内容**
- 检测状态（通过/疑似欺诈/身份未知）
- 说话人识别结果
- 反欺骗检测结果
- 风险分数
- 检测耗时

**可视化元素**
- 状态图标（✅/🚨/⚠️）
- 彩色标签
- 进度条
- 详情卡片

**详细信息**
- 说话人验证详情
- 反欺骗检测详情
- 原始输出展示
- 时间戳记录

**风险分数展示**
```javascript
// 根据分数显示不同颜色
const riskColor = computed(() => {
  if (score < 0.3) return '#67c23a'  // 绿色
  if (score < 0.7) return '#e6a23c'  // 橙色
  return '#f56c6c'                    // 红色
})
```

---

## UI/UX设计

### 设计原则

1. **简洁明了**
   - 清晰的视觉层次
   - 直观的操作流程
   - 最少的学习成本

2. **响应式设计**
   - 适配桌面端
   - 适配平板
   - 适配移动端

3. **视觉反馈**
   - 加载状态提示
   - 操作结果反馈
   - 错误信息提示

4. **一致性**
   - 统一的配色方案
   - 统一的组件风格
   - 统一的交互模式

### 配色方案

```css
/* 主色调 */
--primary-color: #667eea;
--primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* 状态色 */
--success-color: #67c23a;  /* 通过 */
--warning-color: #e6a23c;  /* 警告 */
--danger-color: #f56c6c;   /* 危险 */
--info-color: #909399;     /* 信息 */
```

### 动画效果

1. **录音指示器**
   - 脉冲动画
   - 颜色渐变
   - 吸引注意力

2. **加载状态**
   - 旋转动画
   - 进度条
   - 骨架屏

3. **页面切换**
   - 淡入淡出
   - 平滑过渡
   - 无闪烁

---

## 性能优化

### 1. 代码分割
```javascript
// 路由懒加载
const FileDetection = () => import('@/components/FileDetection.vue')
```

### 2. 资源优化
- 图片懒加载
- 音频流式传输
- 组件按需加载

### 3. 请求优化
- 请求防抖
- 请求缓存
- 并发控制

### 4. 渲染优化
- 虚拟滚动
- 计算属性缓存
- 条件渲染

---

## 安全性

### 1. 输入验证
- 文件类型检查
- 文件大小限制
- 名称格式验证

### 2. XSS防护
- 输入转义
- 内容安全策略
- 安全的HTML渲染

### 3. CSRF防护
- Token验证
- 同源策略
- 请求头验证

---

## 浏览器兼容性

### 支持的浏览器

| 浏览器 | 最低版本 | 录音功能 |
|--------|---------|---------|
| Chrome | 87+ | ✅ |
| Firefox | 78+ | ✅ |
| Safari | 14+ | ✅ |
| Edge | 88+ | ✅ |

### 功能降级

- 不支持录音时显示提示
- 不支持拖拽时使用点击上传
- 不支持某些CSS特性时使用备用样式

---

## 可访问性

### ARIA支持
- 语义化HTML
- ARIA标签
- 键盘导航

### 屏幕阅读器
- 表单标签
- 状态提示
- 错误信息

### 键盘操作
- Tab导航
- Enter提交
- Esc取消

---

## 国际化准备

虽然当前版本为中文，但架构支持国际化：

```javascript
// 未来可以添加
import { createI18n } from 'vue-i18n'

const i18n = createI18n({
  locale: 'zh-CN',
  messages: {
    'zh-CN': { /* 中文 */ },
    'en-US': { /* English */ }
  }
})
```

---

## 扩展性

### 添加新功能

1. 创建新组件
```bash
touch src/components/NewFeature.vue
```

2. 在MainLayout中引入
```vue
import NewFeature from '@/components/NewFeature.vue'
```

3. 添加到标签页
```vue
<el-tab-pane label="新功能" name="new">
  <NewFeature />
</el-tab-pane>
```

### 添加新API

```javascript
// src/api/index.js
export const newApi = (data) => {
  return api.post('/new-endpoint', data)
}
```

---

## 测试建议

### 单元测试
```bash
npm install -D vitest @vue/test-utils
```

### E2E测试
```bash
npm install -D cypress
```

### 测试覆盖
- 组件渲染测试
- API调用测试
- 用户交互测试
- 边界情况测试

---

## 未来规划

- [ ] 批量检测功能
- [ ] 实时监控面板
- [ ] 数据统计图表
- [ ] 用户权限管理
- [ ] 移动端优化
- [ ] PWA支持
- [ ] 离线功能
- [ ] WebSocket实时通信
