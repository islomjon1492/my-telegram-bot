import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# Token va Admin ID
TOKEN = "8935218064:AAEWRF37n6ENH89rqtgAnvvbZL4eNOvz5Hk"
ADMIN_ID = 5566924199  

# Loyihangizning shaxsiy Render havolasi
RENDER_URL = "https://my-telegram-bot-bgpc.onrender.com" 

bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# --- MA'LUMOTLAR BAZASI BILAN ISHLASH ---
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            phone TEXT,
            name TEXT,
            role TEXT,
            level TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user(telegram_id, username, phone, name, role, level):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO users (telegram_id, username, phone, name, role, level)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (telegram_id, username, phone, name, role, level))
    conn.commit()
    conn.close()

def get_users_count():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count
# ----------------------------------------

class Registration(StatesGroup):
    waiting_for_phone = State()
    waiting_for_name = State()
    waiting_for_role = State()
    waiting_for_level = State()

# --- ADMIN UCHUN STATISTIKA BUYRUG'I ---
@dp.message(Command("stat"), F.from_user.id == ADMIN_ID)
async def cmd_stat(message: Message):
    total_users = get_users_count()
    await message.answer(f"📊 **Bot statistikasi:**\n\n👥 Jami foydalanuvchilar soni: {total_users} ta")

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer(
        f"Assalomu alaykum, {message.from_user.full_name}!\nBotimizga xush kelibsiz. Ro'yxatdan o'tish uchun pastdagi tugmani bosing:",
        reply_markup=keyboard
    )
    await state.set_state(Registration.waiting_for_phone)

@dp.message(Registration.waiting_for_phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith('+'): phone = '+' + phone
    await state.update_data(phone=phone)
    await message.answer("Endi ism va familiyangizni kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Registration.waiting_for_name)

@dp.message(Registration.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Listener"), KeyboardButton(text="Speaker")]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("Yo'nalishingizni tanlang:", reply_markup=keyboard)
    await state.set_state(Registration.waiting_for_role)

@dp.message(Registration.waiting_for_role, F.text.in_({"Listener", "Speaker"}))
async def process_role(message: Message, state: FSMContext):
    await state.update_data(role=message.text)
    await message.answer("Darajangizni (Level) yozib yuboring:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Registration.waiting_for_level)

@dp.message(Registration.waiting_for_level)
async def process_level(message: Message, state: FSMContext):
    await state.update_data(level=message.text)
    user_data = await state.get_data()
    
    # Bazaga saqlash
    username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    add_user(
        telegram_id=message.from_user.id,
        username=username,
        phone=user_data['phone'],
        name=user_data['name'],
        role=user_data['role'],
        level=user_data['level']
    )
    
    summary_text = f"🎉 Muvaffaqiyatli yakunlandi!\n\n📱 Telefon: {user_data['phone']}\n👤 Ism: {user_data['name']}\n🎭 Rol: {user_data['role']}\n📊 Daraja: {user_data['level']}"
    await message.answer(summary_text)
    
    admin_text = f"🎉 Yangi foydalanuvchi bazaga saqlandi!\n\n📱 Telefon: {user_data['phone']}\n👤 Ism: {user_data['name']}\n🎭 Rol: {user_data['role']}\n📊 Daraja: {user_data['level']}\n🔗 Telegram: {username}"
    
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text)
    except Exception as e:
        print(f"Xatolik: {e}")
    await state.clear()

async def on_startup(bot: Bot) -> None:
    init_db() # Bot yonganda bazani yaratadi
    await bot.set_webhook(url=f"{RENDER_URL}/webhook")

def main():
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path="/webhook")
    dp.startup.register(on_startup)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host='0.0.0.0', port=8080)

if __name__ == '__main__':
    main()
