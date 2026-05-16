# 抗欺诈说话人识别系统 - Vue前端

基于 Vue 3 + Vite + Element Plus 的现代化前端界面。

## 功能特性

- ✅ 本地文件检测 - 上传音频文件进行检测
- 🎤 录音检测 - 实时录制音频并检测
- 👤 注册说话人（录音） - 录制音频注册新说话人
- 📁 注册说话人（文件） - 上传文件注册新说话人
- 📊 历史记录查询 - 查看和导出检测历史

## 技术栈

- **Vue 3** - 渐进式JavaScript框架
- **Vite** - 下一代前端构建工具
- **Element Plus** - Vue 3 UI组件库
- **Vue Router** - 官方路由管理器
- **Axios** - HTTP客户端

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动后端API

确保后端API服务已启动（默认地址：http://127.0.0.1:8000）

```bash
# 在项目根目录
./scripts/run_api.sh
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:7860

### 4. 构建生产版本

```bash
npm run build
```

构建产物将生成在 `dist` 目录。

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API接口封装
│   │   └── index.js
│   ├── components/       # Vue组件
│   │   ├── FileDetection.vue      # 文件检测
│   │   ├── RecordDetection.vue    # 录音检测
│   │   ├── RegisterRecord.vue     # 录音注册
│   │   ├── RegisterFile.vue       # 文件注册
│   │   ├── HistoryRecords.vue     # 历史记录
│   │   └── ResultDisplay.vue      # 结果展示
│   ├── router/           # 路由配置
│   │   └── index.js
│   ├── views/            # 页面视图
│   │   └── MainLayout.vue
│   ├── App.vue           # 根组件
│   └── main.js           # 入口文件
├── index.html            # HTML模板
├── vite.config.js        # Vite配置
├── package.json          # 项目配置
└── README.md             # 说明文档
```

## API代理配置

开发环境下，Vite会自动将 `/api` 请求代理到后端服务器：

```javascript
// vite.config.js
server: {
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8000',
      changeOrigin: true
    }
  }
}
```

## 浏览器兼容性

- Chrome >= 87
- Firefox >= 78
- Safari >= 14
- Edge >= 88

## 注意事项

1. 录音功能需要浏览器支持 `MediaRecorder API`
2. 录音功能需要用户授权麦克风权限
3. 某些浏览器在非HTTPS环境下可能限制麦克风访问
4. 建议使用现代浏览器以获得最佳体验

## 开发说明

### 添加新组件

在 `src/components/` 目录下创建新的 `.vue` 文件，然后在 `MainLayout.vue` 中引入使用。

### 添加新API

在 `src/api/index.js` 中添加新的API函数：

```javascript
export const newApi = (data) => {
  return api.post('/new-endpoint', data)
}
```

### 修改样式

每个组件都有自己的 `<style scoped>` 样式，全局样式在 `App.vue` 中定义。

## 故障排除

### 问题1: 无法启动开发服务器
- 检查Node.js版本（需要 >= 14.18）
- 删除 `node_modules` 和 `package-lock.json`，重新安装依赖

### 问题2: API请求失败
- 检查后端服务是否启动
- 检查代理配置是否正确
- 查看浏览器控制台的网络请求

### 问题3: 录音功能不可用
- 检查浏览器是否支持 MediaRecorder API
- 检查是否授权了麦克风权限
- 尝试使用HTTPS访问

## 与Gradio版本对比

### 优势
- ✅ 更现代化的UI设计
- ✅ 更好的响应式布局
- ✅ 更流畅的用户体验
- ✅ 更易于定制和扩展
- ✅ 更好的性能和加载速度

### 功能对等
- ✅ 所有Gradio版本的功能都已实现
- ✅ API接口完全兼容
- ✅ 数据格式保持一致

## License

与主项目保持一致
