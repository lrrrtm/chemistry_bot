import random
from datetime import datetime
from typing import List
from contextlib import contextmanager

from sqlalchemy import select, or_
from sqlalchemy.orm import aliased

from db.models import Pool, Topic, User, Work, WorkQuestion, Converting, HandWork
from db.database import Session


@contextmanager
def get_session():
    session = Session()
    session.expire_on_commit = False
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_user(name: str, tid: int) -> User:
    with get_session() as session:
        user = User(name=name, telegram_id=tid)
        session.add(user)
        session.commit()
        return user


def remove_user(telegram_id: int):
    with get_session() as session:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        session.delete(user)
        session.commit()
        return user


def end_work(work_id: int) -> Work:
    with get_session() as session:
        work = session.query(Work).filter_by(id=work_id).first()
        work.end_datetime = datetime.now()
        session.commit()
        return work


def remove_last_user_work(user: User):
    with get_session() as session:
        work = session.query(Work).filter_by(user_id=user.id).order_by(Work.id.desc()).first()
        # print(work.start_datetime, '!!!!!!!!')
        session.delete(work)
        session.commit()


def remove_work(work_id: int) -> Work:
    with get_session() as session:
        work = session.query(Work).filter_by(id=work_id).first()
        session.delete(work)
        session.commit()
        return work


def add_work_questions(work_id: int, questions_ids: List[int]) -> List[int]:
    with get_session() as session:
        ids = []
        for question_id in questions_ids:
            work_question = WorkQuestion(work_id=work_id, question_id=question_id)
            session.add(work_question)
            ids.append(work_question.id)
        session.commit()
        return ids


def get_user_works(tid: int) -> List[Work]:
    with get_session() as session:
        users_alias = aliased(User)
        works = (
            session.query(Work)
            .join(users_alias, Work.user_id == users_alias.id)
            .filter(users_alias.telegram_id == tid)
            .order_by(Work.start_datetime.desc())
            .all()
        )
        return works


def get_topic_by_id(topic_id: int):
    with get_session() as session:
        topic = session.query(Topic).filter_by(id=topic_id).first()
        return topic


def get_topic_by_name_and_volume(topic_name: str, volume: str) -> Topic:
    with get_session() as session:
        topic = session.query(Topic).filter_by(name=topic_name, volume=volume).first()
        return topic


def get_topics_table() -> List[Topic]:
    with get_session() as session:
        data = session.query(Topic).filter_by(is_active=1).all()
        return data


def get_all_pool(active: bool) -> List[Pool]:
    with get_session() as session:
        if active:
            data = session.query(Pool).filter_by(is_active=1).all()
        else:
            data = session.query(Pool).all()

        return data


def get_paginated_pool(page_num, per_page=15) -> List[Pool]:
    offset = (page_num - 1) * per_page
    with get_session() as session:
        items = session.query(Pool).filter_by(is_active=1).limit(per_page).offset(offset).all()
        return items


def get_pool_by_query(query: str) -> List[Pool]:
    with get_session() as session:
        if query.isnumeric():
            items = session.query(Pool).filter_by(is_active=1, id=int(query)).all()
        else:
            items = session.query(Pool).filter_by(is_active=1).filter(Pool.text.like(f'%{query}%')).all()

        return items


def get_pool_by_id(id: int) -> Pool:
    with get_session() as session:
        result = session.query(Pool).filter_by(id=id).first()

        return result


def get_pool_by_tags(tags: List[str]) -> List[Pool]:
    all_pool = get_all_pool(active=True)
    result = set()
    with get_session() as session:
        for cur_tag in tags:
            for q in all_pool:
                if cur_tag in q.tags_list and cur_tag not in result:
                    result.add(q)
    return list(result)


def get_all_topics(active: bool) -> List[Topic]:
    with get_session() as session:
        if active:
            data = session.query(Topic).filter_by(is_active=1).all()
        else:
            data = session.query(Topic).all()

        return data


def get_topic_by_volume(volume: str) -> List[Topic]:
    with get_session() as session:
        data = session.query(Topic).filter_by(is_active=1, volume=volume).all()
        return data


def get_all_tags() -> List[str]:
    with get_session() as session:
        stmt = select(Topic.tags_list)
        tags_lists = session.execute(stmt).scalars().all()
        return tags_lists


def get_all_users() -> List[User]:
    with get_session() as session:
        users = session.query(User).all()
        return users


def get_all_questions() -> List[Pool]:
    with get_session() as session:
        data = session.query(Pool).all()
        return data


