from pydantic import BaseModel
from typing import List, Optional

class CardCreate(BaseModel):
    front: str
    back: str
    labels: Optional[List[str]] = []
