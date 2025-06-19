import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv

load_dotenv()

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

ADMIN_IDS = [123456789]  # ← Мұнда өз Telegram ID-нізді жазыңыз

branches = [
    "Маркет", "Doner House",
    "Кантин центр", "Red Coffee",
    "Кантин Н блок", "Белка",
    "Кантин Спорт", "Кантин Раздача",
    "Uldar Dorm", "Кофе вендинг",
    "Kyzdar Dorm", "Киоск-1"
]

class SalesStates(StatesGroup):
    branch = State()
    kaspi1 = State()
    kaspi2 = State()
    halyk1 = State()
    halyk2 = State()
    ballom = State()
    sert = State()
    nal = State()
    talon = State()
    confirm = State()

async def check_timeout(message: Message, state: FSMContext):
    data = await state.get_data()
    start_time = data.get("start_time")
    if start_time and (datetime.now().timestamp() - start_time > 600):  # 10 минут
        await state.clear()
        await message.answer("⏰ Уақыт өтіп кетті. Бәрін қайтадан бастаймыз.\nҚай бөлімшесіз?", reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=branches[i]), KeyboardButton(text=branches[i + 1])] for i in range(0, len(branches), 2)],
            resize_keyboard=True
        ))
        await state.set_state(SalesStates.branch)
        return False
    return True

@dp.message(commands=["start"])
async def start(message: Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=branches[i]), KeyboardButton(text=branches[i + 1])] for i in range(0, len(branches), 2)],
        resize_keyboard=True
    )
    await message.answer("Қай бөлімшесіз?", reply_markup=keyboard)
    await state.set_state(SalesStates.branch)

@dp.message(commands=["restart"])
async def manual_restart(message: Message, state: FSMContext):
    await state.clear()
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=branches[i]), KeyboardButton(text=branches[i + 1])] for i in range(0, len(branches), 2)],
        resize_keyboard=True
    )
    await message.answer("🔄 Барлығы өшірілді. Қай бөлімшесіз?", reply_markup=keyboard)
    await state.set_state(SalesStates.branch)

@dp.message(commands=["cancel"])
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Процесс тоқтатылды. Қаласаңыз /start деп қайта бастай аласыз.", reply_markup=ReplyKeyboardRemove())

@dp.message(commands=["help"])
async def help_command(message: Message):
    await message.answer(
        "📋 Командалар тізімі:\n"
        "/start – Ботты бастау\n"
        "/restart – Барлығын қайта бастау\n"
        "/cancel – Тоқтату\n"
        "/help – Анықтама\n"
        "/admin – Тек админ үшін мәзір\n"
        "/today – (әзірше) демо: бүгінгі дата\n"
    )

@dp.message(commands=["admin"])
async def admin_only(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Бұл команда тек админдерге арналған.")
        return
    await message.answer("🔐 Админ мәзірі (келесі қадам: Google Sheets, есеп, фильтр т.б.)")

@dp.message(commands=["today"])
async def today_command(message: Message):
    await message.answer(f"📅 Бүгінгі күн: {datetime.today().strftime('%d.%m.%Y')}")

@dp.message(SalesStates.branch)
async def set_branch(message: Message, state: FSMContext):
    if message.text not in branches:
        await message.answer("Кнопкадан таңдаңыз.")
        return
    await state.update_data(branch=message.text, start_time=datetime.now().timestamp())
    await message.answer("Kaspi Pay-1 сомасын жазыңыз:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(SalesStates.kaspi1)

async def ask_next(message: Message, state: FSMContext, field: str, next_state: State, prompt: str):
    if not await check_timeout(message, state):
        return
    if not message.text.isdigit():
        await message.answer("Тек сандармен жазыңыз:")
        return
    await state.update_data(**{field: int(message.text)})
    await message.answer(prompt)
    await state.set_state(next_state)

@dp.message(SalesStates.kaspi1)
async def kaspi1(message: Message, state: FSMContext):
    await ask_next(message, state, "kaspi1", SalesStates.kaspi2, "Kaspi Pay-2 сомасы:")

@dp.message(SalesStates.kaspi2)
async def kaspi2(message: Message, state: FSMContext):
    await ask_next(message, state, "kaspi2", SalesStates.halyk1, "Halyk-1 сомасы:")

@dp.message(SalesStates.halyk1)
async def halyk1(message: Message, state: FSMContext):
    await ask_next(message, state, "halyk1", SalesStates.halyk2, "Halyk-2 сомасы:")

@dp.message(SalesStates.halyk2)
async def halyk2(message: Message, state: FSMContext):
    await ask_next(message, state, "halyk2", SalesStates.ballom, "Баллом сомасы:")

@dp.message(SalesStates.ballom)
async def ballom(message: Message, state: FSMContext):
    await ask_next(message, state, "ballom", SalesStates.sert, "Сертификат сомасы:")

@dp.message(SalesStates.sert)
async def sert(message: Message, state: FSMContext):
    await ask_next(message, state, "sert", SalesStates.nal, "Наличка сомасы:")

@dp.message(SalesStates.nal)
async def nal(message: Message, state: FSMContext):
    await ask_next(message, state, "nal", SalesStates.talon, "Талон сомасы:")

@dp.message(SalesStates.talon)
async def talon(message: Message, state: FSMContext):
    if not await check_timeout(message, state):
        return
    if not message.text.isdigit():
        await message.answer("Санды дұрыс енгізіңіз:")
        return
    await state.update_data(talon=int(message.text))
    data = await state.get_data()
    total = sum([data[key] for key in ["kaspi1", "kaspi2", "halyk1", "halyk2", "ballom", "sert", "nal", "talon"]])
    await state.update_data(total=total)
    date_str = datetime.today().strftime("%d.%m.%Y")
    result = (
        f"📅 Күні: {date_str}\n"
        f"🏢 Бөлімше: {data['branch']}\n\n"
        f"Kaspi Pay-1: {data['kaspi1']}\n"
        f"Kaspi Pay-2: {data['kaspi2']}\n"
        f"Halyk-1: {data['halyk1']}\n"
        f"Halyk-2: {data['halyk2']}\n"
        f"Баллом: {data['ballom']}\n"
        f"Сертификат: {data['sert']}\n"
        f"Наличка: {data['nal']}\n"
        f"Талон: {data['talon']}\n\n"
        f"💰 Жалпы: {total}"
    )
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Растаймын"), KeyboardButton(text="🔁 Қайта жазамын")]],
        resize_keyboard=True
    )
    await message.answer(result, reply_markup=keyboard)
    await state.set_state(SalesStates.confirm)

@dp.message(SalesStates.confirm)
async def confirm(message: Message, state: FSMContext):
    if message.text == "✅ Растаймын":
        await message.answer("✅ Мәлімет сақталды! (кейін Google Sheets-ке жазылады)", reply_markup=ReplyKeyboardRemove())
        await state.clear()
    elif message.text == "🔁 Қайта жазамын":
        await message.answer("Бәрін қайта бастаймыз. /start басыңыз", reply_markup=ReplyKeyboardRemove())
        await state.clear()
    else:
        await message.answer("✅ немесе 🔁 кнопкаларын таңдаңыз")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
