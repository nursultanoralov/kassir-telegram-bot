import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from dotenv import load_dotenv
from sheets import save_to_sheet
from datetime import datetime

load_dotenv()

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"), default=Bot.Default(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

ADMIN_ID = 425438049
TIMEOUT_MINUTES = 10

class Form(StatesGroup):
    branch = State()
    values = State()

branches = [
    "Маркет", "Кантин центр", "Кантин H блок", "Кантин Спорт",
    "Uldar Dorm", "Kyzdar Dorm", "Doner House", "Red Coffee",
    "Белка", "Кантин Раздача", "Кофе вендинг", "Киоск-1"
]

fields = [
    "Kaspi Pay1", "Kaspi Pay2", "Halyk bank1", "Halyk bank2",
    "Талон", "Сертификат", "Наличка", "Гости", "Сотрудники"
]

def get_main_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(branch)] for branch in branches
    ], resize_keyboard=True)

def get_confirm_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton("✅ Растаймын")],
        [KeyboardButton("🔁 Қайта енгізу")]
    ], resize_keyboard=True)

@dp.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.branch)
    await message.answer("Бөлімшені таңдаңыз:", reply_markup=get_main_keyboard())

@dp.message(Form.branch)
async def branch_chosen(message: Message, state: FSMContext):
    if message.text not in branches:
        await message.answer("Келесі тізімнен бөлімшені таңдаңыз.")
        return
    await state.update_data(branch=message.text, values={})
    await state.set_state(Form.values)
    await ask_next_field(message, state)

async def ask_next_field(message: Message, state: FSMContext):
    data = await state.get_data()
    values = data["values"]
    for field in fields:
        if field not in values:
            await message.answer(f"{field} сомасын енгізіңіз (мысалы: 12000):")
            return
    total = sum(int(values.get(field, 0)) for field in fields)
    formatted_values = "\n".join([
        f"{field}: <b>{format(int(values.get(field, 0)), ',').replace(',', ' ')}</b> тг" if field in ["Наличка"] else
        f"{field}: {format(int(values.get(field, 0)), ',').replace(',', ' ')} тг"
        for field in fields
    ])
    formatted_total = f"<b>Жалпы: {format(total, ',').replace(',', ' ')} тг</b>"

    await message.answer(
        f"<b>Кіріс мәліметтері:</b>\n\n{formatted_values}\n\n{formatted_total}",
        reply_markup=get_confirm_keyboard()
    )

@dp.message(Form.values)
async def process_field(message: Message, state: FSMContext):
    data = await state.get_data()
    values = data["values"]
    current_field = None
    for field in fields:
        if field not in values:
            current_field = field
            break
    if not current_field:
        await message.answer("Бәрі енгізілген.")
        return

    if not message.text.replace(" ", "").isdigit():
        await message.answer("Сан енгізіңіз:")
        return

    values[current_field] = int(message.text.replace(" ", ""))
    await state.update_data(values=values)
    await ask_next_field(message, state)

@dp.message(F.text == "✅ Растаймын")
async def confirm_data(message: Message, state: FSMContext):
    data = await state.get_data()
    branch = data["branch"]
    values = data["values"]
    total = sum(int(values.get(field, 0)) for field in fields)

    await message.answer("Google Sheets кестесіне енгізілуде...")
    save_to_sheet(branch, message.from_user.full_name, message.from_user.id, values, total)
    await message.answer("✅ Енгізілді. /start командасы арқылы қайта бастауға болады.")
    await state.clear()

@dp.message(F.text == "🔁 Қайта енгізу")
async def retry_input(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Қайта басталды. Бөлімшені таңдаңыз:", reply_markup=get_main_keyboard())
    await state.set_state(Form.branch)

@dp.message(F.text == "/help")
async def help_handler(message: Message, state: FSMContext):
    await message.answer("🛠 Көмек алу үшін /start деп жазыңыз.\nМәзірден бөлімшені таңдап, сомаларды енгізіңіз.")

@dp.message(F.text == "/admin")
async def admin_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Сізде рұқсат жоқ.")
        return
    await message.answer(f"Admin панелі\n\nID: <code>{message.from_user.id}</code>\nАты: {message.from_user.full_name}")

@dp.message(F.text == "/restart")
async def restart_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Қайтадан басталды. Бөлімшені таңдаңыз:", reply_markup=get_main_keyboard())
    await state.set_state(Form.branch)

async def clear_old_sessions():
    while True:
        await asyncio.sleep(60)
        now = datetime.now()
        # Мұнда 10 минут өткен сессияларды FSMContext арқылы тазалауға болады егер сақталса

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
