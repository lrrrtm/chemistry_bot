"""normalize work sources

Revision ID: 0002_normalize_work_sources
Revises: 0001_stage1_foundation
Create Date: 2026-04-05 13:45:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_normalize_work_sources"
down_revision = "0001_stage1_foundation"
branch_labels = None
depends_on = None


def _table_exists(bind, table_name: str) -> bool:
    return sa.inspect(bind).has_table(table_name)


def _index_exists(bind, table_name: str, index_name: str) -> bool:
    indexes = sa.inspect(bind).get_indexes(table_name)
    return any(idx["name"] == index_name for idx in indexes)


def _column_is_nullable(bind, table_name: str, column_name: str) -> bool | None:
    columns = sa.inspect(bind).get_columns(table_name)
    for column in columns:
        if column["name"] == column_name:
            return column.get("nullable")
    return None


def upgrade() -> None:
    bind = op.get_bind()

    if not _table_exists(bind, "works"):
        return

    if _column_is_nullable(bind, "works", "topic_id") is False:
        op.alter_column(
            "works",
            "topic_id",
            existing_type=sa.BigInteger(),
            nullable=True,
        )

    op.execute("UPDATE works SET topic_id = NULL WHERE topic_id IN (0, -1)")
    op.execute("UPDATE works SET hand_work_id = NULL WHERE hand_work_id = ''")

    if not _index_exists(bind, "works", "ix_works_topic_id"):
        op.create_index("ix_works_topic_id", "works", ["topic_id"], unique=False)

    if not _index_exists(bind, "works", "ix_works_hand_work_id"):
        op.create_index("ix_works_hand_work_id", "works", ["hand_work_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()

    if not _table_exists(bind, "works"):
        return

    if _index_exists(bind, "works", "ix_works_hand_work_id"):
        op.drop_index("ix_works_hand_work_id", table_name="works")

    if _index_exists(bind, "works", "ix_works_topic_id"):
        op.drop_index("ix_works_topic_id", table_name="works")
