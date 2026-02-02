import uuid
from typing import Literal, Optional
from pydantic import BaseModel, Field



def generate_chunk_id(source :str, chunk_index: int) -> str:
    unique_string = f"{source} : {chunk_index}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_string))

class ChunkMetadata(BaseModel):
    page_number: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    section_title: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    header_level: Optional[int] = None
    element_type : Optional[str] = None


class Chunk(BaseModel):
    id : str =Field(default_factory= lambda : str(uuid.uuid4()))
    content : str
    source : str
    source_type : Literal["pdf", "code", "markdown"]
    metadata: ChunkMetadata = Field(default_factory=ChunkMetadata)
    token_count : int =0
    chunk_index : int = 0
    parent_id : Optional[str] = None

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "Chunk":
        return cls.model_validate(data)