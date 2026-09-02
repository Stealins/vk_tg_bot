import socket
import ssl

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

url = 'api.vk.com'
port = 443

sock.connect((url, port))

# оборачиваем в SSL чтобы установилось HTTPS соединение (при отправке запросов на сервер)
context = ssl.create_default_context()
secure_sock = context.wrap_socket(sock, server_hostname= url)

with open('personal_data/token.txt', 'r') as f:
    token = f.read()

with open('personal_data/peer_id.txt', 'r') as f:
    peer_id = f.read()

path = (
    '/method/groups.getLongPollServer'
    "?group_id=240182411"
    f"&access_token={token}"
    "&v=5.199"
)

request = (
    f"GET {path} HTTP/1.1\r\n"
    "Host: api.vk.com\r\n"
    "Connection: close\r\n"
    "User-Agent: Python-Socket/1.0\r\n"
    "\r\n"
)

# 3. Отправляем
secure_sock.send(request.encode())

# Открываем файл для записи
with open('sockets/getLPserver.json', 'w', encoding='utf-8') as f:
    
    first_chunk = True
    while True:
        chunk = secure_sock.recv(4096)
        if not chunk:
            break
        
        # Декодируем и пишем
        text = chunk.decode('utf-8')
        # Убираем HTTP-заголовки только в первом чанке
        if first_chunk:
            header_end = text.find('\r\n\r\n')
            if header_end != -1:
                text = text[header_end + 4:]
            first_chunk = False
        
        f.write(text)

secure_sock.close()




