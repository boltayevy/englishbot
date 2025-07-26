import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from dotenv import load_dotenv
from deep_translator import GoogleTranslator

# .env fayldan o'qish
load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Log sozlash
logging.basicConfig(level=logging.INFO)

# Botni yaratish
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Foydalanuvchi tillari
user_languages = {}


def translate(text, target_lang):
    return GoogleTranslator(source='auto', target=target_lang).translate(text)


@dp.message(F.text == "/start")
async def start_handler(message: Message):
    kb = [
        [{"text": "🇺🇿 O'zbekcha"}, {"text": "🇷🇺 Русский"}, {"text": "🇬🇧 English"}]
    ]
    await message.answer(
        "👋 Salom! Men matnni siz tanlagan tilga tarjima qilaman.\n\n⬇ Tilni tanlang:",
        reply_markup={"keyboard": kb, "resize_keyboard": True}
    )


@dp.message(F.text.in_(["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇬🇧 English"]))
async def language_selected(message: Message):
    lang_map = {"🇺🇿 O'zbekcha": "uz", "🇷🇺 Русский": "ru", "🇬🇧 English": "en"}
    user_languages[message.from_user.id] = lang_map[message.text]
    await message.answer(
        f"✅ Til tanlandi: {message.text}\nEndi tarjima qilinadigan matnni yuboring.",
        reply_markup={"remove_keyboard": True}
    )


@dp.message(F.text)
async def translate_handler(message: Message):
    lang = user_languages.get(message.from_user.id)
    if not lang:
        await message.answer("Iltimos, avval tilni tanlang. /start buyrug‘ini bosing.")
        return

    try:
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        translated = translate(message.text, lang)
        await message.answer(f"🔁 Tarjima:\n<code>{translated}</code>")
    except Exception:
        await message.answer("❌ Tarjima qilishda xatolik yuz berdi. Qayta urinib ko‘ring.")


@dp.message(F.text == "/admin")
async def admin_handler(message: Message):
    await message.answer("📞 Bog‘lanish uchun admin: @masterplay707")


@dp.message(F.text == "/help")
async def help_handler(message: Message):
    await message.answer(
        "ℹ️ Matn yuboring, men uni tanlangan tilga tarjima qilaman. Tilni o‘zgartirish uchun /start ni bosing."
    )


# Webhookni sozlash
async def on_startup(dispatcher: Dispatcher, bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)


def create_app():
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET).register(app, path=WEBHOOK_PATH)
    app.on_startup.append(on_startup)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), port=8000)
