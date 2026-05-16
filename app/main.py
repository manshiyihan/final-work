import time
import threading
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, Query, Header, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from app.repositories.db import init_db
from app.services.auth_service import (
    register_user,
    login_user,
    logout_user,
    get_current_user,
    verify_token,
)
from app.repositories.record_repo import (
    count_records,
    insert_inference_record,
    insert_speaker_profile,
    insert_system_event,
    list_records,
    list_latest_records,
)
from app.services.audio_service import cleanup_file, ensure_16k_audio, file_sha256, save_upload_file, validate_audio_file
from app.services.fusion_service import extract_speaker_name, parse_outputs
from app.services.maintenance_service import archive_old_records, cleanup_upload_files, start_maintenance_worker
from app.services.model_service import run_both_inferences_parallel
from app.services.model_loader import model_manager
from app.services.register_service import register_speaker


app = FastAPI(title="Conformer Anti-Fraud Speaker API", version="0.1.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

maintenance_stop_event = threading.Event()
maintenance_thread = None


# 依赖项：获取当前用户
async def get_current_user_dep(authorization: Optional[str] = Header(None)):
    """获取当前登录用户（可选）"""
    if not authorization:
        return None
    
    # 支持 "Bearer token" 格式
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    session = verify_token(token)
    if not session:
        return None
    
    return get_current_user(token)


def _normalize_speaker_for_display(item):
    speaker_result = (item.get("speaker_result") or "").strip()
    if speaker_result and speaker_result not in {"known", "unknown"}:
        return speaker_result
    parsed_name = extract_speaker_name(item.get("mfa_raw_output", ""))
    if parsed_name != "unknown":
        return parsed_name
    return "未知"


def _normalize_record_items(items):
    normalized = []
    for item in items:
        row = dict(item)
        row["speaker_result"] = _normalize_speaker_for_display(row)
        normalized.append(row)
    return normalized


@app.on_event("startup")
def startup_event():
    global maintenance_thread
    init_db()
    
    # 预加载模型到内存
    print("Preloading models...")
    model_manager.load_all_models()
    print("Models loaded successfully")
    
    maintenance_stop_event.clear()
    maintenance_thread = start_maintenance_worker(maintenance_stop_event)


@app.on_event("shutdown")
def shutdown_event():
    maintenance_stop_event.set()


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "time": datetime.now().isoformat(timespec="seconds"),
    }


@app.post("/api/verify")
async def verify_audio(audio: UploadFile = File(...), input_type: str = Form(default="upload")):
    start = time.perf_counter()
    saved_path = ""
    converted_path = ""
    try:
        # 验证文件格式
        is_valid, error_msg = validate_audio_file(audio.filename or "", audio.content_type)
        if not is_valid:
            return JSONResponse(status_code=400, content={"ok": False, "error": error_msg})
        
        raw_bytes = await audio.read()
        filename = f"{int(time.time() * 1000)}_{Path(audio.filename or 'audio.wav').name}"
        saved_path = save_upload_file(filename, raw_bytes)
        audio_hash = file_sha256(saved_path)
        use_path, converted_path = ensure_16k_audio(saved_path)

        # 并行运行两个模型推理
        (mfa_result, mfa_json), (rawgat_result, rawgat_json) = await run_both_inferences_parallel(use_path)
        
        fused = parse_outputs(mfa_result, rawgat_result, mfa_json=mfa_json, rawgat_json=rawgat_json)
        latency_ms = int((time.perf_counter() - start) * 1000)

        insert_inference_record(
            {
                "input_type": input_type,
                "audio_path": saved_path,
                "audio_hash": audio_hash,
                "mfa_raw_output": mfa_result,
                "rawgat_raw_output": rawgat_result,
                "speaker_result": fused["speaker_result"],
                "spoof_result": fused["spoof_result"],
                "risk_score": fused["risk_score"],
                "final_label": fused["final_label"],
                "latency_ms": latency_ms,
            }
        )

        return {
            "ok": True,
            "mfa_result": mfa_result,
            "rawgat_result": rawgat_result,
            "speaker_result": fused["speaker_result"],
            "spoof_result": fused["spoof_result"],
            "risk_score": fused["risk_score"],
            "final_label": fused["final_label"],
            "latency_ms": latency_ms,
        }
    except Exception as exc:
        insert_system_event("verify", "error", "verify failed", str(exc))
        return JSONResponse(status_code=500, content={"ok": False, "error": str(exc)})
    finally:
        cleanup_file(converted_path)


