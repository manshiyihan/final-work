"""模型推理服务 - 使用常驻内存的模型"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Tuple

from app.services.model_loader import model_manager


# 线程池用于并行推理
_executor = ThreadPoolExecutor(max_workers=2)


def run_mfa_conformer_inference(audio_path: str) -> Tuple[str, Dict]:
    """MFA Conformer 推理（同步版本）"""
    return model_manager.mfa_inference(audio_path)


def run_rawgat_st_inference(audio_path: str) -> Tuple[str, Dict]:
    """RawGAT-ST 推理（同步版本）"""
    return model_manager.rawgat_inference(audio_path)


async def run_both_inferences_parallel(audio_path: str) -> Tuple[Tuple[str, Dict], Tuple[str, Dict]]:
    """并行运行两个模型的推理"""
    loop = asyncio.get_event_loop()
    
    # 在线程池中并行执行两个推理任务
    mfa_task = loop.run_in_executor(_executor, run_mfa_conformer_inference, audio_path)
    rawgat_task = loop.run_in_executor(_executor, run_rawgat_st_inference, audio_path)
    
    # 等待两个任务完成
    mfa_result, rawgat_result = await asyncio.gather(mfa_task, rawgat_task)
    
    return mfa_result, rawgat_result
