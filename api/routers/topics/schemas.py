from pydantic import BaseModel
from typing import List


class TopicCreate(BaseModel):
    name: str
    volume: str


class TopicTagsUpdate(BaseModel):
    tags_list: List[str]
