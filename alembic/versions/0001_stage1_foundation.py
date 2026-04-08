"""stage1 foundation

Revision ID: 0001_stage1_foundation
Revises:
Create Date: 2026-04-05 11:30:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "0001_stage1_foundation"
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(bind, table_name: str) -> bool:
    return sa.inspect(bind).has_table(table_name)


def _index_exists(bind, table_name: str, index_name: str) -> bool:
    indexes = sa.inspect(bind).get_indexes(table_name)
    return any(idx["name"] == index_name for idx in indexes)


def _unique_exists(bind, table_name: str, index_name: str) -> bool:
    uniques = sa.inspect(bind).get_unique_constraints(table_name)
    indexes = sa.inspect(bind).get_indexes(table_name)
    return any(item["name"] == index_name for item in uniques + indexes)


def upgrade() -> None:
    bind = op.get_bind()

    if not _table_exists(bind, "tags"):
        op.create_table(
            "tags",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("slug", sa.String(length=255), nullable=False),
            sa.Column("label", sa.String(length=255), nullable=True),
            sa.Column("kind", sa.String(length=50), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("slug", name="uq_tags_slug"),
            mysql_charset="utf8mb4",
            mysql_collate="utf8mb4_0900_ai_ci",
        )

    if not _table_exists(bind, "topic_tags"):
        op.create_table(
            "topic_tags",
            sa.Column("topic_id", sa.BigInteger(), nullable=False),
            sa.Column("tag_id", sa.BigInteger(), nullable=False),
            sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("topic_id", "tag_id", name="pk_topic_tags"),
            mysql_charset="utf8mb4",
            mysql_collate="utf8mb4_0900_ai_ci",
        )

    if not _table_exists(bind, "pool_tags"):
        op.create_table(
            "pool_tags",
            sa.Column("pool_id", sa.BigInteger(), nullable=False),
            sa.Column("tag_id", sa.BigInteger(), nullable=False),
            sa.ForeignKeyConstraint(["pool_id"], ["pool.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("pool_id", "tag_id", name="pk_pool_tags"),
            mysql_charset="utf8mb4",
            mysql_collate="utf8mb4_0900_ai_ci",
        )

    if not _table_exists(bind, "hand_work_questions"):
        op.create_table(
            "hand_work_questions",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("hand_work_id", sa.BigInteger(), nullable=False),
            sa.Column("question_id", sa.BigInteger(), nullable=False),
            sa.Column("position", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["hand_work_id"], ["hand_works.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["question_id"], ["pool.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("hand_work_id", "position", name="uq_hand_work_questions_position"),
            mysql_charset="utf8mb4",
            mysql_collate="utf8mb4_0900_ai_ci",
        )

    if not _unique_exists(bind, "users", "uq_users_telegram_id"):
        op.create_index("uq_users_telegram_id", "users", ["telegram_id"], unique=True)

    if not _index_exists(bind, "users", "ix_users_is_deleted"):
        op.create_index("ix_users_is_deleted", "users", ["is_deleted"], unique=False)

    if not _index_exists(bind, "topics", "ix_topics_is_active"):
        op.create_index("ix_topics_is_active", "topics", ["is_active"], unique=False)

    if not _index_exists(bind, "pool", "ix_pool_is_active"):
        op.create_index("ix_pool_is_active", "pool", ["is_active"], unique=False)

    if not _index_exists(bind, "works", "ix_works_user_finished_started"):
        op.create_index(
            "ix_works_user_finished_started",
            "works",
            ["user_id", "end_datetime", "start_datetime"],
            unique=False,
        )

    if not _index_exists(bind, "work_questions_list", "ix_work_questions_list_work_status_position"):
        op.create_index(
            "ix_work_questions_list_work_status_position",
            "work_questions_list",
            ["work_id", "status", "position"],
            unique=False,
        )

    if not _unique_exists(bind, "work_questions_list", "uq_work_questions_list_work_position"):
        op.create_index(
            "uq_work_questions_list_work_position",
            "work_questions_list",
            ["work_id", "position"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()

    if _unique_exists(bind, "work_questions_list", "uq_work_questions_list_work_position"):
        op.drop_index("uq_work_questions_list_work_position", table_name="work_questions_list")

    if _index_exists(bind, "work_questions_list", "ix_work_questions_list_work_status_position"):
        op.drop_index("ix_work_questions_list_work_status_position", table_name="work_questions_list")

    if _index_exists(bind, "works", "ix_works_user_finished_started"):
        op.drop_index("ix_works_user_finished_started", table_name="works")

    if _index_exists(bind, "pool", "ix_pool_is_active"):
        op.drop_index("ix_pool_is_active", table_name="pool")

    if _index_exists(bind, "topics", "ix_topics_is_active"):
        op.drop_index("ix_topics_is_active", table_name="topics")

    if _index_exists(bind, "users", "ix_users_is_deleted"):
        op.drop_index("ix_users_is_deleted", table_name="users")

    if _unique_exists(bind, "users", "uq_users_telegram_id"):
        op.drop_index("uq_users_telegram_id", table_name="users")

    if _table_exists(bind, "hand_work_questions"):
        op.drop_table("hand_work_questions")

    if _table_exists(bind, "pool_tags"):
        op.drop_table("pool_tags")

    if _table_exists(bind, "topic_tags"):
        op.drop_table("topic_tags")

    if _table_exists(bind, "tags"):
        op.drop_table("tags")
