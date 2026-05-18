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
#                     ДАННЫЕ
# ==================================================

user_lengths = {}
running = {}

letters = "abcdefghijklmnopqrstuvwxyz"

# ==================================================
#            КРАСИВЫЕ СЛОГИ / СЛОВА
# ==================================================

parts = [
    "lu", "xe", "zo", "ra", "ka", "mi", "no",
    "ta", "vo", "xi", "ne", "sa", "re", "di",
    "fa", "go", "ha", "ko", "la", "mo", "ni"
]

endings = [
    "x", "z", "y", "n", "o", "a"
]

# ==================================================
#          УМНАЯ ГЕНЕРАЦИЯ USERNAME
# ==================================================

def generate_username(length):

    mode = random.randint(1, 4)

    # ==========================================
    # БРЕНД-СТИЛЬ (luxe, zora, nexo)
    # ==========================================

    if mode == 1:

        name = random.choice(parts) + random.choice(parts)

        return name[:length]

    # ==========================================
    # СЛОГОВЫЙ СТИЛЬ
    # ==========================================

    elif mode == 2:

        result = ""

        while len(result) < length:
            result += random.choice(parts)

        return result[:length]

    # ==========================================
    # ПОВТОРЕНИЯ
    # ==========================================

    elif mode == 3:

        char = random.choice(letters)

        return (char * (length - 1)) + random.choice(endings)

    # ==========================================
    # СИММЕТРИЯ
    # ==========================================

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
#           ПРОВЕРКА USERNAME
# ==================================================

async def check_username(username):

    try:

        await app.get_chat(username)

        return False

    except UsernameNotOccupied:

        return True

    except UsernameInvalid:

        return False

    except FloodWait as e:

        await asyncio.sleep(e.value)

        return False

    except:

        return False

# ==================================================
#               КЛАВИАТУРА
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
#               ПОИСК
# ==================================================

async def search_loop(chat_id, message):

    while running.get(chat_id):

        length = user_lengths.get(chat_id, 5)

        username = generate_username(length)

        free = await check_username(username)

        # ======================================
        # ТОЛЬКО СВОБОДНЫЕ
        # ======================================

        if free:

            await message.reply(
                f"""
✨ LUXE SEARCH

🎉 Найден свободный username

👤 @{username}

💎 Статус: свободен
"""
            )

        # ======================================
        # АНТИ FLOOD
        # ======================================

        await asyncio.sleep(0.8)

# ==================================================
#                 START
# ==================================================

@app.on_message(filters.command("start"))
async def start(_, message):

    user_lengths[message.chat.id] = 5

    text = """
✨ Добро пожаловать в Luxe Search

🔍 Умный поиск красивых Telegram username
💎 Генерация стильных username
⚡ Проверка через Telegram API

Выбери длину username ниже 👇
"""

    await message.reply(
        text,
        reply_markup=keyboard()
    )

# ==================================================
#              ОБРАБОТЧИК
# ==================================================

@app.on_message(filters.text)
async def handler(_, message):

    chat_id = message.chat.id
    text = message.text

    # ==========================================
    # ВЫБОР ДЛИНЫ
    # ==========================================

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

    # ==========================================
    # СТАРТ
    # ==========================================

    elif text == "🚀 Начать поиск":

        if running.get(chat_id):

            return await message.reply(
                "⚠️ Поиск уже запущен"
            )

        running[chat_id] = True

        await message.reply(
            """
🚀 Luxe Search запущен

🔍 Начинаю поиск красивых username...
"""
        )

        asyncio.create_task(
            search_loop(chat_id, message)
        )

    # ==========================================
    # СТОП
    # ==========================================

    elif text == "🛑 Остановить":

        running[chat_id] = False

        await message.reply(
            "🛑 Поиск остановлен"
        )

# ==================================================
#                   RUN
# ==================================================

print("✨ LUXE SEARCH RUNNING ✨")

app.run()
