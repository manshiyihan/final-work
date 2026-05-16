from datetime import datetime
from typing import Any, Dict, List, Optional

from app.repositories.db import get_conn


def insert_inference_record(payload: Dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO inference_record (
                input_type, audio_path, audio_hash,
                mfa_raw_output, rawgat_raw_output,
                speaker_result, spoof_result, risk_score,
                final_label, latency_ms, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["input_type"],
                payload["audio_path"],
                payload.get("audio_hash"),
                payload["mfa_raw_output"],
                payload["rawgat_raw_output"],
                payload["speaker_result"],
                payload["spoof_result"],
                payload["risk_score"],
                payload["final_label"],
                payload["latency_ms"],
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()


def insert_system_event(event_type: str, level: str, message: str, detail: str = "") -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO system_event_log (event_type, level, message, detail, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (event_type, level, message, detail, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()


def insert_speaker_profile(speaker_name: str, embedding_name: str, note: str = "") -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO speaker_profile (speaker_name, embedding_name, created_at, note)
            VALUES (?, ?, ?, ?)
            """,
            (speaker_name, embedding_name, datetime.now().isoformat(timespec="seconds"), note),
        )
        conn.commit()


def list_latest_records(limit: int = 50) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
        rows = conn.execute(
            "SELECT * FROM inference_record ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return rows


def list_records(
    limit: int = 20,
    offset: int = 0,
    final_label: Optional[str] = None,
    input_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    query = "SELECT * FROM inference_record"
    clauses = []
    params: List[Any] = []

    if final_label:
        clauses.append("final_label = ?")
        params.append(final_label)
    if input_type:
        clauses.append("input_type = ?")
        params.append(input_type)

    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_conn() as conn:
        conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
        rows = conn.execute(query, tuple(params)).fetchall()
    return rows


def count_records(final_label: Optional[str] = None, input_type: Optional[str] = None) -> int:
    query = "SELECT COUNT(1) AS total FROM inference_record"
    clauses = []
    params: List[Any] = []

    if final_label:
        clauses.append("final_label = ?")
        params.append(final_label)
    if input_type:
        clauses.append("input_type = ?")
        params.append(input_type)

    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    with get_conn() as conn:
        row = conn.execute(query, tuple(params)).fetchone()
    return int(row[0] if row else 0)


def list_records_older_than(cutoff_iso: str, limit: int = 500, offset: int = 0) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
        rows = conn.execute(
            """
            SELECT * FROM inference_record
            WHERE created_at < ?
            ORDER BY created_at ASC
            LIMIT ? OFFSET ?
            """,
            (cutoff_iso, limit, offset),
        ).fetchall()
    return rows


def delete_records_by_ids(record_ids: List[int]) -> int:
    if not record_ids:
        return 0
    placeholders = ",".join(["?"] * len(record_ids))
    with get_conn() as conn:
        cursor = conn.execute(
            f"DELETE FROM inference_record WHERE id IN ({placeholders})",
            tuple(record_ids),
        )
        conn.commit()
    return int(cursor.rowcount or 0)


def count_records_older_than(cutoff_iso: str) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(1) FROM inference_record WHERE created_at < ?",
            (cutoff_iso,),
        ).fetchone()
    return int(row[0] if row else 0)


def check_speaker_exists(speaker_name: str) -> bool:
    """检查说话人名称是否已存在"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(1) FROM speaker_profile WHERE speaker_name = ?",
            (speaker_name,),
        ).fetchone()
    return int(row[0] if row else 0) > 0


def check_embedding_exists(embedding_name: str) -> bool:
    """检查嵌入名称是否已存在"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(1) FROM speaker_profile WHERE embedding_name = ?",
            (embedding_name,),
        ).fetchone()
    return int(row[0] if row else 0) > 0
