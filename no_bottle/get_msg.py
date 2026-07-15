import json
import requests

with open('getLPserver.json', 'r') as f:
    enter_data = json.load(f)

key = enter_data['response']['key']
server_url = enter_data['response']['server']
ts = enter_data['response']['ts']

while True:
    try:
        r = requests.get(url = server_url, params = {'key' : key, 'v' : 5.199, 'ts' : ts})
        response_data = r.json()
        if response_data['updates']:
            print(response_data['updates'])
        ts = response_data['ts']   
    except requests.exceptions.RequestException as e:
        print('Connection Error', e)
        continue

