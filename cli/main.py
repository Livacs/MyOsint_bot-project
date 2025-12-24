import os
import sys
import logging
import asyncio
import tempfile
import mimetypes
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from PIL import Image
from PIL.ExifTags import TAGS
import requests
import phonenumbers
from phonenumbers import geocoder, carrier, timezone
import art

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print("🚀 Запуск OSINT-бота...")
print(f"Python: {sys.executable}")
print(f"Рабочая папка: {os.getcwd()}")

# Загрузка токена
try:
    from config import BOT_TOKEN
    if "ВАШ_ТОКЕН" in BOT_TOKEN or len(BOT_TOKEN) < 20:
        print("❌ ОШИБКА: Укажите корректный BOT_TOKEN в config.py")
        sys.exit(1)
    print("✅ Токен загружен")
except ImportError:
    print("❌ ОШИБКА: Создайте файл config.py с BOT_TOKEN")
    sys.exit(1)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Проверка подключения
async def test_bot_connection():
    try:
        me = await bot.get_me()
        print(f"✅ Бот запущен: @{me.username} (ID: {me.id})")
        return True
    except Exception as e:
        print(f"❌ Не удалось подключиться к Telegram: {e}")
        return False


# Команды
@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("🎉 Привет! Я OSINT-бот. Используй /help для справки.")


@dp.message(Command("help"))
async def help_command(message: Message):
    help_text = (
        "📋 Команды бота:\n\n"
        "/phone <номер> — анализ номера (например, /phone +79123456789)\n"
        "/ip <адрес> — анализ IP (например, /ip 8.8.8.8)\n\n"
        "📸 Анализ метаданных фото:\n"
        "→ Отправьте изображение как файл (не как фото!), чтобы сохранить EXIF.\n"
        "→ Поддерживаются JPG, PNG и другие форматы.\n\n"
        "⚠️ Telegram удаляет EXIF при отправке как 'Фото'!"
    )
    await message.answer(help_text)


@dp.message(Command("phone"))
async def phone_command(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Укажите номер. Пример: /phone +79123456789")
        return

    phone = parts[1].strip()
    msg = await message.answer(f"🔍 Анализ номера: {phone}...")

    try:
        parsed = phonenumbers.parse(phone, None)
        if not phonenumbers.is_valid_number(parsed):
            await msg.edit_text("❌ Неверный формат номера.")
            return

        country = geocoder.description_for_number(parsed, "ru") or "Не определена"
        operator = carrier.name_for_number(parsed, "ru") or "Не определён"
        timezones = ", ".join(timezone.time_zones_for_number(parsed)) or "Не определён"

        result = (
            f"📱 Номер: {phone}\n"
            f"🌍 Страна: {country}\n"
            f"🏢 Оператор: {operator}\n"
            f"⏰ Часовой пояс: {timezones}"
        )
        await msg.edit_text(result)
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {str(e)}")


@dp.message(Command("ip"))
async def ip_command(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Укажите IP. Пример: /ip 8.8.8.8")
        return

    ip = parts[1].strip()
    msg = await message.answer(f"🔍 Анализ IP: {ip}...")

    try:
        # Попытка через ipapi.co
        resp = requests.get(f"https://ipapi.co/{ip}/json/", timeout=10)
        if resp.status_code == 200:
            d = resp.json()
            if d.get("error"):
                raise Exception("Недействительный IP")
            lat, lon = d.get("latitude"), d.get("longitude")
            map_link = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else "N/A"
            result = (
                f"🌐 IP: {ip}\n"
                f"📍 Страна: {d.get('country_name', 'N/A')}\n"
                f"🏙️ Город: {d.get('city', 'N/A')}\n"
                f"📡 Организация: {d.get('org', 'N/A')}\n"
                f"🕒 Часовой пояс: {d.get('timezone', 'N/A')}\n"
                f"🗺️ Карта: {map_link}"
            )
            await msg.edit_text(result)
            return

        # Резерв: ip-api.com
        resp = requests.get(f"http://ip-api.com/json/{ip}", timeout=10)
        if resp.status_code == 200:
            d = resp.json()
            if d.get("status") != "success":
                raise Exception("IP не найден")
            lat, lon = d.get("lat"), d.get("lon")
            map_link = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else "N/A"
            result = (
                f"🌐 IP: {ip}\n"
                f"📍 Страна: {d.get('country', 'N/A')}\n"
                f"🏙️ Город: {d.get('city', 'N/A')}\n"
                f"📡 Провайдер: {d.get('isp', 'N/A')}\n"
                f"🕒 Часовой пояс: {d.get('timezone', 'N/A')}\n"
                f"🗺️ Карта: {map_link}"
            )
            await msg.edit_text(result)
            return

        await msg.edit_text("❌ Не удалось получить данные об IP.")
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {str(e)}")


# Основной обработчик сообщений
@dp.message()
async def handle_message(message: Message):
    if message.photo:
        await message.answer(
            "⚠️ При отправке как фото Telegram удаляет все метаданные (EXIF).\n"
            "Пожалуйста, отправьте изображение как файл, чтобы я мог проанализировать EXIF."
        )
    elif message.document:
        await process_document(message)
    else:
        await message.answer("🤖 Используйте /help для справки.")


async def process_document(message: Message):
    doc = message.document
    filename = doc.file_name or "unknown"

    # Проверка MIME-типа
    mime_type, _ = mimetypes.guess_type(filename)
    if not (mime_type and mime_type.startswith("image")):
        await message.answer("📂 Пожалуйста, отправьте именно изображение (JPG, PNG и т.д.).")
        return

    # Ограничение размера (Telegram позволяет до 20 МБ)
    if doc.file_size > 20 * 1024 * 1024:
        await message.answer("❌ Файл слишком большой (макс. 20 МБ).")
        return

    tmp_path = None
    try:
        file_info = await bot.get_file(doc.file_id)
        tmp_path = tempfile.mktemp(suffix=os.path.splitext(filename)[1] or ".jpg")

        await bot.download_file(file_info.file_path, tmp_path)

        # Проверка, что это изображение
        try:
            with Image.open(tmp_path) as img:
                img.verify()
        except Exception:
            await message.answer("❌ Файл повреждён или не является изображением.")
            return

        # Повторное открытие для чтения EXIF
        with Image.open(tmp_path) as img:
            exifdata = img.getexif()
            if not exifdata:
                await message.answer("🔍 В этом файле нет EXIF-метаданных.")
                return

            exif_lines = []
            for tag_id in exifdata:
                tag = TAGS.get(tag_id, tag_id)
                value = exifdata.get(tag_id)
                exif_lines.append(f"{tag}: {value}")

            exif_text = "\n".join(exif_lines)
            if len(exif_text) > 4000:
                exif_text = exif_text[:4000] + "\n... (обрезано)"

            await message.answer(f"📸 Найдены метаданные EXIF:\n\n{exif_text}")

    except Exception as e:
        await message.answer(f"❌ Ошибка при анализе файла: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


# Запуск
async def main():
    print(art.text2art("TeleOSinter"))
    if await test_bot_connection():
        print("✅ Бот готов к работе. Ожидание сообщений...")
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
