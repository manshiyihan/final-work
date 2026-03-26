"""
CFAD数据集加载器
支持clean_version, codec_version, noisy_version
"""
import torch
import os
import soundfile as sf
from torch.utils.data import Dataset
import numpy as np
from pathlib import Path
from joblib import Parallel, delayed


class CFADDataset(Dataset):
    """CFAD数据集加载器"""
    def __init__(self, 
                 cfad_root,
                 version='clean',  # 'clean', 'codec', 'noisy'
                 split='train',    # 'train', 'dev', 'test_seen', 'test_unseen'
                 transform=None,
                 sample_size=None):
        """
        Args:
            cfad_root: CFAD数据集根目录
            version: 数据版本 (clean/codec/noisy)
            split: 数据集划分
            transform: 数据变换
            sample_size: 采样数量（用于快速测试）
        """
        self.cfad_root = Path(cfad_root)
        self.version = version
        self.split = split
        self.transform = transform
        
        # 构建数据路径
        version_map = {
            'clean': 'clean_version',
            'codec': 'codec_version', 
            'noisy': 'noisy_version'
        }
        
        split_map = {
            'train': f'train_{version}',
            'dev': f'dev_{version}' if version != 'clean' else 'dev_clean',
            'test_seen': f'test_seen_{version}' if version != 'clean' else 'test_seen_clean',
            'test_unseen': f'test_unseen_{version}' if version != 'clean' else 'test_unseen_clean'
        }
        
        self.data_dir = self.cfad_root / version_map[version] / split_map[split]
        
        if not self.data_dir.exists():
            raise ValueError(f"数据目录不存在: {self.data_dir}")
        
        print(f'加载CFAD数据集: {self.data_dir}')
        
        # 缓存文件名
        self.cache_fname = f'cache_cfad_{version}_{split}.pth'
        
        # 加载或创建数据列表
        if os.path.exists(self.cache_fname):
            print(f'从缓存加载: {self.cache_fname}')
            cache_data = torch.load(self.cache_fname)
            self.data_x = cache_data['data_x']
            self.data_y = cache_data['data_y']
            self.files_meta = cache_data['files_meta']
        else:
            print('扫描数据文件...')
            self.files_meta = self._scan_files()
            print(f'找到 {len(self.files_meta)} 个文件')
            
            print('加载音频数据...')
            data = list(map(self._read_file, self.files_meta))
            self.data_x, self.data_y = map(list, zip(*data))
            
            if self.transform:
                print('应用数据变换...')
                self.data_x = Parallel(n_jobs=4, prefer='threads')(
                    delayed(self.transform)(x) for x in self.data_x
                )
            
            # 保存缓存
            print(f'保存缓存: {self.cache_fname}')
            torch.save({
                'data_x': self.data_x,
                'data_y': self.data_y,
                'files_meta': self.files_meta
            }, self.cache_fname)
        
        # 采样（用于快速测试）
        if sample_size and sample_size < len(self.files_meta):
            print(f'采样 {sample_size} 个样本用于测试')
            select_idx = np.random.choice(
                len(self.files_meta), 
                size=(sample_size,), 
                replace=False
            ).astype(np.int32)
            self.files_meta = [self.files_meta[x] for x in select_idx]
            self.data_x = [self.data_x[x] for x in select_idx]
            self.data_y = [self.data_y[x] for x in select_idx]
        
        self.length = len(self.data_x)
        
        # 统计信息
        num_real = sum(self.data_y)
        num_fake = self.length - num_real
        print(f'数据集统计: 总数={self.length}, 真实={num_real}, 伪造={num_fake}')
    
    def _scan_files(self):
        """扫描所有音频文件"""
        files_meta = []
        
        # 真实语音
        real_dir = self.data_dir / 'real_clean' if 'clean' in str(self.data_dir) else \
                   self.data_dir / 'real_codec' if 'codec' in str(self.data_dir) else \
                   self.data_dir / 'real_noise'
        
        if real_dir.exists():
            for audio_file in real_dir.rglob('*.wav'):
                files_meta.append({
                    'path': str(audio_file),
                    'label': 1,  # 真实语音
                    'type': 'real',
                    'source': audio_file.parent.name
                })
        
        # 伪造语音
        fake_dir = self.data_dir / 'fake_clean' if 'clean' in str(self.data_dir) else \
                   self.data_dir / 'fake_codec' if 'codec' in str(self.data_dir) else \
                   self.data_dir / 'fake_noise'
        
        if fake_dir.exists():
            for audio_file in fake_dir.rglob('*.wav'):
                files_meta.append({
                    'path': str(audio_file),
                    'label': 0,  # 伪造语音
                    'type': 'fake',
                    'source': audio_file.parent.name
                })
        
        return files_meta
    
    def _read_file(self, meta):
        """读取音频文件"""
        try:
            data_x, sample_rate = sf.read(meta['path'])
            # 确保是单声道
            if len(data_x.shape) > 1:
                data_x = data_x[:, 0]
            return data_x, float(meta['label'])
        except Exception as e:
            print(f"读取文件失败 {meta['path']}: {e}")
            # 返回静音
            return np.zeros(16000), float(meta['label'])
    
    def __len__(self):
        return self.length
    
    def __getitem__(self, idx):
        x = self.data_x[idx]
        y = self.data_y[idx]
        meta = self.files_meta[idx]
        return x, y, meta


def get_cfad_dataloaders(cfad_root, 
                         version='clean',
                         batch_size=10,
                         transform=None,
                         num_workers=4):
    """
    获取CFAD数据加载器
    
    Returns:
        train_loader, dev_loader, test_seen_loader, test_unseen_loader
    """
    train_set = CFADDataset(
        cfad_root=cfad_root,
        version=version,
        split='train',
        transform=transform
    )
    
    dev_set = CFADDataset(
        cfad_root=cfad_root,
        version=version,
        split='dev',
        transform=transform
    )
    
    test_seen_set = CFADDataset(
        cfad_root=cfad_root,
        version=version,
        split='test_seen',
        transform=transform
    )
    
    test_unseen_set = CFADDataset(
        cfad_root=cfad_root,
        version=version,
        split='test_unseen',
        transform=transform
    )
    
    train_loader = torch.utils.data.DataLoader(
        train_set, 
        batch_size=batch_size, 
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True
    )
    
    dev_loader = torch.utils.data.DataLoader(
        dev_set,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )
    
    test_seen_loader = torch.utils.data.DataLoader(
        test_seen_set,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )
    
    test_unseen_loader = torch.utils.data.DataLoader(
        test_unseen_set,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )
    
    return train_loader, dev_loader, test_seen_loader, test_unseen_loader
