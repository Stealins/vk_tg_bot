import requests
import json
import sys
import signal
import os   
import time
import logging
from datetime import datetime
from logging_config import setup_logging
from getLPserver import get_LP_server
from transfer_msg import send_message_to_telegram   

setup_logging()
logger = logging.getLogger(__name__)

BOT_TOKEN = None
API_URL = None
STATE_FILE = 'personal_data/state.json'
group_id = None
proxies = None
offset = None
UserState = 'Base'
ChatList = {}
CurrentChat = None
server_url = None
key = None
ts = None
lp_available = False
last_save_time = time.time()

class Chat:
    """Класс для хранения информации об одном VK чате и его привязке к Telegram"""

    global group_id
    
    def __init__(self):
        self.peer_id = None                # ID чата в VK
        self.name = None  # Название для отображения
        
        # Куда отправлять в Telegram
        self.tg_chat_id = group_id          # ID Telegram чата/группы
        self.tg_topic_id = None        # ID топика (если есть)
        
        self.created_at = datetime.now().isoformat()
        self.last_activity = datetime.now().isoformat()
        self.is_active = True
        
        # Настройки чата
        self.settings = {
            'notify_about_new_messages': True,
            'notify_about_edits': False,
            'custom_keywords': []
        }
    
    def to_dict(self):
        """Преобразовать в словарь для сохранения"""
        return {
            'peer_id': self.peer_id,
            'name': self.name,
            'tg_chat_id': self.tg_chat_id,
            'tg_topic_id': self.tg_topic_id,
            'created_at': self.created_at,
            'last_activity': self.last_activity,
            'is_active': self.is_active,
            'settings': self.settings
        }
    
    @classmethod
    def from_dict(cls, data):
        """Создать объект из словаря"""
        chat = cls(
            peer_id=data['peer_id'],
            name=data.get('name', ''),
            lp_data=data.get('lp_data', {}),
            tg_chat_id=data.get('tg_chat_id'),
            tg_topic_id=data.get('tg_topic_id')
        )
        chat.created_at = data.get('created_at', chat.created_at)
        chat.last_activity = data.get('last_activity', chat.last_activity)
        chat.is_active = data.get('is_active', True)
        chat.settings = data.get('settings', chat.settings)
        return chat
    
    def update_activity(self):
        """Обновить время активности"""
        self.last_activity = datetime.now().isoformat()
    
    def __repr__(self):
        return f"Chat(peer_id={self.peer_id}, name='{self.name}', tg_chat_id={self.tg_chat_id})"

def get_updates():
    global offset
    try:
        r = requests.get(
            url=f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates',
            proxies=proxies,
            params={'timeout': 25, 'offset': offset},
            timeout=35
        )
        response_data = r.json()
        
        if response_data.get('ok') and response_data.get('result'):
            updates = response_data['result']
            if updates:
                # Берём ID последнего обновления + 1
                last_update_id = updates[-1]['update_id']
                offset = last_update_id + 1
                logger.debug(f"Offset обновлён до {offset} (получено {len(updates)} обновлений)")
        
        return response_data
    
    except requests.exceptions.HTTPError as e:
        logger.error(f"Get updates HTTP error: {e}", exc_info=True)  # e.g., 404 Not Found or 500 Server Error

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Get updates connection Error: {e}", exc_info=True)  # e.g., DNS failure, refused connection

    except requests.exceptions.Timeout as e:
        logger.error(f"Get updates timeout Error: {e}", exc_info=True)  # Request took too long

    except requests.exceptions.RequestException as e:
        logger.error(f"Get updates an ambiguous error occurred: {e}",exc_info=True)

