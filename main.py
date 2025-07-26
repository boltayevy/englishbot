import logging
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

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
    # kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔤 Inglizcha so'z")],
        [KeyboardButton(text="📚 Darsni boshlash")],
        [KeyboardButton(text="📞 Admin bilan bog'lanish")]
    ],
    resize_keyboard=True
)
    kb.add(KeyboardButton("🇺🇿 O'zbekcha"), KeyboardButton("🇷🇺 Русский"), KeyboardButton("🇬🇧 English"))
    await message.answer(
        "👋 Salom! Tilni tanlang:",
        reply_markup=kb
    )

@dp.message(F.text.in_(["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇬🇧 English"]))
async def choose_language(message: Message):
    lang_map = {"🇺🇿 O'zbekcha": "uz", "🇷🇺 Русский": "ru", "🇬🇧 English": "en"}
    user_languages[message.from_user.id] = lang_map[message.text]
    await message.answer(f"✅ Til tanlandi: {message.text}. Endi matn yozing.", reply_markup={"remove_keyboard": True})

@dp.message(F.text & (~F.command))
async def translate_handler(message: Message):
    lang = user_languages.get(message.from_user.id)
    if not lang:
        await message.answer("Iltimos, tilni tanlang. /start buyrug‘ini bosing.")
        return
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    try:
        result = translate(message.text, lang)
        await message.answer(f"🔁 Tarjima natijasi:\n<code>{result}</code>")
    except Exception as e:
        logger.error(f"Error in translation: {e}")
        await message.answer("❌ Xatolik yuz berdi.")

@dp.message(F.text == "/statistics")
async def cmd_stats(message: Message):
    now = datetime.now()
    total = len(users_db)
    today = len([d for d in users_db.values() if d.date() == now.date()])
    week = len([d for d in users_db.values() if (now - d).days < 7])
    month = len([d for d in users_db.values() if (now - d).days < 30])
    await message.answer(f"<b>Statistika</b>\n\nUmumiy: {total}\nBugun: {today}\nBu hafta: {week}\nBu oy: {month}")

@dp.message(F.text == "/admin")
async def cmd_admin(message: Message):
    await message.answer("👨‍💻 Admin: @masterplay707")

@dp.message(F.text == "/help")
async def cmd_help(message: Message):
    await message.answer("🔹 /start – tilni tanlash\n🔹 /statistics – statistika\n🔹 Tarjima qilish uchun matn yozing.")

async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL, secret_token=WEBHOOK_SECRET)
    logger.info("Webhook set: %s", WEBHOOK_URL)

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    logger.info("Webhook deleted")

def create_app():
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET).register(app, path=WEBHOOK_PATH)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    setup_application(app, dp, bot=bot)
    return app

if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
