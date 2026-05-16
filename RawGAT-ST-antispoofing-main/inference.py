import argparse
import json
import os
from pathlib import Path
import soundfile as sf
import torch
import yaml
from torch import nn
from model import RawGAT_ST
import numpy as np

# 获取脚本所在目录
BASE_DIR = Path(__file__).parent.absolute()

def pad(x, max_len=64600):
    x_len = x.shape[0]
    if x_len >= max_len:
        return x[:max_len]  # 如果音频长度超过 max_len，则截断

    # 如果音频长度不足 max_len，则进行重复填充
    num_repeats = int(max_len / x_len) + 1
    padded_x = np.tile(x, (1, num_repeats))[:, :max_len][0]
    return padded_x


def load_audio_file(file_path, max_len=64600):
    # 加载音频文件
    audio_data, sample_rate = sf.read(file_path)
    
    # 如果是多声道（立体声），转换为单声道
    if audio_data.ndim > 1:
        # 使用平均值转换为单声道
        audio_data = np.mean(audio_data, axis=-1)
    
    # 确保是1D数组
    audio_data = audio_data.flatten()
    
    # 如果采样率不是16kHz，需要重采样
    if sample_rate != 16000:
        try:
            import librosa
            audio_data = librosa.resample(audio_data.astype(np.float32), orig_sr=sample_rate, target_sr=16000)
        except ImportError:
            raise ImportError("librosa is required for audio resampling. Please install it with: pip install librosa")
    
    # 填充或截断到指定长度
    audio_data = pad(audio_data, max_len=max_len)
    return audio_data


def predict_audio(file_path, model, device):
    # 加载音频文件
    audio_data = load_audio_file(file_path)

    # 将音频数据转换为 PyTorch 张量，并添加通道维度和批量维度
    audio_tensor = torch.Tensor(audio_data).unsqueeze(0)
    audio_tensor = audio_tensor.to(device)

    # 设置模型为评估模式
    model.eval()

    # 获取模型的输出
    with torch.no_grad():
        output = model(audio_tensor, Freq_aug=False)

    # 获取预测结果
    _, predicted = torch.max(output, 1)
    return predicted.item()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ASVSpoof2019 RawGAT-ST 模型单个音频预测')
    parser.add_argument('--audio_path', type=str, required=True, help='待预测音频文件路径')
    parser.add_argument('--model_path', type=str, default=str(BASE_DIR / "epoch_42.pth"), help='模型检查点路径')
    parser.add_argument('--model_config', type=str, default=str(BASE_DIR / "model_config_RawGAT_ST.yaml"), help='模型配置文件路径')
    parser.add_argument('--json_output', action='store_true', help='输出JSON格式结果')

    # 解析命令行参数
    args = parser.parse_args()

    # 确定使用 CPU 还是 GPU
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
   
    # 加载模型配置
    with open(args.model_config, 'r') as f_yaml:
        config = yaml.safe_load(f_yaml)

    # 初始化模型
    model = RawGAT_ST(config['model'], device)

    # 加载模型权重
    model.load_state_dict(torch.load(args.model_path, map_location=device))
    model.to(device)

    # 对音频文件进行预测
    prediction = predict_audio(args.audio_path, model, device)

    # 输出预测结果
    if args.json_output:
        print(
            json.dumps(
                {
                    "ok": True,
                    "label": "bonafide" if prediction == 1 else "spoof",
                    "label_zh": "真实" if prediction == 1 else "虚假",
                    "prediction": int(prediction),
                },
                ensure_ascii=False,
            )
        )
    print("判断结果:", "真实" if prediction == 1 else "虚假")
