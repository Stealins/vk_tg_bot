import requests

with open('personal_data/token_tg.txt', 'r') as f:
    token = f.read().strip()

with open('personal_data/peer_tg.txt', 'r') as f:
    peer = f.read().strip()

data = {
    'chat_id': peer,
    'text': 'hello',
}

proxies = {
    'http': 'socks5h://127.0.0.1:10808',
    'https': 'socks5h://127.0.0.1:10808',
}

url = f'https://api.telegram.org/bot{token}/sendMessage'

def send_message_to_telegram(chat_id: int, topic_id: int, text: str, proxies=proxies):
    global token
    
    # URL для запроса к Bot API (токен должен быть определён глобально)
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # Параметры запроса
    data = {
        'chat_id': chat_id,
        'text': text,
        'message_thread_id': topic_id  # именно этот параметр отвечает за топик
    }

    try:
        response = requests.post(url, proxies=proxies, data=data, timeout=10)
        return response.json()
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        return None