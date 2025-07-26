import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv
from deep_translator import GoogleTranslator

# Load .env
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

user_languages = {}
users_db = {}

def translate(text, target_lang):
    return GoogleTranslator(source='auto', target=target_lang).translate(text)

@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    user_id = message.from_user.id
    users_db[user_id] = datetime.now()
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔤 Inglizcha so'z")],
            [KeyboardButton(text="📚 Darsni boshlash")],
            [KeyboardButton(text="📞 Admin bilan bog'lanish")],
            [
                KeyboardButton(text="🇺🇿 O'zbekcha"),
                KeyboardButton(text="🇷🇺 Русский"),
                KeyboardButton(text="🇬🇧 English")
            ]
        ],
        resize_keyboard=True
    )
    await message.answer("👋 Salom! Tilni tanlang:", reply_markup=kb)

@dp.message(F.text.in_(["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇬🇧 English"]))
async def choose_language(message: Message):
    lang_map = {
        "🇺🇿 O'zbekcha": "uz",
        "🇷🇺 Русский": "ru",
        "🇬🇧 English": "en"
    }
    user_languages[message.from_user.id] = lang_map[message.text]
    await message.answer(f"✅ Til tanlandi: {message.text}. Endi matn yozing.", reply_markup=ReplyKeyboardRemove())

@dp.message(F.text == "📞 Admin bilan bog'lanish")
async def contact_admin(message: Message):
    await message.answer("👨‍💻 Admin: @masterplay707")

@dp.message(F.text == "📚 Darsni boshlash")
async def start_lesson(message: Message):
    await message.answer("📘 Hozircha dars moduli yo‘q. Tez orada qo‘shiladi!")

@dp.message(F.text == "🔤 Inglizcha so'z")
async def random_word(message: Message):
    await message.answer("📝 Bu bo‘lim ham tez orada ishga tushadi.")

@dp.message(F.text == "/statistics")
async def cmd_stats(message: Message):
    now = datetime.now()
    total = len(users_db)
    today = len([d for d in users_db.values() if d.date() == now.date()])
    week = len([d for d in users_db.values() if (now - d).days < 7])
    month = len([d for d in users_db.values() if (now - d).days < 30])
    await message.answer(
        f"<b>📊 Statistika</b>\n\n"
        f"<b>Umumiy foydalanuvchilar:</b> {total}\n"
        f"<b>Bugun qo‘shilganlar:</b> {today}\n"
        f"<b>Haftalik:</b> {week}\n"
        f"<b>Oylik:</b> {month}"
    )

@dp.message(F.text == "/admin")
async def cmd_admin(message: Message):
    await message.answer("👨‍💻 Admin bilan bog'lanish: @masterplay707")

@dp.message(F.text == "/help")
async def cmd_help(message: Message):
    await message.answer(
        "ℹ️ Yordam:\n\n"
        "🔹 /start – Botni ishga tushurish\n"
        "🔹 Tilni tanlang va matn kiriting – Tarjima qilish uchun\n"
        "🔹 /statistics – Foydalanuvchi statistikasi\n"
        "🔹 /admin – Admin bilan bog'lanish"
    )

@dp.message(F.text & (~F.command))
async def translate_handler(message: Message):
    lang = user_languages.get(message.from_user.id)
    if not lang:
        await message.answer("Iltimos, tilni tanlang. /start buyrug‘ini bosing.")
        return
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    try:
        result = translate(message.text, lang)
        await message.answer(f"🔁 Tarjima natijasi:\n<code>{result}</code>")
    except Exception as e:
        logger.error(f"Error in translation: {e}")
        await message.answer("❌ Tarjima qilishda xatolik yuz berdi.")

# Webhook uchun
async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL, secret_token=WEBHOOK_SECRET)
    logger.info(f"Webhook o‘rnatildi: {WEBHOOK_URL}")

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    logger.info("Webhook olib tashlandi")

def create_app():
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET).register(app, path=WEBHOOK_PATH)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    setup_application(app, dp, bot=bot)
    return app

if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
