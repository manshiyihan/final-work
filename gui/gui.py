import subprocess
import os
import tempfile
import json
import mimetypes
import csv
import gradio as gr
from pathlib import Path
import soundfile as sf
import librosa
import numpy as np
from urllib import error, request

# 模型路径配置
# 仓库根目录：gui/gui.py -> comb_model/
BASE_DIR = Path(__file__).resolve().parent.parent

MFA_CHECKPOINT = str(BASE_DIR / "mfa_conformer_sv" / "epoch=17_cosine_eer=0.72.ckpt")
MFA_INFERENCE_SCRIPT = str(BASE_DIR / "mfa_conformer_sv" / "newinference.py")
MFA_FAISS_DIR = BASE_DIR / "mfa_conformer_sv" / "faiss"
RAWGAT_MODEL = str(BASE_DIR / "RawGAT-ST-antispoofing-main" / "epoch_42.pth")
RAWGAT_INFERENCE_SCRIPT = str(BASE_DIR / "RawGAT-ST-antispoofing-main" / "inference.py")
RAWGAT_CONFIG = str(BASE_DIR / "RawGAT-ST-antispoofing-main" / "model_config_RawGAT_ST.yaml")
API_BASE_URL = os.getenv("COMB_API_BASE_URL", "http://127.0.0.1:8000")

# 确保faiss目录存在
MFA_FAISS_DIR.mkdir(parents=True, exist_ok=True)

# 打印路径用于调试
print(f"BASE_DIR: {BASE_DIR}")
print(f"RAWGAT_CONFIG: {RAWGAT_CONFIG}")
print(f"RAWGAT_CONFIG exists: {os.path.exists(RAWGAT_CONFIG)}")


def build_multipart_form_data(fields, files):
    boundary = "----CombModelBoundary7MA4YWxkTrZu0gW"
    lines = []
    for name, value in fields.items():
        lines.extend(
            [
                f"--{boundary}",
                f'Content-Disposition: form-data; name="{name}"',
                "",
                str(value),
            ]
        )
    for name, file_path in files.items():
        filename = os.path.basename(file_path)
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        with open(file_path, "rb") as file:
            file_data = file.read()
        lines.extend(
            [
                f"--{boundary}",
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"',
                f"Content-Type: {content_type}",
                "",
            ]
        )
        lines.append(file_data)
    lines.append(f"--{boundary}--")
    lines.append("")

    body = b""
    for line in lines:
        if isinstance(line, bytes):
            body += line + b"\r\n"
        else:
            body += line.encode("utf-8") + b"\r\n"

    return body, boundary


