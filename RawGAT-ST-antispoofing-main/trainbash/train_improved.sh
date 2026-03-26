#!/bin/bash

# RawGAT-ST 改进训练脚本
# 使用数据增强和正则化提升泛化能力

echo "=========================================="
echo "RawGAT-ST 改进训练"
echo "=========================================="

# 配置路径（根据实际情况修改）
DATABASE_PATH="/home/xujiwu/下载/LA"
PROTOCOLS_PATH="/home/xujiwu/下载/RawGAT-ST-antispoofing-main/database"

# 训练参数
BATCH_SIZE=10
NUM_EPOCHS=100
LEARNING_RATE=0.0001
WEIGHT_DECAY=0.0005
DROPOUT=0.3
MIXUP_ALPHA=0.2

# 进入工作目录
cd RawGAT-ST-antispoofing-main

echo "开始训练..."
echo "数据路径: $DATABASE_PATH"
echo "批次大小: $BATCH_SIZE"
echo "训练轮数: $NUM_EPOCHS"
echo ""

# 运行改进的训练脚本
python main_improved.py \
    --database_path "$DATABASE_PATH" \
    --protocols_path "$PROTOCOLS_PATH" \
    --batch_size $BATCH_SIZE \
    --num_epochs $NUM_EPOCHS \
    --lr $LEARNING_RATE \
    --weight_decay $WEIGHT_DECAY \
    --dropout $DROPOUT \
    --use_mixup \
    --mixup_alpha $MIXUP_ALPHA \
    --lr_scheduler cosine \
    --early_stop_patience 15 \
    --comment "improved_v1"

echo ""
echo "训练完成！"
echo "模型保存在: models/model_improved_logical_${NUM_EPOCHS}_${BATCH_SIZE}_improved_v1/"
echo ""
echo "查看训练日志:"
echo "tensorboard --logdir logs/"
