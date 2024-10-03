import os.path
from datetime import datetime
from os import getenv
from typing import List

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InputFile, FSInputFile, ReplyKeyboardMarkup, ReplyKeyboardRemove

from db.crud import (get_user, get_user_works, get_topic_by_id, get_work_questions, get_all_topics, create_new_work,
                     get_random_questions_by_tag_list, insert_work_questions, remove_last_user_work,
                     get_question_from_pool, close_question, open_next_question, end_work, get_topic_by_name,
                     update_question_status, get_skipped_questions)
from db.models import Pool
from tgbot.handlers.menu import cmd_menu
from tgbot.handlers.trash import bot
from tgbot.keyboards.new_work import get_user_work_way_kb, SelectWorkWayCallbackFactory, get_new_work_types_kb, \
    SelectNewWorkTypeCallbackFactory, get_topics_kb, get_start_work_kb, StartNewWorkCallbackFactory, get_view_result_kb, \
    get_skip_question_kb, get_self_check_kb, SelfCheckCallbackFactory, get_redo_skipped_questions_kb, \
    ReDoSkippedQuestionCallbackFactory
from tgbot.lexicon.messages import lexicon
from tgbot.lexicon.buttons import lexicon as btns_lexicon
from tgbot.states.picking_topic import UserTopicChoice
from tgbot.states.wait_for_answer_to_question import UserAnswerToQuestion
from utils.answer_checker import check_answer
from utils.tags_helper import get_ege_tags_list, get_ege_self_check_tags_list

router = Router()