def await_message(url, key, ts):
    try:
        r = requests.get(url=url, params={'key': key,
                                          'v': '5.199',
                                          'ts': ts,
                                          'mode': 2})
        response_data = r.json()
        logger.info('Получен ответ от ВК')
        if 'updates' in response_data and response_data['updates']:
            logger.info('Получен апдейт от ВК!')
            for update in response_data['updates']:   # обрабатываем все обновления
                if update['type'] == 'message_new':
                    msg = update['object']['message']
                    vk_peer_id = msg['peer_id']       # ID чата/пользователя в ВК
                    text = msg['text']

                    # Ищем соответствующий топик в Telegram
                    if vk_peer_id in ChatList:
                        chat_obj = ChatList[vk_peer_id]
                        tg_chat_id = chat_obj.tg_chat_id
                        tg_topic_id = chat_obj.tg_topic_id
                        # Отправляем в Telegram
                        send_message_to_telegram(
                            chat_id=tg_chat_id,
                            topic_id=tg_topic_id,
                            text=text
                        )
                    else:
                        logger.info(f'Нет привязки для peer_id {vk_peer_id}')

        return response_data['ts']

    except requests.exceptions.HTTPError as e:
        logger.error(f"Await message HTTP Error: {e}", exc_info=True)  # e.g., 404 Not Found or 500 Server Error
        return ts
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Await message connection Error: {e}", exc_info=True)  # e.g., DNS failure, refused connection
        return ts

    except requests.exceptions.Timeout as e:
        logger.error(f"Await message timeout Error: {e}", exc_info=True)  # Request took too long
        return ts

    except requests.exceptions.RequestException as e:
        logger.error(f"Await message an ambiguous error occurred: {e}",exc_info=True)
        return ts

def send_message(chat_id, text, reply_markup=None):
    payload = {'chat_id': chat_id, 'text': text}
    if reply_markup:
        payload['reply_markup'] = reply_markup
    try:
        r = requests.post(f'{API_URL}/sendMessage', json=payload)
        return r.json()
    
    except requests.exceptions.HTTPError as e:
        logger.error(f"Send message await message HTTP Error: {e}", exc_info=True)  # e.g., 404 Not Found or 500 Server Error

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Send message await message connection Error: {e}", exc_info=True)  # e.g., DNS failure, refused connection

    except requests.exceptions.Timeout as e:
        logger.error(f"Send message await message timeout Error: {e}", exc_info=True)  # Request took too long

    except requests.exceptions.RequestException as e:
        logger.error(f"Send message await message an ambiguous error occurred: {e}",exc_info=True)


def create_topic(chat_obj):
    global BOT_TOKEN, proxies

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/createForumTopic"
    
    payload = {
        'chat_id': chat_obj.tg_chat_id,
        'name': chat_obj.name
        # Можно добавить icon_color или icon_custom_emoji_id при желании
    }

    try:
        response = requests.post(url, proxies=proxies, json=payload, timeout=10)
        result = response.json()

        if result.get('ok'):
            topic_id = result['result']['message_thread_id']
            chat_obj.tg_topic_id = topic_id   # сохраняем ID топика в объекте
            
            # Отправляем приветственное сообщение в созданный топик
            send_message_to_telegram(
                chat_id=chat_obj.tg_chat_id,
                topic_id=topic_id,
                text=f"📌 Топик для чата «{chat_obj.name}» успешно создан!"
            )
            logger.info(f"✅ Топик создан! ID: {topic_id} для чата {chat_obj.name}")
            return topic_id
        else:
            error_msg = result.get('description', 'Неизвестная ошибка')
            logger.info(f"❌ Ошибка создания топика: {error_msg}")
            return None

    except requests.exceptions.HTTPError as e:
        logger.error(f"Create topic await message HTTP Error: {e}", exc_info=True)  # e.g., 404 Not Found or 500 Server Error

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Create topic await message connection Error: {e}", exc_info=True)  # e.g., DNS failure, refused connection

    except requests.exceptions.Timeout as e:
        logger.error(f"Create topic await message timeout Error: {e}", exc_info=True)  # Request took too long

    except requests.exceptions.RequestException as e:
        logger.error(f"Create topic await message an ambiguous error occurred: {e}",exc_info=True)

def main_menu_markup():
    return {
        'inline_keyboard': [
            [{'text': '➕ Добавить VK-чат', 'callback_data': 'add_chat'}],
        ]
    }

def handle_start(message):
    chat_id = message['chat']['id']
    send_message(
        chat_id,
        'Привет! Это бот для пересылки сообщений из VK в Telegram.',
        reply_markup=main_menu_markup()
    )

