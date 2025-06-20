import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery
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

# Айнымалылар
ADMIN_ID = 425438049
FIELDS = ["Kaspi Pay-1", "Kaspi Pay-2", "Halyk-1", "Halyk-2", "Баллом", "Сертификат", "Наличка", "Талон"]
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
    await call.message.answer(f"✍️ {call.data} бөлімшесі таңдалды.\n\n{FIELDS[0]} сомасын жазыңыз:")
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
    await call.message.answer("🔁 Қайта бастаймыз. /start деп бастау керек.")

@dp.callback_query(F.data == "confirm")
async def confirm(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    branch = data["branch"]
    values = data["values"]
    full_name = call.from_user.full_name
    user_id = call.from_user.id
    total = sum(values.values())

    if is_allowed(user_id):
        save_to_sheet(branch, full_name, user_id, values, total)
        await call.message.answer("✅ Есеп қабылданды! Рақмет.")
    else:
        entry = {
            "branch": branch,
            "username": full_name,
            "user_id": user_id,
            "values": values,
            "total": total
        }
        add_temp_entry(user_id, entry)

        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Рұқсат беру", callback_data=f"approve_{user_id}")
        kb.button(text="❌ Бас тарту", callback_data=f"deny_{user_id}")
        kb.adjust(2)

        await bot.send_message(
            ADMIN_ID,
            f"🆕 Жаңа қолданушы есеп толтырды:\n\n👤 {full_name}\n🆔 ID: {user_id}\n📍 Бөлімше: {branch}\n💰 Жалпы сома: {total:,} тг\n\nРұқсат бересіз бе?",
            reply_markup=kb.as_markup()
        )

        await call.message.answer("⏳ Admin рұқсатын күтіңіз. Есебіңіз уақытша сақталды.")
    await state.clear()

@dp.callback_query(F.data.startswith("approve_"))
async def approve_user(call: CallbackQuery):
    user_id = int(call.data.split("_")[1])
    entry = get_temp_entry(user_id)

    if entry:
        add_user(user_id)
        save_to_sheet(entry["branch"], entry["username"], entry["user_id"], entry["values"])
        remove_temp_entry(user_id)
        await bot.send_message(user_id, "✅ Сізге рұқсат берілді. Есебіңіз тіркелді.")
        await call.message.edit_text("✅ Қолданушыға рұқсат берілді.")
    else:
        await call.message.edit_text("⚠️ Мәлімет табылмады.")

@dp.callback_query(F.data.startswith("deny_"))
async def deny_user(call: CallbackQuery):
    user_id = int(call.data.split("_")[1])
    remove_temp_entry(user_id)
    await bot.send_message(user_id, "❌ Сізге рұқсат берілмеді. Қосымша ақпарат алу үшін әкімшіге хабарласыңыз.")
    await call.message.edit_text("🚫 Қолданушыға рұқсат берілмеді.")

if __name__ == "__main__":
    dp.run_polling(bot)
