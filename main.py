from pyrogram import Client
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
def write_log(username, flag, status, error=None):
    """
    Записывает логи об отправленных сообщениях в файл logs.json и отправляет их второму боту.
    """
    log_entry = {
        "time": datetime.datetime.now().isoformat(),
        "username": username,
        "flag": flag,
        "status": status,
        "error": error
    }

    # Сохраняем в JSON-лог
    try:
        with open('logs.json', 'a') as log_file:
            log_file.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Failed to write log to file. Error: {e}")

    # Отправляем лог второму боту
    send_log_to_bot(log_entry)

# Функция для отправки логов второму боту
def send_log_to_bot(log_entry):
    try:
        # Подключаемся ко второму боту
        with Client('log_bot', api_id, api_hash, bot_token=second_bot_token) as log_app:
            message = f"""
📋 **Лог сообщения:**
🕒 Время: {log_entry['time']}
👤 Пользователь: {log_entry['username']}
🏷️ Флаг: {log_entry['flag']}
📌 Статус: {log_entry['status']}
❗ Ошибка: {log_entry['error'] or 'Нет'}
"""
            log_app.send_message(second_bot_chat_id, message)
    except Exception as e:
        print(f"Failed to send log to bot. Error: {e}")

# Загрузка API данных
api_credentials_file = 'C:/Users/Comp/PycharmProjects/pythonProject4/venv/api_credentials.txt'
api_id, api_hash = read_api_credentials(api_credentials_file)

# Токен второго бота и ID чата для логов
second_bot_token = "7858171694:AAG-r3buBbrLZ7HdlNrHy0YkUPo8LdnFKos"  # Токен второго бота
second_bot_chat_id = "1002342514963"  # ID чата, куда будут отправляться логи

# Сообщения для разных флагов
messages = {
    "steam": "Привет! Здесь новости о Steam и интересных предложениях.",
    "crypto": "Добрый день! Узнайте последние новости и тренды из мира криптовалют.",
    "default": "Здравствуйте! У нас есть интересная информация для вас."
}

# Функция отправки сообщений
def send_messages():
    """
    Читает список чатов из файла, отправляет сообщения и записывает результаты в лог.
    """
    print("Starting send_messages")
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
                write_log("N/A", "N/A", "FAIL", "Invalid entry format")
                print(f"Invalid entry format: {entry}")
                continue

            link, flag = entry
            username = link.split('/')[-1]  # Извлечение username из ссылки
            message = messages.get(flag, messages["default"])  # Генерация сообщения по флагу

            try:
                app.send_message(username, message)
                write_log(username, flag, "SUCCESS")
                print(f"Message successfully sent to {username} with flag '{flag}'")
            except Exception as e:
                write_log(username, flag, "FAIL", str(e))
                print(f"Failed to send message to {username}. Error: {e}")

    print("Finished send_messages")

# Запуск немедленной отправки и расписания
send_messages()
schedule.every(10).minutes.do(send_messages)  # Повторять каждые 10 минут

# Основной цикл для выполнения задач по расписанию
while True:
    schedule.run_pending()
    time.sleep(60)