def get_user(telegram_id: int) -> User:
    with get_session() as session:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        return user


def get_work_questions(work_id: int) -> List[WorkQuestion]:
    with get_session() as session:
        questions = (
            session.query(WorkQuestion)
            .filter_by(work_id=work_id)
            .order_by(WorkQuestion.position.asc())
            .all()
        )
        return questions


def get_question_from_pool(question_id: int) -> Pool:
    with get_session() as session:
        question = session.query(Pool).filter_by(id=question_id).first()
        return question


def get_work_by_url_data(user_id: str, telegram_id: str, work_id: str) -> Work:
    with get_session() as session:
        work = session.query(Work).filter_by(id=int(work_id), user_id=int(user_id)).first()
        return work


def get_work_questions_joined_pool(work_id: int) -> List[WorkQuestion]:
    with get_session() as session:
        results = (
            session.query(
                WorkQuestion.question_id,
                Pool.question_image,
                Pool.text,
                WorkQuestion.position,
                WorkQuestion.user_answer,
                Pool.answer,
                Pool.answer_image,
                WorkQuestion.user_mark,
                Pool.full_mark,
                WorkQuestion.start_datetime,
                WorkQuestion.end_datetime,

            )
            .join(Pool, WorkQuestion.question_id == Pool.id)
            .filter(WorkQuestion.work_id == work_id)
            .order_by(WorkQuestion.position.asc())
            .all()
        )
        return results


def get_random_questions_by_tag_list(tag_list: list) -> List[Pool]:
    with get_session() as session:
        selected_questions = []

        for tag_data in tag_list:
            tag = tag_data['tag']
            limit = tag_data['limit']

            t = tag
            # todo: разобраться
            # if "ege" in tag:
            #     t = [tag]

            questions = session.query(Pool).filter(Pool.tags_list.contains(t)).all()
            if tag_data['limit'] is not None:
                if len(questions) < limit:
                    return None
                else:
                    selected_questions.extend(random.sample(questions, limit))

            else:
                selected_questions.extend(questions)

        return selected_questions


def create_new_work(user_id: int, work_type: str, topic_id: int, hand_work_id: str = None) -> Work:
    with get_session() as session:
        work = Work(
            user_id=user_id,
            work_type=work_type,
            topic_id=topic_id if topic_id and topic_id > 0 else 0,
            hand_work_id=hand_work_id
        )
        session.add(work)
        session.commit()

        return work


def insert_work_questions(work: Work, questions_list: List[Pool]):
    with get_session() as session:
        for index, question in enumerate(questions_list):
            pos = index + 1

            q = WorkQuestion(
                work_id=work.id,
                question_id=question.id,
                position=pos,
            )
            session.add(q)
        session.commit()


def switch_image_flag(value: int, img_type: str, q_id: int):
    with get_session() as session:
        q = session.query(Pool).filter_by(id=q_id).first()

        if img_type == "question":
            q.question_image = value

        elif img_type == "answer":
            q.answer_image = value

        session.commit()


def update_question_status(q_id: int, status: str):
    with get_session() as session:
        q = session.query(WorkQuestion).filter_by(id=q_id).first()
        q.status = status
        q.start_datetime = None

        session.commit()


def deactivate_question(q_id: int):
    with get_session() as session:
        q = session.query(Pool).filter_by(id=q_id).first()
        q.is_active = 0

        session.commit()


def update_question(question: Pool):
    with get_session() as session:
        q = session.query(Pool).filter_by(id=question.id).first()

        q.text = question.text
        q.answer = question.answer
        q.full_mark = question.full_mark
        q.tags_list = question.tags_list
        q.is_rotate = question.is_rotate
        q.is_selfcheck = question.is_selfcheck
        q.level = question.level

        session.commit()


def close_question(q_id: int, user_answer: str, user_mark: int, end_datetime: datetime,
                   start_datetime: datetime = None):
    with get_session() as session:
        q = session.query(WorkQuestion).filter_by(id=q_id).first()
        q.status = "answered"
        q.user_answer = user_answer
        q.user_mark = user_mark
        q.start_datetime = start_datetime
        q.end_datetime = end_datetime

        session.commit()


def open_next_question(work_id: int) -> WorkQuestion:
    with get_session() as session:
        q = session.query(WorkQuestion).filter_by(work_id=work_id, status="waiting").first()
        if q is not None:
            q.status = "current"
            q.start_datetime = datetime.now()

            session.commit()
            return q
        return None


