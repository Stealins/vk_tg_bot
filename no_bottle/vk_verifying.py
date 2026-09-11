import hashlib
import base64
import secrets
import string
import logging
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# 1. Генерируем code_verifier (строка из 64 безопасных символов)
allowed_chars = string.ascii_letters + string.digits + "-._~"
code_verifier = ''.join(secrets.choice(allowed_chars) for _ in range(64))
with open('personal_data/code_verifier.txt', 'w') as f:
    f.write(code_verifier)

# 2. Вычисляем SHA-256 хеш от code_verifier
sha256_hash = hashlib.sha256(code_verifier.encode('utf-8')).digest()

# 3. Кодируем хеш в Base64URL (и убираем padding '=')
code_challenge = base64.urlsafe_b64encode(sha256_hash).decode('utf-8').rstrip("=")
with open('personal_data/code_challenge.txt', 'w') as f:
    f.write(code_challenge)
