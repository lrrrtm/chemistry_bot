from datetime import datetime, timedelta
from typing import List, Optional
from contextlib import contextmanager
import uuid

from sqlalchemy.orm import aliased
from sqlalchemy import func, or_

from db.models import (
    Pool,
    Topic,
    User,
    Work,
    WorkQuestion,
    Converting,
    HandWork,
    Tag,
    TopicTag,
    PoolTag,
    HandWorkQuestion,
    TheoryDocument,
    TheoryDocumentTag,
    StudentAccessGrant,
)
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


def _normalize_tag(raw: str | None) -> str | None:
    if raw is None:
        return None
    tag = raw.strip().lower().replace("\u0451", "\u0435")
    return tag or None


def _normalized_tags(tags_list: list | None) -> list[str]:
    if not tags_list:
        return []
    result: list[str] = []
    seen: set[str] = set()
    for raw in tags_list:
        normalized = _normalize_tag(str(raw))
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def _get_or_create_tag(session, slug: str) -> Tag:
    tag = session.query(Tag).filter_by(slug=slug).first()
    if tag is None:
        tag = Tag(slug=slug, label=slug)
        session.add(tag)
        session.flush()
    return tag


def _sync_pool_tags(session, pool_id: int, tags_list: list | None):
    normalized = _normalized_tags(tags_list)
    session.query(PoolTag).filter_by(pool_id=pool_id).delete()
    for slug in normalized:
        tag = _get_or_create_tag(session, slug)
        session.add(PoolTag(pool_id=pool_id, tag_id=tag.id))


def _sync_topic_tags(session, topic_id: int, tags_list: list | None):
    normalized = _normalized_tags(tags_list)
    session.query(TopicTag).filter_by(topic_id=topic_id).delete()
    for slug in normalized:
        tag = _get_or_create_tag(session, slug)
        session.add(TopicTag(topic_id=topic_id, tag_id=tag.id))


def _sync_theory_document_tags(session, document_id: int, tags_list: list | None):
    normalized = _normalized_tags(tags_list)
    session.query(TheoryDocumentTag).filter_by(document_id=document_id).delete()
    for slug in normalized:
        tag = _get_or_create_tag(session, slug)
        session.add(TheoryDocumentTag(document_id=document_id, tag_id=tag.id))


def _load_pool_tags_map(session, pool_ids: list[int]) -> dict[int, list[str]]:
    if not pool_ids:
        return {}
    rows = (
        session.query(PoolTag.pool_id, Tag.slug)
        .join(Tag, Tag.id == PoolTag.tag_id)
        .filter(PoolTag.pool_id.in_(pool_ids))
        .order_by(PoolTag.pool_id.asc(), Tag.slug.asc())
        .all()
    )
    result: dict[int, list[str]] = {}
    for pool_id, slug in rows:
        result.setdefault(pool_id, []).append(slug)
    return result


def _hydrate_pool_tags(session, questions: list[Pool]) -> list[Pool]:
    tags_map = _load_pool_tags_map(session, [q.id for q in questions])
    for question in questions:
        question.tags_list = list(tags_map.get(question.id, []))
    return questions


def _load_topic_tags_map(session, topic_ids: list[int]) -> dict[int, list[str]]:
    if not topic_ids:
        return {}
    rows = (
        session.query(TopicTag.topic_id, Tag.slug)
        .join(Tag, Tag.id == TopicTag.tag_id)
        .filter(TopicTag.topic_id.in_(topic_ids))
        .order_by(TopicTag.topic_id.asc(), Tag.slug.asc())
        .all()
    )
    result: dict[int, list[str]] = {}
    for topic_id, slug in rows:
        result.setdefault(topic_id, []).append(slug)
    return result


def _hydrate_topic_tags(session, topics: list[Topic]) -> list[Topic]:
    tags_map = _load_topic_tags_map(session, [t.id for t in topics])
    for topic in topics:
        topic.tags_list = list(tags_map.get(topic.id, []))
    return topics


def _load_theory_document_tags_map(session, document_ids: list[int]) -> dict[int, list[str]]:
    if not document_ids:
        return {}
    rows = (
        session.query(TheoryDocumentTag.document_id, Tag.slug)
        .join(Tag, Tag.id == TheoryDocumentTag.tag_id)
        .filter(TheoryDocumentTag.document_id.in_(document_ids))
        .order_by(TheoryDocumentTag.document_id.asc(), Tag.slug.asc())
        .all()
    )
    result: dict[int, list[str]] = {}
    for document_id, slug in rows:
        result.setdefault(document_id, []).append(slug)
    return result


def _hydrate_theory_document_tags(session, documents: list[TheoryDocument]) -> list[TheoryDocument]:
    tags_map = _load_theory_document_tags_map(session, [document.id for document in documents])
    for document in documents:
        document.tags_list = list(tags_map.get(document.id, []))
    return documents


def _load_hand_work_question_ids_map(session, hand_work_ids: list[int]) -> dict[int, list[int]]:
    if not hand_work_ids:
        return {}
    rows = (
        session.query(HandWorkQuestion.hand_work_id, HandWorkQuestion.question_id)
        .filter(HandWorkQuestion.hand_work_id.in_(hand_work_ids))
        .order_by(HandWorkQuestion.hand_work_id.asc(), HandWorkQuestion.position.asc())
        .all()
    )
    result: dict[int, list[int]] = {}
    for hand_work_id, question_id in rows:
        result.setdefault(hand_work_id, []).append(question_id)
    return result


def _hydrate_hand_work_questions(session, hand_works: list[HandWork]) -> list[HandWork]:
    questions_map = _load_hand_work_question_ids_map(session, [hw.id for hw in hand_works])
    for hand_work in hand_works:
        hand_work.questions_list = list(questions_map.get(hand_work.id, []))
    return hand_works


def _normalize_work_source(
    work_type: str,
    topic_id: Optional[int],
    hand_work_id: Optional[str],
) -> tuple[Optional[int], Optional[str]]:
    normalized_topic_id = topic_id if topic_id and topic_id > 0 else None
    normalized_hand_work_id = hand_work_id.strip() if hand_work_id else None
    if normalized_hand_work_id == "":
        normalized_hand_work_id = None

    if work_type == "topic":
        if normalized_topic_id is None:
            raise ValueError("topic_id is required for topic work")
        return normalized_topic_id, None

    if work_type == "hand_work":
        if normalized_hand_work_id is None:
            raise ValueError("hand_work_id is required for hand_work")
        return None, normalized_hand_work_id

    return None, None


def _with_for_update(query):
    lock_method = getattr(query, "with_for_update", None)
    if callable(lock_method):
        return lock_method()
    return query


def _get_current_work_questions_locked(session, work_id: int) -> list[WorkQuestion]:
    query = (
        session.query(WorkQuestion)
        .filter_by(work_id=work_id, status="current")
        .order_by(WorkQuestion.position.asc())
    )
    return _with_for_update(query).all()


def _get_first_waiting_work_question_locked(session, work_id: int) -> Optional[WorkQuestion]:
    query = (
        session.query(WorkQuestion)
        .filter_by(work_id=work_id, status="waiting")
        .order_by(WorkQuestion.position.asc())
    )
    return _with_for_update(query).first()


def _heal_current_work_questions(session, work_id: int) -> Optional[WorkQuestion]:
    current_questions = _get_current_work_questions_locked(session, work_id)
    if not current_questions:
        return None

    keeper = current_questions[0]
    keeper.current_work_id = keeper.work_id
    for duplicate in current_questions[1:]:
        duplicate.status = "waiting"
        duplicate.current_work_id = None
        duplicate.start_datetime = None

    return keeper


def _purge_user_related_data(session, user_id: int):
    work_ids = [work_id for (work_id,) in session.query(Work.id).filter_by(user_id=user_id).all()]
    if work_ids:
        session.query(WorkQuestion).filter(WorkQuestion.work_id.in_(work_ids)).delete(synchronize_session=False)
        session.query(Work).filter(Work.id.in_(work_ids)).delete(synchronize_session=False)
    session.query(StudentAccessGrant).filter_by(user_id=user_id).delete(synchronize_session=False)


def _active_users_query(session):
    return session.query(User).filter_by(is_deleted=0)


def _active_student_access_grants_query(session):
    return session.query(StudentAccessGrant).filter(StudentAccessGrant.consumed_at.is_(None))


def create_user(name: str, tid: int) -> User:
    with get_session() as session:
        existing_user = session.query(User).filter_by(telegram_id=tid).first()
        if existing_user:
            if existing_user.is_deleted:
                existing_user_id = getattr(existing_user, "id", None)
                if existing_user_id is not None:
                    _purge_user_related_data(session, existing_user_id)
            existing_user.name = name
            existing_user.is_deleted = 0
            session.commit()
            return existing_user

        user = User(name=name, telegram_id=tid)
        session.add(user)
        session.commit()
        return user


def create_invited_user(
    name: str,
) -> User:
    with get_session() as session:
        user = User(
            name=name,
            telegram_id=None,
        )
        session.add(user)
        session.commit()
        return user


def issue_student_access_grant(
    user_id: int,
    purpose: str,
    token_hash: str,
    expires_at: datetime,
    created_by: str | None = None,
    revoke_existing: bool = True,
) -> StudentAccessGrant | None:
    with get_session() as session:
        user = _active_users_query(session).filter_by(id=user_id).first()
        if not user:
            return None
        if revoke_existing:
            session.query(StudentAccessGrant).filter_by(
                user_id=user_id,
                purpose=purpose,
            ).delete(synchronize_session=False)
        grant = StudentAccessGrant(
            user_id=user_id,
            purpose=purpose,
            token_hash=token_hash,
            expires_at=expires_at,
            created_by=created_by,
        )
        session.add(grant)
        session.commit()
        return grant


def get_student_access_grant_by_token_hash(token_hash: str) -> StudentAccessGrant | None:
    with get_session() as session:
        return session.query(StudentAccessGrant).filter_by(token_hash=token_hash).first()


def revoke_student_access_grants(user_id: int, purpose: str | None = None):
    with get_session() as session:
        query = session.query(StudentAccessGrant).filter_by(user_id=user_id)
        if purpose:
            query = query.filter_by(purpose=purpose)
        query.delete(synchronize_session=False)
        session.commit()


def mark_student_access_grant_consumed(grant_id: int) -> StudentAccessGrant | None:
    with get_session() as session:
        grant = session.query(StudentAccessGrant).filter_by(id=grant_id).first()
        if not grant:
            return None
        grant.consumed_at = datetime.now()
        session.commit()
        return grant


def activate_user_credentials(
    user_id: int,
    username: str,
    password_hash: str,
) -> User | None:
    with get_session() as session:
        user = _active_users_query(session).filter_by(id=user_id).first()
        if not user:
            return None
        user.username = username
        user.password_hash = password_hash
        session.commit()
        return user


def revoke_user_web_access(user_id: int) -> User | None:
    with get_session() as session:
        user = _active_users_query(session).filter_by(id=user_id).first()
        if not user:
            return None
        user.username = None
        user.password_hash = None
        user.student_token_version = (user.student_token_version or 0) + 1
        session.query(StudentAccessGrant).filter_by(user_id=user_id).delete(synchronize_session=False)
        session.commit()
        return user


def remove_user(user_id: int):
    with get_session() as session:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            _purge_user_related_data(session, user.id)
            user.username = None
            user.password_hash = None
            user.invite_token_hash = None
            user.invite_expires_at = None
            user.invite_consumed_at = None
            user.telegram_link_token_hash = None
            user.telegram_link_expires_at = None
            user.telegram_id = None
            user.is_deleted = 1
            session.commit()
        return user


def end_work(work_id: int) -> Work:
    with get_session() as session:
        work = session.query(Work).filter_by(id=work_id).first()
        work.end_datetime = datetime.now()
        work.share_token = str(uuid.uuid4())
        session.commit()
        return work


def get_work_by_token(token: str) -> Work:
    with get_session() as session:
        return session.query(Work).filter_by(share_token=token).first()


def get_user_by_id(user_id: int) -> User:
    with get_session() as session:
        return _active_users_query(session).filter_by(id=user_id).first()


def remove_last_user_work(user: User):
    with get_session() as session:
        work = session.query(Work).filter_by(user_id=user.id).order_by(Work.id.desc()).first()
        if work is None:
            return None
        session.delete(work)
        session.commit()


