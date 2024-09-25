from datetime import datetime
from pydoc_data.topics import topics
from typing import List
from contextlib import contextmanager

from sqlalchemy.orm import aliased

from db.models import Pool, Stats, Topic, User, Work, WorkQuestion
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


def get_user(telegram_id: int) -> User:
    with get_session() as session:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        return user


def remove_user(telegram_id: int):
    with get_session() as session:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        session.delete(user)
        session.commit()
        return user


def add_work(user_id: int, work_type: str, topic_id: int) -> Work:
    with get_session() as session:
        work = Work(user_id=user_id, work_type=work_type, topic_id=topic_id)
        session.add(work)
        session.commit()
        return work


def end_work(work_id: int) -> Work:
    with get_session() as session:
        work = session.query(Work).filter_by(id=work_id).first()
        work.end_datetime = datetime.now()
        session.commit()
        return work


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


def get_topic(topic_id: int):
    with get_session as session:
        topic = session.query(Topic).filter_by(id=topic_id).first()
        return topic


def get_all_topics() -> List[Topic]:
    with get_session() as session:
        topics = session.query(Topic).all()
        return topics


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

print(get_work_questions_joined_pool(10))