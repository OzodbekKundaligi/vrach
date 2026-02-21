import asyncio
import html
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatMemberStatus, ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import Config, load_config
from database import Database
from keyboards import (
    ADMIN_PANEL_TEXT,
    BTN_ADMIN_ADD,
    BTN_ADMIN_LIST,
    BTN_ADMIN_REMOVE,
    BTN_ADMINS,
    BTN_BACK,
    BTN_CARD_ACTIVATE,
    BTN_CARD_ADD,
    BTN_CARD_LIST,
    BTN_CARD_REMOVE,
    BTN_CARDS,
    BTN_CHANNEL_ADD,
    BTN_CHANNEL_LIST,
    BTN_CHANNEL_REMOVE,
    BTN_CHANNELS,
    BTN_CUSTOM_MENU_ADD,
    BTN_CUSTOM_MENU_LIST,
    BTN_CUSTOM_MENU_REMOVE,
    BTN_EXIT,
    BTN_MENUS,
    BTN_SETTING_INSTAGRAM,
    BTN_SETTING_INBOX,
    BTN_SETTING_LIST,
    BTN_SETTING_THRESHOLD,
    BTN_SETTINGS,
    BTN_STATS,
    admin_admins_menu_keyboard,
    admin_cards_menu_keyboard,
    admin_channels_menu_keyboard,
    admin_custom_menus_keyboard,
    admin_entry_keyboard,
    admin_main_menu_keyboard,
    admin_settings_menu_keyboard,
    language_select_keyboard,
    payment_review_keyboard,
    phone_request_keyboard,
    profile_actions_keyboard,
    remove_reply_keyboard,
    subscription_keyboard_with_text,
    user_main_menu_keyboard,
)
from states import AdminStates, UserStates

UZ_TZ = timezone(timedelta(hours=5))
SUPPORTED_LANGS = {"lotin", "kril", "russ"}
DEFAULT_LANG = "lotin"