def remove_work(work_id: int) -> Work:
    with get_session() as session:
        work = session.query(Work).filter_by(id=work_id).first()
        session.delete(work)
        session.commit()
        return work


def get_user_works(tid: int) -> List[Work]:
    with get_session() as session:
        users_alias = aliased(User)
        works = (
            session.query(Work)
            .join(users_alias, Work.user_id == users_alias.id)
            .filter(users_alias.telegram_id == tid, users_alias.is_deleted == 0)
            .order_by(Work.start_datetime.desc())
            .all()
        )
        return works


def get_user_works_by_user_id(user_id: int) -> List[Work]:
    with get_session() as session:
        return (
            session.query(Work)
            .filter(Work.user_id == user_id)
            .order_by(Work.start_datetime.desc())
            .all()
        )


def get_topic_by_id(topic_id: int):
    with get_session() as session:
        topic = session.query(Topic).filter_by(id=topic_id).first()
        if topic:
            _hydrate_topic_tags(session, [topic])
        return topic


def get_topic_by_name_and_volume(topic_name: str, volume: str) -> Topic:
    with get_session() as session:
        topic = session.query(Topic).filter_by(name=topic_name, volume=volume).first()
        if topic:
            _hydrate_topic_tags(session, [topic])
        return topic


def get_topics_table() -> List[Topic]:
    with get_session() as session:
        data = session.query(Topic).filter_by(is_active=1).all()
        _hydrate_topic_tags(session, data)
        return data


def get_all_pool(active: bool) -> List[Pool]:
    with get_session() as session:
        if active:
            data = session.query(Pool).filter_by(is_active=1).all()
        else:
            data = session.query(Pool).all()

        _hydrate_pool_tags(session, data)
        return data


def get_pool_by_tags(tags: list) -> List[Pool]:
    with get_session() as session:
        normalized = _normalized_tags(tags)
        if not normalized:
            return []
        data = (
            session.query(Pool)
            .join(PoolTag, PoolTag.pool_id == Pool.id)
            .join(Tag, Tag.id == PoolTag.tag_id)
            .filter(Pool.is_active == 1, Tag.slug.in_(normalized))
            .distinct()
            .all()
        )
        _hydrate_pool_tags(session, data)
        return data


def get_pool_by_id(id: int) -> Pool:
    with get_session() as session:
        result = session.query(Pool).filter_by(id=id).first()
        if result:
            _hydrate_pool_tags(session, [result])

        return result


def get_all_topics(active: bool) -> List[Topic]:
    with get_session() as session:
        if active:
            data = session.query(Topic).filter_by(is_active=1).all()
        else:
            data = session.query(Topic).all()

        _hydrate_topic_tags(session, data)
        return data


def get_topic_by_volume(volume: str) -> List[Topic]:
    with get_session() as session:
        data = session.query(Topic).filter_by(is_active=1, volume=volume).all()
        _hydrate_topic_tags(session, data)
        return data


def rename_user(user_id: int, new_name: str) -> None:
    with get_session() as session:
        user = session.query(User).filter_by(id=user_id, is_deleted=0).first()
        if user:
            user.name = new_name
            session.commit()


def get_all_users() -> List[User]:
    with get_session() as session:
        users = session.query(User).filter_by(is_deleted=0).all()
        return users


def get_all_questions() -> List[Pool]:
    with get_session() as session:
        data = session.query(Pool).all()
        _hydrate_pool_tags(session, data)
        return data


def get_user(telegram_id: int) -> User:
    with get_session() as session:
        user = session.query(User).filter_by(telegram_id=telegram_id, is_deleted=0).first()
        return user


def get_user_by_username(username: str) -> User | None:
    with get_session() as session:
        return _active_users_query(session).filter(func.lower(User.username) == username.lower()).first()


def get_user_by_invite_token_hash(invite_token_hash: str) -> User | None:
    with get_session() as session:
        return _active_users_query(session).filter_by(invite_token_hash=invite_token_hash).first()


def get_user_by_telegram_link_token_hash(token_hash: str) -> User | None:
    with get_session() as session:
        return _active_users_query(session).filter_by(telegram_link_token_hash=token_hash).first()


