from aiogram.fsm.state import StatesGroup, State


class InputAdminMessage(StatesGroup):
    waiting_for_msg = State()