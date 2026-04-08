from pydantic import BaseModel


class TheoryDocumentUpdate(BaseModel):
    title: str
    tags_list: list[str]
