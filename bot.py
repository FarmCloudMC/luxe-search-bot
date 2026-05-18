import asyncio
import random

from pyrogram import Client, filters
from pyrogram.errors import (
    UsernameNotOccupied,
    UsernameInvalid,
    FloodWait
)

from pyrogram.types import ReplyKeyboardMarkup

# ==================================================
#                 ✨ LUXE SEARCH ✨
# ==================================================

API_ID = 32799796
API_HASH = "b7b9ebff2da0c27f5c666224d21cb5b5"
BOT_TOKEN = "8900312971:AAHHumEiLbPfJA7RdzJQ6wtc1ui0fLT3DDI"

app = Client(
    "luxe_search",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ==================================================
#                    ДАННЫЕ
# ==================================================

user_lengths = {}
running = {}

letters = "abcdefghijklmnopqrstuvwxyz"

# ==================================================
#             КРАСИВЫЕ ЧАСТИ
# ==================================================

parts = [
    "lu", "xe", "zo", "ra", "ka",
    "mi", "no", "ta", "vo", "xi",
    "ne", "sa", "re", "di", "fa",
    "go", "ha", "ko", "la", "mo",
    "ni", "ro", "za", "ve", "xo"
]

endings = ["x", "z", "y", "n", "o", "a"]

# ==================================================
#         УМНАЯ ГЕНЕРАЦИЯ USERNAME
# ==================================================

def generate_username(length):

    mode = random.randint(1, 4)

    # ======================================
    # БРЕНД-СТИЛЬ
    # ======================================

    if mode == 1:

        result = (
            random.choice(parts) +
            random.choice(parts)
        )

        return result[:length]

    # ======================================
    # СЛОГОВЫЙ
    # ======================================

    elif mode == 2:

        result = ""

        while len(result) < length:
            result += random.choice(parts)

        return result[:length]

    # ======================================
    # ПОВТОРЫ
    # ======================================

    elif mode == 3:

        char = random.choice(letters)

        return (
            char * (length - 1)
        ) + random.choice(endings)

    # ======================================
    # СИММЕТРИЯ
    # ======================================

    else:

        half = length // 2

        base = ''.join(
            random.choice(letters)
            for _ in range(half)
        )

        if length % 2 == 0:
            return base + base[::-1]

        return (
            base +
            random.choice(letters) +
            base[::-1]
        )

# ==================================================
#             ПРОВЕРКА USERNAME
# ==================================================

async def check_username(username):

    try:

        await app.resolve_peer(username)

        # username существует
        return False

    except UsernameNotOccupied:

        # свободен
        return True

    except UsernameInvalid:

        return False

    except FloodWait as e:

        print(f"FLOOD WAIT: {e.value}")

        await asyncio.sleep(e.value)

        return False

    except Exception as e:

        print(f"ERROR: {e}")

        return False

# ==================================================
#                КЛАВИАТУРА
# ==================================================

def keyboard():

    return ReplyKeyboardMarkup(
        [
            ["✨ 5 символов", "💎 6 символов"],
            ["🔥 7 символов"],
            ["🚀 Начать поиск"],
            ["🛑 Остановить"]
        ],
        resize_keyboard=True
    )

# ==================================================
#                  ПОИСК
# ==================================================

async def search_loop(chat_id, message):

    while running.get(chat_id):

        length = user_lengths.get(chat_id, 5)

        username = generate_username(length)

        print(f"CHECKING: {username}")

        free = await check_username(username)

        # ==================================
        # НАЙДЕН СВОБОДНЫЙ
        # ==================================

        if free:

            await message.reply(
                f"""
✨ LUXE SEARCH

🎉 Найден свободный username

👤 @{username}

💎 Статус: свободен
"""
            )

        # ==================================
        # АНТИ-ФЛУД
        # ==================================

        await asyncio.sleep(0.3)

# ==================================================
#                   START
# ==================================================

@app.on_message(filters.command("start"))
async def start(_, message):

    user_lengths[message.chat.id] = 6

    text = """
✨ Добро пожаловать в Luxe Search

🔍 Умный поиск красивых username
💎 Проверка через Telegram API
⚡ Быстрый и стабильный поиск

Выбери длину username 👇
"""

    await message.reply(
        text,
        reply_markup=keyboard()
    )

# ==================================================
#                ОБРАБОТЧИК
# ==================================================

@app.on_message(filters.text)
async def handler(_, message):

    chat_id = message.chat.id
    text = message.text

    # ======================================
    # ВЫБОР ДЛИНЫ
    # ======================================

    if text == "✨ 5 символов":

        user_lengths[chat_id] = 5

        await message.reply(
            "✨ Установлено: 5 символов"
        )

    elif text == "💎 6 символов":

        user_lengths[chat_id] = 6

        await message.reply(
            "💎 Установлено: 6 символов"
        )

    elif text == "🔥 7 символов":

        user_lengths[chat_id] = 7

        await message.reply(
            "🔥 Установлено: 7 символов"
        )

    # ======================================
    # СТАРТ
    # ======================================

    elif text == "🚀 Начать поиск":

        if running.get(chat_id):

            return await message.reply(
                "⚠️ Поиск уже работает"
            )

        running[chat_id] = True

        await message.reply(
            """
🚀 Luxe Search запущен

🔍 Начинаю поиск username...
"""
        )

        asyncio.create_task(
            search_loop(chat_id, message)
        )

    # ======================================
    # СТОП
    # ======================================

    elif text == "🛑 Остановить":

        running[chat_id] = False

        await message.reply(
            "🛑 Поиск остановлен"
        )

# ==================================================
#                    RUN
# ==================================================

print("✨ LUXE SEARCH RUNNING ✨")

app.run()
