"""用户数据库操作"""
import sqlite3
from datetime import datetime
from typing import Optional, Dict, List

from app.repositories.db import get_conn


def create_user(username: str, email: str, password_hash: str, full_name: str = None) -> int:
    """创建新用户"""
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, full_name, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (username, email, password_hash, full_name, datetime.now().isoformat()),
        )
        conn.commit()
        return cursor.lastrowid


def get_user_by_username(username: str) -> Optional[Dict]:
    """根据用户名获取用户"""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, password_hash, full_name, role, is_active, created_at, last_login
            FROM users
            WHERE username = ?
            """,
            (username,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[Dict]:
    """根据邮箱获取用户"""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, password_hash, full_name, role, is_active, created_at, last_login
            FROM users
            WHERE email = ?
            """,
            (email,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """根据ID获取用户"""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, full_name, role, is_active, created_at, last_login
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def update_last_login(user_id: int) -> None:
    """更新最后登录时间"""
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE users
            SET last_login = ?
            WHERE id = ?
            """,
            (datetime.now().isoformat(), user_id),
        )
        conn.commit()


def list_users(limit: int = 50, offset: int = 0) -> List[Dict]:
    """获取用户列表"""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, full_name, role, is_active, created_at, last_login
            FROM users
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return [dict(row) for row in cursor.fetchall()]


def count_users() -> int:
    """统计用户总数"""
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]
