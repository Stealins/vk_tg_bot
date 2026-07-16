import requests

with open('personal_data/token_tg.txt', 'r') as f:
    token = f.read()

with open('personal_data/peer_tg.txt', 'r') as f:
    peer = f.read()

data = {'message' : 'hello',
    'peer' : peer,
}

try:
    requests.post(url = f'https://api.telegram.org/bot{token}/messages.sendMessage', data = data) 
except requests.exceptions.RequestException as e:
    print('Error:', e)