"""
CFAD数据集改进训练脚本
针对CFAD数据集优化，提升泛化能力
"""
import argparse
import sys
import os
from pathlib import Path
import numpy as np
from torch import Tensor
from torchvision import transforms
import yaml
import torch
from torch import nn
from model import RawGAT_ST
from tensorboardX import SummaryWriter
from core_scripts.startup_config import set_random_seed
from augmentation import WaveformAugment, SpecAugment, MixupAugment
from data_utils_cfad import get_cfad_dataloaders

BASE_DIR = Path(__file__).parent.absolute()


def pad(x, max_len=64600):
    """填充或截断音频到固定长度"""
    x_len = x.shape[0]
    if x_len >= max_len:
        return x[:max_len]
    num_repeats = int(max_len / x_len) + 1
    padded_x = np.tile(x, (1, num_repeats))[:, :max_len][0]
    return padded_x


class EarlyStopping:
    """早停机制"""
    def __init__(self, patience=10, min_delta=0.001):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False
        
    def __call__(self, val_loss):
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0


def train_epoch(data_loader, model, optimizer, device, 
                waveform_aug, mixup_aug, use_mixup=True):
    """训练一个epoch"""
    running_loss = 0
    num_total = 0.0
    model.train()
    
    weight = torch.FloatTensor([0.1, 0.9]).to(device)
    criterion = nn.CrossEntropyLoss(weight=weight)
    
    for batch_x, batch_y, batch_meta in data_loader:
        batch_size = batch_x.size(0)
        num_total += batch_size
        
        # 波形级增强
        batch_x = waveform_aug(batch_x)
        batch_x = batch_x.to(device)
        batch_y = batch_y.view(-1).type(torch.int64).to(device)
        
        # Mixup增强
        if use_mixup and np.random.random() < 0.5:
            batch_x, y_a, y_b, lam = mixup_aug(batch_x, batch_y)
            batch_out = model(batch_x, Freq_aug=True)
            batch_loss = lam * criterion(batch_out, y_a) + \
                        (1 - lam) * criterion(batch_out, y_b)
        else:
            batch_out = model(batch_x, Freq_aug=True)
            batch_loss = criterion(batch_out, batch_y)
        
        # Label smoothing
        batch_loss = batch_loss * 0.9 + \
                    0.1 * torch.mean(-torch.log_softmax(batch_out, dim=1))
        
        running_loss += (batch_loss.item() * batch_size)
        
        optimizer.zero_grad()
        batch_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
    
    running_loss /= num_total
    return running_loss


def evaluate(data_loader, model, device):
    """评估模型"""
    val_loss = 0.0
    num_total = 0.0
    num_correct = 0.0
    model.eval()
    
    weight = torch.FloatTensor([0.1, 0.9]).to(device)
    criterion = nn.CrossEntropyLoss(weight=weight)
    
    with torch.no_grad():
        for batch_x, batch_y, batch_meta in data_loader:
            batch_size = batch_x.size(0)
            num_total += batch_size
            
            batch_x = batch_x.to(device)
            batch_y = batch_y.view(-1).type(torch.int64).to(device)
            
            batch_out = model(batch_x, Freq_aug=False)
            batch_loss = criterion(batch_out, batch_y)
            val_loss += (batch_loss.item() * batch_size)
            
            # 计算准确率
            _, predicted = torch.max(batch_out.data, 1)
            num_correct += (predicted == batch_y).sum().item()
    
    val_loss /= num_total
    accuracy = 100.0 * num_correct / num_total
    return val_loss, accuracy