def handle_response(response_data):
    global offset
    if response_data:
        if not response_data.get('ok'):
            error_code = response_data.get('error_code')
            description = response_data.get('description')
            print(f"Ошибка {error_code}: {description}")
            return
        
        results = response_data.get('result')
        for result in results:
            if 'callback_query' in result:
                offset = result['update_id'] + 1
                handle_callback(result['callback_query'])

            elif 'message' in result:
                offset = result['update_id'] + 1
                handle_message(result['message'])

def handle_callback(callback_query):
    global offset, UserState
    if callback_query['data'] == 'add_chat':
        UserState = 'waiting_for_chat_name'
        chat_id = callback_query['message']['chat']['id'] 
        send_message(chat_id = chat_id, text = 'Введи название своего чата ВК: ')

def check_vk_token(message , status):
    global offset, UserState
    chat_id = message['chat']['id']
    try:
        with open('personal_data/token.txt', 'r') as f:
            token = f.read()
            if token == '':
                UserState = 'waiting_vk_token'
                send_message(chat_id = chat_id, text = 'Не нашли Ваш токен ВК. Пожалуйста, введите его:')
            if UserState == 'waiting_vk_token':
                with open('personal_data/token.txt', 'r') as f:
                    f.write(message['text'])
            UserState = status

    except FileNotFoundError as e:
        logger.error(f"Папка не найдена: {e}", exc_info=True)
        

def handle_message(message):
    global CurrentChat, offset, UserState, key, ts, server_url
    if message['from']['is_bot']:
        pass

    elif message['text'] == '/start':
        check_vk_token(message, status = 'Basic')
        handle_start(message)
    
    elif UserState == 'waiting_for_chat_name':
        chat_id = message['chat']['id']
        if message['text'] in ChatList:
            send_message(chat_id = chat_id,
                         text = 'Чат с таким именем уже существует. Хотите перезаписать его?',
                         reply_markup = None
                         )
            UserState = 'waiting_for_confirm'
        else:
            CurrentChat = Chat()
            CurrentChat.update_activity()
            CurrentChat.name = message['text']
            UserState = 'waiting_for_chat_peer'
            send_message(chat_id = chat_id,
                         text = 'Введите peer_id для данного чата. Личная переписка: peer_id равен ID пользователя (положительное число).' \
                         'Групповая беседа (чат): peer_id вычисляется по формуле 2000000000 + id_беседы.' \
                         'Например: Если ID беседы — 5, то peer_id будет 2000000005.' \
                         'Сообщество: peer_id равен -id_сообщества (отрицательное число)')
            
    elif UserState == 'waiting_for_chat_peer':
        CurrentChat.peer_id = message['text']
        topic_id = create_topic(CurrentChat)
        if topic_id is not None:
            ChatList[CurrentChat.peer_id] = CurrentChat
            # остальной код...
        else:
            send_message(chat_id, "Не удалось создать топик. Проверьте права бота и что группа является форумом.")
        save_state()
        await_message(url = server_url, key = key, ts = ts)
        CurrentChat = None
        UserState = 'Base'


def save_state():
    """Сохраняет текущее состояние бота в JSON-файл."""
    global ChatList, offset, ts, key, server_url

    state = {
        'chats': {},          # peer_id -> данные чата
        'offset': offset,
        'ts': ts,
        'key': key,
        'server_url': server_url,
        'saved_at': datetime.now().isoformat()
    }

    # Преобразуем объекты Chat в словари
    for peer_id, chat_obj in ChatList.items():
        state['chats'][str(peer_id)] = chat_obj.to_dict()

    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=4)
        logger.info(f"[{datetime.now().isoformat()}] Состояние сохранено в {STATE_FILE}")
    except Exception as e:
        logger.error(f"Ошибка сохранения состояния: {e}", exc_info=True)