@router.message(Command("new_work"))
@router.message(F.text == btns_lexicon['main_menu']['new_work'])
async def cmd_new_work(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user is None:
        await message.answer(
            text="Для того, чтобы использовать эту команду, необходимо зарегистрироваться. Напиши или нажми /start"
        )
    else:
        works_list = get_user_works(message.from_user.id)
        if works_list and works_list[0].end_datetime is None:

            await message.answer(
                text="У тебя есть незаконченное задание, можем закончить его или создать новое. Как поступим?",
                reply_markup=get_user_work_way_kb()
            )
        else:
            await message.answer(
                text=f"<b>{btns_lexicon['main_menu']['new_work']}</>"
                     f"\n\nВыбери, что ты хочешь начать решать",
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
            text=f"<b>{btns_lexicon['main_menu']['new_work']}</>"
                 f"\n\nВыбери, что ты хочешь начать решать"
        )
        await callback.message.edit_reply_markup(
            reply_markup=get_new_work_types_kb()
        )
    elif action == 'continue_last_work':
        await callback.message.delete()
        await go_next_question(get_user(callback.from_user.id).telegram_id, state)


@router.callback_query(SelectNewWorkTypeCallbackFactory.filter())
async def process_user_work_way(callback: types.CallbackQuery, callback_data: SelectNewWorkTypeCallbackFactory,
                                state: FSMContext):
    await callback.answer()
    action = callback_data.work_type

    if action == "ege":
        await callback.message.edit_text(
            text=f"<b>{btns_lexicon['main_menu']['new_work']}</b>"
                 f"\n\nМы составим для тебя вариант из 34 заданий. "
                 f"После каждого задания будет необходимо отправить ответ в таком виде, который требует конкретное задание. Твои решения задания из второй части КИМа тебе нужно будет оценить самостоятельно."
                 f"\n\nКак только ты будешь готов(-а), нажми на кнопку под этим сообщением."
        )
        await callback.message.edit_reply_markup(
            reply_markup=get_start_work_kb(work_type="ege")
        )

    elif action == "topic":
        await callback.message.delete()

        topics_list = get_all_topics()
        await callback.message.answer(
            text=f"<b>{btns_lexicon['main_menu']['new_work']}</b>"
                 "\n\nВыбери из списка тему, на которую ты хочешь решать задания."
                 "\n\nМы составим для тебя вариант из 20 заданий. После каждого задания будет необходимо отправить ответ в таком виде, который требуется в задании. Решения некоторых заданий тебе нужно будет оценить самостоятельно.",
            reply_markup=get_topics_kb(topics_list)
        )
        await state.set_state(UserTopicChoice.waiting_for_answer)


@router.message(UserTopicChoice.waiting_for_answer)
async def process_user_topic_choice(message: Message, state: FSMContext):
    await state.clear()

    if message.text == btns_lexicon['service']['back']:
        await message.answer(
            text="<b>Выбор темы отменён</b>",
            reply_markup=ReplyKeyboardRemove()
        )
        await cmd_new_work(message, state)
    else:
        topic_name = message.text.strip()
        topic_data = get_topic_by_name(topic_name)
        if topic_data is not None:
            await message.answer(
                text=f"<b>{btns_lexicon['main_menu']['new_work']}</b>"
                     f"\n\nВыбрана тема «{topic_data.name}»",
                reply_markup=ReplyKeyboardRemove()
            )
            await message.answer(
                text=f"<b>{btns_lexicon['main_menu']['new_work']}</b>"
                     f"\n\nКак только ты будешь готов(-а), нажми на кнопку под этим сообщением.",
                reply_markup=get_start_work_kb(work_type="topic", topic_id=topic_data.id)
            )
        else:
            await message.answer(
                text=f"<b>Такой темы нет среди предложенных. Выбери одну из доступных тем, нажав на нужную кнопку.</b>"
            )
            await state.set_state(UserTopicChoice.waiting_for_answer)


@router.callback_query(StartNewWorkCallbackFactory.filter())
async def process_user_work_way(callback: types.CallbackQuery, callback_data: StartNewWorkCallbackFactory,
                                state: FSMContext):
    await callback.answer()
    action = callback_data.action
    work_type = callback_data.work_type
    topic_id = callback_data.topic_id

    if action == "start":
        await callback.message.delete()
        msg = await bot.send_message(
            chat_id=callback.from_user.id,
            text=f"<b>{btns_lexicon['main_menu']['new_work']}</b>"
                 f"\n\nПодбираем задачи специально для тебя...",
            reply_markup=ReplyKeyboardRemove()
        )

        user = get_user(callback.from_user.id)
        work = create_new_work(user_id=user.id, work_type=work_type, topic_id=topic_id)

        tags_list = get_ege_tags_list() if work_type == "ege" else [{'tag': t, 'limit': None} for t in
                                                                    get_topic_by_id(topic_id).tags_list]

        questions_list = get_random_questions_by_tag_list(tags_list)
        insert_work_questions(work, questions_list)

        await bot.send_message(
            chat_id=callback.from_user.id,
            text=f"<b>{btns_lexicon['main_menu']['new_work']}</b>"
                 f"\n\nВариант готов, можешь приступать к решению, желаем удачи!"
        )

        await go_next_question(user.telegram_id, state)

    elif action == "cancel":
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
        await callback.message.edit_text(
            text=f"Отменили создание нового варианта. Когда снова захочешь порешать задачки, нажимай на <b>{btns_lexicon['main_menu']['new_work']}</b>"
        )


async def go_next_question(user_tid: int, state: FSMContext):
    user = get_user(user_tid)
    work = get_user_works(user.telegram_id)[0]
    questions_list = get_work_questions(work_id=work.id)

    self_check_note = f"<blockquote>Ответ и решение этого задания тебе нужно проверить самостоятельно. Для этого нажми на кнопку «{btns_lexicon['new_work']['self_check']}» после того, как получишь ответ.</blockquote>"

    for q in questions_list:
        if q.status in ["current", "waiting"]:
            q_info = get_question_from_pool(q.question_id)

            question_text_block = f"\n\n{self_check_note}\n\n{q_info.text}" if any(
                elem in q_info.tags_list for elem in get_ege_self_check_tags_list()) else f"\n\n{q_info.text}"

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
                        self_check_btn_visible=any(elem in q_info.tags_list for elem in get_ege_self_check_tags_list())
                    )
                )
            else:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=f"№{q.position} <code>(id{q_info.id})</code>"
                         f"{question_text_block}",
                    reply_markup=get_skip_question_kb(
                        self_check_btn_visible=any(elem in q_info.tags_list for elem in get_ege_self_check_tags_list())
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
        await message.answer(f"Вопрос №{data['position']} пропущен, переходим к следующему")
        update_question_status(
            q_id=data['question_id'],
            status="skipped"
        )
        # close_question(
        #     q_id=data['question_id'],
        #     user_answer="вопрос пропущен",
        #     user_mark=0,
        #     end_datetime=datetime.now()
        # )
    elif message.text.strip() == btns_lexicon['new_work']['self_check']:
        # todo: генерация сообщения для проверки решения
        question_data = data['question_data']
        if bool(question_data.answer_image):
            if os.path.exists(os.path.join(getenv('ROOT_FOLDER'), f"data/answers_images/{question_data.id}.png")):
                src = os.path.join(getenv('ROOT_FOLDER'), f"data/answers_images/{question_data.id}.png")
            else:
                src = os.path.exists(os.path.join(getenv('ROOT_FOLDER'), f"data/questions_images/error.png"))

            await message.answer_photo(
                photo=FSInputFile(src),
                show_caption_above_media=True,
                caption=f"Ответ на вопрос №{data['position']} <code>(id{question_data.id})</code>",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await message.answer(
                text=f"Ответ на вопрос №{data['position']} <code>(id{question_data.id})</code>"
                     f"\n\n{question_data.answer}",
                reply_markup=ReplyKeyboardRemove()
            )
        await message.answer(
            text=f"Оцени свой ответ, поставив нужный балл за вопрос №{data['position']}",
            reply_markup=get_self_check_kb(
                max_mark=question_data.full_mark,
                work_id=data['work_id'],
                work_question_id=data['question_id'],
            )
        )
        return

    else:
        if any(elem in data['question_data'].tags_list for elem in get_ege_self_check_tags_list()):
            await message.answer(
                text=f"Это задание требует самостоятельной проверки твоего решения. Пожалуйста, нажми на кнопку «{btns_lexicon['new_work']['self_check']}»"
            )
            return

        close_question(
            q_id=data['question_id'],
            user_answer=message.text.strip(),
            user_mark=check_answer(data['question_data'], message.text.strip()),
            end_datetime=datetime.now()
        )

    result = open_next_question(data['work_id'])

    if result is None:
        skipped_questions = get_skipped_questions(data['work_id'])
        if skipped_questions:
            await message.answer(
                text=f"У тебя остались пропущенные вопросы ({len(skipped_questions)}), хочешь вернуться к ним и попробовать решить их ещё раз?",
                reply_markup=get_redo_skipped_questions_kb(data['work_id'])
            )
            await state.clear()
        else:
            msg = await message.answer(
                text="<b>Обрабатываем твои ответы...</b>",
                reply_markup=ReplyKeyboardRemove()
            )

            await msg.delete()

            await bot.send_message(
                chat_id=message.chat.id,
                text=f"<b>📊 Результаты</b>"
                     f"\n\nНажми на кнопку под сообщением, чтобы посмотреть результаты выполнения работы",
                reply_markup=get_view_result_kb(get_user(message.chat.id), data['work_id'])
            )
            end_work(data['work_id'])
            await state.clear()
    else:
        await go_next_question(message.from_user.id, state)


@router.callback_query(SelfCheckCallbackFactory.filter())
async def process_self_check(callback: types.CallbackQuery, callback_data: SelfCheckCallbackFactory,
                             state: FSMContext):
    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    mark = callback_data.mark
    work_question_id = callback_data.work_question_id
    work_id = callback_data.work_id

    await callback.message.edit_text(
        text=f"<b>Выставленно баллов: {mark}</b>"
    )

    close_question(
        q_id=work_question_id,
        user_answer="самостоятельная проверка",
        user_mark=mark,
        end_datetime=datetime.now()
    )

    result = open_next_question(work_id)

    if result is None:
        skipped_questions = get_skipped_questions(work_id)
        if skipped_questions:
            await callback.message.answer(
                text=f"У тебя остались пропущенные вопросы ({len(skipped_questions)}), хочешь вернуться к ним и попробовать решить их ещё раз?",
                reply_markup=get_redo_skipped_questions_kb(work_id)
            )
            await state.clear()
        else:
            msg = await callback.message.answer(
                text="<b>Обрабатываем твои ответы...</b>",
                reply_markup=ReplyKeyboardRemove()
            )

            await msg.delete()

            await bot.send_message(
                chat_id=callback.from_user.id,
                text=f"<b>📊 Результаты</b>"
                     f"\n\nНажми на кнопку под этим сообщением, чтобы их посмотреть.",
                reply_markup=get_view_result_kb(get_user(callback.from_user.id), work_id)
            )
            end_work(work_id)
            await state.clear()
    else:
        await go_next_question(callback.from_user.id, state)


@router.callback_query(ReDoSkippedQuestionCallbackFactory.filter())
async def process_user_work_way(callback: types.CallbackQuery, callback_data: ReDoSkippedQuestionCallbackFactory,
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
                user_answer="---",
                user_mark=0,
                end_datetime=datetime.now()
            )
        await callback.message.answer(
            text=f"<b>📊 Результаты</b>"
                 f"\n\nНажми на кнопку под сообщением, чтобы посмотреть результаты выполнения работы",
            reply_markup=get_view_result_kb(get_user(callback.from_user.id), work_id)
        )
        end_work(work_id)
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