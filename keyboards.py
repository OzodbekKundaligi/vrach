from typing import Any, Iterable, List, Optional

from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder

ADMIN_PANEL_TEXT = "Admin panel"

BTN_STATS = "Statistika"
BTN_CHANNELS = "Kanallar"
BTN_CARDS = "Kartalar"
BTN_SETTINGS = "Sozlamalar"
BTN_ADMINS = "Adminlar"
BTN_MENUS = "Menyular"
BTN_BACK = "Orqaga"
BTN_EXIT = "Paneldan chiqish"

BTN_CHANNEL_ADD = "Kanal qo'shish"
BTN_CHANNEL_REMOVE = "Kanal o'chirish"
BTN_CHANNEL_LIST = "Kanallar ro'yxati"

BTN_CARD_ADD = "Karta qo'shish"
BTN_CARD_ACTIVATE = "Aktiv karta tanlash"
BTN_CARD_REMOVE = "Karta o'chirish"
BTN_CARD_LIST = "Kartalar ro'yxati"

BTN_SETTING_INSTAGRAM = "Instagram link"
BTN_SETTING_THRESHOLD = "Shubhali limit"
BTN_SETTING_INBOX = "Qabul chat ID"
BTN_SETTING_LIST = "Sozlamalar holati"

BTN_ADMIN_ADD = "Admin qo'shish"
BTN_ADMIN_REMOVE = "Admin o'chirish"
BTN_ADMIN_LIST = "Adminlar ro'yxati"

BTN_CUSTOM_MENU_ADD = "Menyu qo'shish"
BTN_CUSTOM_MENU_REMOVE = "Menyu o'chirish"
BTN_CUSTOM_MENU_LIST = "Menyular ro'yxati"

BTN_PROFILE = "Profil"
BTN_DELETE_DATA = "Ma'lumotlarni o'chirish"


def _derive_channel_url(chat_ref: str) -> Optional[str]:
    if chat_ref.startswith("@"):
        return f"https://t.me/{chat_ref[1:]}"
    if chat_ref.startswith("https://t.me/"):
        return chat_ref
    return None


def subscription_keyboard(channels: Iterable[Any], instagram_url: str) -> InlineKeyboardMarkup:
    return subscription_keyboard_with_text(channels, instagram_url, "Obunani tekshirish")


def subscription_keyboard_with_text(
    channels: Iterable[Any], instagram_url: str, check_button_text: str
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for index, channel in enumerate(channels, start=1):
        chat_ref = str(channel["chat_ref"])
        join_url = channel["join_url"] or _derive_channel_url(chat_ref)
        if join_url:
            builder.button(text=f"Kanal {index}", url=join_url)

    if instagram_url:
        builder.button(text="Instagram", url=instagram_url)

    builder.button(text=check_button_text, callback_data="user:check_subs")
    builder.adjust(1)
    return builder.as_markup()


def language_select_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Lotin", callback_data="user:lang:lotin")
    builder.button(text="Kril", callback_data="user:lang:kril")
    builder.button(text="Russ", callback_data="user:lang:russ")
    builder.adjust(3)
    return builder.as_markup()


def payment_review_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Tasdiqlash", callback_data=f"pay:approve:{payment_id}")
    builder.button(text="Rad etish", callback_data=f"pay:reject:{payment_id}")
    builder.adjust(2)
    return builder.as_markup()


def admin_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_STATS), KeyboardButton(text=BTN_CHANNELS)],
            [KeyboardButton(text=BTN_CARDS), KeyboardButton(text=BTN_SETTINGS)],
            [KeyboardButton(text=BTN_MENUS), KeyboardButton(text=BTN_ADMINS)],
            [KeyboardButton(text=BTN_EXIT)],
        ],
        resize_keyboard=True,
    )


def admin_entry_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=ADMIN_PANEL_TEXT)]],
        resize_keyboard=True,
    )


def user_main_menu_keyboard(
    profile_button_text: str = BTN_PROFILE,
    delete_button_text: str = BTN_DELETE_DATA,
    extra_buttons: Optional[List[str]] = None,
) -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text=profile_button_text), KeyboardButton(text=delete_button_text)]]
    for title in extra_buttons or []:
        keyboard.append([KeyboardButton(text=title)])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def profile_actions_keyboard(
    edit_first_name_text: str,
    edit_last_name_text: str,
    edit_phone_text: str,
    edit_birth_date_text: str,
    close_text: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=edit_first_name_text, callback_data="user:profile:edit:first_name")
    builder.button(text=edit_last_name_text, callback_data="user:profile:edit:last_name")
    builder.button(text=edit_phone_text, callback_data="user:profile:edit:phone")
    builder.button(text=edit_birth_date_text, callback_data="user:profile:edit:birth_date")
    builder.button(text=close_text, callback_data="user:profile:close")
    builder.adjust(1)
    return builder.as_markup()


def admin_channels_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_CHANNEL_ADD), KeyboardButton(text=BTN_CHANNEL_REMOVE)],
            [KeyboardButton(text=BTN_CHANNEL_LIST), KeyboardButton(text=BTN_BACK)],
        ],
        resize_keyboard=True,
    )


def admin_cards_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_CARD_ADD), KeyboardButton(text=BTN_CARD_ACTIVATE)],
            [KeyboardButton(text=BTN_CARD_REMOVE), KeyboardButton(text=BTN_CARD_LIST)],
            [KeyboardButton(text=BTN_BACK)],
        ],
        resize_keyboard=True,
    )


def admin_settings_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_SETTING_INSTAGRAM), KeyboardButton(text=BTN_SETTING_THRESHOLD)],
            [KeyboardButton(text=BTN_SETTING_INBOX)],
            [KeyboardButton(text=BTN_SETTING_LIST), KeyboardButton(text=BTN_BACK)],
        ],
        resize_keyboard=True,
    )


def admin_admins_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ADMIN_ADD), KeyboardButton(text=BTN_ADMIN_REMOVE)],
            [KeyboardButton(text=BTN_ADMIN_LIST), KeyboardButton(text=BTN_BACK)],
        ],
        resize_keyboard=True,
    )


def admin_custom_menus_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_CUSTOM_MENU_ADD), KeyboardButton(text=BTN_CUSTOM_MENU_REMOVE)],
            [KeyboardButton(text=BTN_CUSTOM_MENU_LIST), KeyboardButton(text=BTN_BACK)],
        ],
        resize_keyboard=True,
    )


def remove_reply_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def phone_request_keyboard(button_text: str = "Telefon raqam yuborish") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=button_text, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
