import os
import re
import subprocess
from pathlib import Path
from typing import Tuple

from app.core.config import MFA_CHECKPOINT, MFA_INFERENCE_SCRIPT
from app.repositories.record_repo import check_embedding_exists, check_speaker_exists


def clean_speaker_name(speaker_name: str) -> str:
    cleaned = re.sub(r"[^\w\s\u4e00-\u9fff-]", "", speaker_name.strip())
    cleaned = re.sub(r"[-\s]+", "_", cleaned)
    return cleaned


def check_embedding_file_exists(embedding_name: str) -> bool:
    """检查嵌入文件是否已存在于文件系统中"""
    # 获取 MFA 推理脚本所在目录
    script_dir = Path(MFA_INFERENCE_SCRIPT).parent
    faiss_dir = script_dir / "faiss"
    embedding_file = faiss_dir / f"{embedding_name}.npy"
    return embedding_file.exists()


def register_speaker(audio_path: str, speaker_name: str) -> Tuple[str, str]:
    speaker_name_clean = clean_speaker_name(speaker_name)
    if not speaker_name_clean:
        raise ValueError("说话人名称无效，请使用字母、数字、中文或下划线")

    # 检查数据库中是否已存在该说话人
    if check_speaker_exists(speaker_name):
        raise ValueError(f"说话人名称 '{speaker_name}' 已存在，请使用其他名称")
    
    # 检查数据库中是否已存在该嵌入名称
    if check_embedding_exists(speaker_name_clean):
        raise ValueError(f"说话人标识 '{speaker_name_clean}' 已存在，请使用其他名称")
    
    # 检查文件系统中是否已存在该嵌入文件
    if check_embedding_file_exists(speaker_name_clean):
        raise ValueError(f"说话人文件 '{speaker_name_clean}' 已存在，请使用其他名称")

    command = [
        "python",
        MFA_INFERENCE_SCRIPT,
        "--test_audio",
        audio_path,
        "--checkpoint_path",
        MFA_CHECKPOINT,
        "--mode",
        "add",
        "--new_embedding_name",
        speaker_name_clean,
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
        raise RuntimeError(error_msg or "注册失败")
    return speaker_name_clean, result.stdout.strip()
