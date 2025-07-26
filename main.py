# main.py
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot and Dispatcher
bot = Bot(token=API_TOKEN, default=types.DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

# User statistics (for demo purpose only)
users_db = {}

@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    user_id = message.from_user.id
    now = datetime.now()
    users_db[user_id] = now
    await message.answer("Salom! Bot ishga tushdi.\n/statistics buyrug'i orqali statistikani ko'rishingiz mumkin.")

@dp.message(F.text == "/statistics")
async def get_statistics(message: Message):
    now = datetime.now()
    today = [dt for dt in users_db.values() if dt.date() == now.date()]
    week = [dt for dt in users_db.values() if (now - dt).days < 7]
    month = [dt for dt in users_db.values() if (now - dt).days < 30]
    total = len(users_db)
    await message.answer(f"<b>📊 Statistika:</b>\n\nTotal foydalanuvchilar: {total}\nBugun: {len(today)}\nBu hafta: {len(week)}\nBu oy: {len(month)}")

@dp.message(F.text == "/admin")
async def get_admin_info(message: Message):
    await message.answer("<b>👨‍💻 Admin:</b> @your_admin_username")

async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)
    logger.info("Webhook o'rnatildi: %s", WEBHOOK_URL)

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    logger.info("Webhook o'chirildi.")

def create_app():
    app = web.Application()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp)
    return app

if __name__ == "__main__":
    web.run_app(create_app(), port=8000)
