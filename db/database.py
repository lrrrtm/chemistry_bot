import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from db.models import Base
from dotenv import load_dotenv
from os import getenv

load_dotenv()
DATABASE_URL = f"mysql+mysqlconnector://{getenv('DB_USER')}:{getenv('DB_PASSWORD')}@{getenv('DB_HOST')}:{getenv('DB_PORT')}/{getenv('DB_NAME')}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)
Session = scoped_session(sessionmaker(bind=engine))

for _attempt in range(10):
    try:
        Base.metadata.create_all(engine)
        break
    except Exception as _e:
        logging.warning("DB not ready (attempt %d/10): %s", _attempt + 1, _e)
        if _attempt == 9:
            raise
        time.sleep(3 * (_attempt + 1))


def _run_migrations():
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_NAME='works' AND COLUMN_NAME='share_token' "
            f"AND TABLE_SCHEMA='{getenv('DB_NAME')}'"
        ))
        if result.scalar() == 0:
            conn.execute(text(
                "ALTER TABLE works ADD COLUMN share_token VARCHAR(36) NULL UNIQUE COMMENT 'UUID токен для публичной ссылки на результат'"
            ))
            conn.commit()
            logging.info("Migration: added share_token column to works table")


_run_migrations()
