#!/bin/bash

# CFAD数据集改进训练脚本
# 使用数据增强和正则化提升泛化能力

echo "=========================================="
echo "CFAD数据集 - RawGAT-ST 改进训练"
echo "=========================================="

# CFAD数据集路径（使用绝对路径）
CFAD_ROOT="/home/xujiwu/comb_model/CFAD"

# 训练参数
VERSION="clean"          # 数据版本: clean, codec, noisy
BATCH_SIZE=16           # 批次大小
NUM_EPOCHS=100          # 训练轮数
LEARNING_RATE=0.0001    # 学习率
WEIGHT_DECAY=0.0005     # 权重衰减
MIXUP_ALPHA=0.2         # Mixup强度
LR_SCHEDULER="cosine"   # 学习率调度器
EARLY_STOP=15           # 早停耐心值
NUM_WORKERS=4           # 数据加载线程数

echo "CFAD数据路径: $CFAD_ROOT"
echo "数据版本: $VERSION"
echo "批次大小: $BATCH_SIZE"
echo "训练轮数: $NUM_EPOCHS"
echo "学习率: $LEARNING_RATE"
echo "权重衰减: $WEIGHT_DECAY"
echo ""

# 检查CFAD数据集是否存在
if [ ! -d "$CFAD_ROOT" ]; then
    echo "错误: CFAD数据集不存在: $CFAD_ROOT"
    echo "请确保CFAD数据集在正确的位置"
    exit 1
fi

echo "开始训练..."
echo ""

# 运行CFAD改进训练脚本
python train_cfad_improved.py \
    --cfad_root "$CFAD_ROOT" \
    --version "$VERSION" \
    --batch_size $BATCH_SIZE \
    --num_epochs $NUM_EPOCHS \
    --lr $LEARNING_RATE \
    --weight_decay $WEIGHT_DECAY \
    --use_mixup \
    --mixup_alpha $MIXUP_ALPHA \
    --lr_scheduler "$LR_SCHEDULER" \
    --early_stop_patience $EARLY_STOP \
    --num_workers $NUM_WORKERS \
    --comment "improved_v1"

echo ""
echo "=========================================="
echo "训练完成！"
echo "=========================================="
echo "模型保存在: models/cfad_${VERSION}_improved_v1/"
echo ""
echo "查看训练日志:"
echo "tensorboard --logdir logs/"
echo ""
echo "评估模型:"
echo "cd .."
echo "python evaluate_cfad_advanced.py"
