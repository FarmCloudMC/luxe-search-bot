import asyncio
import random
import aiohttp

from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup

API_ID = 32799796
API_HASH = "b7b9ebff2da0c27f5c666224d21cb5b5"
BOT_TOKEN = "8900312971:AAHHumEiLbPfJA7RdzJQ6wtc1ui0fLT3DDI"

app = Client("luxe_search", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_len = {}
running = {}

letters = "abcdefghijklmnopqrstuvwxyz"

# =========================
# SMART GEN (нормальный)
# =========================

def gen(l):
    return ''.join(random.choice(letters) for _ in range(l))

# =========================
# TELEGRAM CHECK (РАБОЧИЙ)
# =========================

async def tg_check(session, username):
    try:
        url = f"https://t.me/{username}"
        async with session.get(url, allow_redirects=True, timeout=10) as r:
            text = await r.text()

            # если есть явный профиль → занят
            if "tgme_page_title" in text:
                return False

            # если страница пустая/ошибка → может быть свободен
            if r.status in [404, 200]:
                return True

            return False

    except:
        return False

# =========================
# FRAGMENT CHECK (СТАБИЛЬНЫЙ)
# =========================

async def fr_check(session, username):
    try:
        url = f"https://fragment.com/username/{username}"
        async with session.get(url, timeout=10) as r:
            text = await r.text()

            if "available" in text.lower():
                return True

            if r.status == 404:
                return True

            return False

    except:
        return False

# =========================
# KEYBOARD
# =========================

def kb():
    return ReplyKeyboardMarkup(
        [
            ["5", "6", "7"],
            ["START", "STOP"]
        ],
        resize_keyboard=True
    )

# =========================
# LOOP
# =========================

async def loop(chat_id, msg):
    async with aiohttp.ClientSession() as session:

        while running.get(chat_id):

            l = user_len.get(chat_id, 6)
            username = gen(l)

            print("CHECK:", username)

            tg = await tg_check(session, username)
            fr = await fr_check(session, username)

            print("TG:", tg, "FR:", fr)

            if tg and fr:
                await msg.reply(f"✨ @{username}")

            await asyncio.sleep(0.5)

# =========================
# START
# =========================

@app.on_message(filters.command("start"))
async def start(_, m):
    user_len[m.chat.id] = 6

    await m.reply(
        "LUXE SEARCH\nREADY",
        reply_markup=kb()
    )

# =========================
# HANDLER
# =========================

@app.on_message(filters.text)
async def h(_, m):

    chat_id = m.chat.id
    t = m.text

    if t in ["5", "6", "7"]:
        user_len[chat_id] = int(t)
        await m.reply("OK")

    elif t == "START":

        if running.get(chat_id):
            return

        running[chat_id] = True
        await m.reply("STARTED")

        asyncio.create_task(loop(chat_id, m))

    elif t == "STOP":
        running[chat_id] = False
        await m.reply("STOPPED")

print("RUNNING")
app.run()