def post_audio_api(endpoint, audio_path, extra_fields=None):
    extra_fields = extra_fields or {}
    body, boundary = build_multipart_form_data(extra_fields, {"audio": audio_path})
    req = request.Request(
        f"{API_BASE_URL}{endpoint}",
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return True, data
    except error.URLError as exc:
        return False, f"API请求失败: {exc}"
    except Exception as exc:
        return False, f"API响应异常: {exc}"


def get_json_api(endpoint):
    req = request.Request(f"{API_BASE_URL}{endpoint}", method="GET")
    try:
        with request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return True, data
    except error.URLError as exc:
        return False, f"API请求失败: {exc}"
    except Exception as exc:
        return False, f"API响应异常: {exc}"


def fetch_history_records(page, final_label, input_type, limit=10):
    label = "" if final_label == "all" else final_label
    source = "" if input_type == "all" else input_type
    endpoint = (
        f"/api/records/query?limit={int(limit)}&page={int(page)}"
        f"&final_label={label}&input_type={source}"
    )
    ok, resp = get_json_api(endpoint)
    if not ok:
        return f"❌ 获取历史记录失败：{resp}", []

    if not resp.get("ok"):
        return f"❌ 获取历史记录失败：{resp.get('error', '未知错误')}", []

    items = resp.get("items", [])
    pager = resp.get("pagination", {})
    summary = (
        f"✅ 共 {pager.get('total', 0)} 条记录，"
        f"当前第 {pager.get('page', 1)} 页，每页 {pager.get('limit', limit)} 条"
    )
    table_rows = []
    for item in items:
        table_rows.append(
            [
                item.get("id"),
                item.get("created_at", ""),
                item.get("input_type", ""),
                item.get("final_label", ""),
                item.get("risk_score", ""),
                item.get("latency_ms", ""),
                item.get("speaker_result", ""),
                item.get("spoof_result", ""),
            ]
        )
    return summary, table_rows


def export_history_csv(page, final_label, input_type, limit=200):
    label = "" if final_label == "all" else final_label
    source = "" if input_type == "all" else input_type
    endpoint = (
        f"/api/records/query?limit={int(limit)}&page={int(page)}"
        f"&final_label={label}&input_type={source}"
    )
    ok, resp = get_json_api(endpoint)
    if not ok:
        return None, f"❌ 导出失败：{resp}"
    if not resp.get("ok"):
        return None, f"❌ 导出失败：{resp.get('error', '未知错误')}"

    items = resp.get("items", [])
    return _write_history_csv(items), f"✅ 导出成功，共 {len(items)} 条，已生成 CSV 文件"


def _write_history_csv(items):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", newline="", encoding="utf-8") as tmp:
        writer = csv.writer(tmp)
        writer.writerow(
            [
                "id",
                "created_at",
                "input_type",
                "final_label",
                "risk_score",
                "latency_ms",
                "speaker_name",
                "spoof_result",
                "audio_path",
                "audio_hash",
            ]
        )
        for item in items:
            writer.writerow(
                [
                    item.get("id", ""),
                    item.get("created_at", ""),
                    item.get("input_type", ""),
                    item.get("final_label", ""),
                    item.get("risk_score", ""),
                    item.get("latency_ms", ""),
                    item.get("speaker_result", ""),
                    item.get("spoof_result", ""),
                    item.get("audio_path", ""),
                    item.get("audio_hash", ""),
                ]
            )
        file_path = tmp.name
    return file_path


def export_all_history_csv(final_label, input_type, page_size=200):
    label = "" if final_label == "all" else final_label
    source = "" if input_type == "all" else input_type

    first_endpoint = (
        f"/api/records/query?limit={int(page_size)}&page=1"
        f"&final_label={label}&input_type={source}"
    )
    ok, first_resp = get_json_api(first_endpoint)
    if not ok:
        return None, f"❌ 全量导出失败：{first_resp}"
    if not first_resp.get("ok"):
        return None, f"❌ 全量导出失败：{first_resp.get('error', '未知错误')}"

    pagination = first_resp.get("pagination", {})
    total = int(pagination.get("total", 0))
    if total == 0:
        return None, "⚠️ 当前筛选条件下没有可导出的记录"

    all_items = list(first_resp.get("items", []))
    total_pages = (total + int(page_size) - 1) // int(page_size)
    for page in range(2, total_pages + 1):
        endpoint = (
            f"/api/records/query?limit={int(page_size)}&page={page}"
            f"&final_label={label}&input_type={source}"
        )
        ok, resp = get_json_api(endpoint)
        if not ok or not resp.get("ok"):
            return None, f"❌ 全量导出失败：第 {page} 页请求异常"
        all_items.extend(resp.get("items", []))

    file_path = _write_history_csv(all_items)
    return file_path, f"✅ 全量导出成功，共 {len(all_items)} 条，已生成 CSV 文件"


def _to_status_text(final_label):
    if final_label == "pass":
        return "✅ 通过"
    if final_label == "fraud_risk":
        return "🚨 疑似欺诈"
    if final_label == "identity_unknown":
        return "⚠️ 身份未知"
    return "❓ 待确认"


def _extract_speaker_name_for_ui(mfa_result):
    text = (mfa_result or "").strip()
    if not text:
        return "未知"
    if "匹配人员" in text:
        parts = text.replace("：", ":").split(":", 1)
        if len(parts) == 2 and parts[1].strip():
            return parts[1].strip()
    if "不在库中" in text:
        return "未知"
    return text.splitlines()[0].strip() if text else "未知"


def _extract_spoof_result_for_ui(rawgat_result):
    text = (rawgat_result or "").strip().lower()
    if any(token in text for token in ["虚假", "spoof", "fake"]):
        return "伪造语音"
    if any(token in text for token in ["真实", "bonafide", "real"]):
        return "真实语音"
    return "未知"


def _build_simple_result_text(status, speaker_name, spoof_text, risk_score, latency_ms, current_time, mode_label):
    return f"""
## {status}

- 说话人: **{speaker_name}**
- 反欺诈: **{spoof_text}**
- 风险分数: **{risk_score}** | 耗时: **{latency_ms} ms**

`{mode_label}` · `{current_time}`
"""


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
        api_ok, api_result = post_audio_api("/api/verify", audio_path, {"input_type": "upload"})
        if api_ok and api_result.get("ok"):
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            mfa_result = api_result.get("mfa_result", "")
            rawgat_result = api_result.get("rawgat_result", "")
            final_label = api_result.get("final_label", "unknown")
            risk_score = api_result.get("risk_score", "N/A")
            latency_ms = api_result.get("latency_ms", "N/A")
            status = _to_status_text(final_label)
            speaker_name = api_result.get("speaker_result", "未知")
            spoof_text = "伪造语音" if api_result.get("spoof_result") == "spoof" else "真实语音"
            result_text = _build_simple_result_text(
                status, speaker_name, spoof_text, risk_score, latency_ms, current_time, "API模式"
            )
            return result_text, mfa_result, rawgat_result

        # API不可用时，回退到本地推理
        mfa_result, _ = run_mfa_conformer_inference(audio_path)
        rawgat_result, _ = run_rawgat_st_inference(audio_path)

        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        speaker_name = _extract_speaker_name_for_ui(mfa_result)
        spoof_text = _extract_spoof_result_for_ui(rawgat_result)
        status = "🚨 疑似欺诈" if spoof_text == "伪造语音" else ("⚠️ 身份未知" if speaker_name == "未知" else "✅ 通过")
        risk_score = "0.9" if spoof_text == "伪造语音" else ("0.7" if speaker_name == "未知" else "0.1")
        result_text = _build_simple_result_text(
            status, speaker_name, spoof_text, risk_score, "N/A", current_time, "本地模式"
        )
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
        
        api_ok, api_result = post_audio_api("/api/verify", temp_audio_path, {"input_type": "record"})
        if api_ok and api_result.get("ok"):
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            mfa_result = api_result.get("mfa_result", "")
            rawgat_result = api_result.get("rawgat_result", "")
            final_label = api_result.get("final_label", "unknown")
            risk_score = api_result.get("risk_score", "N/A")
            latency_ms = api_result.get("latency_ms", "N/A")
            status = _to_status_text(final_label)
            speaker_name = api_result.get("speaker_result", "未知")
            spoof_text = "伪造语音" if api_result.get("spoof_result") == "spoof" else "真实语音"
            result_text = _build_simple_result_text(
                status, speaker_name, spoof_text, risk_score, latency_ms, current_time, "API模式"
            )
            return result_text, mfa_result, rawgat_result

        # API不可用时，回退到本地推理
        mfa_result, _ = run_mfa_conformer_inference(temp_audio_path)
        rawgat_result, _ = run_rawgat_st_inference(temp_audio_path)
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        speaker_name = _extract_speaker_name_for_ui(mfa_result)
        spoof_text = _extract_spoof_result_for_ui(rawgat_result)
        status = "🚨 疑似欺诈" if spoof_text == "伪造语音" else ("⚠️ 身份未知" if speaker_name == "未知" else "✅ 通过")
        risk_score = "0.9" if spoof_text == "伪造语音" else ("0.7" if speaker_name == "未知" else "0.1")
        result_text = _build_simple_result_text(
            status, speaker_name, spoof_text, risk_score, "N/A", current_time, "本地模式"
        )
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
                    
                    api_ok, api_result = post_audio_api(
                        "/api/register",
                        temp_audio_path,
                        {"speaker_name": speaker_name},
                    )
                    if api_ok and api_result.get("ok"):
                        return f"✅ 注册成功: {api_result.get('speaker_name', speaker_name)}", ""

                    # API不可用时，回退到本地注册
                    result, _ = register_speaker(temp_audio_path, speaker_name)
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
                    
                    api_ok, api_result = post_audio_api(
                        "/api/register",
                        audio_path,
                        {"speaker_name": speaker_name},
                    )
                    if api_ok and api_result.get("ok"):
                        return f"✅ 注册成功: {api_result.get('speaker_name', speaker_name)}", ""

                    # API不可用时，回退到本地注册
                    result, _ = register_speaker(audio_path, speaker_name)
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

        # 模式5: 历史记录查询
        with gr.Tab("历史记录", id="history_tab"):
            gr.Markdown("### 查询检测历史记录（来自后端数据库）")
            with gr.Row():
                history_page = gr.Number(label="页码", value=1, precision=0)
                history_label = gr.Dropdown(
                    label="最终标签过滤",
                    choices=["all", "pass", "fraud_risk", "identity_unknown"],
                    value="all",
                )
                history_input_type = gr.Dropdown(
                    label="输入类型过滤",
                    choices=["all", "upload", "record"],
                    value="all",
                )
                history_refresh_btn = gr.Button("刷新记录", variant="primary")
                history_export_btn = gr.Button("导出当前筛选CSV")
                history_export_all_btn = gr.Button("导出全部筛选CSV")

            history_summary = gr.Textbox(label="查询摘要", interactive=False)
            history_table = gr.Dataframe(
                headers=[
                    "ID",
                    "时间",
                    "输入类型",
                    "最终标签",
                    "风险分数",
                    "耗时(ms)",
                    "说话人姓名",
                    "反欺诈结果",
                ],
                datatype=["number", "str", "str", "str", "number", "number", "str", "str"],
                interactive=False,
                row_count=10,
                col_count=(8, "fixed"),
            )
            history_export_file = gr.File(label="CSV下载", interactive=False)
            history_export_status = gr.Textbox(label="导出状态", interactive=False)

            history_refresh_btn.click(
                fn=fetch_history_records,
                inputs=[history_page, history_label, history_input_type],
                outputs=[history_summary, history_table],
            )
            history_export_btn.click(
                fn=export_history_csv,
                inputs=[history_page, history_label, history_input_type],
                outputs=[history_export_file, history_export_status],
            )
            history_export_all_btn.click(
                fn=export_all_history_csv,
                inputs=[history_label, history_input_type],
                outputs=[history_export_file, history_export_status],
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

