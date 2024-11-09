from aiogram.fsm.state import StatesGroup, State


class InputMessage(StatesGroup):
    waiting_for_msg = State()
    message_text = State()