# CFAD数据集训练快速指南

## 🚀 快速开始

所有文件已经配置好，可以直接开始训练！

### 方式一：使用启动脚本（推荐）

```bash
cd RawGAT-ST-antispoofing-main
./train_cfad.sh
```

### 方式二：手动运行

```bash
cd RawGAT-ST-antispoofing-main

python train_cfad_improved.py \
    --cfad_root /home/xujiwu/comb_model/CFAD \
    --version clean \
    --batch_size 16 \
    --num_epochs 100
```

## 📁 文件说明

已创建的文件：
- ✅ `augmentation.py` - 数据增强模块
- ✅ `data_utils_cfad.py` - CFAD数据加载器
- ✅ `train_cfad_improved.py` - 改进的训练脚本
- ✅ `train_cfad.sh` - 一键启动脚本

## ⚙️ 训练参数

在 `train_cfad.sh` 中可以修改：

```bash
VERSION="clean"          # 数据版本: clean, codec, noisy
BATCH_SIZE=16           # 批次大小（显存不足改为8）
NUM_EPOCHS=100          # 训练轮数
LEARNING_RATE=0.0001    # 学习率
WEIGHT_DECAY=0.0005     # 权重衰减
MIXUP_ALPHA=0.2         # Mixup强度
```

## 📊 训练过程

训练时会显示：

```
Epoch 1/100
------------------------------------------------------------
训练损失: 0.3245
验证损失: 0.2891 | 准确率: 87.32%
已见测试: 损失=0.0234 | 准确率=99.12%
未见测试: 损失=0.1567 | 准确率=82.45%  ⭐ 重点关注
✓ 保存最佳模型 (未见测试准确率: 82.45%)
```

## 📈 查看训练日志

在另一个终端运行：

```bash
cd RawGAT-ST-antispoofing-main
tensorboard --logdir logs/
```

然后打开浏览器访问: http://localhost:6006

## 🎯 预期效果

| 指标 | 当前值 | 目标值 |
|------|--------|--------|
| 未见测试EER | 26.49% | 8-15% |
| 未见测试准确率 | 73.5% | 85-92% |

## 🔧 常见问题

### 1. CUDA out of memory

```bash
# 修改 train_cfad.sh 中的 BATCH_SIZE
BATCH_SIZE=8  # 或者更小
```

### 2. 数据加载慢

第一次运行会扫描所有文件并生成缓存，需要10-20分钟。
之后会直接加载缓存，速度很快。

### 3. 想要快速测试

```bash
python train_cfad_improved.py \
    --cfad_root /home/xujiwu/comb_model/CFAD \
    --version clean \
    --batch_size 16 \
    --num_epochs 10 \
    --comment "quick_test"
```

## 📝 训练完成后

1. **查看最佳模型**
   ```bash
   ls models/cfad_clean_improved_v1/best_model.pth
   ```

2. **评估模型**
   ```bash
   cd ..
   python evaluate_cfad_advanced.py
   ```

3. **查看训练曲线**
   - 打开TensorBoard
   - 检查 loss/test_unseen 和 accuracy/test_unseen

## 💡 改进策略

训练脚本已集成：
- ✅ 波形增强（噪声、时移、速度扰动）
- ✅ Mixup数据混合
- ✅ 频谱掩码
- ✅ Label smoothing
- ✅ 梯度裁剪
- ✅ 余弦退火学习率
- ✅ 早停机制
- ✅ 权重衰减

## 🎓 下一步

1. 运行 `./train_cfad.sh` 开始训练
2. 监控TensorBoard查看进度
3. 等待训练完成（约8-12小时）
4. 评估模型性能
5. 根据结果调整参数

祝训练顺利！🚀
