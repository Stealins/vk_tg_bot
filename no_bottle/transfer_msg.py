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

def send_message_to_telegram(url = url, data = data, proxies = proxies):
    try:
        response = requests.post(url, proxies=proxies, data=data, timeout=10)
        print('Status:', response.status_code)
        print('Response:', response.json())
    except requests.exceptions.RequestException as e:
        print('Error:', e) 