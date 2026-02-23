import os.path
from datetime import datetime
from os import getenv
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, ReplyKeyboardRemove

from db.crud import (get_user, get_user_works, get_work_questions, get_all_topics, create_new_work,
                     insert_work_questions, remove_last_user_work,
                     get_question_from_pool, close_question, open_next_question, end_work, get_topic_by_name_and_volume,
                     update_question_status, get_skipped_questions, get_hand_work, get_questions_list_by_id,
                     remove_work, get_all_pool, get_topic_by_volume)
from tgbot.handlers.trash import bot
from tgbot.keyboards.new_work import get_user_work_way_kb, SelectWorkWayCallbackFactory, get_new_work_types_kb, \
    SelectNewWorkTypeCallbackFactory, get_topics_kb, get_start_work_kb, StartNewWorkCallbackFactory, get_view_result_kb, \
    get_skip_question_kb, get_self_check_kb, SelfCheckCallbackFactory, get_redo_skipped_questions_kb, \
    ReDoSkippedQuestionCallbackFactory, get_topics_volumes_kb, SelectNewWorkVolumeCallbackFactory
from tgbot.lexicon.messages import lexicon as msg_lexicon
from tgbot.lexicon.buttons import lexicon as btns_lexicon, lexicon
from tgbot.states.picking_topic import UserTopicChoice, UserTopicVolumeChoice
from tgbot.states.wait_for_answer_to_question import UserAnswerToQuestion
from utils.answer_checker import check_answer
from utils.tags_helper import get_ege_tags_list, get_random_questions, get_questions_list_for_topic_work

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
                reply_markup=get_user_work_way_kb(hand_work_id=None)
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
    hand_work_id = callback_data.hand_work_id

    if action == 'start_new_work':
        remove_last_user_work(get_user(callback.from_user.id))

        if hand_work_id is None:
            await callback.message.edit_text(
                text=msg_lexicon['new_work']['select_type_of_work']
            )
            await callback.message.edit_reply_markup(
                reply_markup=get_new_work_types_kb()
            )

        else:
            hand_work = get_hand_work(identificator=hand_work_id)
            await callback.message.edit_text(
                text=msg_lexicon['new_work']['hand_work_caption'].format(hand_work.name),
            )

            await callback.message.edit_reply_markup(
                reply_markup=get_start_work_kb(work_type="hand_work", hand_work_id=hand_work_id)
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
        topics_all = get_all_topics(active=True)
        volumes = list(dict.fromkeys(t.volume for t in topics_all))
        await callback.message.edit_text(
            text=f"<b>{lexicon['new_work']['topic']}</b>"
                 f"\n\nВыбери нужный тебе раздел"
        )

        await callback.message.edit_reply_markup(
            reply_markup=get_topics_volumes_kb(volumes)
        )


@router.callback_query(SelectNewWorkVolumeCallbackFactory.filter())
async def process_starting_work(callback: types.CallbackQuery, callback_data: SelectNewWorkVolumeCallbackFactory,
                                state: FSMContext):
    volume = callback_data.volume

    if volume is None:
        await callback.answer()
        await callback.message.edit_text(
            text=msg_lexicon['new_work']['select_type_of_work']
        )
        await callback.message.edit_reply_markup(
            reply_markup=get_new_work_types_kb()
        )

    else:
        # topics_list = get_all_topics(active=True)
        topics_list = get_topic_by_volume(volume=volume)
        try:
            topics_list = sorted(topics_list, key=lambda x: int(x.name.split(" ")[0]))
        except (ValueError, IndexError):
            pass

        if not topics_list:
            await callback.answer(
                text=f"ℹ️ В разделе «{volume}» пока нет доступных тем. Попробуй выбрать другой раздел",
                show_alert=True
            )

        else:
            await callback.message.delete()

            await callback.message.answer(
                text=f"<b>{lexicon['new_work']['topic']}</b>"
                     f"\n\nВыбран раздел <b>{volume}</b>"
                     f"\n\nТеперь выбери нужную тебе тему",
                reply_markup=get_topics_kb(topics_list)
            )

            await state.set_state(UserTopicChoice.waiting_for_answer)
            await state.update_data(selected_volume=volume)


@router.message(UserTopicChoice.waiting_for_answer)
async def process_user_topic_choice(message: Message, state: FSMContext):
    data = await state.get_data()

    if message.text == btns_lexicon['service']['back']:
        await state.clear()
        await message.answer(
            text=btns_lexicon['service']['back'],
            reply_markup=ReplyKeyboardRemove()
        )

        topics_all = get_all_topics(active=True)
        volumes = list(dict.fromkeys(t.volume for t in topics_all))
        await message.answer(
            text=f"<b>{lexicon['new_work']['topic']}</b>"
                 f"\n\nВыбери нужный тебе раздел",
            reply_markup=get_topics_volumes_kb(volumes)
        )

    else:
        input_topic_name = message.text.strip()
        selected_volume = data['selected_volume']
        topic_data = get_topic_by_name_and_volume(topic_name=input_topic_name, volume=selected_volume)
        if topic_data is not None:
            await state.clear()
            msg = await message.answer(
                text="Загружаем данные",
                reply_markup=ReplyKeyboardRemove()
            )
            await msg.delete()

            await message.answer(
                text=msg_lexicon['new_work']['topic_work_caption_2'].format(
                    btns_lexicon['new_work']['topic'],
                    topic_data.volume,
                    topic_data.name
                ),
                reply_markup=get_start_work_kb(work_type="topic", topic_id=topic_data.id)
            )
        else:
            await message.answer(
                text=msg_lexicon['new_work']['topic_is_not_exists']
            )
            # await state.set_state(UserTopicChoice.waiting_for_answer)


@router.callback_query(StartNewWorkCallbackFactory.filter())
async def process_starting_work(callback: types.CallbackQuery, callback_data: StartNewWorkCallbackFactory,
                                state: FSMContext):
    await callback.answer()
    action = callback_data.action
    work_type = callback_data.work_type
    topic_id = callback_data.topic_id
    hand_work_id = callback_data.hand_work_id

    works_list = get_user_works(callback.from_user.id)
    if works_list and works_list[0].end_datetime is None:
        return

    if action == "start":

        await callback.message.delete()
        msg = await bot.send_message(
            chat_id=callback.from_user.id,
            text=msg_lexicon['new_work']['preparing_questions_list'],
            reply_markup=ReplyKeyboardRemove()
        )

        user = get_user(callback.from_user.id)
        work = create_new_work(user_id=user.id, work_type=work_type, topic_id=topic_id, hand_work_id=hand_work_id)

        pool = get_all_pool(active=True)

        if work_type == "ege":
            tags_list = get_ege_tags_list(each_question_limit=1)

        elif work_type == "hand_work":
            hand_work = get_hand_work(identificator=hand_work_id)

        if work_type == "ege":
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
                    text="<b>😬 Упс, что-то поломалось</b>"
                         "\n\nВ нашей базе не хватило задачек для того, чтобы составить для тебя тренировку. Мы уже получили информацию об этом и занялись исправлением ошибки. А пока ты можешь выбрать другую тему персональной тренировки."
                )
                # todo: отправить админу сообщение
                return

        elif work_type == "topic":
            data = get_questions_list_for_topic_work(topic_id=topic_id)
            if data['is_ok']:
                questions_list = data['detail']

            else:
                remove_work(work.id)
                await msg.delete()

                await callback.message.answer(
                    text="<b>😬 Упс, что-то поломалось</b>"
                         "\n\nВ нашей базе не хватило задачек для того, чтобы составить для тебя тренировку. Мы уже получили информацию об этом и занялись исправлением ошибки. А пока ты можешь выбрать другую тему персональной тренировки."
                )
                # todo: отправить админу сообщение
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
                text=msg_lexicon['new_work']['starting_hand_work_cancelled'].format(
                    getenv('BOT_NAME'),
                    hand_work_id
                )
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

            question_text_block = f"\n\n{self_check_note}\n\n{q_info.text}" if bool(
                q_info.is_selfcheck) else f"\n\n{q_info.text}"

            if bool(q_info.question_image):
                if os.path.exists(os.path.join(getenv('ROOT_FOLDER'), f"data/images/questions/{q_info.id}.png")):
                    src = os.path.join(getenv('ROOT_FOLDER'), f"data/images/questions/{q_info.id}.png")
                else:
                    src = os.path.join(getenv('ROOT_FOLDER'), f"data/images/questions/error.png")

                await bot.send_photo(
                    chat_id=user.telegram_id,
                    photo=FSInputFile(src),
                    caption=f"№{q.position} <code>(id{q_info.id})</code>"
                            f"{question_text_block}",
                    show_caption_above_media=True,
                    reply_markup=get_skip_question_kb(
                        self_check_btn_visible=bool(q_info.is_selfcheck)
                    )
                )
            else:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=f"№{q.position} <code>(id{q_info.id})</code>"
                         f"{question_text_block}",
                    reply_markup=get_skip_question_kb(
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

            if os.path.exists(os.path.join(getenv('ROOT_FOLDER'), f"data/images/answers/{question_data.id}.png")):
                src = os.path.join(getenv('ROOT_FOLDER'), f"data/images/answers/{question_data.id}.png")
            else:
                src = os.path.join(getenv('ROOT_FOLDER'), f"data/images/questions/error.png")

            await message.answer_photo(
                photo=FSInputFile(src),
                show_caption_above_media=True,
                caption=msg_lexicon['new_work']['answer_to_question_head'].format(data['position'], question_data.id) +
                        f"\n\n{question_data.answer}",
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
            work_data = end_work(work_id)
            await bot.send_message(
                chat_id=user_tid,
                text=msg_lexicon['new_work']['view_results'],
                reply_markup=get_view_result_kb(work_data.share_token)
            )
            if work_data.work_type == "hand_work":
                user = get_user(user_tid)
                hand_work_data = get_hand_work(work_data.hand_work_id)
                await bot.send_message(
                    chat_id=getenv('ADMIN_ID'),
                    text=msg_lexicon['new_work']['hand_work_ended'].format(user.name, hand_work_data.name),
                    reply_markup=get_view_result_kb(work_data.share_token)
                )
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
