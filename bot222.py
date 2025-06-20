import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from datetime import datetime
from sheets import save_to_sheet

load_dotenv()
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher(storage=MemoryStorage())

# Параметрлер
FIELDS = [
    "Kaspi Pay1", "Kaspi Pay2", "Halyk bank1", "Halyk bank2",
    "Талон", "Сертификат", "Наличка", "Гости", "Сотрудники"
]

BRANCHES = [
    "Маркет", "Кантин центр", "Кантин H блок", "Кантин Спорт",
    "Uldar Dorm", "Kyzdar Dorm", "Doner House", "Red Coffee",
    "Белка", "Кантин Раздача", "Кофе вендинг", "Киоск-1"
]

class ReportState(StatesGroup):
    choosing_branch: State = State()
    filling_values: State = State()

@dp.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardBuilder()
    for branch in BRANCHES:
        kb.button(text=branch, callback_data=branch)
    kb.adjust(2)
    await message.answer("📍 Қай бөлімшенің есебін толтырасыз?", reply_markup=kb.as_markup())
    await state.set_state(ReportState.choosing_branch)

@dp.callback_query(ReportState.choosing_branch)
async def branch_chosen(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(branch=call.data, values={})
    await state.update_data(current_field=0)
    await call.message.answer(f"✍️ {call.data} бөлімшесі таңдалды.\n\n{FIELDS[0]} сомасын жазыңыз:")
    await state.set_state(ReportState.filling_values)

@dp.message(ReportState.filling_values)
async def fill_value(message: Message, state: FSMContext):
    data = await state.get_data()
    index = data["current_field"]
    field = FIELDS[index]

    try:
        value = int(message.text.replace(" ", "").replace("тг", ""))
    except ValueError:
        return await message.answer("❌ Тек сан енгізіңіз (мысалы: 12000)")

    values = data.get("values", {})
    values[field] = value
    await state.update_data(values=values)

    if index + 1 < len(FIELDS):
        next_field = FIELDS[index + 1]
        await state.update_data(current_field=index + 1)
        await message.answer(f"{next_field} сомасын жазыңыз:")
    else:
        total = sum(values.values())

        def fmt(val): return f"{val:,}".replace(",", " ")
        cash_fmt = fmt(values.get("Наличка", 0))
        total_fmt = fmt(total)

        text = "\n".join(f"{k}: {fmt(v)}" for k, v in values.items())
        confirm_text = (
            f"✅ Барлық мән енгізілді:\n\n{text}\n\n"
            f"💵 Наличка: *{cash_fmt}*\n📊 Жалпы: *{total_fmt}*"
        )

        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Растаймын", callback_data="confirm")
        kb.button(text="🔁 Қайта толтырамын", callback_data="restart")
        kb.adjust(2)

        await message.answer(confirm_text, parse_mode="Markdown", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "restart")
async def restart(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    await call.message.answer("🔁 Қайта бастау үшін /start деп жазыңыз.")

@dp.callback_query(F.data == "confirm")
async def confirm(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    branch = data["branch"]
    values = data["values"]
    full_name = call.from_user.full_name
    user_id = call.from_user.id
    total = sum(values.values())

    # Google Sheets-ке сақтау
    save_to_sheet(branch, full_name, user_id, values, total)

    await call.message.answer("✅ Есеп қабылданды! Рақмет.")
    await state.clear()

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
