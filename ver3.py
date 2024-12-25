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


class FileProcessor:
    """Класс для обработки файлов, таких как ZIP-архивы."""

    @staticmethod
    def extract_zip(file_bytes: bytes, temp_dir: str):
        try:
            with zipfile.ZipFile(BytesIO(file_bytes), 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            return True
        except zipfile.BadZipFile:
            logger.error("Ошибка: это не ZIP файл или файл поврежден.")
            return False


class ImageManager:
    """Класс для управления изображениями."""

    def __init__(self):
        self.background_images = []
        self.overlay_images = []
        self.result_images = []

    def add_background(self, image):
        self.background_images.append(image)

    def add_overlay(self, image):
        self.overlay_images.append(image)

    def clear_images(self):
        self.background_images.clear()
        self.overlay_images.clear()
        self.result_images.clear()

    def generate_images(self, sets_count: int):
        self.result_images = []
        for i in range(sets_count):
            bg = self.background_images[i % len(self.background_images)]
            for overlay in self.overlay_images:
                bg = bg.convert("RGBA")
                overlay = overlay.convert("RGBA")
                overlay_resized = overlay.resize(bg.size, Image.Resampling.LANCZOS)
                result = Image.alpha_composite(bg, overlay_resized)
                self.result_images.append(result)

    def save_images_as_zip(self, temp_zip):
        with zipfile.ZipFile(temp_zip, 'w') as zipf:
            for idx, result in enumerate(self.result_images):
                img_filename = f"image_{idx + 1}.png"
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                    result.save(temp_file, "PNG")
                    temp_file.seek(0)
                    zipf.write(temp_file.name, img_filename)

    def save_images_individually(self):
        temp_files = []
        for result in self.result_images:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                result.save(temp_file, "PNG")
                temp_files.append(temp_file.name)
        return temp_files


class AutoCreoBot:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.image_manager = ImageManager()
        self.expected_type = None
        self.generated_sets_count = 0
        self.setup_handlers()

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        self.application.add_handler(MessageHandler(filters.Document.MimeType("application/zip"), self.handle_zip))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.application.add_handler(MessageHandler(filters.Document.MimeType("image/png"), self.handle_png_document))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_sets_count))

    async def start(self, update: Update, context: CallbackContext):
        keyboard = [
            [InlineKeyboardButton("Отправить фоны", callback_data="send_background")],
            [InlineKeyboardButton("Отправить шаблоны", callback_data="send_overlay")],
            [InlineKeyboardButton("Генерировать изображения", callback_data="generate_images")],
            [InlineKeyboardButton("Очистить все", callback_data="clear_all")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if update.message:
            await update.message.reply_text("Добро пожаловать! Выберите одно из действий ниже:",
                                            reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.message.edit_text("Добро пожаловать! Выберите одно из действий ниже:",
                                                          reply_markup=reply_markup)

    def create_main_menu_button(self):
        keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back_to_main_menu")]]
        return InlineKeyboardMarkup(keyboard)

    async def button_handler(self, update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        message = query.message

        if query.data == "send_background":
            self.expected_type = 'background'
            reply_markup = self.create_main_menu_button()
            await message.edit_text("Пожалуйста, отправьте ZIP архив с фонами или изображения (форматы: PNG, JPG).",
                                    reply_markup=reply_markup)

        elif query.data == "send_overlay":
            self.expected_type = 'overlay'
            reply_markup = self.create_main_menu_button()
            await message.edit_text("Пожалуйста, отправьте ZIP архив с шаблонами или изображения (форматы: PNG, JPG).",
                                    reply_markup=reply_markup)

        elif query.data == "generate_images":
            if self.image_manager.background_images and self.image_manager.overlay_images:
                keyboard = [
                    [InlineKeyboardButton("Генерировать для всех фонов", callback_data="generate_all_sets")],
                    [InlineKeyboardButton("Введите количество наборов", callback_data="input_sets_count")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await message.edit_text("Как вы хотите генерировать изображения?", reply_markup=reply_markup)
            else:
                await message.edit_text(
                    "Не все изображения получены. Пожалуйста, отправьте архивы с фонами и шаблонами.")
                reply_markup = self.create_main_menu_button()
                await message.reply_text("Вы можете вернуться в главное меню.", reply_markup=reply_markup)

        elif query.data == "clear_all":
            self.image_manager.clear_images()
            await message.edit_text("Все изображения и настройки очищены. Пожалуйста, отправьте новые архивы.")
            reply_markup = self.create_main_menu_button()
            await message.reply_text("Вы можете вернуться в главное меню.", reply_markup=reply_markup)

        elif query.data == "back_to_main_menu":
            await self.start(update, context)

        elif query.data == "send_as_zip":
            await self.send_images_as_zip(message)

        elif query.data == "send_individually":
            await self.send_images_individually(message)

        elif query.data == "generate_all_sets":
            self.generated_sets_count = len(self.image_manager.background_images)
            await self.generate_images(message)

        elif query.data == "input_sets_count":
            await message.edit_text("Введите количество наборов для генерации:")

    async def handle_sets_count(self, update: Update, context: CallbackContext):
        try:
            sets_count = int(update.message.text)
            if sets_count > 0:
                if sets_count > len(self.image_manager.background_images):
                    reply_markup = self.create_main_menu_button()
                    await update.message.reply_text(
                        f"Ошибка: недостаточно фонов для создания {sets_count} наборов. Пожалуйста, загрузите больше фонов.",
                        reply_markup=reply_markup
                    )
                else:
                    self.generated_sets_count = sets_count
                    await update.message.reply_text(
                        f"Количество наборов установлено: {sets_count}. Генерация начнется.")
                    await self.generate_images(update.message)
            else:
                await update.message.reply_text("Пожалуйста, введите положительное число.")
        except ValueError:
            await update.message.reply_text("Ошибка: Пожалуйста, введите число.")

    async def handle_zip(self, update: Update, context: CallbackContext):
        file = update.message.document
        file_info = await file.get_file()
        file_bytes = await file_info.download_as_bytearray()

        with tempfile.TemporaryDirectory() as temp_dir:
            if not FileProcessor.extract_zip(file_bytes, temp_dir):
                await update.message.reply_text("Ошибка: это не ZIP файл или файл поврежден.")
                return

            if self.expected_type == 'background':
                await self.process_background_zip(temp_dir, update)
            elif self.expected_type == 'overlay':
                await self.process_overlay_zip(temp_dir, update)

    async def handle_photo(self, update: Update, context: CallbackContext):
        file = update.message.photo[-1]
        file_info = await file.get_file()
        file_path = os.path.join(tempfile.gettempdir(), f"temp_{file.file_id}.jpg")
        await file_info.download_to_drive(file_path)

        if self.expected_type == 'background':
            self.image_manager.add_background(Image.open(file_path))
            reply_markup = self.create_main_menu_button()
            await update.message.reply_text("Фон получен.", reply_markup=reply_markup)
        else:
            reply_markup = self.create_main_menu_button()
            await update.message.reply_text("Ошибка: фото принимаются только для фонов.", reply_markup=reply_markup)

    async def handle_png_document(self, update: Update, context: CallbackContext):
        if self.expected_type != 'overlay':
            reply_markup = self.create_main_menu_button()
            await update.message.reply_text("Ошибка: PNG файлы принимаются только для шаблонов.",
                                            reply_markup=reply_markup)
            return

        file = update.message.document
        file_info = await file.get_file()
        file_path = os.path.join(tempfile.gettempdir(), f"overlay_{file.file_id}.png")
        await file_info.download_to_drive(file_path)

        self.image_manager.add_overlay(Image.open(file_path))
        reply_markup = self.create_main_menu_button()
        await update.message.reply_text("Шаблон (PNG) получен.", reply_markup=reply_markup)

    async def process_background_zip(self, temp_dir: str, update: Update):
        found_backgrounds = False
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            if filename.lower().endswith(('png', 'jpg', 'jpeg')):
                try:
                    self.image_manager.add_background(Image.open(file_path))
                    found_backgrounds = True
                except Exception as e:
                    logger.error(f"Ошибка при открытии файла {filename}: {e}")

        if found_backgrounds:
            reply_markup = self.create_main_menu_button()
            await update.message.reply_text(f"Фоны получены, всего фонов: {len(self.image_manager.background_images)}.",
                                            reply_markup=reply_markup)
        else:
            reply_markup = self.create_main_menu_button()
            await update.message.reply_text("Не было найдено фонов в архиве.", reply_markup=reply_markup)

    async def process_overlay_zip(self, temp_dir: str, update: Update):
        found_overlay = False
        for filename in os.listdir(temp_dir):
            if filename.lower().endswith('.png'):
                try:
                    file_path = os.path.join(temp_dir, filename)
                    self.image_manager.add_overlay(Image.open(file_path))
                    found_overlay = True
                except Exception as e:
                    logger.error(f"Ошибка при обработке файла {filename}: {e}")
        if found_overlay:
            reply_markup = self.create_main_menu_button()
            await update.message.reply_text(f"Шаблоны (PNG) получены: {len(self.image_manager.overlay_images)}.",
                                            reply_markup=reply_markup)
        else:
            reply_markup = self.create_main_menu_button()
            await update.message.reply_text("В архиве не найдено PNG изображений.", reply_markup=reply_markup)

    async def generate_images(self, message):
        sets_to_generate = self.generated_sets_count if self.generated_sets_count > 0 else len(
            self.image_manager.background_images)
        self.image_manager.generate_images(sets_to_generate)

        keyboard = [
            [InlineKeyboardButton("Отправить как ZIP файл", callback_data="send_as_zip")],
            [InlineKeyboardButton("Отправить по очереди", callback_data="send_individually")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text("Изображения успешно сгенерированы. Выберите способ отправки:",
                                 reply_markup=reply_markup)

    async def send_images_as_zip(self, message):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
            self.image_manager.save_images_as_zip(temp_zip.name)
            await message.reply_document(document=open(temp_zip.name, 'rb'), filename="result_images.zip")
        # Отправляем сообщение о завершении и добавляем кнопку возврата в главное меню
        keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back_to_main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text("Файлы успешно отправлены! 🎉", reply_markup=reply_markup)

    async def send_images_individually(self, message):
        temp_files = self.image_manager.save_images_individually()
        for file_path in temp_files:
            await message.reply_document(document=open(file_path, 'rb'), filename=os.path.basename(file_path))
            os.remove(file_path)

        # Отправляем сообщение о завершении и добавляем кнопку возврата в главное меню
        keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back_to_main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text("Фото успешно отправлены! 🎉", reply_markup=reply_markup)

    def run(self):
        self.application.run_polling()


if __name__ == "__main__":

    bot = AutoCreoBot("7090094864:AAHsT-P_px-y27eqTlFlKxQ4-OcKWg94_cI")
    bot.run()
