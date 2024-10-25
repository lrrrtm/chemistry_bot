from aiogram.fsm.state import StatesGroup, State


class UserTopicVolumeChoice(StatesGroup):
    waiting_for_answer = State()


class UserTopicChoice(StatesGroup):
    waiting_for_answer = State()
