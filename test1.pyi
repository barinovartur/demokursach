from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import os
import re

# Ваш API ID, API Hash и токен бота
api_id = '23529309'  # Введите свой API ID
api_hash = '393fc4549c67b351e83a06c3d6f8560b'  # Введите свой API Hash
bot_token = '8082807784:AAE3r07nZ_xWvoA9H5p0M54Jy9v7NVlGqF8'  # Введите свой токен бота

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Хранилище данных
accounts = []  # Список аккаунтов для спама
api_hashes = []  # Список для хранения API и hash
infle_data = {"steam": [], "crypto": [], "other": []}  # Инфлы по категориям
templates = {"steam": "", "crypto": "", "other": ""}  # Шаблоны для сообщений

account_file = "accounts.txt"  # Файл для сохранения аккаунтов
session_dir = "sessions"  # Папка для хранения сессий
os.makedirs(session_dir, exist_ok=True)  # Создаём папку для сессий, если её нет

# Функция для создания кнопки "Назад" в меню
def back_button():
    return InlineKeyboardButton("Назад", callback_data="back_to_main_menu")

# Проверка корректности введённых данных
def validate_account_data(data):
    # Шаблон: @username:phonenumber:api:hash
    pattern = r"^@[\w\d_]+:\+?\d+:\d+:[a-fA-F0-9]{32}$"
    return re.match(pattern, data)

# Сохранение аккаунта в файл
def save_account_to_file(account_data):
    try:
        with open(account_file, "a") as f:
            f.write(account_data + "\n")
        return True
    except Exception as e:
        return f"Ошибка записи в файл: {e}"

# Функция для сохранения сессии аккаунта
def save_account_session(account_data, category):
    try:
        # Определяем путь к файлу сессии для указанной категории
        session_file = os.path.join(session_dir, f"{category}_session.txt")
        with open(session_file, "a") as f:
            f.write(account_data + "\n")
        return True
    except Exception as e:
        return f"Ошибка записи в файл сессии: {e}"

# Главная кнопка
@app.on_message(filters.command('start'))
async def start(client, message):
    main_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton("1) Запуск спама", callback_data="spam_start")],
        [InlineKeyboardButton("2) Загрузка API и Hash", callback_data="upload_api_hash")],
        [InlineKeyboardButton("3) Загрузка базы инфлов", callback_data="upload_inflows")],
        [InlineKeyboardButton("4) Выбор шаблона", callback_data="choose_template")],
        [InlineKeyboardButton("5) Посмотреть всех инфлов", callback_data="view_inflows")]
    ])
    await message.reply("Главное меню", reply_markup=main_menu)

