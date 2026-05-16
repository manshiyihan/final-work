# Gradio到Vue迁移指南

本文档说明如何从Gradio前端迁移到Vue前端。

## 架构对比

### Gradio版本 (gui/gui.py)
- 基于Python的Gradio框架
- 服务端渲染
- 简单快速但定制性有限
- 端口: 7860

### Vue版本 (frontend/)
- 基于Vue 3 + Vite
- 客户端渲染
- 高度可定制，现代化UI
- 端口: 7860（保持一致）

## 功能映射

| Gradio功能 | Vue组件 | 说明 |
|-----------|---------|------|
| 本地文件检测 Tab | FileDetection.vue | 完全对等 |
| 录音检测 Tab | RecordDetection.vue | 完全对等 |
| 注册说话人（录音）Tab | RegisterRecord.vue | 完全对等 |
| 注册说话人（文件）Tab | RegisterFile.vue | 完全对等 |
| 历史记录 Tab | HistoryRecords.vue | 完全对等 |

## API接口保持不变

Vue前端使用相同的后端API接口：

- `POST /api/verify` - 音频检测
- `POST /api/register` - 注册说话人
- `GET /api/records/query` - 查询历史记录
- `GET /api/health` - 健康检查

## 迁移步骤

### 1. 安装Node.js环境

```bash
# 检查是否已安装
node --version
npm --version

# 如未安装，访问 https://nodejs.org/ 下载安装
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 启动后端API（必须）

```bash
# 在项目根目录
./scripts/run_api.sh
```

### 4. 启动Vue前端

```bash
# 方式1: 使用启动脚本
./frontend/run.sh

# 方式2: 直接运行
cd frontend
npm run dev
```

### 5. 访问应用

打开浏览器访问: http://localhost:7860

## 配置说明

### 后端API地址配置

开发环境通过Vite代理配置（`vite.config.js`）：

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8000',
      changeOrigin: true
    }
  }
}
```

生产环境需要配置Nginx反向代理或修改API基础URL。

### 端口配置

修改 `vite.config.js` 中的端口：

```javascript
server: {
  port: 7860  // 修改为其他端口
}
```

## 生产部署

### 1. 构建生产版本

```bash
cd frontend
npm run build
```

### 2. 部署静态文件

构建产物在 `frontend/dist` 目录，可以部署到：

- Nginx
- Apache
- CDN
- 静态托管服务

### 3. Nginx配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # 后端API代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 优势对比

### Vue版本优势

1. **性能更好**
   - 客户端渲染，减轻服务器压力
   - 按需加载，首屏加载更快
   - 更流畅的交互体验

2. **UI更现代**
   - Element Plus组件库
   - 响应式设计
   - 更美观的视觉效果

3. **可定制性强**
   - 完全控制前端代码
   - 易于添加新功能
   - 易于修改样式

4. **开发体验好**
   - 热模块替换（HMR）
   - TypeScript支持（可选）
   - 完善的开发工具

### Gradio版本优势

1. **快速原型**
   - Python代码即可创建UI
   - 无需前端知识
   - 适合快速演示

2. **部署简单**
   - 单个Python文件
   - 无需构建步骤

## 兼容性说明

### 数据格式
- ✅ API请求/响应格式完全兼容
- ✅ 数据库结构无需修改
- ✅ 模型推理逻辑无需修改

### 功能特性
- ✅ 所有Gradio功能都已实现
- ✅ 录音功能使用浏览器原生API
- ✅ 文件上传使用FormData

### 浏览器要求
- Chrome >= 87
- Firefox >= 78
- Safari >= 14
- Edge >= 88

## 常见问题

### Q: 可以同时运行Gradio和Vue版本吗？
A: 可以，但需要修改其中一个的端口号，避免冲突。

### Q: 如何切换回Gradio版本？
A: 停止Vue前端，运行 `./gui/run_gui.sh` 即可。

### Q: Vue版本需要修改后端代码吗？
A: 不需要，后端API完全兼容。

### Q: 录音功能在Vue版本中如何实现？
A: 使用浏览器原生的 MediaRecorder API，无需额外依赖。

### Q: 如何添加新功能？
A: 在 `src/components/` 创建新组件，在 `MainLayout.vue` 中引入即可。

## 技术支持

如遇到问题，请检查：

1. Node.js版本是否 >= 14.18
2. 后端API是否正常运行
3. 浏览器控制台是否有错误信息
4. 网络请求是否成功

## 下一步

- [ ] 添加用户认证功能
- [ ] 添加实时监控面板
- [ ] 添加批量处理功能
- [ ] 优化移动端体验
- [ ] 添加国际化支持
