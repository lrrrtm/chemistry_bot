"""enforce single current question per work

Revision ID: 0003_one_current_workq
Revises: 0002_normalize_work_sources
Create Date: 2026-04-05 15:20:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_one_current_workq"
down_revision = "0002_normalize_work_sources"
branch_labels = None
depends_on = None


def _table_exists(bind, table_name: str) -> bool:
    return sa.inspect(bind).has_table(table_name)


def _index_exists(bind, table_name: str, index_name: str) -> bool:
    indexes = sa.inspect(bind).get_indexes(table_name)
    return any(idx["name"] == index_name for idx in indexes)


def _column_exists(bind, table_name: str, column_name: str) -> bool:
    columns = sa.inspect(bind).get_columns(table_name)
    return any(column["name"] == column_name for column in columns)


def upgrade() -> None:
    bind = op.get_bind()

    if not _table_exists(bind, "work_questions_list"):
        return

    op.execute(
        """
        UPDATE work_questions_list wq
        JOIN (
            SELECT work_id, MIN(position) AS keeper_position
            FROM work_questions_list
            WHERE status = 'current'
            GROUP BY work_id
            HAVING COUNT(*) > 1
        ) duplicated
            ON duplicated.work_id = wq.work_id
        SET
            wq.status = 'waiting',
            wq.start_datetime = NULL
        WHERE
            wq.status = 'current'
            AND wq.position <> duplicated.keeper_position
        """
    )

    if not _column_exists(bind, "work_questions_list", "current_work_id"):
        op.add_column(
            "work_questions_list",
            sa.Column("current_work_id", sa.BigInteger(), nullable=True),
        )

    op.execute(
        """
        UPDATE work_questions_list
        SET current_work_id = CASE
            WHEN status = 'current' THEN work_id
            ELSE NULL
        END
        """
    )

    if not _index_exists(bind, "work_questions_list", "uq_work_questions_list_current_work"):
        op.create_index(
            "uq_work_questions_list_current_work",
            "work_questions_list",
            ["current_work_id"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()

    if not _table_exists(bind, "work_questions_list"):
        return

    if _index_exists(bind, "work_questions_list", "uq_work_questions_list_current_work"):
        op.drop_index("uq_work_questions_list_current_work", table_name="work_questions_list")

    if _column_exists(bind, "work_questions_list", "current_work_id"):
        op.execute("ALTER TABLE work_questions_list DROP COLUMN current_work_id")
