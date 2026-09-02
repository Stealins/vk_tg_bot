import socket
import ssl
import json

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

with open('personal_data/token_tg.txt', 'r') as f:
    token = f.read().strip()

with open('personal_data/peer_tg.txt', 'r') as f:
    peer = f.read().strip()


url = 'api.telegram.org'

context = ssl.create_default_context()
secure_sock = context.wrap_socket(sock, server_hostname = url)

path = (
    f'/bot{token}/sendMessage'
    f'chat_id={peer}'
    'text = hello'
)

request = (
    f"POST {path} HTTP/1.1\r\n"
    "Host: api.telegram.org\r\n"
    "Connection: close\r\n"
    "User-Agent: Python-Socket/1.0\r\n"
    "\r\n"
)

try:
    secure_sock.send(request.encode())
    answer = secure_sock.recv(4096)
    print(answer)
except:
    print('Error')