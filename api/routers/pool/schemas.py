from typing import List

from pydantic import BaseModel


class QuestionUpdate(BaseModel):
    text: str
    answer: str
    level: int
    full_mark: int
    tags_list: List[str]
    is_rotate: int
    is_selfcheck: int


class NewQuestion(BaseModel):
    text: str
    answer: str
    type: str
    level: int
    full_mark: int
    tags_list: List[str]
    is_rotate: bool = False
    is_selfcheck: bool = False
