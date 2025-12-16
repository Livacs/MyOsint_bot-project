import click
import art
import os
import sys
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print("🚀 Запуск основного кода бота...")
print(f"Python path: {sys.executable}")
print(f"Working dir: {os.getcwd()}")

# Загрузка токена
try:
    from config import BOT_TOKEN

    if "ВАШ_ТОКЕН" in BOT_TOKEN or len(BOT_TOKEN) < 20:
        print(f"❌ ПРОБЛЕМА: Неправильный токен: {BOT_TOKEN}")
        sys.exit(1)
    else:
        print("✅ Токен загружен успешно")
        print(f"Длина токена: {len(BOT_TOKEN)} символов")
except Exception as e:
    print(f"❌ Ошибка загрузки токена: {e}")
    sys.exit(1)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Проверка подключения бота
async def test_bot_connection():
    try:
        me = await bot.get_me()
        print(f"✅ Бот подключен: {me.username} (ID: {me.id})")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения бота: {e}")
        return False


# Обработчики команд
@dp.message(Command("start"))
async def start_command(message: types.Message):
    print(f"📨 Получен /start от {message.from_user.first_name}")
    await message.answer("🎉 Добро пожаловать в OSINT бот! Используй /help для списка команд")


@dp.message(Command("help"))
async def help_command(message: types.Message):
    print(f"📨 Получен /help от {message.from_user.first_name}")
    help_text = """
📋 Доступные команды:
/start - начать работу
/help - помощь
/phone <номер> - поиск по номеру телефона
/ip <адрес> - поиск по IP адресу

📷 Отправь фото для анализа метаданных
    """
    await message.answer(help_text)


@dp.message(Command("phone"))
async def phone_command(message: types.Message):
    print(f"📨 Получен /phone от {message.from_user.first_name}")

    # Получаем текст после команды
    command_text = message.text

    # Проверяем формат: /phone +79123456789
    if len(command_text.split()) < 2:
        await message.answer("❌ Укажите номер телефона. Пример: `/phone +79123456789`")
        return

    phone_number = command_text.split()[1]

    # Отправляем сообщение о начале поиска
    search_msg = await message.answer(f"🔍 Ищу информацию по номеру: {phone_number}...")

    try:
        # Здесь будет реальный поиск
        # Пока заглушка с примером данных
        result = await search_phone_info(phone_number)

        await search_msg.edit_text(result)

    except Exception as e:
        await search_msg.edit_text(f"❌ Ошибка при поиске: {str(e)}")

# Функция для поиска информации по номеру телефона
async def search_phone_info(phone_number: str) -> str:
    """
    Функция для OSINT поиска по номеру телефона
    В реальном боте здесь должен быть код для сбора информации
    """

    # Пример данных (заглушка)
    import phonenumbers
    from phonenumbers import geocoder, carrier, timezone

    try:
        # Парсим номер
        parsed_number = phonenumbers.parse(phone_number, None)

        # Проверяем валидность
        if not phonenumbers.is_valid_number(parsed_number):
            return "❌ Неверный номер телефона"

        # Получаем информацию
        country = geocoder.description_for_number(parsed_number, "ru")
        operator = carrier.name_for_number(parsed_number, "ru")
        time_zones = timezone.time_zones_for_number(parsed_number)

        # Формируем результат
        result = f"""
📱 Информация по номеру: {phone_number}
        
🌍 Страна: {country if country else "Не определена"}
🏢 Оператор: {operator if operator else "Не определён"}
⏰ Часовой пояс: {', '.join(time_zones) if time_zones else "Не определён"}
        
⚠️ Информация получена из открытых источников
        """

        return result

    except Exception as e:
        return f"❌ Ошибка при обработке номера: {str(e)}"


