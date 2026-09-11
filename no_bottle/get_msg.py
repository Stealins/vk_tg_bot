import json
import requests
from transfer_msg import send_message_to_telegram

with open('personal_data/getLPserver.json', 'r') as f:
    enter_data = json.load(f)

with open('personal_data/group_id.txt', 'r') as f:
    group_id = f.read()

key = enter_data['response']['key']
server_url = enter_data['response']['server']
ts = enter_data['response']['ts']



with open('personal_data/peer_tg.txt', 'r') as f:
    peer = f.read().strip()

def await_message(url = server_url, key = key, ts = ts):
    global group_id
    while True:
        try:
            r = requests.get(url = server_url, params = {'key' : key, 'v' : 5.199, 'ts' : ts})
            response_data = r.json()
            if response_data['updates']:
                update = response_data['updates'][0]
                if update['type'] == 'message_new':

                    data = {
                            'chat_id': peer,
                            'text': f'{update['object']['message']['text']}',
                            }

                    send_message_to_telegram(chat_id = group_id, )
                    
            ts = response_data['ts']   
        except requests.exceptions.RequestException as e:
            print('Connection Error', e)
            continue

