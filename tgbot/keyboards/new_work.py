from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from db.models import User, Pool, WorkQuestion
from tgbot.lexicon.buttons import lexicon

from aiogram.filters.callback_data import CallbackData


class SelectWorkWayCallbackFactory(CallbackData, prefix="work_way"):
    action: str


class SelectNewWorkTypeCallbackFactory(CallbackData, prefix="new_work_type"):
    work_type: str


class StartNewWorkCallbackFactory(CallbackData, prefix="start_new_work"):
    action: str
    work_type: str
    topic_id: int


class SelfCheckCallbackFactory(CallbackData, prefix="self_check"):
    mark: int
    work_id: int
    work_question_id: int


class ReDoSkippedQuestionCallbackFactory(CallbackData, prefix="redo_skipped"):
    action: str
    work_id: int


def get_user_work_way_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=lexicon['new_work']['continue_last_work'],
        callback_data=SelectWorkWayCallbackFactory(action="continue_last_work"),
    )
    builder.button(
        text=lexicon['new_work']['start_new_work'],
        callback_data=SelectWorkWayCallbackFactory(action="start_new_work")
    )
    builder.adjust(1)
    return builder.as_markup()


def get_new_work_types_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=lexicon['new_work']['ege'],
        callback_data=SelectNewWorkTypeCallbackFactory(work_type="ege"),
    )
    builder.button(
        text=lexicon['new_work']['topic'],
        callback_data=SelectNewWorkTypeCallbackFactory(work_type="topic")
    )
    builder.adjust(1)
    return builder.as_markup()


def get_topics_kb(topics_list: list) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(
        text=lexicon['service']['back'],
    )
    for topic in topics_list:
        builder.button(
            text=topic.name,
        )
    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)


def get_start_work_kb(work_type: str, topic_id: int = -1) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=lexicon['new_work']['start'],
        callback_data=StartNewWorkCallbackFactory(action="start", work_type=work_type, topic_id=topic_id),
    )
    builder.button(
        text=lexicon['new_work']['cancel'],
        callback_data=StartNewWorkCallbackFactory(action="cancel", work_type=work_type, topic_id=topic_id)
    )
    builder.adjust(1)
    return builder.as_markup()


def get_view_result_kb(user: User, work_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=lexicon['new_work']['view_results'],
        url=f"http://31.134.153.162:7002/stats?uuid={user.id}&tid={user.telegram_id}&work={work_id}"
    )

    builder.adjust(1)

    return builder.as_markup()


def get_skip_question_kb(self_check_btn_visible: bool = False) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    if self_check_btn_visible:
        builder.button(
            text=lexicon['new_work']['self_check'],
        )

    builder.button(
        text=lexicon['new_work']['skip_question'],
    )
    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)


def get_self_check_kb(max_mark: int, work_id: int, work_question_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for i in range(max_mark + 1):
        builder.button(
            text=str(i),
            callback_data=SelfCheckCallbackFactory(
                mark=i,
                work_id=work_id,
                work_question_id=work_question_id
            )
        )
    builder.adjust(max_mark + 1)

    return builder.as_markup()


def get_redo_skipped_questions_kb(work_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text=lexicon['new_work']['redo_skipped'],
        callback_data=ReDoSkippedQuestionCallbackFactory(work_id=work_id, action="redo")
    )
    builder.button(
        text=lexicon['new_work']['cancel_skipped'],
        callback_data=ReDoSkippedQuestionCallbackFactory(work_id=work_id, action="skip")
    )
    builder.adjust(1)

    return builder.as_markup()