def set_telegram_link_token(
    user_id: int,
    token_hash: str | None,
    expires_at: datetime | None,
) -> User | None:
    with get_session() as session:
        user = _active_users_query(session).filter_by(id=user_id).first()
        if not user:
            return None
        user.telegram_link_token_hash = token_hash
        user.telegram_link_expires_at = expires_at
        session.commit()
        return user


def link_telegram_to_user(user_id: int, telegram_id: int) -> User:
    with get_session() as session:
        target_user = _active_users_query(session).filter_by(id=user_id).first()
        if not target_user:
            raise ValueError("User not found")

        already_linked = _active_users_query(session).filter_by(telegram_id=telegram_id).first()
        if already_linked and already_linked.id != user_id:
            raise ValueError("Telegram already linked")

        target_user.telegram_id = telegram_id
        target_user.telegram_link_token_hash = None
        target_user.telegram_link_expires_at = None
        session.commit()
        return target_user


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
        if question:
            _hydrate_pool_tags(session, [question])
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


def create_new_work(
    user_id: int,
    work_type: str,
    topic_id: Optional[int],
    hand_work_id: Optional[str] = None,
) -> Work:
    with get_session() as session:
        normalized_topic_id, normalized_hand_work_id = _normalize_work_source(
            work_type=work_type,
            topic_id=topic_id,
            hand_work_id=hand_work_id,
        )
        work = Work(
            user_id=user_id,
            work_type=work_type,
            topic_id=normalized_topic_id,
            hand_work_id=normalized_hand_work_id,
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
        q.current_work_id = q.work_id if status == "current" else None
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
        _sync_pool_tags(session, q.id, q.tags_list)

        session.commit()


def close_question(q_id: int, user_answer: str, user_mark: int, end_datetime: datetime,
                   start_datetime: datetime = None):
    with get_session() as session:
        q = session.query(WorkQuestion).filter_by(id=q_id).first()
        q.status = "answered"
        q.current_work_id = None
        q.user_answer = user_answer
        q.user_mark = user_mark
        q.start_datetime = start_datetime
        q.end_datetime = end_datetime

        session.commit()


def open_next_question(work_id: int) -> WorkQuestion:
    with get_session() as session:
        keeper = _heal_current_work_questions(session, work_id)
        if keeper is not None:
            session.commit()
            return keeper

        q = _get_first_waiting_work_question_locked(session, work_id)
        if q is not None:
            q.status = "current"
            q.current_work_id = q.work_id
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
        )
        session.add(w)
        session.flush()
        for index, question_id in enumerate(questions_ids_list, start=1):
            session.add(
                HandWorkQuestion(
                    hand_work_id=w.id,
                    question_id=question_id,
                    position=index,
                )
            )
        session.commit()
        return w


def get_hand_work(identificator: str) -> HandWork:
    with get_session() as session:
        data = session.query(HandWork).filter_by(identificator=identificator).first()
        if data:
            _hydrate_hand_work_questions(session, [data])
        return data


def get_all_hand_works() -> List[HandWork]:
    with get_session() as session:
        data = session.query(HandWork).filter_by(is_deleted=0).order_by(HandWork.created_at.desc()).all()
        _hydrate_hand_work_questions(session, data)
        return data


def delete_hand_work(hand_work_id: int) -> bool:
    with get_session() as session:
        hw = session.query(HandWork).filter_by(id=hand_work_id).first()
        if not hw:
            return False
        hw.is_deleted = 1
        session.commit()
        return True


def get_questions_list_by_id(ids_list: List[int]) -> List[Pool]:
    with get_session() as session:
        if not ids_list:
            return []

        data = session.query(Pool).filter(Pool.id.in_(ids_list)).all()
        _hydrate_pool_tags(session, data)
        data_by_id = {question.id: question for question in data}
        return [data_by_id[q_id] for q_id in ids_list if q_id in data_by_id]


def get_hand_work_questions(identificator: str) -> List[Pool]:
    with get_session() as session:
        data = (
            session.query(Pool)
            .join(HandWorkQuestion, HandWorkQuestion.question_id == Pool.id)
            .join(HandWork, HandWork.id == HandWorkQuestion.hand_work_id)
            .filter(HandWork.identificator == identificator)
            .order_by(HandWorkQuestion.position.asc())
            .all()
        )
        _hydrate_pool_tags(session, data)
        return data


