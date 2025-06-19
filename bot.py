import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable is missing")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command(commands=["start"]))
async def start_cmd(message: Message):
    await message.answer("Сәлем! Мен кассир бот болып жұмыс істеймін 🧾")

@dp.message()
async def echo(message: Message):
    await message.answer(f"👇 Мен қайталаймын:\n“{message.text}”")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
