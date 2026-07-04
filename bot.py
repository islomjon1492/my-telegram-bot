import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, Update
from aiohttp import web

# Token va Admin ID
TOKEN = "8935218064:AAEWRF37n6ENH89rqtgAnvvbZL4eNOvz5Hk"
ADMIN_ID = 5566924199  

# Loyihangizning shaxsiy Render havolasi (Oxirida / belgisi bo'lmasligi shart!)
RENDER_URL = "https://my-telegram-bot-bgpc.onrender.com" 

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
    
    summary_text = f"🎉 Muvaffaqiyatli yakunlandi!\n\n📱 Telefon: {user_data['phone']}\n👤 Ism: {user_data['name']}\n🎭 Rol: {user_data['role']}\n📊 Daraja: {user_data['level']}"
    await message.answer(summary_text)
    
    username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    admin_text = f"🎉 Yangi foydalanuvchi!\n\n📱 Telefon: {user_data['phone']}\n👤 Ism: {user_data['name']}\n🎭 Rol: {user_data['role']}\n📊 Daraja: {user_data['level']}\n🔗 Telegram: {username}"
    
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text)
    except Exception as e:
        print(f"Xatolik: {e}")
    await state.clear()

# Telegramdan keladigan Webhook so'rovlarini qabul qilish funksiyasi
async def telegram_webhook_handler(request):
    try:
        json_data = await request.json()
        update = Update.model_validate(json_data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        logging.error(f"Webhook error: {e}")
    return web.Response(text="OK")

async def on_startup(app):
    # Telegram tizimiga bizning Render serverimiz manzilini ulaymiz
    await bot.set_webhook(url=f"{RENDER_URL}/webhook")
    print("Webhook muvaffaqiyatli o'rnatildi!")

async def main():
    app = web.Application()
    app.router.add_post('/webhook', telegram_webhook_handler)
    app.on_startup.append(on_startup)
    return app

if __name__ == '__main__':
    app = asyncio.run(main())
    web.run_app(app, host='0.0.0.0', port=8080)
