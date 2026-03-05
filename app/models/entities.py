from dataclasses import dataclass
from typing import List

@dataclass
class Company:
    id: int | None
    code: str
    name: str
    mst: str
    emails: List[str]
