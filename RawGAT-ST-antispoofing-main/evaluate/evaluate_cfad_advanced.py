#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CFAD数据集高级评估脚本
支持更多评估指标和可视化
"""

import argparse
import os
import sys
from pathlib import Path
import numpy as np
import torch
import yaml
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端

from tqdm import tqdm

BASE_DIR = Path(__file__).parent.absolute()

# 导入基础评估脚本的类
sys.path.insert(0, str(BASE_DIR))
from evaluate_cfad import CFADDataset, load_audio_file, pad
sys.path.insert(0, str(BASE_DIR / "RawGAT-ST-antispoofing-main"))

from model import RawGAT_ST
from tDCF_python import eval_metrics as em


def predict_batch(model, audio_paths, device, batch_size=8):
    """批量预测"""
    model.eval()
    scores = []
    file_ids = []
    
    with torch.no_grad():
        for i in tqdm(range(0, len(audio_paths), batch_size), desc="预测中"):
            batch_paths = audio_paths[i:i+batch_size]
            batch_audio = []
            batch_ids = []
            
            for path_info in batch_paths:
                try:
                    audio = load_audio_file(path_info['path'])
                    batch_audio.append(audio)
                    batch_ids.append(path_info['file_id'])
                except Exception as e:
                    print(f"警告: 无法加载 {path_info['path']}: {e}")
                    continue
            
            if not batch_audio:
                continue
            
            # 模型期望输入形状: [batch_size, sequence_length]
            batch_audio_array = np.array(batch_audio)
            audio_tensor = torch.FloatTensor(batch_audio_array).to(device)
            output = model(audio_tensor, Freq_aug=False)
            batch_scores = output[:, 1].cpu().numpy()
            
            scores.extend(batch_scores)
            file_ids.extend(batch_ids)
    
    return scores, file_ids


def compute_all_metrics(bonafide_scores, spoof_scores):
    """计算所有评估指标"""
    bonafide_scores = np.array(bonafide_scores)
    spoof_scores = np.array(spoof_scores)
    
    metrics = {}
    
    # 1. EER
    eer, eer_threshold = em.compute_eer(bonafide_scores, spoof_scores)
    metrics['EER'] = eer * 100
    metrics['EER_threshold'] = eer_threshold
    
    # 2. DET曲线
    frr, far, thresholds = em.compute_det_curve(bonafide_scores, spoof_scores)
    metrics['FRR'] = frr
    metrics['FAR'] = far
    metrics['thresholds'] = thresholds
    
    # 3. 准确率相关指标
    all_scores = np.concatenate([bonafide_scores, spoof_scores])
    all_labels = np.concatenate([np.ones(len(bonafide_scores)), np.zeros(len(spoof_scores))])
    
    # EER阈值下的指标
    pred_eer = (all_scores >= eer_threshold).astype(int)
    metrics['Accuracy_at_EER'] = np.mean(pred_eer == all_labels) * 100
    
    # 计算TP, TN, FP, FN
    tp = np.sum((pred_eer == 1) & (all_labels == 1))
    tn = np.sum((pred_eer == 0) & (all_labels == 0))
    fp = np.sum((pred_eer == 1) & (all_labels == 0))
    fn = np.sum((pred_eer == 0) & (all_labels == 1))
    
    metrics['TP'] = tp
    metrics['TN'] = tn
    metrics['FP'] = fp
    metrics['FN'] = fn
    
    # 精确率、召回率、F1分数
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    metrics['Precision'] = precision * 100
    metrics['Recall'] = recall * 100
    metrics['F1_Score'] = f1 * 100
    
    # 4. 最佳准确率
    best_acc = 0
    best_thresh = 0
    for thresh in np.linspace(np.min(all_scores), np.max(all_scores), 1000):
        pred = (all_scores >= thresh).astype(int)
        acc = np.mean(pred == all_labels)
        if acc > best_acc:
            best_acc = acc
            best_thresh = thresh
    
    metrics['Best_Accuracy'] = best_acc * 100
    metrics['Best_Accuracy_threshold'] = best_thresh
    
    # 5. AUC (使用DET曲线计算)
    # AUC = 1 - 积分(FAR, FRR)
    auc = np.trapz(1 - frr, far)
    metrics['AUC'] = auc
    
    # 6. 分数统计
    metrics['Bonafide_Mean'] = np.mean(bonafide_scores)
    metrics['Bonafide_Std'] = np.std(bonafide_scores)
    metrics['Spoof_Mean'] = np.mean(spoof_scores)
    metrics['Spoof_Std'] = np.std(spoof_scores)
    
    return metrics


def plot_results(bonafide_scores, spoof_scores, metrics, output_dir):
    """绘制评估结果图表"""
    bonafide_scores = np.array(bonafide_scores)
    spoof_scores = np.array(spoof_scores)
    
    fig = plt.figure(figsize=(16, 12))
    
    # 1. 分数分布直方图
    ax1 = plt.subplot(2, 3, 1)
    plt.hist(bonafide_scores, bins=50, alpha=0.7, label='Bonafide', density=True, color='green')
    plt.hist(spoof_scores, bins=50, alpha=0.7, label='Spoof', density=True, color='red')
    plt.axvline(metrics['EER_threshold'], color='blue', linestyle='--', label=f'EER threshold ({metrics["EER_threshold"]:.4f})')
    plt.xlabel('Score')
    plt.ylabel('Density')
    plt.title('Score Distribution')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 2. DET曲线
    ax2 = plt.subplot(2, 3, 2)
    plt.plot(metrics['FAR'] * 100, metrics['FRR'] * 100, 'b-', linewidth=2)
    eer_idx = np.argmin(np.abs(metrics['FAR'] - metrics['FRR']))
    plt.plot(metrics['FAR'][eer_idx] * 100, metrics['FRR'][eer_idx] * 100, 'ro', 
             markersize=10, label=f'EER: {metrics["EER"]:.2f}%')
    plt.xlabel('False Acceptance Rate (%)')
    plt.ylabel('False Rejection Rate (%)')
    plt.title('DET Curve')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xscale('log')
    plt.yscale('log')
    
    # 3. ROC曲线
    ax3 = plt.subplot(2, 3, 3)
    tpr = 1 - metrics['FRR']  # True Positive Rate
    fpr = metrics['FAR']  # False Positive Rate
    plt.plot(fpr * 100, tpr * 100, 'b-', linewidth=2, label=f'ROC (AUC={metrics["AUC"]:.4f})')
    plt.plot([0, 100], [0, 100], 'k--', alpha=0.5, label='Random')
    plt.xlabel('False Positive Rate (%)')
    plt.ylabel('True Positive Rate (%)')
    plt.title('ROC Curve')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 4. 箱线图
    ax4 = plt.subplot(2, 3, 4)
    data_to_plot = [bonafide_scores, spoof_scores]
    bp = plt.boxplot(data_to_plot, labels=['Bonafide', 'Spoof'], patch_artist=True)
    bp['boxes'][0].set_facecolor('green')
    bp['boxes'][1].set_facecolor('red')
    plt.ylabel('Score')
    plt.title('Score Boxplot')
    plt.grid(True, alpha=0.3)
    
    # 5. 累积分布函数
    ax5 = plt.subplot(2, 3, 5)
    sorted_bonafide = np.sort(bonafide_scores)
    sorted_spoof = np.sort(spoof_scores)
    plt.plot(sorted_bonafide, np.arange(len(sorted_bonafide)) / len(sorted_bonafide), 
             'g-', label='Bonafide CDF', linewidth=2)
    plt.plot(sorted_spoof, np.arange(len(sorted_spoof)) / len(sorted_spoof), 
             'r-', label='Spoof CDF', linewidth=2)
    plt.axvline(metrics['EER_threshold'], color='blue', linestyle='--', label='EER threshold')
    plt.xlabel('Score')
    plt.ylabel('Cumulative Probability')
    plt.title('Cumulative Distribution Function')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 6. 指标总结表
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    metrics_text = f"""
评估指标总结

