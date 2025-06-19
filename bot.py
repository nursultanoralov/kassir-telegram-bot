import os
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from sheets import save_to_sheet

load_dotenv()

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"), parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

BRANCHES = [
    "Маркет", "Кантин центр", "Кантин H блок", "Кантин Спорт",
    "Uldar Dorm", "Kyzdar Dorm", "Doner House", "Red Coffee",
    "Белка", "Кантин Раздача", "Кофе вендинг", "Киоск-1"
]

FIELDS = [
    "Kaspi Pay1", "Kaspi Pay2", "Halyk bank1", "Halyk bank2",
    "Талон", "Сертификат", "Наличка", "Гости", "Сотрудники"
]

class Form(StatesGroup):
    choosing_branch = State()
    filling_data = State()
    confirming = State()

user_data = {}

@dp.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()
    buttons = [[KeyboardButton(text=branch)] for branch in BRANCHES]
    markup = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await message.answer("Филиалды таңдаңыз:", reply_markup=markup)
    await state.set_state(Form.choosing_branch)

@dp.message(Form.choosing_branch)
async def choose_branch(message: Message, state: FSMContext):
    branch = message.text
    if branch not in BRANCHES:
        return await message.answer("Тізімнен филиалды таңдаңыз.")
    user_data[message.from_user.id] = {"branch": branch, "data": {}}
    await state.update_data(index=0)
    await message.answer(f"{FIELDS[0]}:")
    await state.set_state(Form.filling_data)

@dp.message(Form.filling_data)
async def fill_data(message: Message, state: FSMContext):
    try:
        amount = int(message.text.replace(" ", ""))
    except ValueError:
        return await message.answer("Сан енгізіңіз:")

    state_data = await state.get_data()
    index = state_data.get("index", 0)
    field = FIELDS[index]
    user_data[message.from_user.id]["data"][field] = amount

    if index + 1 < len(FIELDS):
        await state.update_data(index=index + 1)
        await message.answer(f"{FIELDS[index + 1]}:")
    else:
        data = user_data[message.from_user.id]["data"]
        total = sum(data.values())
        user_data[message.from_user.id]["total"] = total

        lines = []
        for f in FIELDS:
            value = data.get(f, 0)
            if f == "Наличка":
                lines.append(f"<b>{f}</b>: <b>{value:,}тг</b>".replace(",", " "))
            else:
                lines.append(f"{f}: {value:,}тг".replace(",", " "))
        lines.append(f"\n<b>Жалпы сома:</b> <b>{total:,}тг</b>".replace(",", " "))

        markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Растаймын")], [KeyboardButton(text="Қайта енгізу")]],
            resize_keyboard=True)
        await message.answer("\n".join(lines), reply_markup=markup)
        await state.set_state(Form.confirming)

@dp.message(Form.confirming)
async def confirm(message: Message, state: FSMContext):
    if message.text == "Қайта енгізу":
        await state.update_data(index=0)
        await message.answer(f"{FIELDS[0]}:")
        await state.set_state(Form.filling_data)
    elif message.text == "Растаймын":
        uid = message.from_user.id
        username = message.from_user.full_name
        branch = user_data[uid]["branch"]
        values = user_data[uid]["data"]
        total = user_data[uid]["total"]
        save_to_sheet(branch, username, uid, values, total)
        await message.answer("✅ Мәліметтер Google Sheets-ке енгізілді!",
                             reply_markup=ReplyKeyboardMarkup(
                                 keyboard=[[KeyboardButton(text="/start")]], resize_keyboard=True))
        await state.clear()

@dp.message(F.text.in_({"/cancel", "cancel"}))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Операция тоқтатылды. Қайта бастау үшін /start басыңыз.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
