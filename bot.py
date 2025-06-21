
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from datetime import datetime
from sheets import save_to_sheet
from access_control import is_allowed, add_user
from temp_storage import add_temp_entry, get_temp_entry, remove_temp_entry

load_dotenv()
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher(storage=MemoryStorage())

ADMIN_ID = int(os.getenv("ADMIN_ID", "425438049"))

FIELDS = [
    "Kaspi Pay-1", "Kaspi Pay-2", "Halyk-1", "Halyk-2",
    "Баллом", "Сертификат", "Наличка", "Талон", "Сотрудники"
]

BRANCHES = [
    "Маркет", "Кантин центр", "Кантин H блок", "Кантин Спорт",
    "Uldar Dorm", "Kyzdar Dorm", "Doner House", "Red Coffee",
    "Белка", "Кантин Раздача", "Кофе вендинг", "Киоск-1"
]

class ReportState(StatesGroup):
    choosing_branch = State()
    filling_values = State()

@dp.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if not is_allowed(user_id):
        add_temp_entry(user_id, {
            "username": message.from_user.full_name,
            "user_id": user_id
        })
        await bot.send_message(ADMIN_ID,
            f"🚫 Жаңа қолданушы рұқсат сұрады:

👤 Аты: {message.from_user.full_name}
🆔 ID: {user_id}

Рұқсат беру үшін:
/approve_{user_id}")
        return await message.answer("Сізге бұл ботты қолдануға рұқсат жоқ. Әкімші рұқсат берген соң ғана жұмыс істей аласыз.")

    await state.clear()
    kb = InlineKeyboardBuilder()
    for branch in BRANCHES:
        kb.button(text=branch, callback_data=branch)
    kb.adjust(2)
    await message.answer("📍 Қай бөлімшенің есебін толтырасыз?", reply_markup=kb.as_markup())
    await state.set_state(ReportState.choosing_branch)

@dp.callback_query(ReportState.choosing_branch)
async def branch_chosen(call: CallbackQuery, state: FSMContext):
    await state.update_data(branch=call.data, values={})
    await call.message.answer(f"✍️ {call.data} бөлімшесі таңдалды.

{FIELDS[0]} сомасын жазыңыз:")
    await state.update_data(current_field=0)
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
        def fmt(val): return f"{val:,}".replace(",", " ") + "тг"
        total = sum(values.values())
        cash_fmt = fmt(values.get("Наличка", 0))
        total_fmt = fmt(total)
        text = "\n".join(f"{k}: {fmt(v)}" for k, v in values.items())

        confirm_text = (
            f"✅ Барлығы енгізілді:\n\n{text}\n\n"
            f"💵 Наличка: *{cash_fmt}*\n📊 Жалпы: *{total_fmt}*"
        )

        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Растаймын", callback_data="confirm")
        kb.button(text="🔁 Қайта толтырамын", callback_data="restart")
        kb.adjust(2)

        await message.answer(confirm_text, parse_mode="Markdown", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "restart")
async def restart(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("🔁 Қайта бастау үшін /start командасын енгізіңіз.")

@dp.callback_query(F.data == "confirm")
async def confirm(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    values = data["values"]
    total = sum(values.values())

    user_id = call.from_user.id
    username = call.from_user.full_name
    entry = {
        "branch": data["branch"],
        "values": values,
        "username": username,
        "user_id": user_id,
        "total": total
    }

    if is_allowed(user_id):
        save_to_sheet(entry)
        await call.message.answer("✅ Есеп қабылданды! Рақмет.")
    else:
        add_temp_entry(user_id, entry)
        await call.message.answer("✅ Есеп уақытша сақталды. Әкімші рұқсат берген соң тіркеледі.")
        await bot.send_message(ADMIN_ID,
            f"👤 Жаңа қолданушы есеп жіберді:

🆔 {user_id}
📋 /approve_{user_id} арқылы рұқсат беріңіз.")

    await state.clear()

@dp.message(F.text.regexp(r"^/approve_(\d+)$"))
async def approve_user(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("Сізде рұқсат жоқ.")

    user_id = int(message.text.split("_")[1])
    entry = get_temp_entry(user_id)

    if not entry:
        return await message.answer("Бұл қолданушының уақытша деректері табылмады.")

    add_user(user_id)
    save_to_sheet(entry)
    remove_temp_entry(user_id)

    await message.answer(f"✅ {user_id} рұқсат берілді және есебі тіркелді.")
    await bot.send_message(user_id, "✅ Сізге ботты қолдануға рұқсат берілді.")

if __name__ == "__main__":
    dp.run_polling(bot)