@app.post("/api/register")
async def register_audio(audio: UploadFile = File(...), speaker_name: str = Form(...)):
    saved_path = ""
    converted_path = ""
    try:
        # 验证文件格式
        is_valid, error_msg = validate_audio_file(audio.filename or "", audio.content_type)
        if not is_valid:
            return JSONResponse(status_code=400, content={"ok": False, "error": error_msg})
        
        raw_bytes = await audio.read()
        filename = f"{int(time.time() * 1000)}_{Path(audio.filename or 'register.wav').name}"
        saved_path = save_upload_file(filename, raw_bytes)
        use_path, converted_path = ensure_16k_audio(saved_path)

        speaker_name_clean, raw_output = register_speaker(use_path, speaker_name)
        insert_speaker_profile(speaker_name=speaker_name, embedding_name=speaker_name_clean, note=raw_output)
        return {"ok": True, "speaker_name": speaker_name_clean, "message": "注册成功", "raw_output": raw_output}
    except Exception as exc:
        insert_system_event("register", "error", "register failed", str(exc))
        return JSONResponse(status_code=500, content={"ok": False, "error": str(exc)})
    finally:
        cleanup_file(converted_path)


@app.get("/api/records")
def records(limit: int = 50):
    items = list_latest_records(limit=limit)
    return {"ok": True, "items": _normalize_record_items(items)}


@app.get("/api/records/query")
def query_records(
    limit: int = 20,
    page: int = 1,
    final_label: str = "",
    input_type: str = "",
):
    safe_limit = min(max(limit, 1), 100)
    safe_page = max(page, 1)
    offset = (safe_page - 1) * safe_limit

    items = list_records(
        limit=safe_limit,
        offset=offset,
        final_label=final_label or None,
        input_type=input_type or None,
    )
    items = _normalize_record_items(items)
    total = count_records(final_label=final_label or None, input_type=input_type or None)
    return {
        "ok": True,
        "items": items,
        "pagination": {
            "page": safe_page,
            "limit": safe_limit,
            "total": total,
        },
        "filters": {
            "final_label": final_label or "all",
            "input_type": input_type or "all",
        },
    }


@app.post("/api/maintenance/cleanup-uploads")
def maintenance_cleanup_uploads(retention_days: int = Query(default=7, ge=1, le=365)):
    result = cleanup_upload_files(retention_days=retention_days)
    insert_system_event("maintenance", "info", "upload cleanup finished", str(result))
    return {"ok": True, "result": result}


@app.post("/api/maintenance/archive-records")
def maintenance_archive_records(
    retention_days: int = Query(default=30, ge=1, le=3650),
    delete_archived: bool = Query(default=True),
):
    result = archive_old_records(retention_days=retention_days, delete_archived=delete_archived)
    insert_system_event("maintenance", "info", "db archive finished", str(result))
    return {"ok": True, "result": result}


# ==================== 用户认证API ====================

@app.post("/api/auth/register")
async def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(None),
):
    """用户注册"""
    try:
        success, message = register_user(username, email, password, full_name)
        if success:
            return {"ok": True, "message": message}
        else:
            return JSONResponse(status_code=400, content={"ok": False, "error": message})
    except Exception as exc:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(exc)})


@app.post("/api/auth/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
):
    """用户登录"""
    try:
        success, token_or_message, user_info = login_user(username, password)
        if success:
            return {
                "ok": True,
                "token": token_or_message,
                "user": user_info,
            }
        else:
            return JSONResponse(status_code=401, content={"ok": False, "error": token_or_message})
    except Exception as exc:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(exc)})


@app.post("/api/auth/logout")
async def logout(authorization: str = Header(None)):
    """用户登出"""
    if not authorization:
        return JSONResponse(status_code=401, content={"ok": False, "error": "未提供令牌"})
    
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    success = logout_user(token)
    if success:
        return {"ok": True, "message": "登出成功"}
    else:
        return {"ok": False, "message": "令牌无效"}


@app.get("/api/auth/me")
async def get_me(current_user: Optional[dict] = Depends(get_current_user_dep)):
    """获取当前用户信息"""
    if not current_user:
        return JSONResponse(status_code=401, content={"ok": False, "error": "未登录"})
    
    return {"ok": True, "user": current_user}
