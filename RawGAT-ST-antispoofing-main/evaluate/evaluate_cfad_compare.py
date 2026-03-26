#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CFAD数据集对比评估脚本
支持同时测试已见数据集和未见数据集，并生成对比报告
"""

import argparse
import os
import sys
from pathlib import Path
import numpy as np
import torch
import yaml
from datetime import datetime
from tqdm import tqdm

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("警告: pandas未安装，将跳过CSV文件生成")

# 添加项目路径
BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR / "RawGAT-ST-antispoofing-main"))

from model import RawGAT_ST
from tDCF_python import eval_metrics as em
from evaluate_cfad import CFADDataset, load_audio_file, pad, predict_batch, compute_metrics


def evaluate_single_dataset(model, data_dir, device, batch_size, audio_ext='.wav', dataset_name=""):
    """评估单个数据集"""
    print(f"\n{'='*60}")
    print(f"评估数据集: {dataset_name}")
    print(f"数据目录: {data_dir}")
    print(f"{'='*60}")
    
    # 加载数据集
    dataset = CFADDataset(data_dir, audio_ext=audio_ext)
    print(f"数据集大小: {len(dataset)}")
    
    if len(dataset) == 0:
        print(f"警告: 数据集 {dataset_name} 为空，跳过")
        return None
    
    # 统计标签分布
    labels = [s['label'] for s in dataset.samples]
    bonafide_count = sum(labels)
    spoof_count = len(labels) - bonafide_count
    print(f"真实语音数量: {bonafide_count}")
    print(f"伪造语音数量: {spoof_count}")
    
    if bonafide_count == 0 or spoof_count == 0:
        print(f"警告: 数据集 {dataset_name} 缺少真实或伪造语音样本，无法计算指标")
        return None
    
    # 预测
    print("开始预测...")
    scores, file_ids = predict_batch(model, dataset.samples, device, batch_size)
    
    # 分离分数
    bonafide_scores = [scores[i] for i in range(len(scores)) if dataset.samples[i]['label'] == 1]
    spoof_scores = [scores[i] for i in range(len(scores)) if dataset.samples[i]['label'] == 0]
    
    print(f"真实语音分数数量: {len(bonafide_scores)}")
    print(f"伪造语音分数数量: {len(spoof_scores)}")
    
    # 计算指标
    print("计算评估指标...")
    metrics = compute_metrics(bonafide_scores, spoof_scores)
    
    # 添加数据集信息
    metrics['dataset_name'] = dataset_name
    metrics['data_dir'] = str(data_dir)
    metrics['total_samples'] = len(dataset)
    metrics['bonafide_count'] = bonafide_count
    metrics['spoof_count'] = spoof_count
    metrics['bonafide_scores'] = bonafide_scores
    metrics['spoof_scores'] = spoof_scores
    metrics['all_scores'] = scores
    metrics['all_labels'] = labels
    
    return metrics


def generate_comparison_report(results, output_dir):
    """生成对比报告"""
    output_dir = Path(output_dir)
    
    # 创建对比报告
    report_file = output_dir / "comparison_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("CFAD数据集对比评估报告\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 数据集信息
        f.write("-" * 80 + "\n")
        f.write("数据集信息\n")
        f.write("-" * 80 + "\n")
        for result in results:
            if result:
                f.write(f"\n{result['dataset_name']}:\n")
                f.write(f"  数据目录: {result['data_dir']}\n")
                f.write(f"  总样本数: {result['total_samples']}\n")
                f.write(f"  真实语音: {result['bonafide_count']}\n")
                f.write(f"  伪造语音: {result['spoof_count']}\n")
        
        # 指标对比
        f.write("\n" + "=" * 80 + "\n")
        f.write("评估指标对比\n")
        f.write("=" * 80 + "\n\n")
        
        # 创建对比表格
        f.write(f"{'指标':<25} {'已见数据集':<20} {'未见数据集':<20} {'差异':<15}\n")
        f.write("-" * 80 + "\n")
        
        if len(results) >= 2 and results[0] and results[1]:
            seen = results[0]
            unseen = results[1]
            
            # EER对比
            eer_diff = unseen['EER'] - seen['EER']
            f.write(f"{'EER (%)':<25} {seen['EER']:<20.4f} {unseen['EER']:<20.4f} {eer_diff:+.4f}\n")
            
            # 准确率对比
            acc_diff = unseen['Accuracy_at_EER'] - seen['Accuracy_at_EER']
            f.write(f"{'准确率 (EER阈值) (%)':<25} {seen['Accuracy_at_EER']:<20.4f} {unseen['Accuracy_at_EER']:<20.4f} {acc_diff:+.4f}\n")
            
            # 最佳准确率对比
            best_acc_diff = unseen['Best_Accuracy'] - seen['Best_Accuracy']
            f.write(f"{'最佳准确率 (%)':<25} {seen['Best_Accuracy']:<20.4f} {unseen['Best_Accuracy']:<20.4f} {best_acc_diff:+.4f}\n")
        
        # 详细指标
        f.write("\n" + "-" * 80 + "\n")
        f.write("详细指标\n")
        f.write("-" * 80 + "\n")
        
        for result in results:
            if result:
                f.write(f"\n{result['dataset_name']}:\n")
                f.write(f"  EER: {result['EER']:.4f}%\n")
                f.write(f"  EER阈值: {result['EER_threshold']:.6f}\n")
                f.write(f"  EER阈值下的准确率: {result['Accuracy_at_EER']:.4f}%\n")
                f.write(f"  最佳准确率: {result['Best_Accuracy']:.4f}%\n")
                f.write(f"  最佳准确率阈值: {result['Best_Accuracy_threshold']:.6f}\n")
    
    print(f"\n对比报告已保存到: {report_file}")
    
    # 保存CSV格式的对比表格
    if len(results) >= 2 and results[0] and results[1] and HAS_PANDAS:
        csv_file = output_dir / "comparison_table.csv"
        comparison_data = {
            '指标': ['EER (%)', '准确率 (EER阈值) (%)', '最佳准确率 (%)', 
                    'EER阈值', '最佳准确率阈值', '总样本数', '真实语音数', '伪造语音数'],
            '已见数据集': [
                results[0]['EER'],
                results[0]['Accuracy_at_EER'],
                results[0]['Best_Accuracy'],
                results[0]['EER_threshold'],
                results[0]['Best_Accuracy_threshold'],
                results[0]['total_samples'],
                results[0]['bonafide_count'],
                results[0]['spoof_count']
            ],
            '未见数据集': [
                results[1]['EER'],
                results[1]['Accuracy_at_EER'],
                results[1]['Best_Accuracy'],
                results[1]['EER_threshold'],
                results[1]['Best_Accuracy_threshold'],
                results[1]['total_samples'],
                results[1]['bonafide_count'],
                results[1]['spoof_count']
            ],
            '差异': [
                results[1]['EER'] - results[0]['EER'],
                results[1]['Accuracy_at_EER'] - results[0]['Accuracy_at_EER'],
                results[1]['Best_Accuracy'] - results[0]['Best_Accuracy'],
                results[1]['EER_threshold'] - results[0]['EER_threshold'],
                results[1]['Best_Accuracy_threshold'] - results[0]['Best_Accuracy_threshold'],
                results[1]['total_samples'] - results[0]['total_samples'],
                results[1]['bonafide_count'] - results[0]['bonafide_count'],
                results[1]['spoof_count'] - results[0]['spoof_count']
            ]
        }
        df = pd.DataFrame(comparison_data)
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"对比表格已保存到: {csv_file}")
    elif len(results) >= 2 and results[0] and results[1] and not HAS_PANDAS:
        # 如果没有pandas，生成简单的CSV文件
        csv_file = output_dir / "comparison_table.csv"
        with open(csv_file, 'w', encoding='utf-8-sig') as f:
            f.write("指标,已见数据集,未见数据集,差异\n")
            f.write(f"EER (%),{results[0]['EER']:.4f},{results[1]['EER']:.4f},{results[1]['EER'] - results[0]['EER']:+.4f}\n")
            f.write(f"准确率 (EER阈值) (%),{results[0]['Accuracy_at_EER']:.4f},{results[1]['Accuracy_at_EER']:.4f},{results[1]['Accuracy_at_EER'] - results[0]['Accuracy_at_EER']:+.4f}\n")
            f.write(f"最佳准确率 (%),{results[0]['Best_Accuracy']:.4f},{results[1]['Best_Accuracy']:.4f},{results[1]['Best_Accuracy'] - results[0]['Best_Accuracy']:+.4f}\n")
        print(f"对比表格已保存到: {csv_file}")


def plot_comparison(results, output_dir):
    """绘制对比图表"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
    except ImportError:
        print("警告: matplotlib未安装，跳过图表生成")
        return
    
    if len(results) < 2 or not results[0] or not results[1]:
        return
    
    seen = results[0]
    unseen = results[1]
    
    fig = plt.figure(figsize=(16, 10))
    
    # 1. EER和准确率对比柱状图
    ax1 = plt.subplot(2, 3, 1)
    metrics_names = ['EER (%)', '准确率 (EER阈值) (%)', '最佳准确率 (%)']
    seen_values = [seen['EER'], seen['Accuracy_at_EER'], seen['Best_Accuracy']]
    unseen_values = [unseen['EER'], unseen['Accuracy_at_EER'], unseen['Best_Accuracy']]
    
    x = np.arange(len(metrics_names))
    width = 0.35
    
    plt.bar(x - width/2, seen_values, width, label='已见数据集', color='skyblue')
    plt.bar(x + width/2, unseen_values, width, label='未见数据集', color='lightcoral')
    plt.xlabel('指标')
    plt.ylabel('百分比 (%)')
    plt.title('主要指标对比')
    plt.xticks(x, metrics_names, rotation=15, ha='right')
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')
    
    # 2. 分数分布对比
    ax2 = plt.subplot(2, 3, 2)
    plt.hist(seen['bonafide_scores'], bins=50, alpha=0.6, label='已见-真实', 
             density=True, color='green', histtype='step', linewidth=2)
    plt.hist(seen['spoof_scores'], bins=50, alpha=0.6, label='已见-伪造', 
             density=True, color='red', histtype='step', linewidth=2)
    plt.hist(unseen['bonafide_scores'], bins=50, alpha=0.6, label='未见-真实', 
             density=True, color='darkgreen', histtype='step', linewidth=2, linestyle='--')
    plt.hist(unseen['spoof_scores'], bins=50, alpha=0.6, label='未见-伪造', 
             density=True, color='darkred', histtype='step', linewidth=2, linestyle='--')
    plt.xlabel('分数')
    plt.ylabel('密度')
    plt.title('分数分布对比')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 3. DET曲线对比
    ax3 = plt.subplot(2, 3, 3)
    plt.plot(seen['FAR'] * 100, seen['FRR'] * 100, 'b-', linewidth=2, label=f"已见 (EER={seen['EER']:.2f}%)")
    plt.plot(unseen['FAR'] * 100, unseen['FRR'] * 100, 'r--', linewidth=2, label=f"未见 (EER={unseen['EER']:.2f}%)")
    plt.xlabel('False Acceptance Rate (%)')
    plt.ylabel('False Rejection Rate (%)')
    plt.title('DET曲线对比')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xscale('log')
    plt.yscale('log')
    
    # 4. 箱线图对比
    ax4 = plt.subplot(2, 3, 4)
    data_to_plot = [
        seen['bonafide_scores'], seen['spoof_scores'],
        unseen['bonafide_scores'], unseen['spoof_scores']
    ]
    bp = plt.boxplot(data_to_plot, labels=['已见-真实', '已见-伪造', '未见-真实', '未见-伪造'], 
                     patch_artist=True)
    colors = ['lightgreen', 'lightcoral', 'darkgreen', 'darkred']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    plt.ylabel('分数')
    plt.title('分数箱线图对比')
    plt.xticks(rotation=15, ha='right')
    plt.grid(True, alpha=0.3, axis='y')
    
    # 5. 指标差异对比
    ax5 = plt.subplot(2, 3, 5)
    differences = [
        unseen['EER'] - seen['EER'],
        unseen['Accuracy_at_EER'] - seen['Accuracy_at_EER'],
        unseen['Best_Accuracy'] - seen['Best_Accuracy']
    ]
    diff_labels = ['EER差异', '准确率差异', '最佳准确率差异']
    colors_diff = ['red' if d > 0 else 'green' for d in differences]
    plt.barh(diff_labels, differences, color=colors_diff, alpha=0.7)
    plt.xlabel('差异值')
    plt.title('指标差异 (未见 - 已见)')
    plt.axvline(0, color='black', linestyle='-', linewidth=0.8)
    plt.grid(True, alpha=0.3, axis='x')
    
    # 6. 统计信息对比表
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    stats_text = f"""
统计信息对比

已见数据集:
  样本数: {seen['total_samples']}
  真实: {seen['bonafide_count']}
  伪造: {seen['spoof_count']}
  真实均值: {np.mean(seen['bonafide_scores']):.4f}
  伪造均值: {np.mean(seen['spoof_scores']):.4f}

未见数据集:
  样本数: {unseen['total_samples']}
  真实: {unseen['bonafide_count']}
  伪造: {unseen['spoof_count']}
  真实均值: {np.mean(unseen['bonafide_scores']):.4f}
  伪造均值: {np.mean(unseen['spoof_scores']):.4f}

性能差异:
  EER: {unseen['EER'] - seen['EER']:+.4f}%
  准确率: {unseen['Accuracy_at_EER'] - seen['Accuracy_at_EER']:+.4f}%
"""
    ax6.text(0.1, 0.5, stats_text, fontsize=9, family='monospace',
             verticalalignment='center', transform=ax6.transAxes)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'comparison_plots.png', dpi=300, bbox_inches='tight')
    print(f"对比图表已保存到: {output_dir / 'comparison_plots.png'}")


