"""模型加载和管理服务 - 保持模型常驻内存"""
import os
import json
import torch
import numpy as np
import faiss
import yaml
from pathlib import Path
from typing import Dict, Tuple, Optional
import soundfile as sf

from app.core.config import (
    MFA_CHECKPOINT,
    RAWGAT_CONFIG,
    RAWGAT_MODEL,
)


class ModelManager:
    """模型管理器 - 单例模式，保持模型常驻内存"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.mfa_model = None
            self.rawgat_model = None
            self.faiss_index = None
            self.speaker_ids = []
            self.register_embedding_paths = []
            self._initialized = True
    
    def load_mfa_model(self):
        """加载 MFA Conformer 模型"""
        if self.mfa_model is not None:
            return  # 已加载
        
        print(f"Loading MFA Conformer model on {self.device}...")
        
        # 动态导入 MFA 模型
        import sys
        mfa_dir = Path(__file__).parent.parent.parent / "mfa_conformer_sv"
        if str(mfa_dir) not in sys.path:
            sys.path.insert(0, str(mfa_dir))
        
        from main import Task
        
        # 加载模型
        self.mfa_model = Task(
            embedding_dim=192,
            num_blocks=6,
            loss_name="amsoftmax",
            input_layer="conv2d2",
            pos_enc_layer_type="abs_pos",
            sample_rate=16000
        )
        self.mfa_model.eval()
        
        state_dict = torch.load(MFA_CHECKPOINT, map_location=self.device)["state_dict"]
        self.mfa_model.load_state_dict(state_dict)
        self.mfa_model.to(self.device)
        
        # 加载 FAISS 索引和说话人信息
        self._load_faiss_index()
        
        print("MFA Conformer model loaded successfully")
    
    def _load_faiss_index(self):
        """加载 FAISS 索引"""
        base_dir = Path(__file__).parent.parent.parent / "mfa_conformer_sv"
        register_folder = base_dir / "faiss"
        index_path = register_folder / "faiss_index.index"
        
        # 获取注册嵌入向量列表
        self.register_embedding_paths = []
        self.speaker_ids = []
        
        for root, dirs, files in os.walk(register_folder):
            for file in files:
                if file.endswith('.npy'):
                    self.register_embedding_paths.append(os.path.join(root, file))
                    self.speaker_ids.append(os.path.basename(root))
        
        # 加载 FAISS 索引
        if index_path.exists():
            self.faiss_index = faiss.read_index(str(index_path))
        else:
            # 创建新索引
            dimension = 192
            self.faiss_index = faiss.IndexFlatIP(dimension)
            
            # 加载现有嵌入向量
            register_embeddings = []
            for embedding_path in self.register_embedding_paths:
                emb = torch.from_numpy(np.load(embedding_path)).squeeze().to(self.device)
                emb_normalized = emb / torch.norm(emb)
                register_embeddings.append(emb_normalized)
            
            if register_embeddings:
                register_matrix = torch.stack(register_embeddings).cpu().numpy()
                self.faiss_index.add(register_matrix)
    
    def load_rawgat_model(self):
        """加载 RawGAT-ST 模型"""
        if self.rawgat_model is not None:
            return  # 已加载
        
        print(f"Loading RawGAT-ST model on {self.device}...")
        
        # 动态导入 RawGAT 模型
        import sys
        rawgat_dir = Path(__file__).parent.parent.parent / "RawGAT-ST-antispoofing-main"
        if str(rawgat_dir) not in sys.path:
            sys.path.insert(0, str(rawgat_dir))
        
        from model import RawGAT_ST
        
        # 加载配置
        with open(RAWGAT_CONFIG, 'r') as f:
            config = yaml.safe_load(f)
        
        # 初始化模型
        self.rawgat_model = RawGAT_ST(config['model'], str(self.device))
        self.rawgat_model.load_state_dict(torch.load(RAWGAT_MODEL, map_location=self.device))
        self.rawgat_model.to(self.device)
        self.rawgat_model.eval()
        
        print("RawGAT-ST model loaded successfully")
    
    def load_all_models(self):
        """加载所有模型"""
        self.load_mfa_model()
        self.load_rawgat_model()
    
    def mfa_inference(self, audio_path: str, threshold: float = 0.27) -> Tuple[str, Dict]:
        """MFA Conformer 推理"""
        if self.mfa_model is None:
            self.load_mfa_model()
        
        # 动态导入音频加载函数
        import sys
        mfa_dir = Path(__file__).parent.parent.parent / "mfa_conformer_sv"
        if str(mfa_dir) not in sys.path:
            sys.path.insert(0, str(mfa_dir))
        
        from module.dataset import load_audio
        
        try:
            # 加载音频
            wav = load_audio(audio_path, -1, 16000)
            
            # 提取嵌入向量
            with torch.no_grad():
                test_embedding = self.mfa_model(torch.FloatTensor(wav).unsqueeze(0).to(self.device))
            
            # L2 归一化
            test_embedding_normalized = test_embedding / torch.norm(test_embedding)
            
            # FAISS 搜索
            test_embedding_np = test_embedding_normalized.detach().cpu().numpy()
            D, I = self.faiss_index.search(test_embedding_np, 1)
            
            max_similarity = float(D[0][0])
            matching_index = int(I[0][0])
            
            if matching_index < len(self.register_embedding_paths):
                matching_embedding_file = self.register_embedding_paths[matching_index]
                matched_name = os.path.splitext(os.path.basename(matching_embedding_file))[0]
            else:
                matched_name = "unknown"
            
            # 构建结果
            if max_similarity >= threshold:
                result_dict = {
                    "ok": True,
                    "mode": "verify",
                    "matched": True,
                    "speaker_name": matched_name,
                    "similarity": max_similarity,
                    "threshold": threshold,
                }
                result_str = f"匹配人员: {matched_name}"
            else:
                result_dict = {
                    "ok": True,
                    "mode": "verify",
                    "matched": False,
                    "speaker_name": "unknown",
                    "similarity": max_similarity,
                    "threshold": threshold,
                }
                result_str = "该人员不在库中"
            
            return result_str, result_dict
            
        except Exception as e:
            error_dict = {"ok": False, "mode": "verify", "error": str(e)}
            return f"Error: {str(e)}", error_dict
    
    def rawgat_inference(self, audio_path: str) -> Tuple[str, Dict]:
        """RawGAT-ST 推理"""
        if self.rawgat_model is None:
            self.load_rawgat_model()
        
        try:
            # 加载音频
            audio_data = self._load_audio_file(audio_path)
            
            # 转换为张量
            audio_tensor = torch.Tensor(audio_data).unsqueeze(0).to(self.device)
            
            # 推理
            with torch.no_grad():
                output = self.rawgat_model(audio_tensor, Freq_aug=False)
            
            # 获取预测结果
            _, predicted = torch.max(output, 1)
            prediction = predicted.item()
            
            # 构建结果
            result_dict = {
                "ok": True,
                "label": "bonafide" if prediction == 1 else "spoof",
                "label_zh": "真实" if prediction == 1 else "虚假",
                "prediction": int(prediction),
            }
            result_str = f"判断结果: {'真实' if prediction == 1 else '虚假'}"
            
            return result_str, result_dict
            
        except Exception as e:
            error_dict = {"ok": False, "error": str(e)}
            return f"Error: {str(e)}", error_dict
    
    @staticmethod
    def _load_audio_file(file_path: str, max_len: int = 64600) -> np.ndarray:
        """加载音频文件"""
        audio_data, sample_rate = sf.read(file_path)
        
        # 转换为单声道
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=-1)
        
        audio_data = audio_data.flatten()
        
        # 重采样到 16kHz
        if sample_rate != 16000:
            try:
                import librosa
                audio_data = librosa.resample(
                    audio_data.astype(np.float32),
                    orig_sr=sample_rate,
                    target_sr=16000
                )
            except ImportError:
                raise ImportError("librosa is required for resampling")
        
        # 填充或截断
        audio_data = ModelManager._pad_audio(audio_data, max_len)
        return audio_data
    
    @staticmethod
    def _pad_audio(x: np.ndarray, max_len: int = 64600) -> np.ndarray:
        """填充或截断音频"""
        x_len = x.shape[0]
        if x_len >= max_len:
            return x[:max_len]
        
        num_repeats = int(max_len / x_len) + 1
        padded_x = np.tile(x, (1, num_repeats))[:, :max_len][0]
        return padded_x


# 全局单例
model_manager = ModelManager()
