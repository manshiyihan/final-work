import subprocess
import os
import tempfile
import gradio as gr
from pathlib import Path
import soundfile as sf
import librosa
import numpy as np

# 模型路径配置
# 仓库根目录：gui/gui.py -> comb_model/
BASE_DIR = Path(__file__).resolve().parent.parent

MFA_CHECKPOINT = str(BASE_DIR / "mfa_conformer_sv" / "epoch=17_cosine_eer=0.72.ckpt")
MFA_INFERENCE_SCRIPT = str(BASE_DIR / "mfa_conformer_sv" / "newinference.py")
MFA_FAISS_DIR = BASE_DIR / "mfa_conformer_sv" / "faiss"
RAWGAT_MODEL = str(BASE_DIR / "RawGAT-ST-antispoofing-main" / "epoch_42.pth")
RAWGAT_INFERENCE_SCRIPT = str(BASE_DIR / "RawGAT-ST-antispoofing-main" / "inference.py")
RAWGAT_CONFIG = str(BASE_DIR / "RawGAT-ST-antispoofing-main" / "model_config_RawGAT_ST.yaml")

# 确保faiss目录存在
MFA_FAISS_DIR.mkdir(parents=True, exist_ok=True)


def run_mfa_conformer_inference(audio_path):
    """运行说话人验证模型"""
    mode = 'verify'
    command = [
        "python", MFA_INFERENCE_SCRIPT,
        "--test_audio", audio_path,
        "--checkpoint_path", MFA_CHECKPOINT,
        "--mode", mode,
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return f"错误: {result.stderr}", "error"
        output = result.stdout.strip()
        return output, "success"
    except subprocess.TimeoutExpired:
        return "错误: 推理超时", "error"
    except Exception as e:
        return f"错误: {str(e)}", "error"


def run_rawgat_st_inference(audio_path):
    """运行反欺骗模型"""
    command = [
        "python", RAWGAT_INFERENCE_SCRIPT,
        "--audio_path", audio_path,
        "--model_path", RAWGAT_MODEL,
        "--model_config", RAWGAT_CONFIG,
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return f"错误: {result.stderr}", "error"
        output = result.stdout.strip()
        return output, "success"
    except subprocess.TimeoutExpired:
        return "错误: 推理超时", "error"
    except Exception as e:
        return f"错误: {str(e)}", "error"


def register_speaker(audio_path, speaker_name):
    """注册新的说话人"""
    if not speaker_name or speaker_name.strip() == "":
        return "❌ 错误: 请输入说话人名称", "error"
    
    # 清理说话人名称（移除特殊字符，只保留字母数字、中文、下划线和连字符）
    import re
    # 允许中文字符、英文字母、数字、下划线和连字符
    speaker_name_clean = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', speaker_name.strip())
    speaker_name_clean = re.sub(r'[-\s]+', '_', speaker_name_clean)
    
    if not speaker_name_clean:
        return "❌ 错误: 说话人名称无效，请使用字母、数字、中文或下划线", "error"
    
    mode = 'add'
    command = [
        "python", MFA_INFERENCE_SCRIPT,
        "--test_audio", audio_path,
        "--checkpoint_path", MFA_CHECKPOINT,
        "--mode", mode,
        "--new_embedding_name", speaker_name_clean,
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
            return f"❌ 注册失败: {error_msg}", "error"
        output = result.stdout.strip()
        if "Index saved" in output or "saved" in output.lower() or not output:
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"""✅ **注册成功！**

**说话人名称**: {speaker_name_clean}
**注册时间**: {current_time}

说话人已成功添加到系统中，现在可以使用该说话人的音频进行验证了。""", "success"
        return f"📝 注册结果: {output}", "success"
    except subprocess.TimeoutExpired:
        return "❌ 错误: 注册超时，请重试", "error"
    except Exception as e:
        return f"❌ 错误: {str(e)}", "error"


def process_audio_file(audio_file):
    """处理上传的音频文件"""
    if audio_file is None:
        return "请先上传音频文件", "", ""
    
    # 处理不同格式的文件输入
    if isinstance(audio_file, str):
        audio_path = audio_file
    elif hasattr(audio_file, 'name'):
        audio_path = audio_file.name
    else:
        audio_path = str(audio_file)
    
    if not os.path.exists(audio_path):
        return "错误: 音频文件不存在", "", ""
    
    try:
        # 运行两个模型
        mfa_result, mfa_status = run_mfa_conformer_inference(audio_path)
        rawgat_result, rawgat_status = run_rawgat_st_inference(audio_path)
        
        # 格式化结果
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        result_text = f"""
## 📊 检测结果

### 🎤 说话人验证结果
{mfa_result}

### 🛡️ 反欺骗检测结果
{rawgat_result}

---
*检测完成时间: {current_time}*
"""
        
        return result_text, mfa_result, rawgat_result
    except Exception as e:
        return f"错误: {str(e)}", "", ""


def convert_audio_to_16khz_mono(input_path, output_path):
    """将音频转换为16kHz单声道格式"""
    try:
        # 使用librosa加载音频，自动转换为单声道和指定采样率
        audio_data, sr = librosa.load(input_path, sr=16000, mono=True)
        
        # 确保数据类型正确
        audio_data = audio_data.astype(np.float32)
        
        # 保存为16kHz单声道WAV文件
        sf.write(output_path, audio_data, 16000, subtype='PCM_16')
        
        return True, None
    except Exception as e:
        return False, str(e)


def process_recorded_audio(audio):
    """处理录音文件"""
    if audio is None:
        return "请先录制音频", "", ""
    
    # Gradio Audio组件返回文件路径
    audio_path = audio if isinstance(audio, str) else (audio if audio else None)
    
    if audio_path is None or not os.path.exists(audio_path):
        return "错误: 音频文件不存在", "", ""
    
    # 创建临时文件用于存储转换后的音频
    temp_audio_path = None
    try:
        # 转换音频格式为16kHz单声道
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            temp_audio_path = tmp_file.name
        
        success, error_msg = convert_audio_to_16khz_mono(audio_path, temp_audio_path)
        
        if not success:
            return f"错误: 音频格式转换失败 - {error_msg}", "", ""
        
        # 使用转换后的音频文件运行两个模型
        mfa_result, mfa_status = run_mfa_conformer_inference(temp_audio_path)
        rawgat_result, rawgat_status = run_rawgat_st_inference(temp_audio_path)
        
        # 格式化结果
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        result_text = f"""
## 📊 检测结果

### 🎤 说话人验证结果
{mfa_result}

### 🛡️ 反欺骗检测结果
{rawgat_result}

---
*检测完成时间: {current_time}*
"""
        
        return result_text, mfa_result, rawgat_result
    except Exception as e:
        return f"错误: {str(e)}", "", ""
    finally:
        # 清理临时文件
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
            except:
                pass


# 自定义CSS样式
custom_css = """
.gradio-container {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.main-header {
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 30px;
    border-radius: 10px;
    color: white;
    margin-bottom: 20px;
}
.result-box {
    border: 2px solid #667eea;
    border-radius: 10px;
    padding: 20px;
    margin: 10px 0;
    background: #f8f9fa;
}
"""


# 创建Gradio界面
with gr.Blocks(css=custom_css, theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    <div class="main-header">
        <h1>抗欺诈说话人识别系统</h1>
        <p>说话人验证 + 反欺骗检测</p>
    </div>
    """)
    
    with gr.Tabs() as tabs:
        # 模式1: 本地文件检测
        with gr.Tab("本地文件检测", id="file_tab"):
            gr.Markdown("### 上传音频文件进行检测")
            with gr.Row():
                with gr.Column():
                    file_input = gr.File(
                        label="选择音频文件",
                        file_types=["audio"],
                        type="filepath"
                    )
                    file_btn = gr.Button("开始检测", variant="primary", size="lg")
                
                with gr.Column():
                    file_audio_player = gr.Audio(label="音频预览", type="filepath")
            
            file_result = gr.Markdown(label="检测结果", elem_classes=["result-box"])
            
            with gr.Row():
                file_mfa_result = gr.Textbox(
                    label="说话人验证结果",
                    interactive=False,
                    lines=2
                )
                file_rawgat_result = gr.Textbox(
                    label="反欺骗检测结果",
                    interactive=False,
                    lines=2
                )
            
            # 绑定事件
            file_input.change(
                fn=lambda x: x,
                inputs=file_input,
                outputs=file_audio_player
            )
            
            file_btn.click(
                fn=process_audio_file,
                inputs=file_input,
                outputs=[file_result, file_mfa_result, file_rawgat_result]
            )
        
        # 模式2: 录音检测
        with gr.Tab("录音检测", id="record_tab"):
            gr.Markdown("### 录制音频进行实时检测")
            with gr.Row():
                with gr.Column():
                    record_input = gr.Audio(
                        label="录制音频",
                        sources=["microphone"],
                        type="filepath"
                    )
                    record_btn = gr.Button("开始检测", variant="primary", size="lg")
                
                with gr.Column():
                    record_audio_player = gr.Audio(label="录音预览", type="filepath")
            
            record_result = gr.Markdown(label="检测结果", elem_classes=["result-box"])
            
            with gr.Row():
                record_mfa_result = gr.Textbox(
                    label="说话人验证结果",
                    interactive=False,
                    lines=2
                )
                record_rawgat_result = gr.Textbox(
                    label="反欺骗检测结果",
                    interactive=False,
                    lines=2
                )
            
            # 绑定事件
            record_input.change(
                fn=lambda x: x,
                inputs=record_input,
                outputs=record_audio_player
            )
            
            record_btn.click(
                fn=process_recorded_audio,
                inputs=record_input,
                outputs=[record_result, record_mfa_result, record_rawgat_result]
            )
        
        # 模式3: 注册说话人（录音）
        with gr.Tab("注册说话人（录音）", id="register_record_tab"):
            gr.Markdown("### 录制音频注册新的说话人")
            with gr.Row():
                with gr.Column():
                    register_record_input = gr.Audio(
                        label="录制音频",
                        sources=["microphone"],
                        type="filepath"
                    )
                    register_record_name = gr.Textbox(
                        label="说话人名称",
                        placeholder="请输入说话人名称（例如：张三、John等）",
                        info="名称将用于标识该说话人"
                    )
                    register_record_btn = gr.Button("✅ 注册说话人", variant="primary", size="lg")
                
                with gr.Column():
                    register_record_audio_player = gr.Audio(label="录音预览", type="filepath")
            
            register_record_result = gr.Markdown(label="注册结果", elem_classes=["result-box"])
            
            # 绑定事件
            register_record_input.change(
                fn=lambda x: x,
                inputs=register_record_input,
                outputs=register_record_audio_player
            )
            
            def process_register_record(audio, speaker_name):
                """处理录音注册"""
                if audio is None:
                    return "请先录制音频", ""
                
                audio_path = audio if isinstance(audio, str) else (audio if audio else None)
                
                if audio_path is None or not os.path.exists(audio_path):
                    return "错误: 音频文件不存在", ""
                
                try:
                    # 转换音频格式为16kHz单声道
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                        temp_audio_path = tmp_file.name
                    
                    success, error_msg = convert_audio_to_16khz_mono(audio_path, temp_audio_path)
                    
                    if not success:
                        return f"错误: 音频格式转换失败 - {error_msg}", ""
                    
                    # 注册说话人
                    result, status = register_speaker(temp_audio_path, speaker_name)
                    
                    return result, ""
                except Exception as e:
                    return f"错误: {str(e)}", ""
                finally:
                    # 清理临时文件
                    if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path):
                        try:
                            os.unlink(temp_audio_path)
                        except:
                            pass
            
            register_record_btn.click(
                fn=process_register_record,
                inputs=[register_record_input, register_record_name],
                outputs=[register_record_result, register_record_name]
            )
        
        # 模式4: 注册说话人（文件上传）
        with gr.Tab("注册说话人（文件）", id="register_file_tab"):
            gr.Markdown("### 上传音频文件注册新的说话人")
            with gr.Row():
                with gr.Column():
                    register_file_input = gr.File(
                        label="选择音频文件",
                        file_types=["audio"],
                        type="filepath"
                    )
                    register_file_name = gr.Textbox(
                        label="说话人名称",
                        placeholder="请输入说话人名称（例如：张三、John等）",
                        info="名称将用于标识该说话人"
                    )
                    register_file_btn = gr.Button("✅ 注册说话人", variant="primary", size="lg")
                
                with gr.Column():
                    register_file_audio_player = gr.Audio(label="音频预览", type="filepath")
            
            register_file_result = gr.Markdown(label="注册结果", elem_classes=["result-box"])
            
            # 绑定事件
            register_file_input.change(
                fn=lambda x: x,
                inputs=register_file_input,
                outputs=register_file_audio_player
            )
            
            def process_register_file(audio_file, speaker_name):
                """处理文件注册"""
                if audio_file is None:
                    return "请先上传音频文件", ""
                
                # 处理不同格式的文件输入
                if isinstance(audio_file, str):
                    audio_path = audio_file
                elif hasattr(audio_file, 'name'):
                    audio_path = audio_file.name
                else:
                    audio_path = str(audio_file)
                
                if not os.path.exists(audio_path):
                    return "错误: 音频文件不存在", ""
                
                # 创建临时文件用于存储转换后的音频
                temp_audio_path = None
                try:
                    # 检查音频格式，如果不是16kHz单声道则转换
                    try:
                        audio_data, sr = sf.read(audio_path)
                        need_convert = False
                        if sr != 16000:
                            need_convert = True
                        if audio_data.ndim > 1:
                            need_convert = True
                        
                        if need_convert:
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                                temp_audio_path = tmp_file.name
                            success, error_msg = convert_audio_to_16khz_mono(audio_path, temp_audio_path)
                            if not success:
                                return f"错误: 音频格式转换失败 - {error_msg}", ""
                            audio_path = temp_audio_path
                    except:
                        # 如果读取失败，尝试使用librosa转换
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                            temp_audio_path = tmp_file.name
                        success, error_msg = convert_audio_to_16khz_mono(audio_path, temp_audio_path)
                        if not success:
                            return f"错误: 音频格式转换失败 - {error_msg}", ""
                        audio_path = temp_audio_path
                    
                    # 注册说话人
                    result, status = register_speaker(audio_path, speaker_name)
                    
                    return result, ""
                except Exception as e:
                    return f"错误: {str(e)}", ""
                finally:
                    # 清理临时文件
                    if temp_audio_path and os.path.exists(temp_audio_path):
                        try:
                            os.unlink(temp_audio_path)
                        except:
                            pass
            
            register_file_btn.click(
                fn=process_register_file,
                inputs=[register_file_input, register_file_name],
                outputs=[register_file_result, register_file_name]
            )
    
    gr.Markdown("""
    ---
    ### 使用说明
    1. **本地文件检测**: 上传本地音频文件（支持 wav, mp3, flac 等格式）
    2. **录音检测**: 点击录音按钮，录制音频后进行检测
    3. **注册说话人（录音）**: 录制音频并输入说话人名称，将说话人注册到系统中
    4. **注册说话人（文件）**: 上传音频文件并输入说话人名称，将说话人注册到系统中
    5. 系统将同时进行说话人验证和反欺骗检测
    6. 检测结果会实时显示在下方
    """)


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )

