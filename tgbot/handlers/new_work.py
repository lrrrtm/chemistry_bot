import os.path
from datetime import datetime
from os import getenv
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, ReplyKeyboardRemove

from db.crud import (get_user, get_user_works, get_topic_by_id, get_work_questions, get_all_topics, create_new_work,
                     insert_work_questions, remove_last_user_work,
                     get_question_from_pool, close_question, open_next_question, end_work, get_topic_by_name,
                     update_question_status, get_skipped_questions, get_hand_work, get_questions_list_by_id,
                     get_all_questions, remove_work)
from tgbot.handlers.trash import bot
from tgbot.keyboards.new_work import get_user_work_way_kb, SelectWorkWayCallbackFactory, get_new_work_types_kb, \
    SelectNewWorkTypeCallbackFactory, get_topics_kb, get_start_work_kb, StartNewWorkCallbackFactory, get_view_result_kb, \
    get_skip_question_kb, get_self_check_kb, SelfCheckCallbackFactory, get_redo_skipped_questions_kb, \
    ReDoSkippedQuestionCallbackFactory
from tgbot.lexicon.messages import lexicon as msg_lexicon
from tgbot.lexicon.buttons import lexicon as btns_lexicon, lexicon
from tgbot.states.picking_topic import UserTopicChoice
from tgbot.states.wait_for_answer_to_question import UserAnswerToQuestion
from utils.answer_checker import check_answer
from utils.tags_helper import get_ege_tags_list, get_random_questions

router = Router()


