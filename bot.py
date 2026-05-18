import asyncio
import random
import aiohttp

from pyrogram import Client, filters
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

# красивые части
parts = [
    "lu", "xe", "zo", "ra", "ka",
    "mi", "no", "ta", "vo", "xi",
    "ne", "sa", "re", "di", "fa",
    "go", "ha", "ko", "la", "mo",
    "ni", "ro", "za", "ve", "xo"
]

letters = "abcdefghijklmnopqrstuvwxyz"

# ==================================================
#             ГЕНЕРАЦИЯ USERNAME
# ==================================================

def generate_username(length):

    mode = random.randint(1, 4)

    # бренд стиль
    if mode == 1:

        result = (
            random.choice(parts) +
            random.choice(parts)
        )

        return result[:length]

    # слоговый
    elif mode == 2:

        result = ""

        while len(result) < length:
            result += random.choice(parts)

        return result[:length]

    # повторения
    elif mode == 3:

        char = random.choice(letters)

        return (
            char * (length - 1)
        ) + random.choice(letters)

    # симметрия
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
#           ПРОВЕРКА TELEGRAM
# ==================================================

async def check_telegram(session, username):

    try:

        url = f"https://t.me/{username}"

        async with session.get(url) as r:

            text = await r.text()

            text = text.lower()

            # свободный username
            if (
                "if you have telegram" not in text
                and "preview channel" not in text
                and "preview chat" not in text
            ):
                return True

            return False

    except:
        return False

# ==================================================
#           ПРОВЕРКА FRAGMENT
# ==================================================

async def check_fragment(session, username):

    try:

        url = f"https://fragment.com/username/{username}"

        async with session.get(url) as r:

            text = await r.text()

            text = text.lower()

            if "available" in text:
                return True

            if r.status == 404:
                return True

            return False

    except:
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
#                   ПОИСК
# ==================================================

async def search_loop(chat_id, message):

    async with aiohttp.ClientSession() as session:

        while running.get(chat_id):

            length = user_lengths.get(chat_id, 6)

            username = generate_username(length)

            print(f"CHECKING: {username}")

            tg = await check_telegram(
                session,
                username
            )

            fr = await check_fragment(
                session,
                username
            )

            # только полностью свободные
            if tg and fr:

                await message.reply(
                    f"""
✨ LUXE SEARCH

🎉 Найден свободный username

👤 @{username}

📱 Telegram: свободен
💎 Fragment: свободен
"""
                )

            await asyncio.sleep(0.5)

# ==================================================
#                    START
# ==================================================

@app.on_message(filters.command("start"))
async def start(_, message):

    user_lengths[message.chat.id] = 6

    await message.reply(
        """
✨ Добро пожаловать в Luxe Search

🔍 Умный поиск красивых username
💎 Проверка Telegram + Fragment
⚡ Стильные username

Выбери длину 👇
""",
        reply_markup=keyboard()
    )

# ==================================================
#                 ОБРАБОТКА
# ==================================================

@app.on_message(filters.text)
async def handler(_, message):

    chat_id = message.chat.id
    text = message.text

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

    elif text == "🚀 Начать поиск":

        if running.get(chat_id):

            return await message.reply(
                "⚠️ Поиск уже работает"
            )

        running[chat_id] = True

        await message.reply(
            """
🚀 Luxe Search запущен

🔍 Начинаю поиск...
"""
        )

        asyncio.create_task(
            search_loop(chat_id, message)
        )

    elif text == "🛑 Остановить":

        running[chat_id] = False

        await message.reply(
            "🛑 Поиск остановлен"
        )

# ==================================================
#                      RUN
# ==================================================

print("✨ LUXE SEARCH RUNNING ✨")

app.run()