@dp.message(Command("ip"))
async def ip_command(message: types.Message):
    print(f"📨 Получен /ip от {message.from_user.first_name}")

    # Получаем текст после команды
    command_text = message.text

    # Проверяем формат: /ip 8.8.8.8
    if len(command_text.split()) < 2:
        await message.answer("❌ Укажите IP адрес. Пример: `/ip 8.8.8.8`")
        return

    ip_address = command_text.split()[1]

    # Отправляем сообщение о начале поиска
    search_msg = await message.answer(f"🔍 Ищу информацию по IP: {ip_address}...")

    try:
        # Выполняем поиск
        result = await search_ip_info(ip_address)

        await search_msg.edit_text(result)

    except Exception as e:
        await search_msg.edit_text(f"❌ Ошибка при поиске: {str(e)}")


# Функция для поиска информации по IP
async def search_ip_info(ip_address: str) -> str:
    """
    Функция для OSINT поиска по IP адресу
    """

    import requests
    import json

    try:
        # Используем бесплатный API для получения информации об IP
        # ipapi.co - бесплатный сервис
        response = requests.get(f"https://ipapi.co/{ip_address}/json/", timeout=10)

        if response.status_code != 200:
            # Пробуем другой API
            response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=10)

            if response.status_code != 200:
                return "❌ Не удалось получить информацию об IP"

            data = response.json()

            if data.get("status") != "success":
                return "❌ Неверный IP адрес или сервис недоступен"

            # Формируем результат для ip-api.com
            result = f"""
🌐 Информация по IP: {ip_address}

📍 Локация:
• Страна: {data.get('country', 'N/A')}
• Регион: {data.get('regionName', 'N/A')}
• Город: {data.get('city', 'N/A')}
• Почтовый индекс: {data.get('zip', 'N/A')}

📡 Провайдер:
• Организация: {data.get('org', 'N/A')}
• Интернет-провайдер: {data.get('isp', 'N/A')}
• ASN: {data.get('as', 'N/A')}

📊 Техническая информация:
• Часовой пояс: {data.get('timezone', 'N/A')}
• Широта: {data.get('lat', 'N/A')}
• Долгота: {data.get('lon', 'N/A')}

🌍Карта: https://www.google.com/maps?q={data.get('lat', '')},{data.get('lon', '')}
            """

            return result

        # Для ipapi.co
        data = response.json()

        # Формируем результат
        result = f"""
🌐 Информация по IP: {ip_address}

📍 Локация:
• Страна: {data.get('country_name', 'N/A')}
• Регион: {data.get('region', 'N/A')}
• Город: {data.get('city', 'N/A')}
• Почтовый индекс: {data.get('postal', 'N/A')}

📡 Провайдер:
• Организация: {data.get('org', 'N/A')}
• Интернет-провайдер: {data.get('asn', 'N/A')}

📊 Техническая информация:
• Часовой пояс: {data.get('timezone', 'N/A')}
• Валюта: {data.get('currency', 'N/A')}
• Язык: {data.get('languages', 'N/A')}
• Широта: {data.get('latitude', 'N/A')}
• Долгота: {data.get('longitude', 'N/A')}

🌍 Карта: https://www.google.com/maps?q={data.get('latitude', '')},{data.get('longitude', '')}

⚠️ Информация получена из открытых источников
        """

        return result

    except requests.exceptions.Timeout:
        return "❌ Таймаут при запросе к сервису"
    except requests.exceptions.RequestException as e:
        return f"❌ Ошибка сети: {str(e)}"
    except Exception as e:
        return f"❌ Ошибка при обработке IP: {str(e)}"


@dp.message()
async def handle_other_messages(message: types.Message):
    print(f"📨 Получено сообщение: {message.text}")
    await message.answer("🤖 Используй /help для списка команд")


# Основная асинхронная функция
async def main():
    # Показываем арт
    project_name = art.text2art("TeleOSinter")
    print(project_name)

    # Тестируем подключение
    if not await test_bot_connection():
        return

    print("✅ Запуск поллинга...")
    await dp.start_polling(bot)


# Запуск приложения
if __name__ == "__main__":
    asyncio.run(main())

