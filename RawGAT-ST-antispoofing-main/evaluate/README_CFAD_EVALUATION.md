# CFAD数据集评估指南

本指南介绍如何在CFAD数据集上评估抗伪造语音模型（RawGAT-ST）的各种指标。

## 功能特性

- ✅ 支持多种数据集格式（协议文件或目录结构）
- ✅ 计算多种评估指标（EER, 准确率, 精确率, 召回率, F1, AUC等）
- ✅ 生成可视化图表（DET曲线, ROC曲线, 分数分布等）
- ✅ 批量处理，支持GPU加速
- ✅ 自动音频格式转换（16kHz单声道）

## 评估指标

### 基础指标
- **EER (Equal Error Rate)**: 等错误率，FAR和FRR相等时的错误率
- **准确率 (Accuracy)**: 正确分类的样本比例
- **精确率 (Precision)**: 预测为正例中真正为正例的比例
- **召回率 (Recall)**: 真正例中被正确预测的比例
- **F1分数**: 精确率和召回率的调和平均

### 高级指标
- **AUC**: ROC曲线下面积
- **DET曲线**: 检测错误权衡曲线
- **ROC曲线**: 受试者工作特征曲线
- **混淆矩阵**: TP, TN, FP, FN统计

## CFAD数据集结构

CFAD数据集的标准结构如下：

```
CFAD/
├── clean_version/
│   ├── train_clean/
│   │   ├── real_clean/
│   │   └── fake_clean/
│   ├── dev_clean/
│   │   ├── real_clean/
│   │   └── fake_clean/
│   ├── test_seen_clean/
│   │   ├── real_clean/
│   │   └── fake_clean/
│   └── test_unseen_clean/
│       ├── real_clean/
│       └── fake_clean/
├── noisy_version/
│   └── ...
└── codec_version/
    └── ...
```

## 数据集格式支持

### 方式1: CFAD标准结构（推荐）

脚本自动识别以下目录结构：
- `real_clean/`, `real_codec/`, `real_noise/` 等 → 真实语音
- `fake_clean/`, `fake_codec/`, `fake_noise/` 等 → 伪造语音

### 方式2: 通用目录结构

也支持以下结构：
```
data_dir/
├── bonafide/ 或 real/
│   └── ...
└── spoof/ 或 fake/
    └── ...
```

### 方式3: 协议文件格式

创建一个文本文件，每行格式为：
```
file_id label
```

其中 `label` 可以是：
- `bonafide`, `real`, `1` → 真实语音
- `spoof`, `fake`, `0` → 伪造语音

## 使用方法

### 方式1: 对比评估（已见 vs 未见数据集）⭐ 推荐

同时评估已见和未见数据集，并生成对比报告：

```bash
python evaluate_cfad_compare.py \
    --base_dir /path/to/CFAD \
    --version clean \
    --output_dir ./comparison_results
```

**输出内容：**
- 对比报告（文本格式）
- 对比表格（CSV格式）
- 对比可视化图表（6个子图）
- 各数据集的详细结果

### 方式2: 直接指定数据目录（单个数据集评估）

```bash
# 基础评估
python evaluate_cfad.py \
    --data_dir /path/to/CFAD/clean_version/test_seen_clean \
    --output_dir ./results

# 高级评估（包含可视化）
python evaluate_cfad_advanced.py \
    --data_dir /path/to/CFAD/clean_version/test_seen_clean \
    --output_dir ./results \
    --batch_size 16
```

### 方式3: 使用自动路径构建（更便捷）

```bash
# 自动构建路径: CFAD/clean_version/test_seen_clean/
python evaluate_cfad.py \
    --data_dir /path/to/CFAD \
    --version clean \
    --split test_seen \
    --output_dir ./results

# 评估noisy版本
python evaluate_cfad_advanced.py \
    --data_dir /path/to/CFAD \
    --version noisy \
    --split dev \
    --output_dir ./results_noisy
```

### 方式4: 使用协议文件

```bash
python evaluate_cfad_advanced.py \
    --data_dir /path/to/cfad/dataset \
    --protocol_file /path/to/protocol.txt \
    --output_dir ./results
```

## 参数说明

### 对比评估脚本 (evaluate_cfad_compare.py)

