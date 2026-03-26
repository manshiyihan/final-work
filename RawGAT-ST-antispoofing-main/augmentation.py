"""
数据增强模块 - 提升模型泛化能力
"""
import torch
import numpy as np
import random


class SpecAugment:
    """频谱增强"""
    def __init__(self, freq_mask_param=14, time_mask_param=50, num_masks=2):
        self.freq_mask_param = freq_mask_param
        self.time_mask_param = time_mask_param
        self.num_masks = num_masks
    
    def __call__(self, x):
        """
        x: (batch, channels, freq, time)
        """
        if not self.training:
            return x
            
        # 频率掩码
        for _ in range(self.num_masks):
            f = np.random.uniform(0, self.freq_mask_param)
            f = int(f)
            f0 = random.randint(0, x.shape[2] - f)
            x[:, :, f0:f0+f, :] = 0
        
        # 时间掩码
        for _ in range(self.num_masks):
            t = np.random.uniform(0, self.time_mask_param)
            t = int(t)
            t0 = random.randint(0, x.shape[3] - t)
            x[:, :, :, t0:t0+t] = 0
            
        return x


class WaveformAugment:
    """波形级增强"""
    def __init__(self, noise_ratio=0.005, shift_max=0.2):
        self.noise_ratio = noise_ratio
        self.shift_max = shift_max
    
    def add_noise(self, x):
        """添加高斯噪声"""
        noise = torch.randn_like(x) * self.noise_ratio
        return x + noise
    
    def time_shift(self, x):
        """时间平移"""
        shift = int(x.shape[-1] * self.shift_max * (random.random() - 0.5))
        return torch.roll(x, shift, dims=-1)
    
    def speed_perturb(self, x, rate_range=(0.9, 1.1)):
        """速度扰动"""
        rate = random.uniform(*rate_range)
        indices = torch.linspace(0, x.shape[-1]-1, int(x.shape[-1]/rate))
        indices = indices.long().clamp(0, x.shape[-1]-1)
        return x[..., indices]
    
    def __call__(self, x):
        """随机应用增强"""
        if random.random() < 0.5:
            x = self.add_noise(x)
        if random.random() < 0.3:
            x = self.time_shift(x)
        if random.random() < 0.3:
            x = self.speed_perturb(x)
        return x


class MixupAugment:
    """Mixup数据增强"""
    def __init__(self, alpha=0.2):
        self.alpha = alpha
    
    def __call__(self, x, y):
        """
        x: 输入数据
        y: 标签
        """
        if self.alpha > 0:
            lam = np.random.beta(self.alpha, self.alpha)
        else:
            lam = 1
        
        batch_size = x.size(0)
        index = torch.randperm(batch_size).to(x.device)
        
        mixed_x = lam * x + (1 - lam) * x[index]
        y_a, y_b = y, y[index]
        
        return mixed_x, y_a, y_b, lam