def load_state():
    """Загружает состояние из JSON-файла, если он существует."""
    global ChatList, offset, ts, key, server_url

    if not os.path.exists(STATE_FILE):
        logger.info("Файл состояния не найден, начинаем с чистого листа.")
        return

    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            state = json.load(f)

        # Восстанавливаем чаты
        ChatList.clear()
        for peer_id_str, chat_dict in state.get('chats', {}).items():
            peer_id = int(peer_id_str)  # ключи храним как строки
            chat = Chat.from_dict(chat_dict)
            ChatList[peer_id] = chat

        # Восстанавливаем остальные параметры
        offset = state.get('offset')
        ts = state.get('ts')
        key = state.get('key')
        server_url = state.get('server_url')

        logger.info(f"Состояние загружено из {STATE_FILE}, чатов: {len(ChatList)}")
    except Exception as e:
        logger.error(f"Ошибка загрузки состояния: {e}")
        # При ошибке лучше начать заново, но можно и оставить пустым

def stop_bot(signum=None, frame=None):
    """
    Останавливает бот, сохраняя состояние перед выходом.
    Можно вызывать как обработчик сигнала или вручную.
    """
    logger.info("\nПолучен сигнал завершения. Сохраняем состояние...")
    save_state()
    logger.info("Бот остановлен.")
    sys.exit(0)


def bot():
    global server_url, key, ts, lp_available, offset, last_save_time
    while True:
        try:
            # 1. Обработка команд из Telegram
            response_data = get_updates()
            if response_data:
                handle_response(response_data)

            # 2. Если Long Poll доступен – получаем сообщения из VK
            if lp_available and server_url and key and ts:
                ts = await_message(url = server_url, key = key, ts = ts)

            # 3. Автосохранение раз в минуту
            if time.time() - last_save_time > 60:
                save_state()
                last_save_time = time.time()

            time.sleep(0.5)  # снижаем нагрузку на CPU

        except KeyboardInterrupt:
            stop_bot()
        except Exception as e:
            logger.info(f"Ошибка в основном цикле: {e}", exc_info=True)
            # При ошибке Long Poll можно попробовать переполучить сервер
            if 'lp' in str(e).lower() or 'connection' in str(e).lower():
                try:
                    new_server, new_key, new_ts = get_LP_server()
                    server_url, key, ts = new_server, new_key, new_ts
                    lp_available = True
                    logger.info("Long Poll сервер обновлён")
                except Exception as lp_err:
                    logger.error(f"Не удалось обновить Long Poll: {lp_err}", exc_info=True)
                    lp_available = False
            time.sleep(5)  # пауза перед повторной попыткой

def main():
    global server_url, key, ts, lp_available, BOT_TOKEN, API_URL, group_id, proxies

    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, stop_bot)
    signal.signal(signal.SIGTERM, stop_bot)

    # 1. Проверка токена Telegram
    if not os.path.exists('personal_data/token_tg.txt') or not open('personal_data/token_tg.txt').read().strip():
        logger.fatal("Ошибка: не найден токен Telegram. Поместите его в personal_data/token_tg.txt")
        sys.exit(1)

    if not os.path.exists('personal_data/group_id.txt') or not open('personal_data/group_id.txt').read().strip():
        logger.error("Ошибка: не найден id вашей супергруппы. Поместите его в personal_data/group_id.txt")
        sys.exit(2)
    

    # 1.1 Если с token_tg все впорядке, считываем токен и устанавливаем прокси
    with open('personal_data/token_tg.txt', 'r') as f:
        BOT_TOKEN = f.read()
        API_URL = f'https://api.telegram.org/bot{BOT_TOKEN}'

    #id группы, куда был добавлен бот
    with open('personal_data/group_id.txt', 'r') as f:
        group_id = f.read()
    
    proxies = {
        'http': 'socks5h://127.0.0.1:10808',
        'https': 'socks5h://127.0.0.1:10808',
    }

    offset = None
    # Здесь будут отобраены активные сессии юзеров    
    UserState = 'Base'
    ChatList = {}
    CurrentChat = None
    lp_available = False

    # 2. Загрузка состояния (восстанавливаем ChatList, offset)
    load_state()

    # 3. Пытаемся получить параметры Long Poll
    try:
        server_url, key, ts = get_LP_server()
        lp_available = True
        logger.info("Long Poll сервер успешно инициализирован")
        if not lp_available:
            logger.error("Не удалось получить Long Poll сервер. Проверьте VK-токен.")
    except Exception as e:
        logger.error(f"Ошибка инициализации Long Poll: {e}")

    # 4. Запуск основного цикла
    bot()

if __name__ == "__main__":
    main()
