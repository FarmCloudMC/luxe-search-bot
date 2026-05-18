import asyncio
import json
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Теперь читаем их
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле")

ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
OPERATOR_USERNAME = os.getenv("OPERATOR_USERNAME", "emdrug")
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ========== КОНФИГ ==========
OPERATOR_USERNAME = "emdrug"
STORE_NAME = "Emerald Store"
DATA_FILE = "emerald_store_data.json"
CURRENCY = "₸"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ========== ЗАГРУЗКА / СОХРАНЕНИЕ ДАННЫХ ==========
def load_data():
    default_data = {
        "products": [],
        "cities": ["Рудный", "Костанай", "Качар", "Федоровка", "Лисаковск"],
        "promocodes": [],
        "users": {},
        "orders": [],
        "reviews": [],         # список отзывов: {id, name, date, text}
        "next_product_id": 1,
        "next_order_id": 1,
        "next_review_id": 1
    }
    if not os.path.exists(DATA_FILE):
        return default_data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            loaded = json.load(f)
        except:
            return default_data
    for key, default_value in default_data.items():
        if key not in loaded:
            loaded[key] = default_value
    for p in loaded.get("products", []):
        if "cities" not in p:
            p["cities"] = loaded["cities"].copy()
    for uid, u_data in loaded.get("users", {}).items():
        if "balance" not in u_data:
            u_data["balance"] = 0
        if "orders" not in u_data:
            u_data["orders"] = []
    return loaded

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

data = load_data()

# ========== КЛАВИАТУРЫ ==========
def user_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📦 Прайс"), types.KeyboardButton(text="👤 Профиль")],
            [types.KeyboardButton(text="📝 Отзывы"), types.KeyboardButton(text="🎟 Промокод")],
            [types.KeyboardButton(text="🛟 Саппорт")]
        ],
        resize_keyboard=True
    )

def admin_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="➕ Добавить товар"), types.KeyboardButton(text="✏️ Редактировать товар")],
            [types.KeyboardButton(text="🗑 Удалить товар"), types.KeyboardButton(text="🏙️ Города")],
            [types.KeyboardButton(text="➕ Добавить баланс"), types.KeyboardButton(text="➖ Списать баланс")],
            [types.KeyboardButton(text="✍️ Создать отзыв"), types.KeyboardButton(text="🎫 Создать промокод")],
            [types.KeyboardButton(text="📢 Рассылка"), types.KeyboardButton(text="📊 Статистика")],
            [types.KeyboardButton(text="📦 Список товаров"), types.KeyboardButton(text="🔙 Выйти из админки")]
        ],
        resize_keyboard=True
    )

def add_cities_keyboard(selected_cities):
    kb = []
    for city in data["cities"]:
        checked = "✅ " if city in selected_cities else "⬜ "
        kb.append([InlineKeyboardButton(text=f"{checked}{city}", callback_data=f"addcity_{city}")])
    kb.append([InlineKeyboardButton(text="✅ ГОТОВО", callback_data="done_cities")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def is_admin(user_id):
    return user_id in ADMIN_IDS

# ========== FSM СОСТОЯНИЯ ==========
class AddProduct(StatesGroup):
    name = State()
    desc = State()
    price = State()
    cities = State()

class EditProduct(StatesGroup):
    select_id = State()
    field = State()
    new_value = State()
    cities = State()

class DeleteProduct(StatesGroup):
    select_id = State()

class PromocodeState(StatesGroup):
    code = State()
    discount = State()
    expires_days = State()

class BroadcastState(StatesGroup):
    message = State()

class CityManage(StatesGroup):
    action = State()
    name = State()

class BalanceOperation(StatesGroup):
    user_id = State()
    amount = State()
    operation = State()  # "add" or "remove"

class ReviewCreation(StatesGroup):
    name = State()
    text = State()
    date = State()       # дата в формате ДД.ММ.ГГГГ, можно авто

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
async def send_order_notification_to_admin(order_id, user_id, product_name, price, city):
    user_link = f"tg://user?id={user_id}"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data=f"confirm_order_{order_id}")]
    ])
    text = (
        f"🆕 **НОВЫЙ ЗАКАЗ #{order_id}**\n\n"
        f"👤 Покупатель: [user]({user_link}) (ID: `{user_id}`)\n"
        f"📦 Товар: {product_name}\n"
        f"💰 Сумма: {price} {CURRENCY}\n"
        f"🏙️ Город: {city}\n"
        f"🕒 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Нажмите кнопку ниже, чтобы подтвердить заказ."
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="Markdown", reply_markup=keyboard)
        except:
            pass