def get_hand_work_question_count(identificator: str) -> int:
    with get_session() as session:
        return (
            session.query(HandWorkQuestion.id)
            .join(HandWork, HandWork.id == HandWorkQuestion.hand_work_id)
            .filter(HandWork.identificator == identificator)
            .count()
        )


def get_ege_converting() -> List[Converting]:
    with get_session() as session:
        data = session.query(Converting).all()
        return data


def update_ege_converting(data: dict):
    with get_session() as session:
        for input_mark, value in data.items():
            el = session.query(Converting).filter_by(input_mark=input_mark).first()
            if el is not None:
                el.output_mark = value['value']
        session.commit()


def insert_pool_data(data: List[Pool]):
    with get_session() as session:
        for el in data:
            session.add(el)
        session.flush()
        for el in data:
            _sync_pool_tags(session, el.id, el.tags_list)
        session.commit()
        return data


def insert_question_into_pool(q: Pool) -> Pool:
    with get_session() as session:
        session.add(q)
        session.flush()
        _sync_pool_tags(session, q.id, q.tags_list)
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
            _sync_topic_tags(session, t.id, t.tags_list)
            session.commit()
            return t


def get_theory_document_by_id(document_id: int, active_only: bool = False) -> TheoryDocument | None:
    with get_session() as session:
        query = session.query(TheoryDocument).filter_by(id=document_id)
        if active_only:
            query = query.filter_by(is_active=1)
        document = query.first()
        if document:
            _hydrate_theory_document_tags(session, [document])
        return document


def get_theory_documents(active: bool = True, query: str | None = None) -> list[TheoryDocument]:
    with get_session() as session:
        sql_query = session.query(TheoryDocument)
        if active:
            sql_query = sql_query.filter(TheoryDocument.is_active == 1)

        raw_query = (query or "").strip()
        normalized_query = _normalize_tag(raw_query)
        if raw_query:
            title_pattern = f"%{raw_query.lower()}%"
            tag_pattern = f"%{normalized_query or raw_query.lower()}%"
            sql_query = (
                sql_query
                .outerjoin(TheoryDocumentTag, TheoryDocumentTag.document_id == TheoryDocument.id)
                .outerjoin(Tag, Tag.id == TheoryDocumentTag.tag_id)
                .filter(
                    or_(
                        func.lower(TheoryDocument.title).like(title_pattern),
                        func.lower(Tag.slug).like(tag_pattern),
                        func.lower(Tag.label).like(tag_pattern),
                    )
                )
                .distinct()
            )

        documents = (
            sql_query
            .order_by(TheoryDocument.title.asc(), TheoryDocument.created_at.desc())
            .all()
        )
        _hydrate_theory_document_tags(session, documents)
        return documents


def create_theory_document(
    title: str,
    file_name: str,
    original_file_name: str | None,
    mime_type: str,
    file_size: int,
    tags_list: list[str] | None,
) -> TheoryDocument:
    with get_session() as session:
        document = TheoryDocument(
            title=title,
            file_name=file_name,
            original_file_name=original_file_name,
            mime_type=mime_type,
            file_size=file_size,
            tags_list=tags_list or [],
            is_active=1,
            created_at=datetime.now(),
        )
        session.add(document)
        session.flush()
        _sync_theory_document_tags(session, document.id, document.tags_list)
        session.commit()
        _hydrate_theory_document_tags(session, [document])
        return document


def update_theory_document(
    document_id: int,
    title: str,
    tags_list: list[str] | None,
) -> TheoryDocument | None:
    with get_session() as session:
        document = session.query(TheoryDocument).filter_by(id=document_id).first()
        if not document:
            return None
        document.title = title
        document.tags_list = list(tags_list or [])
        _sync_theory_document_tags(session, document.id, document.tags_list)
        session.commit()
        _hydrate_theory_document_tags(session, [document])
        return document


