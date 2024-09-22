from aiogram.fsm.state import StatesGroup, State


class InputUserName(StatesGroup):
    waiting_for_msg = State()