def get_skipped_questions(work_id: int) -> List[WorkQuestion]:
    with get_session() as session:
        data = session.query(WorkQuestion).filter_by(work_id=work_id, status="skipped").all()

        return data


def get_output_mark(input_mark: int):
    with get_session() as session:
        data = session.query(Converting).filter_by(input_mark=input_mark).first()
        if data is None:
            return 0
        return data.output_mark


def insert_new_hand_work(name: str, identificator: str, questions_ids_list: list) -> HandWork:
    with get_session() as session:
        w = HandWork(
            name=name,
            identificator=identificator,
            questions_list=questions_ids_list

        )
        session.add(w)
        session.commit()
        return w


def get_hand_work(identificator: str) -> HandWork:
    with get_session() as session:
        data = session.query(HandWork).filter_by(identificator=identificator).first()
        return data


def get_all_hand_works() -> List[HandWork]:
    with get_session() as session:
        return session.query(HandWork).order_by(HandWork.created_at.desc()).all()


def delete_hand_work(hand_work_id: int) -> bool:
    with get_session() as session:
        hw = session.query(HandWork).filter_by(id=hand_work_id).first()
        if not hw:
            return False
        session.delete(hw)
        session.commit()
        return True


def get_questions_list_by_id(ids_list: List[int]) -> List[Pool]:
    result = []
    with get_session() as session:
        for q_id in ids_list:
            q = session.query(Pool).filter_by(id=q_id).first()
            result.append(q)

        return result


def get_ege_converting() -> List[Converting]:
    with get_session() as session:
        data = session.query(Converting).all()
        return data


def update_ege_converting(data: dict):
    with get_session() as session:
        for key, value in data.items():
            el = session.query(Converting).filter_by(id=key).first()
            el.output_mark = value['value']
            session.commit()


def insert_pool_data(data: List[Pool]):
    with get_session() as session:
        for el in data:
            session.add(el)
        session.commit()
        return data


def insert_question_into_pool(q: Pool) -> Pool:
    with get_session() as session:
        session.add(q)
        session.commit()
        return q


def create_topic(name: str, volume: str) -> Topic:
    with get_session() as session:
        t = Topic(name=name, volume=volume, tags_list=[], is_active=1)
        session.add(t)
        session.commit()
        return t


def deactivate_topic(topic_id: int):
    with get_session() as session:
        t = session.query(Topic).filter_by(id=topic_id).first()
        if t:
            t.is_active = 0
            session.commit()


def update_topic(topic_id: int, tags_list: list):
    with get_session() as session:
        t = session.query(Topic).filter_by(id=topic_id).first()
        if t:
            t.tags_list = tags_list
            session.commit()
            return t


def insert_topics_data(data):
    with get_session() as session:
        old_data = session.query(Topic).all()
        old_topic_names = []

        for el in old_data:
            old_topic_names.append({'volume': el.volume, 'topic_name': el.name.lower()})
            el.is_active = 0
        session.commit()

        for volume, topics_data in data.items():
            for topic_name, tags_list in topics_data.items():
                if len(list(filter(lambda item: item['volume'] == volume and item['topic_name'].lower() == topic_name.lower(), old_topic_names))) == 1:
                # if topic_name.lower() in old_topic_names:
                    topic = session.query(Topic).filter_by(name=topic_name).first()
                    topic.tags_list = tags_list
                    topic.volume = volume
                    topic.is_active = 1
                else:
                    t = Topic(
                        name=topic_name,
                        tags_list=tags_list,
                        volume=volume,
                        is_active=1
                    )
                    session.add(t)

        session.commit()

        # for name, data in data.items():
        #     if name.lower() in old_topic_names:
        #         print("exists")
        #         topic = session.query(Topic).filter_by(name=name).first()
        #         topic.tags_list = data['tags']
        #         topic.volume = data['volume']
        #         topic.is_active = 1
        #
        #         print(topic.name, topic.volume, topic.tags_list)
        #
        #     else:
        #         print("new")
        #         t = Topic(
        #             name=name,
        #             tags_list=data['tags'],
        #             volume=data['volume'],
        #             is_active=1
        #         )
        #         print(t.name, t.volume, t.tags_list)
        #         session.add(t)
        # session.commit()


if __name__ == "__main__":
    data = get_pool_by_tags(['соли'])
    try:
        print(len(data))
        for el in data:
            print(el.id, el.text)
    except Exception as e:
        print(e)
