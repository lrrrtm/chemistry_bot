from datetime import datetime

from sqlalchemy import Column, Integer, BigInteger, String, Text, ForeignKey, DateTime, Index
from sqlalchemy.dialects.mysql import TINYINT, VARCHAR
from sqlalchemy.orm import declarative_base, reconstructor

Base = declarative_base()


# Таблица 'converting'
class Converting(Base):
    __tablename__ = 'converting'

    id = Column(Integer, primary_key=True, autoincrement=True)
    input_mark = Column(Integer)
    output_mark = Column(Integer)


# Таблица 'pool'
class Pool(Base):
    __tablename__ = 'pool'

    def __init__(self, *args, tags_list=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tags_list = list(tags_list or [])

    @reconstructor
    def init_on_load(self):
        self.tags_list = []

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id вопроса')
    import_id = Column(Text, nullable=True)
    type = Column(Text, nullable=False, comment='Тип вопроса (1 или 2 часть)')
    level = Column(Integer, nullable=False, comment='Сложность вопроса (от 1 до 5)')
    text = Column(VARCHAR(2048), nullable=True, comment='Текст вопроса', default='Вопрос на картинке')
    question_image = Column(TINYINT, nullable=False, default=0, comment='Наличие изображения вопроса')
    answer = Column(VARCHAR(2048), nullable=True, comment='Текст ответа', default='Ответ на картинке')
    answer_image = Column(TINYINT, nullable=False, default=0, comment='Наличие изображения ответа')
    full_mark = Column(TINYINT, nullable=False, default=0, comment='Максимальный первичный балл')
    is_rotate = Column(Integer, nullable=False)
    is_selfcheck = Column(Integer, nullable=False)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False)


# Таблица 'topics'
class Topic(Base):
    __tablename__ = 'topics'

    def __init__(self, *args, tags_list=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tags_list = list(tags_list or [])

    @reconstructor
    def init_on_load(self):
        self.tags_list = []

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id темы')
    volume = Column(String(255), nullable=False)
    name = Column(Text, nullable=False, comment='Название темы')
    is_active = Column(Integer, nullable=False)


# Таблица 'users'
class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, nullable=True)
    name = Column(Text, nullable=False)
    username = Column(String(64), nullable=True, unique=True)
    password_hash = Column(String(255), nullable=True)
    invite_token_hash = Column(String(64), nullable=True)
    invite_expires_at = Column(DateTime, nullable=True)
    invite_consumed_at = Column(DateTime, nullable=True)
    telegram_link_token_hash = Column(String(64), nullable=True)
    telegram_link_expires_at = Column(DateTime, nullable=True)
    student_token_version = Column(Integer, nullable=False, default=0)
    is_deleted = Column(Integer, nullable=False, default=0)


# Таблица 'works'
class Work(Base):
    __tablename__ = 'works'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id задания')
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, default=0,
                     comment='Внутренний id пользователя')
    work_type = Column(Text, nullable=False, comment='тип задания (ЕГЭ/отдельная тема)')
    topic_id = Column(BigInteger, ForeignKey('topics.id'), nullable=True,
                      comment='id темы, если work_type = topic')
    hand_work_id = Column(VARCHAR(50), nullable=True)
    start_datetime = Column(DateTime, nullable=False, comment='Начало выполнения задания', default=datetime.now)
    end_datetime = Column(DateTime, nullable=True, comment='Окончание выполнения задания')
    share_token = Column(VARCHAR(36), nullable=True, unique=True, comment='UUID токен для публичной ссылки на результат')


# Таблица 'work_questions_list'
class WorkQuestion(Base):
    __tablename__ = 'work_questions_list'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id статуса вопроса')
    work_id = Column(BigInteger, ForeignKey('works.id'), nullable=False, default=0, comment='id задания')
    question_id = Column(BigInteger, ForeignKey('pool.id'), nullable=False, comment='id вопроса из пула вопросов')
    position = Column(Integer, nullable=False)
    status = Column(Text, nullable=False, default='waiting')
    current_work_id = Column(BigInteger, nullable=True)
    user_answer = Column(Text, nullable=True)
    user_mark = Column(Integer, nullable=True)
    start_datetime = Column(DateTime, nullable=True)
    end_datetime = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('ix_work_questions_list_work_status_position', 'work_id', 'status', 'position'),
        Index('uq_work_questions_list_work_position', 'work_id', 'position', unique=True),
        Index('uq_work_questions_list_current_work', 'current_work_id', unique=True),
    )


class HandWork(Base):
    __tablename__ = 'hand_works'

    def __init__(self, *args, questions_list=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.questions_list = list(questions_list or [])

    @reconstructor
    def init_on_load(self):
        self.questions_list = []

    id = Column(BigInteger, nullable=False, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, default="Персональная тренировка")
    identificator = Column(VARCHAR(100), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    is_deleted = Column(Integer, nullable=False, default=0)


class TheoryDocument(Base):
    __tablename__ = 'theory_documents'

    def __init__(self, *args, tags_list=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tags_list = list(tags_list or [])

    @reconstructor
    def init_on_load(self):
        self.tags_list = []

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False, unique=True)
    original_file_name = Column(String(255), nullable=True)
    mime_type = Column(String(100), nullable=False, default="application/pdf")
    file_size = Column(BigInteger, nullable=False, default=0)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    slug = Column(String(255), nullable=False, unique=True)
    label = Column(String(255), nullable=True)
    kind = Column(String(50), nullable=True)


class TopicTag(Base):
    __tablename__ = 'topic_tags'

    topic_id = Column(BigInteger, ForeignKey('topics.id', ondelete='CASCADE'), primary_key=True)
    tag_id = Column(BigInteger, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)


class PoolTag(Base):
    __tablename__ = 'pool_tags'

    pool_id = Column(BigInteger, ForeignKey('pool.id', ondelete='CASCADE'), primary_key=True)
    tag_id = Column(BigInteger, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)


class HandWorkQuestion(Base):
    __tablename__ = 'hand_work_questions'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    hand_work_id = Column(BigInteger, ForeignKey('hand_works.id', ondelete='CASCADE'), nullable=False)
    question_id = Column(BigInteger, ForeignKey('pool.id', ondelete='RESTRICT'), nullable=False)
    position = Column(Integer, nullable=False)

    __table_args__ = (
        Index('uq_hand_work_questions_position', 'hand_work_id', 'position', unique=True),
    )


class TheoryDocumentTag(Base):
    __tablename__ = 'theory_document_tags'

    document_id = Column(BigInteger, ForeignKey('theory_documents.id', ondelete='CASCADE'), primary_key=True)
    tag_id = Column(BigInteger, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)


class StudentAccessGrant(Base):
    __tablename__ = 'student_access_grants'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    purpose = Column(String(50), nullable=False)
    token_hash = Column(String(64), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    consumed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    created_by = Column(String(50), nullable=True)

    __table_args__ = (
        Index('ix_student_access_grants_user_purpose', 'user_id', 'purpose'),
        Index('ix_student_access_grants_expires_at', 'expires_at'),
    )
