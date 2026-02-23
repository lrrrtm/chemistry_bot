from typing import List, Optional

from pydantic import BaseModel


class HandWorkCreate(BaseModel):
    name: str
    questions: dict  # tag -> count
    mode: str = "tags"  # "tags" or "hard_filter"
    hard_tags: Optional[List[str]] = None
    questions_count: Optional[int] = None


class SendTrainingRequest(BaseModel):
    telegram_id: int
    link: str
    name: str
