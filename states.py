from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    waiting_channel_add = State()
    waiting_channel_remove = State()

    waiting_card_owner = State()
    waiting_card_number = State()
    waiting_card_activate = State()
    waiting_card_delete = State()

    waiting_admin_add = State()
    waiting_admin_remove = State()

    waiting_instagram_url = State()
    waiting_suspicious_threshold = State()
    waiting_inbox_chat_id = State()

    waiting_custom_menu_name = State()
    waiting_custom_menu_text = State()
    waiting_custom_menu_delete = State()


class UserStates(StatesGroup):
    waiting_first_name = State()
    waiting_last_name = State()
    waiting_phone = State()
    waiting_birth_date = State()
    editing_first_name = State()
    editing_last_name = State()
    editing_phone = State()
    editing_birth_date = State()
