import asyncio
import random
import string

from pyrogram import Client, filters
from pyrogram.errors import UsernameNotOccupied, UsernameInvalid, FloodWait

# =========================
#      LUXE SEARCH
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
running = {}

letters = string.ascii_lowercase


# =========================
#   GENERATE USERNAME
# =========================

def gen(length):
    return ''.join(random.choice(letters) for _ in range(length))


# =========================
#   CHECK TELEGRAM
# =========================

async def is_free(username):
    try:
        await app.get_chat(username)
        return False  # занят
    except UsernameNotOccupied:
        return True   # свободен
    except UsernameInvalid:
        return False
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return False
    except:
        return False


# =========================
#     SEARCH LOOP
# =========================

async def search(chat_id, message, length):

    while running.get(chat_id):

        tasks = []

        for _ in range(5):
            username = gen(length)
            tasks.append((username, asyncio.create_task(is_free(username))))

        for username, task in tasks:

            free = await task

            if free and running.get(chat_id):
                await message.reply(f"🎉 НАЙДЕНО\n\n👤 @{username}")

        await asyncio.sleep(0.2)


# =========================
#         START
# =========================

@app.on_message(filters.command("start"))
async def start(_, message):

    user_lengths[message.chat.id] = 5

    await message.reply(
        "✨ LUXE SEARCH\n\n"
        "Выбери длину и нажми старт"
    )


# =========================
#       HANDLER
# =========================

@app.on_message(filters.text)
async def handler(_, message):

    chat_id = message.chat.id
    text = message.text

    if text == "5":
        user_lengths[chat_id] = 5
        await message.reply("✨ 5 символов")

    elif text == "6":
        user_lengths[chat_id] = 6
        await message.reply("💎 6 символов")

    elif text == "7":
        user_lengths[chat_id] = 7
        await message.reply("🔥 7 символов")

    elif text.lower().startswith("старт") or "начать" in text.lower():

        if running.get(chat_id):
            return await message.reply("⚠️ Уже работает")

        running[chat_id] = True

        length = user_lengths.get(chat_id, 5)

        await message.reply(f"🚀 Поиск запущен ({length})")

        asyncio.create_task(search(chat_id, message, length))


    elif "стоп" in text.lower():

        running[chat_id] = False
        await message.reply("🛑 Остановлено")


print("LUXE SEARCH RUNNING ⚡")
app.run()
