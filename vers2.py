from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from PIL import Image
from io import BytesIO
import logging

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Класс для бота
class ImageOverlayBot:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.background_image = None
        self.overlay_image = None
        self.setup_handlers()

    def setup_handlers(self):
        # Обработчик команды /start
        self.application.add_handler(CommandHandler("start", self.start))

        # Обработчик команды /clear
        self.application.add_handler(CommandHandler("clear", self.clear))

        # Обработчик фотографий
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_image))

        # Обработчик документов (например, PNG)
        self.application.add_handler(MessageHandler(filters.Document.MimeType("image/png"), self.handle_image))

    async def start(self, update: Update, context: CallbackContext):
        await update.message.reply_text("Отправьте два изображения: фоновое и с прозрачным фоном (PNG).")

    async def clear(self, update: Update, context: CallbackContext):
        # Очищаем хранимые изображения
        self.background_image = None
        self.overlay_image = None
        await update.message.reply_text("Все изображения очищены. Пожалуйста, отправьте новые фотографии.")

    async def handle_image(self, update: Update, context: CallbackContext):
        # Проверка, если это изображение или документ
        if len(update.message.photo) > 0:
            # Это фото
            file = await update.message.photo[-1].get_file()
        elif update.message.document:
            # Это файл
            file = await update.message.document.get_file()

        if file:
            # Загружаем файл
            file_bytes = await file.download_as_bytearray()

            # Открываем изображение из байтов
            image = Image.open(BytesIO(file_bytes))

            # Если не загружено фоновое изображение
            if self.background_image is None:
                self.background_image = image
                await update.message.reply_text(
                    "Фоновое изображение получено. Теперь отправьте изображение с прозрачным фоном (PNG).")
            else:
                self.overlay_image = image
                self.create_overlay_image()
                await update.message.reply_text("Изображение создано. Отправляю результат...")
                await self.send_result(update)

    def create_overlay_image(self):
        # Убедимся, что оба изображения в формате RGBA, чтобы поддерживать прозрачность
        self.background_image = self.background_image.convert("RGBA")
        self.overlay_image = self.overlay_image.convert("RGBA")

        # Масштабируем накладываемое изображение до размера фонового
        overlay_resized = self.overlay_image.resize(self.background_image.size)

        # Накладываем изображение с прозрачным фоном на фоновое
        background_resized = self.background_image.copy()
        background_resized.paste(overlay_resized, (0, 0), overlay_resized)  # Используем альфа-канал

        # Преобразуем изображение в RGB для отправки
        self.result_image = background_resized.convert('RGB')

    async def send_result(self, update: Update):
        with BytesIO() as output:
            self.result_image.save(output, format='JPEG')
            output.seek(0)
            await update.message.reply_photo(photo=InputFile(output), caption="Вот ваше изображение с наложением.")

    def run(self):
        self.application.run_polling()


if __name__ == '__main__':
    # Замените 'YOUR_BOT_TOKEN' на ваш токен
    bot = ImageOverlayBot('7090094864:AAHsT-P_px-y27eqTlFlKxQ4-OcKWg94_cI')
    bot.run()
