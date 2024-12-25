import os
import tempfile
import zipfile
from PIL import Image
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters


class ImageGenerator:

    def __init__(self):
        self.background_image = None
        self.overlay_image = None
        self.result_images = []

    def create_overlay_image(self, background: Image, overlay: Image) -> Image:
        """
        Функция наложения шаблона на фон с максимальным сохранением качества.
        """
        # Конвертируем оба изображения в RGBA (если они еще не в этом формате)
        background = background.convert("RGBA")
        overlay = overlay.convert("RGBA")

        # Если размеры изображений разные, масштабируем шаблон под фон с сохранением качества
        if overlay.size != background.size:
            # Масштабируем изображение шаблона с использованием самого качественного алгоритма LANCZOS
            overlay = overlay.resize(background.size, Image.Resampling.LANCZOS)

        # Накладываем изображение шаблона на фон с сохранением прозрачности
        background_resized = background.copy()
        background_resized.paste(overlay, (0, 0), overlay)  # Используем альфа-канал для прозрачности

        return background_resized

    async def send_results(self, query):
        """
        Функция отправки результата как архива PNG.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Сохраняем изображения в PNG для максимального сохранения качества
            for idx, result_image in enumerate(self.result_images):
                file_path = os.path.join(temp_dir, f"result_{idx + 1}.png")
                result_image.save(file_path, format='PNG', quality=100)  # Сохраняем в PNG без потерь

            # Создаем архив с изображениями
            zip_path = os.path.join(temp_dir, "generated_images.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_name in os.listdir(temp_dir):
                    if file_name.startswith("result_"):
                        zipf.write(os.path.join(temp_dir, file_name), file_name)

            # Отправляем архив с изображениями
            with open(zip_path, 'rb') as zip_file:
                await query.message.reply_document(document=InputFile(zip_file),
                                                   caption="Генерация завершена. Архив с изображениями.")

    async def generate_images(self, update, context):
        """
        Основная функция для генерации изображений с наложением шаблона на фон.
        """
        if not self.background_image or not self.overlay_image:
            await update.message.reply_text("Пожалуйста, сначала загрузите оба изображения: фон и шаблон.")
            return

        # Создаем финальное изображение с наложением
        result_image = self.create_overlay_image(self.background_image, self.overlay_image)

        # Добавляем результат в список
        self.result_images.append(result_image)

        # Отправляем результаты
        await self.send_results(update)

    async def start(self, update, context):
        """
        Обработчик команды /start.
        """
        await update.message.reply_text("Привет! Загрузите сначала два файла: фон и шаблон.")

    async def button_handler(self, update, context):
        """
        Обработчик кнопок (например, по нажатию на кнопку пользователь может вызвать генерацию).
        """
        # Получаем объект callback_query
        query = update.callback_query

        # Генерируем изображения при нажатии кнопки
        await self.generate_images(query, context)

    async def handle_file(self, update, context):
        """
        Обработчик загрузки файлов. Ожидает два файла: фон и шаблон.
        """
        file = update.message.document
        file_name = file.file_name.lower()

        # Получаем объект файла через get_file
        file_obj = await file.get_file()

        # Скачиваем файл с помощью метода download() объекта file
        file_path = os.path.join(tempfile.gettempdir(), file.file_name)
        await file_obj.download_to_drive(file_path)

        # Проверяем тип загруженного файла и сохраняем его
        if "background" in file_name:
            self.background_image = Image.open(file_path)
            await update.message.reply_text("Фон загружен. Пожалуйста, загрузите шаблон.")
        elif "overlay" in file_name:
            self.overlay_image = Image.open(file_path)
            await update.message.reply_text("Шаблон загружен. Теперь вы можете генерировать изображения.")
            # После загрузки шаблона показываем кнопку для начала генерации
            keyboard = [
                [InlineKeyboardButton("Начать генерацию", callback_data='generate')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Нажмите кнопку ниже, чтобы начать генерацию:", reply_markup=reply_markup)
        else:
            await update.message.reply_text(
                "Ошибка: загрузите изображения с корректными именами (например, background.png и overlay.png).")


def main():
    """
    Основная функция для запуска бота.
    """
    # Токен вашего бота
    token = "7090094864:AAHsT-P_px-y27eqTlFlKxQ4-OcKWg94_cI"

    # Создаем приложение Telegram
    application = Application.builder().token(token).build()

    # Создаем объект генератора изображений
    image_generator = ImageGenerator()

    # Обработчики команд
    application.add_handler(CommandHandler("start", image_generator.start))

    # Обработчик загрузки файлов
    application.add_handler(MessageHandler(filters.Document.ALL, image_generator.handle_file))

    # Обработчик кнопок (например, нажатие кнопки для начала генерации)
    application.add_handler(CallbackQueryHandler(image_generator.button_handler, pattern='generate'))

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()
