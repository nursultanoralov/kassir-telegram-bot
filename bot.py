import os
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from sheets import save_to_sheet
from access_control import is_allowed, add_user
from temp_storage import add_temp_entry, get_temp_entry, remove_temp_entry

load_dotenv()

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher(storage=MemoryStorage())

ADMIN_ID = int(os.getenv("ADMIN_ID", 425438049))

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
    username = message.from_user.full_name

    # Әрқашан админге /restart құқығы бар
    if user_id != ADMIN_ID and not is_allowed(user_id):
        text = (
            f"🚫 Жаңа қолданушы рұқсат сұрады:\n"
            f"{username} (ID: {user_id})\n"
            f"Рұқсат беру үшін /approve_{user_id} немесе /reject_{user_id} деп жазыңыз."
        )
        await bot.send_message(chat_id=ADMIN_ID, text=text)
        return await message.answer("⏳ Сізге рұқсат берілмеген. Админ рұқсат беруі керек.")

    await state.clear()
    kb = InlineKeyboardBuilder()
    for branch in BRANCHES:
        kb.button(text=branch, callback_data=branch)
    kb.adjust(2)
    await message.answer("📍 Қай бөлімшенің есебін толтырасыз?", reply_markup=kb.as_markup())
    await state.set_state(ReportState.choosing_branch)


@dp.callback_query(ReportState.choosing_branch)
async def branch_chosen(call: CallbackQuery, state: FSMContext):
    await state.update_data(branch=call.data, values={}, current_field=0)
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
    await call.message.answer("🔁 Қайта бастау үшін /start командасын жазыңыз.")


@dp.callback_query(F.data == "confirm")
async def confirm(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data:
        return await call.message.answer("Қате: Мемлекет күйі бос.")

    branch = data["branch"]
    values = data["values"]
    username = call.from_user.full_name
    user_id = call.from_user.id

    entry = {
        "branch": branch,
        "values": values,
        "username": username,
        "user_id": user_id
    }

    if user_id == ADMIN_ID or is_allowed(user_id):
        save_to_sheet(branch, username, user_id, values)
        await call.message.answer("✅ Есеп қабылданды! Рақмет.")
    else:
        add_temp_entry(user_id, entry)
        kb = InlineKeyboardBuilder()
        kb.button(text=f"✅ Рұқсат беремін", callback_data=f"approve_{user_id}")
        kb.button(text=f"❌ Қайтару", callback_data=f"reject_{user_id}")
        kb.adjust(2)

        await bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"📥 Жаңа қолданушы есеп жіберді (күтіп тұр):\n"
                f"{username} (ID: {user_id})"
            ),
            reply_markup=kb.as_markup()
        )
        await call.message.answer("⏳ Есебіңіз админге жіберілді. Рұқсат күтіңіз.")

    await state.clear()


@dp.message(F.text.regexp(r"^/approve_(\d+)$"))
async def approve_by_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    user_id = int(message.text.split("_")[1])
    await handle_approval(user_id, approve=True, message=message)


@dp.message(F.text.regexp(r"^/reject_(\d+)$"))
async def reject_by_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    user_id = int(message.text.split("_")[1])
    await handle_approval(user_id, approve=False, message=message)


@dp.callback_query(F.data.regexp(r"^(approve|reject)_(\d+)$"))
async def handle_callback_approval(call: CallbackQuery):
    action, user_id = call.data.split("_")
    await handle_approval(int(user_id), approve=(action == "approve"), message=call.message)


async def handle_approval(user_id: int, approve: bool, message: Message | CallbackQuery):
    entry = get_temp_entry(user_id)
    if not entry:
        return await message.answer("❌ Бұл қолданушы үшін есеп табылмады.")

    if approve:
        add_user(user_id)
        save_to_sheet(entry["branch"], entry["username"], entry["user_id"], entry["values"])
        await bot.send_message(chat_id=user_id, text="✅ Есебіңіз қабылданды! Сізге рұқсат берілді.")
        await message.answer(f"✅ Қолданушы {entry['username']} (ID: {user_id}) рұқсат алып, есебі сақталды.")
    else:
        await bot.send_message(chat_id=user_id, text="❌ Сіздің есебіңіз қабылданбады. Қосымша ақпарат қажет.")
        await message.answer(f"🚫 Қолданушы {entry['username']} (ID: {user_id}) рұқсат берілмеді.")

    remove_temp_entry(user_id)


if __name__ == "__main__":
    dp.run_polling(bot)
