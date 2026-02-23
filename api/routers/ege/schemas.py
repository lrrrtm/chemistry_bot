from pydantic import BaseModel


class EgeConvertingUpdate(BaseModel):
    data: dict  # input_mark -> output_mark
