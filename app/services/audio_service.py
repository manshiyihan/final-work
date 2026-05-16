import hashlib
import os
import tempfile
from pathlib import Path
from typing import Tuple

import librosa
import numpy as np
import soundfile as sf

from app.core.config import UPLOAD_DIR


# 支持的音频格式
SUPPORTED_AUDIO_EXTENSIONS = {'.wav', '.mp3', '.flac', '.ogg', '.opus', '.aac', '.m4a', '.webm', '.wma'}
SUPPORTED_AUDIO_MIMETYPES = {
    'audio/wav', 'audio/x-wav', 'audio/wave',
    'audio/mpeg', 'audio/mp3',
    'audio/flac', 'audio/x-flac',
    'audio/ogg', 'audio/opus',
    'audio/aac', 'audio/m4a', 'audio/x-m4a',
    'audio/webm', 'audio/x-ms-wma'
}


def validate_audio_file(filename: str, content_type: str = None) -> Tuple[bool, str]:
    """
    验证文件是否为支持的音频格式
    
    Args:
        filename: 文件名
        content_type: MIME类型（可选）
    
    Returns:
        (is_valid, error_message)
    """
    # 检查文件扩展名
    file_ext = Path(filename).suffix.lower()
    
    if file_ext not in SUPPORTED_AUDIO_EXTENSIONS:
        supported_formats = ', '.join(sorted(SUPPORTED_AUDIO_EXTENSIONS))
        return False, f"不支持的文件格式 '{file_ext}'。支持的格式: {supported_formats}"
    
    # 如果提供了MIME类型，也进行验证
    if content_type and content_type not in SUPPORTED_AUDIO_MIMETYPES:
        # 某些浏览器可能不提供正确的MIME类型，所以这里只是警告而不是拒绝
        pass
    
    return True, ""


def convert_audio_to_16khz_mono(input_path: str, output_path: str) -> Tuple[bool, str]:
    try:
        audio_data, _ = librosa.load(input_path, sr=16000, mono=True)
        audio_data = audio_data.astype(np.float32)
        sf.write(output_path, audio_data, 16000, subtype="PCM_16")
        return True, ""
    except Exception as exc:  # pragma: no cover
        return False, str(exc)


def ensure_16k_audio(input_path: str) -> Tuple[str, str]:
    temp_audio_path = None
    try:
        audio_data, sr = sf.read(input_path)
        need_convert = sr != 16000 or getattr(audio_data, "ndim", 1) > 1
    except Exception:
        need_convert = True

    if need_convert:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            temp_audio_path = tmp_file.name
        success, error_msg = convert_audio_to_16khz_mono(input_path, temp_audio_path)
        if not success:
            raise RuntimeError(f"音频格式转换失败: {error_msg}")
        return temp_audio_path, temp_audio_path

    return input_path, ""


def save_upload_file(filename: str, content: bytes) -> str:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    target = UPLOAD_DIR / filename
    with open(target, "wb") as file:
        file.write(content)
    return str(target)


def file_sha256(path: str) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def cleanup_file(path: str) -> None:
    if path and os.path.exists(path):
        try:
            Path(path).unlink()
        except Exception:
            pass
