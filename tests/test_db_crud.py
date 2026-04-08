from __future__ import annotations

import importlib
import sys
import types
from contextlib import contextmanager
from dataclasses import dataclass
from types import SimpleNamespace

import pytest


@pytest.fixture
def crud_module(monkeypatch: pytest.MonkeyPatch):
    fake_db_database = types.ModuleType("db.database")
    fake_db_database.Session = lambda: None
    monkeypatch.setitem(sys.modules, "db.database", fake_db_database)
    sys.modules.pop("db.crud", None)

    import db.crud as crud

    crud = importlib.reload(crud)
    try:
        yield crud
    finally:
        sys.modules.pop("db.crud", None)


class QueryStub:
    def __init__(self, *, first_result=None, all_result=None, count_result=None):
        self.first_result = first_result
        self.all_result = all_result if all_result is not None else []
        self.count_result = count_result

    def filter_by(self, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def join(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def with_for_update(self, *args, **kwargs):
        return self

    def first(self):
        return self.first_result

    def all(self):
        return self.all_result

    def count(self):
        return self.count_result


class SessionStub:
    def __init__(self, *queries: QueryStub):
        self.queries = list(queries)
        self.added = []
        self.commits = 0

    def query(self, model):
        if not self.queries:
            raise AssertionError("Unexpected query() call")
        return self.queries.pop(0)

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commits += 1


@dataclass
class WorkQuestionStub:
    id: int
    position: int
    status: str
    work_id: int = 77
    current_work_id: int | None = None
    start_datetime: object = "started"


def _patch_session(monkeypatch: pytest.MonkeyPatch, crud, session: SessionStub) -> None:
    @contextmanager
    def fake_get_session():
        yield session

    monkeypatch.setattr(crud, "get_session", fake_get_session)


def test_normalize_work_source_enforces_consistency(crud_module):
    crud = crud_module

    assert crud._normalize_work_source("ege", 12, " hand ") == (None, None)
    assert crud._normalize_work_source("topic", 7, " hand ") == (7, None)
    assert crud._normalize_work_source("hand_work", 7, " hand ") == (None, "hand")

    with pytest.raises(ValueError):
        crud._normalize_work_source("topic", None, None)

    with pytest.raises(ValueError):
        crud._normalize_work_source("hand_work", None, "")


def test_create_user_reactivates_soft_deleted_user(crud_module, monkeypatch: pytest.MonkeyPatch):
    crud = crud_module
    existing = SimpleNamespace(name="Old Name", telegram_id=101, is_deleted=1)
    session = SessionStub(QueryStub(first_result=existing))
    _patch_session(monkeypatch, crud, session)

    result = crud.create_user(name="New Name", tid=101)

    assert result is existing
    assert existing.name == "New Name"
    assert existing.is_deleted == 0
    assert session.commits == 1
    assert session.added == []


def test_create_new_work_nulls_unused_sources(crud_module, monkeypatch: pytest.MonkeyPatch):
    crud = crud_module
    session = SessionStub()
    _patch_session(monkeypatch, crud, session)

    work = crud.create_new_work(user_id=5, work_type="ege", topic_id=99, hand_work_id="abc")

    assert work.topic_id is None
    assert work.hand_work_id is None
    assert session.commits == 1
    assert len(session.added) == 1


def test_open_next_question_keeps_first_current_and_resets_duplicates(
    crud_module, monkeypatch: pytest.MonkeyPatch
):
    crud = crud_module
    keeper = WorkQuestionStub(id=1, position=1, status="current")
    duplicate = WorkQuestionStub(id=2, position=3, status="current")
    session = SessionStub(QueryStub(all_result=[keeper, duplicate]))
    _patch_session(monkeypatch, crud, session)

    result = crud.open_next_question(work_id=77)

    assert result is keeper
    assert keeper.current_work_id == keeper.work_id
    assert duplicate.status == "waiting"
    assert duplicate.current_work_id is None
    assert duplicate.start_datetime is None
    assert session.commits == 1


def test_open_next_question_promotes_first_waiting_question(
    crud_module, monkeypatch: pytest.MonkeyPatch
):
    crud = crud_module
    waiting = WorkQuestionStub(id=5, position=2, status="waiting", start_datetime=None)
    session = SessionStub(
        QueryStub(all_result=[]),
        QueryStub(first_result=waiting),
    )
    _patch_session(monkeypatch, crud, session)

    result = crud.open_next_question(work_id=77)

    assert result is waiting
    assert waiting.status == "current"
    assert waiting.current_work_id == waiting.work_id
    assert waiting.start_datetime is not None
    assert session.commits == 1


def test_open_next_question_returns_none_when_queue_is_empty(
    crud_module, monkeypatch: pytest.MonkeyPatch
):
    crud = crud_module
    session = SessionStub(
        QueryStub(all_result=[]),
        QueryStub(first_result=None),
    )
    _patch_session(monkeypatch, crud, session)

    result = crud.open_next_question(work_id=77)

    assert result is None
    assert session.commits == 0


def test_update_question_status_clears_current_marker(
    crud_module, monkeypatch: pytest.MonkeyPatch
):
    crud = crud_module
    question = WorkQuestionStub(id=9, position=1, status="current", current_work_id=77)
    session = SessionStub(QueryStub(first_result=question))
    _patch_session(monkeypatch, crud, session)

    crud.update_question_status(q_id=9, status="skipped")

    assert question.status == "skipped"
    assert question.current_work_id is None
    assert question.start_datetime is None
    assert session.commits == 1


def test_close_question_clears_current_marker(
    crud_module, monkeypatch: pytest.MonkeyPatch
):
    crud = crud_module
    question = WorkQuestionStub(id=11, position=2, status="current", current_work_id=77)
    session = SessionStub(QueryStub(first_result=question))
    _patch_session(monkeypatch, crud, session)

    crud.close_question(
        q_id=11,
        user_answer="42",
        user_mark=1,
        end_datetime=SimpleNamespace(),
    )

    assert question.status == "answered"
    assert question.current_work_id is None
    assert question.user_answer == "42"
    assert question.user_mark == 1
    assert session.commits == 1


def test_get_questions_list_by_id_preserves_requested_order(
    crud_module, monkeypatch: pytest.MonkeyPatch
):
    crud = crud_module
    q10 = SimpleNamespace(id=10, tags_list=["a"])
    q30 = SimpleNamespace(id=30, tags_list=["b"])
    session = SessionStub(QueryStub(all_result=[q10, q30]))
    _patch_session(monkeypatch, crud, session)
    monkeypatch.setattr(crud, "_hydrate_pool_tags", lambda session, questions: questions)

    result = crud.get_questions_list_by_id([30, 20, 10])

    assert [question.id for question in result] == [30, 10]


def test_get_pool_by_tags_returns_empty_for_empty_tags(
    crud_module, monkeypatch: pytest.MonkeyPatch
):
    crud = crud_module
    session = SessionStub()
    _patch_session(monkeypatch, crud, session)

    result = crud.get_pool_by_tags([])

    assert result == []


def test_get_hand_work_question_count_uses_normalized_table(
    crud_module, monkeypatch: pytest.MonkeyPatch
):
    crud = crud_module
    session = SessionStub(QueryStub(count_result=3))
    _patch_session(monkeypatch, crud, session)

    result = crud.get_hand_work_question_count("normalized")

    assert result == 3
