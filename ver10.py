from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from PIL import Image
import zipfile
import os
import tempfile
import logging
from io import BytesIO

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageOverlayBot:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.background_images = []  # Список фонов
        self.overlay_images = []  # Список шаблонов
        self.result_images = []  # Список для результатов
        self.expected_type = None  # Ожидаемый тип файлов
        self.setup_handlers()

    def setup_handlers(self):
        # Обработчики команд и сообщений
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        self.application.add_handler(MessageHandler(filters.Document.MimeType("application/zip"), self.handle_zip))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.application.add_handler(MessageHandler(filters.Document.MimeType("image/png"), self.handle_png_document))

    async def start(self, update: Update, context: CallbackContext):
        """Главное меню."""
        keyboard = [
            [InlineKeyboardButton("Отправить фоны", callback_data="send_background")],
            [InlineKeyboardButton("Отправить шаблоны", callback_data="send_overlay")],
            [InlineKeyboardButton("Генерировать изображения", callback_data="generate_images")],
            [InlineKeyboardButton("Очистить все", callback_data="clear_all")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.message:
            # Обработка команды /start
            await update.message.reply_text("Добро пожаловать! Выберите одно из действий ниже:", reply_markup=reply_markup)
        elif update.callback_query:
            # Обработка кнопки "Вернуться в главное меню"
            await update.callback_query.message.edit_text("Добро пожаловать! Выберите одно из действий ниже:", reply_markup=reply_markup)

    def create_main_menu_button(self):
        """Создает клавиатуру с кнопкой возврата в главное меню."""
        keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back_to_main_menu")]]
        return InlineKeyboardMarkup(keyboard)

    async def button_handler(self, update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        message = query.message

        if query.data == "send_background":
            self.expected_type = 'background'
            reply_markup = self.create_main_menu_button()  # Добавляем кнопку возврата в главное меню
            await message.edit_text("Пожалуйста, отправьте ZIP архив с фонами или изображения (форматы: PNG, JPG).",
                                    reply_markup=reply_markup)

        elif query.data == "send_overlay":
            self.expected_type = 'overlay'
            reply_markup = self.create_main_menu_button()  # Добавляем кнопку возврата в главное меню
            await message.edit_text("Пожалуйста, отправьте ZIP архив с шаблонами или изображения (форматы: PNG, JPG).",
                                    reply_markup=reply_markup)

        elif query.data == "generate_images":
            if self.background_images and self.overlay_images:
                await message.edit_text("Генерация изображений...")
                await self.generate_images(message)
            else:
                await message.edit_text(
                    "Не все изображения получены. Пожалуйста, отправьте архивы с фонами и шаблонами.")

        elif query.data == "clear_all":
            self.background_images = []
            self.overlay_images = []
            await message.edit_text("Все изображения и настройки очищены. Пожалуйста, отправьте новые архивы.")

        elif query.data == "back_to_main_menu":
            await self.start(update, context)

        elif query.data == "send_as_zip":
            await self.send_images_as_zip(message)

        elif query.data == "send_individually":
            await self.send_images_individually(message)

    async def handle_zip(self, update: Update, context: CallbackContext):
        file = update.message.document
        file_info = await file.get_file()
        file_bytes = await file_info.download_as_bytearray()

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                with zipfile.ZipFile(BytesIO(file_bytes), 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                if self.expected_type == 'background':
                    await self.process_background_zip(temp_dir, update)
                elif self.expected_type == 'overlay':
                    await self.process_overlay_zip(temp_dir, update)

            except zipfile.BadZipFile:
                await update.message.reply_text("Ошибка: это не ZIP файл или файл поврежден.")
            except Exception as e:
                logger.error(f"Ошибка при обработке ZIP файла: {e}")

    async def handle_photo(self, update: Update, context: CallbackContext):
        file = update.message.photo[-1]  # Берем самое большое фото
        file_info = await file.get_file()
        file_path = os.path.join(tempfile.gettempdir(), f"temp_{file.file_id}.jpg")
        await file_info.download_to_drive(file_path)

        # Проверяем тип и добавляем фото в соответствующий список
        if self.expected_type == 'background':
            self.background_images.append(Image.open(file_path))
            reply_markup = self.create_main_menu_button()  # Добавляем кнопку возврата в главное меню
            await update.message.reply_text("Фон получен.", reply_markup=reply_markup)
        else:
            reply_markup = self.create_main_menu_button()  # Добавляем кнопку возврата в главное меню
            await update.message.reply_text("Ошибка: фото принимаются только для фонов.", reply_markup=reply_markup)

    async def handle_png_document(self, update: Update, context: CallbackContext):
        """Обработка отправленных PNG-файлов как документов."""
        if self.expected_type != 'overlay':
            reply_markup = self.create_main_menu_button()  # Добавляем кнопку возврата в главное меню
            await update.message.reply_text("Ошибка: PNG файлы принимаются только для шаблонов.", reply_markup=reply_markup)
            return

        file = update.message.document
        file_info = await file.get_file()
        file_path = os.path.join(tempfile.gettempdir(), f"overlay_{file.file_id}.png")
        await file_info.download_to_drive(file_path)

        self.overlay_images.append(Image.open(file_path))
        reply_markup = self.create_main_menu_button()  # Добавляем кнопку возврата в главное меню
        await update.message.reply_text("Шаблон (PNG) получен.", reply_markup=reply_markup)

    async def process_background_zip(self, temp_dir: str, update: Update):
        found_backgrounds = False
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            if filename.lower().endswith(('png', 'jpg', 'jpeg')):
                try:
                    image = Image.open(file_path)
                    self.background_images.append(image)
                    found_backgrounds = True
                except Exception as e:
                    logger.error(f"Ошибка при открытии файла {filename}: {e}")

        if found_backgrounds:
            reply_markup = self.create_main_menu_button()  # Добавляем кнопку возврата в главное меню
            await update.message.reply_text(f"Фоны получены, всего фонов: {len(self.background_images)}.", reply_markup=reply_markup)
        else:
            reply_markup = self.create_main_menu_button()  # Добавляем кнопку возврата в главное меню
            await update.message.reply_text("Не было найдено фонов в архиве.", reply_markup=reply_markup)

    async def process_overlay_zip(self, temp_dir: str, update: Update):
        found_overlay = False
        for filename in os.listdir(temp_dir):
            if filename.lower().endswith('.png'):
                try:
                    file_path = os.path.join(temp_dir, filename)
                    self.overlay_images.append(Image.open(file_path))
                    found_overlay = True
                except Exception as e:
                    logger.error(f"Ошибка при обработке файла {filename}: {e}")
        if found_overlay:
            reply_markup = self.create_main_menu_button()  # Добавляем кнопку возврата в главное меню
            await update.message.reply_text(f"Шаблоны (PNG) получены: {len(self.overlay_images)}.", reply_markup=reply_markup)
        else:
            reply_markup = self.create_main_menu_button()  # Добавляем кнопку возврата в главное меню
            await update.message.reply_text("В архиве не найдено PNG изображений.", reply_markup=reply_markup)

    async def generate_images(self, message):
        for bg in self.background_images:
            for overlay in self.overlay_images:
                bg = bg.convert("RGBA")
                overlay = overlay.convert("RGBA")
                overlay_resized = overlay.resize(bg.size, Image.Resampling.LANCZOS)
                result = Image.alpha_composite(bg, overlay_resized)
                self.result_images.append(result)

        # Добавляем выбор, как отправить изображения
        keyboard = [
            [InlineKeyboardButton("Отправить как ZIP файл", callback_data="send_as_zip")],
            [InlineKeyboardButton("Отправить по очереди", callback_data="send_individually")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text("Генерация завершена! Как вы хотите получить изображения?", reply_markup=reply_markup)

    async def send_images_as_zip(self, message):
            # Создаем временный ZIP файл
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
                with zipfile.ZipFile(temp_zip, 'w') as zipf:
                    for idx, result in enumerate(self.result_images):
                        img_filename = f"image_{idx + 1}.png"
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                            result.save(temp_file, "PNG")
                            temp_file.seek(0)
                            zipf.write(temp_file.name, img_filename)

                # Отправляем ZIP файл
                temp_zip.seek(0)
                await message.reply_document(document=temp_zip, filename="generated_images.zip")
                os.remove(temp_zip.name)

    async def send_images_individually(self, message):
            for result in self.result_images:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                    result.save(temp_file, "PNG")
                    temp_file.seek(0)
                    await message.reply_photo(photo=temp_file)
                os.remove(temp_file.name)

# Токен вашего бота
TOKEN = "7090094864:AAHsT-P_px-y27eqTlFlKxQ4-OcKWg94_cI"

# Создаем и запускаем бота
bot = ImageOverlayBot(TOKEN)
bot.application.run_polling()
