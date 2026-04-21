from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
import database as db

ADMINS = [654714933, 6386475731]

def get_main_menu(user_id):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📋 Мои кошельки", callback_data="my_wallets"))
    builder.row(InlineKeyboardButton(text="🔍 Проверить кошелек", callback_data="check_wallet"))
    builder.row(InlineKeyboardButton(text="➕ Добавить кошелек", callback_data="add_wallet"))
    builder.row(InlineKeyboardButton(text="❓ FAQ", callback_data="faq"))
    if user_id in ADMINS:
        builder.row(InlineKeyboardButton(text="🔑 Админ-панель", callback_data="admin_panel"))
    return builder.as_markup()

def get_wallets_nav_kb(user_id):
    wallets = db.get_user_wallets_sync(user_id)
    builder = InlineKeyboardBuilder()
    if not wallets:
        builder.row(InlineKeyboardButton(text="📭 Список пуст", callback_data="to_main"))
    else:
        for w in wallets:
            builder.row(InlineKeyboardButton(text=f"🏷 {w['label']}", callback_data=f"info:{w['wallet_address']}:{w['network']}"))
    builder.row(InlineKeyboardButton(text="🏠 Назад", callback_data="to_main"))
    return builder.as_markup()

def get_wallet_manage_kb(addr, net):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔄 Обновить", callback_data=f"info:{addr}:{net}"))
    builder.row(InlineKeyboardButton(text="✏️ Метка", callback_data=f"edit:{addr}"), InlineKeyboardButton(text="🗑 Удалить", callback_data=f"del:{addr}"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="my_wallets"))
    return builder.as_markup()