# Обработчик callback запросов
@app.on_callback_query()
async def handle_callback(client, callback_query):
    data = callback_query.data

    if data == "spam_start":
        # Меню для запуска спама
        spam_menu = InlineKeyboardMarkup([
            [InlineKeyboardButton("1.1) Выбор аккаунта", callback_data="choose_account")],
            [back_button()]  # Кнопка "Назад"
        ])
        await callback_query.message.edit_text("Выберите аккаунт для спама:", reply_markup=spam_menu)

    elif data == "upload_api_hash":
        # Меню для загрузки API и Hash
        await callback_query.message.edit_text("Загрузите API и Hash аккаунта в формате .txt.", reply_markup=InlineKeyboardMarkup([[back_button()]]))

    elif data == "upload_inflows":
        # Меню для загрузки инфлов
        inflow_menu = InlineKeyboardMarkup([
            [InlineKeyboardButton("Стим инфлы", callback_data="upload_steam_inflows")],
            [InlineKeyboardButton("Крипто инфлы", callback_data="upload_crypto_inflows")],
            [InlineKeyboardButton("Другие инфлы", callback_data="upload_other_inflows")],
            [back_button()]  # Кнопка "Назад"
        ])
        await callback_query.message.edit_text("Выберите категорию для загрузки инфлов:", reply_markup=inflow_menu)

    elif data == "choose_template":
        # Меню для выбора шаблона
        template_menu = InlineKeyboardMarkup([
            [InlineKeyboardButton("Стим", callback_data="choose_steam_template")],
            [InlineKeyboardButton("Крипто", callback_data="choose_crypto_template")],
            [InlineKeyboardButton("Другие", callback_data="choose_other_template")],
            [back_button()]  # Кнопка "Назад"
        ])
        await callback_query.message.edit_text("Выберите категорию шаблона:", reply_markup=template_menu)

    elif data == "view_inflows":
        # Вывод всех инфлов
        all_inflows = "\n".join([
            f"Стим: {', '.join(infle_data['steam'])}",
            f"Крипто: {', '.join(infle_data['crypto'])}",
            f"Другие: {', '.join(infle_data['other'])}"
        ])
        await callback_query.message.edit_text(f"Все инфлы:\n{all_inflows}", reply_markup=InlineKeyboardMarkup([[back_button()]]))

    elif data == "upload_steam_inflows":
        # Загрузка стим инфлов
        await callback_query.message.edit_text("Загрузите файл с инфлами для Steam в формате .txt.", reply_markup=InlineKeyboardMarkup([[back_button()]]))

    elif data == "upload_crypto_inflows":
        # Загрузка крипто инфлов
        await callback_query.message.edit_text("Загрузите файл с инфлами для Crypto в формате .txt.", reply_markup=InlineKeyboardMarkup([[back_button()]]))

    elif data == "upload_other_inflows":
        # Загрузка других инфлов
        await callback_query.message.edit_text("Загрузите файл с инфлами для Other в формате .txt.", reply_markup=InlineKeyboardMarkup([[back_button()]]))

    elif data == "back_to_main_menu":
        # Удаление предыдущего сообщения перед возвратом в главное меню
        await callback_query.message.delete()  # Удаляем предыдущее сообщение
        await start(client, callback_query.message)  # Возвращаем в главное меню

@app.on_message(filters.text)
async def handle_text(client, message):
    # Обработка текста пользователя для загрузки API и Hash, инфлов или шаблонов
    if message.text.endswith('.txt'):
        if 'api' in message.text.lower():
            # Пример добавления API и Hash
            account_data = message.text.strip()  # Данные аккаунта
            if validate_account_data(account_data):
                inflo_category = "steam"  # Пример категории
                infle_data[inflo_category].append(account_data)
                # Сохраняем данные в файл
                result = save_account_to_file(account_data)
                if result == True:
                    result = save_account_session(account_data, inflo_category)
                    if result == True:
                        await message.reply(f"Данные аккаунта успешно загружены в категорию {inflo_category}!")
                    else:
                        await message.reply(f"Ошибка записи в файл сессии: {result}")
                else:
                    await message.reply(f"Ошибка записи в файл: {result}")
            else:
                await message.reply("Неверный формат данных. Убедитесь, что данные соответствуют шаблону: @username:phonenumber:api:hash.")
        elif 'steam' in message.text.lower():
            # Пример добавления инфлов Steam
            infle_data["steam"].append(message.text.strip())
            await message.reply("Steam инфлы загружены!")
        elif 'crypto' in message.text.lower():
            # Пример добавления инфлов Crypto
            infle_data["crypto"].append(message.text.strip())
            await message.reply("Crypto инфлы загружены!")
        elif 'other' in message.text.lower():
            # Пример добавления инфлов Other
            infle_data["other"].append(message.text.strip())
            await message.reply("Other инфлы загружены!")
        else:
            await message.reply("Неверный формат файла.")
    else:
        if "Введите сообщение для" in message.text:
            category = message.text.split(" ")[-2].lower()  # Определение категории
            templates[category] = message.text  # Сохраняем шаблон
            await message.reply(f"Шаблон для {category} сохранён!")

# Запуск бота
app.run()