I18N: Dict[str, Dict[str, str]] = {
    "lotin": {
        "lang_prompt": "Tilni tanlang:",
        "lang_saved": "Til saqlandi.",
        "sub_required": "Botdan foydalanish uchun avval majburiy obunalardan o'ting.",
        "sub_missing": "Obuna bo'lmagan kanallar: <b>{channels}</b>",
        "sub_check_btn": "Obunani tekshirish",
        "sub_not_full": "Obuna hali to'liq emas",
        "sub_ok": "Obuna tasdiqlandi",
        "reg_start": "Registratsiya boshlanadi.\nIsmingizni yuboring.",
        "reg_first_invalid": "Ismni to'g'ri kiriting.",
        "reg_last_prompt": "Familiyangizni yuboring.",
        "reg_last_invalid": "Familiyani to'g'ri kiriting.",
        "reg_phone_prompt": "Telefon raqamingizni yuboring.",
        "reg_phone_button": "Telefon raqam yuborish",
        "reg_phone_self_only": "Faqat o'zingizning raqamingizni yuboring.",
        "reg_phone_invalid": "Telefon raqam noto'g'ri. Masalan: +998901234567",
        "reg_birth_prompt": "Tug'ilgan sanangizni yuboring.\nFormat: <code>DD.MM.YYYY</code>",
        "reg_birth_invalid": "Sana xato. Format: <code>DD.MM.YYYY</code>",
        "reg_data_lost": "Registratsiya ma'lumotlari yo'qoldi. /start ni bosing.",
        "reg_done_paid": "Registratsiya tugadi.\nBizning xizmatimiz pullik, foydalanish uchun to'lov qiling.",
        "must_register": "Avval registratsiyadan o'ting. /start",
        "card_not_set": "To'lov kartasi hali sozlanmagan.\nAdmin bilan bog'laning yoki keyinroq qayta urinib ko'ring.",
        "payment_prompt": "Xabar yuborish uchun avval to'lov qiling.\n\nKarta egasi: <b>{owner}</b>\nKarta raqami: <code>{card}</code>\n\nTo'lov qilgach chek rasmini yoki faylini shu chatga yuboring.",
        "ready_with_credits": "To'lov tasdiqlangan. Sizda <b>{credits}</b> ta xabar limiti bor.\nHabaringizni yuboring.",
        "receipt_pending": "Chekingiz tekshiruvda. Admin tasdiqlashini kuting.",
        "receipt_accepted": "Chek qabul qilindi. Tekshiruvga yuborildi.\nPayment ID: <code>{payment_id}</code>",
        "payment_approved": "To'lovingiz tasdiqlandi.\nHabaringizni yuboring.",
        "payment_rejected": "To'lovingiz rad etildi.\nIltimos qayta to'lov qilib chek yuboring.",
        "send_error_restart": "Xatolik yuz berdi. /start ni qayta bosing.",
        "admin_send_failed": "Adminlarga xabar yuborib bo'lmadi. Keyinroq qayta urinib ko'ring.",
        "msg_sent_remaining": "Xabaringiz yuborildi.\nQolgan limit: <b>{remaining}</b>.\nYana xabar yuborishingiz mumkin.",
        "msg_sent_pay_again": "Xabaringiz yuborildi.\nKeyingi xabar uchun qayta to'lov qiling.",
        "receipt_wait": "Chekingiz tekshiruvda. Iltimos kuting.",
        "menu_profile_btn": "Profil",
        "menu_delete_btn": "Ma'lumotlarni o'chirish",
        "profile_text": "Profil:\nIsm: <b>{first_name}</b>\nFamiliya: <b>{last_name}</b>\nTelefon: <code>{phone}</code>\nTug'ilgan sana: <code>{birth_date}</code>",
        "profile_not_found": "Profil topilmadi. /start ni bosing.",
        "profile_edit_first_btn": "Ismni tahrirlash",
        "profile_edit_last_btn": "Familiyani tahrirlash",
        "profile_edit_phone_btn": "Telefonni tahrirlash",
        "profile_edit_birth_btn": "Sanani tahrirlash",
        "profile_close_btn": "Yopish",
        "profile_edit_first_prompt": "Yangi ismingizni yuboring.",
        "profile_edit_last_prompt": "Yangi familiyangizni yuboring.",
        "profile_edit_phone_prompt": "Yangi telefon raqamingizni yuboring.",
        "profile_edit_birth_prompt": "Yangi tug'ilgan sanani yuboring.\nFormat: <code>DD.MM.YYYY</code>",
        "profile_updated": "Profil ma'lumoti yangilandi.",
        "profile_deleted": "Ma'lumotlaringiz bazadan butunlay o'chirildi.\n/start ni bosing.",
    },
    "kril": {
        "lang_prompt": "\u0422\u0438\u043b\u043d\u0438 \u0442\u0430\u043d\u043b\u0430\u043d\u0433:",
        "lang_saved": "\u0422\u0438\u043b \u0441\u0430\u049b\u043b\u0430\u043d\u0434\u0438.",
        "sub_required": "\u0411\u043e\u0442\u0434\u0430\u043d \u0444\u043e\u0439\u0434\u0430\u043b\u0430\u043d\u0438\u0448 \u0443\u0447\u0443\u043d \u0430\u0432\u0432\u0430\u043b \u043c\u0430\u0436\u0431\u0443\u0440\u0438\u0439 \u043e\u0431\u0443\u043d\u0430\u043b\u0430\u0440\u0434\u0430\u043d \u045e\u0442\u0438\u043d\u0433.",
        "sub_missing": "\u041e\u0431\u0443\u043d\u0430 \u0431\u045e\u043b\u043c\u0430\u0433\u0430\u043d \u043a\u0430\u043d\u0430\u043b\u043b\u0430\u0440: <b>{channels}</b>",
        "sub_check_btn": "\u041e\u0431\u0443\u043d\u0430\u043d\u0438 \u0442\u0435\u043a\u0448\u0438\u0440\u0438\u0448",
        "sub_not_full": "\u041e\u0431\u0443\u043d\u0430 \u0434\u0430\u043b\u0438 \u0442\u045e\u043b\u0438\u049b \u044d\u043c\u0430\u0441",
        "sub_ok": "\u041e\u0431\u0443\u043d\u0430 \u0442\u0430\u0441\u0434\u0438\u049b\u043b\u0430\u043d\u0434\u0438",
        "reg_start": "\u0420\u045e\u0439\u0445\u0430\u0442\u0434\u0430\u043d \u045e\u0442\u0438\u0448 \u0431\u043e\u0448\u043b\u0430\u043d\u0430\u0434\u0438.\n\u0418\u0441\u043c\u0438\u043d\u0433\u0438\u0437\u043d\u0438 \u044e\u0431\u043e\u0440\u0438\u043d\u0433.",
        "reg_first_invalid": "\u0418\u0441\u043c\u043d\u0438 \u0442\u045e\u0493\u0440\u0438 \u043a\u0438\u0440\u0438\u0442\u0438\u043d\u0433.",
        "reg_last_prompt": "\u0424\u0430\u043c\u0438\u043b\u0438\u044f\u043d\u0433\u0438\u0437\u043d\u0438 \u044e\u0431\u043e\u0440\u0438\u043d\u0433.",
        "reg_last_invalid": "\u0424\u0430\u043c\u0438\u043b\u0438\u044f\u043d\u0438 \u0442\u045e\u0493\u0440\u0438 \u043a\u0438\u0440\u0438\u0442\u0438\u043d\u0433.",
        "reg_phone_prompt": "\u0422\u0435\u043b\u0435\u0444\u043e\u043d \u0440\u0430\u049b\u0430\u043c\u0438\u043d\u0433\u0438\u0437\u043d\u0438 \u044e\u0431\u043e\u0440\u0438\u043d\u0433.",
        "reg_phone_button": "\u0422\u0435\u043b\u0435\u0444\u043e\u043d \u0440\u0430\u049b\u0430\u043c \u044e\u0431\u043e\u0440\u0438\u0448",
        "reg_phone_self_only": "\u0424\u0430\u049b\u0430\u0442 \u045e\u0437\u0438\u043d\u0433\u0438\u0437\u043d\u0438\u043d\u0433 \u0440\u0430\u049b\u0430\u043c\u0438\u043d\u0438 \u044e\u0431\u043e\u0440\u0438\u043d\u0433.",
        "reg_phone_invalid": "\u0422\u0435\u043b\u0435\u0444\u043e\u043d \u0440\u0430\u049b\u0430\u043c \u043d\u043e\u0442\u045e\u0493\u0440\u0438. \u041c\u0430\u0441\u0430\u043b\u0430\u043d: +998901234567",
        "reg_birth_prompt": "\u0422\u0443\u0493\u0438\u043b\u0433\u0430\u043d \u0441\u0430\u043d\u0430\u043d\u0433\u0438\u0437\u043d\u0438 \u044e\u0431\u043e\u0440\u0438\u043d\u0433.\n\u0424\u043e\u0440\u043c\u0430\u0442: <code>DD.MM.YYYY</code>",
        "reg_birth_invalid": "\u0421\u0430\u043d\u0430 \u0445\u0430\u0442\u043e. \u0424\u043e\u0440\u043c\u0430\u0442: <code>DD.MM.YYYY</code>",
        "reg_data_lost": "\u0420\u045e\u0439\u0445\u0430\u0442 \u043c\u0430\u044a\u043b\u0443\u043c\u043e\u0442\u043b\u0430\u0440\u0438 \u0439\u045e\u049b\u043e\u043b\u0434\u0438. /start \u043d\u0438 \u0431\u043e\u0441\u0438\u043d\u0433.",
        "reg_done_paid": "\u0420\u045e\u0439\u0445\u0430\u0442 \u0442\u0443\u0433\u0430\u0434\u0438.\n\u0425\u0438\u0437\u043c\u0430\u0442\u0438\u043c\u0438\u0437 \u043f\u0443\u043b\u043b\u0438\u043a, \u0444\u043e\u0439\u0434\u0430\u043b\u0430\u043d\u0438\u0448 \u0443\u0447\u0443\u043d \u0442\u045e\u043b\u043e\u0432 \u049b\u0438\u043b\u0438\u043d\u0433.",
        "must_register": "\u0410\u0432\u0432\u0430\u043b \u0440\u045e\u0439\u0445\u0430\u0442\u0434\u0430\u043d \u045e\u0442\u0438\u043d\u0433. /start",
        "card_not_set": "\u0422\u045e\u043b\u043e\u0432 \u043a\u0430\u0440\u0442\u0430\u0441\u0438 \u0434\u0430\u043b\u0438 \u0441\u043e\u0437\u043b\u0430\u043d\u043c\u0430\u0433\u0430\u043d.\n\u0410\u0434\u043c\u0438\u043d \u0431\u0438\u043b\u0430\u043d \u0431\u043e\u0493\u043b\u0430\u043d\u0438\u043d\u0433 \u0451\u043a\u0438 \u043a\u0435\u0439\u0438\u043d\u0440\u043e\u049b \u049b\u0430\u0439\u0442\u0430 \u0443\u0440\u0438\u043d\u0438\u0431 \u043a\u045e\u0440\u0438\u043d\u0433.",
        "payment_prompt": "\u0425\u0430\u0431\u0430\u0440 \u044e\u0431\u043e\u0440\u0438\u0448 \u0443\u0447\u0443\u043d \u0430\u0432\u0432\u0430\u043b \u0442\u045e\u043b\u043e\u0432 \u049b\u0438\u043b\u0438\u043d\u0433.\n\n\u041a\u0430\u0440\u0442\u0430 \u044d\u0433\u0430\u0441\u0438: <b>{owner}</b>\n\u041a\u0430\u0440\u0442\u0430 \u0440\u0430\u049b\u0430\u043c\u0438: <code>{card}</code>\n\n\u0422\u045e\u043b\u043e\u0432 \u049b\u0438\u043b\u0433\u0430\u0447 \u0447\u0435\u043a \u0440\u0430\u0441\u043c\u0438\u043d\u0438 \u0451\u043a\u0438 \u0444\u0430\u0439\u043b\u0438\u043d\u0438 \u0448\u0443 \u0447\u0430\u0442\u0433\u0430 \u044e\u0431\u043e\u0440\u0438\u043d\u0433.",
        "ready_with_credits": "\u0422\u045e\u043b\u043e\u0432 \u0442\u0430\u0441\u0434\u0438\u049b\u043b\u0430\u043d\u0434\u0438. \u0421\u0438\u0437\u0434\u0430 <b>{credits}</b> \u0442\u0430 \u0445\u0430\u0431\u0430\u0440 \u043b\u0438\u043c\u0438\u0442\u0438 \u0431\u043e\u0440.\n\u0425\u0430\u0431\u0430\u0440\u0438\u043d\u0433\u0438\u0437\u043d\u0438 \u044e\u0431\u043e\u0440\u0438\u043d\u0433.",
        "receipt_pending": "\u0427\u0435\u043a\u0438\u043d\u0433\u0438\u0437 \u0442\u0435\u043a\u0448\u0438\u0440\u0443\u0432\u0434\u0430. \u0410\u0434\u043c\u0438\u043d \u0442\u0430\u0441\u0434\u0438\u049b\u043b\u0430\u0448\u0438\u043d\u0438 \u043a\u0443\u0442\u0438\u043d\u0433.",
        "receipt_accepted": "\u0427\u0435\u043a \u049b\u0430\u0431\u0443\u043b \u049b\u0438\u043b\u0438\u043d\u0434\u0438. \u0422\u0435\u043a\u0448\u0438\u0440\u0443\u0432\u0433\u0430 \u044e\u0431\u043e\u0440\u0438\u043b\u0434\u0438.\nPayment ID: <code>{payment_id}</code>",
        "payment_approved": "\u0422\u045e\u043b\u043e\u0432\u0438\u043d\u0433\u0438\u0437 \u0442\u0430\u0441\u0434\u0438\u049b\u043b\u0430\u043d\u0434\u0438.\n\u0425\u0430\u0431\u0430\u0440\u0438\u043d\u0433\u0438\u0437\u043d\u0438 \u044e\u0431\u043e\u0440\u0438\u043d\u0433.",
        "payment_rejected": "\u0422\u045e\u043b\u043e\u0432\u0438\u043d\u0433\u0438\u0437 \u0440\u0430\u0434 \u044d\u0442\u0438\u043b\u0434\u0438.\n\u0418\u043b\u0442\u0438\u043c\u043e\u0441 \u049b\u0430\u0439\u0442\u0430 \u0442\u045e\u043b\u043e\u0432 \u049b\u0438\u043b\u0438\u0431 \u0447\u0435\u043a \u044e\u0431\u043e\u0440\u0438\u043d\u0433.",
        "send_error_restart": "\u0425\u0430\u0442\u043e\u043b\u0438\u043a \u044e\u0437 \u0431\u0435\u0440\u0434\u0438. /start \u043d\u0438 \u049b\u0430\u0439\u0442\u0430 \u0431\u043e\u0441\u0438\u043d\u0433.",
        "admin_send_failed": "\u0410\u0434\u043c\u0438\u043d\u043b\u0430\u0440\u0433\u0430 \u0445\u0430\u0431\u0430\u0440 \u044e\u0431\u043e\u0440\u0438\u0431 \u0431\u045e\u043b\u043c\u0430\u0434\u0438. \u041a\u0435\u0439\u0438\u043d\u0440\u043e\u049b \u049b\u0430\u0439\u0442\u0430 \u0443\u0440\u0438\u043d\u0438\u0431 \u043a\u045e\u0440\u0438\u043d\u0433.",
        "msg_sent_remaining": "\u0425\u0430\u0431\u0430\u0440\u0438\u043d\u0433\u0438\u0437 \u044e\u0431\u043e\u0440\u0438\u043b\u0434\u0438.\n\u049a\u043e\u043b\u0433\u0430\u043d \u043b\u0438\u043c\u0438\u0442: <b>{remaining}</b>.\n\u042f\u043d\u0430 \u0445\u0430\u0431\u0430\u0440 \u044e\u0431\u043e\u0440\u0438\u0448\u0438\u043d\u0433\u0438\u0437 \u043c\u0443\u043c\u043a\u0438\u043d.",
        "msg_sent_pay_again": "\u0425\u0430\u0431\u0430\u0440\u0438\u043d\u0433\u0438\u0437 \u044e\u0431\u043e\u0440\u0438\u043b\u0434\u0438.\n\u041a\u0435\u0439\u0438\u043d\u0433\u0438 \u0445\u0430\u0431\u0430\u0440 \u0443\u0447\u0443\u043d \u049b\u0430\u0439\u0442\u0430 \u0442\u045e\u043b\u043e\u0432 \u049b\u0438\u043b\u0438\u043d\u0433.",
        "receipt_wait": "\u0427\u0435\u043a\u0438\u043d\u0433\u0438\u0437 \u0442\u0435\u043a\u0448\u0438\u0440\u0443\u0432\u0434\u0430. \u0418\u043b\u0442\u0438\u043c\u043e\u0441 \u043a\u0443\u0442\u0438\u043d\u0433.",
        "menu_profile_btn": "\u041f\u0440\u043e\u0444\u0438\u043b",
        "menu_delete_btn": "\u041c\u0430\u044a\u043b\u0443\u043c\u043e\u0442\u043b\u0430\u0440\u043d\u0438 \u045e\u0447\u0438\u0440\u0438\u0448",
        "profile_text": "\u041f\u0440\u043e\u0444\u0438\u043b:\n\u0418\u0441\u043c: <b>{first_name}</b>\n\u0424\u0430\u043c\u0438\u043b\u0438\u044f: <b>{last_name}</b>\n\u0422\u0435\u043b\u0435\u0444\u043e\u043d: <code>{phone}</code>\n\u0422\u0443\u0493\u0438\u043b\u0433\u0430\u043d \u0441\u0430\u043d\u0430: <code>{birth_date}</code>",
        "profile_not_found": "\u041f\u0440\u043e\u0444\u0438\u043b \u0442\u043e\u043f\u0438\u043b\u043c\u0430\u0434\u0438. /start \u043d\u0438 \u0431\u043e\u0441\u0438\u043d\u0433.",
        "profile_edit_first_btn": "\u0418\u0441\u043c\u043d\u0438 \u0442\u0430\u04b3\u0440\u0438\u0440\u043b\u0430\u0448",
        "profile_edit_last_btn": "\u0424\u0430\u043c\u0438\u043b\u0438\u044f\u043d\u0438 \u0442\u0430\u04b3\u0440\u0438\u0440\u043b\u0430\u0448",
        "profile_edit_phone_btn": "\u0422\u0435\u043b\u0435\u0444\u043e\u043d\u043d\u0438 \u0442\u0430\u04b3\u0440\u0438\u0440\u043b\u0430\u0448",
        "profile_edit_birth_btn": "\u0421\u0430\u043d\u0430\u043d\u0438 \u0442\u0430\u04b3\u0440\u0438\u0440\u043b\u0430\u0448",
        "profile_close_btn": "\u0401\u043f\u0438\u0448",
        "profile_edit_first_prompt": "\u042f\u043d\u0433\u0438 \u0438\u0441\u043c\u0438\u043d\u0433\u0438\u0437\u043d\u0438 \u044e\u0431\u043e\u0440\u0438\u043d\u0433.",
        "profile_edit_last_prompt": "\u042f\u043d\u0433\u0438 \u0444\u0430\u043c\u0438\u043b\u0438\u044f\u043d\u0433\u0438\u0437\u043d\u0438 \u044e\u0431\u043e\u0440\u0438\u043d\u0433.",
        "profile_edit_phone_prompt": "\u042f\u043d\u0433\u0438 \u0442\u0435\u043b\u0435\u0444\u043e\u043d \u0440\u0430\u049b\u0430\u043c\u0438\u043d\u0433\u0438\u0437\u043d\u0438 \u044e\u0431\u043e\u0440\u0438\u043d\u0433.",
        "profile_edit_birth_prompt": "\u042f\u043d\u0433\u0438 \u0442\u0443\u0493\u0438\u043b\u0433\u0430\u043d \u0441\u0430\u043d\u0430\u043d\u0438 \u044e\u0431\u043e\u0440\u0438\u043d\u0433.\n\u0424\u043e\u0440\u043c\u0430\u0442: <code>DD.MM.YYYY</code>",
        "profile_updated": "\u041f\u0440\u043e\u0444\u0438\u043b \u043c\u0430\u044a\u043b\u0443\u043c\u043e\u0442\u0438 \u044f\u043d\u0433\u0438\u043b\u0430\u043d\u0434\u0438.",
        "profile_deleted": "\u041c\u0430\u044a\u043b\u0443\u043c\u043e\u0442\u043b\u0430\u0440\u0438\u043d\u0433\u0438\u0437 \u0431\u0430\u0437\u0430\u0434\u0430\u043d \u0431\u0443\u0442\u0443\u043d\u043b\u0430\u0439 \u045e\u0447\u0438\u0440\u0438\u043b\u0434\u0438.\n/start \u043d\u0438 \u0431\u043e\u0441\u0438\u043d\u0433.",
    },
    "russ": {
        "lang_prompt": "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u044f\u0437\u044b\u043a:",
        "lang_saved": "\u042f\u0437\u044b\u043a \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d.",
        "sub_required": "\u0427\u0442\u043e\u0431\u044b \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u044c\u0441\u044f \u0431\u043e\u0442\u043e\u043c, \u0441\u043d\u0430\u0447\u0430\u043b\u0430 \u0432\u044b\u043f\u043e\u043b\u043d\u0438\u0442\u0435 \u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0438.",
        "sub_missing": "\u041d\u0435 \u043f\u043e\u0434\u043f\u0438\u0441\u0430\u043d\u044b \u043d\u0430 \u043a\u0430\u043d\u0430\u043b\u044b: <b>{channels}</b>",
        "sub_check_btn": "\u041f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0443",
        "sub_not_full": "\u041f\u043e\u0434\u043f\u0438\u0441\u043a\u0430 \u0435\u0449\u0435 \u043d\u0435 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0430",
        "sub_ok": "\u041f\u043e\u0434\u043f\u0438\u0441\u043a\u0430 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0430",
        "reg_start": "\u041d\u0430\u0447\u043d\u0435\u043c \u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u044e.\n\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0438\u043c\u044f.",
        "reg_first_invalid": "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043a\u043e\u0440\u0440\u0435\u043a\u0442\u043d\u043e\u0435 \u0438\u043c\u044f.",
        "reg_last_prompt": "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0444\u0430\u043c\u0438\u043b\u0438\u044e.",
        "reg_last_invalid": "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043a\u043e\u0440\u0440\u0435\u043a\u0442\u043d\u0443\u044e \u0444\u0430\u043c\u0438\u043b\u0438\u044e.",
        "reg_phone_prompt": "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u043d\u043e\u043c\u0435\u0440 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430.",
        "reg_phone_button": "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043d\u043e\u043c\u0435\u0440 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430",
        "reg_phone_self_only": "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0442\u043e\u043b\u044c\u043a\u043e \u0441\u0432\u043e\u0439 \u043d\u043e\u043c\u0435\u0440 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430.",
        "reg_phone_invalid": "\u041d\u0435\u0432\u0435\u0440\u043d\u044b\u0439 \u043d\u043e\u043c\u0435\u0440 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430. \u041f\u0440\u0438\u043c\u0435\u0440: +998901234567",
        "reg_birth_prompt": "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0434\u0430\u0442\u0443 \u0440\u043e\u0436\u0434\u0435\u043d\u0438\u044f.\n\u0424\u043e\u0440\u043c\u0430\u0442: <code>DD.MM.YYYY</code>",
        "reg_birth_invalid": "\u041d\u0435\u0432\u0435\u0440\u043d\u0430\u044f \u0434\u0430\u0442\u0430. \u0424\u043e\u0440\u043c\u0430\u0442: <code>DD.MM.YYYY</code>",
        "reg_data_lost": "\u0414\u0430\u043d\u043d\u044b\u0435 \u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u0438 \u043f\u043e\u0442\u0435\u0440\u044f\u043d\u044b. \u041d\u0430\u0436\u043c\u0438\u0442\u0435 /start.",
        "reg_done_paid": "\u0420\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u044f \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0430.\n\u041d\u0430\u0448 \u0441\u0435\u0440\u0432\u0438\u0441 \u043f\u043b\u0430\u0442\u043d\u044b\u0439, \u0432\u044b\u043f\u043e\u043b\u043d\u0438\u0442\u0435 \u043e\u043f\u043b\u0430\u0442\u0443.",
        "must_register": "\u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u043f\u0440\u043e\u0439\u0434\u0438\u0442\u0435 \u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u044e. /start",
        "card_not_set": "\u041f\u043b\u0430\u0442\u0435\u0436\u043d\u0430\u044f \u043a\u0430\u0440\u0442\u0430 \u0435\u0449\u0435 \u043d\u0435 \u043d\u0430\u0441\u0442\u0440\u043e\u0435\u043d\u0430.\n\u0421\u0432\u044f\u0436\u0438\u0442\u0435\u0441\u044c \u0441 \u0430\u0434\u043c\u0438\u043d\u043e\u043c \u0438\u043b\u0438 \u043f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u043f\u043e\u0437\u0436\u0435.",
        "payment_prompt": "\u0427\u0442\u043e\u0431\u044b \u043e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435, \u0441\u043d\u0430\u0447\u0430\u043b\u0430 \u043e\u043f\u043b\u0430\u0442\u0438\u0442\u0435.\n\n\u0412\u043b\u0430\u0434\u0435\u043b\u0435\u0446 \u043a\u0430\u0440\u0442\u044b: <b>{owner}</b>\n\u041d\u043e\u043c\u0435\u0440 \u043a\u0430\u0440\u0442\u044b: <code>{card}</code>\n\n\u041f\u043e\u0441\u043b\u0435 \u043e\u043f\u043b\u0430\u0442\u044b \u043e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0444\u043e\u0442\u043e \u0438\u043b\u0438 \u0444\u0430\u0439\u043b \u0447\u0435\u043a\u0430 \u0432 \u044d\u0442\u043e\u0442 \u0447\u0430\u0442.",
        "ready_with_credits": "\u041e\u043f\u043b\u0430\u0442\u0430 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0430. \u0423 \u0432\u0430\u0441 <b>{credits}</b> \u043a\u0440\u0435\u0434\u0438\u0442(\u043e\u0432) \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u044f.\n\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435.",
        "receipt_pending": "\u0412\u0430\u0448 \u0447\u0435\u043a \u043d\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0435. \u041e\u0436\u0438\u0434\u0430\u0439\u0442\u0435 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u044f \u0430\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0430.",
        "receipt_accepted": "\u0427\u0435\u043a \u043f\u0440\u0438\u043d\u044f\u0442 \u0438 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d \u043d\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0443.\nPayment ID: <code>{payment_id}</code>",
        "payment_approved": "\u0412\u0430\u0448 \u043f\u043b\u0430\u0442\u0435\u0436 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d.\n\u0422\u0435\u043f\u0435\u0440\u044c \u043e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435.",
        "payment_rejected": "\u0412\u0430\u0448 \u043f\u043b\u0430\u0442\u0435\u0436 \u043e\u0442\u043a\u043b\u043e\u043d\u0435\u043d.\n\u041e\u043f\u043b\u0430\u0442\u0438\u0442\u0435 \u043f\u043e\u0432\u0442\u043e\u0440\u043d\u043e \u0438 \u043e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u043d\u043e\u0432\u044b\u0439 \u0447\u0435\u043a.",
        "send_error_restart": "\u041f\u0440\u043e\u0438\u0437\u043e\u0448\u043b\u0430 \u043e\u0448\u0438\u0431\u043a\u0430. \u041d\u0430\u0436\u043c\u0438\u0442\u0435 /start \u0435\u0449\u0435 \u0440\u0430\u0437.",
        "admin_send_failed": "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0434\u043e\u0441\u0442\u0430\u0432\u0438\u0442\u044c \u0430\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0430\u043c. \u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u043f\u043e\u0437\u0436\u0435.",
        "msg_sent_remaining": "\u0412\u0430\u0448\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043e.\n\u041e\u0441\u0442\u0430\u0442\u043e\u043a \u043a\u0440\u0435\u0434\u0438\u0442\u0430: <b>{remaining}</b>.\n\u0412\u044b \u043c\u043e\u0436\u0435\u0442\u0435 \u043e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0435\u0449\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435.",
        "msg_sent_pay_again": "\u0412\u0430\u0448\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043e.\n\u0414\u043b\u044f \u0441\u043b\u0435\u0434\u0443\u044e\u0449\u0435\u0433\u043e \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u044f \u0441\u043d\u043e\u0432\u0430 \u043e\u043f\u043b\u0430\u0442\u0438\u0442\u0435.",
        "receipt_wait": "\u0412\u0430\u0448 \u0447\u0435\u043a \u043d\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0435. \u041f\u043e\u0436\u0430\u043b\u0443\u0439\u0441\u0442\u0430, \u043f\u043e\u0434\u043e\u0436\u0434\u0438\u0442\u0435.",
        "menu_profile_btn": "\u041f\u0440\u043e\u0444\u0438\u043b\u044c",
        "menu_delete_btn": "\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u0434\u0430\u043d\u043d\u044b\u0435",
        "profile_text": "\u041f\u0440\u043e\u0444\u0438\u043b\u044c:\n\u0418\u043c\u044f: <b>{first_name}</b>\n\u0424\u0430\u043c\u0438\u043b\u0438\u044f: <b>{last_name}</b>\n\u0422\u0435\u043b\u0435\u0444\u043e\u043d: <code>{phone}</code>\n\u0414\u0430\u0442\u0430 \u0440\u043e\u0436\u0434\u0435\u043d\u0438\u044f: <code>{birth_date}</code>",
        "profile_not_found": "\u041f\u0440\u043e\u0444\u0438\u043b\u044c \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d. \u041d\u0430\u0436\u043c\u0438\u0442\u0435 /start.",
        "profile_edit_first_btn": "\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u0438\u043c\u044f",
        "profile_edit_last_btn": "\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u0444\u0430\u043c\u0438\u043b\u0438\u044e",
        "profile_edit_phone_btn": "\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u0442\u0435\u043b\u0435\u0444\u043e\u043d",
        "profile_edit_birth_btn": "\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u0434\u0430\u0442\u0443",
        "profile_close_btn": "\u0417\u0430\u043a\u0440\u044b\u0442\u044c",
        "profile_edit_first_prompt": "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u043d\u043e\u0432\u043e\u0435 \u0438\u043c\u044f.",
        "profile_edit_last_prompt": "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u043d\u043e\u0432\u0443\u044e \u0444\u0430\u043c\u0438\u043b\u0438\u044e.",
        "profile_edit_phone_prompt": "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u043d\u043e\u0432\u044b\u0439 \u043d\u043e\u043c\u0435\u0440 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430.",
        "profile_edit_birth_prompt": "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u043d\u043e\u0432\u0443\u044e \u0434\u0430\u0442\u0443 \u0440\u043e\u0436\u0434\u0435\u043d\u0438\u044f.\n\u0424\u043e\u0440\u043c\u0430\u0442: <code>DD.MM.YYYY</code>",
        "profile_updated": "\u041f\u0440\u043e\u0444\u0438\u043b\u044c \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d.",
        "profile_deleted": "\u0412\u0430\u0448\u0438 \u0434\u0430\u043d\u043d\u044b\u0435 \u043f\u043e\u043b\u043d\u043e\u0441\u0442\u044c\u044e \u0443\u0434\u0430\u043b\u0435\u043d\u044b \u0438\u0437 \u0431\u0430\u0437\u044b.\n\u041d\u0430\u0436\u043c\u0438\u0442\u0435 /start.",
    },
}


