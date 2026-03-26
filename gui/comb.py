import subprocess
import argparse
import os
from pathlib import Path

# 获取脚本所在目录
BASE_DIR = Path(__file__).parent.absolute()

def run_mfa_conformer_inference(audio_path):
    mode='verify'
    checkpoint_path = str(BASE_DIR / "mfa_conformer_sv" / "epoch=17_cosine_eer=0.72.ckpt")
    inference_script = str(BASE_DIR / "mfa_conformer_sv" / "newinference.py")
    command = [
        "python", inference_script,
        "--test_audio", audio_path,
        "--checkpoint_path", checkpoint_path,
        "--mode", mode,
        # 添加其他必要的参数
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout

def run_rawgat_st_inference(audio_path):
    model_path = str(BASE_DIR / "RawGAT-ST-antispoofing-main" / "epoch_42.pth")
    inference_script = str(BASE_DIR / "RawGAT-ST-antispoofing-main" / "inference.py")
    command = [
        "python", inference_script,
        "--audio_path", audio_path,
        "--model_path", model_path,
        # 添加其他必要的参数
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout

def main():
    parser = argparse.ArgumentParser(description='Run inference on two models for a given audio file.')
    parser.add_argument('--audio_path', type=str, required=True, help='Path to the audio file to be processed.')
    args = parser.parse_args()
    
    mfa_conformer_result = run_mfa_conformer_inference(args.audio_path)
    print(mfa_conformer_result)

    rawgat_st_result = run_rawgat_st_inference(args.audio_path)
    print(rawgat_st_result)

if __name__ == "__main__":
    main()
