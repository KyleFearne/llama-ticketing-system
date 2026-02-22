from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Ticket(BaseModel):
    id: int
    subject: str
    body: str
    tags: Optional[List[str]] = []
    status: str
    ai_subject: Optional[str] = None
    category: Optional[str] = None
    suggested_assignee: Optional[str] = None
    created_at: datetime