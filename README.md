# 基于Conformer模型的抗欺诈说话人识别系统

## 项目简介

本系统是一个基于深度学习的抗欺诈说话人识别系统，融合了 MFA Conformer 说话人识别模型和 RawGAT-ST 反欺诈检测模型，实现双重验证机制：

- **说话人识别**：基于 MFA Conformer 模型，提取 192 维声纹嵌入向量，通过 FAISS 向量检索实现高效说话人匹配
- **反欺诈检测**：基于 RawGAT-ST 模型，检测合成语音、重放攻击等欺诈行为
- **结果融合**：双模型并行推理，智能融合输出最终判定结果和风险评分

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Vue 3 前端 (端口 7860)                  │
│   Element Plus UI | 文件上传 | 实时录音 | 历史记录           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI 后端 (端口 8000)                     │
│   用户认证 | 音频处理 | 模型调度 | 数据存储                  │
└─────────────────────────────────────────────────────────────┘
                    │                    │
         ┌──────────┴──────────┐        │
         ▼                     ▼        ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  MFA Conformer  │  │   RawGAT-ST     │  │   SQLite 数据库 │
│  说话人识别模型  │  │   反欺诈模型     │  │   推理记录存储  │
│  (FAISS 检索)   │  │  (二分类检测)   │  │   用户会话管理  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite 5 + Element Plus + Vue Router |
| 后端 | FastAPI + Uvicorn + Python 3.8+ |
| 深度学习 | PyTorch + Lightning |
| 说话人识别 | MFA Conformer (192维嵌入向量) |
| 反欺诈检测 | RawGAT-ST (RawNet2 + Graph Attention) |
| 向量检索 | FAISS (内积索引) |
| 数据库 | SQLite |
| 音频处理 | librosa + soundfile |

## 目录结构

```
.
├── app/                           # FastAPI 后端
│   ├── main.py                    # 应用入口和 API 路由
│   ├── core/                      # 核心配置
│   │   └── config.py
│   ├── services/                  # 业务服务
│   │   ├── model_loader.py        # 模型加载与管理
│   │   ├── model_service.py       # 模型推理服务
│   │   ├── fusion_service.py      # 结果融合服务
│   │   ├── audio_service.py       # 音频处理服务
│   │   ├── auth_service.py        # 用户认证服务
│   │   └── ...
│   ├── repositories/              # 数据访问层
│   └── configs/                   # 配置文件
├── frontend/                      # Vue 3 前端
│   ├── src/
│   │   ├── components/            # Vue 组件
│   │   │   ├── FileDetection.vue  # 文件上传检测
│   │   │   ├── RecordDetection.vue # 实时录音检测
│   │   │   ├── RegisterFile.vue   # 文件注册说话人
│   │   │   ├── HistoryRecords.vue # 历史记录
│   │   │   └── ...
│   │   ├── views/                 # 页面视图
│   │   │   ├── Login.vue          # 登录/注册页
│   │   │   └── MainLayout.vue     # 主布局
│   │   ├── api/                   # API 调用
│   │   └── router/                # 路由配置
│   ├── package.json
│   └── vite.config.js
├── mfa_conformer_sv/              # 说话人识别模型
│   ├── main.py                    # MFA Conformer 模型定义
│   ├── newinference.py            # 推理脚本
│   ├── epoch=17_cosine_eer=0.72.ckpt  # 预训练权重
│   ├── faiss/                     # FAISS 索引和说话人嵌入
│   └── module/                    # 数据处理模块
├── RawGAT-ST-antispoofing-main/   # 反欺诈检测模型
│   ├── model.py                   # RawGAT-ST 模型定义
│   ├── inference.py               # 推理脚本
│   ├── epoch_42.pth               # 预训练权重
│   └── model_config_RawGAT_ST.yaml
├── data/                          # 数据目录
│   ├── app.db                     # SQLite 数据库
│   └── uploads/                   # 上传文件存储
├── scripts/                       # 启动脚本
│   ├── run_api.sh                 # 启动后端
│   └── run_vue_frontend.sh        # 启动前端
└── requirements_api.txt           # Python 依赖
```

---

## 系统部署

### 环境要求

**操作系统**：Ubuntu 20.04 LTS 或更高版本

| 软件 | 版本要求 |
|------|----------|
| Python | >= 3.8 |
| Node.js | >= 14.18 |
| CUDA (可选) | >= 11.0 (GPU 加速) |
| 内存 | >= 8GB |
| 磁盘 | >= 5GB (含模型权重) |

### 一、安装依赖

#### 1. 后端 Python 依赖

