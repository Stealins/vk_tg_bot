import json
import requests

with open('personal_data/token.txt', 'r') as f:
    token = f.read()

with open('personal_data/peer_id.txt', 'r') as f:
    peer_id = f.read()

data = {'group_id': 240182411,
        'access_token' : token,
        'v' : 5.199
        }

r = requests.get(url ='https://api.vk.com/method/groups.getLongPollServer', params = data)

with open('no_bottle/getLPserver.json', 'w') as f: 
    data = json.loads(r.text)
    formatted_json = json.dumps(data, indent = 4, ensure_ascii = False)   
    f.write(formatted_json)
