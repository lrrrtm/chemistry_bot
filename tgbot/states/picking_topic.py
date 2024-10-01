from aiogram.fsm.state import StatesGroup, State


class UserTopicChoice(StatesGroup):
    waiting_for_answer = State()