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

letters = "abcdefghijklmnopqrstuvwxyz"


# =========================
#   SMART GEN (быстро)
# =========================

def gen(l):
    return ''.join(random.choice(letters) for _ in range(l))


# =========================
#   CHECK (SAFE)
# =========================

async def check(username):
    try:
        await app.get_chat(username)
        return False
    except UsernameNotOccupied:
        return True
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return False
    except:
        return False


# =========================
#   LOOP (СТАБИЛЬНЫЙ)
# =========================

async def loop(chat_id, msg):

    while running.get(chat_id):

        username = gen(lengths.get(chat_id, 5))

        free = await check(username)

        if free:
            await msg.reply(f"✨ @{username}")

        await asyncio.sleep(0.4)


# =========================
#   KEYBOARD
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
#   START
# =========================

@app.on_message(filters.command("start"))
async def start(_, m):

    lengths[m.chat.id] = 5

    await m.reply(
        "LUXE SEARCH\nREADY",
        reply_markup=kb()
    )


# =========================
#   HANDLER
# =========================

@app.on_message(filters.text)
async def h(_, m):

    chat_id = m.chat.id
    t = m.text

    if t in ["5", "6", "7"]:
        lengths[chat_id] = int(t)
        await m.reply(f"OK {t}")

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
