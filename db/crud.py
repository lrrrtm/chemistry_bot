import random
from datetime import datetime
from pydoc_data.topics import topics
from typing import List
from contextlib import contextmanager

from sqlalchemy.orm import aliased

from db.models import Pool, Stats, Topic, User, Work, WorkQuestion, Converting
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


def get_topic_by_name(topic_name: str) -> Topic:
    with get_session() as session:
        topic = session.query(Topic).filter_by(name=topic_name).first()
        return topic


def get_all_topics() -> List[Topic]:
    with get_session() as session:
        topics = session.query(Topic).all()
        return topics


def get_all_users() -> List[User]:
    with get_session() as session:
        users = session.query(User).all()
        return users

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


def get_work_by_url_data(user_id: int, telegram_id: int, work_id: int) -> Work:
    with get_session() as session:
        work = session.query(Work).filter_by(id=work_id, user_id=user_id).first()
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
            if "ege" in tag:
                t = [tag]

            questions = session.query(Pool).filter(Pool.tags_list.contains(t)).all()
            if tag_data['limit'] is not None:
                if len(questions) < limit:
                    return None
                else:
                    selected_questions.extend(random.sample(questions, limit))

            else:
                selected_questions.extend(questions)

        return selected_questions


def create_new_work(user_id: int, work_type: str, topic_id: int) -> Work:
    with get_session() as session:
        work = Work(
            user_id=user_id,
            work_type=work_type,
            topic_id=topic_id
        )
        session.add(work)
        session.commit()

        return work


def insert_work_questions(work: Work, questions_list: List[Pool]):
    with get_session() as session:
        for question in questions_list:
            pos = int(question.tags_list[-1].split("_")[-1]) if question.type == "ege" else -1

            q = WorkQuestion(
                work_id=work.id,
                question_id=question.id,
                position=pos,
            )
            session.add(q)
        session.commit()


def update_question_status(q_id: int, status: str):
    with get_session() as session:
        q = session.query(WorkQuestion).filter_by(id=q_id).first()
        q.status = status
        q.start_datetime = None

        session.commit()


def close_question(q_id: int, user_answer: str, user_mark: int, end_datetime: datetime):
    with get_session() as session:
        q = session.query(WorkQuestion).filter_by(id=q_id).first()
        q.status = "answered"
        q.user_answer = user_answer
        q.user_mark = user_mark
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
        return data.output_mark
