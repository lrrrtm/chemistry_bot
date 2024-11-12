from datetime import datetime

from sqlalchemy import Column, Integer, BigInteger, String, Text, JSON, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.mysql import TINYINT, VARCHAR
from sqlalchemy.orm import declarative_base

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
    tags_list = Column(JSON, nullable=False, comment='Список тегов')
    created_at = Column(DateTime, nullable=False)


# Таблица 'topics'
class Topic(Base):
    __tablename__ = 'topics'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id темы')
    volume = Column(String, nullable=False)
    name = Column(Text, nullable=False, comment='Название темы')
    tags_list = Column(JSON, nullable=False, comment='Список тегов темы')
    is_active = Column(Integer, nullable=False)


# Таблица 'users'
class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, nullable=False)
    name = Column(Text, nullable=False)


# Таблица 'works'
class Work(Base):
    __tablename__ = 'works'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id задания')
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, default=0,
                     comment='Внутренний id пользователя')
    work_type = Column(Text, nullable=False, comment='тип задания (ЕГЭ/отдельная тема)')
    topic_id = Column(BigInteger, ForeignKey('topics.id'), nullable=False, default=0,
                      comment='id темы, если work_type = topic')
    hand_work_id = Column(VARCHAR(50), nullable=True)
    start_datetime = Column(DateTime, nullable=False, comment='Начало выполнения задания', default=datetime.now)
    end_datetime = Column(DateTime, nullable=False, comment='Окончание выполнения задания')


# Таблица 'work_questions_list'
class WorkQuestion(Base):
    __tablename__ = 'work_questions_list'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id статуса вопроса')
    work_id = Column(BigInteger, ForeignKey('works.id'), nullable=False, default=0, comment='id задания')
    question_id = Column(BigInteger, ForeignKey('pool.id'), nullable=False, comment='id вопроса из пула вопросов')
    position = Column(Integer, nullable=False)
    status = Column(Text, nullable=False, default='waiting')
    user_answer = Column(Text, nullable=False)
    user_mark = Column(Integer, nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)


class HandWork(Base):
    __tablename__ = 'hand_works'

    id = Column(BigInteger, nullable=False, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, default="Персональная тренировка")
    identificator = Column(VARCHAR(100), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    questions_list = Column(JSON, nullable=False)
