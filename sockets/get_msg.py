import socket
import ssl
import json

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

with open('sockets/getLPserver.json', 'r') as f:
    enter_data = json.load(f)

host = enter_data['response']['server']
key = enter_data['response']['key']
ts = enter_data['response']['ts']

sock.connect(host = host, port = 443)

context = ssl.create_default_context()
secure_sock =context.wrap_socket(sock, )