EER: {metrics['EER']:.4f}%
EER阈值: {metrics['EER_threshold']:.6f}

准确率 (EER阈值): {metrics['Accuracy_at_EER']:.4f}%
最佳准确率: {metrics['Best_Accuracy']:.4f}%

精确率: {metrics['Precision']:.4f}%
召回率: {metrics['Recall']:.4f}%
F1分数: {metrics['F1_Score']:.4f}%

AUC: {metrics['AUC']:.4f}

混淆矩阵:
  TP: {metrics['TP']}
  TN: {metrics['TN']}
  FP: {metrics['FP']}
  FN: {metrics['FN']}

分数统计:
  Bonafide均值: {metrics['Bonafide_Mean']:.4f}
  Bonafide标准差: {metrics['Bonafide_Std']:.4f}
  Spoof均值: {metrics['Spoof_Mean']:.4f}
  Spoof标准差: {metrics['Spoof_Std']:.4f}
"""
    ax6.text(0.1, 0.5, metrics_text, fontsize=10, family='monospace',
             verticalalignment='center', transform=ax6.transAxes)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'evaluation_plots.png', dpi=300, bbox_inches='tight')
    print(f"图表已保存到: {output_dir / 'evaluation_plots.png'}")


def main():
    parser = argparse.ArgumentParser(description='CFAD数据集高级评估')
    parser.add_argument('--data_dir', type=str, required=True,
                        help='CFAD数据集目录路径')
    parser.add_argument('--protocol_file', type=str, default=None,
                        help='协议文件路径（可选）')
    parser.add_argument('--model_path', type=str,
                        default=str(BASE_DIR / "RawGAT-ST-antispoofing-main" / "epoch_42.pth"),
                        help='模型检查点路径')
    parser.add_argument('--model_config', type=str,
                        default=str(BASE_DIR / "RawGAT-ST-antispoofing-main" / "model_config_RawGAT_ST.yaml"),
                        help='模型配置文件路径')
    parser.add_argument('--output_dir', type=str, default='./evaluation_results',
                        help='结果输出目录')
    parser.add_argument('--batch_size', type=int, default=8,
                        help='批处理大小')
    parser.add_argument('--audio_ext', type=str, default='.wav',
                        help='音频文件扩展名')
    parser.add_argument('--version', type=str, default=None,
                        choices=['clean', 'noisy', 'codec'],
                        help='CFAD数据集版本（clean/noisy/codec），用于自动构建路径')
    parser.add_argument('--split', type=str, default=None,
                        choices=['train', 'dev', 'test_seen', 'test_unseen'],
                        help='数据集划分（train/dev/test_seen/test_unseen），用于自动构建路径')
    
    args = parser.parse_args()
    
    # 如果指定了version和split，自动构建CFAD路径
    if args.version and args.split:
        base_dir = Path(args.data_dir)
        if base_dir.name.endswith('_version'):
            data_dir = base_dir / f"{args.split}_{args.version}"
        else:
            data_dir = base_dir / f"{args.version}_version" / f"{args.split}_{args.version}"
        print(f"自动构建路径: {data_dir}")
        if not data_dir.exists():
            print(f"警告: 路径不存在，使用原始路径: {args.data_dir}")
            data_dir = Path(args.data_dir)
        args.data_dir = str(data_dir)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"使用设备: {device}")
    
    # 加载模型
    print("加载模型...")
    with open(args.model_config, 'r') as f:
        config = yaml.safe_load(f)
    
    model = RawGAT_ST(config['model'], device)
    model.load_state_dict(torch.load(args.model_path, map_location=device))
    model.to(device)
    model.eval()
    print("模型加载完成")
    
    # 加载数据集
    print("加载数据集...")
    print(f"数据目录: {args.data_dir}")
    dataset = CFADDataset(args.data_dir, args.protocol_file, args.audio_ext)
    print(f"数据集大小: {len(dataset)}")
    
    if len(dataset) == 0:
        print("错误: 未找到任何音频文件！")
        print("提示: 请检查数据目录结构，CFAD数据集应包含 real_*/fake_* 或 bonafide/spoof 目录")
        return
    
    labels = [s['label'] for s in dataset.samples]
    bonafide_count = sum(labels)
    spoof_count = len(labels) - bonafide_count
    print(f"真实语音数量: {bonafide_count}")
    print(f"伪造语音数量: {spoof_count}")
    
    if bonafide_count == 0:
        print("警告: 未找到真实语音样本！")
    if spoof_count == 0:
        print("警告: 未找到伪造语音样本！无法计算EER等指标。")
        print("提示: 请确保数据目录包含 fake_* 或 spoof 目录")
    
    # 预测
    print("开始预测...")
    scores, file_ids = predict_batch(model, dataset.samples, device, args.batch_size)
    
    # 分离分数
    bonafide_scores = [scores[i] for i in range(len(scores)) if dataset.samples[i]['label'] == 1]
    spoof_scores = [scores[i] for i in range(len(scores)) if dataset.samples[i]['label'] == 0]
    
    print(f"真实语音分数数量: {len(bonafide_scores)}")
    print(f"伪造语音分数数量: {len(spoof_scores)}")
    
    # 保存分数文件
    score_file = output_dir / "scores.txt"
    with open(score_file, 'w') as f:
        for i, sample in enumerate(dataset.samples):
            if i < len(scores):
                label_str = 'bonafide' if sample['label'] == 1 else 'spoof'
                f.write(f"{sample['file_id']} {label_str} {scores[i]:.6f}\n")
    print(f"分数文件已保存到: {score_file}")
    
    # 检查是否有足够的样本计算指标
    if len(bonafide_scores) == 0 or len(spoof_scores) == 0:
        print("\n错误: 缺少真实或伪造语音样本，无法计算评估指标！")
        print("请确保数据目录包含 both real_* 和 fake_* 目录")
        return
    
    # 计算指标
    print("计算评估指标...")
    metrics = compute_all_metrics(bonafide_scores, spoof_scores)
    
    # 保存结果
    result_file = output_dir / "evaluation_results.txt"
    with open(result_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("CFAD数据集评估结果（高级版）\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"数据集路径: {args.data_dir}\n")
        f.write(f"模型路径: {args.model_path}\n")
        f.write(f"数据集大小: {len(dataset)}\n")
        f.write(f"真实语音数量: {bonafide_count}\n")
        f.write(f"伪造语音数量: {spoof_count}\n\n")
        f.write("-" * 80 + "\n")
        f.write("评估指标:\n")
        f.write("-" * 80 + "\n")
        f.write(f"EER (等错误率): {metrics['EER']:.4f}%\n")
        f.write(f"EER阈值: {metrics['EER_threshold']:.6f}\n")
        f.write(f"EER阈值下的准确率: {metrics['Accuracy_at_EER']:.4f}%\n")
        f.write(f"最佳准确率: {metrics['Best_Accuracy']:.4f}%\n")
        f.write(f"最佳准确率阈值: {metrics['Best_Accuracy_threshold']:.6f}\n\n")
        f.write(f"精确率 (Precision): {metrics['Precision']:.4f}%\n")
        f.write(f"召回率 (Recall): {metrics['Recall']:.4f}%\n")
        f.write(f"F1分数: {metrics['F1_Score']:.4f}%\n\n")
        f.write(f"AUC: {metrics['AUC']:.4f}\n\n")
        f.write("混淆矩阵:\n")
        f.write(f"  TP (True Positive): {metrics['TP']}\n")
        f.write(f"  TN (True Negative): {metrics['TN']}\n")
        f.write(f"  FP (False Positive): {metrics['FP']}\n")
        f.write(f"  FN (False Negative): {metrics['FN']}\n\n")
        f.write("分数统计:\n")
        f.write(f"  Bonafide均值: {metrics['Bonafide_Mean']:.4f}\n")
        f.write(f"  Bonafide标准差: {metrics['Bonafide_Std']:.4f}\n")
        f.write(f"  Spoof均值: {metrics['Spoof_Mean']:.4f}\n")
        f.write(f"  Spoof标准差: {metrics['Spoof_Std']:.4f}\n")
    
    # 绘制图表
    print("生成可视化图表...")
    plot_results(bonafide_scores, spoof_scores, metrics, output_dir)
    
    # 打印结果
    print("\n" + "=" * 80)
    print("评估结果")
    print("=" * 80)
    print(f"EER (等错误率): {metrics['EER']:.4f}%")
    print(f"准确率 (EER阈值): {metrics['Accuracy_at_EER']:.4f}%")
    print(f"最佳准确率: {metrics['Best_Accuracy']:.4f}%")
    print(f"精确率: {metrics['Precision']:.4f}%")
    print(f"召回率: {metrics['Recall']:.4f}%")
    print(f"F1分数: {metrics['F1_Score']:.4f}%")
    print(f"AUC: {metrics['AUC']:.4f}")
    print("=" * 80)
    print(f"\n详细结果已保存到: {result_file}")
    print(f"分数文件已保存到: {score_file}")
    print(f"可视化图表已保存到: {output_dir / 'evaluation_plots.png'}")


if __name__ == '__main__':
    main()

