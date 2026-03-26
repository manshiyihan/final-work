"""
改进版训练脚本 - 增强泛化能力
主要改进：
1. 数据增强
2. 正则化增强
3. 学习率调度
4. 早停机制
"""
import argparse
import sys
import os
from pathlib import Path
import data_utils
import numpy as np
from torch import Tensor
from torch.utils.data import DataLoader
from torchvision import transforms
import yaml
import torch
from torch import nn
from model import RawGAT_ST
from tensorboardX import SummaryWriter
from core_scripts.startup_config import set_random_seed
from augmentation import WaveformAugment, SpecAugment, MixupAugment

BASE_DIR = Path(__file__).parent.absolute()


def pad(x, max_len=64600):
    x_len = x.shape[0]
    if x_len >= max_len:
        return x[:max_len]
    num_repeats = int(max_len / x_len)+1
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


def train_epoch_improved(data_loader, model, optimizer, device, 
                        waveform_aug, spec_aug, mixup_aug, use_mixup=True):
    """改进的训练函数"""
    running_loss = 0
    num_total = 0.0
    model.train()
    
    # 加权交叉熵
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
            batch_loss = lam * criterion(batch_out, y_a) + (1 - lam) * criterion(batch_out, y_b)
        else:
            batch_out = model(batch_x, Freq_aug=True)
            batch_loss = criterion(batch_out, batch_y)
        
        # Label smoothing效果
        batch_loss = batch_loss * 0.9 + 0.1 * torch.mean(-torch.log_softmax(batch_out, dim=1))
        
        running_loss += (batch_loss.item() * batch_size)
        
        optimizer.zero_grad()
        batch_loss.backward()
        
        # 梯度裁剪
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()
    
    running_loss /= num_total
    return running_loss


def evaluate_accuracy(data_loader, model, device):
    """评估函数"""
    val_loss = 0.0
    num_total = 0.0
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
    
    val_loss /= num_total
    return val_loss


if __name__ == '__main__':
    parser = argparse.ArgumentParser('改进的RawGAT-ST训练')
    
    # 数据集路径
    parser.add_argument('--database_path', type=str, 
                       default='/home/xujiwu/下载/LA')
    parser.add_argument('--protocols_path', type=str, 
                       default='/home/xujiwu/下载/RawGAT-ST-antispoofing-main/database')
    
    # 超参数
    parser.add_argument('--batch_size', type=int, default=10)
    parser.add_argument('--num_epochs', type=int, default=300)
    parser.add_argument('--lr', type=float, default=0.0001)
    parser.add_argument('--weight_decay', type=float, default=0.0005)  # 增加权重衰减
    parser.add_argument('--dropout', type=float, default=0.3)  # dropout率
    
    # 增强参数
    parser.add_argument('--use_mixup', action='store_true', default=True)
    parser.add_argument('--mixup_alpha', type=float, default=0.2)
    
    # 学习率调度
    parser.add_argument('--lr_scheduler', type=str, default='cosine', 
                       choices=['step', 'cosine', 'plateau'])
    
    # 早停
    parser.add_argument('--early_stop_patience', type=int, default=15)
    
    parser.add_argument('--seed', type=int, default=1234)
    parser.add_argument('--model_path', type=str, default=None)
    parser.add_argument('--comment', type=str, default='improved')
    parser.add_argument('--track', type=str, default='logical')
    parser.add_argument('--features', type=str, default='Raw_GAT')
    
    args = parser.parse_args()
    
    # 设置随机种子
    set_random_seed(args.seed, args)
    
    # 配置文件
    dir_yaml = str(BASE_DIR / "model_config_RawGAT_ST.yaml")
    with open(dir_yaml, 'r') as f_yaml:
        parser1 = yaml.safe_load(f_yaml)
    
    if not os.path.exists('models'):
        os.mkdir('models')
    
    # 模型保存路径
    model_tag = 'model_improved_{}_{}_{}'.format(
        args.track, args.num_epochs, args.batch_size)
    if args.comment:
        model_tag = model_tag + '_{}'.format(args.comment)
    model_save_path = os.path.join('models', model_tag)
    
    if not os.path.exists(model_save_path):
        os.mkdir(model_save_path)
    
    # 数据变换
    data_transforms = transforms.Compose([
        lambda x: pad(x),
        lambda x: Tensor(x)
    ])
    
    # 设备
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print('设备: {}'.format(device))
    
    # 数据加载
    is_logical = (args.track == 'logical')
    
    train_set = data_utils.ASVDataset(
        database_path=args.database_path,
        protocols_path=args.protocols_path,
        is_train=True, 
        is_logical=is_logical, 
        transform=data_transforms,
        feature_name=args.features
    )
    train_loader = DataLoader(train_set, batch_size=args.batch_size, 
                             shuffle=True, num_workers=4)
    
    dev_set = data_utils.ASVDataset(
        database_path=args.database_path,
        protocols_path=args.protocols_path,
        is_train=False, 
        is_logical=is_logical,
        transform=data_transforms,
        feature_name=args.features, 
        is_eval=False, 
        eval_part=0
    )
    dev_loader = DataLoader(dev_set, batch_size=args.batch_size, shuffle=False)
    
    # 初始化增强器
    waveform_aug = WaveformAugment()
    spec_aug = SpecAugment()
    mixup_aug = MixupAugment(alpha=args.mixup_alpha)
    
    # 模型
    model = RawGAT_ST(parser1['model'], device)
    model = model.to(device)
    
    if args.model_path:
        model.load_state_dict(torch.load(args.model_path, map_location=device))
        print('加载模型: {}'.format(args.model_path))
    
    # 优化器
    optimizer = torch.optim.AdamW(model.parameters(), 
                                  lr=args.lr, 
                                  weight_decay=args.weight_decay)
    
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
    writer = SummaryWriter('logs/{}'.format(model_tag))
    
    # 训练循环
    best_val_loss = float('inf')
    
    for epoch in range(args.num_epochs):
        print(f'\n===== Epoch {epoch+1}/{args.num_epochs} =====')
        
        # 训练
        train_loss = train_epoch_improved(
            train_loader, model, optimizer, device,
            waveform_aug, spec_aug, mixup_aug, 
            use_mixup=args.use_mixup
        )
        
        # 验证
        val_loss = evaluate_accuracy(dev_loader, model, device)
        
        # 记录
        writer.add_scalar('train_loss', train_loss, epoch)
        writer.add_scalar('val_loss', val_loss, epoch)
        writer.add_scalar('learning_rate', optimizer.param_groups[0]['lr'], epoch)
        
        print(f'训练损失: {train_loss:.4f} | 验证损失: {val_loss:.4f}')
        
        # 学习率调度
        if args.lr_scheduler == 'plateau':
            scheduler.step(val_loss)
        else:
            scheduler.step()
        
        # 保存最佳模型
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), 
                      os.path.join(model_save_path, 'best_model.pth'))
            print(f'保存最佳模型 (验证损失: {val_loss:.4f})')
        
        # 定期保存
        if (epoch + 1) % 10 == 0:
            torch.save(model.state_dict(), 
                      os.path.join(model_save_path, f'epoch_{epoch+1}.pth'))
        
        # 早停检查
        early_stopping(val_loss)
        if early_stopping.early_stop:
            print(f'\n早停触发于epoch {epoch+1}')
            break
    
    writer.close()
    print('\n训练完成!')
