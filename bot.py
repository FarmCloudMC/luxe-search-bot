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

letters = "abcdefghijklmnopqrstuvwxyz"

# ==================================================
#              БОЛЬШЕ СЛОГОВ
# ==================================================

parts = [

    "lu", "xe", "zo", "ra", "ka",
    "mi", "no", "ta", "vo", "xi",
    "ne", "sa", "re", "di", "fa",
    "go", "ha", "ko", "la", "mo",
    "ni", "ro", "za", "ve", "xo",

    "zen", "vex", "luna", "nova",
    "kira", "zoro", "nexo", "viro",
    "lux", "vanta", "lyra", "nero",
    "sora", "kairo", "velo", "zenix",
    "aero", "astro", "onyx", "xeno",
    "vena", "rave", "kova", "luro",
    "vexo", "nori", "mira", "ziva",
    "runa", "hex", "ony", "vori",
    "lyon", "kexo", "vexo", "xora",
    "feno", "seno", "vexo", "rizo"

]

# ==================================================
#          УМНАЯ ГЕНЕРАЦИЯ USERNAME
# ==================================================

def generate_username(length):

    mode = random.randint(1, 5)

    # ======================================
    # БРЕНД СТИЛЬ
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
        ) + random.choice(letters)

    # ======================================
    # СИММЕТРИЯ
    # ======================================

    elif mode == 4:

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

    # ======================================
    # СМЕШАННЫЙ СТИЛЬ
    # ======================================

    else:

        result = (
            random.choice(parts)[:2] +
            ''.join(
                random.choice(letters)
                for _ in range(length - 4)
            ) +
            random.choice(parts)[:2]
        )

        return result[:length]

# ==================================================
#        ПРОВЕРКА TELEGRAM (НОРМ)
# ==================================================

async def check_telegram(session, username):

    try:

        url = f"https://t.me/{username}"

        async with session.get(
            url,
            timeout=10
        ) as r:

            text = await r.text()

            text = text.lower()

            # ==================================
            # ЕСЛИ USERNAME ЗАНЯТ
            # ==================================

            occupied_signs = [

                "view in telegram",
                "preview channel",
                "preview chat",
                "send message",
                "subscribers",
                "members"

            ]

            for sign in occupied_signs:

                if sign in text:
                    return False

            # ==================================
            # ЕСЛИ СВОБОДЕН
            # ==================================

            free_signs = [

                "if you have telegram",
                "this channel can't be displayed",
                "username is not occupied"

            ]

            for sign in free_signs:

                if sign in text:
                    return True

            return False

    except Exception as e:

        print(f"TG ERROR: {e}")

        return False

# ==================================================
#       ПРОВЕРКА FRAGMENT (НОРМ)
# ==================================================

async def check_fragment(session, username):

    try:

        url = f"https://fragment.com/username/{username}"

        async with session.get(
            url,
            timeout=10
        ) as r:

            text = await r.text()

            text = text.lower()

            # ==================================
            # ЗАНЯТ НА FRAGMENT
            # ==================================

            busy_signs = [

                "auction",
                "owner",
                "bids"

            ]

            for sign in busy_signs:

                if sign in text:
                    return False

            # ==================================
            # СВОБОДЕН
            # ==================================

            if (
                "available" in text
                or r.status == 404
            ):
                return True

            return False

    except Exception as e:

        print(f"FRAGMENT ERROR: {e}")

        return False

# ==================================================
#                 КЛАВИАТУРА
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
#                    ПОИСК
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

            print(f"TG: {tg} | FRAGMENT: {fr}")

            # ==================================
            # ТОЛЬКО ПОЛНОСТЬЮ СВОБОДНЫЕ
            # ==================================

            if tg and fr:

                await message.reply(
                    f"""
✨ LUXE SEARCH

🎉 Найден свободный username

👤 @{username}

📱 Telegram: ✅ свободен
💎 Fragment: ✅ свободен
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
#                  ОБРАБОТКА
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

🔍 Начинаю поиск стильных username...
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
