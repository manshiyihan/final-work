# 基于Conformer模型的抗欺诈说话人识别系统

> 毕业设计终稿

## 项目简介

本系统是一个基于深度学习的抗欺诈说话人识别系统，融合了 MFA Conformer 说话人识别模型和 RawGAT-ST 反欺诈检测模型，实现双重验证机制。

### 核心功能

- **说话人识别**：基于 MFA Conformer 模型，提取 192 维声纹嵌入向量，通过 FAISS 向量检索实现高效说话人匹配
- **反欺诈检测**：基于 RawGAT-ST 模型，检测合成语音、重放攻击等欺诈行为
- **结果融合**：双模型并行推理，智能融合输出最终判定结果和风险评分
- **Web界面**：基于 Vue 3 + FastAPI 的前后端分离架构

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
| 前端 | Vue 3 + Vite 5 + Element Plus |
| 后端 | FastAPI + Uvicorn + Python 3.8+ |
| 深度学习 | PyTorch + Lightning |
| 说话人识别 | MFA Conformer (192维嵌入向量) |
| 反欺诈检测 | RawGAT-ST (RawNet2 + Graph Attention) |
| 向量检索 | FAISS |
| 数据库 | SQLite |

## 系统要求

> **本系统仅支持 Linux 系统运行**

| 软件 | 版本要求 |
|------|----------|
| 操作系统 | Ubuntu 20.04 LTS 或更高版本 |
| Python | >= 3.8 |
| Node.js | >= 14.18 |
| CUDA (可选) | >= 11.0 |
| 内存 | >= 8GB |
| 磁盘 | >= 5GB |

## 快速开始

### 1. 创建环境

```bash
# 使用 conda 创建环境
conda env create -f environment.yml
conda activate mfa
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 启动服务

```bash
# 终端1 - 启动后端
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 终端2 - 启动前端
cd frontend && npm run dev
```

### 4. 访问系统

- 前端界面：http://localhost:7860
- API 文档：http://127.0.0.1:8000/docs

## 目录结构

```
.
├── app/                           # FastAPI 后端
│   ├── main.py                    # 应用入口
│   ├── services/                  # 业务服务
│   └── repositories/              # 数据访问层
├── frontend/                      # Vue 3 前端
│   ├── src/components/            # Vue 组件
│   └── src/views/                 # 页面视图
├── mfa_conformer_sv/              # 说话人识别模型
├── RawGAT-ST-antispoofing-main/   # 反欺诈检测模型
├── data/                          # 数据目录
├── environment.yml                # Conda 环境配置
└── requirements_api.txt           # Python 依赖
```

## 使用说明

### 注册与登录

1. 访问 http://localhost:7860
2. 点击「注册」创建新账号
3. 使用账号密码登录系统

### 检测功能

| 功能 | 说明 |
|------|------|
| 文件检测 | 上传音频文件进行说话人识别和反欺诈检测 |
| 录音检测 | 实时录制音频进行检测 |
| 注册说话人 | 录制或上传音频，将说话人注册到声纹库 |
| 历史记录 | 查看所有检测记录 |

### API 接口

```bash
# 用户注册
curl -X POST "http://127.0.0.1:8000/api/auth/register" \
  -F "username=testuser" -F "email=test@test.com" -F "password=123456"

# 用户登录
curl -X POST "http://127.0.0.1:8000/api/auth/login" \
  -F "username=testuser" -F "password=123456"

# 音频检测
curl -X POST "http://127.0.0.1:8000/api/verify" \
  -H "Authorization: Bearer <token>" \
  -F "audio=@test.wav"
```

## 性能指标

| 指标 | 数值 |
|------|------|
| MFA Conformer EER | 0.72% |
| RawGAT-ST 准确率 | ~95% |
| 单次推理延迟 | ~1-2s (CPU) / ~200ms (GPU) |

## 致谢

- [MFA Conformer](https://github.com/wenet-e2e/wenet-speaker) - 说话人识别模型
- [RawGAT-ST](https://github.com/JinxinXiang/RawGAT-ST-antispoofing) - 反欺诈检测模型
- [FastAPI](https://fastapi.tiangolo.com/) - Python Web 框架
- [Vue.js](https://vuejs.org/) - JavaScript 框架
