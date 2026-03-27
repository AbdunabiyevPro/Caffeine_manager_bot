from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_filial_kb():
    kb = [
        [KeyboardButton(text="Rivera"), KeyboardButton(text="Samarqand Darvoza")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)


def get_phone_kb():
    kb = [[KeyboardButton(text="📱 Kontaktni yuborish", request_contact=True)]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_go_to_bot_kb(bot_username):
    buttons = [
        [
            InlineKeyboardButton(
                text="📝 Hisobot topshirish",
                url=f"https://t.me/{bot_username}?start=report"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


from aiogram import types

def get_group_reply_kb():
    buttons = [
        [types.InlineKeyboardButton(text="Javob berish ✍️", url="https://t.me/caffeine_manager_bot")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def get_status_kb():
    buttons = [
        [types.InlineKeyboardButton(text="✅ Ishxonadaman", callback_data="status_at_work")],
        [types.InlineKeyboardButton(text="🏃 Yo'ldaman (o'z vaqtida)", callback_data="status_on_way")],
        [types.InlineKeyboardButton(text="⏰ Kech qolaman", callback_data="status_late")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)