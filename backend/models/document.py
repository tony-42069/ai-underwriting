from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Document(BaseModel):
    id: Optional[str] = None
    filename: str
    status: str
    uploaded_at: datetime = datetime.now()
    processed: bool = False