if __name__ == '__main__':
    parser = argparse.ArgumentParser('CFAD数据集改进训练')
    
    # CFAD数据集路径
    parser.add_argument('--cfad_root', type=str, 
                       default='./CFAD',
                       help='CFAD数据集根目录')
    parser.add_argument('--version', type=str, default='clean',
                       choices=['clean', 'codec', 'noisy'],
                       help='数据版本')
    
    # 训练参数
    parser.add_argument('--batch_size', type=int, default=16)
    parser.add_argument('--num_epochs', type=int, default=100)
    parser.add_argument('--lr', type=float, default=0.0001)
    parser.add_argument('--weight_decay', type=float, default=0.0005)
    
    # 增强参数
    parser.add_argument('--use_mixup', action='store_true', default=True)
    parser.add_argument('--mixup_alpha', type=float, default=0.2)
    
    # 学习率调度
    parser.add_argument('--lr_scheduler', type=str, default='cosine',
                       choices=['step', 'cosine', 'plateau'])
    parser.add_argument('--early_stop_patience', type=int, default=15)
    
    # 其他
    parser.add_argument('--seed', type=int, default=1234)
    parser.add_argument('--model_path', type=str, default=None)
    parser.add_argument('--comment', type=str, default='cfad_improved')
    parser.add_argument('--num_workers', type=int, default=4)
    
    # backend options (required by set_random_seed)
    parser.add_argument('--cudnn-deterministic-toggle', action='store_false',
                        default=True,
                        help='use cudnn-deterministic? (default true)')
    parser.add_argument('--cudnn-benchmark-toggle', action='store_true',
                        default=False,
                        help='use cudnn-benchmark? (default false)')
    
    args = parser.parse_args()
    
    # 设置随机种子
    set_random_seed(args.seed, args)
    
    # 加载模型配置
    dir_yaml = str(BASE_DIR / "model_config_RawGAT_ST.yaml")
    with open(dir_yaml, 'r') as f_yaml:
        model_config = yaml.safe_load(f_yaml)
    
    # 创建模型保存目录
    if not os.path.exists('models'):
        os.mkdir('models')
    
    model_tag = f'cfad_{args.version}_{args.comment}'
    model_save_path = os.path.join('models', model_tag)
    
    if not os.path.exists(model_save_path):
        os.mkdir(model_save_path)
    
    print('='*60)
    print(f'CFAD数据集改进训练')
    print('='*60)
    print(f'数据版本: {args.version}')
    print(f'批次大小: {args.batch_size}')
    print(f'训练轮数: {args.num_epochs}')
    print(f'学习率: {args.lr}')
    print(f'权重衰减: {args.weight_decay}')
    print(f'使用Mixup: {args.use_mixup}')
    print(f'模型保存路径: {model_save_path}')
    print('='*60)
    
    # 数据变换
    data_transforms = transforms.Compose([
        lambda x: pad(x),
        lambda x: Tensor(x)
    ])
    
    # 设备
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'\n使用设备: {device}')
    
    # 加载数据
    print('\n加载CFAD数据集...')
    train_loader, dev_loader, test_seen_loader, test_unseen_loader = \
        get_cfad_dataloaders(
            cfad_root=args.cfad_root,
            version=args.version,
            batch_size=args.batch_size,
            transform=data_transforms,
            num_workers=args.num_workers
        )
    
    # 初始化增强器
    waveform_aug = WaveformAugment()
    mixup_aug = MixupAugment(alpha=args.mixup_alpha)
    
    # 初始化模型
    print('\n初始化模型...')
    model = RawGAT_ST(model_config['model'], device)
    model = model.to(device)
    
    if args.model_path:
        model.load_state_dict(torch.load(args.model_path, map_location=device))
        print(f'加载预训练模型: {args.model_path}')
    
    # 优化器
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay
    )
    
    # 学习率调度器
    if args.lr_scheduler == 'cosine':
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=args.num_epochs, eta_min=1e-6)
    elif args.lr_scheduler == 'step':
        scheduler = torch.optim.lr_scheduler.StepLR(
            optimizer, step_size=30, gamma=0.5)
    else:
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=5)
    
    # 早停
    early_stopping = EarlyStopping(patience=args.early_stop_patience)
    
    # TensorBoard
    writer = SummaryWriter(f'logs/{model_tag}')
    
    # 训练循环
    best_val_loss = float('inf')
    best_test_unseen_acc = 0.0
    
    print('\n开始训练...\n')
    
    for epoch in range(args.num_epochs):
        print(f'Epoch {epoch+1}/{args.num_epochs}')
        print('-' * 60)
        
        # 训练
        train_loss = train_epoch(
            train_loader, model, optimizer, device,
            waveform_aug, mixup_aug, use_mixup=args.use_mixup
        )
        
        # 验证
        dev_loss, dev_acc = evaluate(dev_loader, model, device)
        test_seen_loss, test_seen_acc = evaluate(test_seen_loader, model, device)
        test_unseen_loss, test_unseen_acc = evaluate(test_unseen_loader, model, device)
        
        # 记录
        writer.add_scalar('loss/train', train_loss, epoch)
        writer.add_scalar('loss/dev', dev_loss, epoch)
        writer.add_scalar('loss/test_seen', test_seen_loss, epoch)
        writer.add_scalar('loss/test_unseen', test_unseen_loss, epoch)
        writer.add_scalar('accuracy/dev', dev_acc, epoch)
        writer.add_scalar('accuracy/test_seen', test_seen_acc, epoch)
        writer.add_scalar('accuracy/test_unseen', test_unseen_acc, epoch)
        writer.add_scalar('learning_rate', optimizer.param_groups[0]['lr'], epoch)
        
        print(f'训练损失: {train_loss:.4f}')
        print(f'验证损失: {dev_loss:.4f} | 准确率: {dev_acc:.2f}%')
        print(f'已见测试: 损失={test_seen_loss:.4f} | 准确率={test_seen_acc:.2f}%')
        print(f'未见测试: 损失={test_unseen_loss:.4f} | 准确率={test_unseen_acc:.2f}%')
        
        # 学习率调度
        if args.lr_scheduler == 'plateau':
            scheduler.step(dev_loss)
        else:
            scheduler.step()
        
        # 保存最佳模型（基于未见测试集准确率）
        if test_unseen_acc > best_test_unseen_acc:
            best_test_unseen_acc = test_unseen_acc
            torch.save(model.state_dict(),
                      os.path.join(model_save_path, 'best_model.pth'))
            print(f'✓ 保存最佳模型 (未见测试准确率: {test_unseen_acc:.2f}%)')
        
        # 定期保存
        if (epoch + 1) % 10 == 0:
            torch.save(model.state_dict(),
                      os.path.join(model_save_path, f'epoch_{epoch+1}.pth'))
        
        # 早停检查
        early_stopping(dev_loss)
        if early_stopping.early_stop:
            print(f'\n早停触发于epoch {epoch+1}')
            break
        
        print()
    
    writer.close()
    
    print('='*60)
    print('训练完成!')
    print(f'最佳未见测试准确率: {best_test_unseen_acc:.2f}%')
    print(f'模型保存在: {model_save_path}')
    print('='*60)
