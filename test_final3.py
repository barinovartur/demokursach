from pyrogram import Client, filters
import schedule
import time
import datetime
import json

# Чтение API данных из файла
def read_api_credentials(file_path):
    try:
        with open(file_path, 'r') as f:
            line = f.readline().strip()
            api_id, api_hash = line.split(":")
            return int(api_id), api_hash
    except Exception as e:
        print(f"Failed to read API credentials. Error: {e}")
        exit(1)

# Функция записи логов
def write_log(file_path, log_entry):
    """
    Записывает данные в указанный лог-файл.

    :param file_path: Путь к файлу логов
    :param log_entry: Словарь с данными для записи
    """
    try:
        with open(file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Failed to write log to {file_path}. Error: {e}")

# Загрузка API данных
api_credentials_file = 'C:/Users/Comp/PycharmProjects/pythonProject4/venv/api_credentials.txt'
api_id, api_hash = read_api_credentials(api_credentials_file)
logs_info = 'C:/Users/Comp/PycharmProjects/pythonProject4/venv/logs.json'

# Сообщения для разных флагов
messages = {
    "steam": "Привет! Здесь новости о Steam и интересных предложениях.",
    "crypto": "Добрый день! Узнайте последние новости и тренды из мира криптовалют.",
    "default": "Здравствуйте! У нас есть интересная информация для вас."
}

# Чтение списка разрешенных пользователей из файла
def read_allowed_users(file_path):
    try:
        with open(file_path, 'r') as f:
            # Извлекаем usernames из чатов
            allowed_users = {line.strip().split(":")[0] for line in f if line.strip()}
        return allowed_users
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return set()
    except Exception as e:
        print(f"Failed to read allowed users. Error: {e}")
        return set()

# Функция отправки сообщений
def send_messages():
    """
    Читает список чатов из файла, отправляет сообщения и записывает результаты в лог.
    Сообщения отправляются только пользователям, указанным в файле chats.txt.
    """
    print("Starting send_messages")
    allowed_users = read_allowed_users('C:/Users/Comp/PycharmProjects/pythonProject4/venv/chats.txt')  # Разрешенные пользователи

    try:
        with open('C:/Users/Comp/PycharmProjects/pythonProject4/venv/chats.txt', 'r') as f:
            links_and_flags = [line.strip().split(":") for line in f if line.strip()]
    except FileNotFoundError:
        print("Error: File chats.txt not found.")
        return
    except Exception as e:
        print(f"Failed to read chat links and flags. Error: {e}")
        return

    with Client('my_new_account', api_id, api_hash) as app:
        for entry in links_and_flags:
            if len(entry) != 2:
                write_log(logs_info, {"time": datetime.datetime.now().isoformat(), "username": "N/A", "flag": "N/A", "status": "FAIL", "error": "Invalid entry format"})
                print(f"Invalid entry format: {entry}")
                continue

            link, flag = entry
            username = link.split('/')[-1]  # Извлечение username из ссылки

            # Пропускаем пользователей, которых нет в списке разрешенных
            if username not in allowed_users:
                print(f"User {username} is not in the allowed list. Skipping.")
                continue

            message = messages.get(flag, messages["default"])  # Генерация сообщения по флагу

            try:
                sent_message = app.send_message(username, message)
                if hasattr(sent_message, 'message_id'):
                    write_log(logs_info,
                              {"time": datetime.datetime.now().isoformat(), "username": username, "flag": flag,
                               "status": "SUCCESS", "message_id": sent_message.message_id})
                    print(f"Message successfully sent to {username} with flag '{flag}'")
                else:
                    write_log(logs_info,
                              {"time": datetime.datetime.now().isoformat(), "username": username, "flag": flag,
                               "status": "SUCCESS", "message_id": "UNKNOWN"})
                    print(f"Message sent to {username}, but 'message_id' is missing in response.")
            except Exception as e:
                write_log(logs_info, {"time": datetime.datetime.now().isoformat(), "username": username, "flag": flag,
                                        "status": "FAIL", "error": str(e)})
                print(f"Failed to send message to {username}. Error: {e}")

    print("Finished send_messages")

# Создание клиента для обработки входящих сообщений
app = Client('my_new_account', api_id, api_hash)

@app.on_message(filters.text)  # Обрабатываем все текстовые сообщения
def save_reply(client, message):
    """
    Обрабатывает входящие текстовые сообщения и сохраняет их в отдельный лог.

    :param client: Клиент Pyrogram
    :param message: Сообщение Pyrogram
    """
    # Проверка наличия message_id
    message_id = getattr(message, 'message_id', None)

    from_user = message.from_user.username if message.from_user else str(message.from_user.id)

    # Пропускаем сообщения от пользователей, которых нет в списке разрешенных
    allowed_users = read_allowed_users('C:/Users/Comp/PycharmProjects/pythonProject4/venv/chats.txt')
    if from_user not in allowed_users:
        print(f"Message from {from_user} is ignored (not in allowed list).")
        return

    log_entry = {
        "time": datetime.datetime.now().isoformat(),
        "from_user": from_user,
        "message_id": message_id,  # Добавляем message_id только если он существует
        "message_text": message.text
    }

    write_log('C:/Users/Comp/PycharmProjects/pythonProject4/venv/replies.json', log_entry)
    print(f"Message saved: {log_entry}")

# Запуск немедленной отправки сообщений и основного цикла
send_messages()

# Запуск клиента для обработки событий
app.run()
