import hashlib
import secrets

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