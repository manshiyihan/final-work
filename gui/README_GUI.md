# 语音安全检测系统 GUI

一个美观易用的语音安全检测系统界面，支持说话人验证和反欺骗检测。

## 功能特性

- **本地文件检测**: 上传本地音频文件进行检测
- **录音检测**: 实时录制音频并进行检测
- **双重检测**: 同时进行说话人验证和反欺骗检测
- **历史记录查询**: 查看数据库中的检测历史并按标签筛选
- **美观界面**: 现代化的 Web 界面设计

## 系统要求

- Python 3.7+
- 已安装项目所需的模型和依赖

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements_gui.txt
```

### 2. 启动后端 API（推荐）

在项目根目录执行：

```bash
./scripts/run_api.sh
```

默认地址为 `http://127.0.0.1:8000`。

### 3. 启动 GUI

方式一：使用启动脚本
```bash
./run_gui.sh
```

方式二：直接运行
```bash
python gui.py
```

如果后端 API 不在默认地址，可设置：

```bash
export COMB_API_BASE_URL="http://你的后端IP:8000"
```

### 4. 访问界面

启动后，在浏览器中打开显示的地址（通常是 `http://localhost:7860`）

## 使用说明

### 模式1: 本地文件检测

1. 切换到 "📁 本地文件检测" 标签页
2. 点击 "选择音频文件" 按钮，选择要检测的音频文件
3. 上传后可以预览音频
4. 点击 "🚀 开始检测" 按钮
5. 等待检测完成，查看结果

### 模式2: 录音检测

1. 切换到 "🎤 录音检测" 标签页
2. 点击录音按钮开始录制（需要允许浏览器访问麦克风）
3. 录制完成后，点击 "🚀 开始检测" 按钮
4. 等待检测完成，查看结果

### 模式3: 历史记录查询

1. 切换到 "历史记录" 标签页
2. 选择页码、最终标签和输入类型筛选
3. 点击 "刷新记录" 查看数据库中的历史检测数据
4. 点击 "导出当前筛选CSV" 可下载当前筛选结果，便于实验统计与论文附录
5. 点击 "导出全部筛选CSV" 可自动分页汇总导出当前筛选下的全部记录

## 检测结果说明

### 说话人验证结果
- 如果匹配成功，会显示匹配的人员名称
- 如果未匹配，会显示 "该人员不在库中"

### 反欺骗检测结果
- **真实**: 音频为真实语音
- **虚假**: 音频为伪造/合成语音

## 配置说明

模型路径在 `gui.py` 中配置，默认路径为：
- MFA Conformer 模型: `mfa_conformer_sv/epoch=17_cosine_eer=0.72.ckpt`
- RawGAT-ST 模型: `RawGAT-ST-antispoofing-main/epoch_42.pth`

如需修改，请编辑 `gui.py` 中的路径配置。  
GUI 默认优先调用 API（`/api/verify`、`/api/register`），若 API 不可用会自动回退到本地推理模式。

## 故障排除

### 问题1: 无法启动界面
- 检查是否安装了 `gradio`: `pip install gradio`
- 检查端口 7860 是否被占用

### 问题2: 检测失败
- 检查模型文件是否存在
- 检查音频文件格式是否支持
- 查看终端错误信息

### 问题3: 录音功能不可用
- 检查浏览器是否允许访问麦克风
- 尝试使用 HTTPS 连接（某些浏览器要求）

## 注意事项

- 确保音频文件格式正确（支持 wav, mp3, flac 等）
- 录音时请保持环境安静
- 检测过程可能需要几秒钟，请耐心等待

## 技术栈

- **Gradio**: Web 界面框架
- **Python**: 后端处理
- **Subprocess**: 调用模型推理脚本

## 批量评测（论文实验）

在后端 API 启动后，可使用脚本批量调用 `/api/verify` 并导出 CSV：

```bash
python scripts/eval_batch.py --audio_dir wav --output_csv results/eval_results.csv
```

如需提供真值标签，可传入 `--manifest_csv`，格式为两列：`filename,label`。

## 数据清理与归档策略

- 上传音频目录 `data/uploads` 默认保留 7 天，后端会定时清理过期文件。
- `inference_record` 默认保留 30 天，过期记录会归档导出到 `data/archive` 下的 CSV 文件，并从数据库删除。
- 定时任务由后端启动时自动运行，也可手动触发：

```bash
# 手动清理 uploads
curl -X POST "http://127.0.0.1:8000/api/maintenance/cleanup-uploads?retention_days=7"

# 手动归档数据库记录
curl -X POST "http://127.0.0.1:8000/api/maintenance/archive-records?retention_days=30&delete_archived=true"
```

