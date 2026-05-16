# Vue前端快速入门

## 5分钟快速开始

### 第一步：检查环境

```bash
# 检查Node.js（需要 >= 14.18）
node --version

# 如果未安装，访问 https://nodejs.org/ 下载安装
```

### 第二步：安装依赖

```bash
cd frontend
npm install
```

预计耗时：1-3分钟

### 第三步：启动后端

```bash
# 在新终端窗口
cd ..
./scripts/run_api.sh
```

等待看到：`Uvicorn running on http://127.0.0.1:8000`

### 第四步：启动前端

```bash
# 回到frontend目录
cd frontend
npm run dev
```

### 第五步：访问应用

打开浏览器访问：http://localhost:7860

🎉 完成！

---

## 一键启动脚本

### Linux/Mac

```bash
# 启动后端（终端1）
./scripts/run_api.sh

# 启动前端（终端2）
./scripts/run_vue_frontend.sh
```

### Windows

```bash
# 启动后端（终端1）
cd app
python -m uvicorn main:app --reload

# 启动前端（终端2）
cd frontend
npm run dev
```

---

## 常见问题

### Q1: npm install 失败

**解决方案**
```bash
# 清理缓存
npm cache clean --force

# 删除node_modules
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

### Q2: 端口被占用

**解决方案**
```bash
# 查找占用7860端口的进程
lsof -i :7860

# 杀死进程
kill -9 <PID>

# 或修改端口（vite.config.js）
server: {
  port: 8080  // 改为其他端口
}
```

### Q3: 无法连接后端API

**检查清单**
- [ ] 后端是否启动？
- [ ] 后端端口是否为8000？
- [ ] 防火墙是否阻止？
- [ ] 代理配置是否正确？

**测试后端**
```bash
curl http://127.0.0.1:8000/api/health
```

### Q4: 录音功能不可用

**可能原因**
- 浏览器不支持MediaRecorder API
- 未授权麦克风权限
- 使用HTTP而非HTTPS

**解决方案**
- 使用Chrome/Firefox/Edge最新版
- 允许麦克风权限
- 本地开发使用localhost（自动允许）

---

## 功能测试

### 测试文件上传

1. 切换到"本地文件检测"标签
2. 点击上传区域
3. 选择音频文件（wav/mp3/flac）
4. 点击"开始检测"
5. 查看结果

### 测试录音

1. 切换到"录音检测"标签
2. 点击"开始录音"
3. 允许麦克风权限
4. 说话3-5秒
5. 点击"停止录音"
6. 点击"开始检测"
7. 查看结果

### 测试注册

1. 切换到"注册说话人（录音）"标签
2. 录制音频
3. 输入说话人名称
4. 点击"注册说话人"
5. 查看注册结果

### 测试历史记录

1. 切换到"历史记录"标签
2. 点击"刷新记录"
3. 查看历史数据
4. 尝试筛选功能
5. 导出CSV

---

## 开发模式

### 热更新

修改代码后自动刷新，无需手动重启：

```bash
# 启动开发服务器
npm run dev

# 修改 src/components/FileDetection.vue
# 浏览器自动刷新
```

### 调试技巧

**1. Vue DevTools**
```bash
# 安装Chrome扩展
# https://chrome.google.com/webstore/detail/vuejs-devtools
```

**2. 查看网络请求**
- 打开浏览器开发者工具（F12）
- 切换到Network标签
- 查看API请求和响应

**3. 查看控制台日志**
```javascript
// 在组件中添加
console.log('调试信息', data)
```

---

## 生产构建

### 构建命令

```bash
npm run build
```

构建产物在 `dist/` 目录。

### 预览构建结果

```bash
npm run preview
```

访问：http://localhost:4173

### 部署到服务器

```bash
# 1. 构建
npm run build

# 2. 上传dist目录到服务器
scp -r dist/* user@server:/var/www/html/

# 3. 配置Nginx
# 参考 README.md 中的Nginx配置
```

---

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API接口封装
│   │   └── index.js      # axios配置和API函数
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
│   ├── utils/            # 工具函数
│   │   └── audioConverter.js
│   ├── App.vue           # 根组件
│   └── main.js           # 入口文件
├── public/               # 静态资源
├── index.html            # HTML模板
├── vite.config.js        # Vite配置
├── package.json          # 项目配置
└── README.md             # 文档
```

---

## 下一步

### 学习资源

**Vue 3**
- 官方文档：https://vuejs.org/
- 中文文档：https://cn.vuejs.org/

**Element Plus**
- 官方文档：https://element-plus.org/
- 组件示例：https://element-plus.org/zh-CN/component/button.html

**Vite**
- 官方文档：https://vitejs.dev/
- 中文文档：https://cn.vitejs.dev/

### 进阶功能

- [ ] 添加用户认证
- [ ] 添加数据可视化
- [ ] 添加批量处理
- [ ] 优化移动端
- [ ] 添加PWA支持

### 贡献代码

欢迎提交Issue和Pull Request！

---

## 获取帮助

### 文档
- [详细README](README.md)
- [功能详解](FEATURES.md)
- [迁移指南](MIGRATION_GUIDE.md)
- [对比文档](../COMPARISON.md)

### 社区
- 提交Issue
- 查看示例代码
- 阅读源码注释

---

## 总结

✅ 5分钟快速启动
✅ 完整功能测试
✅ 开发调试技巧
✅ 生产部署指南
✅ 学习资源推荐

现在开始使用Vue前端吧！🚀