def main():
    parser = argparse.ArgumentParser(description='CFAD数据集对比评估（已见 vs 未见）')
    parser.add_argument('--base_dir', type=str, required=True,
                        help='CFAD数据集基础目录路径')
    parser.add_argument('--version', type=str, default='clean',
                        choices=['clean', 'noisy', 'codec'],
                        help='CFAD数据集版本（默认: clean）')
    parser.add_argument('--model_path', type=str,
                        default=str(BASE_DIR / "RawGAT-ST-antispoofing-main" / "epoch_42.pth"),
                        help='模型检查点路径')
    parser.add_argument('--model_config', type=str,
                        default=str(BASE_DIR / "RawGAT-ST-antispoofing-main" / "model_config_RawGAT_ST.yaml"),
                        help='模型配置文件路径')
    parser.add_argument('--output_dir', type=str, default='./comparison_results',
                        help='结果输出目录')
    parser.add_argument('--batch_size', type=int, default=8,
                        help='批处理大小')
    parser.add_argument('--audio_ext', type=str, default='.wav',
                        help='音频文件扩展名')
    
    args = parser.parse_args()
    
    # 构建数据集路径
    base_dir = Path(args.base_dir)
    version_dir = base_dir / f"{args.version}_version"
    
    seen_dir = version_dir / f"test_seen_{args.version}"
    unseen_dir = version_dir / f"test_unseen_{args.version}"
    
    print("=" * 80)
    print("CFAD数据集对比评估")
    print("=" * 80)
    print(f"基础目录: {args.base_dir}")
    print(f"版本: {args.version}")
    print(f"已见数据集: {seen_dir}")
    print(f"未见数据集: {unseen_dir}")
    print("=" * 80)
    
    # 检查路径
    if not seen_dir.exists():
        print(f"错误: 已见数据集路径不存在: {seen_dir}")
        return
    if not unseen_dir.exists():
        print(f"错误: 未见数据集路径不存在: {unseen_dir}")
        return
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 为每个数据集创建子目录
    seen_output = output_dir / "test_seen"
    unseen_output = output_dir / "test_unseen"
    seen_output.mkdir(exist_ok=True)
    unseen_output.mkdir(exist_ok=True)
    
    # 设备
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"\n使用设备: {device}")
    
    # 加载模型
    print("加载模型...")
    with open(args.model_config, 'r') as f:
        config = yaml.safe_load(f)
    
    model = RawGAT_ST(config['model'], device)
    model.load_state_dict(torch.load(args.model_path, map_location=device))
    model.to(device)
    model.eval()
    print("模型加载完成")
    
    # 评估两个数据集
    results = []
    
    # 评估已见数据集
    seen_result = evaluate_single_dataset(
        model, str(seen_dir), device, args.batch_size, 
        args.audio_ext, f"test_seen_{args.version}"
    )
    if seen_result:
        # 保存已见数据集的分数文件
        score_file = seen_output / "scores.txt"
        with open(score_file, 'w') as f:
            for i, score in enumerate(seen_result['all_scores']):
                label_str = 'bonafide' if seen_result['all_labels'][i] == 1 else 'spoof'
                f.write(f"sample_{i:06d} {label_str} {score:.6f}\n")
        results.append(seen_result)
    
    # 评估未见数据集
    unseen_result = evaluate_single_dataset(
        model, str(unseen_dir), device, args.batch_size,
        args.audio_ext, f"test_unseen_{args.version}"
    )
    if unseen_result:
        # 保存未见数据集的分数文件
        score_file = unseen_output / "scores.txt"
        with open(score_file, 'w') as f:
            for i, score in enumerate(unseen_result['all_scores']):
                label_str = 'bonafide' if unseen_result['all_labels'][i] == 1 else 'spoof'
                f.write(f"sample_{i:06d} {label_str} {score:.6f}\n")
        results.append(unseen_result)
    
    # 生成对比报告
    if len(results) >= 2:
        print("\n" + "=" * 80)
        print("生成对比报告...")
        print("=" * 80)
        generate_comparison_report(results, output_dir)
        plot_comparison(results, output_dir)
        
        # 打印简要对比
        print("\n" + "=" * 80)
        print("简要对比结果")
        print("=" * 80)
        print(f"{'指标':<30} {'已见数据集':<20} {'未见数据集':<20} {'差异':<15}")
        print("-" * 80)
        print(f"{'EER (%)':<30} {results[0]['EER']:<20.4f} {results[1]['EER']:<20.4f} {results[1]['EER'] - results[0]['EER']:+.4f}")
        print(f"{'准确率 (EER阈值) (%)':<30} {results[0]['Accuracy_at_EER']:<20.4f} {results[1]['Accuracy_at_EER']:<20.4f} {results[1]['Accuracy_at_EER'] - results[0]['Accuracy_at_EER']:+.4f}")
        print(f"{'最佳准确率 (%)':<30} {results[0]['Best_Accuracy']:<20.4f} {results[1]['Best_Accuracy']:<20.4f} {results[1]['Best_Accuracy'] - results[0]['Best_Accuracy']:+.4f}")
        print("=" * 80)
    else:
        print("\n警告: 无法生成对比报告，需要至少两个有效的数据集结果")
    
    print(f"\n所有结果已保存到: {output_dir}")


if __name__ == '__main__':
    main()

