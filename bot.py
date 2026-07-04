import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiohttp import web

# Token va Admin ID
TOKEN = "8935218064:AAEWRF37n6ENH89rqtgAnvvbZL4eNOvz5Hk"
ADMIN_ID = 5566924199  

bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

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
        f"Assalomu alaykum, {message.from_user.full_name}!\nBotimizga xush kelibsiz. Ro'yxatdan o'tish uchun tugmani bosing:",
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
    
    summary_text = f"🎉 Muvaffaqiyatli yakunlandi!\n\n📱 Telefon: {user_data['phone']}\n👤 Ism: {user_data['name']}\n🎭 Rol: {user_data['role']}\n📊 Daraja: {user_data['level']}"
    await message.answer(summary_text)
    
    username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    admin_text = f"🎉 Yangi foydalanuvchi!\n\n📱 Telefon: {user_data['phone']}\n👤 Ism: {user_data['name']}\n🎭 Rol: {user_data['role']}\n📊 Daraja: {user_data['level']}\n🔗 Telegram: {username}"
    
    try: await bot.send_message(chat_id=ADMIN_ID, text=admin_text)
    except Exception as e: print(f"Xatolik: {e}")
    await state.clear()

# Server uchun soxta sahifa (Render o'chib qolmasligi uchun)
async def handle(request):
    return web.Response(text="Bot ishlamoqda...")

async def main():
    # Botni orqa fonda ishga tushiramiz
    asyncio.create_task(dp.start_polling(bot))
    
    # Web serverni yoqamiz
    app = web.Application()
    app.router.add_get('/', handle)
    return app

if __name__ == '__main__':
    app = asyncio.run(main())
    web.run_app(app, port=8080)
