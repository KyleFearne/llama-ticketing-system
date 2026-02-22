from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Employee(BaseModel):
    id: int
    name: str

class Ticket(BaseModel):
    id: int
    body: str
    tags: Optional[List[str]] = []
    status: str
    source: Optional[str] = None
    ai_subject: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    assigned_to: Optional[str] = None
    suggested_response: Optional[str] = None
    created_at: datetime

class TicketUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None