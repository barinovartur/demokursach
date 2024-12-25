from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from PIL import Image
from io import BytesIO
import zipfile
import os
import tempfile
import logging

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Класс для бота
class ImageOverlayBot:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.background_images = []  # Список фонов
        self.overlay_images = []  # Список шаблонов
        self.setup_handlers()

    def setup_handlers(self):
        # Обработчик команды /start
        self.application.add_handler(CommandHandler("start", self.start))

        # Обработчик команды /clear
        self.application.add_handler(CommandHandler("clear", self.clear))

        # Обработчик для получения ZIP файлов с изображениями
        self.application.add_handler(MessageHandler(filters.Document.MimeType("application/zip"), self.handle_zip))

        # Обработчик нажатия кнопок
        self.application.add_handler(CallbackQueryHandler(self.button_handler))

    async def start(self, update: Update, context: CallbackContext):
        # Главное меню
        keyboard = [
            [InlineKeyboardButton("Отправить ZIP с фонами", callback_data="background_image_zip")],
            [InlineKeyboardButton("Отправить ZIP с шаблонами", callback_data="overlay_image_zip")],
            [InlineKeyboardButton("Генерировать изображения", callback_data="generate_images")],
            [InlineKeyboardButton("Очистить все", callback_data="clear_all")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Добро пожаловать! Выберите одно из действий ниже:", reply_markup=reply_markup)

    async def clear(self, update: Update, context: CallbackContext):
        # Очищаем хранимые изображения
        self.background_images = []
        self.overlay_images = []
        await update.message.reply_text("Все изображения очищены. Пожалуйста, отправьте новые архивы.")

    async def button_handler(self, update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()

        if query.data == "background_image_zip":
            # Устанавливаем флаг для фонов
            context.user_data['expected_type'] = 'background'
            await query.edit_message_text("Пожалуйста, отправьте ZIP архив с фонами.")

        elif query.data == "overlay_image_zip":
            # Устанавливаем флаг для шаблонов
            context.user_data['expected_type'] = 'overlay'
            await query.edit_message_text("Пожалуйста, отправьте ZIP архив с шаблонами.")

        elif query.data == "generate_images":
            if self.background_images and self.overlay_images:
                await query.edit_message_text("Генерация изображений...")
                await self.generate_images(query)
            else:
                await query.edit_message_text("Не все изображения получены. Пожалуйста, отправьте архивы с фонами и шаблонами.")

        elif query.data == "clear_all":
            self.background_images = []
            self.overlay_images = []
            await query.edit_message_text("Все изображения и настройки очищены. Пожалуйста, отправьте новые архивы.")

    async def handle_zip(self, update: Update, context: CallbackContext):
        file = update.message.document
        file_info = await file.get_file()
        file_bytes = await file_info.download_as_bytearray()

        # Создаем временную папку для распаковки архива
        with tempfile.TemporaryDirectory() as temp_dir:
            # Сохраняем и распаковываем ZIP файл
            try:
                with zipfile.ZipFile(BytesIO(file_bytes), 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                await update.message.reply_text("Файл получен, разархивирован и готов к работе.")
            except zipfile.BadZipFile:
                await update.message.reply_text("Ошибка: это не ZIP файл или файл поврежден. Пожалуйста, отправьте корректный архив.")
                return

            # Проверяем тип архива
            if 'expected_type' not in context.user_data:
                await update.message.reply_text("Ошибка: не указан тип архива. Пожалуйста, отправьте архив с фонами или шаблонами.")
                return

            if context.user_data['expected_type'] == 'background':
                await self.process_background_zip(temp_dir, update)
            elif context.user_data['expected_type'] == 'overlay':
                await self.process_overlay_zip(temp_dir, update)

    async def process_background_zip(self, temp_dir: str, update: Update):
        found_backgrounds = False

        # Ищем изображения в архиве, которые будут фонами
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
            await update.message.reply_text(f"Фоны получены, всего фонов: {len(self.background_images)}.")
        else:
            await update.message.reply_text("Не было найдено фонов в архиве. Пожалуйста, отправьте архив с фонами.")

    async def process_overlay_zip(self, temp_dir: str, update: Update):
        found_overlay = False

        # Ищем изображения в архиве, которые будут шаблонами
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            if filename.lower().endswith(('png', 'jpg', 'jpeg')):
                try:
                    image = Image.open(file_path)
                    self.overlay_images.append(image)
                    found_overlay = True
                except Exception as e:
                    logger.error(f"Ошибка при открытии файла {filename}: {e}")

        if found_overlay:
            await update.message.reply_text(f"Шаблоны получены, всего шаблонов: {len(self.overlay_images)}.")
        else:
            await update.message.reply_text("Не было найдено шаблонов в архиве. Пожалуйста, отправьте архив с шаблонами.")

    async def generate_images(self, query):
        self.result_images = []

        # Для каждого фона генерируем изображения с каждым шаблоном
        for background in self.background_images:
            for overlay in self.overlay_images:
                result_image = self.create_overlay_image(background, overlay)
                self.result_images.append(result_image)

            # После генерации удаляем текущий фон из списка
            self.background_images.remove(background)

        await self.send_results(query)

    def create_overlay_image(self, background: Image, overlay: Image) -> Image:
        # Убедимся, что оба изображения в формате RGBA, чтобы поддерживать прозрачность
        background = background.convert("RGBA")
        overlay = overlay.convert("RGBA")

        # Масштабируем накладываемое изображение до размера фонового с использованием высокого качества
        overlay_resized = overlay.resize(background.size, Image.LANCZOS)

        # Накладываем изображение с прозрачным фоном на фоновое
        background_resized = background.copy()
        background_resized.paste(overlay_resized, (0, 0), overlay_resized)  # Используем альфа-канал

        return background_resized.convert('RGB')

    async def send_results(self, query):
        # Создаем временную папку для хранения изображений
        with tempfile.TemporaryDirectory() as temp_dir:
            # Сохраняем изображения как файлы в папке с высоким качеством
            for idx, result_image in enumerate(self.result_images):
                file_path = os.path.join(temp_dir, f"result_{idx + 1}.png")
                result_image.save(file_path, format='PNG', quality=95)

            # Создаем ZIP архив с изображениями
            zip_path = os.path.join(temp_dir, "generated_images.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_name in os.listdir(temp_dir):
                    if file_name.startswith("result_"):
                        zipf.write(os.path.join(temp_dir, file_name), file_name)

            # Отправляем архив как документ
            with open(zip_path, 'rb') as zip_file:
                await query.message.reply_document(document=InputFile(zip_file), caption="Генерация завершена. Архив с изображениями.")

        # Кнопка для возвращения в главное меню после генерации
        keyboard = [[InlineKeyboardButton("Главное меню", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Генерация завершена. Вернуться в главное меню:", reply_markup=reply_markup)

# Запуск бота
def main():
    token = "7090094864:AAHsT-P_px-y27eqTlFlKxQ4-OcKWg94_cI"
    bot = ImageOverlayBot(token)
    bot.application.run_polling()

if __name__ == '__main__':
    main()
