# 1. Що це: Модуль безпеки, криптографічного хешування паролів та керування токенами авторизації.
# 2. Для чого: Для захисту облікових даних користувачів і перевірки сесійних Bearer-токенів.
# 3. Призначення: Хешувати паролі з сіллю (SHA-256) та генерувати/валідувати підписані токени доступу.


import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Optional, Dict, Any

SECRET_KEY = "poshta_secret_key_sprint2_hmac_sha256"
TOKEN_EXPIRE_SECONDS = 60 * 60 * 24 * 7  # 7 діб


def get_password_hash(password: str) -> str:
    """Генерує безпечний SHA-256 хеш із сіллю."""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((password + salt).encode("utf-8"))
    return f"{salt}${hash_obj.hexdigest()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Перевіряє, чи введений пароль відповідає збереженому хешу."""
    try:
        salt, stored_hash = hashed_password.split("$")
        check_hash = hashlib.sha256((plain_password + salt).encode("utf-8")).hexdigest()
        return secrets.compare_digest(check_hash, stored_hash)
    except ValueError:
        return False


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(user_id: int, username: str, role: str) -> str:
    """Генерує підписаний токен авторизації (формат JWT HS256) для користувача."""
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + TOKEN_EXPIRE_SECONDS,
    }
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Перевіряє підпис і термін дії токена та повертає декодований payload або None."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
        actual_sig = _b64url_decode(signature_b64)
        if not secrets.compare_digest(expected_sig, actual_sig):
            return None
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        if "exp" in payload and int(time.time()) > int(payload["exp"]):
            return None
        return payload
    except Exception:
        return None