def h(value: object) -> str:
    return html.escape(str(value), quote=False)


def user_display_name(message: Message) -> str:
    first = message.from_user.first_name if message.from_user else ""
    last = message.from_user.last_name if message.from_user and message.from_user.last_name else ""
    full_name = f"{first} {last}".strip()
    return full_name or "NoName"


def normalize_lang(language: str) -> str:
    return language if language in SUPPORTED_LANGS else DEFAULT_LANG


def user_lang(db: Database, user_id: int) -> str:
    return normalize_lang(db.get_user_language(user_id))


def t(db: Database, user_id: int, key: str, **kwargs: object) -> str:
    lang = user_lang(db, user_id)
    base = I18N.get(lang, I18N[DEFAULT_LANG])
    template = base.get(key) or I18N[DEFAULT_LANG].get(key) or key
    return template.format(**kwargs)


PROFILE_BUTTON_TEXTS = {
    str(values.get("menu_profile_btn", "")).strip().casefold()
    for values in I18N.values()
    if str(values.get("menu_profile_btn", "")).strip()
}
DELETE_BUTTON_TEXTS = {
    str(values.get("menu_delete_btn", "")).strip().casefold()
    for values in I18N.values()
    if str(values.get("menu_delete_btn", "")).strip()
}


def user_menu_keyboard(db: Database, user_id: int):
    extra_buttons = [str(row["button_text"]) for row in db.list_custom_menus()]
    return user_main_menu_keyboard(
        t(db, user_id, "menu_profile_btn"),
        t(db, user_id, "menu_delete_btn"),
        extra_buttons=extra_buttons,
    )


