"""
改进的RawGAT-ST模型 - 增强泛化能力
主要改进：
1. 增加Dropout层
2. 添加BatchNorm
3. 使用更强的正则化
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from model import CONV, GraphAttentionLayer, Pool, Residual_block


class ImprovedRawGAT_ST(nn.Module):
    """改进版RawGAT-ST，增强泛化能力"""
    def __init__(self, d_args, device, dropout_rate=0.3):
        super(ImprovedRawGAT_ST, self).__init__()
        self.device = device
        self.dropout_rate = dropout_rate
        
        # Sinc卷积层
        self.conv_time = CONV(
            device=self.device,
            out_channels=d_args['out_channels'],
            kernel_size=d_args['first_conv'],
            in_channels=d_args['in_channels']
        )
        
        self.first_bn = nn.BatchNorm2d(num_features=1)
        self.selu = nn.SELU(inplace=True)
        
        # 编码器
        self.encoder1 = nn.Sequential(
            nn.Sequential(Residual_block(nb_filts=d_args['filts'][1], first=True)),
            nn.Dropout2d(p=dropout_rate * 0.5),  # 轻度dropout
            nn.Sequential(Residual_block(nb_filts=d_args['filts'][1])),
            nn.Sequential(Residual_block(nb_filts=d_args['filts'][2])),
            nn.Dropout2d(p=dropout_rate * 0.5),
            nn.Sequential(Residual_block(nb_filts=d_args['filts'][3])),
            nn.Sequential(Residual_block(nb_filts=d_args['filts'][3])),
            nn.Sequential(Residual_block(nb_filts=d_args['filts'][3]))
        )
        
        self.encoder2 = nn.Sequential(
            nn.Sequential(Residual_block(nb_filts=d_args['filts'][1], first=True)),
            nn.Dropout2d(p=dropout_rate * 0.5),
            nn.Sequential(Residual_block(nb_filts=d_args['filts'][1])),
            nn.Sequential(Residual_block(nb_filts=d_args['filts'][2])),
            nn.Dropout2d(p=dropout_rate * 0.5),
            nn.Sequential(Residual_block(nb_filts=d_args['filts'][3])),
            nn.Sequential(Residual_block(nb_filts=d_args['filts'][3])),
            nn.Sequential(Residual_block(nb_filts=d_args['filts'][3]))
        )
        
        # GAT层 - 增加dropout
        self.GAT_layer1 = GraphAttentionLayer(d_args['filts'][-1][-1], 32)
        self.pool1 = Pool(0.64, 32, dropout_rate)
        
        self.GAT_layer2 = GraphAttentionLayer(d_args['filts'][-1][-1], 32)
        self.pool2 = Pool(0.81, 32, dropout_rate)
        
        self.GAT_layer3 = GraphAttentionLayer(32, 16)
        self.pool3 = Pool(0.64, 16, dropout_rate)
        
        # 投影层
        self.proj1 = nn.Linear(14, 12)
        self.proj2 = nn.Linear(23, 12)
        self.proj = nn.Linear(16, 1)
        
        # 分类器 - 添加dropout
        self.dropout_final = nn.Dropout(p=dropout_rate)
        self.proj_node = nn.Linear(7, 2)
        
        # 权重初始化
        self._init_weights()
    
    def _init_weights(self):
        """改进的权重初始化"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x, Freq_aug=False):
        """前向传播"""
        nb_samp = x.shape[0]
        len_seq = x.shape[1]
        x = x.view(nb_samp, 1, len_seq)
        
        # Sinc卷积 + 频率掩码
        if Freq_aug:
            x = self.conv_time(x, mask=True)
        else:
            x = self.conv_time(x, mask=False)
        
        x = x.unsqueeze(dim=1)
        x = F.max_pool2d(torch.abs(x), (3, 3))
        x = self.first_bn(x)
        x = self.selu(x)
        
        # 频谱分支
        e1 = self.encoder1(x)
        x_max, _ = torch.max(torch.abs(e1), dim=3)
        x_gat1 = self.GAT_layer1(x_max.transpose(1, 2))
        x_pool1 = self.pool1(x_gat1)
        out1 = self.proj1(x_pool1.transpose(1, 3))
        out1 = out1.view(out1.shape[0], out1.shape[1], out1.shape[3])
        
        # 时间分支
        e2 = self.encoder2(x)
        x_max2, _ = torch.max(torch.abs(e2), dim=2)
        x_gat2 = self.GAT_layer2(x_max2.transpose(1, 2))
        x_pool2 = self.pool2(x_gat2)
        out2 = self.proj2(x_pool2.transpose(1, 3))
        out2 = out2.view(out2.shape[0], out2.shape[1], out2.shape[3])
        
        # 融合
        out_gat = torch.mul(out1, out2)
        
        # 时频融合GAT
        x_gat3 = self.GAT_layer3(out_gat.transpose(1, 2))
        x_pool3 = self.pool3(x_gat3)
        
        out_proj = self.proj(x_pool3).flatten(1)
        
        # 最终分类 - 添加dropout
        out_proj = self.dropout_final(out_proj)
        output = self.proj_node(out_proj)
        
        return output
