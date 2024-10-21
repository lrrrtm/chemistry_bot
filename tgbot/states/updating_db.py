from aiogram.fsm.state import StatesGroup, State


class UpdateTopics(StatesGroup):
    waiting_for_msg = State()


class InsertPool(StatesGroup):
    waiting_for_msg = State()