async def update_order_status(order_id, new_status, user_id=None, notify_user=True):
    order = next((o for o in data["orders"] if o["id"] == order_id), None)
    if not order:
        return
    order["status"] = new_status
    save_data(data)
    if notify_user and user_id:
        status_text = "принят и находится в обработке" if new_status == "подтверждён" else new_status
        await bot.send_message(
            user_id,
            f"📬 **Статус заказа #{order_id} обновлён!**\n\n"
            f"Текущий статус: *{status_text}*.\n"
            f"Спасибо, что выбрали {STORE_NAME}!",
            parse_mode="Markdown"
        )

# ========== ОБРАБОТЧИКИ ==========
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = str(message.from_user.id)
    if user_id not in data["users"]:
        data["users"][user_id] = {
            "orders": [],
            "joined": datetime.now().isoformat(),
            "balance": 0
        }
        save_data(data)
    text = (
        f"✨ Добро пожаловать в **{STORE_NAME}**! ✨\n\n"
        f"🔮 Только лучшие позиции.\n"
        f"💳 Оплата с баланса бота.\n"
        f"🚚 Доставка по городам: {', '.join(data['cities'])}\n\n"
        f"Для покупки нажми **📦 Прайс**.\n"
        f"Ваш баланс: **{data['users'][user_id]['balance']} {CURRENCY}**"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=user_keyboard())

# ---------- ПРАЙС (выбор города, затем товара) ----------
@dp.message(F.text == "📦 Прайс")
async def show_cities(message: Message):
    if not data["cities"]:
        await message.answer("Список городов пуст. Обратитесь к администратору.")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=city, callback_data=f"city_{city}")] for city in data["cities"]
    ] + [[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_city_selection")]])
    await message.answer("🏙️ Выберите ваш город:", reply_markup=keyboard)

@dp.callback_query(F.data == "cancel_city_selection")
async def cancel_city_selection(callback: CallbackQuery):
    await callback.message.edit_text("Выбор города отменён.")
    await callback.message.answer("Главное меню", reply_markup=user_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("city_"))
async def city_selected(callback: CallbackQuery):
    city = callback.data.split("_", 1)[1]
    available_products = [p for p in data["products"] if city in p.get("cities", [])]
    if not available_products:
        await callback.message.edit_text(f"❌ В городе {city} пока нет доступных товаров.")
        await callback.answer()
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{p['name']} — {p['price']} {CURRENCY}", callback_data=f"product_{p['id']}_{city}")]
        for p in available_products
    ] + [[InlineKeyboardButton(text="◀️ Назад к городам", callback_data="back_to_cities")]])
    await callback.message.edit_text(f"📦 Выберите товар для города {city}:", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "back_to_cities")
