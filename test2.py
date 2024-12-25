from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import json

# Вставьте сюда свой токен
API_TOKEN = "8082807784:AAE3r07nZ_xWvoA9H5p0M54Jy9v7NVlGqF8"

app = Client("my_bot", bot_token=API_TOKEN)

# Структура для хранения базы инфлов
influ_database = {
    "steam": [],
    "crypto": [],
    "other": []
}

# Структура для хранения шаблонов сообщений
templates = {
    "steam": "",
    "crypto": "",
    "other": ""
}

# Главное меню
main_menu = [
    [InlineKeyboardButton("Запуск спама", callback_data="start_spam")],
    [InlineKeyboardButton("Загрузка данных от аккаунта", callback_data="load_account_data")],
    [InlineKeyboardButton("Загрузка базы инфлов", callback_data="load_influ_base")],
    [InlineKeyboardButton("Выбор шаблона", callback_data="choose_template")],
    [InlineKeyboardButton("Посмотреть всех инфлов", callback_data="view_influ")]
]

# Подменю для загрузки базы инфлов
load_influ_base_menu = [
    [InlineKeyboardButton("Стим инфлы", callback_data="load_steam_influ")],
    [InlineKeyboardButton("Крипто инфлы", callback_data="load_crypto_influ")],
    [InlineKeyboardButton("Другие инфлы", callback_data="load_other_influ")]
]

# Подменю для выбора шаблона
choose_template_menu = [
    [InlineKeyboardButton("Стим", callback_data="choose_steam_template")],
    [InlineKeyboardButton("Крипто", callback_data="choose_crypto_template")],
    [InlineKeyboardButton("Другие", callback_data="choose_other_template")]
]


# Основная команда для запуска бота
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply(
        "Добро пожаловать в бот для работы с инфлами!",
        reply_markup=InlineKeyboardMarkup(main_menu)
    )


@app.on_callback_query(filters.regex("start_spam"))
async def start_spam(client, callback_query):
    # Здесь будет логика для запуска спама
    await callback_query.message.edit("Выберите аккаунт для залива (функционал залива будет позже).")


@app.on_callback_query(filters.regex("load_account_data"))
async def load_account_data(client, callback_query):
    await callback_query.message.edit("Введите данные от аккаунта в формате @user:phonenumber:api:hash")


@app.on_callback_query(filters.regex("load_influ_base"))
async def load_influ_base(client, callback_query):
    await callback_query.message.edit(
        "Выберите категорию инфлов для загрузки.",
        reply_markup=InlineKeyboardMarkup(load_influ_base_menu)
    )


@app.on_callback_query(filters.regex("load_steam_influ"))
async def load_steam_influ(client, callback_query):
    await callback_query.message.edit("Введите базу инфлов для Steam (формат: @username)")


@app.on_callback_query(filters.regex("load_crypto_influ"))
async def load_crypto_influ(client, callback_query):
    await callback_query.message.edit("Введите базу инфлов для Crypto (формат: @username)")


@app.on_callback_query(filters.regex("load_other_influ"))
async def load_other_influ(client, callback_query):
    await callback_query.message.edit("Введите базу инфлов для Other (формат: @username)")


@app.on_message(filters.regex(r"^@[\w]+$"))  # Паттерн для @username
async def save_influ(client, message):
    username = message.text.strip()

    # Определяем категорию инфлов, в зависимости от контекста
    if "steam" in message.reply_to_message.text.lower():
        category = "steam"
    elif "crypto" in message.reply_to_message.text.lower():
        category = "crypto"
    elif "other" in message.reply_to_message.text.lower():
        category = "other"
    else:
        await message.reply("Неизвестная категория инфлов. Попробуйте снова.")
        return

    # Добавляем @username в соответствующую категорию
    influ_database[category].append({"username": username, "category_flag": category})

    # Сохраняем инфлы в файл
    with open("C:/Users/Comp/PycharmProjects/pythonProject4/venv/influ_database.json", "w") as f:
        json.dump(influ_database, f)

    await message.reply(f"База инфлов для категории {category} обновлена. Пользователь {username} добавлен.")


@app.on_callback_query(filters.regex("choose_template"))
async def choose_template(client, callback_query):
    await callback_query.message.edit(
        "Выберите категорию для шаблона сообщения.",
        reply_markup=InlineKeyboardMarkup(choose_template_menu)
    )


@app.on_callback_query(filters.regex("choose_steam_template"))
async def choose_steam_template(client, callback_query):
    await callback_query.message.edit("Введите шаблон сообщения для Steam:")


@app.on_callback_query(filters.regex("choose_crypto_template"))
async def choose_crypto_template(client, callback_query):
    await callback_query.message.edit("Введите шаблон сообщения для Crypto:")


@app.on_callback_query(filters.regex("choose_other_template"))
async def choose_other_template(client, callback_query):
    await callback_query.message.edit("Введите шаблон сообщения для Other:")


@app.on_message(filters.text)
async def save_template(client, message):
    # Сохраняем шаблон для соответствующей категории
    if "steam" in message.reply_to_message.text.lower():
        templates["steam"] = message.text
        await message.reply(f"Шаблон для Steam сохранен.")
    elif "crypto" in message.reply_to_message.text.lower():
        templates["crypto"] = message.text
        await message.reply(f"Шаблон для Crypto сохранен.")
    elif "other" in message.reply_to_message.text.lower():
        templates["other"] = message.text
        await message.reply(f"Шаблон для Other сохранен.")
    else:
        await message.reply("Неизвестная категория шаблона. Попробуйте снова.")


@app.on_callback_query(filters.regex("view_influ"))
async def view_influ(client, callback_query):
    # Загружаем базу инфлов из файла
    try:
        with open("influ_database.json", "r") as f:
            influ_database = json.load(f)
    except FileNotFoundError:
        influ_database = {"steam": [], "crypto": [], "other": []}

    # Выводим все инфлы по категориям
    steam_influ = "\n".join([user["username"] for user in influ_database["steam"]]) or "Нет инфлов"
    crypto_influ = "\n".join([user["username"] for user in influ_database["crypto"]]) or "Нет инфлов"
    other_influ = "\n".join([user["username"] for user in influ_database["other"]]) or "Нет инфлов"

    message = f"**Стим инфлы**:\n{steam_influ}\n\n**Крипто инфлы**:\n{crypto_influ}\n\n**Другие инфлы**:\n{other_influ}"

    await callback_query.message.edit(message)


if __name__ == "__main__":
    app.run()