def user_profile_keyboard(db: Database, user_id: int):
    return profile_actions_keyboard(
        t(db, user_id, "profile_edit_first_btn"),
        t(db, user_id, "profile_edit_last_btn"),
        t(db, user_id, "profile_edit_phone_btn"),
        t(db, user_id, "profile_edit_birth_btn"),
        t(db, user_id, "profile_close_btn"),
    )


def format_profile_text(db: Database, user_id: int) -> str:
    profile = db.get_user_profile(user_id)
    if not profile:
        return t(db, user_id, "profile_not_found")
    return t(
        db,
        user_id,
        "profile_text",
        first_name=h(profile["first_name"] or "-"),
        last_name=h(profile["last_name"] or "-"),
        phone=h(profile["phone"] or "-"),
        birth_date=h(profile["birth_date"] or "-"),
    )


def format_payment_text(db: Database, user_id: int) -> str:
    card = db.get_active_card()
    if not card:
        return t(db, user_id, "card_not_set")

    return t(
        db,
        user_id,
        "payment_prompt",
        owner=h(card["owner_name"]),
        card=h(card["card_number"]),
    )


def format_channels_text(channels: List[object]) -> str:
    if not channels:
        return "Majburiy kanal yo'q."
    lines = ["Majburiy kanallar:"]
    for row in channels:
        item = f"{row['id']}. {row['chat_ref']}"
        if row["title"]:
            item += f" ({h(row['title'])})"
        if row["join_url"]:
            item += f"\nURL: {h(row['join_url'])}"
        lines.append(item)
    return "\n".join(lines)


def format_cards_text(cards: List[object]) -> str:
    if not cards:
        return "Kartalar yo'q."
    lines = ["Kartalar:"]
    for row in cards:
        marker = " [AKTIV]" if int(row["is_active"]) == 1 else ""
        lines.append(
            f"{row['id']}. {h(row['owner_name'])} | <code>{h(row['card_number'])}</code>{marker}"
        )
    return "\n".join(lines)


def format_admins_text(admin_ids: List[int]) -> str:
    if not admin_ids:
        return "Adminlar yo'q."
    lines = ["Adminlar ro'yxati:"]
    for admin_id in admin_ids:
        lines.append(str(admin_id))
    return "\n".join(lines)


def format_custom_menus_text(menus: List[object]) -> str:
    if not menus:
        return "Menyular yo'q."
    lines = ["Menyular ro'yxati:"]
    for row in menus:
        lines.append(
            f"{row['id']}. {h(row['button_text'])}\nJavob: {h(row['response_text'])}"
        )
    return "\n\n".join(lines)


def format_settings_text(db: Database) -> str:
    instagram_url = db.get_setting("instagram_url", "")
    suspicious_threshold = db.get_int_setting("suspicious_threshold", 3)
    inbox_chat_id = db.get_setting("inbox_chat_id", "")
    instagram_text = instagram_url if instagram_url else "(kiritilmagan)"
    inbox_text = inbox_chat_id if inbox_chat_id else "(kiritilmagan)"
    return (
        "Sozlamalar:\n"
        f"Instagram URL: {h(instagram_text)}\n"
        f"Shubhali urinish limiti: {suspicious_threshold}\n"
        f"Qabul chat ID: {h(inbox_text)}"
    )


def is_valid_chat_ref(chat_ref: str) -> bool:
    if chat_ref.startswith("@") and len(chat_ref) > 1:
        return True
    if chat_ref.startswith("-100") and chat_ref[1:].isdigit():
        return True
    return False


def is_valid_instagram_url(value: str) -> bool:
    lowered = value.lower()
    if not (lowered.startswith("https://") or lowered.startswith("http://")):
        return False
    return "instagram.com" in lowered


def normalize_phone(value: str) -> Optional[str]:
    raw = value.strip().replace(" ", "").replace("-", "")
    if raw.startswith("+"):
        raw_digits = "+" + "".join(ch for ch in raw[1:] if ch.isdigit())
    else:
        raw_digits = "".join(ch for ch in raw if ch.isdigit())
        if raw_digits and not raw_digits.startswith("+"):
            raw_digits = f"+{raw_digits}"
    digits = "".join(ch for ch in raw_digits if ch.isdigit())
    if len(digits) < 9 or len(digits) > 15:
        return None
    return raw_digits


def parse_birth_date(value: str) -> Optional[str]:
    cleaned = value.strip().replace("-", ".").replace("/", ".")
    try:
        parsed = datetime.strptime(cleaned, "%d.%m.%Y")
    except ValueError:
        return None
    if parsed.year < 1900 or parsed > datetime.now():
        return None
    return parsed.strftime("%Y-%m-%d")


async def get_missing_channels(bot: Bot, user_id: int, channels: List[object]) -> List[str]:
    missing: List[str] = []
    for row in channels:
        chat_ref = str(row["chat_ref"])
        try:
            member = await bot.get_chat_member(chat_id=chat_ref, user_id=user_id)
            if member.status in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED}:
                missing.append(chat_ref)
        except TelegramBadRequest:
            missing.append(chat_ref)
    return missing


def extract_receipt(message: Message) -> Optional[Tuple[str, str]]:
    if message.photo:
        return ("photo", message.photo[-1].file_id)
    if message.document:
        return ("document", message.document.file_id)
    return None


async def send_subscription_prompt(message: Message, db: Database, missing: List[str]) -> None:
    channels = db.list_channels()
    instagram_url = db.get_setting("instagram_url", "")
    lang_user_id = message.from_user.id if message.from_user else 0
    missing_text = ", ".join(missing) if missing else "barchasi"
    text = (
        f"{t(db, lang_user_id, 'sub_required')}\n"
        f"{t(db, lang_user_id, 'sub_missing', channels=h(missing_text))}\n\n"
        f"{t(db, lang_user_id, 'sub_check_btn')}"
    )
    await message.answer(
        text,
        reply_markup=subscription_keyboard_with_text(
            channels,
            instagram_url,
            t(db, lang_user_id, "sub_check_btn"),
        ),
    )


async def send_payment_to_admins(bot: Bot, db: Database, message: Message, payment_id: int) -> None:
    username = f"@{message.from_user.username}" if message.from_user and message.from_user.username else "(yo'q)"
    admin_caption = (
        f"Yangi to'lov cheki\n\n"
        f"Payment ID: <code>{payment_id}</code>\n"
        f"User ID: <code>{message.from_user.id}</code>\n"
        f"User: {h(user_display_name(message))}\n"
        f"Username: {h(username)}\n"
        f"Caption: {h(message.caption or '-')}"
    )
    receipt = extract_receipt(message)
    if not receipt:
        return

    receipt_type, file_id = receipt
    for admin_id in db.list_admins():
        try:
            if receipt_type == "photo":
                await bot.send_photo(
                    admin_id,
                    photo=file_id,
                    caption=admin_caption,
                    reply_markup=payment_review_keyboard(payment_id),
                )
            else:
                await bot.send_document(
                    admin_id,
                    document=file_id,
                    caption=admin_caption,
                    reply_markup=payment_review_keyboard(payment_id),
                )
        except TelegramForbiddenError:
            continue
        except TelegramBadRequest:
            continue


