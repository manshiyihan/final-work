import csv
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from app.core.config import (
    ARCHIVE_DIR,
    DB_ARCHIVE_PAGE_SIZE,
    DB_RECORD_RETENTION_DAYS,
    MAINTENANCE_INTERVAL_SECONDS,
    UPLOAD_DIR,
    UPLOAD_RETENTION_DAYS,
)
from app.repositories.record_repo import (
    count_records_older_than,
    delete_records_by_ids,
    list_records_older_than,
)


ARCHIVE_COLUMNS = [
    "id",
    "input_type",
    "audio_path",
    "audio_hash",
    "mfa_raw_output",
    "rawgat_raw_output",
    "speaker_result",
    "spoof_result",
    "risk_score",
    "final_label",
    "latency_ms",
    "created_at",
]


def cleanup_upload_files(retention_days: int = UPLOAD_RETENTION_DAYS) -> Dict[str, int]:
    now = datetime.now()
    cutoff = now - timedelta(days=retention_days)
    deleted = 0
    kept = 0

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for path in UPLOAD_DIR.iterdir():
        if not path.is_file():
            continue
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            if mtime < cutoff:
                path.unlink(missing_ok=True)
                deleted += 1
            else:
                kept += 1
        except Exception:
            kept += 1
    return {"deleted_files": deleted, "kept_files": kept}


def _write_archive_csv(records: List[Dict], archive_path: Path) -> None:
    with open(archive_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=ARCHIVE_COLUMNS)
        writer.writeheader()
        for row in records:
            writer.writerow({key: row.get(key, "") for key in ARCHIVE_COLUMNS})


def archive_old_records(retention_days: int = DB_RECORD_RETENTION_DAYS, delete_archived: bool = True) -> Dict[str, str]:
    cutoff = datetime.now() - timedelta(days=retention_days)
    cutoff_iso = cutoff.isoformat(timespec="seconds")
    total_old = count_records_older_than(cutoff_iso)
    if total_old == 0:
        return {"archived_count": 0, "deleted_count": 0, "archive_file": ""}

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    records: List[Dict] = []
    page = 0
    while True:
        chunk = list_records_older_than(cutoff_iso, limit=DB_ARCHIVE_PAGE_SIZE, offset=page * DB_ARCHIVE_PAGE_SIZE)
        if not chunk:
            break
        records.extend(chunk)
        page += 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = ARCHIVE_DIR / f"inference_record_archive_{timestamp}.csv"
    _write_archive_csv(records, archive_path)

    deleted_count = 0
    if delete_archived:
        deleted_count = delete_records_by_ids([int(item["id"]) for item in records if item.get("id") is not None])

    return {
        "archived_count": len(records),
        "deleted_count": deleted_count,
        "archive_file": str(archive_path),
    }


def run_maintenance_once() -> Dict[str, Dict]:
    upload_result = cleanup_upload_files()
    archive_result = archive_old_records()
    return {"upload_cleanup": upload_result, "db_archive": archive_result}


def start_maintenance_worker(stop_event: threading.Event):
    def _loop():
        while not stop_event.is_set():
            try:
                run_maintenance_once()
            except Exception:
                pass
            stop_event.wait(timeout=MAINTENANCE_INTERVAL_SECONDS)

    thread = threading.Thread(target=_loop, name="maintenance-worker", daemon=True)
    thread.start()
    return thread