```bash
# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements_api.txt
bash conda env create -f environment.yml

# 额外依赖 (如需 GPU 加速)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 2. 前端 Node.js 依赖

```bash
cd frontend
npm install
```

### 二、模型文件准备

系统需要以下预训练模型文件（已包含在仓库中）：

| 模型 | 文件路径 | 大小 |
|------|----------|------|
| MFA Conformer | `mfa_conformer_sv/epoch=17_cosine_eer=0.72.ckpt` | ~50MB |
| RawGAT-ST | `RawGAT-ST-antispoofing-main/epoch_42.pth` | ~20MB |

如需重新训练或下载模型，请参考各模型目录下的 README 文件。

### 三、启动服务

#### 方式一：使用启动脚本 (推荐)

```bash
# 终端 1 - 启动后端
./scripts/run_api.sh

# 终端 2 - 启动前端
./scripts/run_vue_frontend.sh
# 或
cd frontend && ./run.sh
```

#### 方式二：手动启动

```bash
# 终端 1 - 启动后端 API
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 终端 2 - 启动前端开发服务器
cd frontend
npm run dev
```

### 四、验证部署

```bash
# 检查后端健康状态
curl http://127.0.0.1:8000/api/health

# 预期返回
{"status":"ok","time":"2024-01-01T12:00:00"}
```

### 五、访问系统

- **前端界面**：http://localhost:7860
- **API 文档**：http://127.0.0.1:8000/docs
- **API 文档 (ReDoc)**：http://127.0.0.1:8000/redoc

---

## 使用说明

### 用户注册与登录

#### 1. 注册账号

首次使用需要注册账号：

1. 访问 http://localhost:7860，自动跳转到登录页
2. 点击「注册」标签
3. 填写注册信息：
   - 用户名（至少 3 个字符）
   - 邮箱（有效的邮箱格式）
   - 密码（至少 6 个字符）
4. 点击「注册」按钮

#### 2. 登录系统

1. 在登录页输入用户名和密码
2. 点击「登录」按钮
3. 登录成功后自动跳转到主页面

### 核心功能

#### 1. 音频文件检测

用于检测上传的音频文件是否为欺诈音频，并识别说话人身份。

**操作步骤**：
1. 点击左侧菜单「文件检测」
2. 拖拽或点击上传音频文件
3. 支持格式：WAV、MP3、FLAC、OGG 等
4. 系统自动处理并显示结果

**检测结果说明**：
| 字段 | 说明 |
|------|------|
| 说话人结果 | 匹配到的说话人姓名，或「未知」 |
| 欺诈检测结果 | bonafide (真实) 或 spoof (欺诈) |
| 风险评分 | 0.1 (低风险) ~ 0.9 (高风险) |
| 最终判定 | pass / identity_unknown / fraud_risk |

#### 2. 实时录音检测

通过浏览器实时录制音频进行检测。

**操作步骤**：
1. 点击左侧菜单「录音检测」
2. 点击「开始录音」按钮
3. 对着麦克风说话（建议 3-10 秒）
4. 点击「停止录音」
5. 系统自动上传并检测

**注意事项**：
- 需要浏览器授权麦克风权限
- 建议在安静环境下录制
- 录音时长建议 3-10 秒

#### 3. 注册说话人

将新说话人添加到声纹库中。

**操作步骤**：
1. 点击左侧菜单「注册说话人」
2. 输入说话人姓名
3. 上传该说话人的音频文件（文件注册）
   - 或点击「录音注册」实时录制
4. 点击「注册」按钮

**注册建议**：
- 使用清晰、无噪声的音频
- 建议时长 5-30 秒
- 可多次注册同一说话人以提高识别准确率

#### 4. 历史记录

查看历史检测记录。

**功能**：
- 按时间倒序显示记录
- 支持按结果类型筛选
- 支持分页浏览
- 显示检测详情（说话人、欺诈判断、风险评分、延迟等）

### API 接口

#### 认证接口

```bash
# 用户注册
curl -X POST "http://127.0.0.1:8000/api/auth/register" \
  -F "username=testuser" \
  -F "email=test@example.com" \
  -F "password=123456"

# 用户登录
curl -X POST "http://127.0.0.1:8000/api/auth/login" \
  -F "username=testuser" \
  -F "password=123456"

# 返回示例
{
  "ok": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "username": "testuser",
    "email": "test@example.com"
  }
}
```

#### 检测接口

```bash
# 音频检测
curl -X POST "http://127.0.0.1:8000/api/verify" \
  -H "Authorization: Bearer <token>" \
  -F "audio=@test.wav"

# 返回示例
{
  "ok": true,
  "speaker_result": "张三",
  "spoof_result": "bonafide",
  "risk_score": 0.1,
  "final_label": "pass",
  "latency_ms": 1250
}
```

#### 注册说话人接口

```bash
# 注册说话人
curl -X POST "http://127.0.0.1:8000/api/register" \
  -H "Authorization: Bearer <token>" \
  -F "audio=@speaker.wav" \
  -F "speaker_name=张三"

