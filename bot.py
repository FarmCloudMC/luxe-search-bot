import asyncio
import random
import string

from pyrogram import Client, filters
from pyrogram.errors import UsernameNotOccupied, UsernameInvalid, FloodWait
from pyrogram.types import ReplyKeyboardMarkup

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
#        STATE
# =========================

lengths = {}
running = {}
locks = {}

letters = string.ascii_lowercase


# =========================
#     USERNAME GEN
# =========================

def gen(length):
    return ''.join(random.choice(letters) for _ in range(length))


# =========================
#   TELEGRAM CHECK SAFE
# =========================

async def check(username):
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
#      SEARCH ENGINE
# =========================

async def worker(chat_id, message):

    async with locks[chat_id]:

        length = lengths.get(chat_id, 5)

        while running.get(chat_id):

            username = gen(length)

            free = await check(username)

            # ❗ не спамим мусор — только результат
            if free:
                await message.reply(
                    f"✨ LUXE SEARCH\n\n"
                    f"🎉 Найден свободный username:\n"
                    f"👤 @{username}"
                )

            await asyncio.sleep(0.6)  # защита от flood


# =========================
#       KEYBOARD
# =========================

def kb():
    return ReplyKeyboardMarkup(
        [
            ["✨ 5 символов", "💎 6 символов"],
            ["🔥 7 символов"],
            ["🚀 Начать", "🛑 Стоп"]
        ],
        resize_keyboard=True
    )


# =========================
#        START
# =========================

@app.on_message(filters.command("start"))
async def start(_, m):

    lengths[m.chat.id] = 5
    locks[m.chat.id] = asyncio.Lock()

    await m.reply(
        "✨ LUXE SEARCH\n\nВыбери длину и нажми старт",
        reply_markup=kb()
    )


# =========================
#       HANDLER
# =========================

@app.on_message(filters.text)
async def h(_, m):

    chat_id = m.chat.id
    text = m.text

    if text == "✨ 5 символов":
        lengths[chat_id] = 5
        await m.reply("✨ выбрано 5")

    elif text == "💎 6 символов":
        lengths[chat_id] = 6
        await m.reply("💎 выбрано 6")

    elif text == "🔥 7 символов":
        lengths[chat_id] = 7
        await m.reply("🔥 выбрано 7")

    elif text == "🚀 Начать":

        if running.get(chat_id):
            return await m.reply("⚠️ уже работает")

        running[chat_id] = True

        await m.reply("🚀 Luxe Search запущен")

        asyncio.create_task(worker(chat_id, m))


    elif text == "🛑 Стоп":

        running[chat_id] = False
        await m.reply("🛑 остановлено")


print("LUXE SEARCH STABLE RUNNING ⚡")
app.run()