async def alert_suspicious_attempt(bot: Bot, db: Database, message: Message, attempts: int) -> None:
    username = f"@{message.from_user.username}" if message.from_user and message.from_user.username else "(yo'q)"
    alert_text = (
        "Shubhali holat kuzatildi.\n\n"
        f"User ID: <code>{message.from_user.id}</code>\n"
        f"User: {h(user_display_name(message))}\n"
        f"Username: {h(username)}\n"
        f"To'lovsiz urinishlar: {attempts}"
    )
    for admin_id in db.list_admins():
        try:
            await bot.send_message(admin_id, alert_text)
        except TelegramForbiddenError:
            continue
        except TelegramBadRequest:
            continue


async def send_ready_or_payment_message(bot: Bot, db: Database, chat_id: int, user_id: int) -> None:
    channels = db.list_channels()
    missing = await get_missing_channels(bot, user_id, channels)
    if missing:
        instagram_url = db.get_setting("instagram_url", "")
        text = (
            f"{t(db, user_id, 'sub_required')}\n"
            f"{t(db, user_id, 'sub_missing', channels=h(', '.join(missing)))}"
        )
        await bot.send_message(
            chat_id,
            text,
            reply_markup=subscription_keyboard_with_text(
                channels, instagram_url, t(db, user_id, "sub_check_btn")
            ),
        )
        return

    if not db.is_user_registered(user_id):
        await bot.send_message(chat_id, t(db, user_id, "must_register"))
        return

    credits = db.get_credits(user_id)
    if credits > 0:
        await bot.send_message(
            chat_id,
            t(db, user_id, "ready_with_credits", credits=credits),
            reply_markup=user_menu_keyboard(db, user_id),
        )
        return

    pending = db.get_pending_payment(user_id)
    if pending:
        await bot.send_message(
            chat_id,
            t(db, user_id, "receipt_pending"),
            reply_markup=user_menu_keyboard(db, user_id),
        )
        return

    await bot.send_message(
        chat_id,
        format_payment_text(db, user_id),
        reply_markup=user_menu_keyboard(db, user_id),
    )


async def forward_user_message_to_admins(bot: Bot, db: Database, message: Message) -> int:
    sent_count = 0
    username = f"@{message.from_user.username}" if message.from_user and message.from_user.username else "(yo'q)"
    head = (
        "Yangi user xabari.\n"
        f"User ID: <code>{message.from_user.id}</code>\n"
        f"User: {h(user_display_name(message))}\n"
        f"Username: {h(username)}\n\n"
        "Yangi xabar:"
    )

    inbox_chat_id = db.get_setting("inbox_chat_id", "").strip()
    if inbox_chat_id:
        try:
            target_chat: object = int(inbox_chat_id) if inbox_chat_id.lstrip("-").isdigit() else inbox_chat_id
            await bot.send_message(target_chat, head)
            await bot.copy_message(
                chat_id=target_chat,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
            )
            return 1
        except TelegramBadRequest:
            return 0
        except TelegramForbiddenError:
            return 0

    for admin_id in db.list_admins():
        try:
            await bot.send_message(admin_id, head)
            await bot.copy_message(
                chat_id=admin_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
            )
            sent_count += 1
        except TelegramForbiddenError:
            continue
        except TelegramBadRequest:
            continue
    return sent_count


async def process_today_birthdays(bot: Bot, db: Database) -> None:
    now = datetime.now(UZ_TZ)
    month_day = now.strftime("%m-%d")
    year = now.year
    birthday_users = db.list_today_birthdays(month_day)
    if not birthday_users:
        return

    for row in birthday_users:
        user_tg_id = int(row["tg_id"])
        if db.is_birthday_notified(user_tg_id, year):
            continue

        first_name = row["first_name"] or ""
        last_name = row["last_name"] or ""
        phone = row["phone"] or "-"
        birth_date = row["birth_date"] or "-"
        username = f"@{row['username']}" if row["username"] else "(yo'q)"
        text = (
            "Bugun foydalanuvchi tug'ilgan kuni.\n\n"
            f"User ID: <code>{user_tg_id}</code>\n"
            f"Ism: {h(first_name)}\n"
            f"Familiya: {h(last_name)}\n"
            f"Telefon: <code>{h(phone)}</code>\n"
            f"Sana: <code>{h(birth_date)}</code>\n"
            f"Username: {h(username)}\n\n"
            "Shablon: Bugun tug'ilgan kuningiz ekan, sizga 25% chegirma."
        )

        delivered = False
        for admin_id in db.list_admins():
            try:
                await bot.send_message(admin_id, text)
                delivered = True
            except TelegramForbiddenError:
                continue
            except TelegramBadRequest:
                continue

        if delivered:
            db.mark_birthday_notified(user_tg_id, year)


async def birthday_notifier_loop(bot: Bot, db: Database) -> None:
    while True:
        try:
            await process_today_birthdays(bot, db)
        except Exception:
            logging.exception("Birthday notifier error")
        await asyncio.sleep(3600)


