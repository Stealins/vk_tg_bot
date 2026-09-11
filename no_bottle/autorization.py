import hashlib
import base64
import secrets
import string
import requests
import logging
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def creating_codes():
    global code_verifier, code_challenge
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


CLIENT_ID = 2685278
 
def autorization():
    try:
        """
        Формирует ссылку для авторизации по Implicit Flow.
        Токен приходит сразу в адресной строке после редиректа,
        PKCE здесь не нужен.
        """
        global access_token
    
        auth_url = (
            f"https://oauth.vk.com/authorize"
            f"?client_id={CLIENT_ID}"
            f"&display=page"
            f"&redirect_uri=https://oauth.vk.com/blank.html"
            f"&scope=messages,offline"
            f"&response_type=token"
            f"&v=5.199"
        )
    
        # ===== ВОТ ЭТА СТРОКА ВЫВОДИТ ССЫЛКУ =====
        print("\n" + "=" * 70)
        print("📋 Ссылка для авторизации (скопируйте и откройте в браузере):")
        print("=" * 70)
        print(auth_url)
        print("=" * 70)
        print("После авторизации браузер перейдёт на blank.html#access_token=...")
        print("Скопируйте значение access_token из адресной строки")
        print("=" * 70 + "\n")
    
        access_token = input("Введите access_token из URL: ").strip()
    
        # Сохраняем
        with open('personal_data/access_token.txt', 'w') as f:
            f.write(access_token)
    
        logger.info("✅ access_token сохранён")
        return access_token
    
    except requests.exceptions.HTTPError as e:
        logger.error(f"Create topic await message HTTP Error: {e}", exc_info=True)  # e.g., 404 Not Found or 500 Server Error

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Create topic await message connection Error: {e}", exc_info=True)  # e.g., DNS failure, refused connection

    except requests.exceptions.Timeout as e:
        logger.error(f"Create topic await message timeout Error: {e}", exc_info=True)  # Request took too long

    except requests.exceptions.RequestException as e:
        logger.error(f"Create topic await message an ambiguous error occurred: {e}",exc_info=True)
    

autorization()
        

    