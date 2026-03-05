from pydantic import BaseModel
from typing import List

class CompanyCreate(BaseModel):
    code: str
    name: str
    mst: str
    emails: List[str]