@router.message(Command("new_work"))
@router.message(F.text == btns_lexicon['main_menu']['new_work'])
async def cmd_new_work(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user is None:
        await message.answer(
            text=msg_lexicon['service']['need_reg']
        )
    else:
        works_list = get_user_works(message.from_user.id)
        if works_list and works_list[0].end_datetime is None:

            await message.answer(
                text=msg_lexicon['new_work']['previous_work_not_ended'],
                reply_markup=get_user_work_way_kb()
            )
        else:
            await message.answer(
                text=msg_lexicon['new_work']['select_type_of_work'],
                reply_markup=get_new_work_types_kb()
            )


@router.callback_query(SelectWorkWayCallbackFactory.filter())
async def process_user_work_way(callback: types.CallbackQuery, callback_data: SelectWorkWayCallbackFactory,
                                state: FSMContext):
    await callback.answer()
    action = callback_data.action

    if action == 'start_new_work':
        remove_last_user_work(get_user(callback.from_user.id))
        await callback.message.edit_text(
            text=msg_lexicon['new_work']['select_type_of_work']
        )
        await callback.message.edit_reply_markup(
            reply_markup=get_new_work_types_kb()
        )
    elif action == 'continue_last_work':
        await callback.message.delete()
        await go_next_question(get_user(callback.from_user.id).telegram_id, state, add_skipped_questions=True)


@router.callback_query(SelectNewWorkTypeCallbackFactory.filter())
async def process_user_work_type(callback: types.CallbackQuery, callback_data: SelectNewWorkTypeCallbackFactory,
                                 state: FSMContext):
    await callback.answer()
    action = callback_data.work_type

    if action == "ege":
        await callback.message.edit_text(
            text=msg_lexicon['new_work']['ege_work_caption']
        )
        await callback.message.edit_reply_markup(
            reply_markup=get_start_work_kb(work_type="ege")
        )

    elif action == "topic":
        await callback.message.delete()

        topics_list = get_all_topics(active=True)
        await callback.message.answer(
            text=msg_lexicon['new_work']['topic_work_caption'],
            reply_markup=get_topics_kb(topics_list)
        )
        await state.set_state(UserTopicChoice.waiting_for_answer)


@router.message(UserTopicChoice.waiting_for_answer)
async def process_user_topic_choice(message: Message, state: FSMContext):
    await state.clear()

    if message.text == btns_lexicon['service']['back']:
        await message.answer(
            text=msg_lexicon['new_work']['picking_topic_cancelled'],
            reply_markup=ReplyKeyboardRemove()
        )
        await cmd_new_work(message, state)
    else:
        topic_name = message.text.strip()
        topic_data = get_topic_by_name(topic_name)
        if topic_data is not None:
            await message.answer(
                text=msg_lexicon['new_work']['topic_picked'].format(topic_data.name),
                reply_markup=ReplyKeyboardRemove()
            )
            await message.answer(
                text=msg_lexicon['new_work']['topic_work_caption_2'],
                reply_markup=get_start_work_kb(work_type="topic", topic_id=topic_data.id)
            )
        else:
            await message.answer(
                text=msg_lexicon['new_work']['topic_is_not_exists']
            )
            await state.set_state(UserTopicChoice.waiting_for_answer)


@router.callback_query(StartNewWorkCallbackFactory.filter())
async def process_starting_work(callback: types.CallbackQuery, callback_data: StartNewWorkCallbackFactory,
                                state: FSMContext):
    await callback.answer()
    action = callback_data.action
    work_type = callback_data.work_type
    topic_id = callback_data.topic_id
    hand_work_id = callback_data.hand_work_id

    if action == "start":
        await callback.message.delete()
        msg = await bot.send_message(
            chat_id=callback.from_user.id,
            text=msg_lexicon['new_work']['preparing_questions_list'],
            reply_markup=ReplyKeyboardRemove()
        )

        user = get_user(callback.from_user.id)
        work = create_new_work(user_id=user.id, work_type=work_type, topic_id=topic_id, hand_work_id=hand_work_id)

        pool = get_all_questions()

        if work_type == "ege":
            tags_list = get_ege_tags_list(each_question_limit=1)

        elif work_type == "topic":
            tags_list = {tag: 3 for tag in get_topic_by_id(topic_id).tags_list}

        elif work_type == "hand_work":
            hand_work = get_hand_work(identificator=hand_work_id)

        if work_type in ["ege", "topic"]:
            questions_ids_list = get_random_questions(
                pool=pool,
                request_dict=tags_list,
            )

            if questions_ids_list['is_ok']:
                questions_list = get_questions_list_by_id(
                    ids_list=questions_ids_list['detail']
                )

            else:
                remove_work(work.id)
                await msg.delete()

                await callback.message.answer(
                    text="<b>Упс, что-то сломалось</b>"
                         "\n\nВ нашей базе не хватило задачек для того, чтобы составить для тебя персональную тренировку. Мы уже получили информацию об этом и занялись исправлением ошибки. А пока ты можешь выбрать другую тему персональной тренировки."
                )
                return

        elif work_type == "hand_work":
            questions_list = get_questions_list_by_id(hand_work.questions_list)

        insert_work_questions(work, questions_list)

        await msg.delete()

        await try_to_open_next_question(
            work_id=work.id,
            user_tid=user.telegram_id,
            state=state,
            message=callback.message,
        )

    if action == "cancel":
        await callback.message.edit_reply_markup(
            reply_markup=None
        )

        if work_type in ["ege", "topic"]:
            await callback.message.edit_text(
                text=msg_lexicon['new_work']['creating_work_cancelled']
            )
        elif work_type == "hand_work":
            await callback.message.edit_text(
                text=msg_lexicon['new_work']['starting_hand_work_cancelled']
            )


async def go_next_question(user_tid: int, state: FSMContext, add_skipped_questions: bool = False):
    user = get_user(user_tid)
    work = get_user_works(user.telegram_id)[0]
    questions_list = get_work_questions(work_id=work.id)

    self_check_note = msg_lexicon['new_work']['self_check_note']

    questions_statuses = ["current", "waiting"]

    if add_skipped_questions:
        questions_statuses.append("skipped")

    for q in questions_list:
        if q.status in questions_statuses:
            q_info = get_question_from_pool(q.question_id)

            # question_text_block = f"\n\n{self_check_note}\n\n{q_info.text}" if any(
            #     elem in q_info.tags_list for elem in get_ege_self_check_tags_list()) else f"\n\n{q_info.text}"

            question_text_block = f"\n\n{self_check_note}\n\n{q_info.text}" if bool(q_info.is_selfcheck) else f"\n\n{q_info.text}"

            if bool(q_info.question_image):
                if os.path.exists(os.path.join(getenv('ROOT_FOLDER'), f"data/questions_images/{q_info.id}.png")):
                    src = os.path.join(getenv('ROOT_FOLDER'), f"data/questions_images/{q_info.id}.png")
                else:
                    src = os.path.exists(os.path.join(getenv('ROOT_FOLDER'), f"data/questions_images/error.png"))

                await bot.send_photo(
                    chat_id=user.telegram_id,
                    photo=FSInputFile(src),
                    caption=f"№{q.position} <code>(id{q_info.id})</code>"
                            f"{question_text_block}",
                    show_caption_above_media=True,
                    reply_markup=get_skip_question_kb(
                        # self_check_btn_visible=any(elem in q_info.tags_list for elem in get_ege_self_check_tags_list())
                        self_check_btn_visible=bool(q_info.is_selfcheck)
                    )
                )
            else:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=f"№{q.position} <code>(id{q_info.id})</code>"
                         f"{question_text_block}",
                    reply_markup=get_skip_question_kb(
                        # self_check_btn_visible=any(elem in q_info.tags_list for elem in get_ege_self_check_tags_list())
                        self_check_btn_visible=bool(q_info.is_selfcheck)
                    )
                )
            await state.set_state(UserAnswerToQuestion.waiting_for_answer)
            await state.set_data(
                {'work_id': work.id, 'question_id': q.id, 'question_data': q_info, 'position': q.position})
            break


