#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CFAD数据集评估脚本
用于测试抗伪造语音模型在CFAD数据集上的各种指标
"""

import argparse
import os
import sys
from pathlib import Path
import numpy as np
import torch
import yaml
import soundfile as sf
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

# 添加项目路径
BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR / "RawGAT-ST-antispoofing-main"))

from model import RawGAT_ST
from tDCF_python import eval_metrics as em


class CFADDataset(Dataset):
    """CFAD数据集加载器 - 支持CFAD数据集的标准结构"""
    def __init__(self, data_dir, protocol_file=None, audio_ext='.wav'):
        """
        Args:
            data_dir: CFAD数据集目录路径
                     支持以下结构:
                     - data_dir/real_*/ 和 data_dir/fake_*/ (CFAD标准结构)
                     - data_dir/bonafide/ 和 data_dir/spoof/ (通用结构)
                     - 协议文件格式
            protocol_file: 协议文件路径（可选）
            audio_ext: 音频文件扩展名
        """
        self.data_dir = Path(data_dir)
        self.audio_ext = audio_ext
        self.samples = []
        
        if protocol_file and os.path.exists(protocol_file):
            # 从协议文件加载
            self._load_from_protocol(protocol_file)
        else:
            # 从CFAD目录结构加载
            self._load_from_cfad_structure()
    
    def _load_from_protocol(self, protocol_file):
        """从协议文件加载数据"""
        with open(protocol_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    # 格式可能是: label file_path 或 file_path label
                    if len(parts) == 2:
                        if parts[0] in ['bonafide', 'spoof', 'real', 'fake', '0', '1']:
                            label = 1 if parts[0] in ['bonafide', 'real', '1'] else 0
                            file_path = parts[1]
                        else:
                            file_path = parts[0]
                            label = 1 if parts[1] in ['bonafide', 'real', '1'] else 0
                    else:
                        file_path = parts[0]
                        label = 1 if parts[-1] in ['bonafide', 'real', '1'] else 0
                    
                    audio_path = self.data_dir / file_path
                    if not audio_path.exists():
                        audio_path = self.data_dir / (file_path + self.audio_ext)
                    
                    if audio_path.exists():
                        self.samples.append({
                            'path': str(audio_path),
                            'label': label,
                            'file_id': Path(file_path).stem
                        })
    
    def _load_from_cfad_structure(self):
        """从CFAD数据集标准结构加载数据"""
        # CFAD数据集结构: data_dir/real_*/ 和 data_dir/fake_*/
        # 或者: data_dir/bonafide/ 和 data_dir/spoof/
        
        # 查找real目录（支持多种命名）
        real_dirs = []
        fake_dirs = []
        
        # 检查CFAD标准结构: real_clean, real_codec, real_noise等
        for subdir in self.data_dir.iterdir():
            if subdir.is_dir():
                dir_name_lower = subdir.name.lower()
                if dir_name_lower.startswith('real_') or dir_name_lower == 'real' or dir_name_lower == 'bonafide':
                    real_dirs.append(subdir)
                elif dir_name_lower.startswith('fake_') or dir_name_lower == 'fake' or dir_name_lower == 'spoof':
                    fake_dirs.append(subdir)
        
        # 如果没找到，尝试在子目录中查找
        if not real_dirs and not fake_dirs:
            for subdir in self.data_dir.iterdir():
                if subdir.is_dir():
                    # 递归查找real和fake目录
                    for subsubdir in subdir.rglob('*'):
                        if subsubdir.is_dir():
                            dir_name_lower = subsubdir.name.lower()
                            if dir_name_lower.startswith('real_') or dir_name_lower == 'real' or dir_name_lower == 'bonafide':
                                real_dirs.append(subsubdir)
                            elif dir_name_lower.startswith('fake_') or dir_name_lower == 'fake' or dir_name_lower == 'spoof':
                                fake_dirs.append(subsubdir)
        
        # 加载真实语音
        for real_dir in real_dirs:
            for audio_file in real_dir.rglob(f'*{self.audio_ext}'):
                self.samples.append({
                    'path': str(audio_file),
                    'label': 1,  # bonafide/real
                    'file_id': audio_file.stem
                })
        
        # 加载伪造语音
        for fake_dir in fake_dirs:
            for audio_file in fake_dir.rglob(f'*{self.audio_ext}'):
                self.samples.append({
                    'path': str(audio_file),
                    'label': 0,  # spoof/fake
                    'file_id': audio_file.stem
                })
        
        # 如果仍然没找到，尝试从文件名或路径判断
        if not self.samples:
            for audio_file in self.data_dir.rglob(f'*{self.audio_ext}'):
                # 从路径判断标签
                path_str = str(audio_file).lower()
                if 'fake' in path_str or 'spoof' in path_str:
                    label = 0
                elif 'real' in path_str or 'bonafide' in path_str:
                    label = 1
                else:
                    # 默认跳过，避免误分类
                    continue
                
                self.samples.append({
                    'path': str(audio_file),
                    'label': label,
                    'file_id': audio_file.stem
                })
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        return self.samples[idx]


def pad(x, max_len=64600):
    """填充或截断音频到指定长度"""
    x_len = x.shape[0]
    if x_len >= max_len:
        return x[:max_len]
    
    num_repeats = int(max_len / x_len) + 1
    padded_x = np.tile(x, num_repeats)[:max_len]
    return padded_x


def load_audio_file(file_path, max_len=64600):
    """加载音频文件并处理"""
    audio_data, sample_rate = sf.read(file_path)
    
    # 转换为单声道
    if audio_data.ndim > 1:
        audio_data = np.mean(audio_data, axis=-1)
    
    audio_data = audio_data.flatten()
    
    # 重采样到16kHz
    if sample_rate != 16000:
        try:
            import librosa
            audio_data = librosa.resample(audio_data.astype(np.float32), 
                                        orig_sr=sample_rate, target_sr=16000)
        except ImportError:
            raise ImportError("librosa is required for audio resampling. Install with: pip install librosa")
    
    # 填充或截断
    audio_data = pad(audio_data, max_len=max_len)
    return audio_data


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
            
            # 转换为tensor
            # 模型期望输入形状: [batch_size, sequence_length]
            batch_audio_array = np.array(batch_audio)
            audio_tensor = torch.FloatTensor(batch_audio_array).to(device)
            
            # 预测
            output = model(audio_tensor, Freq_aug=False)
            # 使用bonafide类别的分数（索引1）
            batch_scores = output[:, 1].cpu().numpy()
            
            scores.extend(batch_scores)
            file_ids.extend(batch_ids)
    
    return scores, file_ids


def compute_metrics(bonafide_scores, spoof_scores):
    """计算各种评估指标"""
    metrics = {}
    
    # EER (Equal Error Rate)
    eer, threshold = em.compute_eer(
        np.array(bonafide_scores), 
        np.array(spoof_scores)
    )
    metrics['EER'] = eer * 100  # 转换为百分比
    metrics['EER_threshold'] = threshold
    
    # DET曲线
    frr, far, thresholds = em.compute_det_curve(
        np.array(bonafide_scores),
        np.array(spoof_scores)
    )
    metrics['FRR'] = frr
    metrics['FAR'] = far
    metrics['thresholds'] = thresholds
    
    # 计算不同阈值下的准确率
    all_scores = np.concatenate([bonafide_scores, spoof_scores])
    all_labels = np.concatenate([np.ones(len(bonafide_scores)), np.zeros(len(spoof_scores))])
    
    # 在EER阈值下的准确率
    predictions = (all_scores >= threshold).astype(int)
    accuracy = np.mean(predictions == all_labels)
    metrics['Accuracy_at_EER'] = accuracy * 100
    
    # 计算不同阈值下的指标
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
    
    return metrics


def main():
    parser = argparse.ArgumentParser(description='在CFAD数据集上评估抗伪造语音模型')
    parser.add_argument('--data_dir', type=str, required=True,
                        help='CFAD数据集目录路径')
    parser.add_argument('--protocol_file', type=str, default=None,
                        help='协议文件路径（可选，如果不提供则从目录结构推断）')
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
        # CFAD结构: base_dir/{version}_version/{split}_{version}/
        if base_dir.name.endswith('_version'):
            data_dir = base_dir / f"{args.split}_{args.version}"
        else:
            data_dir = base_dir / f"{args.version}_version" / f"{args.split}_{args.version}"
        print(f"自动构建路径: {data_dir}")
        if not data_dir.exists():
            print(f"警告: 路径不存在，使用原始路径: {args.data_dir}")
            data_dir = Path(args.data_dir)
        args.data_dir = str(data_dir)
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 设备
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
    
    # 统计标签分布
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
    
    # 分离真实和伪造的分数
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
    metrics = compute_metrics(bonafide_scores, spoof_scores)
    
    # 保存结果
    result_file = output_dir / "evaluation_results.txt"
    with open(result_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("CFAD数据集评估结果\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"数据集路径: {args.data_dir}\n")
        f.write(f"模型路径: {args.model_path}\n")
        f.write(f"数据集大小: {len(dataset)}\n")
        f.write(f"真实语音数量: {bonafide_count}\n")
        f.write(f"伪造语音数量: {spoof_count}\n\n")
        f.write("-" * 60 + "\n")
        f.write("评估指标:\n")
        f.write("-" * 60 + "\n")
        f.write(f"EER (等错误率): {metrics['EER']:.4f}%\n")
        f.write(f"EER阈值: {metrics['EER_threshold']:.6f}\n")
        f.write(f"EER阈值下的准确率: {metrics['Accuracy_at_EER']:.4f}%\n")
        f.write(f"最佳准确率: {metrics['Best_Accuracy']:.4f}%\n")
        f.write(f"最佳准确率阈值: {metrics['Best_Accuracy_threshold']:.6f}\n")
    
    # 打印结果
    print("\n" + "=" * 60)
    print("评估结果")
    print("=" * 60)
    print(f"EER (等错误率): {metrics['EER']:.4f}%")
    print(f"EER阈值: {metrics['EER_threshold']:.6f}")
    print(f"EER阈值下的准确率: {metrics['Accuracy_at_EER']:.4f}%")
    print(f"最佳准确率: {metrics['Best_Accuracy']:.4f}%")
    print(f"最佳准确率阈值: {metrics['Best_Accuracy_threshold']:.6f}")
    print("=" * 60)
    print(f"\n详细结果已保存到: {result_file}")
    print(f"分数文件已保存到: {score_file}")


if __name__ == '__main__':
    main()

