import json
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from telegram import Bot
from telegram.ext import Updater, CommandHandler
import threading

# Константы
BOT_TOKEN = "7858171694:AAG-r3buBbrLZ7HdlNrHy0YkUPo8LdnFKos"
LOGS_FILE = "C:/Users/Comp/PycharmProjects/pythonProject4/venv/logs.json"
REPLIES_FILE = "C:/Users/Comp/PycharmProjects/pythonProject4/venv/replies.json"
CHAT_ID = '-1002342514963'
# Инициализация бота
bot = Bot(token=BOT_TOKEN)

# Функция для отправки сообщения в Telegram
def send_message(message):
    bot.send_message(chat_id=CHAT_ID, text=message)

# Функция для чтения данных из JSON файла
def read_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Обработчик событий для отслеживания изменений в файлах
class LogHandler(FileSystemEventHandler):
    def __init__(self, file_path, callback):
        self.file_path = file_path
        self.callback = callback
        self.last_position = 0

    def on_modified(self, event):
        if event.src_path == self.file_path:
            # Чтение новых данных из файла
            with open(self.file_path, 'r') as file:
                # Перемещаемся к последней позиции и считываем только новые строки
                file.seek(self.last_position)
                new_data = file.read()
                if new_data:
                    self.callback(new_data)
                self.last_position = file.tell()

# Функция для обработки новых данных из logs.json
def process_logs_data(data):
    logs = json.loads(data)
    for log in logs:
        log_message = f"Время: {log['time']}\nПользователь: {log['username']}\nСтатус: {log['status']}\n"
        send_message(log_message)

# Функция для обработки новых данных из replies.json
def process_replies_data(data):
    replies = json.loads(data)
    for reply in replies:
        reply_message = f"Время: {reply['time']}\nОт: {reply['from_user']}\nСообщение: {reply['message_text']}\n"
        send_message(reply_message)

# Функция для отслеживания файлов
def watch_files():
    log_handler = LogHandler(LOGS_FILE, process_logs_data)
    reply_handler = LogHandler(REPLIES_FILE, process_replies_data)

    # Создание наблюдателя за изменениями в файлах
    observer = Observer()
    observer.schedule(log_handler, path='.', recursive=False)
    observer.schedule(reply_handler, path='.', recursive=False)

    # Запуск наблюдателя в отдельном потоке
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Основная функция бота
def start(update, context):
    update.message.reply_text('Привет! Я отслеживаю изменения в логах и сообщениях.')

def main():
    # Инициализация бота
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Регистрация команд
    dispatcher.add_handler(CommandHandler("start", start))

    # Запуск бота в отдельном потоке
    threading.Thread(target=updater.start_polling).start()

    # Запуск наблюдателя за файлами
    watch_files()

if __name__ == '__main__':
    main()