@router.message(UserAnswerToQuestion.waiting_for_answer)
async def save_and_check_user_answer(message: Message, state: FSMContext):
    data = await state.get_data()

    if message.text.strip() == btns_lexicon['new_work']['skip_question']:
        await message.answer(
            text=msg_lexicon['new_work']['question_skipped'].format(data['position']),
            reply_markup=ReplyKeyboardRemove()
        )
        update_question_status(
            q_id=data['question_id'],
            status="skipped"
        )

    elif message.text.strip() == btns_lexicon['new_work']['self_check']:
        question_data = data['question_data']

        if bool(question_data.answer_image):

            if os.path.exists(os.path.join(getenv('ROOT_FOLDER'), f"data/answers_images/{question_data.id}.png")):
                src = os.path.join(getenv('ROOT_FOLDER'), f"data/answers_images/{question_data.id}.png")
            else:
                src = os.path.exists(os.path.join(getenv('ROOT_FOLDER'), f"data/questions_images/error.png"))

            await message.answer_photo(
                photo=FSInputFile(src),
                show_caption_above_media=True,
                caption=msg_lexicon['new_work']['answer_to_question_head'].format(data['position'], question_data.id),
                reply_markup=ReplyKeyboardRemove()
            )

        else:
            await message.answer(
                text=msg_lexicon['new_work']['answer_to_question_head'].format(data['position'], question_data.id) +
                     f"\n\n{question_data.answer}",
                reply_markup=ReplyKeyboardRemove()
            )

        await message.answer(
            text=msg_lexicon['new_work']['request_to_mark_answer'],
            reply_markup=get_self_check_kb(
                max_mark=question_data.full_mark,
                work_id=data['work_id'],
                work_question_id=data['question_id'],
            )
        )
        return

    else:
        # if any(elem in data['question_data'].tags_list for elem in get_ege_self_check_tags_list()):
        if bool(data['question_data'].is_selfcheck):
            await message.answer(
                text=msg_lexicon['new_work']['self_check_request']
            )
            return

        close_question(
            q_id=data['question_id'],
            user_answer=message.text.strip(),
            user_mark=check_answer(data['question_data'], message.text.strip()),
            end_datetime=datetime.now()
        )

    await try_to_open_next_question(
        work_id=data['work_id'],
        message=message,
        user_tid=message.from_user.id,
        state=state
    )


@router.callback_query(SelfCheckCallbackFactory.filter())
async def process_self_check(callback: types.CallbackQuery, callback_data: SelfCheckCallbackFactory,
                             state: FSMContext):
    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    mark = callback_data.mark
    work_question_id = callback_data.work_question_id
    work_id = callback_data.work_id

    close_question(
        q_id=work_question_id,
        user_answer="самостоятельная проверка",
        user_mark=mark,
        end_datetime=datetime.now()
    )

    await try_to_open_next_question(
        work_id=work_id,
        message=callback.message,
        user_tid=callback.from_user.id,
        state=state
    )


async def try_to_open_next_question(work_id: int, message: Message, user_tid: int, state: FSMContext):
    result = open_next_question(work_id)

    if result is None:
        skipped_questions_list = get_skipped_questions(work_id)
        if skipped_questions_list:
            await message.answer(
                text=msg_lexicon['new_work']['redo_skipped_questions_request'].format(len(skipped_questions_list)),
                reply_markup=get_redo_skipped_questions_kb(work_id)
            )
            await state.clear()

        else:
            await bot.send_message(
                chat_id=user_tid,
                text=msg_lexicon['new_work']['view_results'],
                reply_markup=get_view_result_kb(get_user(user_tid), work_id)
            )
            end_work(work_id)
            await state.clear()
    else:
        await go_next_question(user_tid, state)


@router.callback_query(ReDoSkippedQuestionCallbackFactory.filter())
async def process_skipping_question(callback: types.CallbackQuery, callback_data: ReDoSkippedQuestionCallbackFactory,
                                    state: FSMContext):
    await callback.answer()
    action = callback_data.action
    work_id = callback_data.work_id
    skipped_questions_list = get_skipped_questions(work_id)

    await callback.message.delete()

    if action == "skip":
        for question in skipped_questions_list:
            close_question(
                q_id=question.id,
                user_answer="вопрос пропущен",
                user_mark=0,
                start_datetime=datetime.now(),
                end_datetime=datetime.now()
            )
        await try_to_open_next_question(
            work_id=work_id,
            message=callback.message,
            user_tid=callback.from_user.id,
            state=state
        )
        await state.clear()
    else:
        for question in skipped_questions_list:
            update_question_status(
                q_id=question.id,
                status="waiting"
            )
        await go_next_question(
            user_tid=callback.from_user.id,
            state=state
        )
