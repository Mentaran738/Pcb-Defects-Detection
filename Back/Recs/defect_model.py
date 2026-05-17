from pydantic import BaseModel
from typing import Dict

class DefectClass(BaseModel):
    defects: Dict[str, int] = {}

class DeleteInspectionsRequest(BaseModel):
    ids: list[int]