def replace_theory_document_file(
    document_id: int,
    file_name: str,
    original_file_name: str | None,
    mime_type: str,
    file_size: int,
) -> TheoryDocument | None:
    with get_session() as session:
        document = session.query(TheoryDocument).filter_by(id=document_id).first()
        if not document:
            return None
        document.file_name = file_name
        document.original_file_name = original_file_name
        document.mime_type = mime_type
        document.file_size = file_size
        session.commit()
        _hydrate_theory_document_tags(session, [document])
        return document


def deactivate_theory_document(document_id: int) -> bool:
    with get_session() as session:
        document = session.query(TheoryDocument).filter_by(id=document_id).first()
        if not document:
            return False
        document.is_active = 0
        session.commit()
        return True


# ── TMA-specific helpers ──────────────────────────────────────────────────────

def get_work_by_id(work_id: int) -> Work:
    with get_session() as session:
        return session.query(Work).filter_by(id=work_id).first()


def get_current_work_question(work_id: int):
    """Return the WorkQuestion with status='current', joined with Pool data."""
    with get_session() as session:
        result = (
            session.query(
                WorkQuestion.id,
                WorkQuestion.position,
                WorkQuestion.question_id,
                Pool.text,
                Pool.question_image,
                Pool.is_selfcheck,
                Pool.full_mark,
                Pool.answer,
                Pool.answer_image,
            )
            .join(Pool, WorkQuestion.question_id == Pool.id)
            .filter(WorkQuestion.work_id == work_id, WorkQuestion.status == "current")
            .order_by(WorkQuestion.position.asc())
            .first()
        )
        return result


def get_work_question_count(work_id: int) -> int:
    with get_session() as session:
        return session.query(WorkQuestion).filter_by(work_id=work_id).count()


def requeue_skipped_questions(work_id: int):
    """Set all skipped questions back to waiting so they can be attempted again."""
    with get_session() as session:
        skipped = session.query(WorkQuestion).filter_by(work_id=work_id, status="skipped").all()
        for q in skipped:
            q.status = "waiting"
            q.current_work_id = None
            q.start_datetime = None
        session.commit()


def get_completed_user_works(tid: int) -> List[Work]:
    """Return only finished works (end_datetime is not None), newest first."""
    with get_session() as session:
        users_alias = aliased(User)
        works = (
            session.query(Work)
            .join(users_alias, Work.user_id == users_alias.id)
            .filter(users_alias.telegram_id == tid, users_alias.is_deleted == 0, Work.end_datetime.isnot(None))
            .order_by(Work.end_datetime.desc())
            .all()
        )
        return works


def get_completed_user_works_by_user_id(user_id: int) -> List[Work]:
    with get_session() as session:
        return (
            session.query(Work)
            .filter(Work.user_id == user_id, Work.end_datetime.isnot(None))
            .order_by(Work.end_datetime.desc())
            .all()
        )


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
                    topic = session.query(Topic).filter_by(name=topic_name, volume=volume).first()
                    topic.tags_list = tags_list
                    topic.volume = volume
                    topic.is_active = 1
                    session.flush()
                    _sync_topic_tags(session, topic.id, topic.tags_list)
                else:
                    t = Topic(
                        name=topic_name,
                        tags_list=tags_list,
                        volume=volume,
                        is_active=1
                    )
                    session.add(t)
                    session.flush()
                    _sync_topic_tags(session, t.id, t.tags_list)

        session.commit()


def get_topic_tags(topic_id: int) -> list[str]:
    with get_session() as session:
        data = (
            session.query(Tag.slug)
            .join(TopicTag, TopicTag.tag_id == Tag.id)
            .filter(TopicTag.topic_id == topic_id)
            .order_by(Tag.slug.asc())
            .all()
        )
        return [slug for (slug,) in data]


def get_active_pool_tag_counts() -> dict[str, int]:
    with get_session() as session:
        rows = (
            session.query(Tag.slug, PoolTag.pool_id)
            .join(PoolTag, PoolTag.tag_id == Tag.id)
            .join(Pool, Pool.id == PoolTag.pool_id)
            .filter(Pool.is_active == 1)
            .all()
        )
        counts: dict[str, int] = {}
        for slug, _ in rows:
            counts[slug] = counts.get(slug, 0) + 1
        return counts
