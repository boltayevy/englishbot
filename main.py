import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from flask import Flask, request
from deep_translator import GoogleTranslator

# ==== ENVIRONMENT VARIABLELAR ====
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Telegram bot token
APP_URL = os.getenv("APP_URL")      # Masalan: https://yourbot.onrender.com

WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{APP_URL}{WEBHOOK_PATH}"

# ==== AIROGRAM SETUP ====
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ==== FLASK APP ====
app = Flask(__name__)

@app.route('/')
def index():
    return '🤖 Tarjimon bot ishlayapti!'

@app.route(WEBHOOK_PATH, methods=['POST'])
def process_webhook():
    if request.method == "POST":
        update = types.Update.to_object(request.json)
        dp.process_update(update)
        return {'ok': True}

# ==== Tarjima funksiyasi ====
def translate(text, target='uz'):
    return GoogleTranslator(source='auto', target=target).translate(text)

# ==== HANDLERLAR ====
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer("👋 Assalomu alaykum!\nMatn yuboring, men uni o'zbek tiliga tarjima qilaman.")

@dp.message_handler()
async def message_handler(message: types.Message):
    try:
        translated = translate(message.text)
        await message.answer(f"🔁 Tarjima:\n<code>{translated}</code>", parse_mode="HTML")
    except Exception as e:
        await message.answer("❌ Tarjima qilishda xatolik yuz berdi.")

# ==== Webhook sozlash ====
async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    print("Webhook o‘rnatildi:", WEBHOOK_URL)

async def on_shutdown(dp):
    await bot.delete_webhook()
    print("Webhook olib tashlandi.")

# ==== ASOSY START FUNKSIYASI ====
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host='0.0.0.0',
        port=int(os.environ.get("PORT", 5000)),
    )
