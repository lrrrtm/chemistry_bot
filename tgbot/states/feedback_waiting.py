from aiogram.fsm.state import StatesGroup, State


class InputUserMessage(StatesGroup):
    waiting_for_msg = State()