# 返回示例
{
  "ok": true,
  "speaker_name": "张三",
  "message": "注册成功"
}
```

#### 历史记录接口

```bash
# 获取历史记录
curl "http://127.0.0.1:8000/api/records/query?page=1&limit=20" \
  -H "Authorization: Bearer <token>"

# 筛选条件
curl "http://127.0.0.1:8000/api/records/query?final_label=fraud_risk" \
  -H "Authorization: Bearer <token>"
```

---

## 配置说明

### 后端配置

编辑 `app/core/config.py`：

```python
# 模型路径
MFA_CHECKPOINT = "mfa_conformer_sv/epoch=17_cosine_eer=0.72.ckpt"
RAWGAT_MODEL = "RawGAT-ST-antispoofing-main/epoch_42.pth"

# API 端口
API_HOST = "0.0.0.0"
API_PORT = 8000

# 数据保留策略
UPLOAD_RETENTION_DAYS = 7      # 上传文件保留天数
DB_RECORD_RETENTION_DAYS = 30  # 数据库记录保留天数
```

### 前端配置

编辑 `frontend/vite.config.js`：

```javascript
export default defineConfig({
  server: {
    port: 7860,  // 前端端口
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',  // 后端地址
        changeOrigin: true
      }
    }
  }
})
```

### 风险评分配置

编辑 `app/configs/risk_profile.json`：

```json
{
  "rules": {
    "spoof_label_values": ["spoof"],
    "unknown_speaker_values": ["unknown", "未知"]
  },
  "scores": {
    "fraud_risk": 0.9,
    "identity_unknown": 0.7,
    "pass": 0.1
  }
}
```

---

## 生产部署

### 后端部署（Ubuntu）

使用 Gunicorn + Uvicorn 部署：

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务（4 个工作进程）
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### 使用 systemd 管理后端服务

创建服务文件 `/etc/systemd/system/speaker-auth-api.service`：

```ini
[Unit]
Description=Speaker Authentication API
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/project
Environment="PATH=/path/to/project/venv/bin"
ExecStart=/path/to/project/venv/bin/gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动并启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start speaker-auth-api
sudo systemctl enable speaker-auth-api

# 查看状态
sudo systemctl status speaker-auth-api
```

### 前端部署（Ubuntu）

使用 Nginx 托管前端静态文件：

```bash
# 安装 Nginx
sudo apt update
sudo apt install nginx

# 构建前端
cd frontend
npm run build

# 复制构建产物到 Nginx 目录
sudo cp -r dist/* /var/www/html/

# 配置 Nginx（可选：配置反向代理）
sudo nano /etc/nginx/sites-available/default
```

Nginx 配置示例（包含 API 反向代理）：

```nginx
server {
    listen 80;
    server_name your_domain_or_ip;

    # 前端静态文件
    location / {
        root /var/www/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

重启 Nginx：

```bash
sudo nginx -t              # 测试配置
sudo systemctl restart nginx
```

---

## 常见问题

### Q1: 模型加载失败

**错误信息**：`FileNotFoundError: Checkpoint not found`

**解决方案**：
1. 检查模型文件是否存在
2. 确认路径配置正确
3. 如使用 GPU，确保 CUDA 版本兼容

### Q2: 前端无法连接后端

**解决方案**：
1. 确认后端已启动：`curl http://127.0.0.1:8000/api/health`
2. 检查 CORS 配置
3. 确认端口未被占用

### Q3: 音频处理报错

**错误信息**：`librosa is required for resampling`

**解决方案**：
```bash
pip install librosa soundfile
```

### Q4: GPU 内存不足

**解决方案**：
1. 减小批量大小
2. 使用 CPU 推理（自动降级）
3. 模型会自动检测设备并选择 CPU/GPU

### Q5: Token 过期

**解决方案**：
Token 有效期为 7 天，过期后需重新登录。

---

## 性能指标

| 指标 | 数值 |
|------|------|
| MFA Conformer EER | 0.72% |
| RawGAT-ST 准确率 | ~95% (ASVSpoof2019) |
| 单次推理延迟 | ~1-2 秒 (CPU) / ~200ms (GPU) |
| 并发支持 | 多线程并行推理 |

---

## 开发计划

- [ ] 密码重置功能
- [ ] 批量音频检测
- [ ] 实时流式检测
- [ ] 模型热更新
- [ ] 管理 Webhook 通知

---

## 许可证

本项目仅供学习研究使用。

---

## 致谢

- [MFA Conformer](https://github.com/wenet-e2e/wenet-speaker) - 说话人识别模型
- [RawGAT-ST](https://github.com/JinxinXiang/RawGAT-ST-antispoofing) - 反欺诈检测模型
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Element Plus](https://element-plus.org/) - Vue 3 组件库
