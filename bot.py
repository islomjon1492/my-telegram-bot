import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# Token va Admin ID
TOKEN = "8935218064:AAEWRF37n6ENH89rqtgAnvvbZL4eNOvz5Hk"
ADMIN_ID = 5566924199  

# Loyihangizning shaxsiy Render havolasi
RENDER_URL = "https://onrender.com" 

bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# --- MA'LUMOTLAR BAZASI (SQLite3) ---
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

def get_all_users():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, phone, role, level, username FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

def clear_all_users():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users")
    conn.commit()
    conn.close()
# ------------------------------------

class Registration(StatesGroup):
    waiting_for_phone = State()
    waiting_for_name = State()
    waiting_for_role = State()
    waiting_for_level = State()

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
    
    username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    
    # Bazaga yozish
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
    try: await bot.send_message(chat_id=ADMIN_ID, text=admin_text)
    except Exception as e: print(f"Xatolik: {e}")
    await state.clear()

# --- ADMIN PANEL VEB-SAYT QISMI (HTML) ---
async def admin_panel_page(request):
    users = get_all_users()
    total_users = len(users)
    
    # Jadval qatorlarini yaratish
    table_rows = ""
    for idx, user in enumerate(users, 1):
        table_rows += f"""
        <tr>
            <td>{idx}</td>
            <td>{user[0]}</td>
            <td>{user[1]}</td>
            <td>{user[2]}</td>
            <td>{user[3]}</td>
            <td>{user[4]}</td>
        </tr>
        """
        
    # Chiroyli HTML dizayn
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>LMC Bot Admin Panel</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; }}
            .container {{ max-width: 900px; background: white; margin: 0 auto; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; text-align: center; }}
            .stats {{ background: #e3f2fd; padding: 15px; border-radius: 6px; font-size: 18px; font-weight: bold; color: #0d47a1; margin-bottom: 20px; display: inline-block; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #007bff; color: white; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .btn-danger {{ background-color: #dc3545; color: white; padding: 10px 20px; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; float: right; text-decoration: none; }}
            .btn-danger:hover {{ background-color: #c82333; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>LMC Bot - Ro'yxatdan o'tganlar paneli</h1>
            
            <div class="stats">👥 Jami foydalanuvchilar: {total_users} ta</div>
            <a href="/clear" class="btn-danger" onclick="return confirm('Haqiqatdan ham hamma foydalanuvchilarni o\'chirib, bazani 0 qilmoqchimisiz?')">🔴 Bazani tozalash (Reset)</a>
            
            <table>
                <tr>
                    <th>#</th>
                    <th>Ism / Familiya</th>
                    <th>Telefon</th>
                    <th>Rol</th>
                    <th>Daraja</th>
                    <th>Telegram Username</th>
                </tr>
                {table_rows if table_rows else '<tr><td colspan="6" style="text-align:center;">Hozircha hech kim ro\'yxatdan o\'tmadi.</td></tr>'}
            </table>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

# Bazani tozalash funksiyasi
async def clear_database_handler(request):
    clear_all_users()
    # Tozalab bo'lgach, yana admin saytiga qaytarib yuboradi
    return web.HTTPFound('/')

async def on_startup(bot: Bot) -> None:
    init_db()
    await bot.set_webhook(url=f"{RENDER_URL}/webhook")

def main():
    app = web.Application()
    
    # Sayt yo'llari (Routing)
    app.router.add_get('/', admin_panel_page) # Asosiy sayt sahifasi
    app.router.add_get('/clear', clear_database_handler) # O'chirish havolasi
    
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path="/webhook")
    
    dp.startup.register(on_startup)
    setup_application(app, dp, bot=bot)
    
    web.run_app(app, host='0.0.0.0', port=8080)

if __name__ == '__main__':
    main()