def register_handlers(dp: Dispatcher, db: Database, config: Config) -> None:
    @dp.message(CommandStart())
    async def start_handler(message: Message, state: FSMContext) -> None:
        if message.chat.type != "private" or not message.from_user:
            return
        db.upsert_user(
            tg_id=message.from_user.id,
            username=message.from_user.username,
            full_name=user_display_name(message),
        )
        if db.is_admin(message.from_user.id):
            await state.clear()
            await message.answer("Admin panel tugmasi pastda.", reply_markup=admin_entry_keyboard())
            return

        channels = db.list_channels()
        missing = await get_missing_channels(message.bot, message.from_user.id, channels)
        if missing:
            await send_subscription_prompt(message, db, missing)
            return

        if not db.get_user_language(message.from_user.id):
            await state.clear()
            await message.answer(
                t(db, message.from_user.id, "lang_prompt"),
                reply_markup=language_select_keyboard(),
            )
            return

        if not db.is_user_registered(message.from_user.id):
            await state.clear()
            await state.set_state(UserStates.waiting_first_name)
            await message.answer(t(db, message.from_user.id, "reg_start"))
            return

        await send_ready_or_payment_message(message.bot, db, message.chat.id, message.from_user.id)

    @dp.callback_query(F.data == "user:check_subs")
    async def check_subscriptions_handler(callback: CallbackQuery, state: FSMContext) -> None:
        if not callback.from_user:
            return
        user_id = callback.from_user.id
        channels = db.list_channels()
        missing = await get_missing_channels(callback.bot, user_id, channels)
        if missing:
            instagram_url = db.get_setting("instagram_url", "")
            text = (
                f"{t(db, user_id, 'sub_required')}\n"
                f"{t(db, user_id, 'sub_missing', channels=h(', '.join(missing)))}"
            )
            if callback.message:
                await callback.message.answer(
                    text,
                    reply_markup=subscription_keyboard_with_text(
                        channels,
                        instagram_url,
                        t(db, user_id, "sub_check_btn"),
                    ),
                )
            await callback.answer(t(db, user_id, "sub_not_full"), show_alert=True)
            return

        await callback.answer(t(db, user_id, "sub_ok"))
        if callback.message:
            if not db.get_user_language(user_id):
                await state.clear()
                await callback.message.answer(
                    t(db, user_id, "lang_prompt"),
                    reply_markup=language_select_keyboard(),
                )
                return
            if not db.is_user_registered(user_id):
                await state.clear()
                await state.set_state(UserStates.waiting_first_name)
                await callback.message.answer(t(db, user_id, "reg_start"))
                return
            await send_ready_or_payment_message(
                callback.bot,
                db,
                callback.message.chat.id,
                user_id,
            )

    @dp.callback_query(F.data.startswith("user:lang:"))
    async def language_select_handler(callback: CallbackQuery, state: FSMContext) -> None:
        if not callback.from_user:
            return
        lang = (callback.data or "").split(":")[-1]
        if lang not in SUPPORTED_LANGS:
            await callback.answer("Xato til", show_alert=True)
            return
        db.set_user_language(callback.from_user.id, lang)
        await callback.answer(t(db, callback.from_user.id, "lang_saved"))
        if callback.message:
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except TelegramBadRequest:
                pass

            if not db.is_user_registered(callback.from_user.id):
                await state.clear()
                await state.set_state(UserStates.waiting_first_name)
                await callback.message.answer(t(db, callback.from_user.id, "reg_start"))
            else:
                await send_ready_or_payment_message(
                    callback.bot,
                    db,
                    callback.message.chat.id,
                    callback.from_user.id,
                )

    @dp.message(UserStates.waiting_first_name)
    async def user_first_name_state(message: Message, state: FSMContext) -> None:
        if message.chat.type != "private" or not message.from_user:
            return
        if db.is_admin(message.from_user.id):
            return
        value = (message.text or "").strip()
        if len(value) < 2:
            await message.answer(t(db, message.from_user.id, "reg_first_invalid"))
            return
        await state.update_data(first_name=value)
        await state.set_state(UserStates.waiting_last_name)
        await message.answer(t(db, message.from_user.id, "reg_last_prompt"))

    @dp.message(UserStates.waiting_last_name)
    async def user_last_name_state(message: Message, state: FSMContext) -> None:
        if message.chat.type != "private" or not message.from_user:
            return
        if db.is_admin(message.from_user.id):
            return
        value = (message.text or "").strip()
        if len(value) < 2:
            await message.answer(t(db, message.from_user.id, "reg_last_invalid"))
            return
        await state.update_data(last_name=value)
        await state.set_state(UserStates.waiting_phone)
        await message.answer(
            t(db, message.from_user.id, "reg_phone_prompt"),
            reply_markup=phone_request_keyboard(t(db, message.from_user.id, "reg_phone_button")),
        )

    @dp.message(UserStates.waiting_phone)
    async def user_phone_state(message: Message, state: FSMContext) -> None:
        if message.chat.type != "private" or not message.from_user:
            return
        if db.is_admin(message.from_user.id):
            return

        phone_value: Optional[str] = None
        if message.contact:
            if message.contact.user_id and message.contact.user_id != message.from_user.id:
                await message.answer(t(db, message.from_user.id, "reg_phone_self_only"))
                return
            phone_value = normalize_phone(message.contact.phone_number or "")
        else:
            phone_value = normalize_phone(message.text or "")

        if not phone_value:
            await message.answer(t(db, message.from_user.id, "reg_phone_invalid"))
            return

        await state.update_data(phone=phone_value)
        await state.set_state(UserStates.waiting_birth_date)
        await message.answer(
            t(db, message.from_user.id, "reg_birth_prompt"),
            reply_markup=remove_reply_keyboard(),
        )

    @dp.message(UserStates.waiting_birth_date)
    async def user_birth_date_state(message: Message, state: FSMContext) -> None:
        if message.chat.type != "private" or not message.from_user:
            return
        if db.is_admin(message.from_user.id):
            return

        birth_date = parse_birth_date(message.text or "")
        if not birth_date:
            await message.answer(t(db, message.from_user.id, "reg_birth_invalid"))
            return

        data = await state.get_data()
        first_name = str(data.get("first_name", "")).strip()
        last_name = str(data.get("last_name", "")).strip()
        phone = str(data.get("phone", "")).strip()
        if not first_name or not last_name or not phone:
            await state.clear()
            await message.answer(t(db, message.from_user.id, "reg_data_lost"))
            return

        db.save_user_registration(
            tg_id=message.from_user.id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            birth_date=birth_date,
        )
        await state.clear()
        await message.answer(
            t(db, message.from_user.id, "reg_done_paid"),
            reply_markup=user_menu_keyboard(db, message.from_user.id),
        )
        await message.answer(
            format_payment_text(db, message.from_user.id),
            reply_markup=user_menu_keyboard(db, message.from_user.id),
        )

    @dp.callback_query(F.data.startswith("pay:"))
    async def payment_decision_handler(callback: CallbackQuery) -> None:
        if not callback.from_user:
            return
        if not db.is_admin(callback.from_user.id):
            await callback.answer("Faqat admin", show_alert=True)
            return

        parts = (callback.data or "").split(":")
        if len(parts) != 3:
            await callback.answer("Noto'g'ri callback")
            return

        action = parts[1]
        try:
            payment_id = int(parts[2])
        except ValueError:
            await callback.answer("Payment ID xato")
            return

        payment = db.get_payment(payment_id)
        if not payment:
            await callback.answer("Payment topilmadi", show_alert=True)
            return

        if payment["status"] != "pending":
            await callback.answer("Bu payment allaqachon ko'rilgan", show_alert=True)
            return

        new_status = "approved" if action == "approve" else "rejected"
        updated = db.update_payment_status(payment_id, new_status, callback.from_user.id)
        if not updated:
            await callback.answer("Payment holatini o'zgartirib bo'lmadi", show_alert=True)
            return

        user_id = int(payment["user_tg_id"])
        if new_status == "approved":
            db.add_credits(user_id, 1)
            db.reset_no_payment_attempts(user_id)
            try:
                await callback.bot.send_message(
                    user_id,
                    t(db, user_id, "payment_approved"),
                    reply_markup=user_menu_keyboard(db, user_id),
                )
            except TelegramBadRequest:
                pass
            await callback.answer("Tasdiqlandi")
        else:
            try:
                await callback.bot.send_message(
                    user_id,
                    t(db, user_id, "payment_rejected"),
                    reply_markup=user_menu_keyboard(db, user_id),
                )
            except TelegramBadRequest:
                pass
            await callback.answer("Rad etildi")

        if callback.message:
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except TelegramBadRequest:
                pass
            try:
                await callback.message.answer(
                    f"Payment <code>{payment_id}</code> holati: <b>{new_status}</b>"
                )
            except TelegramBadRequest:
                pass

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == ADMIN_PANEL_TEXT.casefold())
    async def admin_panel_text(message: Message, state: FSMContext) -> None:
        if not message.from_user:
            return
        if not db.is_admin(message.from_user.id):
            await message.answer("Siz admin emassiz.")
            return
        await state.clear()
        await message.answer("Admin panel:", reply_markup=admin_main_menu_keyboard())

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_EXIT.casefold())
    async def admin_panel_close(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.clear()
        await message.answer("Admin panel yopildi.", reply_markup=admin_entry_keyboard())

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_BACK.casefold())
    async def admin_panel_back(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.clear()
        await message.answer("Admin panel:", reply_markup=admin_main_menu_keyboard())

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_STATS.casefold())
    async def admin_menu_stats(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.clear()
        stats = db.payment_stats()
        text = (
            "Statistika:\n"
            f"Users: {db.total_users()}\n"
            f"Yuborilgan xabarlar: {db.total_user_messages()}\n"
            f"To'lov pending: {stats.get('pending', 0)}\n"
            f"To'lov approved: {stats.get('approved', 0)}\n"
            f"To'lov rejected: {stats.get('rejected', 0)}"
        )
        await message.answer(text, reply_markup=admin_main_menu_keyboard())

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_CHANNELS.casefold())
    async def admin_menu_channels(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.clear()
        await message.answer(
            format_channels_text(db.list_channels()),
            reply_markup=admin_channels_menu_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_CARDS.casefold())
    async def admin_menu_cards(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.clear()
        await message.answer(
            format_cards_text(db.list_cards()),
            reply_markup=admin_cards_menu_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_SETTINGS.casefold())
    async def admin_menu_settings(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.clear()
        await message.answer(
            format_settings_text(db),
            reply_markup=admin_settings_menu_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_ADMINS.casefold())
    async def admin_menu_admins(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.clear()
        await message.answer(
            format_admins_text(db.list_admins()),
            reply_markup=admin_admins_menu_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_MENUS.casefold())
    async def admin_menu_custom(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.clear()
        await message.answer(
            format_custom_menus_text(db.list_custom_menus()),
            reply_markup=admin_custom_menus_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_CUSTOM_MENU_LIST.casefold())
    async def admin_custom_menu_list_action(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.clear()
        await message.answer(
            format_custom_menus_text(db.list_custom_menus()),
            reply_markup=admin_custom_menus_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_CUSTOM_MENU_ADD.casefold())
    async def admin_custom_menu_add_action(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.set_state(AdminStates.waiting_custom_menu_name)
        await message.answer(
            "Yangi menyu nomini yuboring (tugmada chiqadigan yozuv).",
            reply_markup=admin_custom_menus_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_CUSTOM_MENU_REMOVE.casefold())
    async def admin_custom_menu_remove_action(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.set_state(AdminStates.waiting_custom_menu_delete)
        await message.answer(
            f"{format_custom_menus_text(db.list_custom_menus())}\n\nO'chirish uchun menyu ID yuboring.",
            reply_markup=admin_custom_menus_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_CHANNEL_LIST.casefold())
    async def admin_channel_list_action(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.clear()
        await message.answer(
            format_channels_text(db.list_channels()),
            reply_markup=admin_channels_menu_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_CHANNEL_ADD.casefold())
    async def admin_channel_add_action(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.set_state(AdminStates.waiting_channel_add)
        await message.answer(
            "Kanal kiriting.\nFormat: <code>@kanal_username</code>\n"
            "Yoki: <code>@kanal_username|https://t.me/kanal_username</code>",
            reply_markup=admin_channels_menu_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_CHANNEL_REMOVE.casefold())
    async def admin_channel_remove_action(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.set_state(AdminStates.waiting_channel_remove)
        await message.answer(
            f"{format_channels_text(db.list_channels())}\n\nO'chirish uchun kanal ID yuboring.",
            reply_markup=admin_channels_menu_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_CARD_LIST.casefold())
    async def admin_card_list_action(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.clear()
        await message.answer(
            format_cards_text(db.list_cards()),
            reply_markup=admin_cards_menu_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_CARD_ADD.casefold())
    async def admin_card_add_action(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.set_state(AdminStates.waiting_card_owner)
        await message.answer("Yangi karta egasini yuboring.", reply_markup=admin_cards_menu_keyboard())

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_CARD_ACTIVATE.casefold())
    async def admin_card_activate_action(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.set_state(AdminStates.waiting_card_activate)
        await message.answer(
            f"{format_cards_text(db.list_cards())}\n\nAktiv qilish uchun karta ID yuboring.",
            reply_markup=admin_cards_menu_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_CARD_REMOVE.casefold())
    async def admin_card_remove_action(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.set_state(AdminStates.waiting_card_delete)
        await message.answer(
            f"{format_cards_text(db.list_cards())}\n\nO'chirish uchun karta ID yuboring.",
            reply_markup=admin_cards_menu_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_SETTING_LIST.casefold())
    async def admin_setting_list_action(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.clear()
        await message.answer(
            format_settings_text(db),
            reply_markup=admin_settings_menu_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_SETTING_INSTAGRAM.casefold())
    async def admin_setting_instagram_action(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.set_state(AdminStates.waiting_instagram_url)
        await message.answer(
            "Instagram link yuboring.\nTozalash uchun <code>-</code> yuboring.",
            reply_markup=admin_settings_menu_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_SETTING_THRESHOLD.casefold())
    async def admin_setting_threshold_action(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.set_state(AdminStates.waiting_suspicious_threshold)
        await message.answer(
            "Shubhali urinish limitini yuboring (masalan: 3).",
            reply_markup=admin_settings_menu_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_SETTING_INBOX.casefold())
    async def admin_setting_inbox_action(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.set_state(AdminStates.waiting_inbox_chat_id)
        await message.answer(
            "Xabar tushadigan chat ID ni yuboring.\n"
            "Masalan: <code>-1001234567890</code>\n"
            "Tozalash uchun <code>-</code> yuboring.",
            reply_markup=admin_settings_menu_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_ADMIN_LIST.casefold())
    async def admin_admin_list_action(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.clear()
        await message.answer(
            format_admins_text(db.list_admins()),
            reply_markup=admin_admins_menu_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_ADMIN_ADD.casefold())
    async def admin_admin_add_action(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.set_state(AdminStates.waiting_admin_add)
        await message.answer(
            "Qo'shmoqchi bo'lgan admin Telegram ID sini yuboring.",
            reply_markup=admin_admins_menu_keyboard(),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() == BTN_ADMIN_REMOVE.casefold())
    async def admin_admin_remove_action(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        await state.set_state(AdminStates.waiting_admin_remove)
        await message.answer(
            f"{format_admins_text(db.list_admins())}\n\nO'chirish uchun admin ID yuboring.",
            reply_markup=admin_admins_menu_keyboard(),
        )

    @dp.message(Command("cancel"))
    async def cancel_any_state(message: Message, state: FSMContext) -> None:
        await state.clear()
        if message.from_user and db.is_admin(message.from_user.id):
            await message.answer("Bekor qilindi.", reply_markup=admin_main_menu_keyboard())
        elif (
            message.from_user
            and db.get_user_language(message.from_user.id)
            and db.is_user_registered(message.from_user.id)
        ):
            await message.answer(
                "Bekor qilindi.",
                reply_markup=user_menu_keyboard(db, message.from_user.id),
            )
        else:
            await message.answer("Bekor qilindi.")

    @dp.message(AdminStates.waiting_channel_add)
    async def admin_add_channel_state(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        text = (message.text or "").strip()
        if not text:
            await message.answer("Bo'sh qiymat yuborildi. Qayta yuboring.")
            return

        if "|" in text:
            chat_ref, join_url = [x.strip() for x in text.split("|", 1)]
        else:
            chat_ref, join_url = text, None

        if not is_valid_chat_ref(chat_ref):
            await message.answer(
                "Chat format xato. Misol: <code>@kanal_username</code> yoki <code>-1001234567890</code>"
            )
            return

        if join_url and not join_url.startswith("http"):
            await message.answer("URL xato. To'g'ri URL yuboring.")
            return

        title = None
        try:
            chat = await message.bot.get_chat(chat_ref)
            title = chat.title if chat.title else None
        except TelegramBadRequest:
            title = None

        db.add_channel(chat_ref, join_url, title)
        await state.clear()
        await message.answer(
            f"Kanal qo'shildi.\n\n{format_channels_text(db.list_channels())}",
            reply_markup=admin_channels_menu_keyboard(),
        )

    @dp.message(AdminStates.waiting_channel_remove)
    async def admin_remove_channel_state(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        try:
            channel_id = int((message.text or "").strip())
        except ValueError:
            await message.answer("ID raqam bo'lishi kerak.")
            return

        removed = db.remove_channel(channel_id)
        await state.clear()
        if removed:
            await message.answer(
                f"Kanal o'chirildi.\n\n{format_channels_text(db.list_channels())}",
                reply_markup=admin_channels_menu_keyboard(),
            )
        else:
            await message.answer(
                "Bunday kanal ID topilmadi.",
                reply_markup=admin_channels_menu_keyboard(),
            )

    @dp.message(AdminStates.waiting_card_owner)
    async def admin_wait_card_owner_state(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        owner = (message.text or "").strip()
        if len(owner) < 2:
            await message.answer("Karta egasi juda qisqa. Qayta kiriting.")
            return
        await state.update_data(card_owner=owner)
        await state.set_state(AdminStates.waiting_card_number)
        await message.answer("Karta raqamini yuboring (masalan: 8600 1234 5678 9012).")

    @dp.message(AdminStates.waiting_card_number)
    async def admin_wait_card_number_state(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        number = (message.text or "").strip()
        digits = "".join(ch for ch in number if ch.isdigit())
        if len(digits) < 12:
            await message.answer("Karta raqami xato. Qayta yuboring.")
            return

        data = await state.get_data()
        owner = data.get("card_owner", "")
        db.add_card(owner_name=owner, card_number=number, activate=False)
        await state.clear()
        await message.answer(
            f"Karta saqlandi.\n\n{format_cards_text(db.list_cards())}",
            reply_markup=admin_cards_menu_keyboard(),
        )

    @dp.message(AdminStates.waiting_card_activate)
    async def admin_activate_card_state(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        try:
            card_id = int((message.text or "").strip())
        except ValueError:
            await message.answer("ID raqam bo'lishi kerak.")
            return

        ok = db.set_active_card(card_id)
        await state.clear()
        if ok:
            await message.answer(
                f"Aktiv karta yangilandi.\n\n{format_cards_text(db.list_cards())}",
                reply_markup=admin_cards_menu_keyboard(),
            )
        else:
            await message.answer("Karta topilmadi.", reply_markup=admin_cards_menu_keyboard())

    @dp.message(AdminStates.waiting_card_delete)
    async def admin_delete_card_state(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        try:
            card_id = int((message.text or "").strip())
        except ValueError:
            await message.answer("ID raqam bo'lishi kerak.")
            return

        ok = db.remove_card(card_id)
        await state.clear()
        if ok:
            await message.answer(
                f"Karta o'chirildi.\n\n{format_cards_text(db.list_cards())}",
                reply_markup=admin_cards_menu_keyboard(),
            )
        else:
            await message.answer("Karta topilmadi.", reply_markup=admin_cards_menu_keyboard())

    @dp.message(AdminStates.waiting_admin_add)
    async def admin_add_admin_state(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        try:
            admin_id = int((message.text or "").strip())
        except ValueError:
            await message.answer("Telegram ID raqam bo'lishi kerak.")
            return

        db.add_admin(admin_id)
        await state.clear()
        await message.answer(
            f"Admin qo'shildi.\n\n{format_admins_text(db.list_admins())}",
            reply_markup=admin_admins_menu_keyboard(),
        )

    @dp.message(AdminStates.waiting_admin_remove)
    async def admin_remove_admin_state(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        try:
            admin_id = int((message.text or "").strip())
        except ValueError:
            await message.answer("Telegram ID raqam bo'lishi kerak.")
            return

        if admin_id == config.super_admin_id:
            await message.answer("SUPER_ADMIN_ID ni o'chirib bo'lmaydi.")
            return
        if config.admin2_id is not None and admin_id == config.admin2_id:
            await message.answer("ADMIN2_ID ni o'chirib bo'lmaydi.")
            return

        removed = db.remove_admin(admin_id)
        await state.clear()
        if removed:
            await message.answer(
                f"Admin o'chirildi.\n\n{format_admins_text(db.list_admins())}",
                reply_markup=admin_admins_menu_keyboard(),
            )
        else:
            await message.answer("Admin topilmadi.", reply_markup=admin_admins_menu_keyboard())

    @dp.message(AdminStates.waiting_custom_menu_name)
    async def admin_custom_menu_name_state(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        name = (message.text or "").strip()
        if not name:
            await message.answer("Menyu nomi bo'sh bo'lmasligi kerak.")
            return
        if len(name) > 64:
            await message.answer("Menyu nomi 64 ta belgidan oshmasligi kerak.")
            return
        if name.casefold() in PROFILE_BUTTON_TEXTS or name.casefold() in DELETE_BUTTON_TEXTS:
            await message.answer("Bu nom band. Iltimos boshqa nom kiriting.")
            return

        await state.update_data(custom_menu_name=name)
        await state.set_state(AdminStates.waiting_custom_menu_text)
        await message.answer("Endi shu tugma bosilganda chiqadigan matnni yuboring.")

    @dp.message(AdminStates.waiting_custom_menu_text)
    async def admin_custom_menu_text_state(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        response_text = (message.text or "").strip()
        if not response_text:
            await message.answer("Javob matni bo'sh bo'lmasligi kerak.")
            return
        if len(response_text) > 4000:
            await message.answer("Javob matni juda uzun. 4000 belgidan oshmasin.")
            return

        data = await state.get_data()
        name = str(data.get("custom_menu_name", "")).strip()
        if not name:
            await state.clear()
            await message.answer(
                "Menyu nomi topilmadi. Qaytadan boshlang.",
                reply_markup=admin_custom_menus_keyboard(),
            )
            return

        created = db.save_custom_menu(name, response_text)
        await state.clear()
        status_text = "Menyu qo'shildi." if created else "Menyu yangilandi."
        await message.answer(
            f"{status_text}\n\n{format_custom_menus_text(db.list_custom_menus())}",
            reply_markup=admin_custom_menus_keyboard(),
        )

    @dp.message(AdminStates.waiting_custom_menu_delete)
    async def admin_custom_menu_delete_state(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        try:
            menu_id = int((message.text or "").strip())
        except ValueError:
            await message.answer("ID raqam bo'lishi kerak.")
            return

        removed = db.remove_custom_menu(menu_id)
        await state.clear()
        if removed:
            await message.answer(
                f"Menyu o'chirildi.\n\n{format_custom_menus_text(db.list_custom_menus())}",
                reply_markup=admin_custom_menus_keyboard(),
            )
        else:
            await message.answer(
                "Menyu topilmadi.",
                reply_markup=admin_custom_menus_keyboard(),
            )

    @dp.message(AdminStates.waiting_instagram_url)
    async def admin_set_instagram_state(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        value = (message.text or "").strip()
        if value == "-":
            db.set_setting("instagram_url", "")
            await state.clear()
            await message.answer("Instagram URL tozalandi.", reply_markup=admin_settings_menu_keyboard())
            return
        if not is_valid_instagram_url(value):
            await message.answer("Instagram URL xato. To'g'ri URL yuboring.")
            return

        db.set_setting("instagram_url", value)
        await state.clear()
        await message.answer("Instagram URL saqlandi.", reply_markup=admin_settings_menu_keyboard())

    @dp.message(AdminStates.waiting_suspicious_threshold)
    async def admin_set_threshold_state(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return
        try:
            threshold = int((message.text or "").strip())
        except ValueError:
            await message.answer("Raqam yuboring.")
            return
        if threshold < 1 or threshold > 100:
            await message.answer("Limit 1 dan 100 gacha bo'lishi kerak.")
            return

        db.set_setting("suspicious_threshold", str(threshold))
        await state.clear()
        await message.answer("Shubhali limit saqlandi.", reply_markup=admin_settings_menu_keyboard())

    @dp.message(AdminStates.waiting_inbox_chat_id)
    async def admin_set_inbox_chat_state(message: Message, state: FSMContext) -> None:
        if not message.from_user or not db.is_admin(message.from_user.id):
            return

        value = (message.text or "").strip()
        if value == "-":
            db.set_setting("inbox_chat_id", "")
            await state.clear()
            await message.answer("Qabul chat ID tozalandi.", reply_markup=admin_settings_menu_keyboard())
            return

        if not (value.lstrip("-").isdigit() or value.startswith("@")):
            await message.answer("Chat ID xato. Misol: -1001234567890 yoki @kanal_username")
            return

        db.set_setting("inbox_chat_id", value)
        await state.clear()
        await message.answer("Qabul chat ID saqlandi.", reply_markup=admin_settings_menu_keyboard())

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() in PROFILE_BUTTON_TEXTS)
    async def user_profile_menu(message: Message, state: FSMContext) -> None:
        if message.chat.type != "private" or not message.from_user:
            return
        if db.is_admin(message.from_user.id):
            return

        channels = db.list_channels()
        missing = await get_missing_channels(message.bot, message.from_user.id, channels)
        if missing:
            await send_subscription_prompt(message, db, missing)
            return

        if not db.get_user_language(message.from_user.id):
            await message.answer(
                t(db, message.from_user.id, "lang_prompt"),
                reply_markup=language_select_keyboard(),
            )
            return

        if not db.is_user_registered(message.from_user.id):
            await message.answer(t(db, message.from_user.id, "must_register"))
            return

        await state.clear()
        await message.answer(
            format_profile_text(db, message.from_user.id),
            reply_markup=user_profile_keyboard(db, message.from_user.id),
        )

    @dp.message(lambda m: bool(m.text) and m.text.strip().casefold() in DELETE_BUTTON_TEXTS)
    async def user_delete_data(message: Message, state: FSMContext) -> None:
        if message.chat.type != "private" or not message.from_user:
            return
        if db.is_admin(message.from_user.id):
            return

        user_id = message.from_user.id
        deleted_text = t(db, user_id, "profile_deleted")
        await state.clear()
        db.delete_user_data(user_id)
        await message.answer(deleted_text, reply_markup=remove_reply_keyboard())

    @dp.message(lambda m: bool(m.text) and bool(db.get_custom_menu_by_button((m.text or "").strip())))
    async def user_custom_menu_text(message: Message, state: FSMContext) -> None:
        if message.chat.type != "private" or not message.from_user:
            return
        if db.is_admin(message.from_user.id):
            return
        if await state.get_state():
            return

        channels = db.list_channels()
        missing = await get_missing_channels(message.bot, message.from_user.id, channels)
        if missing:
            await send_subscription_prompt(message, db, missing)
            return

        if not db.get_user_language(message.from_user.id):
            await message.answer(
                t(db, message.from_user.id, "lang_prompt"),
                reply_markup=language_select_keyboard(),
            )
            return

        if not db.is_user_registered(message.from_user.id):
            await message.answer(t(db, message.from_user.id, "must_register"))
            return

        menu = db.get_custom_menu_by_button((message.text or "").strip())
        if not menu:
            return

        await state.clear()
        await message.answer(
            str(menu["response_text"]),
            parse_mode=None,
            reply_markup=user_menu_keyboard(db, message.from_user.id),
        )

    @dp.callback_query(F.data.startswith("user:profile:edit:"))
    async def user_profile_edit_callback(callback: CallbackQuery, state: FSMContext) -> None:
        if not callback.from_user:
            return
        if db.is_admin(callback.from_user.id):
            await callback.answer("Faqat foydalanuvchilar uchun", show_alert=True)
            return
        if not db.is_user_registered(callback.from_user.id):
            await callback.answer(t(db, callback.from_user.id, "must_register"), show_alert=True)
            return

        field = (callback.data or "").split(":")[-1]
        if field == "first_name":
            await state.set_state(UserStates.editing_first_name)
            prompt_text = t(db, callback.from_user.id, "profile_edit_first_prompt")
            markup = None
        elif field == "last_name":
            await state.set_state(UserStates.editing_last_name)
            prompt_text = t(db, callback.from_user.id, "profile_edit_last_prompt")
            markup = None
        elif field == "phone":
            await state.set_state(UserStates.editing_phone)
            prompt_text = t(db, callback.from_user.id, "profile_edit_phone_prompt")
            markup = phone_request_keyboard(t(db, callback.from_user.id, "reg_phone_button"))
        elif field == "birth_date":
            await state.set_state(UserStates.editing_birth_date)
            prompt_text = t(db, callback.from_user.id, "profile_edit_birth_prompt")
            markup = remove_reply_keyboard()
        else:
            await callback.answer("Xato amal", show_alert=True)
            return

        if callback.message:
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except TelegramBadRequest:
                pass
            await callback.message.answer(prompt_text, reply_markup=markup)
        await callback.answer()

    @dp.callback_query(F.data == "user:profile:close")
    async def user_profile_close_callback(callback: CallbackQuery) -> None:
        if not callback.from_user:
            return
        if callback.message:
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except TelegramBadRequest:
                pass
        await callback.answer()

    @dp.message(UserStates.editing_first_name)
    async def user_edit_first_name_state(message: Message, state: FSMContext) -> None:
        if message.chat.type != "private" or not message.from_user:
            return
        if db.is_admin(message.from_user.id):
            return
        value = (message.text or "").strip()
        if len(value) < 2:
            await message.answer(t(db, message.from_user.id, "reg_first_invalid"))
            return
        db.update_user_first_name(message.from_user.id, value)
        await state.clear()
        await message.answer(
            t(db, message.from_user.id, "profile_updated"),
            reply_markup=user_menu_keyboard(db, message.from_user.id),
        )
        await message.answer(
            format_profile_text(db, message.from_user.id),
            reply_markup=user_profile_keyboard(db, message.from_user.id),
        )

    @dp.message(UserStates.editing_last_name)
    async def user_edit_last_name_state(message: Message, state: FSMContext) -> None:
        if message.chat.type != "private" or not message.from_user:
            return
        if db.is_admin(message.from_user.id):
            return
        value = (message.text or "").strip()
        if len(value) < 2:
            await message.answer(t(db, message.from_user.id, "reg_last_invalid"))
            return
        db.update_user_last_name(message.from_user.id, value)
        await state.clear()
        await message.answer(
            t(db, message.from_user.id, "profile_updated"),
            reply_markup=user_menu_keyboard(db, message.from_user.id),
        )
        await message.answer(
            format_profile_text(db, message.from_user.id),
            reply_markup=user_profile_keyboard(db, message.from_user.id),
        )

    @dp.message(UserStates.editing_phone)
    async def user_edit_phone_state(message: Message, state: FSMContext) -> None:
        if message.chat.type != "private" or not message.from_user:
            return
        if db.is_admin(message.from_user.id):
            return

        phone_value: Optional[str]
        if message.contact:
            if message.contact.user_id and message.contact.user_id != message.from_user.id:
                await message.answer(t(db, message.from_user.id, "reg_phone_self_only"))
                return
            phone_value = normalize_phone(message.contact.phone_number or "")
        else:
            phone_value = normalize_phone(message.text or "")

        if not phone_value:
            await message.answer(t(db, message.from_user.id, "reg_phone_invalid"))
            return

        db.update_user_phone(message.from_user.id, phone_value)
        await state.clear()
        await message.answer(
            t(db, message.from_user.id, "profile_updated"),
            reply_markup=user_menu_keyboard(db, message.from_user.id),
        )
        await message.answer(
            format_profile_text(db, message.from_user.id),
            reply_markup=user_profile_keyboard(db, message.from_user.id),
        )

    @dp.message(UserStates.editing_birth_date)
    async def user_edit_birth_date_state(message: Message, state: FSMContext) -> None:
        if message.chat.type != "private" or not message.from_user:
            return
        if db.is_admin(message.from_user.id):
            return

        birth_date = parse_birth_date(message.text or "")
        if not birth_date:
            await message.answer(t(db, message.from_user.id, "reg_birth_invalid"))
            return

        db.update_user_birth_date(message.from_user.id, birth_date)
        await state.clear()
        await message.answer(
            t(db, message.from_user.id, "profile_updated"),
            reply_markup=user_menu_keyboard(db, message.from_user.id),
        )
        await message.answer(
            format_profile_text(db, message.from_user.id),
            reply_markup=user_profile_keyboard(db, message.from_user.id),
        )

    @dp.message()
    async def user_main_flow(message: Message) -> None:
        if message.chat.type != "private" or not message.from_user:
            return

        if db.is_admin(message.from_user.id):
            return

        db.upsert_user(
            tg_id=message.from_user.id,
            username=message.from_user.username,
            full_name=user_display_name(message),
        )

        channels = db.list_channels()
        missing = await get_missing_channels(message.bot, message.from_user.id, channels)
        if missing:
            await send_subscription_prompt(message, db, missing)
            return

        if not db.get_user_language(message.from_user.id):
            await message.answer(
                t(db, message.from_user.id, "lang_prompt"),
                reply_markup=language_select_keyboard(),
            )
            return

        if not db.is_user_registered(message.from_user.id):
            await message.answer(t(db, message.from_user.id, "must_register"))
            return

        credits = db.get_credits(message.from_user.id)
        if credits > 0:
            consumed = db.consume_credit(message.from_user.id, 1)
            if not consumed:
                await message.answer(
                    t(db, message.from_user.id, "send_error_restart"),
                    reply_markup=user_menu_keyboard(db, message.from_user.id),
                )
                return

            sent_count = await forward_user_message_to_admins(message.bot, db, message)
            if sent_count == 0:
                db.add_credits(message.from_user.id, 1)
                await message.answer(
                    t(db, message.from_user.id, "admin_send_failed"),
                    reply_markup=user_menu_keyboard(db, message.from_user.id),
                )
                return

            remaining = db.get_credits(message.from_user.id)
            if remaining > 0:
                await message.answer(
                    t(db, message.from_user.id, "msg_sent_remaining", remaining=remaining),
                    reply_markup=user_menu_keyboard(db, message.from_user.id),
                )
            else:
                await message.answer(
                    t(db, message.from_user.id, "msg_sent_pay_again"),
                    reply_markup=user_menu_keyboard(db, message.from_user.id),
                )
                await message.answer(
                    format_payment_text(db, message.from_user.id),
                    reply_markup=user_menu_keyboard(db, message.from_user.id),
                )
            return

        pending = db.get_pending_payment(message.from_user.id)
        if pending:
            await message.answer(
                t(db, message.from_user.id, "receipt_wait"),
                reply_markup=user_menu_keyboard(db, message.from_user.id),
            )
            return

        receipt = extract_receipt(message)
        if receipt:
            receipt_type, file_id = receipt
            payment_id = db.create_payment(
                user_tg_id=message.from_user.id,
                receipt_file_id=file_id,
                receipt_type=receipt_type,
                receipt_caption=message.caption,
            )
            await send_payment_to_admins(message.bot, db, message, payment_id)
            await message.answer(
                t(db, message.from_user.id, "receipt_accepted", payment_id=payment_id),
                reply_markup=user_menu_keyboard(db, message.from_user.id),
            )
            return

        attempts = db.increment_no_payment_attempt(message.from_user.id)
        threshold = db.get_int_setting("suspicious_threshold", 3)
        if attempts >= threshold:
            db.reset_no_payment_attempts(message.from_user.id)
            await alert_suspicious_attempt(message.bot, db, message, attempts)

        await message.answer(
            format_payment_text(db, message.from_user.id),
            reply_markup=user_menu_keyboard(db, message.from_user.id),
        )


async def run_bot() -> None:
    config = load_config()
    db = Database(config.db_path)
    db.ensure_super_admin(config.super_admin_id)
    if config.admin2_id is not None:
        db.add_admin(config.admin2_id)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    register_handlers(dp, db, config)
    birthday_task = asyncio.create_task(birthday_notifier_loop(bot, db))

    try:
        await dp.start_polling(bot)
    finally:
        birthday_task.cancel()
        try:
            await birthday_task
        except asyncio.CancelledError:
            pass
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiogram.dispatcher").setLevel(logging.WARNING)
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    asyncio.run(run_bot())
