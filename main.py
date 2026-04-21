import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

import database as db
import keyboards as kb
import analytics

load_dotenv()

ADMINS = [654714933, 6386475731]
bot = Bot(token=os.getenv("BOT_TOKEN"), default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()

class AddWallet(StatesGroup):
    address = State()
    network = State()
    label = State()

class QuickCheck(StatesGroup):
    address = State()

class EditLabel(StatesGroup):
    address = State()
    new_label = State()

class Broadcast(StatesGroup):
    message = State()

# --- ГЛАВНОЕ МЕНЮ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await db.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(f"🌘 <b>CAMORRA CHECKER</b>\nДобро пожаловать, {message.from_user.first_name}!", reply_markup=kb.get_main_menu(message.from_user.id))

# --- FAQ ---
@dp.callback_query(F.data == "faq")
async def show_faq(callback: types.CallbackQuery):
    text = (
        "🌘 <b>ИНФОРМАЦИЯ</b>\n\n"
        "<b>Мои кошельки:</b> список ваших сохраненных адресов.\n"
        "<b>Проверить кошелек:</b> быстрый разовый анализ адреса.\n"
        "<b>Добавить:</b> сохранить кошелек в базу для быстрого доступа."
    )
    await callback.message.edit_text(text, reply_markup=kb.get_main_menu(callback.from_user.id))

# --- БЫСТРАЯ ПРОВЕРКА ---
@dp.callback_query(F.data == "check_wallet")
async def check_wallet_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🔍 <b>Введите адрес для проверки:</b>")
    await state.set_state(QuickCheck.address)

@dp.message(QuickCheck.address)
async def check_wallet_proc(message: types.Message, state: FSMContext):
    addr = message.text.strip()
    await message.answer("⏳ Анализирую блокчейн...")
    report = await analytics.get_full_analytics(addr, "TRC20")
    await message.answer(report, reply_markup=kb.get_main_menu(message.from_user.id))
    await state.clear()

# --- МОИ КОШЕЛЬКИ ---
@dp.callback_query(F.data == "my_wallets")
async def show_wallets(callback: types.CallbackQuery):
    await callback.message.edit_text("🗂 <b>ВАША БАЗА АКТИВОВ:</b>", reply_markup=kb.get_wallets_nav_kb(callback.from_user.id))

@dp.callback_query(F.data.startswith("info:"))
async def wallet_info(callback: types.CallbackQuery):
    data = callback.data.split(":")
    addr, net = data[1], data[2]
    report = await analytics.get_full_analytics(addr, net)
    await callback.message.edit_text(report, reply_markup=kb.get_wallet_manage_kb(addr, net))

# --- ДОБАВЛЕНИЕ ---
@dp.callback_query(F.data == "add_wallet")
async def add_wallet_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 Введите адрес:")
    await state.set_state(AddWallet.address)

@dp.message(AddWallet.address)
async def add_wallet_addr(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="TRC20", callback_data="net:TRC20"))
    await message.answer("⚙️ Сеть:", reply_markup=builder.as_markup())
    await state.set_state(AddWallet.network)

@dp.callback_query(AddWallet.network, F.data.startswith("net:"))
async def add_wallet_net(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(network=callback.data.split(":")[1])
    await callback.message.edit_text("🏷 Введите метку:")
    await state.set_state(AddWallet.label)

@dp.message(AddWallet.label)
async def add_wallet_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await db.add_wallet(message.from_user.id, data['address'], data['network'], message.text.strip())
    await state.clear()
    await message.answer("✅ Добавлено!", reply_markup=kb.get_main_menu(message.from_user.id))

# --- УДАЛЕНИЕ И ПРАВКА ---
@dp.callback_query(F.data.startswith("del:"))
async def del_wallet(callback: types.CallbackQuery):
    addr = callback.data.split(":")[1]
    await db.delete_wallet(callback.from_user.id, addr)
    await callback.answer("🗑 Удалено")
    await show_wallets(callback)

@dp.callback_query(F.data.startswith("edit:"))
async def edit_label_start(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(edit_addr=callback.data.split(":")[1])
    await callback.message.answer("🏷 Новая метка:")
    await state.set_state(EditLabel.new_label)

@dp.message(EditLabel.new_label)
async def edit_label_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await db.update_label(message.from_user.id, data['edit_addr'], message.text.strip())
    await state.clear()
    await message.answer("✅ Готово!", reply_markup=kb.get_main_menu(message.from_user.id))

# --- АДМИНКА ---
@dp.callback_query(F.data == "admin_panel")
async def admin_menu(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMINS: return
    u, w = await db.get_admin_stats()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📢 Рассылка", callback_data="broadcast"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text(f"🔑 <b>ADMIN</b>\nЮзеров: {u}\nКошельков: {w}", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "to_main")
async def to_main(c: types.CallbackQuery):
    await c.message.edit_text("🌘 Меню:", reply_markup=kb.get_main_menu(c.from_user.id))

async def main():
    await db.init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
