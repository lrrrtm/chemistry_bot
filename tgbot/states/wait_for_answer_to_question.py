from aiogram.fsm.state import StatesGroup, State


class UserAnswerToQuestion(StatesGroup):
    waiting_for_answer = State()