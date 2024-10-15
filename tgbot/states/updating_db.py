from aiogram.fsm.state import StatesGroup, State


class UpdateTopics(StatesGroup):
    waiting_for_msg = State()


class UpdatePool(StatesGroup):
    waiting_for_msg = State()
