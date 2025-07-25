# utils/hash_utils.py

import hashlib

def get_hash(text: str) -> str:
    """
    Возвращает SHA256-хеш строки текста.
    Используется для проверки, был ли пост уже обработан.
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
