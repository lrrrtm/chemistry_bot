import time
import logging
import uuid
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


def _add_column_if_not_exists(conn, table: str, column_def: str, column_name: str):
    """Try to add a column, ignoring 'Duplicate column' errors (MySQL 1060)."""
    try:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_def}"))
        conn.commit()
        logging.info("Migration: added %s column to %s table", column_name, table)
    except Exception as e:
        if '1060' in str(e):
            logging.debug("Migration skipped: %s.%s already exists", table, column_name)
        else:
            raise


def run_migrations():
    with engine.connect() as conn:
        _add_column_if_not_exists(
            conn, 'works',
            "share_token VARCHAR(36) NULL UNIQUE COMMENT 'UUID токен для публичной ссылки на результат'",
            'share_token'
        )
        _add_column_if_not_exists(
            conn, 'users',
            'is_deleted INT NOT NULL DEFAULT 0',
            'is_deleted'
        )
        _add_column_if_not_exists(
            conn, 'hand_works',
            'is_deleted INT NOT NULL DEFAULT 0',
            'is_deleted'
        )

        # Fill share_token for old works that don't have one
        rows = conn.execute(text(
            "SELECT id FROM works WHERE share_token IS NULL"
        )).fetchall()
        for row in rows:
            conn.execute(text(
                "UPDATE works SET share_token = :token WHERE id = :wid"
            ), {"token": str(uuid.uuid4()), "wid": row[0]})
        if rows:
            conn.commit()
            logging.info("Migration: generated share_token for %d old works", len(rows))


run_migrations()
