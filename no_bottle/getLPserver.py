import json
import requests
import asyncio
import logging
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

def get_LP_server():
    with open('personal_data/token.txt', 'r') as f:
        token = f.read().strip()

    data = {
        'access_token': token,
        'v': 5.199
    }

    r = requests.get(url='https://api.vk.com/method/messages.getLongPollServer', params=data)
    
    with open('personal_data/getLPserver.json', 'w') as f:
        response_data = json.loads(r.text)
        formatted_json = json.dumps(response_data, indent=4, ensure_ascii=False)
        f.write(formatted_json)

    if 'response' in response_data:
        server_url = response_data['response']['server']
        if not server_url.startswith(('http://', 'https://')):
            server_url = 'https://' + server_url
        key = response_data['response']['key']
        ts = response_data['response']['ts']
        return [server_url, key, ts]
    else:
        # Если ошибка — возвращаем None, чтобы вызывающий код мог это обработать
        logger.error(f"VK API вернул ошибку: {response_data}")
        return None