- `--base_dir`: CFAD数据集基础目录路径（必需）
- `--version`: CFAD数据集版本（默认: `clean`）
  - `clean`: 干净版本
  - `noisy`: 噪声版本
  - `codec`: 编码版本
- `--model_path`: 模型检查点路径
- `--model_config`: 模型配置文件路径
- `--output_dir`: 结果输出目录（默认: `./comparison_results`）
- `--batch_size`: 批处理大小（默认: 8）
- `--audio_ext`: 音频文件扩展名（默认: `.wav`）

### 单个数据集评估脚本 (evaluate_cfad.py / evaluate_cfad_advanced.py)

- `--data_dir`: CFAD数据集目录路径（必需）
  - 可以是完整路径（如 `CFAD/clean_version/test_seen_clean`）
  - 或基础路径（配合 `--version` 和 `--split` 使用）
- `--version`: CFAD数据集版本（可选）
  - `clean`: 干净版本
  - `noisy`: 噪声版本
  - `codec`: 编码版本
- `--split`: 数据集划分（可选）
  - `train`: 训练集
  - `dev`: 开发集
  - `test_seen`: 测试集（已见）
  - `test_unseen`: 测试集（未见）
- `--protocol_file`: 协议文件路径（可选）
- `--model_path`: 模型检查点路径（默认: `RawGAT-ST-antispoofing-main/epoch_42.pth`）
- `--model_config`: 模型配置文件路径（默认: `RawGAT-ST-antispoofing-main/model_config_RawGAT_ST.yaml`）
- `--output_dir`: 结果输出目录（默认: `./evaluation_results`）
- `--batch_size`: 批处理大小（默认: 8）
- `--audio_ext`: 音频文件扩展名（默认: `.wav`）

**注意**: 如果同时指定 `--version` 和 `--split`，脚本会自动构建路径：
`{data_dir}/{version}_version/{split}_{version}/`

## 输出文件

### 单个数据集评估输出

1. **scores.txt**: 每个音频文件的预测分数
   ```
   file_id label score
   ```

2. **evaluation_results.txt**: 详细的评估指标报告

3. **evaluation_plots.png** (仅高级版): 包含以下图表：
   - 分数分布直方图
   - DET曲线
   - ROC曲线
   - 箱线图
   - 累积分布函数
   - 指标总结表

### 对比评估输出（evaluate_cfad_compare.py）

1. **comparison_report.txt**: 详细的对比评估报告
   - 数据集信息
   - 指标对比表格
   - 详细指标说明

2. **comparison_table.csv**: CSV格式的对比表格，便于Excel分析

3. **comparison_plots.png**: 对比可视化图表，包含：
   - 主要指标对比柱状图
   - 分数分布对比
   - DET曲线对比
   - 箱线图对比
   - 指标差异对比
   - 统计信息对比表

4. **test_seen/scores.txt**: 已见数据集的分数文件
5. **test_unseen/scores.txt**: 未见数据集的分数文件

## 示例输出

```
评估结果
================================================================================
EER (等错误率): 2.3456%
准确率 (EER阈值): 97.6543%
最佳准确率: 98.1234%
精确率: 96.7890%
召回率: 98.5678%
F1分数: 97.6543%
AUC: 0.9876
================================================================================
```

## 注意事项

1. **音频格式**: 脚本会自动将音频转换为16kHz单声道格式
2. **内存使用**: 大批量处理可能需要较多内存，建议根据GPU内存调整batch_size
3. **依赖库**: 需要安装 `librosa` 用于音频重采样
4. **CUDA**: 如果有GPU，会自动使用GPU加速

## 故障排除

### 问题1: 找不到音频文件
- 检查 `--data_dir` 路径是否正确
- 检查音频文件扩展名是否匹配 `--audio_ext`
- 如果使用协议文件，检查文件路径是否正确

### 问题2: 内存不足
- 减小 `--batch_size` 参数
- 使用CPU模式（虽然会慢一些）

### 问题3: 音频加载失败
- 确保安装了 `soundfile` 和 `librosa`
- 检查音频文件是否损坏

## 依赖安装

```bash
pip install torch torchvision
pip install soundfile librosa
pip install matplotlib numpy pandas tqdm pyyaml
```

## 更多信息

如有问题或建议，请查看项目文档或提交Issue。

