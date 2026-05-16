"""用户认证服务"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

from app.repositories.user_repo import (
    create_user,
    get_user_by_username,
    get_user_by_email,
    get_user_by_id,
    update_last_login,
)


# 简单的会话存储（生产环境应使用Redis等）
_sessions: Dict[str, Dict] = {}


def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return hash_password(password) == password_hash


def generate_token() -> str:
    """生成会话令牌"""
    return secrets.token_urlsafe(32)


def register_user(username: str, email: str, password: str, full_name: str = None) -> Tuple[bool, str]:
    """注册新用户"""
    # 验证用户名
    if len(username) < 3:
        return False, "用户名至少3个字符"
    
    if get_user_by_username(username):
        return False, "用户名已存在"
    
    # 验证邮箱
    if not email or "@" not in email:
        return False, "邮箱格式不正确"
    
    if get_user_by_email(email):
        return False, "邮箱已被注册"
    
    # 验证密码
    if len(password) < 6:
        return False, "密码至少6个字符"
    
    # 创建用户
    try:
        password_hash = hash_password(password)
        user_id = create_user(username, email, password_hash, full_name)
        return True, f"注册成功，用户ID: {user_id}"
    except Exception as e:
        return False, f"注册失败: {str(e)}"


def login_user(username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """用户登录"""
    user = get_user_by_username(username)
    
    if not user:
        return False, "用户名或密码错误", None
    
    if not user.get("is_active"):
        return False, "账号已被禁用", None
    
    if not verify_password(password, user["password_hash"]):
        return False, "用户名或密码错误", None
    
    # 生成会话令牌
    token = generate_token()
    
    # 存储会话
    _sessions[token] = {
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(days=7),
    }
    
    # 更新最后登录时间
    update_last_login(user["id"])
    
    # 返回用户信息（不包含密码）
    user_info = {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "full_name": user.get("full_name"),
        "role": user["role"],
    }
    
    return True, token, user_info


def verify_token(token: str) -> Optional[Dict]:
    """验证令牌"""
    session = _sessions.get(token)
    
    if not session:
        return None
    
    # 检查是否过期
    if datetime.now() > session["expires_at"]:
        del _sessions[token]
        return None
    
    return session


def logout_user(token: str) -> bool:
    """用户登出"""
    if token in _sessions:
        del _sessions[token]
        return True
    return False


def get_current_user(token: str) -> Optional[Dict]:
    """获取当前用户信息"""
    session = verify_token(token)
    
    if not session:
        return None
    
    user = get_user_by_id(session["user_id"])
    
    if not user:
        return None
    
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "full_name": user.get("full_name"),
        "role": user["role"],
    }
