import os
import asyncio
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

# Токенді оқу
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS = [425438049]

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# --- Сұхбатты сақтау ---
user_sessions = {}

# --- FSM күйі ---
class SaleState(StatesGroup):
    choosing_branch = State()
    entering_data = State()
    confirm = State()


# --- Старт ---
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Сату орныңызды таңдаңыз:", reply_markup=branch_keyboard())
    await state.set_state(SaleState.choosing_branch)

# --- Филиал таңдау ---
@dp.message(SaleState.choosing_branch)
async def choose_branch(message: Message, state: FSMContext):
    branch = message.text.strip()
    await state.update_data(branch=branch, values={})
    await message.answer("Күнделікті сатылымды енгізіңіз:\n\n<b>Kaspi Pay-1:</b>")
    await state.set_state(SaleState.entering_data)


# --- Деректерді жинау ---
FIELDS = [
    "Kaspi Pay-1", "Kaspi Pay-2", "Halyk-1", "Halyk-2",
    "Баллом", "Сертификат", "Наличка", "Талон"
]

@dp.message(SaleState.entering_data)
async def enter_data(message: Message, state: FSMContext):
    data = await state.get_data()
    values = data.get("values", {})
    field_index = len(values)

    try:
        values[FIELDS[field_index]] = float(message.text)
    except ValueError:
        await message.answer("Санмен жазыңыз:")
        return

    await state.update_data(values=values)

    if field_index + 1 < len(FIELDS):
        await message.answer(f"<b>{FIELDS[field_index + 1]}:</b>")
    else:
        # Факт выручка есептеу
        total = sum(values.values())
        await state.update_data(total=total)
        summary = "\n".join([f"{k}: {v}" for k, v in values.items()])
        text = f"<b>Филиал:</b> {data['branch']}\n\n{summary}\n\n<b>Факт выручка:</b> {total}\n\nРастайсыз ба?"
        await message.answer(text, reply_markup=confirm_keyboard())
        await state.set_state(SaleState.confirm)


# --- Растау немесе қайта енгізу ---
@dp.callback_query(SaleState.confirm)
async def confirm_data(call: CallbackQuery, state: FSMContext):
    await call.answer()
    if call.data == "confirm":
        data = await state.get_data()
        username = call.from_user.username or "жоқ"
        full_name = call.from_user.full_name
        user_id = call.from_user.id
        date = datetime.now().strftime("%Y-%m-%d")
        total = data["total"]
        values = data["values"]
        branch = data["branch"]

        text = f"✅ <b>Жаңа сатылым</b>\n\n📅 <b>{date}</b>\n🏢 <b>{branch}</b>\n👤 <b>{full_name}</b>\n🆔 <code>{user_id}</code>\n\n"
        for k, v in values.items():
            text += f"{k}: {v}\n"
        text += f"\n<b>Факт выручка:</b> {total}"

        # Тек админге жіберу
        for admin_id in ADMIN_IDS:
            await bot.send_message(admin_id, text)

        await call.message.answer("✅ Ақпарат сақталды. Рахмет!")
        await state.clear()
    else:
        await call.message.answer("Қайтадан енгізу үшін /start басыңыз.")
        await state.clear()


# --- Командалар ---
@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer("🛠 Командалар:\n/start – қайта бастау\n/admin – админ бөлімі\n/restart – қайта бастау")


@dp.message(Command("restart"))
async def restart_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔄 Қайтадан бастайық.\nФилиал таңдаңыз:", reply_markup=branch_keyboard())
    await state.set_state(SaleState.choosing_branch)


@dp.message(Command("admin"))
async def admin_cmd(message: Message):
    if message.from_user.id in ADMIN_IDS:
        await message.answer("👤 Сіз админсіз.")
    else:
        await message.answer("🚫 Бұл команда тек админге арналған.")

@dp.message(Command("today"))
async def today_cmd(message: Message):
    if message.from_user.id in ADMIN_IDS:
        date = datetime.now().strftime("%d-%m-%Y")  # күн-ай-жыл
        await message.answer(f"📅 Бүгінгі күн: {date}")
    else:
        await message.answer("🚫 Бұл команда тек админге арналған.")

@dp.message(Command("id"))
async def id_cmd(message: Message):
    await message.answer(f"🆔 Сіздің ID: <code>{message.from_user.id}</code>")


# --- Кнопкалар ---
def branch_keyboard():
    kb = ReplyKeyboardBuilder()
    branches = [
        "Маркет", "Кантин центр", "Кантин H блок",
        "Кантин Спорт", "Uldar Dorm", "Kyzdar Dorm",
        "Doner House", "Red Coffee", "Белка",
        "Кантин Раздача", "Кофе вендинг", "Киоск-1"
    ]
    for i in range(0, len(branches), 2):
        kb.row(
            types.KeyboardButton(text=branches[i]),
            types.KeyboardButton(text=branches[i+1]) if i+1 < len(branches) else None
        )
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)


def confirm_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Растаймын", callback_data="confirm")
    kb.button(text="🔄 Қайта жазамын", callback_data="edit")
    return kb.as_markup()


# --- Бастау ---
async def main():
    print("Бот іске қосылды...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
