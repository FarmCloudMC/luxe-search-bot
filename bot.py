import asyncio
import random

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

# =========================
#      “УМНЫЕ” СЛОГИ
# =========================

syllables = [
    "ka", "ne", "lo", "ra", "mi", "zo", "lu", "ta", "vo", "xi",
    "no", "be", "sa", "re", "di", "fa", "go", "ha", "ja", "ko"
]

endings = ["x", "z", "a", "o", "y", "e", "n"]


# =========================
#   УМНАЯ ГЕНЕРАЦИЯ
# =========================

def smart_username(length):

    mode = random.randint(1, 4)

    # 1. слоговая генерация (самая “человеческая”)
    if mode == 1:
        name = ""
        while len(name) < length:
            name += random.choice(syllables)
        return name[:length]

    # 2. симметрия (aabbaa / xyzyx)
    if mode == 2:
        half = length // 2
        base = ''.join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(half))
        if length % 2 == 0:
            return base + base[::-1]
        return base + random.choice("abcdefghijklmnopqrstuvwxyz") + base[::-1]

    # 3. повторения (aabbx)
    if mode == 3:
        chars = random.choice("abcdefghijklmnopqrstuvwxyz")
        return (chars * (length - 1)) + random.choice(endings)

    # 4. бренд-стиль (nevo, zora, kaira)
    if mode == 4:
        base = random.choice(syllables) + random.choice(syllables)
        return base[:length]


# =========================
#   TELEGRAM CHECK
# =========================

async def check(username):
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


# =========================
#   SEARCH ENGINE
# =========================

async def worker(chat_id, message):

    async with locks[chat_id]:

        length = lengths.get(chat_id, 5)

        while running.get(chat_id):

            username = smart_username(length)

            free = await check(username)

            if free:
                await message.reply(
                    f"✨ LUXE SEARCH\n\n"
                    f"🎉 Найден стильный username:\n"
                    f"👤 @{username}"
                )

            await asyncio.sleep(0.7)


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
        "✨ LUXE SEARCH\n\n"
        "Умный подбор красивых username\n\n"
        "Выбери длину 👇",
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
        await m.reply("✨ 5 символов")

    elif text == "💎 6 символов":
        lengths[chat_id] = 6
        await m.reply("💎 6 символов")

    elif text == "🔥 7 символов":
        lengths[chat_id] = 7
        await m.reply("🔥 7 символов")

    elif text == "🚀 Начать":

        if running.get(chat_id):
            return await m.reply("⚠️ уже работает")

        running[chat_id] = True

        await m.reply("🚀 запуск Luxe Search")

        asyncio.create_task(worker(chat_id, m))


    elif text == "🛑 Стоп":

        running[chat_id] = False
        await m.reply("🛑 остановлено")


print("LUXE SEARCH SMART RUNNING ⚡")
app.run()