async def back_to_cities(callback: CallbackQuery):
    if not data["cities"]:
        await callback.message.edit_text("Список городов пуст.")
        await callback.answer()
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=city, callback_data=f"city_{city}")] for city in data["cities"]
    ] + [[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_city_selection")]])
    await callback.message.edit_text("🏙️ Выберите ваш город:", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data.startswith("product_"))
async def product_selected(callback: CallbackQuery):
    _, pid_str, city = callback.data.split("_", 2)
    pid = int(pid_str)
    product = next((p for p in data["products"] if p["id"] == pid), None)
    if not product or city not in product.get("cities", []):
        await callback.answer("Товар недоступен в этом городе", show_alert=True)
        return
    user_id = str(callback.from_user.id)
    user = data["users"].get(user_id, {"balance": 0})
    balance = user.get("balance", 0)
    price = product["price"]
    if balance < price:
        await callback.message.edit_text(
            f"❌ **Недостаточно средств!**\n\n"
            f"Ваш баланс: {balance} {CURRENCY}\n"
            f"Цена товара: {price} {CURRENCY}\n\n"
            f"Пожалуйста, пополните баланс через оператора @{OPERATOR_USERNAME}.",
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    # Списание средств
    data["users"][user_id]["balance"] -= price
    # Генерация заказа
    order_id = data["next_order_id"]
    data["next_order_id"] += 1
    order = {
        "id": order_id,
        "user_id": callback.from_user.id,
        "product": product["name"],
        "product_id": pid,
        "price": price,
        "city": city,
        "status": "ожидает подтверждения",
        "date": datetime.now().isoformat()
    }
    data["orders"].append(order)
    data["users"][user_id]["orders"].append(order_id)
    save_data(data)
    # Уведомление админам
    await send_order_notification_to_admin(order_id, callback.from_user.id, product["name"], price, city)
    # Ответ пользователю
    await callback.message.edit_text(
        f"✅ **Покупка успешно совершена!**\n\n"
        f"🎫 **Номер заказа:** `{order_id}`\n"
        f"📦 Товар: {product['name']}\n"
        f"💰 Списано: {price} {CURRENCY}\n"
        f"🏙️ Город: {city}\n\n"
        f"Ожидайте подтверждения от оператора @{OPERATOR_USERNAME}. Сохраните номер заказа для связи.",
        parse_mode="Markdown"
    )
    await callback.answer()

# ---------- Подтверждение заказа админом ----------
@dp.callback_query(F.data.startswith("confirm_order_"))
async def confirm_order(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Вы не администратор!", show_alert=True)
        return
    order_id = int(callback.data.split("_")[2])
    order = next((o for o in data["orders"] if o["id"] == order_id), None)
    if not order:
        await callback.answer("Заказ не найден.", show_alert=True)
        return
    if order["status"] != "ожидает подтверждения":
        await callback.answer(f"Заказ уже {order['status']}", show_alert=True)
        return
    await update_order_status(order_id, "подтверждён", order["user_id"], notify_user=True)
    await callback.message.edit_text(
        f"✅ Заказ #{order_id} подтверждён!\n"
        f"Покупатель уведомлён.",
        reply_markup=None
    )
    await callback.answer()

# ---------- Отзывы ----------
@dp.message(F.text == "📝 Отзывы")
async def show_reviews(message: Message):
    if not data["reviews"]:
        await message.answer("📝 Пока нет отзывов. Будьте первым!")
        return
    text = "🌟 **Отзывы наших клиентов:**\n**Чтобы оставить отзыв пишите оператору.**\n\n"
    for rev in data["reviews"][-10:]:  # последние 10
        text += f"👤 *{rev['name']}*  📅 {rev['date']}\n📝 {rev['text']}\n\n"
    await message.answer(text, parse_mode="Markdown")

# ---------- Остальные пользовательские кнопки ----------
@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    user_id = str(message.from_user.id)
    user = data["users"].get(user_id, {})
    balance = user.get("balance", 0)
    orders_list = user.get("orders", [])
    orders_count = len(orders_list)
    total_spent = 0
    orders_text = ""
    for oid in orders_list:
        order = next((o for o in data["orders"] if o["id"] == oid), None)
        if order:
            total_spent += order["price"]
            orders_text += f"• #{order['id']} — {order['product']} ({order['price']} {CURRENCY}) — {order['status']}\n"
    if not orders_text:
        orders_text = "Нет заказов."
    text = (
        f"👤 **Ваш профиль**\n\n"
        f"🆔 ID: `{message.from_user.id}`\n"
        f"📅 Регистрация: {user.get('joined', 'неизвестно')[:10]}\n"
        f"💰 Баланс: {balance} {CURRENCY}\n"
        f"🛍️ Заказов: {orders_count}\n"
        f"💸 Потрачено: {total_spent} {CURRENCY}\n\n"
        f"📋 **История заказов:**\n{orders_text}"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🎟 Промокод")
async def promo_enter(message: Message):
    await message.answer("Введите промокод:")
    @dp.message()
    async def handle_promo(msg: Message):
        code = msg.text
        promo = next((p for p in data["promocodes"] if p["code"].lower() == code.lower()), None)
        if not promo:
            await msg.answer("❌ Неверный промокод.")
            return
        expires = datetime.fromisoformat(promo["expires"])
        if expires < datetime.now():
            await msg.answer("❌ Промокод просрочен.")
            return
        await msg.answer(f"🎉 Промокод **{code}** активирован! Скидка {promo['discount']}% на следующий заказ.")

@dp.message(F.text == "🛟 Саппорт")
async def support(message: Message):
    await message.answer(f"🛟 Служба поддержки: @{OPERATOR_USERNAME}\nСвяжитесь с нами по любым вопросам.")

# ========== АДМИН-ПАНЕЛЬ ==========
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if is_admin(message.from_user.id):
        await message.answer("⚙️ **Панель администратора**", parse_mode="Markdown", reply_markup=admin_keyboard())
    else:
        await message.answer("🚫 Доступ запрещён.")

@dp.message(F.text == "🔙 Выйти из админки")
async def exit_admin(message: Message):
    if is_admin(message.from_user.id):
        await message.answer("Вы вышли из админки.", reply_markup=user_keyboard())

# ---------- Добавление товара ----------
@dp.message(F.text == "➕ Добавить товар")
async def add_product_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Введите **название** товара:")
    await state.set_state(AddProduct.name)

@dp.message(AddProduct.name)
async def add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите **описание** товара:")
    await state.set_state(AddProduct.desc)

@dp.message(AddProduct.desc)
async def add_product_desc(message: Message, state: FSMContext):
    await state.update_data(desc=message.text)
    await message.answer("Введите **цену** (только число в тенге):")
    await state.set_state(AddProduct.price)

@dp.message(AddProduct.price)
async def add_product_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите число.")
        return
    price = int(message.text)
    await state.update_data(price=price)
    if not data["cities"]:
        await message.answer("Сначала добавьте города через '🏙️ Города'.")
        await state.clear()
        return
    await state.update_data(selected_cities=[])
    keyboard = add_cities_keyboard([])
    await message.answer("Выберите города, в которых будет доступен товар (можно несколько):", reply_markup=keyboard)
    await state.set_state(AddProduct.cities)

@dp.callback_query(AddProduct.cities, F.data.startswith("addcity_"))
async def add_product_cities_toggle(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split("_", 1)[1]
    data_state = await state.get_data()
    selected = data_state.get("selected_cities", [])
    if city in selected:
        selected.remove(city)
    else:
        selected.append(city)
    await state.update_data(selected_cities=selected)
    keyboard = add_cities_keyboard(selected)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(AddProduct.cities, F.data == "done_cities")
async def add_product_done(callback: CallbackQuery, state: FSMContext):
    data_state = await state.get_data()
    selected_cities = data_state.get("selected_cities", [])
    if not selected_cities:
        await callback.answer("Выберите хотя бы один город!", show_alert=True)
        return
    new_id = data["next_product_id"]
    product = {
        "id": new_id,
        "name": data_state["name"],
        "desc": data_state["desc"],
        "price": data_state["price"],
        "cities": selected_cities
    }
    data["products"].append(product)
    data["next_product_id"] += 1
    save_data(data)
    await state.clear()
    await callback.message.edit_text(f"✅ Товар **{product['name']}** добавлен! ID: {new_id}, цена: {product['price']} {CURRENCY}, города: {', '.join(selected_cities)}")
    await callback.message.answer("Вернуться в админку: /admin")
    await callback.answer()

# ---------- Редактирование товара ----------
@dp.message(F.text == "✏️ Редактировать товар")
async def edit_product_select(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if not data["products"]:
        await message.answer("Нет товаров для редактирования.")
        return
    text = "📝 **Выберите товар для редактирования:**\n"
    for p in data["products"]:
        text += f"ID: {p['id']} — {p['name']} ({p['price']} {CURRENCY})\n"
    text += "\nВведите ID товара:"
    await message.answer(text, parse_mode="Markdown")
    await state.set_state(EditProduct.select_id)

@dp.message(EditProduct.select_id)
async def edit_product_field_choice(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите числовой ID.")
        return
    pid = int(message.text)
    product = next((p for p in data["products"] if p["id"] == pid), None)
    if not product:
        await message.answer("Товар не найден.")
        await state.clear()
        return
    await state.update_data(pid=pid)
    await message.answer(
        f"Что изменить у **{product['name']}**?\n"
        f"Доступно: `name`, `desc`, `price`, `cities`\n"
        f"Пример: `price`",
        parse_mode="Markdown"
    )
    await state.set_state(EditProduct.field)

@dp.message(EditProduct.field)
async def edit_product_new_value(message: Message, state: FSMContext):
    field = message.text.lower()
    if field not in ["name", "desc", "price", "cities"]:
        await message.answer("Допустимые поля: name, desc, price, cities")
        return
    await state.update_data(field=field)
    if field == "cities":
        pid = (await state.get_data())["pid"]
        product = next(p for p in data["products"] if p["id"] == pid)
        selected = product.get("cities", [])
        await state.update_data(selected_cities=selected)
        keyboard = add_cities_keyboard(selected)
        await message.answer("Выберите города для товара:", reply_markup=keyboard)
        await state.set_state(EditProduct.cities)
    else:
        await message.answer(f"Введите новое значение для `{field}`:")
        await state.set_state(EditProduct.new_value)

@dp.callback_query(EditProduct.cities, F.data.startswith("addcity_"))
async def edit_cities_toggle(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split("_", 1)[1]
    data_state = await state.get_data()
    selected = data_state.get("selected_cities", [])
    if city in selected:
        selected.remove(city)
    else:
        selected.append(city)
    await state.update_data(selected_cities=selected)
    keyboard = add_cities_keyboard(selected)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(EditProduct.cities, F.data == "done_cities")
async def edit_cities_done(callback: CallbackQuery, state: FSMContext):
    data_state = await state.get_data()
    selected = data_state.get("selected_cities", [])
    pid = data_state["pid"]
    product = next(p for p in data["products"] if p["id"] == pid)
    product["cities"] = selected
    save_data(data)
    await state.clear()
    await callback.message.edit_text(f"✅ Города для товара **{product['name']}** обновлены: {', '.join(selected)}")
    await callback.message.answer("Вернуться в админку: /admin")
    await callback.answer()

@dp.message(EditProduct.new_value)
async def edit_product_save(message: Message, state: FSMContext):
    data_state = await state.get_data()
    pid = data_state["pid"]
    field = data_state["field"]
    value = message.text
    product = next((p for p in data["products"] if p["id"] == pid), None)
    if not product:
        await message.answer("Ошибка.")
        await state.clear()
        return
    if field == "name":
        product["name"] = value
    elif field == "desc":
        product["desc"] = value
    elif field == "price":
        if not value.isdigit():
            await message.answer("Цена должна быть числом.")
            return
        product["price"] = int(value)
    save_data(data)
    await message.answer(f"✅ Товар обновлён: {field} -> {value}", reply_markup=admin_keyboard())
    await state.clear()

# ---------- Удаление товара ----------
@dp.message(F.text == "🗑 Удалить товар")
async def delete_product_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if not data["products"]:
        await message.answer("Нет товаров для удаления.")
        return
    text = "🗑 **Выберите ID товара для удаления:**\n"
    for p in data["products"]:
        text += f"ID: {p['id']} — {p['name']} ({p['price']} {CURRENCY})\n"
    text += "\nВведите ID товара:"
    await message.answer(text, parse_mode="Markdown")
    await state.set_state(DeleteProduct.select_id)

@dp.message(DeleteProduct.select_id)
async def delete_product_confirm(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите числовой ID.")
        return
    pid = int(message.text)
    product = next((p for p in data["products"] if p["id"] == pid), None)
    if not product:
        await message.answer("Товар не найден.")
        await state.clear()
        return
    data["products"].remove(product)
    save_data(data)
    await message.answer(f"✅ Товар **{product['name']}** удалён.", reply_markup=admin_keyboard())
    await state.clear()

# ---------- Управление городами ----------
@dp.message(F.text == "🏙️ Города")
async def manage_cities(message: Message):
    if not is_admin(message.from_user.id):
        return
    text = "🏙️ **Список городов:**\n" + "\n".join([f"• {c}" for c in data["cities"]])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить город", callback_data="add_city")],
        [InlineKeyboardButton(text="✖️ Удалить город", callback_data="del_city")]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

@dp.callback_query(F.data == "add_city")
async def add_city_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите название нового города:")
    await state.set_state(CityManage.name)
    await state.update_data(action="add")
    await callback.answer()

@dp.callback_query(F.data == "del_city")
async def del_city_start(callback: CallbackQuery, state: FSMContext):
    if not data["cities"]:
        await callback.message.answer("Список городов пуст.")
        await callback.answer()
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=city, callback_data=f"delcity_{city}")] for city in data["cities"]
    ])
    await callback.message.answer("Выберите город для удаления:", reply_markup=kb)
    await state.set_state(CityManage.action)
    await state.update_data(action="del")
    await callback.answer()

@dp.callback_query(CityManage.action, F.data.startswith("delcity_"))
async def del_city_confirm(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split("_", 1)[1]
    if city in data["cities"]:
        data["cities"].remove(city)
        for p in data["products"]:
            if city in p.get("cities", []):
                p["cities"].remove(city)
        save_data(data)
        await callback.message.edit_text(f"✅ Город {city} удалён.")
    else:
        await callback.message.edit_text("Город не найден.")
    await state.clear()
    await callback.answer()

@dp.message(CityManage.name)
async def add_city_name(message: Message, state: FSMContext):
    city_name = message.text.strip()
    if city_name in data["cities"]:
        await message.answer("Такой город уже существует.")
        return
    data["cities"].append(city_name)
    save_data(data)
    await message.answer(f"✅ Город **{city_name}** добавлен.")
    await state.clear()

# ---------- Добавление/списание баланса ----------
@dp.message(F.text == "➕ Добавить баланс")
async def add_balance_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Введите ID пользователя и сумму через пробел.\nПример: `8213390123 5000`", parse_mode="Markdown")
    await state.set_state(BalanceOperation.user_id)
    await state.update_data(operation="add")

@dp.message(F.text == "➖ Списать баланс")
async def remove_balance_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Введите ID пользователя и сумму для списания через пробел.\nПример: `8213390123 1000`", parse_mode="Markdown")
    await state.set_state(BalanceOperation.user_id)
    await state.update_data(operation="remove")

@dp.message(BalanceOperation.user_id)
async def balance_operation_amount(message: Message, state: FSMContext):
    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Неверный формат. Введите ID и сумму через пробел.")
        return
    user_id = parts[0]
    amount = int(parts[1])
    data_state = await state.get_data()
    operation = data_state.get("operation")
    if user_id not in data["users"]:
        data["users"][user_id] = {
            "orders": [],
            "joined": datetime.now().isoformat(),
            "balance": 0
        }
    if operation == "add":
        data["users"][user_id]["balance"] += amount
        action_text = f"начислено **{amount} {CURRENCY}**"
    else:
        if data["users"][user_id]["balance"] < amount:
            await message.answer(f"❌ Недостаточно средств у пользователя. Баланс: {data['users'][user_id]['balance']} {CURRENCY}")
            await state.clear()
            return
        data["users"][user_id]["balance"] -= amount
        action_text = f"списано **{amount} {CURRENCY}**"
    save_data(data)
    await message.answer(f"✅ Пользователю `{user_id}` {action_text}. Новый баланс: {data['users'][user_id]['balance']} {CURRENCY}", parse_mode="Markdown")
    try:
        if operation == "add":
            await bot.send_message(int(user_id), f"💰 Ваш баланс пополнен на **{amount} {CURRENCY}**! Текущий баланс: {data['users'][user_id]['balance']} {CURRENCY}", parse_mode="Markdown")
        else:
            await bot.send_message(int(user_id), f"➖ С вашего баланса списано **{amount} {CURRENCY}** по решению администратора. Текущий баланс: {data['users'][user_id]['balance']} {CURRENCY}", parse_mode="Markdown")
    except:
        pass
    await state.clear()

# ---------- Создание фейкового отзыва ----------
@dp.message(F.text == "✍️ Создать отзыв")
async def create_review_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Введите **имя/ник** отправителя отзыва (например, 'Алексей'):")
    await state.set_state(ReviewCreation.name)

@dp.message(ReviewCreation.name)
async def review_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите **текст отзыва**:")
    await state.set_state(ReviewCreation.text)

@dp.message(ReviewCreation.text)
async def review_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer("Введите **дату** (в формате ДД.ММ.ГГГГ) или отправьте 'сегодня' для автоматической подстановки:")
    await state.set_state(ReviewCreation.date)

@dp.message(ReviewCreation.date)
async def review_date(message: Message, state: FSMContext):
    date_str = message.text.strip()
    if date_str.lower() == "сегодня":
        date_str = datetime.now().strftime("%d.%m.%Y")
    # простая проверка формата
    try:
        datetime.strptime(date_str, "%d.%m.%Y")
    except:
        await message.answer("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ или 'сегодня'.")
        return
    data_state = await state.get_data()
    new_id = data["next_review_id"]
    data["next_review_id"] += 1
    review = {
        "id": new_id,
        "name": data_state["name"],
        "text": data_state["text"],
        "date": date_str
    }
    data["reviews"].append(review)
    save_data(data)
    await state.clear()
    await message.answer(f"✅ Отзыв от **{review['name']}** добавлен!", parse_mode="Markdown", reply_markup=admin_keyboard())

# ---------- Рассылка ----------
@dp.message(F.text == "📢 Рассылка")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Введите текст рассылки (можно Markdown):")
    await state.set_state(BroadcastState.message)

@dp.message(BroadcastState.message)
async def broadcast_send(message: Message, state: FSMContext):
    text = message.text
    count = 0
    for user_id in data["users"].keys():
        try:
            await bot.send_message(int(user_id), text, parse_mode="Markdown")
            count += 1
        except:
            pass
    await message.answer(f"✅ Рассылка отправлена {count} пользователям.", reply_markup=admin_keyboard())
    await state.clear()

# ---------- Статистика ----------
@dp.message(F.text == "📊 Статистика")
async def admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    total_users = len(data["users"])
    total_orders = len(data["orders"])
    total_revenue = sum(o["price"] for o in data["orders"])
    products_count = len(data["products"])
    promocodes = len(data["promocodes"])
    total_balance = sum(u["balance"] for u in data["users"].values())
    reviews_count = len(data["reviews"])
    text = (
        f"📊 **Статистика {STORE_NAME}**\n\n"
        f"👥 Пользователей: {total_users}\n"
        f"🛍️ Заказов: {total_orders}\n"
        f"💰 Выручка: {total_revenue} {CURRENCY}\n"
        f"📦 Товаров: {products_count}\n"
        f"🎟 Промокодов: {promocodes}\n"
        f"💎 Общий баланс пользователей: {total_balance} {CURRENCY}\n"
        f"📝 Отзывов: {reviews_count}"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "📦 Список товаров")
async def admin_product_list(message: Message):
    if not is_admin(message.from_user.id):
        return
    if not data["products"]:
        await message.answer("Нет товаров.")
        return
    text = "📋 **Все товары:**\n\n"
    for p in data["products"]:
        text += f"ID: {p['id']} | {p['name']} | {p['price']} {CURRENCY}\nГорода: {', '.join(p.get('cities', []))}\n\n"
    await message.answer(text, parse_mode="Markdown")

# ---------- Промокоды ----------
@dp.message(F.text == "🎫 Создать промокод")
async def create_promo_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Введите **код** промокода:")
    await state.set_state(PromocodeState.code)

@dp.message(PromocodeState.code)
async def promo_code(message: Message, state: FSMContext):
    await state.update_data(code=message.text)
    await message.answer("Введите **скидку** (в % от 1 до 100):")
    await state.set_state(PromocodeState.discount)

@dp.message(PromocodeState.discount)
async def promo_discount(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите число.")
        return
    discount = int(message.text)
    if discount < 1 or discount > 100:
        await message.answer("Скидка от 1 до 100.")
        return
    await state.update_data(discount=discount)
    await message.answer("На сколько дней действует промокод? (число дней)")
    await state.set_state(PromocodeState.expires_days)

@dp.message(PromocodeState.expires_days)
async def promo_expires(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите число дней.")
        return
    days = int(message.text)
    expires = datetime.now() + timedelta(days=days)
    data_state = await state.get_data()
    new_promo = {
        "code": data_state["code"],
        "discount": data_state["discount"],
        "expires": expires.isoformat()
    }
    data["promocodes"].append(new_promo)
    save_data(data)
    await state.clear()
    await message.answer(
        f"🎫 Промокод **{new_promo['code']}** создан!\n"
        f"Скидка: {new_promo['discount']}%\n"
        f"Действует до: {expires.strftime('%d.%m.%Y')}",
        parse_mode="Markdown", reply_markup=admin_keyboard()
    )

# ========== ЗАПУСК ==========
async def main():
    print("Бот запущен. Нажми Ctrl+C для остановки.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
