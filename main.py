import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from deep_translator import GoogleTranslator

# 🔐 Token va Webhook URL
API_TOKEN = os.getenv("BOT_TOKEN", "YOUR_REAL_TOKEN")
WEBHOOK_SECRET = 'my-secret-token'
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = os.getenv("WEBHOOK_URL", f"https://your-app.onrender.com{WEBHOOK_PATH}")

# 📋 Log
logging.basicConfig(level=logging.INFO)

# 🤖 Bot va dispatcher
bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())

# 🌐 Foydalanuvchi tili saqlanadi (user_id -> til)
user_languages = {}


# 🔤 Tarjima funksiyasi
def translate(text, target_lang):
    return GoogleTranslator(source='auto', target=target_lang).translate(text)


# 🚀 /start komandasi
@dp.message(commands=["start"])
async def start_handler(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇬🇧 English")
    await message.reply(
        "👋 Assalomu alaykum!\nMen siz yozgan matnni tanlagan tilga tarjima qilaman.\n\n⬇ Iltimos, tilni tanlang:",
        reply_markup=kb
    )


# 🌍 Til tanlash
@dp.message(lambda msg: msg.text in ["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇬🇧 English"])
async def set_language(message: types.Message):
    lang_map = {"🇺🇿 O'zbekcha": "uz", "🇷🇺 Русский": "ru", "🇬🇧 English": "en"}
    user_languages[message.from_user.id] = lang_map[message.text]
    await message.reply(
        f"✅ Siz {message.text} tilini tanladingiz.\nTarjima qilish uchun matn yuboring.",
        reply_markup=types.ReplyKeyboardRemove()
    )


# ✍ Matn tarjimasi
@dp.message()
async def translate_handler(message: types.Message):
    lang = user_languages.get(message.from_user.id)
    if not lang:
        await message.reply("Iltimos, avval /start buyrug'ini bosib tilni tanlang.")
        return

    await bot.send_chat_action(message.chat.id, "typing")  # Typing animatsiya

    try:
        translated = translate(message.text, lang)
        await message.reply(f"🔁 Tarjima:\n<code>{translated}</code>")
    except Exception as e:
        logging.error(f"Tarjima xatosi: {e}")
        await message.reply("❌ Tarjima qilishda xatolik yuz berdi.")


# 👤 /admin komandasi
@dp.message(commands=["admin"])
async def admin_handler(message: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📞 Bog‘lanish", url="https://t.me/masterplay707")],
        [types.InlineKeyboardButton(text="💰 Premium olish", callback_data="buy_premium")]
    ])
    await message.reply("Admin bilan bog‘lanish yoki premium olish:", reply_markup=kb)


# 🆘 /help komandasi
@dp.message(commands=["help"])
async def help_handler(message: types.Message):
    await message.reply(
        "ℹ️ Men siz yuborgan matnni tanlagan tilga tarjima qilaman.\n"
        "Tilni tanlash uchun /start ni bosing.\n"
        "Admin uchun: /admin"
    )


# 💰 Premium funksiya (kelajakda to‘liq qilish uchun tayyor)
@dp.callback_query(lambda c: c.data == "buy_premium")
async def buy_premium(call: types.CallbackQuery):
    await call.message.edit_text(
        "🚀 Premium xususiyatlar hozirda tayyorlanmoqda.\n\n"
        "✅ Yaqin orada quyidagilar qo‘shiladi:\n"
        "- 🔊 Ovozli tarjima\n"
        "- 🗂 Ko‘p tilli matnlar\n"
        "- 📈 Statistika va o‘z tarixingiz\n\n"
        "👤 Admin bilan bog‘lanish: @masterplay707"
    )


# 🔗 Webhook uchun
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL, secret_token=WEBHOOK_SECRET)


def create_app():
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET).register(app, path=WEBHOOK_PATH)
    app.on_startup.append(lambda _: on_startup(bot))
    return app


if __name__ == '__main__':
    web.run_app(create_app(), host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
