import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

import database as db
import keyboards as kb
import analytics

load_dotenv()

# Твои ID
ADMINS = [654714933, 6386475731]

bot = Bot(token=os.getenv("BOT_TOKEN"), default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()

class AddWallet(StatesGroup):
    address = State()
    network = State()
    label = State()

class EditLabel(StatesGroup):
    address = State()
    new_label = State()

class Broadcast(StatesGroup):
    message = State()

# СТАРТ (Работает у всех!)
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        await db.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    except Exception as e:
        print(f"Ошибка БД: {e}")
    
    await message.answer(
        f"🌘 <b>CAMORRA CHECKER</b>\nДобро пожаловать, {message.from_user.first_name}.\n\nВыберите действие:", 
        reply_markup=kb.get_main_menu(message.from_user.id)
    )

# МОИ КОШЕЛЬКИ (Работает у всех)
@dp.callback_query(F.data == "my_wallets")
async def show_wallets(callback: types.CallbackQuery):
    await callback.message.edit_text("🗂 <b>ВАША БАЗА АКТИВОВ:</b>", reply_markup=kb.get_wallets_nav_kb(callback.from_user.id))

# ИНФО О КОШЕЛЬКЕ (Аналитика + кнопки удаления/правки)
@dp.callback_query(F.data.startswith("info:"))
async def wallet_info(callback: types.CallbackQuery):
    data = callback.data.split(":")
    addr, net = data[1], data[2]
    await callback.answer("⏳ Собираю данные...")
    report = await analytics.get_full_analytics(addr, net)
    await callback.message.edit_text(report, reply_markup=kb.get_wallet_manage_kb(addr, net))

# ДОБАВЛЕНИЕ КОШЕЛЬКА (FSM)
@dp.callback_query(F.data == "add_wallet")
async def add_wallet_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 <b>Введите адрес кошелька:</b>")
    await state.set_state(AddWallet.address)

@dp.message(AddWallet.address)
async def add_wallet_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="TRC20", callback_data="net:TRC20"))
    await message.answer("⚙️ <b>Выберите сеть:</b>", reply_markup=builder.as_markup())
    await state.set_state(AddWallet.network)

@dp.callback_query(AddWallet.network, F.data.startswith("net:"))
async def add_wallet_network(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(network=callback.data.split(":")[1])
    await callback.message.edit_text("🏷 <b>Введите метку (название):</b>")
    await state.set_state(AddWallet.label)

@dp.message(AddWallet.label)
async def add_wallet_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await db.add_wallet(message.from_user.id, data['address'], data['network'], message.text.strip())
    await state.clear()
    await message.answer("✅ <b>Кошелек добавлен!</b>", reply_markup=kb.get_main_menu(message.from_user.id))

# УДАЛЕНИЕ
@dp.callback_query(F.data.startswith("del:"))
async def delete_wallet_handler(callback: types.CallbackQuery):
    addr = callback.data.split(":")[1]
    await db.delete_wallet(callback.from_user.id, addr)
    await callback.answer("🗑 Удалено", show_alert=True)
    await show_wallets(callback)

# ИЗМЕНЕНИЕ МЕТКИ
@dp.callback_query(F.data.startswith("edit:"))
async def edit_label_start(callback: types.CallbackQuery, state: FSMContext):
    addr = callback.data.split(":")[1]
    await state.update_data(edit_addr=addr)
    await callback.message.answer("🏷 <b>Введите новую метку:</b>")
    await state.set_state(EditLabel.new_label)

@dp.message(EditLabel.new_label)
async def edit_label_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await db.update_label(message.from_user.id, data['edit_addr'], message.text.strip())
    await state.clear()
    await message.answer("✅ Метка обновлена!", reply_markup=kb.get_main_menu(message.from_user.id))

# АДМИНКА (Только для ADMINS)
@dp.callback_query(F.data == "admin_panel")
async def admin_menu(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMINS: return
    u, w = await db.get_admin_stats()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📢 Рассылка всем", callback_data="broadcast"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text(f"🔑 <b>ADMIN PANEL</b>\n\nЮзеров: {u}\nКошельков: {w}", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "broadcast")
async def b_start(c: types.CallbackQuery, state: FSMContext):
    await c.message.answer("📝 Введите текст для рассылки:")
    await state.set_state(Broadcast.message)

@dp.message(Broadcast.message)
async def b_done(m: types.Message, state: FSMContext):
    users = await db.get_all_users()
    await m.answer(f"🚀 Рассылка пошла на {len(users)} чел...")
    for uid in users:
        try: await m.copy_to(uid)
        except: pass
    await m.answer("✅ Рассылка завершена.")
    await state.clear()

@dp.callback_query(F.data == "to_main")
async def to_main(c: types.CallbackQuery):
    await c.message.edit_text("🌘 Главное меню:", reply_markup=kb.get_main_menu(c.from_user.id))

# ЗАПУСК
async def main():
    await db.init_db()
    print("--- CAMORRA CHECKER ЗАПУЩЕН ---")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
