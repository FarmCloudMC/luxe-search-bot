import asyncio
import random
import string
import aiohttp

from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup

# =========================
#        LUXE SEARCH
# =========================

API_ID = 32799796
API_HASH = "b7b9ebff2da0c27f5c666224d21cb5b5"
BOT_TOKEN = "8900312971:AAHHumEiLbPfJA7RdzJQ6wtc1ui0fLT3DDI"

app = Client(
    "luxe_search",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# =========================
#         DATA
# =========================

user_lengths = {}
search_tasks = {}

letters = string.ascii_lowercase


# =========================
#   USERNAME GENERATOR
# =========================

def generate_username(length):
    return ''.join(random.choice(letters) for _ in range(length))


# =========================
#  TELEGRAM CHECK (FIXED)
# =========================

async def check_telegram(session, username):
    url = f"https://t.me/{username}"

    try:
        async with session.get(url) as r:
            text = await r.text()

            # если страница "not found" → свободен
            if "sorry, this username is not found" in text.lower():
                return True

            if r.status == 404:
                return True

            return False

    except:
        return False


# =========================
#  FRAGMENT CHECK (FIXED)
# =========================

async def check_fragment(session, username):
    url = f"https://fragment.com/username/{username}"

    try:
        async with session.get(url) as r:
            text = await r.text()

            if "available" in text.lower():
                return True

            if r.status == 404:
                return True

            return False

    except:
        return False


# =========================
#      KEYBOARD
# =========================

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


# =========================
#        SEARCH LOOP
# =========================

async def search_loop(chat_id, message, length):

    async with aiohttp.ClientSession() as session:

        while search_tasks.get(chat_id):

            username = generate_username(length)

            tg = await check_telegram(session, username)
            fr = await check_fragment(session, username)

            if tg and fr:
                await message.reply(
                    f"🎉 НАЙДЕНО\n\n👤 @{username}"
                )

            await asyncio.sleep(0.7)


# =========================
#         START
# =========================

@app.on_message(filters.command("start"))
async def start(_, message):

    user_lengths[message.chat.id] = 5

    await message.reply(
        "✨ LUXE SEARCH\n\nВыбери длину и нажми старт",
        reply_markup=keyboard()
    )


# =========================
#       HANDLER
# =========================

@app.on_message(filters.text)
async def handler(_, message):

    chat_id = message.chat.id
    text = message.text

    if text == "✨ 5 символов":
        user_lengths[chat_id] = 5
        await message.reply("✨ Выбрано 5 символов")

    elif text == "💎 6 символов":
        user_lengths[chat_id] = 6
        await message.reply("💎 Выбрано 6 символов")

    elif text == "🔥 7 символов":
        user_lengths[chat_id] = 7
        await message.reply("🔥 Выбрано 7 символов")

    elif text == "🚀 Начать поиск":

        if search_tasks.get(chat_id):
            return await message.reply("⚠️ Уже работает")

        length = user_lengths.get(chat_id, 5)

        search_tasks[chat_id] = True

        await message.reply(f"🚀 Старт поиска ({length})")

        task = asyncio.create_task(
            search_loop(chat_id, message, length)
        )

        search_tasks[chat_id] = task


    elif text == "🛑 Остановить":

        task = search_tasks.get(chat_id)

        if task:
            search_tasks[chat_id] = False

        await message.reply("🛑 Остановлено")


print("LUXE SEARCH RUNNING")
app.run()