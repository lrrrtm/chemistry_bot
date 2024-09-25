from datetime import datetime

from sqlalchemy import Column, Integer, BigInteger, String, Text, JSON, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

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
    type = Column(Text, nullable=False, comment='Тип вопроса (1 или 2 часть)')
    level = Column(Integer, nullable=False, comment='Сложность вопроса (от 1 до 5)')
    text = Column(Text, nullable=False, comment='Текст вопроса')
    question_image = Column(TINYINT, nullable=False, default=0, comment='Наличие изображения вопроса')
    answer = Column(Text, nullable=False, comment='Текст ответа')
    answer_image = Column(TINYINT, nullable=False, default=0, comment='Наличие изображения ответа')
    full_mark = Column(TINYINT, nullable=False, default=0, comment='Максимальный первичный балл')
    tags_list = Column(JSON, nullable=False, comment='Список тегов')

# Таблица 'stats'
class Stats(Base):
    __tablename__ = 'stats'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='id записи')
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='id пользователя')
    work_id = Column(BigInteger, nullable=False, default=0, comment='id задания')
    last_attempt = Column(Integer, nullable=False, comment='Кол-во баллов за последнюю попытку')
    max_attempt = Column(Integer, nullable=False, comment='Лучший результат')

    # user = relationship("Users", back_populates="stats")

# Таблица 'topics'
class Topic(Base):
    __tablename__ = 'topics'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id темы')
    name = Column(Text, nullable=False, comment='Название темы')
    tags_list = Column(JSON, nullable=False, comment='Список тегов темы')

# Таблица 'users'
class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, nullable=False)
    name = Column(Text, nullable=False)

    # stats = relationship("Stats", back_populates="user")

# Таблица 'works'
class Work(Base):
    __tablename__ = 'works'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id задания')
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, default=0, comment='Внутренний id пользователя')
    work_type = Column(Text, nullable=False, comment='тип задания (ЕГЭ/отдельная тема)')
    topic_id = Column(BigInteger, ForeignKey('topics.id'), nullable=False, default=0, comment='id темы, если work_type = topic')
    start_datetime = Column(DateTime, nullable=False, comment='Начало выполнения задания', default=datetime.now)
    end_datetime = Column(DateTime, nullable=False, comment='Окончание выполнения задания')

    # user = relationship("Users")
    # topic = relationship("Topics")

# Таблица 'work_questions_list'
class WorkQuestion(Base):
    __tablename__ = 'work_questions_list'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id статуса вопроса')
    work_id = Column(BigInteger, ForeignKey('works.id'), nullable=False, default=0, comment='id задания')
    question_id = Column(BigInteger, ForeignKey('pool.id'), nullable=False, comment='id вопроса из пула вопросов')
    position = Column(Integer, nullable=False)
    status = Column(Text, nullable=False)
    user_answer = Column(Text, nullable=False)
    user_mark = Column(Integer, nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)

    # work = relationship("Works")
    # question = relationship("Pool")
